-- =====================================================================
-- PRUEBA de la alerta (solo para la demostración, no es parte del ETL).
-- Inserta una lectura con potencia 0 en el mediodía más reciente (hoy a
-- las 12:00 si ya pasó; si no, ayer a las 12:00, hora de Colombia).
-- En 1 a 6 minutos la regla de Grafana pasa Normal → Pending → Firing.
-- Ejecutar con el usuario solarbi (bi_lector no puede escribir).
-- =====================================================================
INSERT INTO silver.lectura_5min (ts, dispositivo_id, p_ac_kw, irradiancia_wm2, temp_modulo_c, energia_kwh)
VALUES (
    (date_trunc('day', (now() AT TIME ZONE 'America/Bogota') - interval '12 hours') + interval '12 hours')
        AT TIME ZONE 'America/Bogota',
    1, 0, 950, 48, 0)
ON CONFLICT (ts, dispositivo_id) DO UPDATE SET p_ac_kw = 0, energia_kwh = 0;

-- Para deshacer la prueba (la alerta vuelve a Normal):
-- DELETE FROM silver.lectura_5min
-- WHERE dispositivo_id = 1 AND p_ac_kw = 0 AND irradiancia_wm2 = 950 AND temp_modulo_c = 48;
