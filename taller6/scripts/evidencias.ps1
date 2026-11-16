<#
  Taller 6 · Reúne las evidencias del clúster para el informe (punto K.4: salida de kubectl get y
  kubectl describe) y ejecuta las demostraciones de resiliencia. Requiere el clúster arriba
  (.\scripts\up.ps1) y deja todo en docs\evidencias\*.txt.

      .\scripts\evidencias.ps1              # todo (incluye borrar los pods de PostgreSQL y Grafana)
      .\scripts\evidencias.ps1 -SinDemos    # solo lectura: get, describe, logs

  No imprime contraseñas: el Secret se muestra con "describe" (solo nombres y tamaños) y las
  consultas a PostgreSQL usan las variables que el pod ya recibió del Secret.
#>
param([switch]$SinDemos)
$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [Text.Encoding]::UTF8      # tildes de los logs de kubectl
$OutputEncoding = New-Object System.Text.UTF8Encoding $false   # SQL con tildes hacia psql
Set-Location (Split-Path $PSScriptRoot -Parent)
$NS  = 'microrred'
$OUT = 'docs/evidencias'
New-Item -ItemType Directory -Force $OUT | Out-Null

# Escribe cada comando con su salida en un archivo de texto (UTF-8 sin BOM)
function Ev([string]$archivo, [scriptblock[]]$comandos) {
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine("# $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') (hora de Colombia)")
    foreach ($c in $comandos) {
        [void]$sb.AppendLine("PS> $($c.ToString().Trim())")
        # Las advertencias de kubectl llegan por stderr: se escriben como texto, sin el ruido de PowerShell
        $res = & $c 2>&1 | ForEach-Object {
            if ($_ -is [System.Management.Automation.ErrorRecord]) { "($($_.Exception.Message.Trim()))" } else { $_ }
        } | Out-String -Width 230
        [void]$sb.AppendLine($res.TrimEnd())
        [void]$sb.AppendLine('')
    }
    [IO.File]::WriteAllText((Join-Path (Get-Location) "$OUT/$archivo"), $sb.ToString())
    Write-Host "  · $archivo" -ForegroundColor Gray
}

# SQL dentro del pod de PostgreSQL con el usuario que el pod recibió del Secret
function Psql([string]$sql) {
    $sql | kubectl exec -i -n $NS postgres-0 -- sh -c 'psql -U $POSTGRES_USER -d $POSTGRES_DB -P pager=off'
}

# API de Grafana por el NodePort (usuario y clave de credenciales.env, sin mostrarlos)
$cred = @{}
Get-Content credenciales.env | ForEach-Object {
    if ($_ -match '^\s*([A-Z_]+)\s*=\s*(.*)$') { $cred[$Matches[1]] = $Matches[2].Trim() }
}
$par = "$($cred.GF_SECURITY_ADMIN_USER):$($cred.GF_SECURITY_ADMIN_PASSWORD)"
$H = @{ Authorization = 'Basic ' + [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($par)) }
# Invoke-WebRequest + UTF-8 explícito: PowerShell 5.1 decodifica mal las tildes y entrega los arreglos
# JSON como un solo objeto; ForEach-Object los vuelve filas.
function Gf([string]$ruta) {
    $r = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:3001$ruta" -Headers $H -TimeoutSec 15
    [Text.Encoding]::UTF8.GetString($r.RawContentStream.ToArray()) | ConvertFrom-Json | ForEach-Object { $_ }
}
function EsperarGrafana {
    for ($i = 0; $i -lt 60; $i++) {
        try { if ((Invoke-RestMethod http://127.0.0.1:3001/api/health -TimeoutSec 5).database -eq 'ok') { return } } catch {}
        Start-Sleep 3
    }
}

$CONTEO = @"
SELECT 'silver.lectura_1min (historico)' AS tabla, count(*) FROM silver.lectura_1min WHERE origen = 'historico'
UNION ALL SELECT 'silver.lectura_1min (simulador)', count(*) FROM silver.lectura_1min WHERE origen = 'simulador'
UNION ALL SELECT 'gold.fact_energia_hora', count(*) FROM gold.fact_energia_hora
UNION ALL SELECT 'gold.fact_evento', count(*) FROM gold.fact_evento
UNION ALL SELECT 'gold.fact_actividad', count(*) FROM gold.fact_actividad;
"@

Write-Host "`n==> Evidencias de lectura" -ForegroundColor Cyan
Ev '01_entorno.txt' @(
    { docker version --format 'Docker cliente {{.Client.Version}} / servidor {{.Server.Version}}' },
    { kind version },
    { kubectl version },
    { kind get clusters },
    { kubectl get nodes -o wide }
)
Ev '02_imagenes.txt' @(
    { docker images --format 'table {{.Repository}}:{{.Tag}}\t{{.Size}}' | Select-String -Pattern 'microrred|postgres|grafana|REPOSITORY' },
    { docker image history microrred-etl:1.0.0 --format '{{.Size}}\t{{.CreatedBy}}' |
        ForEach-Object { $_.Substring(0, [Math]::Min(140, $_.Length)) } | Select-Object -First 12 },
    { docker exec microrred-control-plane crictl images | Select-String -Pattern 'microrred|postgres|grafana|IMAGE' }
)
Ev '03_get_all.txt' @(
    { kubectl get all,pvc,configmap,secret -n $NS -o wide },
    { kubectl get pv },
    { kubectl get storageclass }
)
Ev '04_postgres.txt' @(
    { kubectl describe statefulset postgres -n $NS },
    { kubectl describe pod postgres-0 -n $NS },
    { kubectl describe pvc -n $NS }
)
Ev '05_grafana.txt' @(
    { kubectl describe deployment grafana -n $NS },
    { kubectl describe pod -l app=grafana -n $NS }
)
Ev '06_etl_job.txt' @(
    { kubectl describe job etl-historico -n $NS },
    { kubectl logs job/etl-historico -n $NS -c etl --tail=60 },
    { Psql 'SELECT ejecucion_id, inicio, fin, fin - inicio AS duracion, estado, archivo_bronze FROM ops.etl_ejecucion ORDER BY 1 DESC LIMIT 5;' }
)
$ultimoSim = (kubectl get jobs -n $NS -o name --sort-by=.metadata.creationTimestamp | Select-String simulador | Select-Object -Last 1)
Ev '07_simulador.txt' @(
    { kubectl describe cronjob simulador -n $NS },
    { kubectl get jobs -n $NS --sort-by=.metadata.creationTimestamp },
    { kubectl logs "$ultimoSim" -n $NS },
    { Psql "SELECT inversor_id, count(*) AS minutos_simulados, max(ts) AS ultimo_minuto FROM silver.lectura_1min WHERE origen = 'simulador' GROUP BY 1 ORDER BY 1;" }
)
Ev '08_servicios_dns.txt' @(
    { kubectl get svc,endpointslices -n $NS -o wide },
    { kubectl describe svc postgres-externo -n $NS },
    { kubectl describe svc grafana -n $NS },
    { kubectl exec -n $NS postgres-0 -- getent hosts postgres.microrred.svc.cluster.local grafana.microrred.svc.cluster.local }
)
Ev '09_recursos_sondas.txt' @(
    { kubectl get pods -n $NS -o custom-columns='POD:.metadata.name,REQ_CPU:.spec.containers[*].resources.requests.cpu,REQ_MEM:.spec.containers[*].resources.requests.memory,LIM_CPU:.spec.containers[*].resources.limits.cpu,LIM_MEM:.spec.containers[*].resources.limits.memory' },
    { kubectl get cronjob simulador -n $NS -o jsonpath='{.spec.jobTemplate.spec.template.spec.containers[0].resources}' },
    { kubectl get job etl-historico -n $NS -o jsonpath='{.spec.template.spec.containers[0].resources}' },
    { kubectl get statefulset postgres -n $NS -o jsonpath='{.spec.template.spec.containers[0].livenessProbe}' },
    { kubectl get statefulset postgres -n $NS -o jsonpath='{.spec.template.spec.containers[0].readinessProbe}' },
    { kubectl get deployment grafana -n $NS -o jsonpath='{.spec.template.spec.containers[0].livenessProbe}' },
    { kubectl get deployment grafana -n $NS -o jsonpath='{.spec.template.spec.containers[0].readinessProbe}' }
)
Ev '10_secret_configmap.txt' @(
    { kubectl describe secret microrred-credenciales -n $NS },
    { kubectl get configmap microrred-parametros -n $NS -o yaml },
    { kubectl get configmap -n $NS }
)
Ev '11_grafana_api.txt' @(
    { Gf '/api/health' | Format-List },
    { Gf '/api/datasources' | Select-Object name, type, uid, url, isDefault | Format-Table -AutoSize },
    { Gf '/api/search?type=dash-db' | Select-Object title, uid, folderTitle | Format-Table -AutoSize },
    { (Gf '/api/prometheus/grafana/api/v1/rules').data.groups | ForEach-Object { $_.rules } |
        Select-Object name, state, health, lastEvaluation | Format-Table -AutoSize -Wrap }
)
Ev '12_kustomize_ambientes.txt' @(
    { 'demo:'; kubectl kustomize k8s/overlays/demo | Select-String -Pattern 'SIM_ANOMALIA_CADA_MIN|schedule:|replicas:' },
    { 'dev:';  kubectl kustomize k8s/overlays/dev  | Select-String -Pattern 'SIM_ANOMALIA_CADA_MIN|schedule:|replicas:' }
)

# Punto F: consultas de negocio y catálogo, ejecutadas dentro del pod contra la base del clúster
function PsqlArchivo([string]$ruta) {
    Get-Content $ruta -Raw -Encoding UTF8 |
        kubectl exec -i -n $NS postgres-0 -- sh -c 'psql -U $POSTGRES_USER -d $POSTGRES_DB -P pager=off -e'
}
Ev '13_consultas_negocio.txt' @( { PsqlArchivo 'sql/03_consultas_negocio.sql' } )
Ev '14_catalogo_bd.txt'       @( { PsqlArchivo 'sql/04_catalogo_dbeaver.sql' } )

if (-not $SinDemos) {
    Write-Host "`n==> Demostración 1: se borra el pod de PostgreSQL y los datos siguen ahí" -ForegroundColor Cyan
    Ev '15_demo_postgres.txt' @(
        { kubectl get pod postgres-0 -n $NS -o custom-columns='POD:.metadata.name,UID:.metadata.uid,INICIO:.status.startTime,PVC:.spec.volumes[0].persistentVolumeClaim.claimName' },
        { Psql $CONTEO },
        { kubectl delete pod postgres-0 -n $NS },
        { Start-Sleep 5; kubectl wait --for=condition=ready pod/postgres-0 -n $NS --timeout=240s },
        { kubectl get pod postgres-0 -n $NS -o custom-columns='POD:.metadata.name,UID:.metadata.uid,INICIO:.status.startTime,PVC:.spec.volumes[0].persistentVolumeClaim.claimName' },
        { Psql $CONTEO }
    )

    Write-Host "==> Demostración 2: se borra el pod de Grafana y vuelve con su tablero" -ForegroundColor Cyan
    Ev '16_demo_grafana.txt' @(
        { kubectl get pods -l app=grafana -n $NS -o wide },
        { kubectl delete pod -l app=grafana -n $NS },
        { kubectl rollout status deployment/grafana -n $NS --timeout=240s },
        { kubectl get pods -l app=grafana -n $NS -o wide },
        { EsperarGrafana; Gf '/api/search?type=dash-db' | Select-Object title, uid, folderTitle | Format-Table -AutoSize },
        { Gf '/api/datasources' | Select-Object name, type, uid | Format-Table -AutoSize },
        { Gf '/api/v1/provisioning/alert-rules' | Select-Object title, uid, for | Format-Table -AutoSize }
    )

    Write-Host "==> Bonificación: escalar Grafana a 2 réplicas y volver a 1" -ForegroundColor Cyan
    Ev '17_escalar.txt' @(
        { kubectl scale deployment grafana -n $NS --replicas=2 },
        { kubectl rollout status deployment/grafana -n $NS --timeout=240s },
        { kubectl get pods -l app=grafana -n $NS -o wide },
        { kubectl get endpointslices -n $NS -l kubernetes.io/service-name=grafana },
        { kubectl scale deployment grafana -n $NS --replicas=1 },
        { kubectl rollout status deployment/grafana -n $NS --timeout=240s }
    )
    EsperarGrafana
}

Ev '18_estado_final.txt' @(
    { kubectl get all,pvc -n $NS -o wide },
    { kubectl get events -n $NS --sort-by=.lastTimestamp | Select-Object -Last 40 }
)
Write-Host "`nListo: evidencias en $OUT" -ForegroundColor Green
