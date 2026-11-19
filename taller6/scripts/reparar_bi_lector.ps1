<#
  Taller 6 · Diagnostica y repara la conexión del rol de solo lectura bi_lector (DBeaver / Power BI).

      .\scripts\reparar_bi_lector.ps1

  1. Lee BI_LECTOR_PASSWORD de credenciales.env (no la imprime).
  2. Si el Secret del clúster tiene otra clave, lo vuelve a crear desde credenciales.env.
  3. Le asigna esa clave al rol bi_lector dentro de PostgreSQL (ALTER ROLE; la clave viaja por stdin).
  4. Prueba el ingreso de bi_lector por TCP dentro del pod y revisa que el puerto 55432 responda en el equipo.
#>
$ErrorActionPreference = 'Continue'
$OutputEncoding = New-Object System.Text.UTF8Encoding $false   # lo que se envía por stdin a kubectl
Set-Location (Split-Path $PSScriptRoot -Parent)
$NS = 'microrred'

function Ok([string]$t)  { Write-Host "  OK  $t" -ForegroundColor Green }
function Mal([string]$t) { Write-Host "  !!  $t" -ForegroundColor Red }

# 1. Clave de credenciales.env
$cred = @{}
Get-Content credenciales.env -Encoding UTF8 | ForEach-Object {
    if ($_ -match '^\s*([A-Z_]+)\s*=\s*(.*?)\s*$') { $cred[$Matches[1]] = $Matches[2] }
}
$pw = $cred['BI_LECTOR_PASSWORD']
Write-Host "`n1) credenciales.env"
if (-not $pw) { Mal 'No hay BI_LECTOR_PASSWORD en credenciales.env'; exit 1 }
Ok "BI_LECTOR_PASSWORD tiene $($pw.Length) caracteres"

# 2. Secret del clúster
Write-Host "`n2) Secret microrred-credenciales"
$b64 = kubectl get secret microrred-credenciales -n $NS -o jsonpath='{.data.BI_LECTOR_PASSWORD}' 2>$null
$enSecret = if ($b64) { [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($b64)) } else { '' }
if ($enSecret -ceq $pw) { Ok 'El Secret tiene la misma clave que credenciales.env' }
else {
    Mal 'El Secret tiene otra clave: se vuelve a crear desde credenciales.env'
    kubectl create secret generic microrred-credenciales -n $NS --from-env-file=credenciales.env `
        --dry-run=client -o yaml | kubectl apply -f -
}

# 3. El rol bi_lector existe y recibe la clave de credenciales.env
Write-Host "`n3) Rol bi_lector en PostgreSQL"
$existe = "SELECT count(*) FROM pg_roles WHERE rolname = 'bi_lector';" |
    kubectl exec -i -n $NS postgres-0 -- sh -c 'psql -U $POSTGRES_USER -d $POSTGRES_DB -tA'
if ("$existe".Trim() -eq '1') { Ok 'El rol bi_lector existe' }
else { Mal "No existe el rol bi_lector (respuesta: $existe). Haga .\scripts\down.ps1 y .\scripts\up.ps1"; exit 1 }

$lit = $pw.Replace("'", "''")
$res = "ALTER ROLE bi_lector WITH LOGIN PASSWORD '$lit';" |
    kubectl exec -i -n $NS postgres-0 -- sh -c 'psql -U $POSTGRES_USER -d $POSTGRES_DB -tA' 2>&1
if ("$res" -match 'ALTER ROLE') { Ok 'Clave de bi_lector actualizada con la de credenciales.env' }
else { Mal "No se pudo actualizar la clave: $res"; exit 1 }

# 4a. Ingreso real de bi_lector por TCP (como entra DBeaver), dentro del pod
Write-Host "`n4) Prueba de ingreso"
$quien = $pw | kubectl exec -i -n $NS postgres-0 -- sh -c 'read p; p=$(echo $p | tr -d \\r); PGPASSWORD=$p psql -h 127.0.0.1 -U bi_lector -d $POSTGRES_DB -tAc select\ current_user' 2>&1
if ("$quien".Trim() -eq 'bi_lector') { Ok 'bi_lector entra con la clave de credenciales.env' }
else { Mal "bi_lector no pudo entrar: $quien" }

# 4b. El puerto que usa DBeaver en el equipo
$t = Test-NetConnection 127.0.0.1 -Port 55432 -WarningAction SilentlyContinue
if ($t.TcpTestSucceeded) { Ok 'El puerto 127.0.0.1:55432 responde (NodePort del clúster)' }
else { Mal 'El puerto 55432 no responde: revise que el clúster esté arriba (kubectl get svc -n microrred)' }

Write-Host "`nEn DBeaver: Host 127.0.0.1 · Puerto 55432 · Base microrred · Usuario bi_lector ·" -ForegroundColor Cyan
Write-Host "Contraseña = el valor de BI_LECTOR_PASSWORD en credenciales.env (copiar y pegar)." -ForegroundColor Cyan
