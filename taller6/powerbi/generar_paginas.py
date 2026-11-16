"""Genera las páginas PBIR del informe del Taller 6 (7 páginas con navegador).

    python powerbi/generar_paginas.py <carpeta_temporal> [id_de_la_primera_pagina]

Escribe <carpeta_temporal>/pages/. Para instalarlas: cerrar Power BI Desktop y copiar el contenido
sobre powerbi/microrred.Report/definition/pages/ (la primera página reutiliza el id de la página
que creó Power BI al guardar el .pbip, para no tener que borrar carpetas).
"""
import hashlib
import json
import os
import sys

SALIDA = sys.argv[1]
VC = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.12.0/schema.json"
PG = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"
PGS = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json"
M = "_Medidas"


def uid(*p):
    return hashlib.sha1("|".join(map(str, p)).encode()).hexdigest()[:20]


def lit(v):
    return {"expr": {"Literal": {"Value": v}}}


def col(t, c):
    return {"Column": {"Expression": {"SourceRef": {"Entity": t}}, "Property": c}}


def mea(c, t=M):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": t}}, "Property": c}}


def proj(f, nombre=None):
    k = "Column" if "Column" in f else "Measure"
    t = f[k]["Expression"]["SourceRef"]["Entity"]
    p = f[k]["Property"]
    d = {"field": f, "queryRef": f"{t}.{p}", "nativeQueryRef": nombre or p}
    if nombre:
        d["displayName"] = nombre
    return d


def titulo(texto):
    return {"title": [{"properties": {"show": lit("true"), "text": lit(f"'{texto}'"),
                                      "fontSize": lit("12D")}}],
            "subTitle": [{"properties": {"show": lit("false")}}]}   # sin subtítulo automático en inglés


def visual(pagina, i, tipo, x, y, w, h, roles=None, titulo_txt=None, objetos=None, orden=None):
    v = {"visualType": tipo, "drillFilterOtherVisuals": True}
    if roles:
        v["query"] = {"queryState": {}}
        for r, fs in roles.items():
            ps = [proj(*f) if isinstance(f, tuple) else proj(f) for f in fs]
            if r in ("Category", "Rows") and len(ps) > 1:
                ps[0]["active"] = True      # varios campos en el eje = niveles de profundización
            v["query"]["queryState"][r] = {"projections": ps}
        if orden:
            v["query"]["sortDefinition"] = {"sort": [{"field": orden[0], "direction": orden[1]}], "isDefaultSort": True}
    if objetos:
        v["objects"] = objetos
    cont = {"$schema": VC, "name": uid(pagina, i), "position": {"x": x, "y": y, "z": i, "width": w, "height": h,
                                                                 "tabOrder": i}, "visual": v}
    if titulo_txt:
        cont["visual"]["visualContainerObjects"] = titulo(titulo_txt)
    return cont


def texto(pagina, i, x, y, w, h, lineas):
    parrafos = []
    for t, tam, negrita in lineas:
        estilo = {"fontSize": f"{tam}pt"}
        if negrita:
            estilo["fontWeight"] = "bold"
        parrafos.append({"textRuns": [{"value": t, "textStyle": estilo}]})
    return visual(pagina, i, "textbox", x, y, w, h, objetos={"general": [{"properties": {"paragraphs": parrafos}}]})


def tarjeta(pagina, i, x, y, medida, nombre, w=200, h=110):
    return visual(pagina, i, "card", x, y, w, h, {"Values": [(mea(medida), nombre)]},
                  objetos={"categoryLabels": [{"properties": {"show": lit("true")}}],
                           "labels": [{"properties": {"fontSize": lit("20D"), "labelDisplayUnits": lit("1D")}}]})


def segmentador(pagina, i, x, y, w, h, campo, nombre, estilo="Dropdown"):
    return visual(pagina, i, "slicer", x, y, w, h, {"Values": [(campo, nombre)]},
                  objetos={"data": [{"properties": {"mode": lit(f"'{estilo}'")}}]})


def encabezado(pagina, titulo_pag, subtitulo):
    # Navegador de páginas (barra inferior, mismo lugar en las 7 páginas) + título + segmentadores
    return [visual(pagina, 95, "pageNavigator", 20, 718, 1240, 38),
            texto(pagina, 0, 20, 6, 900, 70, [(titulo_pag, 20, True), (subtitulo, 11, False)]),
            segmentador(pagina, 90, 930, 2, 160, 84, col("dim_fecha", "anio_mes"), "Mes"),
            segmentador(pagina, 91, 1100, 2, 160, 84, col("dim_inversor", "nombre"), "Inversor")]


MES = col("dim_fecha", "anio_mes")
paginas = []

# 1 · Resumen ejecutivo ------------------------------------------------------------------
p = "resumen"
vs = encabezado(p, "Microrred OpenCEM · Resumen ejecutivo",
                "Energía, autosuficiencia y costo · 12/07/2025 a 13/07/2026 · hora local de Shenzhen")
for k, (m_, n) in enumerate([("Fracción solar %", "Fracción solar"), ("Dependencia de la red %", "Dependencia de la red"),
                             ("Batería llena en horas de sol %", "Batería llena (horas de sol)"),
                             ("Ciclos de batería por día", "Ciclos de batería/día"),
                             ("Costo de la red (COP)", "Costo de la red (COP)"), ("Datos válidos %", "Datos válidos")]):
    vs.append(tarjeta(p, 10 + k, 20 + k * 207, 92, m_, n, h=100))
vs.append(visual(p, 20, "lineChart", 20, 202, 820, 260,
                 {"Category": [MES, col("dim_fecha", "fecha")], "Y": [(mea("Energía solar (kWh)"), "Solar"), (mea("Energía de la red (kWh)"), "Red"),
                                           (mea("Energía a la carga (kWh)"), "Consumo")]},
                 "Energía mensual por origen (kWh) · profundice al día con ↓", orden=(MES, "Ascending")))
vs.append(visual(p, 21, "card", 850, 202, 410, 260, {"Values": [(mea("Hallazgo principal"), "Hallazgo principal")]},
                 "Lo que dicen los datos", objetos={"labels": [{"properties": {"fontSize": lit("14D")}}],
                                                    "categoryLabels": [{"properties": {"show": lit("false")}}],
                                                    "wordWrap": [{"properties": {"show": lit("true")}}]}))
vs.append(visual(p, 22, "clusteredBarChart", 20, 470, 1240, 240,
                 {"Category": [col("dim_inversor", "nombre")],
                  "Y": [(mea("Energía solar (kWh)"), "Solar"), (mea("Descarga de batería (kWh)"), "Batería"),
                        (mea("Energía de la red (kWh)"), "Red")]}, "Origen de la energía por inversor (kWh)"))
paginas.append((sys.argv[2] if len(sys.argv) > 2 else p, "1 · Resumen ejecutivo", vs))

# 2 · Configuración (SCD2) ----------------------------------------------------------------
p = "configuracion"
vs = encabezado(p, "¿Por qué la red aporta tanto? · Configuración del inversor (SCD tipo 2)",
                "Cada versión es un cambio real de settings.outpriority / chgpriority registrado por el equipo")
V = col("dim_inversor", "version_config")
vs.append(visual(p, 10, "clusteredBarChart", 20, 96, 620, 290,
                 {"Category": [V], "Y": [(mea("Dependencia de la red %"), "Dependencia de la red")]},
                 "Dependencia de la red por versión de configuración"))
vs.append(visual(p, 11, "clusteredBarChart", 650, 96, 610, 290,
                 {"Category": [V], "Y": [(mea("Batería llena en horas de sol %"), "Batería llena (horas de sol)")]},
                 "Batería llena en horas de sol por versión"))
vs.append(visual(p, 12, "tableEx", 20, 392, 1240, 318,
                 {"Values": [(col("dim_inversor", "nombre"), "Inversor"),
                             (col("dim_inversor", "prioridad_salida_texto"), "Prioridad de salida"),
                             (col("dim_inversor", "prioridad_carga_texto"), "Prioridad de carga"),
                             (col("dim_inversor", "vigente_desde"), "Desde"), (col("dim_inversor", "vigente_hasta"), "Hasta"),
                             (mea("Días con datos"), "Días"), (mea("Dependencia de la red %"), "Red/consumo"),
                             (mea("Ciclos de batería por día"), "Ciclos/día"), (mea("Fracción solar %"), "Fracción solar")]},
                 "Versiones de dim_inversor y su desempeño"))
paginas.append((p, "2 · Configuración (SCD2)", vs))

# 3 · Perfil horario ----------------------------------------------------------------------
p = "perfil"
vs = encabezado(p, "Perfil horario · ¿cuándo se compra energía?",
                "Promedios por hora local del sitio; la franja 'Mediodía solar' es donde conviene mover cargas")
H = col("dim_hora", "hora_texto")
vs.append(visual(p, 10, "clusteredColumnChart", 20, 96, 1240, 316,
                 {"Category": [H], "Y": [(mea("Energía solar (kWh)"), "Solar"), (mea("Descarga de batería (kWh)"), "Batería"),
                                         (mea("Energía de la red (kWh)"), "Red")]},
                 "Energía por hora del día (kWh, periodo filtrado)", orden=(H, "Ascending")))
vs.append(visual(p, 11, "pivotTable", 20, 420, 760, 290,
                 {"Rows": [col("dim_hora", "franja"), col("dim_hora", "hora_texto")], "Columns": [col("dim_inversor", "nombre")],
                  "Values": [(mea("Dependencia de la red %"), "Red/consumo"), (mea("Batería llena en horas de sol %"), "Bat. llena")]},
                 "Franja × inversor · expanda con + para ver cada hora"))
vs.append(visual(p, 12, "clusteredBarChart", 790, 420, 470, 290,
                 {"Category": [col("dim_fecha", "nombre_dia")], "Y": [(mea("Energía a la carga (kWh)"), "Consumo")]},
                 "Consumo por día de la semana (kWh)"))
paginas.append((p, "3 · Perfil horario", vs))

# 4 · Eventos -----------------------------------------------------------------------------
p = "eventos"
vs = encabezado(p, "Eventos operativos y fallas",
                "Detectados por el ETL (batería baja, salida apagada, cortes de red, sin datos) y reportados por el inversor")
for k, (m_, n) in enumerate([("Eventos críticos", "Eventos críticos"), ("Horas de operación aislada", "Horas sin red pública"),
                             ("Fallas reportadas por el inversor", "Fallas del inversor"), ("Horas en evento", "Horas en evento")]):
    vs.append(tarjeta(p, 10 + k, 20 + k * 312, 92, m_, n, w=300, h=100))
vs.append(visual(p, 20, "clusteredBarChart", 20, 202, 520, 508,
                 {"Category": [col("dim_tipo_evento", "categoria"), col("dim_tipo_evento", "nombre")],
                  "Y": [(mea("Eventos"), "Eventos")]},
                 "Eventos por categoría · profundice al tipo con ↓", orden=(mea("Eventos"), "Descending")))
vs.append(visual(p, 21, "lineChart", 550, 202, 710, 250,
                 {"Category": [MES], "Y": [(mea("Eventos críticos"), "Críticos"), (mea("Horas de operación aislada"), "Horas sin red")]},
                 "Evolución mensual", orden=(MES, "Ascending")))
vs.append(visual(p, 22, "tableEx", 550, 460, 710, 250,
                 {"Values": [(col("dim_tipo_evento", "nombre"), "Tipo"), (col("dim_inversor", "nombre"), "Inversor"),
                             (col("dim_fecha", "fecha"), "Fecha"), (col("dim_hora", "hora_texto"), "Hora"),
                             (col("fact_evento", "duracion_min"), "Minutos"),
                             (col("fact_evento", "valor_extremo"), "Valor extremo")]},
                 "Detalle de eventos", orden=(col("fact_evento", "duracion_min"), "Descending")))
paginas.append((p, "4 · Eventos", vs))

# 5 · Cargas y contexto -------------------------------------------------------------------
p = "cargas"
vs = encabezado(p, "¿Qué cargas explican el consumo? · Contexto",
                "Tareas registradas en las estaciones de trabajo, eventos de Windows y calendario del campus")
T = col("fact_actividad", "tipo_tarea")
vs.append(visual(p, 10, "clusteredBarChart", 20, 96, 620, 614,
                 {"Category": [T], "Y": [(mea("Tareas registradas"), "Registros")]},
                 "Registros de contexto por tipo", orden=(mea("Tareas registradas"), "Descending")))
vs.append(visual(p, 11, "clusteredBarChart", 650, 96, 610, 290,
                 {"Category": [T], "Y": [(mea("Carga promedio durante tareas (W)"), "Carga promedio (W)")]},
                 "Carga medida mientras dura cada tipo de tarea (W)",
                 orden=(mea("Carga promedio durante tareas (W)"), "Descending")))
vs.append(visual(p, 12, "clusteredColumnChart", 650, 392, 610, 318,
                 {"Category": [col("dim_hora", "franja")], "Y": [(mea("Tareas registradas"), "Registros")]},
                 "¿En qué franja ocurren?"))
paginas.append((p, "5 · Cargas (contexto)", vs))

# 6 · Económico ---------------------------------------------------------------------------
p = "economico"
vs = encabezado(p, "Indicador económico · escenario de tarifa (what-if)",
                "Tarifa base 930 COP/kWh (estimado estrato 4 EPM); mueva el control para simular otra tarifa")
sl = segmentador(p, 10, 20, 92, 300, 100, col("Tarifa", "Tarifa COP/kWh"), "Tarifa (COP/kWh)")
sl["visual"]["objects"]["selection"] = [{"properties": {"singleSelect": lit("true")}}]
vs.append(sl)
for k, (m_, n) in enumerate([("Costo de la red (COP)", "Costo de la red"), ("Ahorro por energía solar (COP)", "Ahorro solar"),
                             ("Tarifa seleccionada (COP/kWh)", "Tarifa usada")]):
    vs.append(tarjeta(p, 11 + k, 330 + k * 312, 92, m_, n, w=300, h=100))
vs.append(visual(p, 20, "lineChart", 20, 202, 620, 508,
                 {"Category": [MES], "Y": [(mea("Costo de la red acumulado (COP)"), "Costo acumulado")]},
                 "Costo de la red acumulado desde el inicio (COP)", orden=(MES, "Ascending")))
vs.append(visual(p, 21, "clusteredColumnChart", 650, 202, 610, 508,
                 {"Category": [MES], "Y": [(mea("Variación red/día vs mes anterior %"), "Variación vs mes anterior")]},
                 "Red por día con datos: variación frente al mes anterior", orden=(MES, "Ascending")))
paginas.append((p, "6 · Económico", vs))

# 7 · Calidad de datos --------------------------------------------------------------------
p = "calidad"
vs = encabezado(p, "Calidad y conciliación de datos",
                "Reglas del ETL (última corrida) y energía del ETL frente al contador del propio inversor")
for k, (m_, n) in enumerate([("Datos válidos %", "Datos válidos"), ("Disponibilidad del registro %", "Disponibilidad"),
                             ("Filas afectadas por reglas", "Filas afectadas"), ("Meses que concilian (±3 %) %", "Comparaciones dentro de ±3 %")]):
    vs.append(tarjeta(p, 10 + k, 20 + k * 312, 92, m_, n, w=300, h=100))
vs.append(visual(p, 20, "tableEx", 20, 202, 620, 508,
                 {"Values": [(col("Reglas de calidad", "orden"), "#"), (col("Reglas de calidad", "regla"), "Regla"), (col("Reglas de calidad", "descripcion"), "Descripción"),
                             (col("Reglas de calidad", "accion"), "Acción"), (col("Reglas de calidad", "filas_antes"), "Antes"),
                             (col("Reglas de calidad", "filas_despues"), "Después"),
                             (col("Reglas de calidad", "filas_afectadas"), "Afectadas")]},
                 "Reglas de calidad (ops.etl_regla)", orden=(col("Reglas de calidad", "orden"), "Ascending")))
vs.append(visual(p, 21, "tableEx", 650, 202, 610, 508,
                 {"Values": [(col("Conciliación contador", "mes"), "Mes"), (col("Conciliación contador", "inversor_id"), "Inv."),
                             (col("Conciliación contador", "variable"), "Variable"),
                             (col("Conciliación contador", "energia_contador_kwh"), "Contador kWh"),
                             (col("Conciliación contador", "energia_integrada_kwh"), "ETL kWh"),
                             (col("Conciliación contador", "diferencia_pct"), "Dif. %")]},
                 "Conciliación con el contador del inversor", orden=(col("Conciliación contador", "mes"), "Ascending")))
paginas.append((p, "7 · Calidad de datos", vs))

# Escritura -------------------------------------------------------------------------------
base = os.path.join(SALIDA, "pages")
os.makedirs(base, exist_ok=True)
for pid, nombre, vs in paginas:
    d = os.path.join(base, pid)
    os.makedirs(os.path.join(d, "visuals"), exist_ok=True)
    json.dump({"$schema": PG, "name": pid, "displayName": nombre, "displayOption": "FitToPage",
               "height": 760, "width": 1280}, open(os.path.join(d, "page.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    for v in vs:
        vd = os.path.join(d, "visuals", v["name"])
        os.makedirs(vd, exist_ok=True)
        json.dump(v, open(os.path.join(vd, "visual.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
json.dump({"$schema": PGS, "pageOrder": [p[0] for p in paginas], "activePageName": paginas[0][0]},
          open(os.path.join(base, "pages.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(sum(len(v) for _, _, v in paginas), "visuales en", len(paginas), "páginas")
