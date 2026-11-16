# Taller 6 · BI contenerizado y orquestado para una microrred híbrida (solar + batería + red)

> *"From inverter telemetry to actionable insights: a containerized, Kubernetes-orchestrated BI
> pipeline for a hybrid microgrid."*

| | |
|---|---|
| **Autores** | Cristian David López Cardona · Sebastian Pineda |
| **Curso** | Inteligencia de Negocios · Grupo 01 · 2026-II · Docente Ramiro Grisales Montoya |
| **Institución** | Institución Universitaria Pascual Bravo · Departamento de Sistemas Digitales |
| **Repositorio** | <https://github.com/Cat0428/solarbi-lopez-cardona> (carpeta `taller6/`) |
| **Stack** | PostgreSQL 16.9 · Python 3.12 (pandas, psycopg 3) · Grafana 12.2.0 · Power BI · Docker · kind (Kubernetes 1.33) · Kustomize |

## Arquitectura

```
Bronze (SQLite, solo lectura)                      clúster kind · namespace microrred
data/bronze/opencem-v1.0.0.sqlite ──hostPath──►  Job etl-historico ──► StatefulSet postgres (PVC)
                                                     R1–R7, C1–C4            silver.lectura_1min (1 min)
                                                                             silver.contexto (JSONB)
                                    CronJob simulador (cada min) ──────►    gold.* (estrella, 3 hechos)
                                                                             ops.* (linaje, conciliación)
                                                                                   │
                         Grafana (Deployment, provisioning) ◄── bi_lector ────────┤
                         http://127.0.0.1:3001                                     │
                         Power BI / DBeaver (Windows) ◄── NodePort 127.0.0.1:55432 ┘
```

Diagrama completo con los objetos de Kubernetes: [`docs/04_arquitectura_analisis_etica.md`](docs/04_arquitectura_analisis_etica.md).

## Estructura

```
taller6/
├── README.md
├── docker-compose.yml          desarrollo local (mismos archivos de configuración que el clúster)
├── credenciales.env.example    plantilla → copiar a credenciales.env (NO se versiona)
├── etl/                        Dockerfile · run_etl.py · inventario.py · bronze_desde_github.py
├── simulador/                  Dockerfile · simulador.py (streaming simulado)
├── sql/                        01_ddl.sql · 02_gold.sql · 03_consultas_negocio.sql · 04_catalogo_dbeaver.sql
├── k8s/
│   ├── kind-config.yaml        clúster de 1 nodo, puertos y carpeta Bronze
│   ├── base/                   namespace, postgres, grafana, Job, CronJob, kustomization
│   │   ├── parametros.env      umbrales e intervalos (ConfigMap)
│   │   ├── postgres-init/      rol bi_lector y esquemas
│   │   └── grafana/            datasource, tablero JSON, reglas de alerta (provisioning)
│   └── overlays/{dev,demo}/    ambientes con Kustomize
├── scripts/                    up / down / preparar_bronze (.ps1 y .sh) · evidencias.ps1
├── powerbi/                    proyecto .pbip (formato de texto, apto para Git)
└── docs/                       diagnóstico, indicadores, modelo, diccionario, K8s, ética, guía,
                                evidencias/ (salidas de kubectl) e informe/ (PDF y su generador)
```

## Requisitos del equipo anfitrión

- Windows 10/11 con **Docker Desktop** (WSL 2), 16 GB de RAM recomendados (el clúster limita a ~4 GB).
- **kind** ≥ 0.29 y **kubectl** ≥ 1.33 en el PATH (`winget install Kubernetes.kind Kubernetes.kubectl`).
- Power BI Desktop y DBeaver (para el consumo).
- ~8 GB libres en disco: la Bronze oficial ocupa 4,4 GB descomprimida, más imágenes y volúmenes.

## Reproducir desde cero

```powershell
git clone https://github.com/Cat0428/solarbi-lopez-cardona.git
cd solarbi-lopez-cardona\taller6
copy credenciales.env.example credenciales.env        # cambiar las contraseñas
```

**1. Capa Bronze.** Descargue de Zenodo (<https://zenodo.org/records/21436223>) a `data\bronze\`
los archivos `opencem-v1.0.0.sqlite.zst` (302 MB; se descomprime a 4,44 GB),
`opencem-v1.0.0-SHA256SUMS.txt` y `opencem-v1.0.0-support.zip` (diccionario de columnas y
validación oficial). Después ejecute:

```powershell
.\scripts\preparar_bronze.ps1     # verifica SHA-256 y descomprime con zstd (en un contenedor alpine)
```

*Plan B si Zenodo no está disponible:* reconstruir la base desde la exportación CSV pública:

```powershell
git clone --depth 1 https://github.com/OpenCEM-platform/opencem-dataset ..\..\opencem-dataset
python etl\bronze_desde_github.py ..\..\opencem-dataset data\bronze\opencem-github.sqlite
```

El ETL usa `opencem-v1.0.0.sqlite` si existe y, si no, `opencem-github.sqlite`.

**2. Levantar todo con un comando:**

```powershell
.\scripts\up.ps1            # crea el clúster, construye y carga las imágenes, aplica manifiestos y espera el ETL
```

**3. Consumir:**
- Grafana: <http://127.0.0.1:3001> (usuario y clave de `credenciales.env`) → carpeta *Microrred*.
- DBeaver / Power BI: servidor `127.0.0.1:55432`, base `microrred`, usuario `bi_lector`, sin SSL.
- Consultas de negocio: [`sql/03_consultas_negocio.sql`](sql/03_consultas_negocio.sql).
- DBeaver paso a paso (conexiones de administración y de consulta, DDL, diagrama ER, evidencias
  y guion de la sustentación): [`docs/05_dbeaver.md`](docs/05_dbeaver.md); evidencias del punto F en
  [`sql/04_catalogo_dbeaver.sql`](sql/04_catalogo_dbeaver.sql).

**4. Eliminar todo con un comando:** `.\scripts\down.ps1`

**5. Informe de Power BI:** abrir `powerbi\microrred.pbip`. Si el servidor no es `127.0.0.1:55432`,
cambiarlo en *Transformar datos → Parámetros* (`Servidor`, `BaseDatos`). Credenciales: tipo *Base de
datos*, usuario `bi_lector`. Luego *Actualizar*.

| Página | Pregunta que responde |
|---|---|
| 1 · Resumen ejecutivo | ¿Cuánta energía aporta el sol, cuánto se compra y cuánto cuesta? (texto dinámico con el hallazgo) |
| 2 · Configuración (SCD2) | ¿Por qué la red aporta tanto? Desempeño por versión de configuración del inversor |
| 3 · Perfil horario | ¿A qué hora se compra energía? Franja × inversor |
| 4 · Eventos | Batería baja, apagados, cortes de red, pérdida de comunicación y fallas del inversor |
| 5 · Cargas (contexto) | ¿Qué tareas explican el consumo y en qué franja ocurren? |
| 6 · Económico | Costo de la red y ahorro solar con tarifa simulable (what-if 700–1 300 COP/kWh) |
| 7 · Calidad de datos | Reglas del ETL y conciliación contra el contador del inversor |

Modelo: 10 tablas importadas de PostgreSQL, 11 relaciones en estrella, 4 jerarquías, `dim_fecha`
marcada como tabla de fechas, 37 medidas DAX en carpetas (energía, KPI, calidad, eventos,
económico, tiempo), incluidas comparaciones entre periodos (`DATEADD`) y acumulados.
Las siete páginas tienen navegador de páginas, segmentadores de mes e inversor y profundización
(mes → día, franja → hora, categoría → tipo de evento).

**Por qué `.pbip`:** el modelo queda en TMDL y el informe en PBIR (un JSON por página y por visual).
Son archivos de texto: Git muestra el cambio de una medida o de un visual línea a línea y se pueden
revisar y fusionar. Un `.pbix` es un binario comprimido que Git solo puede reemplazar entero. La caché
de datos (`.pbi/cache.abf`) y la configuración local quedan fuera del repositorio.

*Sin Kubernetes (desarrollo):* `docker compose up -d --build` y luego `docker compose run --rm etl`.

## Resultados del ETL (base oficial `opencem-v1.0.0.sqlite`, checksum verificado)

| | |
|---|---|
| Lecturas leídas → válidas | 2 989 759 → 2 919 079 (**97,64 % válidas**; 70 665 fotos vacías o incompletas) |
| `silver.lectura_1min` | 782 217 minutos (12/07/2025 → 13/07/2026) |
| `gold.fact_energia_hora` · `fact_evento` · `fact_actividad` | 17 010 · 24 458 · 25 178 filas |
| `gold.dim_inversor` (SCD2 desde `settings`) | 5 versiones de configuración |
| Conciliación Silver ↔ Gold | 0 lecturas de diferencia; < 0,01 kWh en energía |
| Conciliación con los contadores del inversor | ±1 % (inv. 2) y ±3 % (inv. 1) en meses completos |
| Idempotencia | ETL → simulador → ETL: mismas firmas MD5 en Gold |
| Tiempo y memoria | ~1 min · pico de 2,6 GB |

Detalle de cada regla, conteos antes y después, y criterio dato inválido / evento operativo:
[`docs/01_fuente_y_calidad.md`](docs/01_fuente_y_calidad.md).

## Documentación del informe

| Sección del enunciado | Documento |
|---|---|
| A, E · Fuente, calidad, ETL, conciliación, idempotencia | [`docs/01_fuente_y_calidad.md`](docs/01_fuente_y_calidad.md) · [`docs/inventario_bronze.md`](docs/inventario_bronze.md) (oficial, con checksums) · [`docs/inventario_bronze_github.md`](docs/inventario_bronze_github.md) (fuente complementaria) |
| A, B, C, D, F · Usuarios, indicadores, modelo, bus matrix, SCD, diccionario, índices | [`docs/02_indicadores_modelo_diccionario.md`](docs/02_indicadores_modelo_diccionario.md) |
| F · DBeaver: DDL, diagrama ER, restricciones, índices, consultas y evidencias | [`docs/05_dbeaver.md`](docs/05_dbeaver.md) · [`sql/04_catalogo_dbeaver.sql`](sql/04_catalogo_dbeaver.sql) |
| K · Docker, kind, objetos de Kubernetes, demostraciones | [`docs/03_despliegue_kubernetes.md`](docs/03_despliegue_kubernetes.md) |
| I, J · Arquitectura, Power BI vs Grafana, Modbus/SCADA, Ley 1581, seguridad, hallazgos | [`docs/04_arquitectura_analisis_etica.md`](docs/04_arquitectura_analisis_etica.md) |
| Informe PDF del taller (secciones A–K, capturas y evidencias del clúster) | [`docs/informe/BI_Taller6_Lopez_Cardona.pdf`](docs/informe/BI_Taller6_Lopez_Cardona.pdf) · se regenera con `python docs/informe/construir_informe.py` |
| Evidencias del clúster (`kubectl get`/`describe`, demostraciones) | [`docs/evidencias/`](docs/evidencias/) · las genera `.\scripts\evidencias.ps1` |
| Guía para correr la solución en vivo y guion de la sustentación | [`docs/06_guia_sustentacion.md`](docs/06_guia_sustentacion.md) |

## Datos y licencia

Los datos se publican bajo licencia **CC BY 4.0**. No se suben al repositorio: se descargan de
Zenodo y se verifican con SHA-256.

**Cita obligatoria:**

Bartels, T. S., Wu, R., Lu, X., Chen, Y., Lu, Y., Xia, F., Yang, H., Chen, Y., & Li, T. (2026).
*OpenCEM: Multimodal photovoltaic and battery microgrid dataset with context records and sky
imagery* (Version 1.0.0) [Dataset]. Zenodo. https://doi.org/10.5281/zenodo.21436223

Artículo de los autores: Bartels, T. S. et al. (2026). *Bridging Natural Language and Microgrid
Dynamics: A Context-Aware Simulator and Dataset*. arXiv:2604.05429.
Exportación CSV complementaria: <https://github.com/OpenCEM-platform/opencem-dataset>.
