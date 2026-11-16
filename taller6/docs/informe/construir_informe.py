"""Arma el informe PDF del Taller 6 (BI_Taller6_Lopez_Cardona.pdf).

    python docs/informe/construir_informe.py

Reúne los documentos de docs/ (secciones A–K), las capturas de docs/informe/capturas/ y las
salidas de kubectl de docs/evidencias/ (scripts/evidencias.ps1) en un solo HTML, y lo imprime a
PDF con Chrome sin interfaz. Requiere pandoc y google-chrome (o chromium).
"""
import datetime as dt
import html
import os
import re
import shutil
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
TALLER = os.path.abspath(os.path.join(AQUI, "..", ".."))
DOCS = os.path.join(TALLER, "docs")
CAP = os.path.join(AQUI, "capturas")
EVID = os.path.join(DOCS, "evidencias")
SALIDA = os.path.join(AQUI, "BI_Taller6_Lopez_Cardona.pdf")
REPO = "https://github.com/Cat0428/solarbi-lopez-cardona"
faltantes = []


def leer(nombre):
    with open(os.path.join(DOCS, nombre), encoding="utf-8") as f:
        return f.read()


def seccion(md, desde, hasta=None):
    """Texto desde la línea de encabezado que empieza por `desde` hasta la que empieza por `hasta`."""
    lineas = md.splitlines()
    ini = next(i for i, l in enumerate(lineas) if l.startswith(desde))
    fin = len(lineas)
    if hasta:
        fin = next((i for i, l in enumerate(lineas) if i > ini and l.startswith(hasta)), len(lineas))
    return "\n".join(lineas[ini:fin]).strip() + "\n"


def niveles(md, quitar_numero=True, bajar=0):
    """Ajusta encabezados: quita '2.1 ' y '(A)' y baja `bajar` niveles."""
    def f(m):
        nivel, texto = m.group(1), m.group(2)
        if quitar_numero:
            texto = re.sub(r"^\d+(\.\d+)*\s*·?\s*", "", texto)
        texto = re.sub(r"\s*\(([A-K](, [A-K])*|K\.\d)\)\s*$", "", texto)
        return "#" * min(6, len(nivel) + bajar) + " " + texto
    return re.sub(r"^(#{1,6})\s+(.*)$", f, md, flags=re.M)


def figura(archivo, pie, ancho="100%"):
    ruta = os.path.join(CAP, archivo)
    if not os.path.exists(ruta):
        faltantes.append(archivo)
        return f'\n<div class="pendiente">Captura pendiente: {html.escape(archivo)}</div>\n'
    return (f'\n<figure><img src="capturas/{archivo}" style="width:{ancho}"/>'
            f'<figcaption>{pie}</figcaption></figure>\n')


def evidencia(archivo, titulo=None, desde=None, max_lineas=60, filtro=None):
    """Bloque con la salida real de un comando (docs/evidencias/*.txt)."""
    ruta = os.path.join(EVID, archivo)
    if not os.path.exists(ruta):
        faltantes.append(archivo)
        return f'\n<div class="pendiente">Evidencia pendiente: docs/evidencias/{html.escape(archivo)}</div>\n'
    with open(ruta, encoding="utf-8", errors="replace") as f:
        lineas = f.read().replace("\r", "").splitlines()
    if desde:
        i = next((k for k, l in enumerate(lineas) if desde in l), 0)
        lineas = lineas[i:]
    if filtro:
        lineas = [l for l in lineas if re.search(filtro, l)]
    cortado = len(lineas) > max_lineas
    lineas = [l.rstrip()[:175] for l in lineas[:max_lineas]]
    while lineas and not lineas[-1].strip():
        lineas.pop()
    cuerpo = html.escape("\n".join(lineas))
    if cortado:
        cuerpo += f"\n… (salida recortada; completa en docs/evidencias/{archivo})"
    cab = f'<div class="evtit">{html.escape(titulo or archivo)}</div>' if titulo else ""
    return f'\n<div class="evidencia">{cab}<pre>{cuerpo}</pre></div>\n'


def quitar_mermaid(md, archivo_img, pie):
    return re.sub(r"```mermaid.*?```", figura(archivo_img, pie), md, flags=re.S)


# ------------------------------------------------------------------------------------------
d01, d02, d03, d04, d05 = (leer(n) for n in ("01_fuente_y_calidad.md", "02_indicadores_modelo_diccionario.md",
                                              "03_despliegue_kubernetes.md", "04_arquitectura_analisis_etica.md",
                                              "05_dbeaver.md"))
inv = leer("inventario_bronze.md")
hoy = dt.date.today()
meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
         "octubre", "noviembre", "diciembre"]
fecha_txt = f"{hoy.day} de {meses[hoy.month - 1]} de {hoy.year}"

partes = []
P = partes.append

# Portada --------------------------------------------------------------------------------
P(f"""
<section class="portada">
<div class="inst">INSTITUCIÓN UNIVERSITARIA PASCUAL BRAVO</div>
<div class="dep">Departamento de Sistemas Digitales · Inteligencia de Negocios · Grupo 01 · 2026-II</div>
<div class="tit">Taller 6</div>
<div class="sub">Solución de BI contenerizada y orquestada para el monitoreo energético de una microrred
híbrida (solar + batería + red)</div>
<div class="frase">“From inverter telemetry to actionable insights: a containerized,
Kubernetes-orchestrated BI pipeline for a hybrid microgrid.”</div>
<table class="datos">
<tr><td>Integrante</td><td><b>Cristian David López Cardona</b> (trabajo individual)</td></tr>
<tr><td>Docente</td><td>Ramiro Grisales Montoya</td></tr>
<tr><td>Repositorio</td><td><a href="{REPO}">{REPO}</a> · carpeta <code>taller6/</code></td></tr>
<tr><td>Datos</td><td>OpenCEM v1.0.0 (Zenodo, DOI 10.5281/zenodo.21436223) · licencia CC BY 4.0</td></tr>
<tr><td>Herramientas</td><td>PostgreSQL 16 · Python (pandas) · Docker · kind / Kubernetes 1.33 · Grafana 12 ·
Power BI Desktop (.pbip) · DBeaver · Git y GitHub</td></tr>
<tr><td>Fecha</td><td>Medellín, {fecha_txt}</td></tr>
</table>
</section>
""")

# Contenido ------------------------------------------------------------------------------
P("""
<nav class="indice"><h1 class="sin-salto">Contenido</h1>
<ol>
<li>Resumen ejecutivo: hallazgos y recomendaciones</li>
<li>Descarga, integridad e inventario de los datos</li>
<li>A · Negocio: usuarios, preguntas y diagnóstico de la fuente</li>
<li>B · Indicadores</li>
<li>C · Modelo dimensional</li>
<li>D · Diccionario de datos</li>
<li>E · ETL y calidad de datos</li>
<li>F · Base de datos (PostgreSQL y DBeaver)</li>
<li>G · Power BI</li>
<li>H · Grafana</li>
<li>I · Arquitectura y análisis</li>
<li>J · Ética y seguridad</li>
<li>K · Despliegue: Docker + Kubernetes</li>
<li>Repositorio Git / GitHub</li>
<li>English corner y referencias</li>
</ol></nav>
""")

# 1. Resumen ejecutivo -------------------------------------------------------------------
P("# 1. Resumen ejecutivo: hallazgos y recomendaciones\n")
P("""La solución lleva la telemetría cruda de los dos inversores híbridos de la microrred OpenCEM
(2,99 millones de lecturas, julio de 2025 a julio de 2026) a un modelo dimensional en PostgreSQL y
la publica en dos capas: Grafana para mantenimiento (casi en tiempo real, con alertas) y Power BI para
la dirección (tendencias, comparativos y escenarios). Todo corre en un clúster local de Kubernetes
(kind) que se levanta con `.\\scripts\\up.ps1` y se elimina con `.\\scripts\\down.ps1`.

| Indicador (12/07/2025 a 13/07/2026) | Valor |
|---|---:|
| Fracción solar (solar / (solar + red)) | **33,0 %** |
| Dependencia de la red (red / consumo) | **79,2 %** |
| Batería llena en horas de sol | 39,9 % |
| Ciclos de batería por día | 0,24 |
| Costo de la energía comprada a la red (930 COP/kWh) | **$ 4.092.333** |
| Ahorro por energía solar | $ 2.013.366 |
| Lecturas válidas | 97,64 % |
""")
P(niveles(seccion(d04, "## 4.6", None), bajar=0).replace("## Hallazgos y recomendaciones para la dirección (data storytelling)",
                                                          "## Hallazgos y recomendaciones para la dirección"))

# 2. Datos de origen --------------------------------------------------------------------
P("# 2. Descarga, integridad e inventario de los datos\n")
P("""Se descargaron del registro oficial de Zenodo los tres archivos que pide el taller
(`opencem-v1.0.0.sqlite.zst`, `opencem-v1.0.0-support.zip` y `opencem-v1.0.0-SHA256SUMS.txt`); las
imágenes de cielo (`sky-*.tar.zst`, hasta 4 GB cada una) quedan fuera del alcance. El archivo
`.sqlite` es la capa **Bronze**: no se modifica, no se sube a GitHub (está en `.gitignore`) y el ETL lo
abre en modo solo lectura (`mode=ro&immutable=1`).
""")
P(niveles(seccion(inv, "## Integridad", "## Base"), bajar=0))
chk = os.path.join(DOCS, "evidencia_checksum.txt")
if os.path.exists(chk):
    with open(chk, encoding="utf-8") as f:
        P(f'<div class="evidencia"><div class="evtit">Salida de la verificación (docs/evidencia_checksum.txt)</div>'
          f'<pre>{html.escape(f.read().strip())}</pre></div>\n')
else:
    faltantes.append("evidencia_checksum.txt")
P(niveles(seccion(inv, "## Base", "### "), bajar=0).replace("## Base `opencem-v1.0.0.sqlite` (4,439.4 MB descomprimida)",
                                                           "## Inventario: tablas, filas y periodo"))
P("""El inventario completo (cada columna con tipo, nulos, distintos, mínimo y máximo) está en
`docs/inventario_bronze.md`, generado por `etl/inventario.py`.
""")

# 3. A Negocio ---------------------------------------------------------------------------
P("# 3. A · Negocio: usuarios, preguntas y diagnóstico de la fuente\n")
P(niveles(seccion(d02, "## 2.1", "## 2.2")))
P(niveles(seccion(d01, "## 1.1", "## 1.3")).replace("## Fuente", "## Diagnóstico de la fuente"))

# 4. B Indicadores -----------------------------------------------------------------------
P("# 4. B · Indicadores\n")
P(niveles(seccion(d02, "## 2.2", "## 2.3")).replace("## Catálogo de indicadores\n", ""))

# 5. C Modelo ----------------------------------------------------------------------------
P("# 5. C · Modelo dimensional\n")
P(quitar_mermaid(niveles(seccion(d02, "## 2.3", "## 2.4")).replace("## Modelo dimensional\n", ""),
                 "modelo_estrella.png", "Constelación de hechos (estrellas que comparten dimensiones conformadas)."))

# 6. D Diccionario -----------------------------------------------------------------------
P("# 6. D · Diccionario de datos\n")
P(niveles(seccion(d02, "## 2.4", "## 2.5")).replace("## Diccionario de datos\n", ""))

# 7. E ETL -------------------------------------------------------------------------------
P("# 7. E · ETL y calidad de datos\n")
P(niveles(seccion(d01, "## 1.3", None)))

# 8. F Base de datos ---------------------------------------------------------------------
P("# 8. F · Base de datos (PostgreSQL y DBeaver)\n")
P("""El DDL está en `sql/01_ddl.sql` (esquemas `silver`, `gold` y `ops`, llaves, restricciones `CHECK`
e índices) y se administra desde DBeaver con una conexión de **administración** (dueño del esquema) y
otra de **consulta** (`bi_lector`, solo lectura). El script es idempotente: el ETL lo ejecuta al inicio
de cada corrida y DBeaver puede volver a ejecutarlo sin efectos. `sql/03_consultas_negocio.sql` responde
nueve preguntas de negocio y `sql/04_catalogo_dbeaver.sql` reúne las evidencias del catálogo.
""")
P(niveles(seccion(d02, "## 2.5", None)))
P("## DBeaver\n")
P(figura("dbeaver_conexiones_ddl.jpg", "DBeaver: conexiones de administración y de consulta; DDL ejecutado desde el script versionado."))
P(figura("dbeaver_diagrama_er.jpg", "Diagrama entidad-relación del esquema gold generado por DBeaver a partir de las llaves foráneas."))
P(figura("dbeaver_consulta_json.jpg", "Consulta Q7 sobre el campo JSONB (operadores @>, ? y ->>) ejecutada en DBeaver."))
P("## Consultas de negocio y su resultado\n")
P("""Ejecutadas sobre la base del clúster (`kubectl exec … psql -f sql/03_consultas_negocio.sql`). Q2 compara
cada mes con el anterior (`LAG`), Q3 y Q6 usan `RANK` y `ROW_NUMBER` con `PARTITION BY`, Q4 acumula con
`SUM() OVER`, y Q7/Q8 consultan el JSON con `@>`, `?` y `->>`.
""")
P(evidencia("13_consultas_negocio.txt", "Salida de sql/03_consultas_negocio.sql", max_lineas=120))
P("## Evidencias del catálogo: restricciones, índices y planes de ejecución\n")
P(evidencia("14_catalogo_bd.txt", "Salida de sql/04_catalogo_dbeaver.sql (E1–E9)", max_lineas=110))

# 9. G Power BI --------------------------------------------------------------------------
P("# 9. G · Power BI\n")
P("""**Conexión.** El informe se conecta a PostgreSQL (no a los archivos de origen) en modo *Import*,
con el usuario de solo lectura `bi_lector`. El servidor y la base son parámetros de Power Query
(`Servidor = 127.0.0.1:55432`, `BaseDatos = microrred`): el mismo informe funciona contra el clúster
kind o contra Docker Compose sin editar consultas. Se importan las 8 tablas de Gold y dos de `ops`
(reglas de calidad y conciliación), filtradas a la última corrida del ETL.

**Modelo semántico.** 10 tablas importadas más `Tarifa` y `_Medidas`; 11 relaciones uno-a-varios en
estrella; `dim_fecha` está **marcada como tabla de fechas** (es propia, construida por el ETL con
festivos y eventos del campus); 4 jerarquías (Calendario: año → trimestre → mes → día; Franja horaria:
franja → hora; Inversor y configuración: inversor → versión; Categoría de evento: categoría → tipo) y
37 medidas DAX organizadas en carpetas.

**Inteligencia de tiempo.** `Variación red/día vs mes anterior %` compara cada mes con el anterior con
`DATEADD(dim_fecha[fecha], -1, MONTH)` sobre la energía de red **por día con datos**, para que los
huecos de registro no distorsionen el comparativo; `Costo de la red acumulado (COP)` acumula desde el
inicio del registro. La consulta DAX de la figura muestra ambas medidas mes a mes.

```
Variación red/día vs mes anterior % =
VAR Actual   = [Red por día con datos (kWh/día)]
VAR Anterior = CALCULATE ( [Red por día con datos (kWh/día)], DATEADD ( dim_fecha[fecha], -1, MONTH ) )
RETURN DIVIDE ( Actual - Anterior, Anterior )
```

**Escenario what-if.** La tabla `Tarifa = GENERATESERIES(700, 1300, 10)` alimenta un segmentador de
selección única; `Tarifa seleccionada (COP/kWh) = SELECTEDVALUE(Tarifa[Tarifa COP/kWh], 930)` multiplica
la energía comprada (costo) y la energía solar (ahorro). 930 COP/kWh es la tarifa elegida como base
(estimado residencial estrato 4, EPM Medellín, 2026); el escenario permite ver el efecto de ±40 %.

**Navegación, segmentaciones y profundización.** Las siete páginas tienen un navegador de páginas
inferior y segmentadores de mes e inversor. La profundización (drill-down) está en la energía mensual
(mes → día), en la matriz de franjas (franja → hora) y en los eventos (categoría → tipo).

**Balance energético.** La página 1 muestra de dónde viene la energía (solar, batería, red) por
inversor y a dónde va (consumo); la página 3 lo abre por hora del día y la 2 por versión de
configuración, que es donde aparece el hallazgo principal.

**Formato versionable.** El informe se guarda como **proyecto de Power BI (.pbip)**: el modelo en
**TMDL** y el informe en **PBIR** (JSON por página y por visual). Son archivos de texto, así que Git
muestra diferencias línea a línea (una medida, un visual) y se pueden revisar y fusionar; un `.pbix` es
un binario comprimido que Git solo puede reemplazar entero. La caché de datos y la configuración
local (`.pbi/cache.abf`, `localSettings.json`) quedan en `.gitignore`: en el repositorio no hay datos.
""")
for archivo, pie in [
    ("pbi_1_resumen.jpg", "Página 1 · Resumen ejecutivo: KPI, energía mensual por origen (drill-down mes → día), texto dinámico con el hallazgo y balance por inversor."),
    ("pbi_2_configuracion.jpg", "Página 2 · Desempeño por versión de configuración (dimensión de cambio lento tipo 2)."),
    ("pbi_3_perfil.jpg", "Página 3 · Perfil horario y matriz franja × inversor (drill-down franja → hora)."),
    ("pbi_4_eventos.jpg", "Página 4 · Eventos operativos y fallas (drill-down categoría → tipo)."),
    ("pbi_5_cargas.jpg", "Página 5 · Cargas registradas en el contexto (JSON) y su consumo medido."),
    ("pbi_6_economico.jpg", "Página 6 · Indicador económico con parámetro what-if de tarifa y comparativo frente al mes anterior."),
    ("pbi_7_calidad.jpg", "Página 7 · Calidad de datos: reglas del ETL y conciliación con el contador del inversor."),
    ("pbi_dax_inteligencia_tiempo.jpg", "Vista de consultas DAX: medidas de inteligencia de tiempo (comparativo mensual y acumulado)."),
]:
    P(figura(archivo, pie))

# 10. H Grafana --------------------------------------------------------------------------
P("# 10. H · Grafana\n")
P("""**Fuente de datos.** PostgreSQL (`uid microrred-pg`), creada por *provisioning* desde el ConfigMap
`grafana-datasources`, apuntando al Service `postgres.microrred.svc.cluster.local:5432` con el rol de
solo lectura `bi_lector`. La contraseña llega por variable de entorno desde el Secret: no está en el
archivo de provisioning ni en la imagen.

**Tablero** *Microrred OpenCEM · Monitoreo operativo* (ConfigMap `grafana-tableros`, refresco cada 30 s):
estado actual por inversor (SOC, potencia instantánea, minutos sin datos, datos válidos), series de
tiempo de flujos de potencia, SOC, red pública y temperatura, energía del periodo por origen y la lista
de alertas activas. La variable de tablero `inversor` filtra todos los paneles.

**Reglas de alerta** (ConfigMap `grafana-alertas`, nunca creadas desde la interfaz):

| Regla | Condición | Por qué ese umbral |
|---|---|---|
| Batería baja | SOC < 20 % durante 2 min | El inversor pasa a la red con 10 % y corta en 5 %; en el histórico el SOC llegó a 6 %. 20 % deja ~1 kWh para actuar |
| Inversor sin datos | > 5 min sin lecturas durante 1 min | El inversor reporta cada ~12 s; 5 min son 5 lotes perdidos. Hubo 153 huecos > 10 min y uno de 26 días sin detectar |
| Compra de red con batería llena | red > 500 W con SOC ≥ 95 % durante 5 min | Con prioridad SOL la batería pasó llena el 84 % de las horas de sol mientras se compraba red |

**Streaming simulado.** El CronJob `simulador` corre cada minuto dentro del clúster: toma minutos
reales del histórico, los reubica en la hora actual de Colombia y los inserta con `origen='simulador'`.
En el ambiente *demo* inyecta cada 15 minutos un episodio de 6 minutos con el SOC del inversor 2 en
12 %: supera el `for: 2m` de la regla, la alerta de batería baja pasa a *Firing* y luego vuelve a
*Normal*. Suspender el CronJob dispara la de "sin datos". Una primera versión inyectaba un solo
minuto anómalo al azar y la alerta nunca llegaba a dispararse por el `for: 2m`; se corrigió para que
el episodio dure lo que dura uno real.
""")
P(figura("grafana_tablero.jpg", "Tablero operativo con datos del simulador llegando cada minuto (inversor = Todos). Episodio simulado de batería baja: el inversor 2 está en 12 % y la alerta «Batería baja» pasó de Pending a Alerting."))
P(figura("grafana_alertas.jpg", "Las tres reglas de alerta, marcadas como «Provisionado» (vienen de un ConfigMap, no de la interfaz). En esta captura «Compra de red con batería llena» está en Firing; en la captura anterior la de batería baja del inversor 2 está en Alerting durante el episodio simulado de las 21:00."))
P(figura("grafana_inversor2.jpg", "Variable de tablero filtrando el inversor 2."))
P(evidencia("11_grafana_api.txt", "API de Grafana: fuente de datos, tablero y estado de las reglas", max_lineas=60))

# 11. I Arquitectura ---------------------------------------------------------------------
P("# 11. I · Arquitectura y análisis\n")
arq = niveles(seccion(d04, "## 4.1", "## 4.4"))
arq = re.sub(r"Para el informe se puede exportar.*?\n\n", "", arq, flags=re.S)
P(quitar_mermaid(arq, "arquitectura.png", "Arquitectura completa: de la fuente al consumo, con los objetos de Kubernetes."))

# 12. J Ética ----------------------------------------------------------------------------
P("# 12. J · Ética y seguridad\n")
P(niveles(seccion(d04, "## 4.4", "## 4.6")))

# 13. K Despliegue -----------------------------------------------------------------------
P("# 13. K · Despliegue: Docker + Kubernetes\n")
k = seccion(d03, "## 3.1", "## 3.4")
k = re.sub(r"Mida los tamaños reales.*?\n\n", "", k, flags=re.S)
P(niveles(k))
P(evidencia("02_imagenes.txt", "Tamaño real de las imágenes (docker images) y presencia en el nodo kind", max_lineas=40))
P("## Reproducibilidad y resiliencia\n")
P("""Un comando levanta todo desde cero (`.\\scripts\\up.ps1`: crea el clúster kind, construye y carga
las imágenes, crea el Secret desde `credenciales.env`, aplica los manifiestos con Kustomize y espera a que
termine el Job del ETL) y otro lo elimina (`.\\scripts\\down.ps1`). Las salidas siguientes son reales y
las genera `scripts/evidencias.ps1`.
""")
P(evidencia("00_up.txt", "Levantar desde cero: .\\scripts\\up.ps1 (final de la salida)", max_lineas=70, desde="Esperando la carga"))
P(evidencia("01_entorno.txt", "Versiones y nodo del clúster", max_lineas=30))
P(evidencia("03_get_all.txt", "kubectl get all,pvc,configmap,secret -n microrred", max_lineas=70))
P(evidencia("04_postgres.txt", "kubectl describe statefulset postgres", max_lineas=55))
P(evidencia("05_grafana.txt", "kubectl describe deployment grafana", max_lineas=45))
P(evidencia("06_etl_job.txt", "Job etl-historico: describe, logs y linaje en ops.etl_ejecucion", max_lineas=110))
P(evidencia("07_simulador.txt", "CronJob simulador: describe, historial de Jobs y minutos insertados", max_lineas=90))
P(evidencia("08_servicios_dns.txt", "Services, NodePort y resolución por nombre (DNS del clúster)", max_lineas=60))
P(evidencia("09_recursos_sondas.txt", "Solicitudes y límites de CPU/memoria, y sondas de salud", max_lineas=40))
P(evidencia("10_secret_configmap.txt", "Secret (solo nombres y tamaños) y ConfigMap de parámetros", max_lineas=70))
P("### Demostración 1: se elimina el pod de PostgreSQL y los datos siguen ahí\n")
P(evidencia("15_demo_postgres.txt", "Pod postgres-0 antes y después (UID distinto, mismo PVC, mismos conteos)", max_lineas=60))
P("### Demostración 2: se elimina el pod de Grafana y vuelve con su tablero\n")
P(evidencia("16_demo_grafana.txt", "Pod de Grafana recreado; tablero, fuente y alertas presentes sin configurar nada", max_lineas=60))
P("### Cambio de umbral sin reconstruir la imagen\n")
P("""Los umbrales viven en `k8s/base/parametros.env` (ConfigMap `microrred-parametros`) y en
`k8s/base/grafana/alerting/reglas.yaml` (ConfigMap `grafana-alertas`). Cambiar un valor es editar el
archivo y ejecutar `kubectl apply -k k8s/overlays/demo`: el simulador toma el nuevo parámetro en su
siguiente corrida y, como Kustomize agrega al nombre del ConfigMap un sufijo con el hash del contenido,
el Deployment de Grafana se recrea solo con la regla nueva. Ninguna imagen se reconstruye.
""")
P(niveles(seccion(d03, "## 3.5", None)))
P(evidencia("17_escalar.txt", "Bonificación: Grafana escalado a 2 réplicas y de vuelta a 1", max_lineas=40))
P(evidencia("12_kustomize_ambientes.txt", "Bonificación: Kustomize con ambientes dev y demo", max_lineas=30))

# 14. Repositorio ------------------------------------------------------------------------
P("# 14. Repositorio Git / GitHub\n")
P(f"""Repositorio: <{REPO}> (carpeta `taller6/`). El README explica el proyecto, la arquitectura, los
requisitos del equipo anfitrión, cómo reproducir la solución desde cero y la cita de los datos.

| Se versiona | No se versiona (`.gitignore`) |
|---|---|
| Scripts SQL (`sql/`), ETL y simulador con sus Dockerfile, `docker-compose.yml`, manifiestos de Kubernetes y overlays de Kustomize, tablero y alertas de Grafana (JSON/YAML), proyecto de Power BI (`.pbip`: TMDL + PBIR), documentación y scripts `up`/`down`/`evidencias` | `credenciales.env` (solo se versiona `credenciales.env.example`), la capa Bronze (`data/bronze/*`, 4,4 GB), datos intermedios, la caché de Power BI (`.pbi/cache.abf`) y su configuración local |

Las credenciales llegan al clúster como `Secret` creado en el momento del despliegue
(`kubectl create secret generic --from-env-file=credenciales.env`), nunca desde un YAML versionado:
en base64 cualquiera que lea el repositorio podría decodificarlas.
""")

# 15. English corner y referencias -------------------------------------------------------
P("# 15. English corner y referencias\n")
P("""| Term | Where it appears in this project |
|---|---|
| hybrid microgrid | Two PV + LiFePO4 + grid subsystems, each with a hybrid inverter |
| state of charge (SoC) | `soc_pct`; alert when SoC < 20 % for 2 min |
| self-sufficiency | Solar fraction (33 %) and grid dependency (79 %) |
| grid import | `energia_red_kwh`, valued in COP with the what-if tariff |
| data lineage | `ops.etl_ejecucion`, `ops.etl_regla`, source column of every field in the dictionary |
| idempotent load | Re-running the ETL yields identical MD5 signatures in Gold |
| container image | `microrred-etl:1.0.0`, `microrred-simulador:1.0.0` |
| pod / deployment | `postgres-0`, `deployment/grafana` |
| persistent volume | PVC `data-postgres-0` survives pod deletion |
| secret / config map | `microrred-credenciales` / `microrred-parametros` |
| liveness probe | `pg_isready` and `GET /api/health` |
| provisioning | Grafana datasource, dashboard and alert rules loaded from ConfigMaps |

**Poster:** *From inverter telemetry to actionable insights: a containerized, Kubernetes-orchestrated
BI pipeline for a hybrid microgrid.*

**Cita de los datos.** Bartels, T. S., Wu, R., Lu, X., Chen, Y., Lu, Y., Xia, F., Yang, H., Chen, Y., &
Li, T. (2026). *OpenCEM: Multimodal photovoltaic and battery microgrid dataset with context records and
sky imagery* (Version 1.0.0) [Dataset]. Zenodo. https://doi.org/10.5281/zenodo.21436223

Artículo de los autores: arXiv:2604.05429. Repositorio complementario:
https://github.com/OpenCEM-platform/opencem-dataset.
""")

# Ensamblado -----------------------------------------------------------------------------
md = "\n\n".join(partes)
os.makedirs(os.path.join(AQUI, "_build"), exist_ok=True)
md_path = os.path.join(AQUI, "_build", "informe.md")
with open(md_path, "w", encoding="utf-8") as f:
    f.write(md)
html_path = os.path.join(AQUI, "informe.html")
subprocess.run(["pandoc", md_path, "-f", "markdown+pipe_tables+raw_html-implicit_figures", "-t", "html5",
                "--standalone", "--metadata", "pagetitle=BI Taller 6 · López Cardona", "--css", "estilo.css",
                "-o", html_path], check=True)
chrome = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={SALIDA}", "file://" + html_path], check=True,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("PDF:", SALIDA)
if faltantes:
    print("Pendientes:", ", ".join(sorted(set(faltantes))))
