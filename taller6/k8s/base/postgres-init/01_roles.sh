#!/bin/bash
# =====================================================================
# Taller 6 · Primer arranque de PostgreSQL (solo corre con el volumen vacío)
# - Esquemas de las capas Silver y Gold.
# - Rol bi_lector de SOLO LECTURA para Grafana, Power BI y DBeaver de consulta.
# La contraseña llega por variable de entorno desde el Secret de Kubernetes
# (o desde credenciales.env en docker compose); nunca queda en el repositorio.
# El DDL de tablas lo aplica el ETL (idempotente), no este script.
# =====================================================================
set -e
psql -v ON_ERROR_STOP=1 \
     -v lector_pw="$BI_LECTOR_PASSWORD" -v dbname="$POSTGRES_DB" \
     --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-'EOSQL'
	CREATE SCHEMA IF NOT EXISTS silver;
	CREATE SCHEMA IF NOT EXISTS gold;
	CREATE SCHEMA IF NOT EXISTS ops;

	SELECT format('CREATE ROLE bi_lector LOGIN PASSWORD %L', :'lector_pw')
	WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bi_lector')
	\gexec

	REVOKE CREATE ON SCHEMA public FROM PUBLIC;
	GRANT CONNECT ON DATABASE :"dbname" TO bi_lector;
	GRANT USAGE ON SCHEMA silver, gold, ops TO bi_lector;
	ALTER DEFAULT PRIVILEGES IN SCHEMA silver GRANT SELECT ON TABLES TO bi_lector;
	ALTER DEFAULT PRIVILEGES IN SCHEMA gold   GRANT SELECT ON TABLES TO bi_lector;
	ALTER DEFAULT PRIVILEGES IN SCHEMA ops    GRANT SELECT ON TABLES TO bi_lector;
EOSQL
