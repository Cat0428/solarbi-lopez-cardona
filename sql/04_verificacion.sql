-- =====================================================================
-- Verificación de la carga idempotente. Ejecutar después de correr
-- run_etl.py dos veces: los conteos de silver y dwh deben ser iguales,
-- y dwh.etl_ejecucion debe mostrar dos corridas con los mismos números.
-- =====================================================================
SELECT 'silver.lectura_5min'  AS tabla, count(*) AS filas FROM silver.lectura_5min
UNION ALL
SELECT 'dwh.fact_energia_dia', count(*) FROM dwh.fact_energia_dia
UNION ALL
SELECT 'dwh.dim_fecha',        count(*) FROM dwh.dim_fecha
UNION ALL
SELECT 'dwh.dim_dispositivo',  count(*) FROM dwh.dim_dispositivo;

-- Historial de corridas (linaje): cada corrida reporta las mismas cifras
SELECT ejecucion_id, inicio AT TIME ZONE 'America/Bogota' AS inicio_local,
       filas_leidas, rechazo_duplicados, rechazo_faltantes, rechazo_rango,
       filas_validas, pct_datos_validos, filas_silver_total, filas_fact_total
FROM dwh.etl_ejecucion
ORDER BY ejecucion_id;

-- Resumen diario (lo que consume Power BI)
SELECT d.fecha, f.energia_kwh, f.yield_kwh_kwp, f.performance_ratio,
       f.n_lecturas_validas, f.pct_datos_validos
FROM dwh.fact_energia_dia f
JOIN dwh.dim_fecha d USING (fecha_key)
ORDER BY d.fecha;

-- Consulta de la pregunta D4: potencia promedio por hora (versión PostgreSQL
-- pura, sin macros de Grafana)
SELECT date_trunc('hour', ts AT TIME ZONE 'America/Bogota') AS hora,
       round(avg(p_ac_kw), 3)                               AS potencia_promedio_kw
FROM silver.lectura_5min
GROUP BY 1
ORDER BY 1;
