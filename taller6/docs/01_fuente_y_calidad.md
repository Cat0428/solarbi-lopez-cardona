# 1 · Diagnóstico de la fuente, ETL y calidad de datos

> Todas las cifras salen de la **base oficial de Zenodo** `opencem-v1.0.0.sqlite`
> (SHA-256 `5fe1f213…a6283fa`, verificada; ver [`inventario_bronze.md`](inventario_bronze.md)).
> El ETL las vuelve a calcular en cada corrida y las deja en `ops.etl_regla`, `ops.conciliacion` y
> `ops.conciliacion_contador`.

## 1.1 Fuente

| Elemento | Detalle |
|---|---|
| Sistema | Microrred del campus CUHK-Shenzhen (Longgang, Shenzhen). Dos subsistemas independientes: arreglo FV + banco LiFePO4 de 200 Ah + inversor híbrido SPI4880V150-500P de 8 kW |
| Base | SQLite de 4,44 GB con 8 tablas: `analog_measurements` (2 989 759 filas, 44 columnas), `status`, `totals`, `settings` (176 columnas), `specs`, `statistics`, `fault_history` y `context` (25 178 registros JSON) |
| Cobertura eléctrica | 12/07/2025 21:31 → 13/07/2026 13:13, hora de Shenzhen (UTC+8). El inversor 2 termina el 22/06/2026 |
| Muestreo | Una "foto" del inversor cada ~12–13 s (mediana). Silver: 1 lectura/min en el 50 % de los casos, p99 = 5 min |
| Material de apoyo | `support.zip`: diccionario de 380 columnas con unidades, esquema, reporte de calibración de relojes y validación oficial |
| Inventario completo | [`inventario_bronze.md`](inventario_bronze.md): tablas, columnas, nulos, distintos, mín/máx |

## 1.2 Problemas encontrados (por qué los datos "no son de lectura directa")

| # | Problema | Evidencia | Tratamiento |
|---|---|---|---|
| 1 | **Fotos vacías** | 55 658 lecturas sin ningún valor eléctrico y 70 665 con algún campo obligatorio nulo (~2 %, igual en todas las columnas: falla de lectura Modbus) | R5 marca la lectura inválida; no se imputa |
| 2 | **Valores físicamente imposibles** | 15 lecturas, p. ej. batería en 0 V o 29 V con SOC normal (un banco 16S LiFePO4 no baja de ~40 V sin que el BMS lo desconecte) | R6 la marca inválida |
| 3 | **Huecos** | 153 periodos de más de 10 min sin datos. El mayor es de **26 días** (03 al 29/08/2025) en ambos inversores. Disponibilidad: 77,8 % (inv. 1) y 63,8 % (inv. 2) | R7 no integra energía en el hueco; evento `SIN_DATOS` |
| 4 | **Configuración leída a medias** | `settings` trae campos sueltos en NULL en 65 887 lecturas (2,9 %). Tomadas una por una crearían cambios de configuración falsos | S1 las descarta; S2 toma la configuración más frecuente de cada día |
| 5 | **Contadores cruzados entre inversores** | En `statistics`, el inversor 1 alterna lecturas con los contadores acumulados del inversor 2: 52 955 "retrocesos" seguidos de saltos de hasta 982 kWh. El inversor 2 no tiene ninguno | S3 conserva la serie propia (nunca baja y no crece más de lo que permiten 8 kW en el tiempo transcurrido) |
| 6 | **Relojes del equipo descalibrados** | Los contadores "de hoy" del inversor 2 se reinician cerca de las 10:00 de Shenzhen, no a medianoche. Los autores tuvieron que calibrar el reloj de las fallas (`timestamp_calibration_report.json`) | Se concilia con los contadores **acumulados**, no con los diarios |
| 7 | **Códigos de fábrica sin documentar** | Los arreglos de 16 registros de `fault_history` y los códigos de `settings` (prioridades) no tienen significado publicado (el manual es privado) | Se conservan con su código; las prioridades se interpretan con evidencia (ver 1.5) |
| 8 | **Arreglos JSON en columnas** | `fault_history` tiene 32 posiciones por foto. La misma falla se repite en miles de fotos (2,13 M filas → 20 516 fallas distintas) | F1 las desarma y deja una fila por (inversor, código, hora) |
| 9 | Columnas sin información | `temper4` = 120 constante (sensor ausente), `gridpowerw_a` ≈ 68 W fijos, `generatedpowerp_a` = 0 | No se usan. La red importada es `linepowerw_a` (el balance cierra con correlación 0,92/0,99) |
| 10 | **Zona horaria** | `read_ts` está en UTC; el sitio está en UTC+8 | Todo se guarda en `timestamptz` UTC; fecha y hora del modelo se calculan en `Asia/Shanghai` |

**Fuente complementaria (GitHub).** La exportación CSV pública
(`github.com/OpenCEM-platform/opencem-dataset`) tiene defectos que la base oficial **no** tiene:
- 4,02 M filas para 2,73 M lecturas, porque se anexó una exportación encima de otra;
- la corriente de batería con desborde de entero sin signo (6 538,5 A = −15,1 A);
- filas de 78 campos bajo encabezados de 82;
- contexto duplicado y 5 JSON mal formados, que la versión oficial ya trae reparados (`"repair_reason": "malformed legacy context.value…"`).

Las reglas R1–R3 y C1–C2 existen por eso: con la base oficial dan 0, y ese 0 también es evidencia
(la fuente oficial declara `duplicate_keys: 0`).

**Limitaciones para el análisis:**
- No hay irradiancia ni temperatura de módulo, ni exportación a la red.
- La capacidad del arreglo es ambigua: 26 paneles de 480 W por arreglo (12,48 kWp) o 26 en total (6,24 kWp). El máximo observado (3,9 kW) es más consistente con **6,24 kWp**, el valor parametrizado.

## 1.3 Reglas de limpieza y su efecto (base oficial)

| Regla | Qué hace | Acción | Antes | Después | Afectadas |
|---|---|---|---:|---:|---:|
| R0 | Lecturas leídas de `analog_measurements` | — | 2 989 759 | 2 989 759 | 0 |
| R1 | Filas repetidas | elimina | 2 989 759 | 2 989 759 | 0 |
| R2 | Desborde uint16 en `battcurr` | corrige | 2 989 759 | 2 989 759 | 0 |
| R3 | Llave (read_ts, inversor) repetida | elimina | 2 989 759 | 2 989 759 | 0 |
| R4 | Inversor ∉ {1,2} o fecha imposible | elimina | 2 989 759 | 2 989 759 | 0 |
| R5 | Campo obligatorio vacío | marca inválida | 2 989 759 | 2 919 094 | 70 665 |
| R6 | Fuera de rango físico | marca inválida | 2 919 094 | 2 919 079 | 15 |
| R7 | Hueco > 120 s: integra solo 12 s | corrige | 2 989 759 | 2 989 759 | 8 734 |
| C1 | Contexto repetido | elimina | 25 178 | 25 178 | 0 |
| C2 | JSON mal formado → cuarentena | elimina | 25 178 | 25 178 | 0 |
| C3 | Rutas `/home/<usuario>` enmascaradas | corrige | 25 178 | 25 178 | 0 (la fuente ya las trae como `<user>`) |
| C4 | Fin antes del inicio | elimina | 25 178 | 25 178 | 0 |
| S1 | `settings` con campos nulos | elimina | 2 284 775 | 2 218 888 | 65 887 |
| S2 | Días de configuración → versiones | informa | 497 días | 5 versiones | — |
| S3 | Contador nulo, cruzado o imposible | elimina | 2 283 350 | 1 764 615 | 518 735 |
| F1 | Fotos de `fault_history` → fallas distintas | informa | 2 129 517 × 32 | 20 516 | — |

Resultado: **97,64 % de lecturas válidas** (2 919 079 / 2 989 759). Por inversor: 99,67 % y 95,26 %.

## 1.4 Dato inválido frente a evento operativo real

Criterio **físico**: lo que el equipo no puede producir es un dato inválido. Lo posible pero
indeseable es un evento que se cuenta, no se borra. Cuando fue posible, se confirmó con otra
tabla de la fuente.

| Situación | Clasificación | Por qué / evidencia cruzada |
|---|---|---|
| Batería en 0 V con SOC 90 % | Dato inválido | Contradice al SOC del mismo instante |
| Foto con todos los campos en NULL | Dato inválido (faltante) | Falla de lectura; el validador oficial reporta ~58 k nulos por columna |
| SOC = 6 % | **Evento** `BAT_BAJA` | Real: el equipo está configurado para pasar a la red en 10 % y cortar en 5 % (`settings`) |
| Voltaje de salida < 100 V | **Evento** `SALIDA_APAGADA` | Coincide en el **100 %** de las lecturas con `status.outstatus = 0` (salida apagada reportada por el inversor) |
| Voltaje de red = 0 V | **Evento** `CORTE_RED` | La planta opera aislada: 17,6 % de las lecturas del inversor 1, con cortes de hasta 17 días |
| Registro de `fault_history` | **Evento** `FALLA_<código>` | Lo reporta el propio inversor (20 516 fallas, 9 códigos) |
| PV = 0 a mediodía | Ni lo uno ni lo otro | Nubes, o recorte porque la batería está llena; se analiza como indicador |
| 26 días sin lecturas | **Evento** `SIN_DATOS` | Falla del registro: se documenta y no se imputa |

Los eventos viven en `gold.fact_evento` (inicio, fin, duración), separados de las lecturas.

## 1.5 Interpretación de los códigos de configuración (con evidencia)

El manual del fabricante no es público. Los códigos de `settings.outpriority` y `chgpriority` se
interpretaron con la convención de inversores híbridos tipo SRNE (salida 0 = SOL, 1 = UTI,
2 = SBU). La interpretación **se verificó con el comportamiento medido** de cada versión de
configuración:

| Versión (dim_inversor) | Días | Red / consumo | Batería llena 10–15 h | Lectura |
|---|---:|---:|---:|---|
| Inv. 1 · salida 2, carga 2 (hasta 28/08/2025) | 23 | **0 %** | 0 % | SBU: sol → batería → red. La red no se usa |
| Inv. 1 · salida 0, carga 2 (29/08/2025 → 06/01/2026) | 125 | **108 %** | **84 %** | SOL: el sol cubre el mediodía y la red la noche; la batería queda llena y además la red la carga |
| Inv. 1 · salida 0, carga 3 (desde 07/01/2026) | 188 | 66 % | 51 % | Carga "solo solar": la red deja de cargar la batería |
| Inv. 2 · salida 0, carga 2 / carga 3 | 139 / 127 | 81 % / 76 % | 45 % / 30 % | Mismo patrón |

## 1.6 Frecuencia de la capa Silver: 1 minuto

| Se gana | Se pierde |
|---|---|
| ~4 veces menos filas (782 217 minutos frente a 2,99 M lecturas) | Transitorios de menos de 1 min. Se conserva el máximo por minuto (`carga_max_w`) |
| Coincide con la cadencia del simulador y el refresco de Grafana | La marca de tiempo fraccionaria exacta |
| Conserva la dinámica de las tareas del contexto (compilaciones de ~1–2 min) | — |
| La energía se integra **antes** de agregar (E = P·Δt por lectura): el total no depende de la frecuencia | — |

## 1.7 Conciliación

**a) Entre capas (cada corrida):**

| Control | Origen | Destino | Diferencia |
|---|---:|---:|---:|
| Lecturas válidas (limpieza → Silver) | 2 919 079 | 2 919 079 | 0 |
| Lecturas únicas (limpieza → Silver) | 2 989 759 | 2 989 759 | 0 |
| Energía solar, kWh (lecturas → Gold) | 2 164,911 | 2 164,909 | −0,002 |
| Energía a la carga, kWh | 5 559,278 | 5 559,279 | 0,001 |
| Energía de la red, kWh | 4 400,352 | 4 400,358 | 0,006 |
| Registros de contexto (limpieza → Gold) | 25 178 | 25 178 | 0 |

**b) Contra la fuente:** se compara con los **contadores de energía del propio inversor**
(`statistics.pvgeneratenergytotal` y `usedenergytotal`, ya limpios con S3). Para cada inversor y
mes se toma el Δ del contador entre la primera y la última lectura del mes, y se compara con la
energía que integró el ETL en **exactamente esa ventana** (`ops.conciliacion_contador`).

| Inversor · energía solar | Contador del equipo (kWh) | Integrado por el ETL (kWh) | Diferencia |
|---|---:|---:|---:|
| Inv. 2 · sep-2025 | 200,2 | 199,3 | −0,45 % |
| Inv. 2 · oct-2025 | 176,8 | 176,7 | −0,05 % |
| Inv. 2 · dic-2025 | 137,0 | 137,9 | +0,63 % |
| Inv. 2 · ene-2026 | 184,7 | 185,3 | +0,33 % |
| Inv. 1 · dic-2025 / ene-2026 / feb-2026 | 65,7 / 81,5 / 50,7 | 67,5 / 82,9 / 51,6 | +2,7 / +1,7 / +1,9 % |

En los meses con datos completos la integración coincide con el equipo **dentro de ±1 %
(inversor 2) y ±3 % (inversor 1)**. Eso valida las unidades (W y kWh) y el método. Las grandes
diferencias de julio y agosto de 2025 y de abril y mayo de 2026 se explican así:
- el contador sigue sumando durante los huecos de lecturas analógicas, que el ETL no inventa;
- en 2026 el contador del inversor 1 vuelve a cruzarse con el del inversor 2.

## 1.8 Idempotencia

- Silver histórico, contexto, configuración, fallas y Gold se reemplazan **en una sola
  transacción**. Ante un error, el `ROLLBACK` deja la base intacta.
- Las llaves son deterministas: fecha AAAAMMDD, hora 0–23, versiones del inversor numeradas por
  (inversor, fecha) y `evento_id` por orden de inicio.
- Lo que cargó el simulador (`origen = 'simulador'`) no se toca, y Gold **no depende** de esas
  filas.
- Prueba: ETL → simulador → ETL dejan las mismas firmas MD5 en `fact_energia_hora`, `fact_evento`,
  `fact_actividad`, `dim_inversor` y `dim_fecha`. Solo crece `ops.*` (la bitácora).

## 1.9 Herramienta del ETL

Python 3.12 con pandas y psycopg 3, empaquetado en una imagen propia (`etl/Dockerfile`). Lee
SQLite y JSON de forma nativa, procesa las 4 tablas grandes en **~1 min** con un pico de
**2,6 GB** de memoria, y deja cada regla con su conteo. La parte relacional (Gold) está en
**SQL** (`sql/02_gold.sql`): funciones de ventana para las islas de eventos, el densificado
horario y la SCD2.
