"""
Taller 6 · ETL de la microrred OpenCEM:  Bronze (SQLite) → Silver → Gold (PostgreSQL)

    python -m etl.run_etl                  # dentro del contenedor (Job de Kubernetes)
    python -m etl.run_etl --bronze ruta.sqlite

Pasos
  1. Abre la capa Bronze en SOLO LECTURA (opencem-v1.0.0.sqlite de Zenodo o, como plan B,
     opencem-github.sqlite reconstruida con etl/bronze_desde_github.py).
  2. Aplica las reglas de calidad R1…R7 a las mediciones y C1…C4 al contexto, contando las
     filas antes y después de cada una (ops.etl_regla).
  3. Integra potencia → energía por lectura y agrega a 1 minuto (silver.lectura_1min).
  4. Construye Gold con SQL (sql/02_gold.sql): dimensiones, hechos de energía, eventos y actividad.
  5. Concilia Bronze ↔ Silver ↔ Gold (ops.conciliacion).

Idempotencia: Silver histórico y Gold se reemplazan completos dentro de UNA transacción y las
dimensiones usan llaves fijas; dos corridas seguidas dejan exactamente las mismas filas. Lo que
cargó el simulador (origen = 'simulador') no se toca. Solo ops.* crece: es la bitácora.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sqlite3
import sys
import time
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd
import psycopg

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_SQL = os.path.join(RAIZ, "sql")


def env(nombre: str, defecto: str) -> str:
    return os.getenv(nombre, defecto)


# ---------------------------------------------------------------------------------------------
# Parámetros (ConfigMap microrred-parametros; valores por defecto = los del informe)
# ---------------------------------------------------------------------------------------------
ZONA_SITIO = env("ZONA_SITIO", "Asia/Shanghai")      # la planta está en Shenzhen (UTC+8)
MUESTREO_S = float(env("MUESTREO_S", "12"))           # mediana del intervalo entre lecturas
MAX_DT_S = float(env("MAX_DT_S", "120"))              # más de 2 min sin lectura = hueco, no se integra
INVERSORES_VALIDOS = {1, 2}

# Columnas de la fuente que se usan (nombre en OpenCEM → nombre en el modelo)
COLUMNAS = {
    "read_ts": "read_ts", "inverter": "inversor_id",
    "battsoc": "soc_pct", "battvolt": "bat_voltaje_v", "battcurr": "bat_corriente_a",
    "pv1power": "pv_potencia_w", "outw_a": "carga_potencia_w", "linepowerw_a": "red_potencia_w",
    "outvolta": "salida_voltaje_v", "linevolta": "red_voltaje_v", "linefreq": "red_frecuencia_hz",
    "temper3": "temp_inversor_c",
}
OBLIGATORIAS = ["soc_pct", "bat_voltaje_v", "bat_corriente_a", "pv_potencia_w", "carga_potencia_w",
                "red_potencia_w"]
# Rango físico válido (fuera de él la lectura es un dato inválido, no un evento)
RANGOS = {
    "soc_pct": (0, 100),
    "bat_voltaje_v": (40, 60),          # banco LiFePO4 16S de 51,2 V nominal: 40–58,4 V operativos
    "bat_corriente_a": (-200, 200),     # 200 Ah; el inversor limita a ~150 A
    "pv_potencia_w": (0, 6_500),        # ≤ capacidad del arreglo (6,24 kWp) + margen
    "carga_potencia_w": (0, 8_800),     # 8 kW nominales + 10 %
    "red_potencia_w": (0, 8_800),       # la red solo importa (no hay exportación)
}
DESBORDE_UINT16 = 3276.7                # 0x7FFF / 10: por encima, el valor es negativo mal decodificado


# ---------------------------------------------------------------------------------------------
class Bitacora:
    """Acumula el conteo antes/después de cada regla para ops.etl_regla y la consola."""

    def __init__(self):
        self.reglas: list[tuple] = []

    def registrar(self, regla, descripcion, accion, antes, despues, afectadas=None):
        afectadas = (antes - despues) if afectadas is None else afectadas
        self.reglas.append((len(self.reglas) + 1, regla, descripcion, accion, int(antes), int(despues),
                            int(afectadas)))
        print(f"  {regla:<4} {descripcion[:70]:<70} {antes:>11,} → {despues:>11,}  ({afectadas:,} afectadas)")


def localizar_bronze(ruta: str | None) -> str:
    if ruta:
        return ruta
    carpeta = env("BRONZE_DIR", os.path.join(RAIZ, "data", "bronze"))
    for nombre in (env("BRONZE_ARCHIVO", ""), "opencem-v1.0.0.sqlite", "opencem-github.sqlite"):
        if nombre and os.path.exists(os.path.join(carpeta, nombre)):
            return os.path.join(carpeta, nombre)
    sys.exit(f"No hay base Bronze en {carpeta}. Ver README (preparar_bronze o bronze_desde_github).")


def sha256(ruta: str) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        while bloque := f.read(1 << 22):
            h.update(bloque)
    return h.hexdigest()


def conectar() -> psycopg.Connection:
    faltan = [v for v in ("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB") if not os.getenv(v)]
    if faltan:
        sys.exit(f"Faltan variables de entorno: {', '.join(faltan)} (Secret microrred-credenciales).")
    return psycopg.connect(host=env("PGHOST", "localhost"), port=int(env("PGPORT", "5432")),
                           dbname=os.environ["POSTGRES_DB"], user=os.environ["POSTGRES_USER"],
                           password=os.environ["POSTGRES_PASSWORD"], connect_timeout=10)


# ---------------------------------------------------------------------------------------------
# EXTRACCIÓN
# ---------------------------------------------------------------------------------------------
def extraer(ruta: str) -> dict[str, pd.DataFrame]:
    """Lee de Bronze solo lo que el modelo usa. Las tablas settings, statistics y fault_history
    existen en la base oficial de Zenodo; si faltan (reconstrucción desde GitHub) se omiten."""
    con = sqlite3.connect(f"file:{ruta}?mode=ro&immutable=1", uri=True)
    tablas = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for t in ("analog_measurements", "context"):
        if t not in tablas:
            sys.exit(f"La base {ruta} no tiene la tabla {t}. Tablas: {sorted(tablas)}")
    cols = ", ".join(f'"{c}"' for c in COLUMNAS)
    out = {
        "med": pd.read_sql_query(f"SELECT {cols} FROM analog_measurements", con).rename(columns=COLUMNAS),
        "ctx": pd.read_sql_query('SELECT id, recorded, start, "end", value FROM context', con),
    }
    if "settings" in tablas:
        out["cfg"] = pd.read_sql_query(
            "SELECT read_ts, inverter, outpriority, chgpriority, batstopsoc, inv2linesoc, battfullsoc "
            "FROM settings", con)
    if "statistics" in tablas:
        out["cnt"] = pd.read_sql_query(
            "SELECT read_ts, inverter, json_extract(pvgeneratenergytotal, '$[0]') AS pv_total_kwh, "
            "json_extract(usedenergytotal, '$[0]') AS carga_total_kwh, "
            "json_extract(loadconsumlinetotal, '$[0]') AS carga_desde_red_total_kwh "
            "FROM statistics WHERE pvgeneratenergytotal IS NOT NULL", con)
    if "fault_history" in tablas:
        sel = ", ".join(f"faulthistoryrecord{i:02d}, faulthistoryrecord{i:02d}_time" for i in range(32))
        eventos = set()
        for fila in con.execute(f"SELECT inverter, {sel} FROM fault_history"):
            for i in range(32):
                carga, ts = fila[1 + 2 * i], fila[2 + 2 * i]
                if carga and ts:
                    eventos.add((fila[0], carga, round(ts, 3)))
        out["fal"] = pd.DataFrame(sorted(eventos), columns=["inversor_id", "carga", "ts"])
    con.close()
    return out


# ---------------------------------------------------------------------------------------------
# CONFIGURACIÓN DEL INVERSOR (base de la dimensión SCD tipo 2)
# ---------------------------------------------------------------------------------------------
CAMPOS_CFG = ["outpriority", "chgpriority", "batstopsoc", "inv2linesoc", "battfullsoc"]


def versiones_config(cfg: pd.DataFrame, b: Bitacora) -> pd.DataFrame:
    """Una versión por cada cambio real de prioridad de salida o de carga.
    Las lecturas de settings llegan con campos sueltos en NULL (lectura Modbus parcial): se
    descartan, y por día se toma la configuración más frecuente para no crear versiones falsas
    por un registro mal leído."""
    n0 = len(cfg)
    cfg = cfg.dropna(subset=CAMPOS_CFG)
    b.registrar("S1", "settings: lectura de configuración incompleta (algún campo NULL)", "elimina", n0, len(cfg))
    cfg = cfg.assign(dia=pd.to_datetime(cfg["read_ts"], unit="s", utc=True).dt.tz_convert(ZONA_SITIO).dt.date)
    moda = (cfg.groupby(["inverter", "dia"] + CAMPOS_CFG).size().reset_index(name="n")
               .sort_values("n").groupby(["inverter", "dia"]).tail(1).sort_values(["inverter", "dia"]))
    moda["firma"] = moda[["outpriority", "chgpriority"]].astype(int).astype(str).agg("/".join, axis=1)
    moda["cambio"] = moda["firma"] != moda.groupby("inverter")["firma"].shift()
    vers = moda[moda["cambio"]].copy()
    vers["vigente_hasta"] = (vers.groupby("inverter")["dia"].shift(-1)
                             .map(lambda d: d - timedelta(days=1) if isinstance(d, date) else None))
    b.registrar("S2", "settings: días con configuración → versiones (cambia prioridad de salida o de carga)",
                "informa", len(moda), len(vers), 0)
    return pd.DataFrame({
        "inversor_id": vers["inverter"].astype(int), "vigente_desde": vers["dia"],
        "vigente_hasta": vers["vigente_hasta"].fillna(pd.Timestamp("9999-12-31").date()),
        "prioridad_salida": vers["outpriority"].astype(int), "prioridad_carga": vers["chgpriority"].astype(int),
        "soc_corte_pct": vers["batstopsoc"].astype(int), "soc_paso_a_red_pct": vers["inv2linesoc"].astype(int),
        "soc_lleno_pct": vers["battfullsoc"].astype(int)})


def limpiar_contadores(cnt: pd.DataFrame, b: Bitacora) -> pd.DataFrame:
    """Contadores de energía acumulada del propio inversor (statistics.*total). Se encontró que el
    inversor 1 alterna lecturas con los contadores del inversor 2 (cruce de registros): se conserva
    la serie propia: nunca baja y no crece más de lo que 8 kW nominales permiten en el tiempo transcurrido."""
    n0 = len(cnt)
    partes = []
    for inv, g in cnt.sort_values("read_ts").groupby("inverter"):
        quedan = []
        ultimo = g["carga_total_kwh"].dropna().head(50).min()     # arranca en la serie propia (la menor)
        t_ultimo = g["read_ts"].iloc[0]
        for fila in g.itertuples(index=False):
            v = fila.carga_total_kwh
            if v is None or pd.isna(v):
                continue
            maximo = 8.0 * (fila.read_ts - t_ultimo) / 3600 + 0.2     # 8 kW durante el tiempo transcurrido
            if 0 <= v - ultimo <= maximo:
                quedan.append(fila)
                ultimo, t_ultimo = v, fila.read_ts
        partes.append(pd.DataFrame(quedan))
    limpio = pd.concat(partes, ignore_index=True)
    b.registrar("S3", "statistics: contador nulo, cruzado con el otro inversor o imposible", "elimina",
                n0, len(limpio))
    return limpio


# ---------------------------------------------------------------------------------------------
# LIMPIEZA · mediciones
# ---------------------------------------------------------------------------------------------
def limpiar_mediciones(df: pd.DataFrame, b: Bitacora) -> pd.DataFrame:
    n0 = len(df)
    b.registrar("R0", "Lecturas leídas de Bronze (analog_measurements)", "informa", n0, n0, 0)

    # R1 · duplicados exactos (misma fila en todas las columnas usadas)
    df = df.drop_duplicates()
    b.registrar("R1", "Duplicados exactos (fila repetida en la exportación)", "elimina", n0, len(df))

    # R2 · desbordamiento de entero de 16 bits sin signo en la corriente de batería
    #      (valor 6538,5 = registro 65385 → en realidad -15,1 A). Se CORRIGE, no se borra.
    m = df["bat_corriente_a"] > DESBORDE_UINT16
    df.loc[m, "bat_corriente_a"] = (df.loc[m, "bat_corriente_a"] - 6553.6).round(1)
    b.registrar("R2", "Corriente de batería con desborde uint16 → se decodifica con signo", "corrige",
                len(df), len(df), int(m.sum()))

    # R3 · duplicados de llave (read_ts, inversor): tras R2 la mayoría son la misma lectura
    #      exportada con y sin el error; se conserva una por llave
    n = len(df)
    df = df.drop_duplicates()                                   # los que R2 volvió idénticos
    df = df.sort_values(["inversor_id", "read_ts"]).drop_duplicates(["inversor_id", "read_ts"], keep="last")
    b.registrar("R3", "Duplicados de llave (read_ts, inversor) después de corregir R2", "elimina", n, len(df))

    # R4 · inversor o marca de tiempo imposibles
    n = len(df)
    ahora = time.time()
    df = df[df["inversor_id"].isin(INVERSORES_VALIDOS) & df["read_ts"].between(1_600_000_000, ahora)]
    b.registrar("R4", "Inversor fuera de {1,2} o marca de tiempo fuera de rango", "elimina", n, len(df))

    # A partir de aquí no se borran filas: se MARCAN como inválidas (cuentan para el % de datos válidos)
    df = df.copy()
    df["valida"] = True
    nul = df[OBLIGATORIAS].isna().any(axis=1)
    df.loc[nul, "valida"] = False
    b.registrar("R5", "Campo obligatorio vacío (SOC, V, I, PV, carga o red)", "marca",
                len(df), int(df["valida"].sum()), int(nul.sum()))

    fuera = pd.Series(False, index=df.index)
    for col, (lo, hi) in RANGOS.items():
        fuera |= df[col].notna() & ~df[col].between(lo, hi)
    antes = int(df["valida"].sum())
    df.loc[fuera, "valida"] = False
    b.registrar("R6", "Fuera de rango físico (p. ej. V batería < 40 V, red 65 531 W = desborde)", "marca",
                antes, int(df["valida"].sum()), int((fuera & ~nul).sum()))

    # R7 · intervalo hasta la siguiente lectura: > MAX_DT_S es un hueco y NO se integra
    df["dt_s"] = df.groupby("inversor_id")["read_ts"].shift(-1) - df["read_ts"]
    hueco = df["dt_s"].isna() | (df["dt_s"] > MAX_DT_S)
    df["dt_s"] = df["dt_s"].where(~hueco, MUESTREO_S).clip(lower=0)
    b.registrar("R7", f"Hueco > {MAX_DT_S:.0f} s antes de la siguiente lectura: se integra solo {MUESTREO_S:.0f} s",
                "corrige", len(df), len(df), int(hueco.sum()))
    return df


def a_minutos(df: pd.DataFrame) -> pd.DataFrame:
    """Integra potencia → energía por lectura (E = P·Δt) y agrega a 1 minuto por inversor."""
    df = df.copy()
    v = df["valida"]
    horas = df["dt_s"] / 3600.0
    bat_w = df["bat_voltaje_v"] * df["bat_corriente_a"]           # + descarga / - carga
    df["bat_potencia_w"] = bat_w
    df["pv_energia_wh"] = np.where(v, df["pv_potencia_w"] * horas, 0.0)
    df["carga_energia_wh"] = np.where(v, df["carga_potencia_w"] * horas, 0.0)
    df["red_energia_wh"] = np.where(v, df["red_potencia_w"] * horas, 0.0)
    df["bat_desc_energia_wh"] = np.where(v, bat_w.clip(lower=0) * horas, 0.0)
    df["bat_carga_energia_wh"] = np.where(v, (-bat_w).clip(lower=0) * horas, 0.0)
    df["segundos"] = np.where(v, df["dt_s"], 0.0)
    df["ts"] = pd.to_datetime((df["read_ts"] // 60) * 60, unit="s", utc=True)
    for c in ["soc_pct", "bat_voltaje_v", "bat_corriente_a", "pv_potencia_w", "carga_potencia_w",
              "red_potencia_w", "bat_potencia_w", "salida_voltaje_v", "red_voltaje_v", "red_frecuencia_hz",
              "temp_inversor_c"]:
        df[c] = df[c].where(v)                                     # los promedios solo con lecturas válidas
    g = df.groupby(["inversor_id", "ts"], sort=True)
    out = g.agg(
        n_recibidas=("read_ts", "size"), n_lecturas=("valida", "sum"), segundos_cubiertos=("segundos", "sum"),
        soc_pct=("soc_pct", "last"), soc_min_pct=("soc_pct", "min"), bat_voltaje_v=("bat_voltaje_v", "mean"),
        bat_corriente_a=("bat_corriente_a", "mean"), temp_inversor_c=("temp_inversor_c", "mean"),
        pv_potencia_w=("pv_potencia_w", "mean"), carga_potencia_w=("carga_potencia_w", "mean"),
        carga_max_w=("carga_potencia_w", "max"),
        red_potencia_w=("red_potencia_w", "mean"), bat_potencia_w=("bat_potencia_w", "mean"),
        salida_voltaje_v=("salida_voltaje_v", "mean"), red_voltaje_v=("red_voltaje_v", "mean"),
        red_frecuencia_hz=("red_frecuencia_hz", "mean"),
        pv_energia_wh=("pv_energia_wh", "sum"), carga_energia_wh=("carga_energia_wh", "sum"),
        red_energia_wh=("red_energia_wh", "sum"), bat_carga_energia_wh=("bat_carga_energia_wh", "sum"),
        bat_desc_energia_wh=("bat_desc_energia_wh", "sum"),
    ).reset_index()
    out["segundos_cubiertos"] = out["segundos_cubiertos"].clip(upper=120)
    return out


# ---------------------------------------------------------------------------------------------
# LIMPIEZA · contexto (JSON)
# ---------------------------------------------------------------------------------------------
RX_RUTA_USUARIO = re.compile(r"(/home/|/Users/|C:\\\\Users\\\\)(?!<)[^/\\\s'\"<]+")   # las ya enmascaradas (<user>) no cuentan


def limpiar_contexto(ctx: pd.DataFrame, b: Bitacora) -> tuple[pd.DataFrame, pd.DataFrame]:
    n0 = len(ctx)
    b.registrar("C0", "Registros de contexto leídos de Bronze (context)", "informa", n0, n0, 0)
    ctx = ctx.drop_duplicates(["id", "recorded", "start", "end", "value"])
    b.registrar("C1", "Registros de contexto repetidos (mismo id y contenido)", "elimina", n0, len(ctx))

    filas, rechazos = [], []
    enmascarados = 0
    for r in ctx.itertuples(index=False):
        texto = str(r.value)
        limpio, k = RX_RUTA_USUARIO.subn(lambda mm: mm.group(1) + "<usuario>", texto)
        enmascarados += k > 0
        try:
            valor = json.loads(limpio)
            if not isinstance(valor, dict):
                raise ValueError("no es un objeto JSON")
        except ValueError as e:
            rechazos.append((int(r.id), f"JSON inválido: {e}", limpio))
            continue
        inv = valor.get("inverter")
        try:
            inv = int(inv) if inv is not None else None
        except (TypeError, ValueError):
            inv = None
        filas.append((int(r.id), int(r.recorded), int(r.start), int(r.end), inv,
                      str(valor.get("source", "desconocida")), json.dumps(valor, ensure_ascii=False)))
    n = len(ctx)
    b.registrar("C2", "JSON mal formado (comillas sin escapar) → cuarentena silver.rechazo_contexto",
                "elimina", n, n - len(rechazos))
    b.registrar("C3", "Rutas de carpeta de usuario enmascaradas (/home/<usuario>) · Ley 1581", "corrige",
                len(filas), len(filas), enmascarados)
    ok = pd.DataFrame(filas, columns=["contexto_id", "registrado", "inicio", "fin", "inversor_id", "fuente", "valor"])
    malos = ok["fin"] < ok["inicio"]
    ok = ok[~malos]
    b.registrar("C4", "Intervalo imposible (fin antes del inicio)", "elimina", len(malos), len(ok))
    return ok, pd.DataFrame(rechazos, columns=["contexto_id", "motivo", "valor_texto"])


# ---------------------------------------------------------------------------------------------
# CONCILIACIÓN contra los contadores de energía del propio inversor
# ---------------------------------------------------------------------------------------------
def conciliar_con_contadores(med: pd.DataFrame, cnt: pd.DataFrame) -> list[tuple]:
    """Para cada inversor y mes local: Δ del contador acumulado del equipo (primera → última lectura
    del mes) frente a la energía que el ETL integró desde la potencia en EXACTAMENTE esa ventana.
    Diferencias esperables: resolución del contador (0,1 kWh), huecos que el ETL no integra y que
    el contador sí registra, y la definición interna del fabricante (p. ej. PV antes o después del MPPT)."""
    filas = []
    pares = [("Solar", "pv_total_kwh", "pv_potencia_w"), ("Consumo de la carga", "carga_total_kwh", "carga_potencia_w")]
    for inv, g in cnt.groupby("inverter"):
        m = med[(med["inversor_id"] == inv)].sort_values("read_ts")
        ts = m["read_ts"].to_numpy()
        g = g.sort_values("read_ts").assign(
            mes=pd.to_datetime(g["read_ts"], unit="s", utc=True).dt.tz_convert(ZONA_SITIO).dt.strftime("%Y-%m"))
        for etiqueta, col_cnt, col_p in pares:
            e = np.where(m["valida"], m[col_p] * m["dt_s"], 0.0) / 3.6e6
            acum = np.concatenate([[0.0], np.cumsum(e)])
            for mes, gm in g.dropna(subset=[col_cnt]).groupby("mes"):
                t0, t1 = gm["read_ts"].iloc[0], gm["read_ts"].iloc[-1]
                delta = gm[col_cnt].iloc[-1] - gm[col_cnt].iloc[0]
                i0, i1 = np.searchsorted(ts, t0), np.searchsorted(ts, t1)
                filas.append((int(inv), mes, etiqueta, round(float(delta), 3), round(float(acum[i1] - acum[i0]), 3),
                              round((t1 - t0) / 3600, 1)))
    return filas


# ---------------------------------------------------------------------------------------------
# CARGA
# ---------------------------------------------------------------------------------------------
def copiar(cur, tabla: str, df: pd.DataFrame) -> None:
    buf = io.StringIO()
    df.to_csv(buf, index=False, header=False, na_rep="\\N")
    buf.seek(0)
    with cur.copy(f"COPY {tabla} ({', '.join(df.columns)}) FROM STDIN WITH (FORMAT csv, NULL '\\N')") as cp:
        while datos := buf.read(1 << 20):
            cp.write(datos)


def ejecutar_sql(cur, archivo: str) -> None:
    with open(os.path.join(DIR_SQL, archivo), encoding="utf-8") as f:
        cur.execute(f.read())


def main() -> None:
    ap = argparse.ArgumentParser(description="ETL Taller 6 (OpenCEM)")
    ap.add_argument("--bronze", help="ruta al .sqlite (por defecto se busca en BRONZE_DIR)")
    a = ap.parse_args()
    ruta = localizar_bronze(a.bronze)
    inicio = datetime.now(timezone.utc)
    print(f"Bronze: {ruta}")
    huella = sha256(ruta)
    print(f"SHA-256: {huella}")

    con = conectar()
    con.autocommit = True
    with con.cursor() as cur:
        ejecutar_sql(cur, "01_ddl.sql")
        cur.execute("INSERT INTO ops.etl_ejecucion (inicio, archivo_bronze, sha256_bronze, estado) "
                    "VALUES (%s, %s, %s, 'en curso') RETURNING ejecucion_id",
                    (inicio, os.path.basename(ruta), huella))
        ejec = cur.fetchone()[0]
    print(f"Ejecución {ejec}")

    try:
        b = Bitacora()
        t = time.time()
        datos = extraer(ruta)
        med, ctx = datos["med"], datos["ctx"]
        print(f"Extracción: {len(med):,} mediciones, {len(ctx):,} contextos"
              + "".join(f", {len(datos[k]):,} {n}" for k, n in (("cfg", "configuraciones"), ("cnt", "contadores"),
                                                                ("fal", "fallas")) if k in datos)
              + f" en {time.time() - t:.0f} s")
        print("Reglas de calidad:")
        med = limpiar_mediciones(med, b)
        minutos = a_minutos(med)
        ctx_ok, ctx_mal = limpiar_contexto(ctx, b)
        if "cfg" in datos:
            config = versiones_config(datos["cfg"], b)
        else:   # plan B sin tabla settings: una versión por inversor con prioridades desconocidas (-1)
            config = pd.DataFrame({"inversor_id": [1, 2], "vigente_desde": [pd.Timestamp("2024-01-01").date()] * 2,
                                   "vigente_hasta": [pd.Timestamp("9999-12-31").date()] * 2,
                                   "prioridad_salida": [-1, -1], "prioridad_carga": [-1, -1],
                                   "soc_corte_pct": [None, None], "soc_paso_a_red_pct": [None, None],
                                   "soc_lleno_pct": [None, None]})
        contadores = limpiar_contadores(datos["cnt"], b) if "cnt" in datos else None
        fallas = None
        if "fal" in datos:
            fal = datos["fal"]
            fallas = pd.DataFrame({
                "inversor_id": fal["inversor_id"].astype(int),
                "ts": pd.to_datetime(fal["ts"], unit="s", utc=True),
                "codigo": fal["carga"].map(lambda x: json.loads(x)[0]).astype(int),
                "carga": fal["carga"]}).drop_duplicates(["inversor_id", "ts", "codigo"])
            b.registrar("F1", "fault_history: 32 posiciones × lectura → fallas distintas (inversor, código, hora)",
                        "informa", len(fal), len(fallas), 0)

        totales_origen = {
            "lecturas_validas": float(med["valida"].sum()),
            "lecturas_unicas": float(len(med)),
            "pv_kwh": float(np.where(med["valida"], med["pv_potencia_w"] * med["dt_s"], 0).sum() / 3.6e6),
            "carga_kwh": float(np.where(med["valida"], med["carga_potencia_w"] * med["dt_s"], 0).sum() / 3.6e6),
            "red_kwh": float(np.where(med["valida"], med["red_potencia_w"] * med["dt_s"], 0).sum() / 3.6e6),
            "contextos": float(len(ctx_ok)),
        }

        conciliacion_contador = []
        if contadores is not None and len(contadores):
            conciliacion_contador = conciliar_con_contadores(med, contadores)

        silver = minutos.assign(origen="historico")[[
            "ts", "inversor_id", "origen", "n_recibidas", "n_lecturas", "segundos_cubiertos", "soc_pct",
            "soc_min_pct", "bat_voltaje_v", "bat_corriente_a", "temp_inversor_c", "pv_potencia_w",
            "carga_potencia_w", "carga_max_w", "red_potencia_w", "bat_potencia_w", "salida_voltaje_v",
            "red_voltaje_v", "red_frecuencia_hz", "pv_energia_wh", "carga_energia_wh", "red_energia_wh",
            "bat_carga_energia_wh", "bat_desc_energia_wh"]]
        decimales = silver.select_dtypes("number").columns.drop(["inversor_id", "n_recibidas", "n_lecturas"])
        silver[decimales] = silver[decimales].round(3)
        contexto = pd.DataFrame({
            "contexto_id": ctx_ok["contexto_id"],
            "registrado_ts": pd.to_datetime(ctx_ok["registrado"], unit="s", utc=True),
            "inicio_ts": pd.to_datetime(ctx_ok["inicio"], unit="s", utc=True),
            "fin_ts": pd.to_datetime(ctx_ok["fin"], unit="s", utc=True),
            "inversor_id": ctx_ok["inversor_id"].astype("Int64"),
            "fuente": ctx_ok["fuente"], "valor": ctx_ok["valor"]})

        # Todo el reemplazo de Silver histórico + Gold ocurre en UNA transacción: si algo falla,
        # la base queda como estaba (nunca a medias) y la corrida es repetible.
        t = time.time()
        con.autocommit = False
        with con.cursor() as cur:
            cur.execute("SET LOCAL TIME ZONE 'UTC'")
            cur.execute("DELETE FROM silver.lectura_1min WHERE origen = 'historico'")
            copiar(cur, "silver.lectura_1min", silver)
            cur.execute("TRUNCATE silver.contexto, silver.rechazo_contexto")
            copiar(cur, "silver.contexto", contexto)
            if len(ctx_mal):
                copiar(cur, "silver.rechazo_contexto", ctx_mal)
            cur.execute("TRUNCATE silver.config_inversor, silver.falla_inversor")
            copiar(cur, "silver.config_inversor", config)
            if fallas is not None:
                copiar(cur, "silver.falla_inversor", fallas)
            parametros = {
                "microrred.zona": ZONA_SITIO,
                "microrred.soc_bajo": env("SOC_BAJO_PCT", "20"),
                "microrred.temp_alta": env("TEMP_ALTA_C", "60"),
                "microrred.hueco_min": env("HUECO_MIN", "10"),
                "microrred.lecturas_hora": str(int(3600 / MUESTREO_S)),
                "microrred.capacidad_pv": env("CAPACIDAD_PV_KWP", "6.24"),
            }
            for clave, valor in parametros.items():
                cur.execute("SELECT set_config(%s, %s, true)", (clave, valor))
            ejecutar_sql(cur, "02_gold.sql")
            cur.executemany(
                "INSERT INTO ops.etl_regla VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                [(ejec, *r) for r in b.reglas])
            # Conciliación: lo que salió de la limpieza vs lo que quedó cargado en Silver y Gold
            cur.execute("""
                SELECT (SELECT sum(n_lecturas) FROM silver.lectura_1min WHERE origen='historico'),
                       (SELECT sum(n_recibidas) FROM silver.lectura_1min WHERE origen='historico'),
                       (SELECT sum(energia_pv_kwh) FROM gold.fact_energia_hora),
                       (SELECT sum(energia_carga_kwh) FROM gold.fact_energia_hora),
                       (SELECT sum(energia_red_kwh) FROM gold.fact_energia_hora),
                       (SELECT count(*) FROM gold.fact_actividad)""")
            v = cur.fetchone()
            controles = [
                ("Lecturas válidas: limpieza → silver", totales_origen["lecturas_validas"], v[0],
                 "Deben coincidir exactamente."),
                ("Lecturas únicas: limpieza → silver", totales_origen["lecturas_unicas"], v[1],
                 "Deben coincidir exactamente."),
                ("Energía solar kWh: lecturas → gold", totales_origen["pv_kwh"], v[2],
                 "Diferencia solo por redondeo a 3 decimales por minuto."),
                ("Energía a la carga kWh: lecturas → gold", totales_origen["carga_kwh"], v[3],
                 "Diferencia solo por redondeo."),
                ("Energía de la red kWh: lecturas → gold", totales_origen["red_kwh"], v[4],
                 "Diferencia solo por redondeo."),
                ("Registros de contexto: limpieza → gold", totales_origen["contextos"], v[5],
                 "Deben coincidir exactamente."),
            ]
            cur.executemany("INSERT INTO ops.conciliacion (ejecucion_id, control, valor_origen, valor_destino, "
                            "explicacion) VALUES (%s,%s,%s,%s,%s)", [(ejec, *c) for c in controles])
            if conciliacion_contador:
                cur.executemany("INSERT INTO ops.conciliacion_contador (ejecucion_id, inversor_id, mes, variable, "
                                "energia_contador_kwh, energia_integrada_kwh, horas_ventana) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                                [(ejec, *c) for c in conciliacion_contador])
            cur.execute("UPDATE ops.etl_ejecucion SET fin = now(), estado = 'ok', mensaje = %s WHERE ejecucion_id = %s",
                        (f"{len(silver):,} minutos, {len(contexto):,} contextos", ejec))
        con.commit()
        print(f"Carga Silver + Gold en {time.time() - t:.0f} s")
        print("Conciliación:")
        for nombre, o, d, _ in controles:
            print(f"  {nombre:<42} origen={float(o or 0):>14,.3f}  destino={float(d or 0):>14,.3f}  "
                  f"dif={float(d or 0) - float(o or 0):,.3f}")
        with con.cursor() as cur:
            cur.execute("""SELECT 'silver.lectura_1min', count(*) FROM silver.lectura_1min WHERE origen='historico'
                           UNION ALL SELECT 'silver.contexto', count(*) FROM silver.contexto
                           UNION ALL SELECT 'gold.fact_energia_hora', count(*) FROM gold.fact_energia_hora
                           UNION ALL SELECT 'gold.fact_evento', count(*) FROM gold.fact_evento
                           UNION ALL SELECT 'gold.fact_actividad', count(*) FROM gold.fact_actividad
                           UNION ALL SELECT 'gold.dim_fecha', count(*) FROM gold.dim_fecha""")
            print("Filas cargadas:")
            for tabla, n in cur.fetchall():
                print(f"  {tabla:<26} {n:>10,}")
        print(f"ETL OK · ejecución {ejec}")
    except Exception as e:
        con.rollback()
        con.autocommit = True
        with con.cursor() as cur:
            cur.execute("UPDATE ops.etl_ejecucion SET fin = now(), estado = 'error', mensaje = %s "
                        "WHERE ejecucion_id = %s", (str(e)[:2000], ejec))
        raise
    finally:
        con.close()


if __name__ == "__main__":
    main()
