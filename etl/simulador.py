"""
SolarBI Pascual - Simulador de telemetría (capa Bronze).

Genera 3 días de lecturas cada 5 minutos de un inversor de 5 kWp con
anomalías inyectadas (potencia negativa, irradiancia faltante y filas
duplicadas). Basado en el simulador entregado por el docente; la única
diferencia es la semilla fija (SEMILLA), que hace que el archivo sea
reproducible: si dos personas lo ejecutan obtienen exactamente el mismo
CSV. Para datos distintos en cada ejecución: python etl/simulador.py --sin-semilla

Uso:
    python etl/simulador.py

Salida: data/bronze/telemetria.csv  (este archivo NO se modifica después).
"""
import argparse
import csv
import math
import os
import random
from datetime import datetime, timedelta

SEMILLA = 2026
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_BRONZE = os.path.join(RAIZ, "data", "bronze", "telemetria.csv")


def generar(ruta: str = RUTA_BRONZE, semilla: int | None = SEMILLA) -> str:
    if semilla is not None:
        random.seed(semilla)

    inicio = datetime(2026, 10, 5, 0, 0)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)

    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ts", "dispositivo_id", "p_ac_kw", "irradiancia_wm2", "temp_modulo_c"])
        for i in range(3 * 288):  # 3 días, cada 5 min
            ts = inicio + timedelta(minutes=5 * i)
            sol = max(0.0, math.sin(math.pi * (ts.hour + ts.minute / 60 - 6) / 12))
            irr = round(1000 * sol * random.uniform(0.7, 1.0), 1)
            p_ac = round(5.0 * irr / 1000 * random.uniform(0.80, 0.90), 3)
            fila = [ts.isoformat(sep=" "), 1, p_ac, irr, round(22 + 30 * sol, 1)]
            r = random.random()
            if r < 0.02:
                fila[2] = -1  # anomalía: potencia negativa
            elif r < 0.04:
                fila[3] = ""  # anomalía: dato faltante
            w.writerow(fila)
            if r > 0.98:
                w.writerow(fila)  # anomalía: fila duplicada
    return ruta


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genera la telemetría cruda (Bronze).")
    parser.add_argument("--sin-semilla", action="store_true",
                        help="Genera datos aleatorios distintos en cada ejecución.")
    args = parser.parse_args()
    ruta = generar(semilla=None if args.sin_semilla else SEMILLA)
    print(f"Bronze generado: {ruta}")
