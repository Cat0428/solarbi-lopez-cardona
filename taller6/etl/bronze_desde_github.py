"""
Taller 6 · Plan B para la capa Bronze: reconstruir la base SQLite a partir de la exportación
CSV del repositorio público github.com/OpenCEM-platform/opencem-dataset.

    git clone --depth 1 https://github.com/OpenCEM-platform/opencem-dataset
    python etl/bronze_desde_github.py ruta/opencem-dataset data/bronze/opencem-github.sqlite

La fuente oficial del taller es opencem-v1.0.0.sqlite (Zenodo). Este script produce un archivo
con LAS MISMAS DOS TABLAS que usa el script oficial de exportación del dataset
(scripts/ingest.py lee `analog_measurements` y `context`), para que el ETL funcione igual con
cualquiera de las dos. No corrige nada: solo deja los datos en SQLite tal como vienen. Lo que sí
hace es resolver un defecto de la EXPORTACIÓN, documentado en el informe:

  * Las particiones CSV se escribieron en modo "append": cuando la fuente pasó de 82 a 78
    columnas (desaparecieron battreserve, pvreserve, otherreserve, grid_reserve), se añadieron
    filas de 78 campos debajo de un encabezado de 82. Leídas por encabezado, quedarían
    corridas cuatro posiciones. Aquí cada fila se interpreta según SU número de campos.
  * Las particiones de contexto se solapan (p. ej. 2025-11.csv y 2025-11-a/b.csv repiten
    registros). Se cargan TODAS, con el archivo de origen, para que el ETL mida y quite el
    duplicado con una regla explícita.
"""
from __future__ import annotations

import csv
import glob
import os
import sqlite3
import sys
from collections import Counter

COLS_82 = ("read_ts,inverter,battvolt,battcurr,battsoc,battchgpower,linechgcurr,pvchgcurr,battreserve,"
           "pv1volt,pv1curr,pv1power,pv2volt,pv2curr,pv2power,pv3volt,pv3curr,pv3power,pvreserve,outvolta,"
           "outcurra,outfreq,invcurra,outw_a,outva_a,loadpercenta,normalloadw_a,outvoltb,outcurrb,invcurrb,"
           "outw_b,outva_b,loadpercentb,normalloadw_b,outvoltc,outcurrc,invcurrc,outw_c,outva_c,loadpercentc,"
           "normalloadw_c,outsumw,outsumva,sumloadpercent,generatedpowerp_a,generatedpowerp_b,"
           "generatedpowerp_c,generatedpowers_a,generatedpowers_b,generatedpowers_c,generatedpowerq_a,"
           "generatedpowerq_b,generatedpowerq_c,linevolta,linecurra,linefreq,linevoltb,linecurrb,linevoltc,"
           "linecurrc,linepowerva_a,linepowerva_b,linepowerva_c,linepowerw_a,linepowerw_b,linepowerw_c,"
           "busvoltp,busvoltn,temper1,temper2,temper3,temper4,sir,fanduty,otherreserve,gridpowerw_a,"
           "gridpowerw_b,gridpowerw_c,gridcurr_a,gridcurr_b,gridcurr_c,grid_reserve").split(",")
RESERVAS = {"battreserve", "pvreserve", "otherreserve", "grid_reserve"}
COLS_78 = [c for c in COLS_82 if c not in RESERVAS]
TEXTO = RESERVAS  # arreglos tipo "{0,0,0,0}"


def convertir(col: str, v: str):
    if v == "":
        return None
    if col in TEXTO:
        return v
    try:
        return int(v)
    except ValueError:
        try:
            return float(v)
        except ValueError:
            return v  # se deja tal cual: el ETL lo detecta como no numérico


def main(repo: str, destino: str) -> None:
    if os.path.exists(destino):
        os.remove(destino)
    con = sqlite3.connect(destino)
    tipos = {c: ("TEXT" if c in TEXTO else "REAL") for c in COLS_82}
    tipos["read_ts"] = tipos["inverter"] = "INTEGER"
    con.execute("CREATE TABLE analog_measurements (" + ", ".join(f'"{c}" {tipos[c]}' for c in COLS_82)
                + ", _archivo TEXT)")
    con.execute('CREATE TABLE context (id INTEGER, recorded INTEGER, start INTEGER, "end" INTEGER, '
                'value TEXT, _archivo TEXT)')
    marcadores = ",".join("?" * (len(COLS_82) + 1))
    resumen = Counter()
    for ruta in sorted(glob.glob(os.path.join(repo, "data", "measurements", "*.csv"))):
        nombre = os.path.basename(ruta)
        lote = []
        with open(ruta, newline="", encoding="utf-8") as f:
            lector = csv.reader(f)
            next(lector)
            for fila in lector:
                if len(fila) == 82:
                    reg = dict(zip(COLS_82, fila))
                elif len(fila) == 78:
                    reg = dict(zip(COLS_78, fila))
                else:
                    resumen[f"{nombre}: fila de {len(fila)} campos descartada"] += 1
                    continue
                resumen[f"campos={len(fila)}"] += 1
                lote.append([convertir(c, reg.get(c, "")) for c in COLS_82] + [nombre])
                if len(lote) >= 50_000:
                    con.executemany(f"INSERT INTO analog_measurements VALUES ({marcadores})", lote)
                    lote.clear()
        if lote:
            con.executemany(f"INSERT INTO analog_measurements VALUES ({marcadores})", lote)
        print(f"{nombre}: ok")
    for ruta in sorted(glob.glob(os.path.join(repo, "data", "context", "*.csv"))):
        nombre = os.path.basename(ruta)
        with open(ruta, newline="", encoding="utf-8") as f:
            lector = csv.reader(f)
            next(lector)
            filas = [[convertir("x", r[0]), convertir("x", r[1]), convertir("x", r[2]), convertir("x", r[3]),
                      r[4], nombre] for r in lector if len(r) == 5]
        con.executemany("INSERT INTO context VALUES (?,?,?,?,?,?)", filas)
        resumen["context filas"] += len(filas)
    con.commit()
    con.execute("CREATE INDEX ix_am_ts ON analog_measurements (read_ts, inverter)")
    con.commit()
    con.close()
    for k, v in sorted(resumen.items()):
        print(f"{k}: {v:,}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
