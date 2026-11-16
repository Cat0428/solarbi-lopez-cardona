-- =====================================================================================
-- Taller 6 · Consultas SQL de negocio (ejecutar en DBeaver con el usuario bi_lector)
-- Todas leen de Gold, salvo las de JSON (silver.contexto) y la de estado operativo.
-- La tarifa del escenario está en el ConfigMap (TARIFA_COP_KWH = 930); aquí se fija en un CTE.
-- =====================================================================================

-- Q1 · Balance energético y KPIs por inversor y mes (agregación)
--      fracción solar = solar / (solar + red) · dependencia de red = red / carga (puede pasar de
--      100 %: la red también carga la batería y cubre las pérdidas del inversor) ·
--      autosuficiencia = max(0, 1 − dependencia)
SELECT f.anio_mes, i.nombre AS inversor,
       round(sum(e.energia_pv_kwh), 1)    AS solar_kwh,
       round(sum(e.energia_carga_kwh), 1) AS carga_kwh,
       round(sum(e.energia_red_kwh), 1)   AS red_kwh,
       round(100 * sum(e.energia_red_kwh) / nullif(sum(e.energia_carga_kwh), 0), 1) AS dependencia_red_pct,
       round(100 * greatest(0, 1 - sum(e.energia_red_kwh) / nullif(sum(e.energia_carga_kwh), 0)), 1) AS autosuficiencia_pct,
       round(100 * sum(e.energia_pv_kwh) / nullif(sum(e.energia_pv_kwh) + sum(e.energia_red_kwh), 0), 1) AS fraccion_solar_pct,
       round(100.0 * sum(e.minutos_con_datos) / (count(*) * 60), 1)                       AS disponibilidad_pct,
       round(100.0 * sum(e.lecturas_validas) / nullif(sum(e.lecturas_recibidas), 0), 2)  AS datos_validos_pct
FROM gold.fact_energia_hora e
JOIN gold.dim_fecha f    USING (fecha_key)
JOIN gold.dim_inversor i USING (inversor_key)
GROUP BY f.anio_mes, i.nombre
ORDER BY f.anio_mes, i.nombre;

-- Q2 · Comparativo entre periodos: energía de red de cada mes frente al mes anterior (LAG)
WITH mes AS (
    SELECT f.anio_mes, i.nombre AS inversor, sum(e.energia_red_kwh) AS red_kwh,
           sum(e.minutos_con_datos) / 60.0 AS horas_con_datos
    FROM gold.fact_energia_hora e
    JOIN gold.dim_fecha f USING (fecha_key) JOIN gold.dim_inversor i USING (inversor_key)
    GROUP BY 1, 2
)
SELECT anio_mes, inversor, round(red_kwh, 1) AS red_kwh,
       round(red_kwh / nullif(horas_con_datos, 0) * 24, 2) AS red_kwh_por_dia_con_datos,   -- normaliza huecos
       round(lag(red_kwh) OVER w, 1) AS red_kwh_mes_anterior,
       round(100 * (red_kwh / nullif(lag(red_kwh) OVER w, 0) - 1), 1) AS variacion_pct
FROM mes
WINDOW w AS (PARTITION BY inversor ORDER BY anio_mes)
ORDER BY inversor, anio_mes;

-- Q3 · Perfil horario (franja) con ranking de horas de mayor compra a la red (RANK + PARTITION)
SELECT i.nombre AS inversor, h.hora_texto, h.franja,
       round(avg(e.energia_pv_kwh), 3)  AS solar_kwh_prom,
       round(avg(e.energia_carga_kwh), 3) AS carga_kwh_prom,
       round(avg(e.energia_red_kwh), 3) AS red_kwh_prom,
       rank() OVER (PARTITION BY i.nombre ORDER BY avg(e.energia_red_kwh) DESC) AS ranking_red
FROM gold.fact_energia_hora e
JOIN gold.dim_hora h USING (hora_key) JOIN gold.dim_inversor i USING (inversor_key)
WHERE e.minutos_con_datos >= 45                      -- solo horas con datos suficientes
GROUP BY i.nombre, h.hora_key, h.hora_texto, h.franja
ORDER BY i.nombre, h.hora_key;

-- Q4 · Indicador económico en COP: costo de la red y ahorro por energía solar, con acumulado
--      mensual (SUM OVER) y promedio móvil de 7 días del costo diario
WITH tarifa AS (SELECT 930::numeric AS cop_kwh),
dia AS (
    SELECT f.fecha, f.anio_mes, sum(e.energia_red_kwh) AS red_kwh, sum(e.energia_pv_kwh) AS pv_kwh
    FROM gold.fact_energia_hora e JOIN gold.dim_fecha f USING (fecha_key)
    GROUP BY f.fecha, f.anio_mes
)
SELECT fecha,
       round(red_kwh * t.cop_kwh)  AS costo_red_cop,
       round(pv_kwh * t.cop_kwh)   AS ahorro_solar_cop,
       round(sum(red_kwh * t.cop_kwh) OVER (PARTITION BY anio_mes ORDER BY fecha)) AS costo_red_acumulado_mes,
       round(avg(red_kwh * t.cop_kwh) OVER (ORDER BY fecha ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)) AS costo_movil_7d
FROM dia, tarifa t
ORDER BY fecha;

-- Q5 · Energía solar desaprovechada (indicador propio): horas de sol con batería llena.
--      Con SOC ≥ 98 % y sin exportación a la red, el inversor recorta el arreglo solar.
SELECT i.nombre AS inversor, f.anio_mes,
       round(100.0 * sum(e.minutos_soc_lleno) FILTER (WHERE h.es_hora_solar)
             / nullif(sum(e.minutos_con_datos) FILTER (WHERE h.es_hora_solar), 0), 1) AS pct_horas_sol_bateria_llena,
       round(sum(e.energia_pv_kwh) / nullif(i.capacidad_pv_kwp * count(DISTINCT e.fecha_key), 0), 2) AS rendimiento_kwh_kwp_dia
FROM gold.fact_energia_hora e
JOIN gold.dim_fecha f USING (fecha_key) JOIN gold.dim_hora h USING (hora_key)
JOIN gold.dim_inversor i USING (inversor_key)
WHERE e.minutos_con_datos > 0
GROUP BY i.nombre, i.capacidad_pv_kwp, f.anio_mes
ORDER BY 1, 2;

-- Q6 · Eventos operativos por tipo y mes, con el evento más largo de cada tipo (ROW_NUMBER)
WITH ev AS (
    SELECT te.nombre AS tipo, i.nombre AS inversor, f.anio_mes, e.inicio_ts, e.duracion_min, e.valor_extremo,
           row_number() OVER (PARTITION BY te.nombre, i.nombre ORDER BY e.duracion_min DESC) AS rn
    FROM gold.fact_evento e
    JOIN gold.dim_tipo_evento te USING (tipo_evento_key)
    JOIN gold.dim_inversor i USING (inversor_key)
    JOIN gold.dim_fecha f USING (fecha_key)
)
SELECT tipo, inversor, count(*) AS eventos, round(sum(duracion_min) / 60, 1) AS horas_totales,
       max(duracion_min) FILTER (WHERE rn = 1) AS duracion_max_min,
       min(inicio_ts)    FILTER (WHERE rn = 1) AS inicio_del_mas_largo
FROM ev GROUP BY tipo, inversor ORDER BY eventos DESC;

-- Q7 · JSON (operadores nativos de PostgreSQL sobre JSONB)
--      ¿Qué tipo de tarea explica la carga del inversor 1? Filtro con @> (contención, usa el
--      índice GIN), extracción con ->> y conversión de un campo numérico del JSON.
SELECT c.valor ->> 'task_type'                         AS tipo_tarea,
       c.valor ->> 'llm_estimated_task_effort'         AS esfuerzo,
       count(*)                                        AS tareas,
       round(avg((c.valor ->> 'cpu_cores_active')::int), 1) AS nucleos_prom,
       round(avg(a.carga_prom_w), 0)                   AS carga_prom_w,
       round(sum(a.energia_carga_kwh), 2)              AS energia_kwh
FROM silver.contexto c
JOIN gold.fact_actividad a USING (contexto_id)
WHERE c.valor @> '{"inverter": 1}'
  AND c.valor ? 'task_type'                            -- el JSON tiene la llave
GROUP BY 1, 2
ORDER BY energia_kwh DESC NULLS LAST;

-- Q8 · JSON: modelos de red neuronal entrenados (campos anidados) y su consumo
SELECT c.valor ->> 'model'   AS modelo,
       c.valor ->> 'dataset' AS dataset,
       count(*) AS entrenamientos,
       round(avg(a.duracion_min), 1)  AS duracion_prom_min,
       round(avg(a.carga_prom_w), 0)  AS carga_prom_w
FROM silver.contexto c JOIN gold.fact_actividad a USING (contexto_id)
WHERE c.valor ->> 'task_type' = 'CNN fitting, GPU load'
GROUP BY 1, 2
ORDER BY entrenamientos DESC
LIMIT 15;

-- Q9 · Días festivos o de calendario académico frente a días normales (dimensión enriquecida)
SELECT CASE WHEN f.es_festivo THEN 'Festivo' WHEN f.es_fin_semana THEN 'Fin de semana' ELSE 'Laboral' END AS tipo_dia,
       i.nombre AS inversor,
       count(DISTINCT f.fecha) AS dias,
       round(sum(e.energia_carga_kwh) / count(DISTINCT f.fecha), 2) AS carga_kwh_por_dia
FROM gold.fact_energia_hora e
JOIN gold.dim_fecha f USING (fecha_key) JOIN gold.dim_inversor i USING (inversor_key)
WHERE e.minutos_con_datos > 0
GROUP BY 1, 2 ORDER BY 2, 1;
