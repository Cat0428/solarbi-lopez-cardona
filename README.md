# SolarBI Pascual · Monitoreo operativo con Power BI y Grafana

> *"One governed dataset, two views: Grafana for real-time operations and Power BI for business decisions."*

| | |
|---|---|
| **Autor** | Cristian López Cardona (trabajo individual) |
| **Curso** | Inteligencia de Negocios · Grupo 01 · 2026-II |
| **Docente** | Ramiro Grisales Montoya |
| **Institución** | Institución Universitaria Pascual Bravo · Departamento de Sistemas Digitales |
| **Repositorio** | <https://github.com/Cat0428/solarbi-lopez-cardona> |

## Descripción

Trabajo de consulta y práctica guiada del proyecto de aula **SolarBI Pascual**. Con un enfoque de
**monitoreo operativo** (potencia en el tiempo y detección de fallas), se construyó un flujo pequeño
pero completo sobre la arquitectura medallón:

```
simulador.py ──► data/bronze/telemetria.csv      (Bronze: crudo, nunca se modifica)
                     │  run_etl.py · reglas R1 duplicados, R2 faltantes, R3 rango físico
                     ▼
                 data/silver/*.csv + silver.lectura_5min   (Silver: lecturas válidas cada 5 min)
                     │  sql/03_carga_gold.sql · UPSERT
                     ▼
                 dwh.fact_energia_dia + dimensiones        (Gold: esquema estrella diario)
                     │
          ┌──────────┴──────────┐
     Grafana (silver + dwh)   Power BI (dwh)
     operador de planta       directivos
```

## Estructura

```
├── README.md
├── docker-compose.yml        PostgreSQL 16 + Grafana OSS con todo preconfigurado
├── .env.example              plantilla de credenciales (copiar a .env)
├── requirements.txt
├── docs/                     PDF de la consulta
├── data/bronze/              telemetria.csv (crudo)
├── data/silver/              lectura_5min.csv, rechazos.csv, reporte_calidad.json
├── etl/                      simulador.py, run_etl.py
├── sql/                      01_ddl, 02_roles, 03_carga_gold, 04_verificacion, 05-06 alerta
├── powerbi/                  solarbi.pbix, proyecto solarbi.pbip (texto, apto para Git) + guía DAX
└── grafana/                  dashboard.json + provisioning (data source, dashboard, alerta)
```

## Cómo reproducir la práctica

Requisitos: Python 3.10+, Docker Desktop, Power BI Desktop (Windows).

```bash
# 1. Clonar y configurar credenciales
git clone https://github.com/Cat0428/solarbi-lopez-cardona.git
cd solarbi-lopez-cardona
cp .env.example .env            # Windows: copy .env.example .env   → editar contraseñas

# 2. Levantar PostgreSQL y Grafana
docker compose up -d

# 3. Dependencias de Python
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

# 4. (Opcional) regenerar el Bronze. Ya viene en el repo con semilla fija 2026.
python etl/simulador.py

# 5. ETL completo con un solo comando. Correrlo DOS veces: los conteos no cambian.
python etl/run_etl.py
python etl/run_etl.py
```

Resultado esperado (Bronze con semilla 2026):

| Métrica | Valor |
|---|---|
| Filas leídas | 889 |
| Rechazadas R1 duplicados | 25 |
| Rechazadas R2 faltantes | 23 |
| Rechazadas R3 fuera de rango | 10 |
| Filas válidas | 831 (93,48 % de lo leído · 96,18 % de las 864 lecturas esperadas) |
| `silver.lectura_5min` | 831 filas |
| `dwh.fact_energia_dia` | 3 filas · 79,033 kWh |

6. **Grafana:** <http://localhost:3000> (o el puerto de `GRAFANA_PORT` en `.env`), con el usuario y la clave del `.env`. El data source, el dashboard
   *SolarBI Pascual · Monitoreo operativo* (carpeta SolarBI) y la regla de alerta se crean solos.
   Rango de tiempo: 5 al 7 de octubre de 2026. Para probar la alerta: `sql/06_prueba_alerta.sql`
   (después, borrar la lectura de prueba con el `DELETE` que está al final de ese archivo).
7. **Power BI:** seguir [`powerbi/README.md`](powerbi/README.md).

Sin Docker: instalar PostgreSQL 16 y Grafana OSS nativos, crear la base `solarbi`, ejecutar
`sql/01_ddl.sql`, crear el rol `bi_lector` como en `sql/02_roles.sh` y agregar el data source a mano.

## Reglas de calidad (Bronze → Silver)

| Regla | Condición de rechazo | Justificación |
|---|---|---|
| R1 duplicados | Se repite la clave `(ts, dispositivo_id)`; se conserva la primera | Una lectura por intervalo; si no, la energía se suma dos veces |
| R2 faltantes | Campo obligatorio vacío o no numérico | Sin irradiancia no se puede calcular el Performance Ratio |
| R3 rango físico | `p_ac_kw` fuera de [0; 5,5] · irradiancia fuera de [0; 1500] W/m² · temperatura fuera de [-10; 90] °C | Un inversor de 5 kWp no entrega potencia negativa ni > 110 % de su capacidad |

Las filas rechazadas quedan en `data/silver/rechazos.csv` con su motivo, y cada corrida queda
registrada en `dwh.etl_ejecucion` (linaje).

## Programación diaria (no implementada)

Linux/macOS, `crontab -e` — todos los días a la medianoche:

```cron
0 0 * * * cd /ruta/solarbi-lopez-cardona && .venv/bin/python etl/run_etl.py >> logs/etl.log 2>&1
```

Windows, Programador de tareas (una línea en `cmd`):

```bat
schtasks /Create /TN "SolarBI ETL" /SC DAILY /ST 00:00 /TR "C:\ruta\solarbi\.venv\Scripts\python.exe C:\ruta\solarbi\etl\run_etl.py"
```

## Problemas frecuentes (Windows)

| Síntoma | Causa | Solución |
|---|---|---|
| `Bind for 0.0.0.0:3000 failed: port is already allocated` | Otro programa usa el puerto de Grafana | En `.env`: `GRAFANA_PORT=3001` y `docker compose up -d --force-recreate grafana` |
| `Bind for 0.0.0.0:5432 failed` o el ETL no conecta | Hay un PostgreSQL instalado en Windows en el 5432 | En `.env`: `PGPORT=55432` y `docker compose up -d --force-recreate postgres` |
| `UnicodeDecodeError` al conectar | Error de conexión de PostgreSQL con mensaje en español | Revisar puerto y contraseña (ver filas anteriores) |
| Power BI: *Host desconocido* | No resuelve `localhost` | Usar `127.0.0.1:PUERTO` como servidor |
| Power BI: *encrypted connection* | El contenedor no tiene SSL | Desmarcar **Use encrypted connection** |

En esta práctica se usó Grafana en el puerto **3001** y PostgreSQL en el **55432**.

## Seguridad

- Ninguna contraseña está en el repositorio: todo sale de `.env` (excluido en `.gitignore`).
- Grafana y Power BI se conectan con `bi_lector`, un rol de **solo lectura**. Solo el ETL escribe.

## Autoría

Trabajo desarrollado de forma individual por **Cristian López Cardona**: consulta (Parte A),
flujo ETL y carga en PostgreSQL, dashboard y alerta en Grafana, informe en Power BI y repositorio.
