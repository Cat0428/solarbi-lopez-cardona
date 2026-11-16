"""
Taller 6 · Inventario de la capa Bronze (OpenCEM v1.0.0)

    python etl/inventario.py data/bronze/opencem-v1.0.0.sqlite [--sums data/bronze/opencem-v1.0.0-SHA256SUMS.txt]

Qué hace (punto 9 del enunciado):
  1. Verifica la integridad (SHA-256) de los archivos descargados contra SHA256SUMS.
  2. Abre la base SQLite en modo SOLO LECTURA e inmutable: la capa Bronze no se modifica.
  3. Inventaría tablas, columnas, tipos, número de filas, periodo que cubre cada tabla
     y qué columnas de texto contienen JSON.
  4. Escribe docs/inventario_bronze.md (para el informe) y docs/inventario_bronze.json.

Solo usa la biblioteca estándar de Python.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLS_TIEMPO = {"read_ts", "recorded", "start", "end", "timestamp", "ts"}


def sha256(ruta: str, bloque: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        while chunk := f.read(bloque):
            h.update(chunk)
    return h.hexdigest()


def verificar_checksums(ruta_sums: str) -> list[dict]:
    """Compara cada archivo listado en SHA256SUMS que exista junto a él."""
    carpeta = os.path.dirname(os.path.abspath(ruta_sums))
    resultados = []
    with open(ruta_sums, encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea:
                continue
            esperado, nombre = linea.split(maxsplit=1)
            nombre = nombre.lstrip("*")
            ruta = os.path.join(carpeta, nombre)
            if not os.path.exists(ruta):
                resultados.append({"archivo": nombre, "estado": "no descargado"})
                continue
            calculado = sha256(ruta)
            resultados.append({
                "archivo": nombre,
                "esperado": esperado,
                "calculado": calculado,
                "estado": "OK" if calculado.lower() == esperado.lower() else "NO COINCIDE",
            })
    return resultados


def a_fecha(valor):
    """Interpreta epoch (s o ms) o texto ISO; devuelve texto ISO UTC o el valor tal cual."""
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        v = float(valor)
        if v > 1e12:  # milisegundos
            v /= 1000
        if 1e9 < v < 4e9:
            return datetime.fromtimestamp(v, tz=timezone.utc).isoformat()
    return str(valor)


def inventariar(ruta_db: str) -> dict:
    con = sqlite3.connect(f"file:{ruta_db}?mode=ro&immutable=1", uri=True)
    cur = con.cursor()
    tablas = [r[0] for r in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    vistas = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='view' ORDER BY name")]
    indices = [r for r in cur.execute(
        "SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")]

    salida = {"archivo": os.path.basename(ruta_db), "bytes": os.path.getsize(ruta_db),
              "tablas": [], "vistas": vistas,
              "indices": [{"nombre": n, "tabla": t, "sql": s} for n, t, s in indices]}
    for t in tablas:
        q = f'"{t}"'
        cols = [{"nombre": c[1], "tipo": c[2], "pk": bool(c[5]), "not_null": bool(c[3])}
                for c in cur.execute(f"PRAGMA table_info({q})")]
        filas = cur.execute(f"SELECT count(*) FROM {q}").fetchone()[0]
        fks = [{"columna": r[3], "ref_tabla": r[2], "ref_columna": r[4]}
               for r in cur.execute(f"PRAGMA foreign_key_list({q})")]
        for c in cols:
            cn = f'"{c["nombre"]}"'
            nulos, distintos = cur.execute(
                f"SELECT sum({cn} IS NULL), count(DISTINCT {cn}) FROM {q}").fetchone()
            c["nulos"], c["distintos"] = nulos or 0, distintos
            nom = c["nombre"].lower()
            if nom in COLS_TIEMPO or nom.endswith("_ts") or nom.startswith("t_") or "date" in (c["tipo"] or "").lower():
                mn, mx = cur.execute(f"SELECT min({cn}), max({cn}) FROM {q}").fetchone()
                c["min"], c["max"] = a_fecha(mn), a_fecha(mx)
            elif (c["tipo"] or "").upper() in ("", "TEXT", "JSON", "BLOB") and filas:
                validos, no_nulos = cur.execute(
                    f"SELECT sum(json_valid({cn}) AND substr(trim({cn}),1,1) IN ('{{','[')), "
                    f"count({cn}) FROM {q}").fetchone()
                if validos:
                    c["json"] = f"{validos}/{no_nulos} valores son JSON"
            elif (c["tipo"] or "").upper() in ("REAL", "INTEGER", "NUMERIC", "FLOAT", "DOUBLE"):
                mn, mx, prom = cur.execute(f"SELECT min({cn}), max({cn}), avg({cn}) FROM {q}").fetchone()
                c["min"], c["max"], c["prom"] = mn, mx, prom
        muestra = cur.execute(f"SELECT * FROM {q} LIMIT 3").fetchall()
        salida["tablas"].append({
            "tabla": t, "filas": filas, "columnas": cols, "fks": fks,
            "muestra": [[str(v)[:120] if v is not None else None for v in fila] for fila in muestra],
        })
    con.close()
    return salida


def a_markdown(inv: dict, checks: list[dict]) -> str:
    l = ["# Inventario de la capa Bronze · OpenCEM v1.0.0", "",
         f"Generado: {datetime.now().astimezone().isoformat(timespec='seconds')}", ""]
    if checks:
        l += ["## Integridad (SHA-256)", "", "| Archivo | Estado | SHA-256 calculado |", "|---|---|---|"]
        l += [f"| {c['archivo']} | {c['estado']} | `{c.get('calculado', '')}` |" for c in checks]
        l.append("")
    l += [f"## Base `{inv['archivo']}` ({inv['bytes'] / 1e6:,.1f} MB descomprimida)", "",
          "| Tabla | Filas | Columnas | Periodo |", "|---|---:|---:|---|"]
    for t in inv["tablas"]:
        periodos = [f"{c['nombre']}: {c['min']} → {c['max']}" for c in t["columnas"] if "min" in c
                    and isinstance(c.get("min"), str)]
        l.append(f"| `{t['tabla']}` | {t['filas']:,} | {len(t['columnas'])} | {'<br>'.join(periodos[:2])} |")
    for t in inv["tablas"]:
        l += ["", f"### `{t['tabla']}` · {t['filas']:,} filas", "",
              "| Columna | Tipo | PK | Nulos | Distintos | Mín | Máx | Nota |", "|---|---|---|---:|---:|---|---|---|"]
        for c in t["columnas"]:
            l.append(f"| `{c['nombre']}` | {c['tipo']} | {'✓' if c['pk'] else ''} | {c['nulos']:,} | "
                     f"{c['distintos']:,} | {c.get('min', '')} | {c.get('max', '')} | {c.get('json', '')} |")
        if t["fks"]:
            l.append("")
            l += [f"- FK `{f['columna']}` → `{f['ref_tabla']}.{f['ref_columna']}`" for f in t["fks"]]
    return "\n".join(l) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sqlite", help="ruta al archivo .sqlite descomprimido")
    ap.add_argument("--sums", help="ruta a opencem-v1.0.0-SHA256SUMS.txt")
    ap.add_argument("--salida", default=os.path.join(RAIZ, "docs"))
    a = ap.parse_args()
    if not os.path.exists(a.sqlite):
        sys.exit(f"No existe {a.sqlite}. Ejecute primero scripts/preparar_bronze.")
    checks = verificar_checksums(a.sums) if a.sums else []
    inv = inventariar(a.sqlite)
    os.makedirs(a.salida, exist_ok=True)
    with open(os.path.join(a.salida, "inventario_bronze.json"), "w", encoding="utf-8") as f:
        json.dump({"checksums": checks, **inv}, f, ensure_ascii=False, indent=2, default=str)
    with open(os.path.join(a.salida, "inventario_bronze.md"), "w", encoding="utf-8") as f:
        f.write(a_markdown(inv, checks))
    for c in checks:
        print(f"[checksum] {c['archivo']}: {c['estado']}")
    for t in inv["tablas"]:
        print(f"{t['tabla']:<40} {t['filas']:>12,} filas  {len(t['columnas'])} columnas")


if __name__ == "__main__":
    main()
