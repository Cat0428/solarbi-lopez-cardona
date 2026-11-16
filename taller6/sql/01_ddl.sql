-- =====================================================================================
-- Taller 6 · Microrred híbrida OpenCEM · DDL de las capas Silver, Gold y Ops (PostgreSQL 16)
-- Idempotente: lo ejecuta el ETL al inicio de cada corrida (CREATE ... IF NOT EXISTS).
-- La capa Bronze NO vive en PostgreSQL: es el archivo opencem-v1.0.0.sqlite (solo lectura).
--
-- Convención de tiempo: read_ts de la fuente es época Unix (UTC). La microrred está en
-- Shenzhen (UTC+8), así que las llaves de fecha y hora del modelo se calculan en hora LOCAL
-- DEL SITIO (Asia/Shanghai): el "día solar" de la planta no coincide con el día de Colombia.
-- =====================================================================================

CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
CREATE SCHEMA IF NOT EXISTS ops;

-- -------------------------------------------------------------------------------------
-- OPS: linaje y auditoría de cada corrida del ETL (la única tabla que crece a propósito)
-- -------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ops.etl_ejecucion (
    ejecucion_id     BIGSERIAL    PRIMARY KEY,
    inicio           TIMESTAMPTZ  NOT NULL,
    fin              TIMESTAMPTZ,
    archivo_bronze   TEXT         NOT NULL,
    sha256_bronze    TEXT,
    estado           VARCHAR(12)  NOT NULL CHECK (estado IN ('en curso', 'ok', 'error')),
    mensaje          TEXT
);

-- Conteo antes/después de cada regla de calidad, por corrida (evidencia del punto E)
CREATE TABLE IF NOT EXISTS ops.etl_regla (
    ejecucion_id     BIGINT       NOT NULL REFERENCES ops.etl_ejecucion ON DELETE CASCADE,
    orden            SMALLINT     NOT NULL,
    regla            VARCHAR(12)  NOT NULL,
    descripcion      TEXT         NOT NULL,
    accion           VARCHAR(12)  NOT NULL CHECK (accion IN ('elimina', 'corrige', 'marca', 'informa')),
    filas_antes      BIGINT       NOT NULL,
    filas_despues    BIGINT       NOT NULL,
    filas_afectadas  BIGINT       NOT NULL,
    PRIMARY KEY (ejecucion_id, orden)
);

-- Conciliación Bronze ↔ Silver ↔ Gold (punto E)
CREATE TABLE IF NOT EXISTS ops.conciliacion (
    ejecucion_id     BIGINT       NOT NULL REFERENCES ops.etl_ejecucion ON DELETE CASCADE,
    control          VARCHAR(60)  NOT NULL,
    valor_origen     NUMERIC(18,4),
    valor_destino    NUMERIC(18,4),
    diferencia       NUMERIC(18,4) GENERATED ALWAYS AS (valor_destino - valor_origen) STORED,
    explicacion      TEXT,
    PRIMARY KEY (ejecucion_id, control)
);

-- Conciliación mensual contra los contadores de energía del propio inversor (statistics)
CREATE TABLE IF NOT EXISTS ops.conciliacion_contador (
    ejecucion_id          BIGINT        NOT NULL REFERENCES ops.etl_ejecucion ON DELETE CASCADE,
    inversor_id           SMALLINT      NOT NULL,
    mes                   CHAR(7)       NOT NULL,
    variable              VARCHAR(30)   NOT NULL,
    energia_contador_kwh  NUMERIC(12,3) NOT NULL,
    energia_integrada_kwh NUMERIC(12,3) NOT NULL,
    horas_ventana         NUMERIC(8,1)  NOT NULL,
    diferencia_pct        NUMERIC(8,2)  GENERATED ALWAYS AS
        (CASE WHEN energia_contador_kwh <> 0
              THEN 100 * (energia_integrada_kwh - energia_contador_kwh) / energia_contador_kwh END) STORED,
    PRIMARY KEY (ejecucion_id, inversor_id, mes, variable)
);

-- -------------------------------------------------------------------------------------
-- SILVER: lecturas limpias agregadas a 1 minuto (decisión justificada en el informe)
-- Grano: 1 fila por inversor y minuto (instante UTC truncado al minuto).
-- Alimenta a Grafana (casi tiempo real) y es la base de la capa Gold.
-- origen = 'historico' (ETL) o 'simulador' (streaming); el ETL solo reescribe lo histórico.
-- -------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS silver.lectura_1min (
    ts                    TIMESTAMPTZ   NOT NULL,
    inversor_id           SMALLINT      NOT NULL CHECK (inversor_id IN (1, 2)),
    origen                VARCHAR(10)   NOT NULL DEFAULT 'historico' CHECK (origen IN ('historico', 'simulador')),
    n_recibidas           SMALLINT      NOT NULL CHECK (n_recibidas > 0),    -- lecturas únicas en el minuto
    n_lecturas            SMALLINT      NOT NULL CHECK (n_lecturas BETWEEN 0 AND n_recibidas), -- válidas
    segundos_cubiertos    NUMERIC(6,1)  NOT NULL CHECK (segundos_cubiertos BETWEEN 0 AND 120),
    soc_pct               NUMERIC(5,1)  CHECK (soc_pct BETWEEN 0 AND 100),
    soc_min_pct           NUMERIC(5,1),
    bat_voltaje_v         NUMERIC(5,2),
    bat_corriente_a       NUMERIC(6,2),        -- + descarga / - carga (convención de la fuente)
    temp_inversor_c       NUMERIC(5,1),
    pv_potencia_w         NUMERIC(8,1)  CHECK (pv_potencia_w >= 0),
    carga_potencia_w      NUMERIC(8,1)  CHECK (carga_potencia_w >= 0),
    carga_max_w           NUMERIC(8,1),
    red_potencia_w        NUMERIC(8,1)  CHECK (red_potencia_w >= 0),
    bat_potencia_w        NUMERIC(8,1),        -- V·I: + descarga / - carga
    salida_voltaje_v      NUMERIC(5,1),
    red_voltaje_v         NUMERIC(5,1),
    red_frecuencia_hz     NUMERIC(5,2),
    pv_energia_wh         NUMERIC(10,3) NOT NULL DEFAULT 0,
    carga_energia_wh      NUMERIC(10,3) NOT NULL DEFAULT 0,
    red_energia_wh        NUMERIC(10,3) NOT NULL DEFAULT 0,
    bat_carga_energia_wh  NUMERIC(10,3) NOT NULL DEFAULT 0,
    bat_desc_energia_wh   NUMERIC(10,3) NOT NULL DEFAULT 0,
    cargado_en            TIMESTAMPTZ   NOT NULL DEFAULT now(),
    CONSTRAINT pk_lectura_1min PRIMARY KEY (inversor_id, ts)
);
-- Grafana siempre filtra por rango de tiempo reciente: índice BRIN muy pequeño sobre ts
-- (los datos llegan en orden temporal) en lugar de un B-tree de cientos de MB.
CREATE INDEX IF NOT EXISTS brin_lectura_1min_ts ON silver.lectura_1min USING brin (ts);
-- "Último valor por inversor" (paneles de estado y alertas) usa la PK (inversor_id, ts) en orden inverso.

-- Contexto deduplicado. valor guarda el JSON original como JSONB (consultable con ->, ->>, @>, ?)
-- con las rutas de carpetas de usuario enmascaradas (Ley 1581, ver informe).
CREATE TABLE IF NOT EXISTS silver.contexto (
    contexto_id      INTEGER      PRIMARY KEY,
    registrado_ts    TIMESTAMPTZ  NOT NULL,
    inicio_ts        TIMESTAMPTZ  NOT NULL,
    fin_ts           TIMESTAMPTZ  NOT NULL,
    inversor_id      SMALLINT,                 -- NULL = aplica a todo el sitio (calendario)
    fuente           VARCHAR(40)  NOT NULL,
    valor            JSONB        NOT NULL,
    CONSTRAINT ck_contexto_intervalo CHECK (fin_ts >= inicio_ts)
);
CREATE INDEX IF NOT EXISTS gin_contexto_valor ON silver.contexto USING gin (valor jsonb_path_ops);
CREATE INDEX IF NOT EXISTS ix_contexto_inicio ON silver.contexto (inicio_ts);

-- Versiones de configuración del inversor detectadas en settings (alimentan la SCD2 dim_inversor)
CREATE TABLE IF NOT EXISTS silver.config_inversor (
    inversor_id         SMALLINT  NOT NULL,
    vigente_desde       DATE      NOT NULL,
    vigente_hasta       DATE      NOT NULL,
    prioridad_salida    SMALLINT  NOT NULL,      -- settings.outpriority
    prioridad_carga     SMALLINT  NOT NULL,      -- settings.chgpriority
    soc_corte_pct       SMALLINT,                -- settings.batstopsoc
    soc_paso_a_red_pct  SMALLINT,                -- settings.inv2linesoc
    soc_lleno_pct       SMALLINT,                -- settings.battfullsoc
    PRIMARY KEY (inversor_id, vigente_desde),
    CHECK (vigente_hasta >= vigente_desde)
);

-- Fallas/alarmas registradas por el propio inversor (fault_history), una fila por evento distinto
CREATE TABLE IF NOT EXISTS silver.falla_inversor (
    inversor_id   SMALLINT     NOT NULL,
    ts            TIMESTAMPTZ  NOT NULL,         -- hora calibrada por los autores del dataset
    codigo        SMALLINT     NOT NULL,         -- primer elemento del arreglo
    carga         JSONB        NOT NULL,         -- arreglo original de 16 registros
    PRIMARY KEY (inversor_id, ts, codigo)
);

-- Registros en cuarentena (no se pierden: se explican)
CREATE TABLE IF NOT EXISTS silver.rechazo_contexto (
    contexto_id      INTEGER      PRIMARY KEY,
    motivo           TEXT         NOT NULL,
    valor_texto      TEXT         NOT NULL
);

-- -------------------------------------------------------------------------------------
-- GOLD: modelo dimensional (constelación de hechos que comparten dimensiones conformadas)
-- -------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.dim_fecha (
    fecha_key        INTEGER      PRIMARY KEY,           -- AAAAMMDD (hora local del sitio)
    fecha            DATE         NOT NULL UNIQUE,
    anio             SMALLINT     NOT NULL,
    trimestre        SMALLINT     NOT NULL,
    mes              SMALLINT     NOT NULL,
    nombre_mes       VARCHAR(12)  NOT NULL,
    anio_mes         CHAR(7)      NOT NULL,              -- 2025-11 (orden natural en Power BI)
    semana_iso       SMALLINT     NOT NULL,
    dia              SMALLINT     NOT NULL,
    dia_semana       SMALLINT     NOT NULL,              -- 1 = lunes … 7 = domingo
    nombre_dia       VARCHAR(10)  NOT NULL,
    es_fin_semana    BOOLEAN      NOT NULL,
    es_festivo       BOOLEAN      NOT NULL DEFAULT false, -- derivado del contexto (calendario del campus)
    evento_campus    TEXT                                -- p. ej. "Public Holiday (Labour Day)"
);

-- Dimensión CONSTRUIDA (no existe en la fuente): minuto del día con franja horaria y periodo
-- solar. Permite comparar "franjas horarias" y explicar el consumo nocturno frente al solar.
CREATE TABLE IF NOT EXISTS gold.dim_hora (
    hora_key         SMALLINT     PRIMARY KEY,           -- 0 … 23
    hora_texto       CHAR(5)      NOT NULL,              -- '07:00'
    franja           VARCHAR(20)  NOT NULL,              -- Madrugada, Mañana, Mediodía solar, Tarde, Noche
    orden_franja     SMALLINT     NOT NULL,
    es_hora_solar    BOOLEAN      NOT NULL,              -- 06:00–17:59 local (hay irradiancia útil)
    periodo_tarifa   VARCHAR(16)  NOT NULL               -- Punta / Fuera de punta (escenario what-if)
);

-- Inversor: dimensión de cambio lento TIPO 2. La fuente registra la configuración del equipo
-- (tabla settings) y esta CAMBIÓ durante el año: el inversor 1 pasó de prioridad de salida 2 a 0
-- el 29/08/2025 y ambos cambiaron la prioridad de carga el 07/01/2026. Cada cambio abre una
-- versión nueva (vigente_desde / vigente_hasta / es_actual) y los hechos se enlazan a la versión
-- vigente en su fecha: el comportamiento energético se analiza según la configuración de ese día.
CREATE TABLE IF NOT EXISTS gold.dim_inversor (
    inversor_key       SMALLINT      PRIMARY KEY,        -- clave sustituta
    inversor_id        SMALLINT      NOT NULL,           -- clave natural de la fuente
    nombre             VARCHAR(30)   NOT NULL,
    modelo             VARCHAR(30)   NOT NULL,
    potencia_nominal_kw NUMERIC(5,2) NOT NULL,
    capacidad_pv_kwp   NUMERIC(6,2)  NOT NULL,
    bateria_kwh        NUMERIC(6,2)  NOT NULL,
    carga_principal    VARCHAR(60)   NOT NULL,
    prioridad_salida   SMALLINT      NOT NULL,        -- código del inversor (settings.outpriority)
    prioridad_salida_texto VARCHAR(40) NOT NULL,
    prioridad_carga    SMALLINT      NOT NULL,        -- settings.chgpriority
    prioridad_carga_texto  VARCHAR(40) NOT NULL,
    soc_corte_pct      SMALLINT,
    soc_paso_a_red_pct SMALLINT,
    vigente_desde      DATE          NOT NULL,
    vigente_hasta      DATE          NOT NULL DEFAULT '9999-12-31',
    es_actual          BOOLEAN       NOT NULL DEFAULT true,
    CONSTRAINT uq_inversor_version UNIQUE (inversor_id, vigente_desde)
);

CREATE TABLE IF NOT EXISTS gold.dim_tipo_evento (
    tipo_evento_key  SMALLINT     PRIMARY KEY,
    codigo           VARCHAR(20)  NOT NULL UNIQUE,
    nombre           VARCHAR(60)  NOT NULL,
    categoria        VARCHAR(30)  NOT NULL,              -- Operativo / Comunicación / Reportado por el inversor
    severidad        VARCHAR(20)  NOT NULL,
    regla            TEXT         NOT NULL               -- condición que lo dispara
);

CREATE TABLE IF NOT EXISTS gold.dim_fuente_contexto (
    fuente_key       SMALLINT     PRIMARY KEY,
    fuente           VARCHAR(40)  NOT NULL UNIQUE,       -- workstation1_log, manual entry …
    tipo             VARCHAR(12)  NOT NULL,              -- Automática / Manual
    dispositivo      VARCHAR(40)
);

-- HECHO 1 · Proceso "balance energético". Grano: 1 fila por inversor y HORA LOCAL del sitio.
-- Tabla de hechos transaccional agregada (periodic snapshot horario).
CREATE TABLE IF NOT EXISTS gold.fact_energia_hora (
    fecha_key              INTEGER       NOT NULL REFERENCES gold.dim_fecha,
    hora_key               SMALLINT      NOT NULL REFERENCES gold.dim_hora,
    inversor_key           SMALLINT      NOT NULL REFERENCES gold.dim_inversor,
    energia_pv_kwh         NUMERIC(10,4) NOT NULL,
    energia_carga_kwh      NUMERIC(10,4) NOT NULL,
    energia_red_kwh        NUMERIC(10,4) NOT NULL,
    energia_bat_carga_kwh  NUMERIC(10,4) NOT NULL,
    energia_bat_desc_kwh   NUMERIC(10,4) NOT NULL,
    soc_prom_pct           NUMERIC(5,1),
    soc_min_pct            NUMERIC(5,1),
    soc_fin_pct            NUMERIC(5,1),
    carga_max_w            NUMERIC(8,1),
    minutos_con_datos      SMALLINT      NOT NULL CHECK (minutos_con_datos BETWEEN 0 AND 60),
    minutos_soc_lleno      SMALLINT      NOT NULL,       -- SOC ≥ 98 %: el excedente solar se pierde
    lecturas_validas       INTEGER       NOT NULL,
    lecturas_recibidas     INTEGER       NOT NULL,
    lecturas_esperadas     INTEGER       NOT NULL,       -- 3600 s / 12 s de muestreo = 300
    CONSTRAINT pk_fact_energia_hora PRIMARY KEY (fecha_key, hora_key, inversor_key)
);
CREATE INDEX IF NOT EXISTS ix_feh_inversor_fecha ON gold.fact_energia_hora (inversor_key, fecha_key);

-- HECHO 2 · Proceso "eventos operativos". Grano: 1 fila por evento detectado (inicio a fin).
-- Los eventos NO se mezclan con las lecturas: tienen duración y no son aditivos por minuto.
CREATE TABLE IF NOT EXISTS gold.fact_evento (
    evento_id          BIGINT        PRIMARY KEY,
    fecha_key          INTEGER       NOT NULL REFERENCES gold.dim_fecha,
    hora_key           SMALLINT      NOT NULL REFERENCES gold.dim_hora,
    inversor_key       SMALLINT      NOT NULL REFERENCES gold.dim_inversor,
    tipo_evento_key    SMALLINT      NOT NULL REFERENCES gold.dim_tipo_evento,
    inicio_ts          TIMESTAMPTZ   NOT NULL,
    fin_ts             TIMESTAMPTZ   NOT NULL,
    duracion_min       NUMERIC(10,1) NOT NULL,
    valor_extremo      NUMERIC(10,2),                    -- p. ej. SOC mínimo alcanzado
    cantidad           SMALLINT      NOT NULL DEFAULT 1  -- aditivo: contar eventos
);
CREATE INDEX IF NOT EXISTS ix_fe_tipo_fecha ON gold.fact_evento (tipo_evento_key, fecha_key);

-- HECHO 3 · Proceso "actividad de las cargas" (contexto). Grano: 1 fila por registro de contexto.
CREATE TABLE IF NOT EXISTS gold.fact_actividad (
    contexto_id        INTEGER       PRIMARY KEY,
    fecha_key          INTEGER       NOT NULL REFERENCES gold.dim_fecha,
    hora_key           SMALLINT      NOT NULL REFERENCES gold.dim_hora,
    inversor_key       SMALLINT      REFERENCES gold.dim_inversor,   -- NULL: evento de todo el sitio
    fuente_key         SMALLINT      NOT NULL REFERENCES gold.dim_fuente_contexto,
    tipo_tarea         VARCHAR(60)   NOT NULL,
    esfuerzo_estimado  VARCHAR(20),
    duracion_min       NUMERIC(10,1) NOT NULL,
    carga_prom_w       NUMERIC(8,1),                     -- carga medida mientras duró la tarea
    energia_carga_kwh  NUMERIC(10,4),
    cantidad           SMALLINT      NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS ix_fa_fecha ON gold.fact_actividad (fecha_key);

-- Permisos de lectura para bi_lector (Grafana / Power BI) sobre todo lo creado aquí
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bi_lector') THEN
        GRANT USAGE ON SCHEMA silver, gold, ops TO bi_lector;
        GRANT SELECT ON ALL TABLES IN SCHEMA silver, gold, ops TO bi_lector;
    END IF;
END $$;
