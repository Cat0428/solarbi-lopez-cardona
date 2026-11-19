<#
  Taller 6 · Levanta TODA la solución desde cero con un solo comando (Windows / PowerShell).
      .\scripts\up.ps1            # ambiente demo
      .\scripts\up.ps1 -Ambiente dev
  Requisitos: Docker Desktop encendido, kind y kubectl en el PATH, credenciales.env creado
  y la capa Bronze preparada (.\scripts\preparar_bronze.ps1).
#>
param([ValidateSet('demo', 'dev')][string]$Ambiente = 'demo')
$ErrorActionPreference = 'Continue'
Set-Location (Split-Path $PSScriptRoot -Parent)          # siempre desde taller6/

$CLUSTER = 'microrred'
$NS      = 'microrred'
$IMG_ETL = 'microrred-etl:1.0.0'
$IMG_SIM = 'microrred-simulador:1.0.0'

function Paso([string]$titulo, [scriptblock]$accion) {
    Write-Host "`n==> $titulo" -ForegroundColor Cyan
    & $accion
    if ($LASTEXITCODE -ne 0) { Write-Host "FALLÓ: $titulo" -ForegroundColor Red; exit 1 }
}

foreach ($c in 'docker', 'kind', 'kubectl') {
    if (-not (Get-Command $c -ErrorAction SilentlyContinue)) { Write-Host "Falta '$c' en el PATH." -ForegroundColor Red; exit 1 }
}
if (-not (Test-Path credenciales.env)) { Write-Host 'Falta credenciales.env (copie credenciales.env.example).' -ForegroundColor Red; exit 1 }
if (-not (Get-ChildItem data/bronze -Filter *.sqlite -ErrorAction SilentlyContinue)) {
    Write-Host 'Falta la base .sqlite en data/bronze. Ejecute .\scripts\preparar_bronze.ps1' -ForegroundColor Red; exit 1
}

# Docker Compose (desarrollo) usa los mismos puertos 55432 y 3001: se detiene antes de crear el
# clúster. 'down' sin -v conserva su volumen; el clúster tiene su propio almacenamiento.
if (docker compose ps -q 2>$null) {
    Write-Host 'Deteniendo Docker Compose (libera los puertos 55432 y 3001)...' -ForegroundColor Yellow
    docker compose down
}

$existe = (kind get clusters 2>$null) -contains $CLUSTER
if (-not $existe) {
    # kind recibe la carpeta Bronze con ruta ABSOLUTA (una ruta relativa depende de dónde se
    # ejecute el comando). Se genera una copia temporal de k8s/kind-config.yaml con esa ruta.
    $bronze = (Resolve-Path data/bronze).Path -replace '\\', '/'
    $cfg = Join-Path $env:TEMP 'kind-microrred.yaml'
    $texto = (Get-Content k8s/kind-config.yaml -Raw -Encoding UTF8) -replace 'hostPath: \./data/bronze', "hostPath: `"$bronze`""
    [IO.File]::WriteAllText($cfg, $texto)      # UTF-8 sin BOM: la ruta puede tener tildes
    Paso 'Creando clúster kind de un nodo' { kind create cluster --config $cfg }
}
else {
    Write-Host "Clúster '$CLUSTER' ya existe: se reutiliza."
    # Si Docker Desktop o el equipo se reiniciaron, el contenedor del nodo queda detenido y kind
    # no lo vuelve a encender: se arranca aquí y se espera a que el nodo esté Ready.
    $nodo = "$CLUSTER-control-plane"
    if ((docker inspect -f '{{.State.Running}}' $nodo 2>$null) -ne 'true') {
        Paso "Encendiendo el nodo detenido ($nodo)" { docker start $nodo }
        Write-Host "`n==> Esperando que el nodo quede Ready" -ForegroundColor Cyan
        $listo = $false
        for ($i = 0; $i -lt 36 -and -not $listo; $i++) {      # hasta 3 minutos: la API tarda en volver
            Start-Sleep 5
            kubectl wait --for=condition=Ready node --all --timeout=5s 2>$null | Out-Null
            $listo = ($LASTEXITCODE -eq 0)
        }
        if (-not $listo) { Write-Host 'FALLÓ: el nodo no quedó Ready. Pruebe .\scripts\down.ps1 y luego .\scripts\up.ps1' -ForegroundColor Red; exit 1 }
        Write-Host '  nodo Ready'
        # Los pods se recrean solos; el Job del ETL ya terminado no se vuelve a ejecutar
    }
}

Paso 'Construyendo imagen del ETL'       { docker build -f etl/Dockerfile -t $IMG_ETL . }
Paso 'Construyendo imagen del simulador' { docker build -f simulador/Dockerfile -t $IMG_SIM . }
Paso 'Cargando imágenes propias en el nodo kind' { kind load docker-image $IMG_ETL $IMG_SIM --name $CLUSTER }

# Imágenes oficiales: si ya están en el Docker del anfitrión se copian al nodo, así el despliegue
# no depende de la red del aula. Si la copia falla (p. ej. imagen multiplataforma), el nodo las
# descarga de Docker Hub por su cuenta: por eso este paso no detiene el script.
Write-Host "`n==> Copiando imágenes oficiales al nodo (opcional)" -ForegroundColor Cyan
foreach ($img in 'postgres:16.9', 'grafana/grafana:12.2.0') {
    docker image inspect $img *> $null
    if ($LASTEXITCODE -ne 0) { docker pull $img }
    kind load docker-image $img --name $CLUSTER
    if ($LASTEXITCODE -ne 0) { Write-Host "  (no se pudo copiar $img; el nodo la descargará)" -ForegroundColor Yellow }
}

Paso 'Namespace'                         { kubectl apply -f k8s/base/namespace.yaml }
Paso 'Secret desde credenciales.env'     {
    kubectl create secret generic microrred-credenciales -n $NS --from-env-file=credenciales.env `
        --dry-run=client -o yaml | kubectl apply -f -
}
Paso "Manifiestos (overlay $Ambiente)"   { kubectl apply -k "k8s/overlays/$Ambiente" }
Paso 'Esperando PostgreSQL'              { kubectl rollout status statefulset/postgres -n $NS --timeout=240s }
Paso 'Esperando Grafana'                 { kubectl rollout status deployment/grafana -n $NS --timeout=240s }
Paso 'Esperando la carga histórica (Job ETL)' {
    kubectl wait --for=condition=complete job/etl-historico -n $NS --timeout=1800s
}
kubectl logs job/etl-historico -n $NS --tail=40
kubectl get all,pvc -n $NS
Write-Host "`nListo. Grafana: http://127.0.0.1:3001  ·  PostgreSQL (DBeaver / Power BI): 127.0.0.1:55432" -ForegroundColor Green
