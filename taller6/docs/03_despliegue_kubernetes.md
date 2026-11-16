# 3 · Despliegue: Docker + Kubernetes (K)

## 3.1 Contenedores (K.1)

| Imagen | Base | Tamaño aprox. | Justificación |
|---|---|---|---|
| `microrred-etl:1.0.0` (propia) | `python:3.12-slim-bookworm` | 402 MB (93 MB comprimida en el nodo) | Debian recortado. pandas y psycopg traen ruedas para glibc; en alpine (musl) habría que compilarlas, y la imagen y la construcción crecerían. Corre como usuario 10001, no como root |
| `microrred-simulador:1.0.0` (propia) | `python:3.12-slim-bookworm` | 205 MB (51 MB comprimida) | Solo psycopg. Comparte capas con el ETL en la caché del nodo |
| `postgres:16.9` | oficial | 643 MB (160 MB comprimida) | Versión fija (nunca `latest`) |
| `grafana/grafana:12.2.0` | oficial | 975 MB (204 MB comprimida) | Versión fija |

Tamaños medidos con `docker images` en el equipo del autor y, entre paréntesis, con `crictl images` dentro del nodo kind (`docs/evidencias/02_imagenes.txt`). De los 402 MB del ETL, 169 MB son pandas, numpy y psycopg; el resto es la base Debian slim con Python.

`docker-compose.yml` sirve para el desarrollo local con los mismos archivos de configuración que
el clúster (`k8s/base/...`).

## 3.2 Clúster local (K.2)

**Distribución: kind** (Kubernetes IN Docker), versión del nodo fija en `kindest/node:v1.33.1`.

| Opción | Por qué no / por qué sí |
|---|---|
| **kind** ✔ | Usa el mismo Docker Desktop del taller anterior. El clúster se crea y se destruye en segundos (`up`/`down`) y queda descrito en un archivo versionado (`k8s/kind-config.yaml`) con puertos y carpetas montadas |
| Kubernetes de Docker Desktop | Una casilla en la interfaz: no se puede versionar ni recrear con un comando |
| minikube | Más pesado (VM o driver extra) en Windows |
| k3d | Equivalente a kind; se prefirió kind por ser el proyecto oficial de SIG Testing |

**Cómo llegan las imágenes propias al clúster:** no hay registro. `docker build` las crea en el
Docker del anfitrión y `kind load docker-image microrred-etl:1.0.0 microrred-simulador:1.0.0`
las copia a la caché de containerd del nodo. Los pods usan `imagePullPolicy: IfNotPresent`, así
que nunca intentan descargarlas.

**Cómo llega la Bronze (4,4 GB):** no viaja en la imagen. `kind-config.yaml` monta
`./data/bronze` en el nodo (`extraMounts`, solo lectura) y el Job la ve por un volumen
`hostPath`.

## 3.3 Objetos de Kubernetes por necesidad (K.3)

| Necesidad | Objeto elegido | Por qué ese y no otro |
|---|---|---|
| Aislar el proyecto | `Namespace microrred` | Todo se lista, se limita y se borra en bloque. Las alternativas (etiquetas en `default`) no aíslan nombres ni permisos |
| BD que no pierda datos | **`StatefulSet postgres`** + `volumeClaimTemplates` (PVC `data-postgres-0`, 5 Gi, StorageClass `standard`) | Un Deployment con PVC funcionaría con 1 réplica, pero el StatefulSet garantiza identidad estable (`postgres-0`) y que el pod recreado monte **su mismo** volumen |
| Grafana siempre disponible, con tablero y fuente al iniciar | **`Deployment grafana`** + ConfigMaps de *provisioning* (datasource, proveedor de tableros, tablero JSON, reglas de alerta) | Grafana queda sin estado: todo lo importante está en Git. Un pod nuevo vuelve idéntico. No necesita PVC |
| Credenciales fuera del código | **`Secret microrred-credenciales`** creado por `scripts/up` desde `credenciales.env` (ignorado por Git). Solo se versiona `secret.example.yaml` | Un Secret en YAML dentro del repo expondría las claves (base64 no es cifrado). Alternativas de producción: Sealed Secrets o External Secrets |
| Configuración separada del código | **`ConfigMap microrred-parametros`** generado por Kustomize desde `parametros.env` (umbrales, intervalos, tarifa, zona horaria) | Cambiar un umbral = editar el archivo + `kubectl apply -k`, sin reconstruir imágenes. El simulador lo lee en su siguiente corrida |
| Comunicación por nombre | **`Service postgres`** (headless, que exige el StatefulSet) → DNS `postgres.microrred.svc.cluster.local` | La IP del pod cambia al recrearlo; el nombre del Service no |
| Carga histórica | **`Job etl-historico`** (`backoffLimit: 2`, `restartPolicy: Never`) con `initContainer` que espera a PostgreSQL | Corre una vez y queda `Completed` con sus logs. Un Deployment lo reiniciaría para siempre |
| Datos nuevos periódicos | **`CronJob simulador`** (`* * * * *`, `concurrencyPolicy: Forbid`) | Kubernetes maneja el reloj, los reintentos y el historial. Un Deployment con `sleep` ocuparía recursos todo el tiempo y no dejaría historial por corrida |
| Saber si un servicio está sano | `readinessProbe` y `livenessProbe`: `pg_isready` (exec) en PostgreSQL y `GET /api/health` en Grafana | Readiness saca el pod del Service mientras arranca; liveness lo reinicia si se cuelga |
| No agotar el equipo | `resources.requests/limits` en **todos** los contenedores (incluidos el initContainer y el CronJob) | Suma de límites ≈ 3,9 CPU y 5,7 GiB (el ETL, 4 GiB, solo durante la carga: pico medido de 2,6 GB); cabe en un portátil de 16 GB |
| Acceso desde el anfitrión | **`Service NodePort`** (`postgres-externo` 30432, `grafana` 30300) + `extraPortMappings` de kind → `127.0.0.1:55432` y `127.0.0.1:3001` | Power BI y DBeaver corren en Windows. `kubectl port-forward` también sirve, pero muere al cerrar la terminal; el NodePort queda fijo y versionado |

## 3.4 Reproducibilidad y resiliencia (K.4)

```powershell
cd taller6
copy credenciales.env.example credenciales.env     # editar claves
.\scripts\up.ps1          # un comando: clúster + imágenes + manifiestos + espera al ETL
.\scripts\down.ps1        # un comando: borra todo (clúster, pods, volúmenes)
```

Demostración en vivo:

```powershell
# 1. PostgreSQL pierde el pod pero no los datos
kubectl exec -n microrred postgres-0 -- psql -U microrred -d microrred -c "select count(*) from gold.fact_energia_hora"
kubectl delete pod postgres-0 -n microrred
kubectl get pods -n microrred -w                     # vuelve postgres-0 con el MISMO PVC
kubectl exec -n microrred postgres-0 -- psql -U microrred -d microrred -c "select count(*) from gold.fact_energia_hora"

# 2. Grafana vuelve con su tablero sin configurar nada
kubectl delete pod -n microrred -l app=grafana
kubectl rollout status deployment/grafana -n microrred   # abrir http://127.0.0.1:3001

# 3. Cambiar un umbral sin reconstruir la imagen
#    editar k8s/base/parametros.env (p. ej. SIM_ANOMALIA_CADA_MIN=10) o el número de reglas.yaml
kubectl apply -k k8s/overlays/demo

# 4. Disparar la alerta de "sin datos": pausar el simulador
kubectl patch cronjob simulador -n microrred -p '{\"spec\":{\"suspend\":true}}'
#    … a los ~6 min la alerta pasa a Firing. Reanudar con "suspend":false
```

Evidencias para el informe: `.\scripts\evidencias.ps1` ejecuta `kubectl get` y `kubectl describe`
de todos los objetos, las consultas de negocio, el catálogo de la base, las dos demostraciones de
resiliencia (borrar los pods de PostgreSQL y de Grafana) y el escalado de Grafana, y guarda cada salida
en `docs/evidencias/*.txt`. El informe PDF las incluye tal cual.

## 3.5 Bonificaciones

- **Escalar:** `kubectl scale deployment grafana -n microrred --replicas=2` funciona porque Grafana
  no tiene estado propio. Con alertas en alta disponibilidad habría que configurar
  `unified_alerting.ha_peers` y una base compartida para las sesiones. **PostgreSQL no se escala
  igual:** cada réplica de un StatefulSet tendría su propio PVC con datos distintos. Escalar una
  base exige replicación (primario + réplicas de lectura con streaming replication, o un
  operador como CloudNativePG), no solo más pods.
- **Kustomize con dos ambientes:** `k8s/overlays/dev` (menos recursos, simulador cada 2 min, sin
  anomalías) y `k8s/overlays/demo` (un episodio de batería baja de 6 min cada 15 min para que la alerta se dispare en vivo).
- **Rolling update y rollback del simulador:** construir `microrred-simulador:1.0.1`, cargarlo con
  `kind load`, luego `kubectl set image cronjob/simulador simulador=microrred-simulador:1.0.1 -n microrred`.
  Para revertir: `kubectl rollout undo` aplica a Deployments. En un CronJob se vuelve a la imagen
  anterior con el mismo `set image` o con `kubectl apply -k` desde Git.
