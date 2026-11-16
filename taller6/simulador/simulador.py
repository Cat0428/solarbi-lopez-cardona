"""
Taller 6 · Simulador de streaming (CronJob de Kubernetes, una corrida por minuto)

Cada corrida "reproduce" telemetría histórica como si estuviera llegando ahora:
  1. Busca el último minuto simulado (o arranca SIM_MINUTOS_INICIALES minutos atrás).
  2. Para cada minuto pendiente hasta "ahora" y cada inversor toma un minuto HISTÓRICO de
     silver.lectura_1min: mismo reloj de pared (hora de Colombia) sobre un día histórico
     completo que rota cada día. Así el sol "sale" en la sesión de Colombia aunque la planta
     esté en Shenzhen, y la curva de un día real se reproduce entera.
  3. Lo inserta con origen = 'simulador' (ON CONFLICT DO NOTHING: repetir no duplica).
  4. Inyecta episodios de batería baja en SIM_INVERSOR_ANOMALIA: cada SIM_ANOMALIA_CADA_MIN
     minutos de reloj, durante SIM_ANOMALIA_DURACION_MIN minutos seguidos, el SOC queda en
     SIM_SOC_ANOMALIA %. Un episodio dura varios minutos (como uno real), así que supera el
     "for: 2m" de la regla de Grafana y la alerta pasa a Firing y luego vuelve a Normal.
     Con SIM_ANOMALIA_CADA_MIN = 0 no hay anomalías.
  5. Borra lo simulado con más de SIM_RETENCION_HORAS (la tabla no crece sin límite).

Todo parámetro llega por variables de entorno desde el ConfigMap microrred-parametros:
cambiar un umbral NO requiere reconstruir la imagen; la siguiente corrida ya lo usa.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import psycopg


def env(nombre: str, defecto: str) -> str:
    return os.getenv(nombre, defecto)


ZONA_SITIO = ZoneInfo(env("ZONA_SITIO", "Asia/Shanghai"))
ZONA_DEMO = ZoneInfo(env("SIM_ZONA_RELOJ", "America/Bogota"))
MAX_MINUTOS = int(env("SIM_MAX_MINUTOS", "30"))
MINUTOS_INICIALES = int(env("SIM_MINUTOS_INICIALES", "180"))
ANOMALIA_CADA = int(env("SIM_ANOMALIA_CADA_MIN", "0"))          # 0 = sin anomalías
ANOMALIA_DURACION = int(env("SIM_ANOMALIA_DURACION_MIN", "6"))
INVERSOR_ANOMALIA = int(env("SIM_INVERSOR_ANOMALIA", "2"))
SOC_ANOMALIA = float(env("SIM_SOC_ANOMALIA", "12"))
RETENCION_H = int(env("SIM_RETENCION_HORAS", "48"))
MIN_MINUTOS_DIA = int(env("SIM_MIN_MINUTOS_DIA", "1300"))   # días "completos" que sirven de plantilla

COLUMNAS = ("n_recibidas, n_lecturas, segundos_cubiertos, soc_pct, soc_min_pct, bat_voltaje_v, "
            "bat_corriente_a, temp_inversor_c, pv_potencia_w, carga_potencia_w, carga_max_w, red_potencia_w, "
            "bat_potencia_w, salida_voltaje_v, red_voltaje_v, red_frecuencia_hz, pv_energia_wh, "
            "carga_energia_wh, red_energia_wh, bat_carga_energia_wh, bat_desc_energia_wh")


def conectar() -> psycopg.Connection:
    try:
        return psycopg.connect(host=env("PGHOST", "postgres"), port=int(env("PGPORT", "5432")),
                               dbname=os.environ["POSTGRES_DB"], user=os.environ["POSTGRES_USER"],
                               password=os.environ["POSTGRES_PASSWORD"], connect_timeout=10)
    except KeyError as e:
        sys.exit(f"Falta la variable {e} (Secret microrred-credenciales)")


def dias_plantilla(cur, inversor: int) -> list:
    cur.execute("""
        SELECT (ts AT TIME ZONE %s)::date AS dia
        FROM silver.lectura_1min
        WHERE origen = 'historico' AND inversor_id = %s AND n_lecturas > 0
        GROUP BY 1 HAVING count(*) >= %s ORDER BY 1""", (str(ZONA_SITIO), inversor, MIN_MINUTOS_DIA))
    return [r[0] for r in cur.fetchall()]


def main() -> None:
    ahora = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    with conectar() as con, con.cursor() as cur:
        cur.execute("SELECT max(ts) FROM silver.lectura_1min WHERE origen = 'simulador'")
        ultimo = cur.fetchone()[0]
        desde = (ultimo + timedelta(minutes=1)) if ultimo else ahora - timedelta(minutes=MINUTOS_INICIALES)
        desde = max(desde, ahora - timedelta(minutes=MINUTOS_INICIALES))
        if desde > ahora:
            print("Nada pendiente")
            return
        minutos = []
        m = desde
        while m <= ahora:
            minutos.append(m)
            m += timedelta(minutes=1)
        minutos = minutos[-MAX_MINUTOS:] if ultimo else minutos      # primera vez: llena la ventana inicial

        # Minutos del lote que caen dentro de un episodio de batería baja (determinista por reloj:
        # repetir la corrida o perder un lote no cambia qué minutos son anómalos)
        anomalos = [m for m in minutos
                    if ANOMALIA_CADA > 0 and int(m.timestamp() // 60) % ANOMALIA_CADA < ANOMALIA_DURACION]
        insertadas = 0
        for inversor in (1, 2):
            dias = dias_plantilla(cur, inversor)
            if not dias:
                print(f"Inversor {inversor}: no hay días históricos completos (¿ya corrió el ETL?)")
                continue
            for minuto in minutos:
                reloj = minuto.astimezone(ZONA_DEMO)                        # hora de pared en Colombia
                dia = dias[reloj.date().toordinal() % len(dias)]            # día histórico de turno
                plantilla = datetime.combine(dia, reloj.time(), tzinfo=ZONA_SITIO)
                cur.execute(f"""
                    INSERT INTO silver.lectura_1min (ts, inversor_id, origen, {COLUMNAS})
                    SELECT %s, inversor_id, 'simulador', {COLUMNAS}
                    FROM silver.lectura_1min
                    WHERE origen = 'historico' AND inversor_id = %s
                      AND ts BETWEEN %s - interval '5 minutes' AND %s
                    ORDER BY ts DESC LIMIT 1
                    ON CONFLICT (inversor_id, ts) DO NOTHING""", (minuto, inversor, plantilla, plantilla))
                insertadas += cur.rowcount
            if anomalos and inversor == INVERSOR_ANOMALIA:
                cur.execute("""UPDATE silver.lectura_1min SET soc_pct = %s, soc_min_pct = %s
                               WHERE origen = 'simulador' AND inversor_id = %s AND ts = ANY(%s)""",
                            (SOC_ANOMALIA, SOC_ANOMALIA, inversor, anomalos))
                print(f"ANOMALÍA: inversor {inversor} con SOC {SOC_ANOMALIA} % en {len(anomalos)} minuto(s)")
        cur.execute("DELETE FROM silver.lectura_1min WHERE origen = 'simulador' AND ts < now() - make_interval(hours => %s)",
                    (RETENCION_H,))
        borradas = cur.rowcount
        con.commit()
    print(f"{ahora:%Y-%m-%d %H:%M} UTC · minutos {minutos[0].astimezone(timezone.utc):%H:%M}–"
          f"{minutos[-1].astimezone(timezone.utc):%H:%M} UTC · "
          f"{insertadas} filas nuevas · {borradas} antiguas borradas")


if __name__ == "__main__":
    try:
        main()
    except (psycopg.errors.UndefinedTable, psycopg.OperationalError) as e:
        # Primer minuto del clúster: PostgreSQL todavía arranca o el ETL aún no crea las tablas.
        # No es un fallo del simulador: se omite este lote y el CronJob lo intenta al minuto siguiente.
        print(f"Base aún no lista ({type(e).__name__}); se omite este lote: {str(e).strip()[:120]}")
