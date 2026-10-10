"""
SolarBI Pascual - Punto de entrada único del flujo ETL.

    python etl/run_etl.py

Bronze (CSV crudo, no se modifica)
   └─► Silver (reglas de calidad en pandas → data/silver/ + silver.lectura_5min)
          └─► Gold (agregado diario en SQL → dwh.fact_energia_dia)

La carga es idempotente: todas las escrituras son UPSERT sobre la clave
primaria, así que ejecutar el script dos veces deja los mismos conteos.

Las credenciales se leen de variables de entorno (archivo .env, excluido
del repositorio). Ver .env.example.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

try:  # python-dotenv es opcional: si no está, se usan las variables del sistema
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "etl"))
import simulador  # noqa: E402

RUTA_BRONZE = os.path.join(RAIZ, "data", "bronze", "telemetria.csv")
DIR_SILVER = os.path.join(RAIZ, "data", "silver")
DIR_SQL = os.path.join(RAIZ, "sql")
ZONA = "America/Bogota"

# --- Reglas de calidad ------------------------------------------------------
CAPACIDAD_KWP = 5.0
RANGOS = {                                   # rango físico válido [min, max]
    "p_ac_kw": (0.0, CAPACIDAD_KWP * 1.1),   # no negativa ni mayor al 110 % de la capacidad
    "irradiancia_wm2": (0.0, 1500.0),        # 1500 W/m² supera el máximo terrestre
    "temp_modulo_c": (-10.0, 90.0),
}
CAMPOS_OBLIGATORIOS = ["ts", "dispositivo_id", "p_ac_kw", "irradiancia_wm2", "temp_modulo_c"]


def conectar():
    if load_dotenv:
        load_dotenv(os.path.join(RAIZ, ".env"))
    faltan = [v for v in ("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB") if not os.getenv(v)]
    if faltan:
        sys.exit(f"Faltan variables de entorno: {', '.join(faltan)}. Copie .env.example a .env.")
    host, port = os.getenv("PGHOST", "localhost"), int(os.getenv("PGPORT", "5432"))
    try:
        return psycopg2.connect(
            host=host,
            port=port,
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
        )
    except (psycopg2.OperationalError, UnicodeDecodeError) as e:
        # En Windows en español, libpq devuelve el error en latin-1 y psycopg2
        # no lo puede decodificar: se muestra una pista legible en su lugar.
        sys.exit(
            f"No se pudo conectar a PostgreSQL en {host}:{port} ({type(e).__name__}).\n"
            "Causas frecuentes:\n"
            "  1. Hay otro PostgreSQL instalado en Windows usando ese puerto: cambie PGPORT=5433\n"
            "     en .env y ejecute: docker compose up -d --force-recreate postgres\n"
            "  2. La contraseña de .env no es la que tenía la base cuando se creó: docker compose down -v\n"
            "     y docker compose up -d (borra los datos).\n"
            "  3. El contenedor no está corriendo: docker compose ps"
        )


# --- Silver: limpieza --------------------------------------------------------
def limpiar(bronze: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Aplica las reglas en orden y devuelve (válidas, rechazadas, reporte)."""
    df = bronze.copy()
    df["motivo_rechazo"] = None

    # R1 · Duplicados: misma clave (ts, dispositivo_id). Se conserva la primera.
    dup = df.duplicated(subset=["ts", "dispositivo_id"], keep="first")
    df.loc[dup, "motivo_rechazo"] = "R1_duplicado"

    # R2 · Faltantes: algún campo obligatorio vacío o no numérico.
    num = {c: pd.to_numeric(df[c], errors="coerce") for c in CAMPOS_OBLIGATORIOS if c != "ts"}
    ts = pd.to_datetime(df["ts"], errors="coerce")
    falta = ts.isna()
    for serie in num.values():
        falta |= serie.isna()
    df.loc[falta & df["motivo_rechazo"].isna(), "motivo_rechazo"] = "R2_faltante"

    # R3 · Rango físico.
    fuera = pd.Series(False, index=df.index)
    for col, (lo, hi) in RANGOS.items():
        fuera |= (num[col] < lo) | (num[col] > hi)
    df.loc[fuera & df["motivo_rechazo"].isna(), "motivo_rechazo"] = "R3_fuera_de_rango"

    rechazadas = df[df["motivo_rechazo"].notna()].copy()
    ok = df["motivo_rechazo"].isna()
    validas = pd.DataFrame({
        "ts": ts[ok].dt.tz_localize(ZONA),
        "dispositivo_id": num["dispositivo_id"][ok].astype(int),
        "p_ac_kw": num["p_ac_kw"][ok].round(3),
        "irradiancia_wm2": num["irradiancia_wm2"][ok].round(1),
        "temp_modulo_c": num["temp_modulo_c"][ok].round(1),
    })
    validas["energia_kwh"] = (validas["p_ac_kw"] * 5 / 60).round(5)

    leidas = len(df)
    conteo = rechazadas["motivo_rechazo"].value_counts()
    reporte = {
        "filas_leidas": leidas,
        "rechazo_duplicados": int(conteo.get("R1_duplicado", 0)),
        "rechazo_faltantes": int(conteo.get("R2_faltante", 0)),
        "rechazo_rango": int(conteo.get("R3_fuera_de_rango", 0)),
        "filas_validas": len(validas),
        "pct_datos_validos": round(100 * len(validas) / leidas, 2) if leidas else 0.0,
    }
    return validas, rechazadas, reporte


# --- Gold: carga en PostgreSQL ----------------------------------------------
def cargar(conn, validas: pd.DataFrame) -> dict:
    with conn.cursor() as cur:
        cur.execute(open(os.path.join(DIR_SQL, "01_ddl.sql"), encoding="utf-8").read())

        filas = [
            (r.ts.isoformat(), r.dispositivo_id, r.p_ac_kw, r.irradiancia_wm2, r.temp_modulo_c, r.energia_kwh)
            for r in validas.itertuples(index=False)
        ]
        execute_values(cur, """
            INSERT INTO silver.lectura_5min
                   (ts, dispositivo_id, p_ac_kw, irradiancia_wm2, temp_modulo_c, energia_kwh)
            VALUES %s
            ON CONFLICT (ts, dispositivo_id) DO UPDATE
            SET p_ac_kw         = EXCLUDED.p_ac_kw,
                irradiancia_wm2 = EXCLUDED.irradiancia_wm2,
                temp_modulo_c   = EXCLUDED.temp_modulo_c,
                energia_kwh     = EXCLUDED.energia_kwh,
                cargado_en      = now()
        """, filas, page_size=1000)

        cur.execute(open(os.path.join(DIR_SQL, "03_carga_gold.sql"), encoding="utf-8").read())

        cur.execute("SELECT count(*) FROM silver.lectura_5min")
        n_silver = cur.fetchone()[0]
        cur.execute("SELECT count(*), coalesce(sum(energia_kwh), 0) FROM dwh.fact_energia_dia")
        n_fact, energia = cur.fetchone()
    return {"filas_silver_total": n_silver, "filas_fact_total": n_fact, "energia_total_kwh": float(energia)}


def registrar(conn, inicio, reporte, totales):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO dwh.etl_ejecucion
                (inicio, fin, archivo_origen, filas_leidas, rechazo_duplicados, rechazo_faltantes,
                 rechazo_rango, filas_validas, pct_datos_validos, filas_silver_total, filas_fact_total)
            VALUES (%s, now(), %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING ejecucion_id
        """, (inicio, "data/bronze/telemetria.csv", reporte["filas_leidas"],
              reporte["rechazo_duplicados"], reporte["rechazo_faltantes"], reporte["rechazo_rango"],
              reporte["filas_validas"], reporte["pct_datos_validos"],
              totales["filas_silver_total"], totales["filas_fact_total"]))
        return cur.fetchone()[0]


def main() -> None:
    inicio = datetime.now(timezone.utc)

    # Bronze: solo se genera si no existe; si existe, no se toca.
    if not os.path.exists(RUTA_BRONZE):
        simulador.generar(RUTA_BRONZE)
        print(f"[bronze] No existía: se generó {os.path.relpath(RUTA_BRONZE, RAIZ)}")
    bronze = pd.read_csv(RUTA_BRONZE, dtype=str, keep_default_na=False, na_values=[""])

    # Silver
    validas, rechazadas, reporte = limpiar(bronze)
    os.makedirs(DIR_SILVER, exist_ok=True)
    salida = validas.copy()
    salida["ts"] = salida["ts"].map(lambda t: t.isoformat())
    salida.to_csv(os.path.join(DIR_SILVER, "lectura_5min.csv"), index=False)
    rechazadas.to_csv(os.path.join(DIR_SILVER, "rechazos.csv"), index=False)
    with open(os.path.join(DIR_SILVER, "reporte_calidad.json"), "w", encoding="utf-8") as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)

    # Gold
    conn = conectar()
    try:
        totales = cargar(conn, validas)
        ejecucion = registrar(conn, inicio, reporte, totales)
        conn.commit()          # todo o nada: una sola transacción
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    print("\n=== Reporte de calidad (Bronze → Silver) ===")
    print(f"Filas leídas ............................ {reporte['filas_leidas']:>6}")
    print(f"Rechazadas R1 duplicados ................ {reporte['rechazo_duplicados']:>6}")
    print(f"Rechazadas R2 faltantes ................. {reporte['rechazo_faltantes']:>6}")
    print(f"Rechazadas R3 fuera de rango ............ {reporte['rechazo_rango']:>6}")
    print(f"Filas válidas ........................... {reporte['filas_validas']:>6}")
    print(f"Porcentaje de datos válidos ............. {reporte['pct_datos_validos']:>6.2f} %")
    print("\n=== Conteos en PostgreSQL (deben ser iguales en cada ejecución) ===")
    print(f"silver.lectura_5min ..................... {totales['filas_silver_total']:>6}")
    print(f"dwh.fact_energia_dia .................... {totales['filas_fact_total']:>6}")
    print(f"Energía total (kWh) ..................... {totales['energia_total_kwh']:>9.3f}")
    print(f"\nEjecución #{ejecucion} registrada en dwh.etl_ejecucion.")


if __name__ == "__main__":
    main()
