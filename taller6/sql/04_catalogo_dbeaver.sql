-- =====================================================================================
-- Taller 6 · Evidencias de la base de datos desde DBeaver (punto F)
-- Ejecutar en DBeaver con la conexión "Microrred · consulta (bi_lector)".
-- Solo lee el catálogo de PostgreSQL y los datos: no modifica nada.
-- Cada bloque se ejecuta con Ctrl+Enter (sentencia actual) y su resultado sirve de captura.
-- =====================================================================================

-- E1 · Inventario del modelo: tablas por capa, filas estimadas y tamaño en disco
SELECT n.nspname                                   AS capa,
       c.relname                                   AS tabla,
       c.reltuples::bigint                         AS filas_estimadas,
       pg_size_pretty(pg_total_relation_size(c.oid)) AS tamano_total
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind = 'r'
  AND n.nspname IN ('silver', 'gold', 'ops')
ORDER BY n.nspname, pg_total_relation_size(c.oid) DESC;

-- E2 · Conteo exacto de las tablas Gold (el modelo en estrella que consume Power BI)
SELECT 'dim_fecha'          AS tabla, count(*) AS filas FROM gold.dim_fecha
UNION ALL SELECT 'dim_hora',            count(*) FROM gold.dim_hora
UNION ALL SELECT 'dim_inversor',        count(*) FROM gold.dim_inversor
UNION ALL SELECT 'dim_tipo_evento',     count(*) FROM gold.dim_tipo_evento
UNION ALL SELECT 'dim_fuente_contexto', count(*) FROM gold.dim_fuente_contexto
UNION ALL SELECT 'fact_energia_hora',   count(*) FROM gold.fact_energia_hora
UNION ALL SELECT 'fact_evento',         count(*) FROM gold.fact_evento
UNION ALL SELECT 'fact_actividad',      count(*) FROM gold.fact_actividad;

-- E3 · Restricciones: llaves primarias (p), foráneas (f), únicas (u) y CHECK (c) de cada tabla.
--      Se lee pg_constraint y no information_schema.table_constraints, porque esta última
--      oculta las tablas en las que el rol solo tiene SELECT (caso de bi_lector).
SELECT n.nspname                  AS capa,
       c.conrelid::regclass       AS tabla,
       CASE c.contype WHEN 'p' THEN 'PRIMARY KEY' WHEN 'f' THEN 'FOREIGN KEY'
                      WHEN 'u' THEN 'UNIQUE'      ELSE 'CHECK' END AS tipo,
       c.conname                  AS restriccion,
       pg_get_constraintdef(c.oid) AS definicion
FROM pg_constraint c
JOIN pg_namespace n ON n.oid = c.connamespace
WHERE n.nspname IN ('silver', 'gold', 'ops')
  AND c.contype IN ('p', 'f', 'u', 'c')
ORDER BY 1, 2::text, 3;

-- E4 · Índices y su tipo (B-tree para llaves y filtros, BRIN para tiempo, GIN para JSONB)
SELECT schemaname AS capa,
       tablename  AS tabla,
       indexname  AS indice,
       split_part(split_part(indexdef, 'USING ', 2), ' ', 1) AS tipo,
       pg_size_pretty(pg_relation_size(format('%I.%I', schemaname, indexname)::regclass)) AS tamano,
       indexdef   AS definicion
FROM pg_indexes
WHERE schemaname IN ('silver', 'gold', 'ops')
ORDER BY schemaname, tablename, indexname;

-- E5 · Índice GIN del JSON (operador @> de la consulta Q7).
--      a) Plan real. silver.contexto es pequeña (decenas de miles de filas), así que el
--         planificador puede preferir "Seq Scan": leerla entera cuesta menos que ir al índice.
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF)
SELECT count(*) FROM silver.contexto WHERE valor @> '{"inverter": 1}';

--      b) Prueba de que el índice sí sirve al operador @>: se desactiva el Seq Scan solo dentro
--         de esta transacción. Buscar "Bitmap Index Scan on gin_contexto_valor".
--         (Ejecutar las cuatro líneas juntas con Alt+X.)
BEGIN;
SET LOCAL enable_seqscan = off;
EXPLAIN (COSTS OFF) SELECT count(*) FROM silver.contexto WHERE valor @> '{"inverter": 1}';
ROLLBACK;

-- E6 · El índice BRIN sobre el tiempo: rango de un día en la tabla Silver de 1 minuto
--      Buscar "Bitmap Index Scan on brin_lectura_1min_ts".
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF)
SELECT count(*) AS minutos, round(avg(soc_pct), 1) AS soc_prom
FROM silver.lectura_1min
WHERE ts >= '2025-09-01 00:00+08' AND ts < '2025-09-02 00:00+08';

-- E7 · Seguridad: privilegios efectivos del rol de consulta (solo SELECT, sin escritura)
SELECT table_schema AS capa,
       count(*) FILTER (WHERE privilege_type = 'SELECT')                 AS tablas_con_select,
       count(*) FILTER (WHERE privilege_type IN ('INSERT', 'UPDATE', 'DELETE', 'TRUNCATE')) AS permisos_escritura
FROM information_schema.role_table_grants
WHERE grantee = 'bi_lector'
GROUP BY table_schema
ORDER BY table_schema;

-- E8 · Linaje: últimas corridas del ETL y su resultado
SELECT ejecucion_id, inicio, fin, fin - inicio AS duracion, estado, archivo_bronze,
       left(sha256_bronze, 12) AS sha256_inicio
FROM ops.etl_ejecucion
ORDER BY ejecucion_id DESC
LIMIT 5;

-- E9 · Datos en vivo del simulador (para mostrar durante la sustentación)
SELECT inversor_id, max(ts) AT TIME ZONE 'America/Bogota' AS ultimo_minuto_colombia,
       count(*) AS minutos_simulados
FROM silver.lectura_1min
WHERE origen = 'simulador'
GROUP BY inversor_id;
