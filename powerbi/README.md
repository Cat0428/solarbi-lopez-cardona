# Power BI · SolarBI Pascual (Grupo 01)

Guarden aquí el informe como **Power BI Project (.pbip)** (recomendado para Git) o como `.pbix`.
`Archivo → Guardar como → Tipo: Proyecto de Power BI (*.pbip)`.

## 1. Conexión a PostgreSQL

1. `Inicio → Obtener datos → Base de datos PostgreSQL`.
2. Servidor: `localhost:5432` · Base de datos: `solarbi` · Modo: **Importar**.
3. Credenciales (pestaña *Base de datos*): usuario `bi_lector` y la contraseña de `BI_LECTOR_PASSWORD` del `.env`.
   Es un rol de **solo lectura**: Power BI no puede modificar la bodega.
4. Si aparece el aviso *"no se admite el cifrado"*, acepten la conexión sin cifrar (el contenedor local no tiene SSL).
5. Seleccionen: `dwh.fact_energia_dia`, `dwh.dim_fecha`, `dwh.dim_dispositivo` (y, opcional, `silver.lectura_5min`).

## 2. Modelo (esquema estrella)

| Desde (muchos)                        | Hacia (uno)                         |
|---------------------------------------|-------------------------------------|
| `fact_energia_dia[fecha_key]`         | `dim_fecha[fecha_key]`              |
| `fact_energia_dia[dispositivo_key]`   | `dim_dispositivo[dispositivo_key]`  |

- Marcar `dim_fecha` como tabla de fechas (`Herramientas de tabla → Marcar como tabla de fechas → fecha`).
- Ocultar las claves (`fecha_key`, `dispositivo_key`) en la vista de informe.

## 3. Medidas DAX

Crear una tabla vacía `_Medidas` (`Inicio → Especificar datos → Cargar`) y agregar:

```dax
Energía Total (kWh) =
SUM ( fact_energia_dia[energia_kwh] )

% Datos Válidos =
DIVIDE (
    SUM ( fact_energia_dia[n_lecturas_validas] ),
    SUM ( fact_energia_dia[n_lecturas_esperadas] )
)
-- Formato: Porcentaje, 1 decimal. Es un promedio PONDERADO, no el promedio de los %.

Energía Promedio Diaria (kWh) =
AVERAGEX ( VALUES ( dim_fecha[fecha] ), [Energía Total (kWh)] )

Yield (kWh/kWp) =
SUM ( fact_energia_dia[yield_kwh_kwp] )

Performance Ratio =
DIVIDE (
    SUM ( fact_energia_dia[yield_kwh_kwp] ),
    SUM ( fact_energia_dia[irradiacion_kwh_m2] )
)
-- Formato: Porcentaje. Irradiación en kWh/m² ÷ 1 kW/m² = horas de sol pico.

Potencia Máxima (kW) =
MAX ( fact_energia_dia[p_max_kw] )
```

## 4. Página del informe

| Visual                | Campos                                                          |
|-----------------------|-----------------------------------------------------------------|
| Tarjeta               | `[Energía Total (kWh)]`                                         |
| Gráfico de líneas     | Eje X: `dim_fecha[fecha]` (sin jerarquía) · Eje Y: `[Energía Total (kWh)]` |
| Tarjeta               | `[% Datos Válidos]`                                             |
| (opcional) Tarjetas   | `[Performance Ratio]`, `[Yield (kWh/kWp)]`                      |
| (opcional) Segmentador| `dim_dispositivo[nombre]`                                       |

Valores esperados con el Bronze de semilla 2026: energía total **79,03 kWh**, energía diaria
26,15 / 26,54 / 26,35 kWh y datos válidos **96,2 %**.

## 5. Seguridad a nivel de fila (pregunta G4)

`Modelado → Administrar roles → Nuevo rol` **Responsable Robledo**, tabla `dim_dispositivo`:

```dax
[sitio] = "Sede Robledo"
```

Versión dinámica (un solo rol para todos los responsables), con una tabla `dim_responsable(email, sitio)`
relacionada con `dim_dispositivo[sitio]`:

```dax
dim_responsable[email] = USERPRINCIPALNAME ()
```

Probar con `Modelado → Ver como → Responsable Robledo`. En el servicio, asignar los usuarios al rol
en `Conjunto de datos → Seguridad`.
