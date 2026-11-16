# Guía para correr la solución en vivo y para la sustentación

Todo se ejecuta en **PowerShell** desde la carpeta `taller6`:

```powershell
cd "C:\Users\Cristian Lopéz\Desktop\Universidad2026-2\Inteligencia_de_Negocios_BI\solarbi-López-Cardona\taller6"
```

El enunciado exige presentar **solo** con: terminal con `kubectl`, DBeaver, Power BI, Grafana, GitHub
y el PDF. Nada se crea a mano en el clúster ni se configura Grafana desde la interfaz: todo cambio
se hace en un archivo versionado y se aplica con `kubectl apply -k`.

---

## 1. El día anterior (ensayo completo)

| # | Qué hacer | Comando o acción | Cómo saber que quedó bien |
|---|---|---|---|
| 1 | Docker Desktop encendido, con al menos 6 GB de memoria para WSL | Docker Desktop → *Settings → Resources* | `docker info` responde |
| 2 | kind y kubectl instalados | `kind version` · `kubectl version --client` | Muestran versión (si no: `winget install Kubernetes.kind Kubernetes.kubectl`) |
| 3 | Imágenes base descargadas de antemano (por si el wifi de la universidad falla) | `docker pull kindest/node:v1.33.1`, `docker pull postgres:16.9`, `docker pull grafana/grafana:12.2.0`, `docker pull python:3.12-slim-bookworm` | Aparecen en `docker images` |
| 4 | Bronze en su lugar | `dir data\bronze\opencem-v1.0.0.sqlite` | 4 439 408 640 bytes |
| 5 | Ensayo de punta a punta (cronometrarlo: en el equipo del autor tarda unos 5–8 min, de los cuales el ETL son ~2,5) | `.\scripts\down.ps1` y luego `.\scripts\up.ps1` | Termina con "Listo." y el resumen del ETL |
| 6 | DBeaver con las dos conexiones (*Microrred · consulta (bi_lector)* y *Microrred · administración (microrred)*, ya creadas en el espacio de trabajo `C:\Users\Public\DBeaverWorkspace`, sin contraseñas guardadas) | Abrir **siempre** con `& "C:\Program Files\DBeaver\dbeaver.exe" -data "C:\Users\Public\DBeaverWorkspace"` (sin `-data` falla: intenta escribir en Program Files). Ver `docs/05_dbeaver.md` | Ambas conexiones quedan en verde con el clúster arriba; las claves se escriben al conectar (`credenciales.env`) |
| 7 | Power BI conectado | Abrir `powerbi\microrred.pbip` → *Actualizar* | Página 1 con 33,0 % de fracción solar |
| 8 | Grafana | Navegador → `http://127.0.0.1:3001` | Carpeta *Microrred* → tablero con datos del simulador |
| 9 | PDF y GitHub abiertos en pestañas | `docs\informe\BI_Taller6_Lopez_Cardona.pdf` y el repositorio | — |
| 10 | Dejar todo **abajo** para levantar desde cero en clase | `.\scripts\down.ps1` | `kind get clusters` no lista `microrred` |

> Si el aula no tiene buena red, el paso 3 es el que salva la presentación: `up.ps1` copia al nodo
> kind las imágenes que ya están en el equipo (`kind load docker-image`), así que no las descarga otra
> vez. Las imágenes propias (`microrred-etl`, `microrred-simulador`) se construyen con la capa base
> que ya está en caché.

---

## 2. Guion de la sustentación (≈ 20 minutos)

La historia que se cuenta: **"la planta tiene baterías, pero una configuración las dejó sin usar y se
está comprando a la red energía que el sol y la batería podían dar"**.

| Min | Bloque | Qué mostrar | Qué decir (idea central) |
|---|---|---|---|
| 0–1 | Problema | PDF, portada y sección 1 | Dos inversores híbridos, datos que nadie convierte en decisiones; dirección y mantenimiento necesitan cosas distintas; TI exige Kubernetes |
| 1–2 | **Levantar en vivo** | Terminal: `.\scripts\up.ps1` | "Un solo comando crea el clúster, construye y carga las imágenes, crea el Secret, aplica los manifiestos y espera al ETL." Mientras corre se sigue con la fuente |
| 2–5 | Fuente y calidad | PDF secciones 2 y 7 | Checksum verificado; 2,99 M lecturas; desbordes uint16, duplicados, fotos vacías, JSON mal formado; 97,64 % válidas; dato inválido ≠ evento real; Silver a 1 minuto (qué se gana y qué se pierde) |
| 5–7 | Kubernetes | Terminal: `kubectl get all,pvc -n microrred` | Un objeto por necesidad (tabla K.3): Namespace, StatefulSet + PVC, Deployment, Secret, ConfigMap, Service por nombre, Job, CronJob, sondas, límites, NodePort |
| 7–8 | ETL terminado | `kubectl logs job/etl-historico -n microrred --tail=30` | Conteos por regla, conciliación con el contador del inversor (±1 % y ±3 %), idempotencia |
| 8–10 | Modelo y base | DBeaver: diagrama de `gold`, Q2 (LAG) y Q7 (JSON) | Constelación con 3 procesos de negocio, grano declarado, `dim_inversor` SCD tipo 2 construida desde `settings` |
| 10–15 | **Power BI (historia)** | *Actualizar*; páginas 1 → 2 → 3 → 6 | P1: 79 % de la carga sale de la red. P2: el inversor 1 pasó de SBU a SOL el 29/08/2025 y su dependencia saltó de 0 % a 108 %. P3: la red se compra de noche y el sol sobra al mediodía. P6: mover la tarifa (what-if) |
| 15–17 | **Grafana en vivo** | `http://127.0.0.1:3001` (usuario y clave de `credenciales.env`); tablero; variable *Inversor*; panel *Alertas activas* | Los minutos del simulador llegan cada minuto. En el ambiente demo hay un episodio de batería baja de 6 min en los minutos **:00, :15, :30 y :45** de cada hora: el SOC del inversor 2 cae a 12 %, la alerta pasa a *Pending* y unos 2–3 min después a *Firing*; al terminar el episodio vuelve a *Normal*. **Planear este bloque para que caiga en uno de esos cuartos de hora** |
| 17–19 | Resiliencia | Sección 3 de esta guía | Borrar el pod de PostgreSQL (los datos siguen) y el de Grafana (vuelve con su tablero) |
| 19–20 | Recomendaciones | PDF sección 1 | 1) Volver a SBU (sin inversión). 2) No comprar paneles todavía. 3) Mover entrenamientos y compilaciones al mediodía. 4) Horario de apagado del aire en festivos. 5) Mantener la alerta de "sin datos" |

---

## 3. Demostraciones de Kubernetes (copiar y pegar)

```powershell
# Estado general
kubectl get all,pvc,configmap,secret -n microrred

# 1. PostgreSQL pierde el pod, no los datos
kubectl exec -n microrred postgres-0 -- psql -U microrred -d microrred -c "select count(*) from gold.fact_energia_hora"
kubectl delete pod postgres-0 -n microrred
kubectl get pods -n microrred -w            # Ctrl+C cuando postgres-0 esté 1/1 Running
kubectl exec -n microrred postgres-0 -- psql -U microrred -d microrred -c "select count(*) from gold.fact_energia_hora"

# 2. Grafana vuelve sola con su tablero, fuente y alertas
kubectl delete pod -n microrred -l app=grafana
kubectl rollout status deployment/grafana -n microrred
#    refrescar http://127.0.0.1:3001 → el tablero sigue ahí (viene de un ConfigMap, no de un disco)

# 3. Simular una caída de comunicación: la alerta "Inversor sin datos" se dispara en ~6 min
kubectl patch cronjob simulador -n microrred -p '{\"spec\":{\"suspend\":true}}'
kubectl patch cronjob simulador -n microrred -p '{\"spec\":{\"suspend\":false}}'   # reanudar

# 4. Ver el simulador trabajando
kubectl get jobs -n microrred --sort-by=.metadata.creationTimestamp
kubectl logs -n microrred job/<nombre-del-último-job>
```

(Si `credenciales.env` usa otro `POSTGRES_USER` o `POSTGRES_DB`, cambia `microrred` en el `psql`.)

---

## 4. Pedidos en vivo del docente

### "Cambie un umbral sin reconstruir la imagen"

| Umbral | Archivo | Aplicar | Qué pasa |
|---|---|---|---|
| SOC bajo de la alerta (20 %) | `k8s/base/grafana/alerting/reglas.yaml` → `params: [20]` | `kubectl apply -k k8s/overlays/demo` | El ConfigMap `grafana-alertas-<hash>` cambia de nombre, el Deployment se actualiza y Grafana arranca con la regla nueva |
| Frecuencia de los episodios de batería baja del simulador | `k8s/overlays/demo/kustomization.yaml` → `SIM_ANOMALIA_CADA_MIN` (y `SIM_ANOMALIA_DURACION_MIN` en `parametros.env`) | `kubectl apply -k k8s/overlays/demo` | El siguiente pod del CronJob (en menos de 1 min) lee el valor nuevo |
| SOC bajo, temperatura alta, hueco mínimo, tarifa del ETL | `k8s/base/parametros.env` | `kubectl apply -k k8s/overlays/demo` | Lo usa la siguiente corrida del ETL |

Comprobar: `kubectl get configmap microrred-parametros -n microrred -o yaml`.

> **Si hay que mostrar la alerta ya y no es un cuarto de hora:** cambiar en `k8s/overlays/demo/kustomization.yaml` `SIM_ANOMALIA_CADA_MIN=15` por `SIM_ANOMALIA_CADA_MIN=5` y aplicar con `kubectl apply -k k8s/overlays/demo`. El siguiente pod del simulador (menos de 1 min) ya usa el valor nuevo, sin reconstruir la imagen, y la alerta se dispara en pocos minutos. Es a la vez la demostración de "cambiar un parámetro sin reconstruir la imagen". Devolverlo a 15 al terminar.

### "Cree una medida DAX nueva" (Power BI → *Nueva medida*, en la tabla `_Medidas`)

```DAX
Energía solar mes anterior (kWh) =
CALCULATE ( [Energía solar (kWh)], DATEADD ( dim_fecha[fecha], -1, MONTH ) )

Energía de la red acumulada del año (kWh) =
TOTALYTD ( [Energía de la red (kWh)], dim_fecha[fecha] )

Autosuficiencia % =
DIVIDE ( [Energía solar (kWh)] + [Descarga de batería (kWh)], [Energía a la carga (kWh)] )

Ranking de meses por compra de red =
RANKX ( ALL ( dim_fecha[anio_mes] ), [Energía de la red (kWh)] )
```

Ponerla en una tarjeta o en la tabla de la página 2 y filtrar por inversor para mostrar que responde
al contexto.

### "Agregue un panel a Grafana"

**No** se crea desde la interfaz (el proveedor tiene `allowUiUpdates: false` y el enunciado no lo
califica). Se hace en el JSON versionado:

1. Abrir `k8s/base/grafana/tableros/microrred.json` y copiar el bloque del panel *Estado de carga (SOC)*.
2. Cambiar `id` (número nuevo), `title`, `gridPos.y` (debajo del último, p. ej. 31) y el `rawSql`, por ejemplo:

   ```sql
   SELECT ts AS "time", 'Inversor ' || inversor_id AS metric, temp_inversor_c AS value
   FROM silver.lectura_1min WHERE $__timeFilter(ts) AND inversor_id IN ($inversor) ORDER BY 1
   ```
3. `kubectl apply -k k8s/overlays/demo` y `kubectl rollout status deployment/grafana -n microrred`.
4. Refrescar Grafana: el panel aparece en todos los despliegues futuros porque está en Git.

### "Modifique una consulta"

Abrir `sql/03_consultas_negocio.sql` en DBeaver (conexión de consulta), cambiar el filtro o la
agregación (p. ej. en Q2 cambiar `inversor_id` o el periodo) y ejecutar con **Ctrl+Enter**.

### "Elimine un pod y explique qué pasa"

| Pod | Qué pasa | Por qué |
|---|---|---|
| `postgres-0` | Vuelve con el mismo nombre y monta el mismo PVC; los datos siguen | StatefulSet: identidad estable + `volumeClaimTemplates` |
| `grafana-…` | El ReplicaSet crea otro con nombre distinto; tablero, fuente y alertas vuelven solos | Deployment sin estado + provisioning desde ConfigMaps |
| Un pod del simulador | No pasa nada: el CronJob crea otro en el siguiente minuto | CronJob → Job → Pod efímero |
| El pod del Job `etl-historico` ya completado | Se pierden sus logs, pero la evidencia queda en `ops.etl_ejecucion` y `ops.etl_regla` | El Job ya terminó (`Completed`); no se vuelve a ejecutar solo |

### "Escale" (bonificación)

```powershell
kubectl scale deployment grafana -n microrred --replicas=2
kubectl get pods -n microrred -l app=grafana
kubectl scale deployment grafana -n microrred --replicas=1
```

PostgreSQL **no** se escala así: cada réplica del StatefulSet tendría su propio volumen con datos
distintos. Escalar una base requiere replicación (primario y réplicas de lectura con *streaming
replication*, o un operador como CloudNativePG).

---

## 5. Preguntas probables y respuesta corta

| Pregunta | Respuesta |
|---|---|
| ¿Por qué StatefulSet y no Deployment para PostgreSQL? | Identidad estable (`postgres-0`) y el pod recreado monta **su** PVC; con un Deployment, dos pods podrían competir por el mismo volumen durante un despliegue |
| ¿Por qué el Secret no está en el repositorio? | Un Secret en YAML solo está en base64, que no es cifrado. Se crea en el despliegue desde `credenciales.env` (ignorado por Git); solo se versiona la plantilla |
| ¿Cómo encuentran el ETL y Grafana a PostgreSQL? | Por el DNS del Service: `postgres.microrred.svc.cluster.local`. La IP del pod cambia; el nombre no |
| ¿Cómo llegan las imágenes propias al clúster? | `docker build` en el anfitrión y `kind load docker-image` las copia al nodo; `imagePullPolicy: IfNotPresent` evita que intente descargarlas |
| ¿Por qué kind? | Corre sobre Docker Desktop, se crea y se destruye en segundos y queda descrito en un archivo versionado (`k8s/kind-config.yaml`) con puertos y montajes |
| ¿Por qué la Silver es de 1 minuto? | Se gana volumen manejable (782 mil filas en vez de 3 millones) y series alineadas entre inversores; se pierde el detalle de picos de pocos segundos (por eso se guarda `carga_max_w`) |
| ¿Cómo distinguen un dato inválido de un evento real? | Inválido: físicamente imposible o con desbordes del registro (se corrige o descarta y se cuenta). Evento: valor posible pero fuera de lo deseado (SOC 6 %, red en 0 V): se conserva y se modela en `fact_evento` |
| ¿Qué indicador fotovoltaico no se puede calcular? | El *Performance Ratio*: requiere irradiancia en el plano del panel, que la fuente no trae. Propuesta: piranómetro o irradiancia satelital (y las imágenes de cielo del propio dataset) |
| ¿Es idempotente el ETL? | Sí: borra y recarga por rango dentro de una transacción; dos corridas seguidas dejan las mismas firmas MD5 en Gold |
| ¿Por qué Power BI y Grafana, y no uno solo? | Responden preguntas distintas: Grafana, "qué pasa ahora y hay que actuar" (cada 30 s, alertas); Power BI, "qué pasó, por qué y qué decidir" (modelo semántico, DAX, what-if) |
| ¿Qué pasa con la Ley 1581? | El contexto puede contener rutas de carpetas con nombres de usuario: se enmascaran (`/home/<usuario>`), se usa un rol de solo lectura y los datos personales no salen a los tableros |
| ¿Por qué .pbip? | Modelo en TMDL e informe en PBIR: texto que Git compara línea a línea; el `.pbix` es un binario |

---

## 6. Plan B

| Si pasa esto | Hacer esto |
|---|---|
| `up.ps1` falla al crear el clúster por puertos ocupados | `docker compose down` (el script ya lo intenta) y repetir |
| No hay internet y falta una imagen | Usar las imágenes descargadas el día anterior (paso 3 de la sección 1) |
| El ETL tarda más de lo esperado | Seguir con la explicación; `kubectl logs -f job/etl-historico -n microrred` muestra el avance |
| Power BI no conecta | Verificar `kubectl get svc postgres-externo -n microrred` (NodePort 30432) y que el parámetro `Servidor` sea `127.0.0.1:55432` |
| Grafana no muestra datos nuevos | `kubectl get cronjob simulador -n microrred` (que no esté suspendido) y revisar el log del último Job |

## 7. Al terminar

```powershell
.\scripts\down.ps1      # elimina el clúster completo (la Bronze en data\bronze no se toca)
```
