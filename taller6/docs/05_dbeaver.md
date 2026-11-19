# DBeaver: administración del modelo y consultas (punto F)

El enunciado pide que el DDL del modelo dimensional se **administre desde DBeaver** y que DBeaver sea
una de las herramientas de la sustentación. DBeaver corre en Windows (el anfitrión) y entra al
PostgreSQL del clúster por el `NodePort` publicado en `127.0.0.1:55432` (ver
[03_despliegue_kubernetes.md](03_despliegue_kubernetes.md)). Con Docker Compose el puerto es el mismo.

## 1. Dos conexiones, dos roles

Se crean dos conexiones con el **principio de mínimo privilegio**: la de administración solo se
usa para el DDL; todo lo demás (consultas, evidencias, la demostración en vivo) va por la de
solo lectura, igual que Power BI y Grafana.

| Campo | Microrred · administración | Microrred · consulta |
|---|---|---|
| Host / Puerto | `127.0.0.1` / `55432` | `127.0.0.1` / `55432` |
| Base de datos | `microrred` | `microrred` |
| Usuario | `microrred` (`POSTGRES_USER`) | `bi_lector` |
| Contraseña | `POSTGRES_PASSWORD` de `credenciales.env` | `BI_LECTOR_PASSWORD` de `credenciales.env` |
| Pestaña *General* → tipo de conexión | **Production** (pide confirmar cada ejecución y desactiva el autocommit) | **Development** |
| Pestaña *General* → *Read-only connection* | No | **Sí** |
| Guardar contraseña | No (se escribe al conectar) | Opcional |

Pasos: *Database → New Database Connection → PostgreSQL*. La primera vez DBeaver ofrece
descargar el controlador JDBC de PostgreSQL; hay que aceptarlo (necesita internet). SSL queda
desactivado porque el puerto solo escucha en `127.0.0.1`.

> La contraseña de cada rol se fija **solo en el primer arranque** de PostgreSQL (volumen vacío).
> Si después se cambia `credenciales.env`, la base conserva la anterior: hay que recrear el
> volumen (`down` + `up`) o cambiarla con `ALTER ROLE` desde la conexión de administración.

**Zona horaria.** DBeaver muestra los `timestamptz` en la hora del equipo (Colombia, UTC−5). Las
llaves `fecha_key` y `hora_key` del modelo están en hora del sitio (Asia/Shanghai, UTC+8). Para
ver las horas como las ve el modelo: `SET TIME ZONE 'Asia/Shanghai';` en el editor.

## 2. Abrir los scripts del repositorio en DBeaver

En la vista *Projects* → clic derecho en *Scripts* → **Link Folder** → elegir `taller6\sql`. Así
DBeaver edita los mismos archivos que versiona Git (no copias sueltas en su espacio de trabajo).
A cada script se le asigna la conexión con el selector de la barra superior del editor.

| Script | Conexión | Para qué |
|---|---|---|
| `01_ddl.sql` | administración | Crear o actualizar esquemas, tablas, restricciones e índices |
| `03_consultas_negocio.sql` | consulta | Q1–Q9: preguntas de negocio (agregaciones, ventanas, comparativos, JSON) |
| `04_catalogo_dbeaver.sql` | consulta | E1–E9: evidencias del modelo para el informe |

## 3. Administrar el DDL

1. Abrir `01_ddl.sql` con la conexión de administración y ejecutarlo completo con **Alt+X**
   (*Execute script*). Es idempotente (`CREATE … IF NOT EXISTS`): en una base ya creada solo
   aparecen avisos `NOTICE … already exists, skipping` en la pestaña *Output*.
2. Confirmar con *Commit* (la conexión *Production* no hace autocommit).
3. Refrescar el navegador (F5) y revisar `silver`, `gold` y `ops`.

El ETL ejecuta el mismo archivo al inicio de cada corrida, así que DBeaver y el clúster nunca
divergen: **todo cambio de estructura se escribe en `01_ddl.sql`** y se versiona; nada se crea
a mano solo en la base. `02_gold.sql` vacía y recarga las tablas Gold, pero no las borra, por lo
que un índice o una restricción nuevos se conservan entre corridas.

Ejemplo de cambio en vivo (si el docente lo pide), escrito en `01_ddl.sql` y ejecutado con
Ctrl+Enter:

```sql
CREATE INDEX IF NOT EXISTS ix_fe_inversor ON gold.fact_evento (inversor_key);
```

## 4. Diagrama entidad-relación

En el navegador: `microrred → Schemas → gold` → clic derecho → **View Diagram**. Las líneas salen
de las llaves foráneas declaradas en `01_ddl.sql` (los tres hechos apuntan a sus dimensiones), así
que el diagrama muestra la constelación tal como está en la base. Para el informe: botón
*Save diagram as image* (PNG). Conviene ocultar `ops` y `silver` para que la estrella se lea sola.

## 5. Consultas de negocio y evidencias

En `03_consultas_negocio.sql` cada consulta se ejecuta con **Ctrl+Enter** sobre la sentencia
donde está el cursor; el resultado sale en una pestaña propia. Para el informe sirve una captura
de cada pregunta con su resultado.

`04_catalogo_dbeaver.sql` reúne las evidencias del punto F:

| Bloque | Qué demuestra |
|---|---|
| E1 | Inventario de tablas por capa con filas estimadas y tamaño en disco |
| E2 | Conteo exacto de cada tabla Gold |
| E3 | Llaves primarias, foráneas, únicas y CHECK (restricciones justificadas) |
| E4 | Índices y su tipo: B-tree, **BRIN** sobre el tiempo y **GIN** sobre el JSON |
| E5 | Plan de la consulta JSON con `@>`; prueba de que el índice GIN la atiende |
| E6 | Plan del filtro por rango de tiempo: `Bitmap Index Scan on brin_lectura_1min_ts` |
| E7 | `bi_lector` tiene `SELECT` en las tres capas y cero permisos de escritura |
| E8 | Linaje: últimas corridas del ETL, duración, estado y huella SHA-256 del Bronze |
| E9 | Minutos que va insertando el simulador (datos en vivo) |

Sobre E5: `silver.contexto` tiene pocas filas, así que el planificador puede preferir leerla
completa (`Seq Scan`) en vez de usar el índice; es la decisión correcta para ese tamaño. Por eso
el bloque trae una segunda versión que desactiva el `Seq Scan` solo dentro de la transacción y
muestra `Bitmap Index Scan on gin_contexto_valor`. El índice se justifica porque el contexto crece con cada
anotación nueva y porque Q7 y Q8 filtran el JSON por contenido. En cambio, E6 sí usa BRIN con el
plan normal: la tabla de minutos tiene casi 800 000 filas y llegan en orden de tiempo.

## 6. Demostración en vivo con DBeaver

1. **Conexión:** abrir *Microrred · consulta* y mostrar que apunta a `127.0.0.1:55432` (el
   NodePort del clúster).
2. **Modelo:** el diagrama de `gold` y E3/E4 (restricciones e índices).
3. **Negocio:** Q2 (comparativo entre meses con `LAG`) y Q7 (JSON con `@>`, `?`, `->>`).
4. **Datos en vivo:** ejecutar E9, esperar un minuto (el CronJob del simulador) y volver a
   ejecutar: aumentan los minutos simulados.
5. **Seguridad:** con *Microrred · consulta* intentar `DELETE FROM gold.dim_hora;` → DBeaver lo
   bloquea por ser conexión de solo lectura; aun desactivando esa opción, PostgreSQL responde
   `permission denied` porque `bi_lector` no tiene permisos de escritura (E7).
6. **Persistencia (K.4):** ejecutar E2, borrar el pod (`kubectl delete pod postgres-0 -n microrred`),
   esperar a que vuelva, reconectar (*Invalidate/Reconnect*) y ejecutar E2 otra vez: mismos conteos.

## 7. Problemas frecuentes

| Síntoma | Causa y solución |
|---|---|
| `Connection refused` | El clúster no está arriba o el puerto no se publicó: `kubectl get svc -n microrred` debe mostrar `postgres-externo` con `30432`; con Compose, `docker compose ps` |
| `password authentication failed` | La contraseña de `credenciales.env` cambió después del primer arranque (ver nota de la sección 1) |
| `permission denied for schema …` al ejecutar el DDL | El script se lanzó con la conexión de consulta; usar la de administración |
| Las horas se ven corridas 13 h | Diferencia entre Colombia (UTC−5) y el sitio (UTC+8); usar `SET TIME ZONE` |
| No aparecen las líneas del diagrama | Falta refrescar el navegador después de ejecutar el DDL (F5) |
