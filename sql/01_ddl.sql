-- =====================================================================
-- SolarBI Pascual · DDL de las capas Silver y Gold (PostgreSQL 14+)
-- Idempotente: se puede ejecutar cuantas veces se quiera.
-- La capa Bronze vive como archivo (data/bronze/telemetria.csv).
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS dwh;

-- ---------------------------------------------------------------------
-- SILVER: lecturas limpias cada 5 minutos (una fila por ts y dispositivo)
-- ts se guarda con zona horaria (America/Bogota, UTC-5) para que Grafana
-- y Power BI muestren la hora local correcta.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS silver.lectura_5min (
    ts               TIMESTAMPTZ   NOT NULL,
    dispositivo_id   INTEGER       NOT NULL,
    p_ac_kw          NUMERIC(8,3)  NOT NULL CHECK (p_ac_kw >= 0),
    irradiancia_wm2  NUMERIC(7,1)  NOT NULL CHECK (irradiancia_wm2 BETWEEN 0 AND 1500),
    temp_modulo_c    NUMERIC(5,1)  NOT NULL,
    energia_kwh      NUMERIC(10,5) NOT NULL,          -- p_ac_kw * 5/60
    cargado_en       TIMESTAMPTZ   NOT NULL DEFAULT now(),
    CONSTRAINT pk_lectura_5min PRIMARY KEY (ts, dispositivo_id)
);

-- ---------------------------------------------------------------------
-- GOLD (dwh): esquema estrella mínimo
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dwh.dim_fecha (
    fecha_key     INTEGER     PRIMARY KEY,            -- AAAAMMDD
    fecha         DATE        NOT NULL UNIQUE,
    anio          SMALLINT    NOT NULL,
    mes           SMALLINT    NOT NULL,
    nombre_mes    VARCHAR(12) NOT NULL,
    dia           SMALLINT    NOT NULL,
    dia_semana    SMALLINT    NOT NULL,               -- 1 = lunes ... 7 = domingo
    nombre_dia    VARCHAR(12) NOT NULL
);

CREATE TABLE IF NOT EXISTS dwh.dim_dispositivo (
    dispositivo_key  INTEGER      PRIMARY KEY,        -- clave sustituta
    dispositivo_id   INTEGER      NOT NULL UNIQUE,    -- clave natural de la fuente
    nombre           VARCHAR(40)  NOT NULL,
    tipo             VARCHAR(20)  NOT NULL,
    sitio            VARCHAR(40)  NOT NULL,
    capacidad_kwp    NUMERIC(6,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS dwh.fact_energia_dia (
    fecha_key             INTEGER       NOT NULL REFERENCES dwh.dim_fecha (fecha_key),
    dispositivo_key       INTEGER       NOT NULL REFERENCES dwh.dim_dispositivo (dispositivo_key),
    energia_kwh           NUMERIC(10,3) NOT NULL,
    p_max_kw              NUMERIC(8,3)  NOT NULL,
    irradiacion_kwh_m2    NUMERIC(8,3)  NOT NULL,
    yield_kwh_kwp         NUMERIC(8,3)  NOT NULL,     -- energía / capacidad instalada
    performance_ratio     NUMERIC(6,4),               -- yield / irradiación (kWh/m² ÷ 1 kW/m²)
    n_lecturas_validas    INTEGER       NOT NULL,
    n_lecturas_esperadas  INTEGER       NOT NULL,     -- 288 = 24 h × 12 lecturas/h
    pct_datos_validos     NUMERIC(5,2)  NOT NULL,
    actualizado_en        TIMESTAMPTZ   NOT NULL DEFAULT now(),
    CONSTRAINT pk_fact_energia_dia PRIMARY KEY (fecha_key, dispositivo_key)
);

-- ---------------------------------------------------------------------
-- Bitácora de ejecuciones del ETL (linaje y métricas de calidad)
-- Esta es la única tabla que crece en cada corrida, a propósito.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dwh.etl_ejecucion (
    ejecucion_id          SERIAL        PRIMARY KEY,
    inicio                TIMESTAMPTZ   NOT NULL,
    fin                   TIMESTAMPTZ   NOT NULL,
    archivo_origen        TEXT          NOT NULL,
    filas_leidas          INTEGER       NOT NULL,
    rechazo_duplicados    INTEGER       NOT NULL,
    rechazo_faltantes     INTEGER       NOT NULL,
    rechazo_rango         INTEGER       NOT NULL,
    filas_validas         INTEGER       NOT NULL,
    pct_datos_validos     NUMERIC(5,2)  NOT NULL,
    filas_silver_total    INTEGER       NOT NULL,
    filas_fact_total      INTEGER       NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_lectura_5min_disp_ts
    ON silver.lectura_5min (dispositivo_id, ts);
