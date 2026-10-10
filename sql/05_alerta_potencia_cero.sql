-- =====================================================================
-- Consulta de la regla de alerta de Grafana "Potencia cero en horario solar"
-- (provisionada en grafana/provisioning/alerting/reglas.yaml).
-- Cuenta, por dispositivo, las lecturas con potencia 0 entre las 9:00 y
-- las 15:00 (hora de Colombia) dentro de la ventana de evaluación.
-- Grafana reemplaza $__timeFilter(ts) por la ventana relativa de la regla
-- (24 h para la demostración; en operación real conviene 15 min).
-- La alerta se dispara cuando el conteo es > 0.
-- =====================================================================
SELECT d.nombre AS dispositivo,
       count(l.ts) AS lecturas_potencia_cero
FROM dwh.dim_dispositivo d
LEFT JOIN silver.lectura_5min l
       ON l.dispositivo_id = d.dispositivo_id
      AND $__timeFilter(l.ts)
      AND l.p_ac_kw <= 0
      AND (l.ts AT TIME ZONE 'America/Bogota')::time BETWEEN '09:00' AND '15:00'
GROUP BY d.nombre;
