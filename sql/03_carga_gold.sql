-- =====================================================================
-- SolarBI Pascual · Carga de la capa Gold a partir de Silver
-- run_etl.py lo ejecuta después de cargar silver.lectura_5min.
-- Todas las sentencias son UPSERT: correrlas N veces deja el mismo
-- resultado que correrlas una vez (carga idempotente).
-- =====================================================================

-- 1) Dimensión dispositivo (catálogo maestro del inversor simulado)
INSERT INTO dwh.dim_dispositivo (dispositivo_key, dispositivo_id, nombre, tipo, sitio, capacidad_kwp)
VALUES (1, 1, 'INV-01', 'inversor', 'Sede Robledo', 5.00)
ON CONFLICT (dispositivo_key) DO UPDATE
SET dispositivo_id = EXCLUDED.dispositivo_id,
    nombre         = EXCLUDED.nombre,
    tipo           = EXCLUDED.tipo,
    sitio          = EXCLUDED.sitio,
    capacidad_kwp  = EXCLUDED.capacidad_kwp;

-- 2) Dimensión fecha: una fila por cada día presente en Silver
INSERT INTO dwh.dim_fecha (fecha_key, fecha, anio, mes, nombre_mes, dia, dia_semana, nombre_dia)
SELECT DISTINCT
       to_char(f, 'YYYYMMDD')::int,
       f,
       extract(year  FROM f)::smallint,
       extract(month FROM f)::smallint,
       (ARRAY['enero','febrero','marzo','abril','mayo','junio','julio',
              'agosto','septiembre','octubre','noviembre','diciembre'])[extract(month FROM f)::int],
       extract(day    FROM f)::smallint,
       extract(isodow FROM f)::smallint,
       (ARRAY['lunes','martes','miércoles','jueves','viernes','sábado','domingo'])[extract(isodow FROM f)::int]
FROM (SELECT (ts AT TIME ZONE 'America/Bogota')::date AS f FROM silver.lectura_5min) d
ON CONFLICT (fecha_key) DO NOTHING;

-- 3) Hecho diario: energía = Σ (potencia × 5/60 h) de las lecturas válidas
INSERT INTO dwh.fact_energia_dia AS t (
       fecha_key, dispositivo_key, energia_kwh, p_max_kw, irradiacion_kwh_m2,
       yield_kwh_kwp, performance_ratio, n_lecturas_validas,
       n_lecturas_esperadas, pct_datos_validos, actualizado_en)
SELECT to_char(d.fecha, 'YYYYMMDD')::int                         AS fecha_key,
       dd.dispositivo_key,
       round(d.energia_kwh, 3),
       d.p_max_kw,
       round(d.irradiacion_kwh_m2, 3),
       round(d.energia_kwh / dd.capacidad_kwp, 3)                 AS yield_kwh_kwp,
       round((d.energia_kwh / dd.capacidad_kwp)
             / NULLIF(d.irradiacion_kwh_m2, 0), 4)                AS performance_ratio,
       d.n_validas,
       288,
       round(100.0 * d.n_validas / 288, 2)                        AS pct_datos_validos,
       now()
FROM (
    SELECT (ts AT TIME ZONE 'America/Bogota')::date AS fecha,
           dispositivo_id,
           sum(energia_kwh)                         AS energia_kwh,
           max(p_ac_kw)                             AS p_max_kw,
           sum(irradiancia_wm2 * 5.0 / 60) / 1000   AS irradiacion_kwh_m2,
           count(*)                                 AS n_validas
    FROM silver.lectura_5min
    GROUP BY 1, 2
) d
JOIN dwh.dim_dispositivo dd ON dd.dispositivo_id = d.dispositivo_id
ON CONFLICT (fecha_key, dispositivo_key) DO UPDATE
SET energia_kwh          = EXCLUDED.energia_kwh,
    p_max_kw             = EXCLUDED.p_max_kw,
    irradiacion_kwh_m2   = EXCLUDED.irradiacion_kwh_m2,
    yield_kwh_kwp        = EXCLUDED.yield_kwh_kwp,
    performance_ratio    = EXCLUDED.performance_ratio,
    n_lecturas_validas   = EXCLUDED.n_lecturas_validas,
    n_lecturas_esperadas = EXCLUDED.n_lecturas_esperadas,
    pct_datos_validos    = EXCLUDED.pct_datos_validos,
    actualizado_en       = EXCLUDED.actualizado_en;
