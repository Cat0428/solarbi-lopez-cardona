#!/bin/bash
# =====================================================================
# SolarBI Pascual · Rol de solo lectura para Grafana y Power BI
# Docker lo ejecuta automáticamente la primera vez que se crea el volumen
# de PostgreSQL. La contraseña llega por variable de entorno (.env), nunca
# queda escrita en el repositorio.
# =====================================================================
set -e

psql -v ON_ERROR_STOP=1 \
     -v lector_pw="$BI_LECTOR_PASSWORD" -v dbname="$POSTGRES_DB" \
     --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-'EOSQL'
	SELECT format('CREATE ROLE bi_lector LOGIN PASSWORD %L', :'lector_pw')
	WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bi_lector')
	\gexec

	GRANT CONNECT ON DATABASE :"dbname" TO bi_lector;
	GRANT USAGE ON SCHEMA silver, dwh TO bi_lector;
	GRANT SELECT ON ALL TABLES IN SCHEMA silver, dwh TO bi_lector;
	-- Tablas que el ETL cree en el futuro también quedan legibles
	ALTER DEFAULT PRIVILEGES IN SCHEMA silver GRANT SELECT ON TABLES TO bi_lector;
	ALTER DEFAULT PRIVILEGES IN SCHEMA dwh    GRANT SELECT ON TABLES TO bi_lector;
EOSQL
