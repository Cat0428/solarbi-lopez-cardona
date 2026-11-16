-- =====================================================================================
-- Taller 6 · Construcción de la capa GOLD a partir de Silver (lo ejecuta el ETL)
-- Corre dentro de la MISMA transacción que la carga de Silver: o queda todo o no queda nada.
-- Parámetros (los fija el ETL con set_config(..., true) desde el ConfigMap):
--   microrred.zona            zona horaria del sitio (Asia/Shanghai)
--   microrred.soc_bajo        % de SOC por debajo del cual hay evento de batería baja
--   microrred.temp_alta       °C del inversor por encima de los cuales hay evento
--   microrred.hueco_min       minutos sin datos que constituyen un evento de comunicación
--   microrred.lecturas_hora   lecturas esperadas por hora (3600 s / muestreo)
--   microrred.capacidad_pv    kWp por arreglo
-- Idempotente: hechos y dimensiones se reconstruyen completos desde Silver. Las versiones de
-- dim_inversor (SCD2) salen del historial de configuración del propio inversor, así que cada
-- corrida reproduce exactamente las mismas versiones con las mismas claves.
-- =====================================================================================

TRUNCATE gold.fact_energia_hora, gold.fact_evento, gold.fact_actividad;
DELETE FROM gold.dim_fecha;
DELETE FROM gold.dim_inversor;
DELETE FROM gold.dim_hora;
DELETE FROM gold.dim_tipo_evento;
DELETE FROM gold.dim_fuente_contexto;

-- ---------------------------------------------------------------- dim_hora (construida)
INSERT INTO gold.dim_hora
SELECT h,
       lpad(h::text, 2, '0') || ':00',
       CASE WHEN h < 6 THEN 'Madrugada' WHEN h < 10 THEN 'Mañana' WHEN h < 15 THEN 'Mediodía solar'
            WHEN h < 19 THEN 'Tarde' ELSE 'Noche' END,
       CASE WHEN h < 6 THEN 1 WHEN h < 10 THEN 2 WHEN h < 15 THEN 3 WHEN h < 19 THEN 4 ELSE 5 END,
       h BETWEEN 6 AND 17,
       CASE WHEN h BETWEEN 18 AND 21 THEN 'Punta' ELSE 'Fuera de punta' END
FROM generate_series(0, 23) AS h;

-- ---------------------------------------------------------------- dim_fecha (hora local del sitio)
WITH limites AS (
    SELECT min(d) AS d0, max(d) AS d1 FROM (
        SELECT (min(ts) AT TIME ZONE current_setting('microrred.zona'))::date AS d
        FROM silver.lectura_1min WHERE origen = 'historico'
        UNION ALL SELECT (max(ts) AT TIME ZONE current_setting('microrred.zona'))::date
        FROM silver.lectura_1min WHERE origen = 'historico'
        UNION ALL SELECT (min(ts) AT TIME ZONE current_setting('microrred.zona'))::date FROM silver.falla_inversor
        UNION ALL SELECT (min(inicio_ts) AT TIME ZONE current_setting('microrred.zona'))::date FROM silver.contexto
        UNION ALL SELECT (max(fin_ts) AT TIME ZONE current_setting('microrred.zona'))::date FROM silver.contexto
    ) x
),
calendario AS (   -- anotaciones manuales del campus SIN inversor: festivos, exámenes, vacaciones
    SELECT g::date AS fecha, string_agg(DISTINCT c.valor ->> 'textual_description', ' · ') AS evento,
           bool_or(c.valor ->> 'textual_description' ~* '(holiday|festival)') AS festivo
    FROM silver.contexto c
    CROSS JOIN LATERAL generate_series((c.inicio_ts AT TIME ZONE current_setting('microrred.zona'))::date,
                                       (c.fin_ts    AT TIME ZONE current_setting('microrred.zona'))::date,
                                       interval '1 day') g
    WHERE c.fuente = 'manual entry' AND c.inversor_id IS NULL
    GROUP BY 1
)
INSERT INTO gold.dim_fecha
SELECT to_char(d, 'YYYYMMDD')::int, d, extract(year FROM d), extract(quarter FROM d), extract(month FROM d),
       (ARRAY['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre',
              'Noviembre','Diciembre'])[extract(month FROM d)],
       to_char(d, 'YYYY-MM'), extract(week FROM d), extract(day FROM d), extract(isodow FROM d),
       (ARRAY['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'])[extract(isodow FROM d)],
       extract(isodow FROM d) >= 6,
       coalesce(cal.festivo, false), cal.evento
FROM limites, generate_series(d0, d1, interval '1 day') AS g(d0d)
CROSS JOIN LATERAL (SELECT g.d0d::date AS d) dd
LEFT JOIN calendario cal ON cal.fecha = dd.d;

-- ---------------------------------------------------------------- dim_inversor (SCD tipo 2)
-- Una fila por versión de configuración (silver.config_inversor). El manual del fabricante no es
-- público: los textos siguen la convención de inversores híbridos tipo SRNE (salida 0 = SOL,
-- 1 = UTI, 2 = SBU; carga 0 = solar, 1 = red, 2 = híbrida, 3 = solo solar) y se CONFIRMARON con
-- el comportamiento medido: con salida 2 la red aporta 0 % de la carga; con salida 0 el sol cubre
-- el mediodía y la red la noche mientras la batería sigue llena. Se conserva el código original.
INSERT INTO gold.dim_inversor (inversor_key, inversor_id, nombre, modelo, potencia_nominal_kw, capacidad_pv_kwp,
                               bateria_kwh, carga_principal, prioridad_salida, prioridad_salida_texto,
                               prioridad_carga, prioridad_carga_texto, soc_corte_pct, soc_paso_a_red_pct,
                               vigente_desde, vigente_hasta, es_actual)
SELECT row_number() OVER (ORDER BY c.inversor_id, c.vigente_desde),
       c.inversor_id, 'Inversor ' || c.inversor_id, 'SPI4880V150-500P', 8.0,
       current_setting('microrred.capacidad_pv')::numeric, 10.24,
       CASE c.inversor_id WHEN 1 THEN 'Estaciones de trabajo (CPU/GPU)' ELSE 'Aire acondicionado de la oficina' END,
       c.prioridad_salida,
       CASE c.prioridad_salida WHEN 0 THEN '0 · SOL: solar, luego red' WHEN 1 THEN '1 · UTI: red primero'
            WHEN 2 THEN '2 · SBU: solar, batería, red' ELSE 'Desconocida' END,
       c.prioridad_carga,
       CASE c.prioridad_carga WHEN 0 THEN '0 · Solar primero' WHEN 1 THEN '1 · Red primero'
            WHEN 2 THEN '2 · Híbrida (solar + red)' WHEN 3 THEN '3 · Solo solar' ELSE 'Desconocida' END,
       c.soc_corte_pct, c.soc_paso_a_red_pct,
       -- la primera versión cubre también los días anteriores al primer registro de settings
       CASE WHEN c.vigente_desde = min(c.vigente_desde) OVER (PARTITION BY c.inversor_id)
            THEN DATE '2024-01-01' ELSE c.vigente_desde END,
       c.vigente_hasta,
       c.vigente_hasta = DATE '9999-12-31'
FROM silver.config_inversor c;

-- ---------------------------------------------------------------- dim_tipo_evento
INSERT INTO gold.dim_tipo_evento VALUES
 (1, 'BAT_BAJA',       'Batería baja',                     'Operativo',     'Crítica',
     'SOC mínimo del minuto < ' || current_setting('microrred.soc_bajo') || ' %'),
 (2, 'SALIDA_APAGADA', 'Salida del inversor apagada',      'Operativo',     'Crítica',
     'Voltaje de salida promedio del minuto < 100 V (coincide 100 % con status.outstatus = 0)'),
 (3, 'RED_ANOMALA',    'Red pública fuera de tolerancia',  'Operativo',     'Advertencia',
     'Voltaje de red entre 50 y 190 V, o frecuencia fuera de 49,5–50,5 Hz con red presente'),
 (6, 'CORTE_RED',      'Red pública ausente',              'Operativo',     'Crítica',
     'Voltaje de red < 50 V: la planta opera aislada (solo sol y batería)'),
 (4, 'TEMP_ALTA',      'Temperatura alta del inversor',    'Operativo',     'Advertencia',
     'temper3 > ' || current_setting('microrred.temp_alta') || ' °C'),
 (5, 'SIN_DATOS',      'Pérdida de comunicación',          'Comunicación',  'Advertencia',
     'Más de ' || current_setting('microrred.hueco_min') || ' min sin lecturas del inversor');

-- Fallas/alarmas que REPORTA el inversor (fault_history): un tipo por código
INSERT INTO gold.dim_tipo_evento
SELECT 100 + codigo, 'FALLA_' || codigo, 'Código de falla/alarma ' || codigo || ' del inversor',
       'Reportado por el inversor', 'Sin clasificar',
       'Registro fault_history del equipo (el significado del código está en el manual del fabricante, no publicado)'
FROM (SELECT DISTINCT codigo FROM silver.falla_inversor) f;

-- ---------------------------------------------------------------- dim_fuente_contexto
INSERT INTO gold.dim_fuente_contexto
SELECT row_number() OVER (ORDER BY fuente), fuente,
       CASE WHEN fuente LIKE '%\_log' THEN 'Automática' ELSE 'Manual' END,
       CASE WHEN fuente LIKE 'workstation%' THEN split_part(fuente, '_', 1) END
FROM (SELECT DISTINCT fuente FROM silver.contexto) f;

-- ---------------------------------------------------------------- HECHO 1 · energía por hora
-- Se "densifica": cada inversor tiene TODAS las horas entre su primera y su última lectura,
-- aunque no haya datos (minutos_con_datos = 0). Así la disponibilidad se calcula sumando.
WITH m AS (
    SELECT l.*, (l.ts AT TIME ZONE current_setting('microrred.zona')) AS local_ts
    FROM silver.lectura_1min l
    WHERE l.origen = 'historico'
),
h AS (
    SELECT inversor_id, date_trunc('hour', local_ts) AS hora_local,
           sum(pv_energia_wh) / 1000 AS pv, sum(carga_energia_wh) / 1000 AS carga,
           sum(red_energia_wh) / 1000 AS red, sum(bat_carga_energia_wh) / 1000 AS bcar,
           sum(bat_desc_energia_wh) / 1000 AS bdes,
           avg(soc_pct) AS soc_prom, min(soc_min_pct) AS soc_min,
           (array_agg(soc_pct ORDER BY ts DESC) FILTER (WHERE soc_pct IS NOT NULL))[1] AS soc_fin,
           max(carga_max_w) AS carga_max,
           count(*) FILTER (WHERE n_lecturas > 0) AS min_datos,
           count(*) FILTER (WHERE soc_pct >= 98) AS min_lleno,
           sum(n_lecturas) AS validas, sum(n_recibidas) AS recibidas
    FROM m GROUP BY 1, 2
),
rejilla AS (
    SELECT inversor_id, generate_series(min(hora_local), max(hora_local), interval '1 hour') AS hora_local
    FROM h GROUP BY 1
)
INSERT INTO gold.fact_energia_hora
SELECT to_char(r.hora_local, 'YYYYMMDD')::int, extract(hour FROM r.hora_local)::smallint, di.inversor_key,
       round(coalesce(h.pv, 0), 4), round(coalesce(h.carga, 0), 4), round(coalesce(h.red, 0), 4),
       round(coalesce(h.bcar, 0), 4), round(coalesce(h.bdes, 0), 4),
       round(h.soc_prom, 1), h.soc_min, h.soc_fin, h.carga_max,
       coalesce(h.min_datos, 0), coalesce(h.min_lleno, 0), coalesce(h.validas, 0), coalesce(h.recibidas, 0),
       current_setting('microrred.lecturas_hora')::int
FROM rejilla r
LEFT JOIN h USING (inversor_id, hora_local)
JOIN gold.dim_inversor di ON di.inversor_id = r.inversor_id
                         AND r.hora_local::date BETWEEN di.vigente_desde AND di.vigente_hasta;

-- ---------------------------------------------------------------- HECHO 2 · eventos operativos
-- "Islas" de minutos consecutivos que cumplen la condición (gaps-and-islands con funciones de
-- ventana). Un evento es un intervalo con inicio, fin y duración; no una lectura.
WITH m AS (
    SELECT * FROM silver.lectura_1min WHERE origen = 'historico' AND n_lecturas > 0
),
condicion AS (
    SELECT inversor_id, ts, 'BAT_BAJA'::text AS codigo, soc_min_pct AS valor FROM m
     WHERE soc_min_pct < current_setting('microrred.soc_bajo')::numeric
    UNION ALL
    SELECT inversor_id, ts, 'SALIDA_APAGADA', salida_voltaje_v FROM m WHERE salida_voltaje_v < 100
    UNION ALL
    SELECT inversor_id, ts, 'RED_ANOMALA', red_voltaje_v FROM m
     WHERE red_voltaje_v >= 50 AND (red_voltaje_v < 190 OR red_frecuencia_hz NOT BETWEEN 49.5 AND 50.5)
    UNION ALL
    SELECT inversor_id, ts, 'CORTE_RED', red_voltaje_v FROM m WHERE red_voltaje_v < 50
    UNION ALL
    SELECT inversor_id, ts, 'TEMP_ALTA', temp_inversor_c FROM m
     WHERE temp_inversor_c > current_setting('microrred.temp_alta')::numeric
),
marcas AS (
    SELECT *, CASE WHEN ts - lag(ts) OVER w <= interval '2 minutes' THEN 0 ELSE 1 END AS nueva
    FROM condicion WINDOW w AS (PARTITION BY inversor_id, codigo ORDER BY ts)
),
islas AS (
    SELECT *, sum(nueva) OVER (PARTITION BY inversor_id, codigo ORDER BY ts) AS isla FROM marcas
),
eventos AS (
    SELECT inversor_id, codigo, min(ts) AS inicio, max(ts) + interval '1 minute' AS fin,
           CASE WHEN codigo IN ('TEMP_ALTA') THEN max(valor) ELSE min(valor) END AS extremo
    FROM islas GROUP BY inversor_id, codigo, isla
    UNION ALL
    SELECT inversor_id, 'SIN_DATOS', previo + interval '1 minute', ts, extract(epoch FROM ts - previo) / 60
    FROM (SELECT inversor_id, ts, lag(ts) OVER (PARTITION BY inversor_id ORDER BY ts) AS previo
          FROM silver.lectura_1min WHERE origen = 'historico') g
    WHERE ts - previo > make_interval(mins => current_setting('microrred.hueco_min')::int)
    UNION ALL
    SELECT inversor_id, 'FALLA_' || codigo, ts, ts, NULL FROM silver.falla_inversor
)
INSERT INTO gold.fact_evento
SELECT row_number() OVER (ORDER BY e.inicio, e.inversor_id, e.codigo),
       to_char(e.inicio AT TIME ZONE current_setting('microrred.zona'), 'YYYYMMDD')::int,
       extract(hour FROM e.inicio AT TIME ZONE current_setting('microrred.zona'))::smallint,
       di.inversor_key, te.tipo_evento_key, e.inicio, e.fin,
       round(extract(epoch FROM e.fin - e.inicio) / 60, 1), round(e.extremo, 2), 1
FROM eventos e
JOIN gold.dim_tipo_evento te ON te.codigo = e.codigo
JOIN gold.dim_inversor di ON di.inversor_id = e.inversor_id
 AND (e.inicio AT TIME ZONE current_setting('microrred.zona'))::date BETWEEN di.vigente_desde AND di.vigente_hasta;

-- ---------------------------------------------------------------- HECHO 3 · actividad de las cargas
-- Cada tarea/anotación del contexto con la carga MEDIDA mientras duró (en su inversor).
INSERT INTO gold.fact_actividad
SELECT c.contexto_id,
       to_char(c.inicio_ts AT TIME ZONE current_setting('microrred.zona'), 'YYYYMMDD')::int,
       extract(hour FROM c.inicio_ts AT TIME ZONE current_setting('microrred.zona'))::smallint,
       di.inversor_key, fu.fuente_key,
       coalesce(c.valor ->> 'context_type', c.valor ->> 'task_type',
                CASE WHEN c.inversor_id IS NULL THEN 'Calendario del campus' ELSE 'Anotación manual' END),
       c.valor ->> 'llm_estimated_task_effort',
       round(extract(epoch FROM c.fin_ts - c.inicio_ts) / 60, 1),
       round(med.carga_prom, 1), round(med.energia, 4), 1
FROM silver.contexto c
JOIN gold.dim_fuente_contexto fu ON fu.fuente = c.fuente
LEFT JOIN gold.dim_inversor di ON di.inversor_id = c.inversor_id
 AND (c.inicio_ts AT TIME ZONE current_setting('microrred.zona'))::date BETWEEN di.vigente_desde AND di.vigente_hasta
LEFT JOIN LATERAL (
    SELECT avg(l.carga_potencia_w) AS carga_prom, sum(l.carga_energia_wh) / 1000 AS energia
    FROM silver.lectura_1min l
    WHERE c.inversor_id IS NOT NULL
      AND c.fin_ts - c.inicio_ts <= interval '7 days'
      AND l.inversor_id = c.inversor_id AND l.origen = 'historico'
      AND l.ts >= date_trunc('minute', c.inicio_ts) AND l.ts <= c.fin_ts
) med ON true;

-- Permisos de lectura (tablas recreadas o nuevas)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bi_lector') THEN
        GRANT SELECT ON ALL TABLES IN SCHEMA silver, gold, ops TO bi_lector;
    END IF;
END $$;
