<#
  Taller 6 · Verifica SHA-256 y descomprime la capa Bronze (Windows, sin instalar nada).
  Coloque en taller6\data\bronze\ los archivos descargados de Zenodo:
      opencem-v1.0.0.sqlite.zst   opencem-v1.0.0-SHA256SUMS.txt   opencem-v1.0.0-support.zip
  Ejecuta scripts/preparar_bronze.sh dentro de un contenedor alpine:3.20 (sha256sum + zstd).
  Evidencia para el informe: docs\evidencia_checksum.txt
#>
$ErrorActionPreference = 'Continue'
Set-Location (Split-Path $PSScriptRoot -Parent)
$bronze  = (Resolve-Path data/bronze).Path
$scripts = (Resolve-Path scripts).Path
docker run --rm -v "${bronze}:/d" -v "${scripts}:/s:ro" alpine:3.20 sh /s/preparar_bronze.sh /d |
    Tee-Object -FilePath docs/evidencia_checksum.txt
if ($LASTEXITCODE -ne 0) { Write-Host 'La verificación o la descompresión falló.' -ForegroundColor Red; exit 1 }
