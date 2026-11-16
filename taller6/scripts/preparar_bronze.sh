#!/bin/sh
# Taller 6 · Verifica la integridad (SHA-256) de la descarga de Zenodo y descomprime la base.
#   ./scripts/preparar_bronze.sh            (Linux/macOS con sha256sum y zstd instalados)
#   .\scripts\preparar_bronze.ps1           (Windows: corre ESTE script dentro de un contenedor alpine)
# La salida queda en docs/evidencia_checksum.txt para el informe.
set -eu
BRONZE="${1:-$(dirname "$0")/../data/bronze}"
cd "$BRONZE"
[ -f /etc/alpine-release ] && apk add --no-cache zstd coreutils >/dev/null   # solo dentro de alpine (sha256sum de GNU)
echo "# Verificacion SHA-256 ($(date -Iseconds))"
sha256sum -c opencem-v1.0.0-SHA256SUMS.txt --ignore-missing
echo
echo "# Descompresion con $(zstd -V)"
echo "zstd -d -f opencem-v1.0.0.sqlite.zst -o opencem-v1.0.0.sqlite"
zstd -d -f opencem-v1.0.0.sqlite.zst -o opencem-v1.0.0.sqlite
echo
echo "# Base descomprimida contra manifests/release_manifest.json del support.zip"
echo "esperado:  5fe1f213a4a6804cdfc75f6173f437772c918f45dc0f127eb7e8936c2c2d9fbb  opencem-v1.0.0.sqlite"
printf 'calculado: '; sha256sum opencem-v1.0.0.sqlite
ls -l opencem-v1.0.0.sqlite*
