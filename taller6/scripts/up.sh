#!/usr/bin/env bash
# Taller 6 · Levanta toda la solución desde cero (Linux/macOS/Git Bash):  ./scripts/up.sh [demo|dev]
set -euo pipefail
cd "$(dirname "$0")/.."
AMB="${1:-demo}"; CLUSTER=microrred; NS=microrred
IMG_ETL=microrred-etl:1.0.0; IMG_SIM=microrred-simulador:1.0.0
[ -f credenciales.env ] || { echo "Falta credenciales.env"; exit 1; }
ls data/bronze/*.sqlite >/dev/null 2>&1 || { echo "Falta la base .sqlite (scripts/preparar_bronze.sh)"; exit 1; }
# Compose usa los mismos puertos (55432 y 3001): se detiene antes (sin -v, conserva su volumen)
[ -n "$(docker compose ps -q 2>/dev/null)" ] && docker compose down
# kind recibe la carpeta Bronze con ruta absoluta (copia temporal de la configuración)
if ! kind get clusters 2>/dev/null | grep -qx "$CLUSTER"; then
  CFG="$(mktemp)"; sed "s#hostPath: ./data/bronze#hostPath: \"$(pwd)/data/bronze\"#" k8s/kind-config.yaml > "$CFG"
  kind create cluster --config "$CFG"
fi
docker build -f etl/Dockerfile -t "$IMG_ETL" .
docker build -f simulador/Dockerfile -t "$IMG_SIM" .
kind load docker-image "$IMG_ETL" "$IMG_SIM" --name "$CLUSTER"
# Imágenes oficiales al nodo (opcional: si falla, el nodo las descarga de Docker Hub)
for img in postgres:16.9 grafana/grafana:12.2.0; do
  docker image inspect "$img" >/dev/null 2>&1 || docker pull "$img" || true
  kind load docker-image "$img" --name "$CLUSTER" || echo "  (no se pudo copiar $img; el nodo la descargará)"
done
kubectl apply -f k8s/base/namespace.yaml
kubectl create secret generic microrred-credenciales -n "$NS" --from-env-file=credenciales.env \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -k "k8s/overlays/$AMB"
kubectl rollout status statefulset/postgres -n "$NS" --timeout=240s
kubectl rollout status deployment/grafana -n "$NS" --timeout=240s
kubectl wait --for=condition=complete job/etl-historico -n "$NS" --timeout=1800s
kubectl logs job/etl-historico -n "$NS" --tail=40
kubectl get all,pvc -n "$NS"
echo "Grafana: http://127.0.0.1:3001 · PostgreSQL: 127.0.0.1:55432"
