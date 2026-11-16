"""Da formato institucional al .docx que pandoc genera a partir de informe.html.

    cd docs/informe
    python construir_informe.py                       # genera informe.html (y el PDF web)
    pandoc informe.html -f html -t docx --resource-path=. -o _build/base.docx   (sin la <section class="portada">)
    python formato_word.py _build/base.docx plantilla_word/encabezado.xml plantilla_word/banner_pascual.png BI_Taller6_Lopez_Cardona.docx

- Portada nueva (estilo del informe de auditoría) con el enlace de GitHub.
- Cada sección principal (Heading 1) empieza en página nueva y el contenido fluye debajo.
- Encabezado institucional (banner Pascual Bravo) y pie con número de página.
- Estilos: Arial, tablas con bordes, bloques de evidencia en Consolas con ajuste de línea.
"""
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

base, encabezado, banner, salida = sys.argv[1:5]
tmp = Path(tempfile.mkdtemp())
with zipfile.ZipFile(base) as z:
    z.extractall(tmp)
W = tmp / "word"

REPO = "https://github.com/Cat0428/solarbi-lopez-cardona"
AZUL = "1F3864"

# ---------------------------------------------------------------- estilos
st = (W / "styles.xml").read_text(encoding="utf-8")
st = re.sub(r"<w:rPrDefault>.*?</w:rPrDefault>",
            '<w:rPrDefault><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:eastAsia="Arial" w:cs="Arial"/>'
            '<w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:val="es-CO" w:eastAsia="en-US" w:bidi="ar-SA"/>'
            '</w:rPr></w:rPrDefault>', st, flags=re.S)
st = re.sub(r"<w:pPrDefault>.*?</w:pPrDefault>",
            '<w:pPrDefault><w:pPr><w:spacing w:after="100" w:line="264" w:lineRule="auto"/></w:pPr></w:pPrDefault>',
            st, flags=re.S)

def estilo(sid, xml):
    global st
    patron = r'<w:style [^>]*w:styleId="%s"[^>]*>.*?</w:style>' % sid
    if re.search(patron, st, flags=re.S):
        st = re.sub(patron, lambda m: xml, st, count=1, flags=re.S)
    else:
        st = st.replace("</w:styles>", xml + "</w:styles>")

def h(n, tam, antes, despues, extra_ppr="", extra_rpr=""):
    return (f'<w:style w:type="paragraph" w:styleId="Heading{n}"><w:name w:val="heading {n}"/>'
            f'<w:basedOn w:val="Normal"/><w:next w:val="BodyText"/><w:uiPriority w:val="9"/><w:qFormat/>'
            f'<w:pPr><w:keepNext/><w:keepLines/>{extra_ppr}<w:spacing w:before="{antes}" w:after="{despues}"/>'
            f'<w:outlineLvl w:val="{n-1}"/></w:pPr>'
            f'<w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/><w:b/><w:bCs/>'
            f'<w:color w:val="000000"/><w:sz w:val="{tam}"/><w:szCs w:val="{tam}"/>{extra_rpr}</w:rPr></w:style>')

estilo("Heading1", h(1, 30, 0, 200,
       '<w:pageBreakBefore/><w:pBdr><w:bottom w:val="single" w:sz="12" w:space="4" w:color="000000"/></w:pBdr>'))
estilo("Heading2", h(2, 24, 240, 100))
estilo("Heading3", h(3, 21, 180, 80))
estilo("Normal", '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>')
estilo("BodyText", '<w:style w:type="paragraph" w:styleId="BodyText"><w:name w:val="Body Text"/><w:basedOn w:val="Normal"/>'
       '<w:qFormat/><w:pPr><w:spacing w:before="80" w:after="120"/><w:jc w:val="both"/></w:pPr></w:style>')
estilo("FirstParagraph", '<w:style w:type="paragraph" w:customStyle="1" w:styleId="FirstParagraph"><w:name w:val="First Paragraph"/>'
       '<w:basedOn w:val="BodyText"/><w:next w:val="BodyText"/><w:qFormat/></w:style>')
estilo("Compact", '<w:style w:type="paragraph" w:customStyle="1" w:styleId="Compact"><w:name w:val="Compact"/>'
       '<w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:before="30" w:after="30" w:line="240" w:lineRule="auto"/></w:pPr></w:style>')
estilo("SourceCode", '<w:style w:type="paragraph" w:customStyle="1" w:styleId="SourceCode"><w:name w:val="Source Code"/>'
       '<w:basedOn w:val="Normal"/><w:pPr><w:pBdr><w:top w:val="single" w:sz="4" w:space="3" w:color="BFBFBF"/>'
       '<w:left w:val="single" w:sz="18" w:space="4" w:color="1F3864"/><w:bottom w:val="single" w:sz="4" w:space="3" w:color="BFBFBF"/>'
       '<w:right w:val="single" w:sz="4" w:space="4" w:color="BFBFBF"/></w:pBdr><w:shd w:val="clear" w:color="auto" w:fill="F4F5F7"/>'
       '<w:spacing w:before="0" w:after="160" w:line="216" w:lineRule="auto"/><w:ind w:left="60" w:right="60"/></w:pPr>'
       '<w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/><w:sz w:val="13"/><w:szCs w:val="13"/></w:rPr></w:style>')
estilo("Consola", '<w:style w:type="paragraph" w:customStyle="1" w:styleId="Consola"><w:name w:val="Consola"/>'
       '<w:basedOn w:val="Normal"/><w:pPr><w:shd w:val="clear" w:color="auto" w:fill="0F1720"/>'
       '<w:spacing w:before="0" w:after="160" w:line="216" w:lineRule="auto"/><w:ind w:left="60" w:right="60"/></w:pPr>'
       '<w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/><w:color w:val="DFE7EF"/>'
       '<w:sz w:val="13"/><w:szCs w:val="13"/></w:rPr></w:style>')
estilo("VerbatimChar", '<w:style w:type="character" w:customStyle="1" w:styleId="VerbatimChar"><w:name w:val="Verbatim Char"/>'
       '<w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/><w:color w:val="1F3864"/><w:sz w:val="18"/></w:rPr></w:style>')
estilo("CaptionedFigure", '<w:style w:type="paragraph" w:customStyle="1" w:styleId="CaptionedFigure"><w:name w:val="Captioned Figure"/>'
       '<w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="120" w:after="40"/><w:jc w:val="center"/></w:pPr></w:style>')
estilo("ImageCaption", '<w:style w:type="paragraph" w:customStyle="1" w:styleId="ImageCaption"><w:name w:val="Image Caption"/>'
       '<w:basedOn w:val="Normal"/><w:pPr><w:spacing w:before="0" w:after="200"/><w:jc w:val="center"/></w:pPr>'
       '<w:rPr><w:i/><w:color w:val="595959"/><w:sz w:val="17"/></w:rPr></w:style>')
estilo("Hyperlink", '<w:style w:type="character" w:styleId="Hyperlink"><w:name w:val="Hyperlink"/>'
       '<w:rPr><w:color w:val="0563C1"/><w:u w:val="single"/></w:rPr></w:style>')
estilo("EvidenciaTitulo", '<w:style w:type="paragraph" w:customStyle="1" w:styleId="EvidenciaTitulo"><w:name w:val="Evidencia titulo"/>'
       '<w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:shd w:val="clear" w:color="auto" w:fill="263445"/>'
       '<w:spacing w:before="120" w:after="0"/><w:ind w:left="60" w:right="60"/></w:pPr>'
       '<w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/><w:color w:val="FFFFFF"/><w:sz w:val="16"/></w:rPr></w:style>')
estilo("Table", '<w:style w:type="table" w:default="1" w:styleId="Table"><w:name w:val="Table"/><w:basedOn w:val="TableNormal"/>'
       '<w:qFormat/><w:pPr><w:spacing w:before="20" w:after="20" w:line="240" w:lineRule="auto"/><w:jc w:val="left"/></w:pPr>'
       '<w:rPr><w:sz w:val="16"/><w:szCs w:val="16"/></w:rPr>'
       '<w:tblPr><w:tblBorders><w:top w:val="single" w:sz="4" w:space="0" w:color="A6A6A6"/>'
       '<w:left w:val="single" w:sz="4" w:space="0" w:color="A6A6A6"/><w:bottom w:val="single" w:sz="4" w:space="0" w:color="A6A6A6"/>'
       '<w:right w:val="single" w:sz="4" w:space="0" w:color="A6A6A6"/><w:insideH w:val="single" w:sz="4" w:space="0" w:color="A6A6A6"/>'
       '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="A6A6A6"/></w:tblBorders>'
       '<w:tblCellMar><w:top w:w="40" w:type="dxa"/><w:left w:w="80" w:type="dxa"/><w:bottom w:w="40" w:type="dxa"/>'
       '<w:right w:w="80" w:type="dxa"/></w:tblCellMar></w:tblPr>'
       '<w:tblStylePr w:type="firstRow"><w:rPr><w:b/><w:color w:val="FFFFFF"/></w:rPr>'
       '<w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="1F3864"/></w:tcPr></w:tblStylePr></w:style>')
# Estilo AbstractTitle de pandoc: viene mal formado y no se usa
st = re.sub(r'<w:style [^>]*w:styleId="AbstractTitle"[^>]*>.*?</w:style>', "", st, flags=re.S)
(W / "styles.xml").write_text(st, encoding="utf-8")

# ---------------------------------------------------------------- documento
doc = (W / "document.xml").read_text(encoding="utf-8")

# Título de metadatos de pandoc: sobra (la portada lo reemplaza)
doc = re.sub(r'<w:p>(?:(?!</w:p>).)*?<w:pStyle w:val="Title" />.*?</w:p>', "", doc, count=1, flags=re.S)

# Títulos de los bloques de evidencia: el párrafo justo antes de cada bloque de código
doc = re.sub(r'<w:p>(<w:pPr><w:pStyle w:val="(?:BodyText|FirstParagraph)" /></w:pPr>)((?:(?!</w:p>).)*?)</w:p>'
             r'(?=<w:p><w:pPr><w:pStyle w:val="SourceCode" />)',
             lambda m: ('<w:p><w:pPr><w:pStyle w:val="EvidenciaTitulo" /></w:pPr>' + m.group(2) + '</w:p>')
             if len(re.sub(r"<[^>]+>", "", m.group(2))) < 140 and not re.sub(r"<[^>]+>", "", m.group(2)).rstrip().endswith(".")
             else m.group(0), doc, flags=re.S)
# El bloque que sigue a un título de evidencia es salida de consola: fondo negro
doc = re.sub(r'(<w:pStyle w:val="EvidenciaTitulo" /></w:pPr>(?:(?!</w:p>).)*?</w:p><w:p><w:pPr>)<w:pStyle w:val="SourceCode" />',
             r'\1<w:pStyle w:val="Consola" />', doc, flags=re.S)
# En la consola el texto va claro: se quita el estilo de código en línea (azul) de sus fragmentos
doc = re.sub(r'<w:p><w:pPr><w:pStyle w:val="Consola" />.*?</w:p>',
             lambda m: m.group(0).replace('<w:rStyle w:val="VerbatimChar" />', ''), doc, flags=re.S)
# Los bloques de código pueden partirse entre páginas, pero se ajustan al ancho
doc = doc.replace('<w:wordWrap w:val="off" />', "")

# Imágenes: hasta el ancho útil (17 cm) sin pasar 21 cm de alto
ANCHO, ALTO = 6120000, 7560000
def escalar(m):
    bloque = m.group(0)
    ext = re.search(r'<wp:extent cx="(\d+)" cy="(\d+)"', bloque)
    cx, cy = int(ext.group(1)), int(ext.group(2))
    f = min(ANCHO / cx, ALTO / cy) if cx >= 5300000 else min(1.0, ALTO / cy)
    nx, ny = int(cx * f), int(cy * f)
    bloque = re.sub(r'(<wp:extent) cx="\d+" cy="\d+"', rf'\1 cx="{nx}" cy="{ny}"', bloque)
    bloque = re.sub(r'(<a:ext) cx="\d+" cy="\d+"', rf'\1 cx="{nx}" cy="{ny}"', bloque)
    return bloque
doc = re.sub(r"<wp:inline.*?</wp:inline>", escalar, doc, flags=re.S)

# Tablas sin anchos propios (pandoc las reparte por igual): ancho según el contenido de cada columna
TOTAL = 9638
def texto(xml):
    return re.sub(r"<[^>]+>", "", xml)
def anchos(t):
    g = re.findall(r'<w:gridCol w:w="(\d+)" />', t)
    if not g or len(set(g)) != 1 or len(g) == 1:
        return t
    filas = re.findall(r"<w:tr>.*?</w:tr>", t, flags=re.S)
    n = len(g)
    peso = [0.0] * n
    for c in range(n):
        celdas = []
        for f in filas:
            tcs = re.findall(r"<w:tc>.*?</w:tc>", f, flags=re.S)
            if len(tcs) == n:
                celdas.append(texto(tcs[c]))
        if not celdas:
            return t
        prom = sum(min(len(x), 90) for x in celdas) / len(celdas)
        token = max((len(w) for x in celdas for w in x.split()), default=1)
        peso[c] = max(prom, min(token, 28) * 0.9, 4)
    tot = sum(peso)
    w = [max(700, int(TOTAL * p / tot)) for p in peso]
    w[-1] += TOTAL - sum(w)
    t = re.sub(r"<w:tblGrid>.*?</w:tblGrid>",
               "<w:tblGrid>" + "".join(f'<w:gridCol w:w="{x}" />' for x in w) + "</w:tblGrid>", t, count=1, flags=re.S)
    t = re.sub(r'<w:tblW w:type="pct" w:w="\d+" />', f'<w:tblW w:type="dxa" w:w="{TOTAL}" />', t, count=1)
    def fila(m):
        i = iter(range(10**6))
        return re.sub(r"<w:tcPr />", lambda _: f'<w:tcPr><w:tcW w:w="{w[next(i) % n]}" w:type="dxa" /></w:tcPr>', m.group(0))
    return re.sub(r"<w:tr>.*?</w:tr>", fila, t, flags=re.S)
doc = re.sub(r"<w:tbl>.*?</w:tbl>", lambda m: anchos(m.group(0)), doc, flags=re.S)

# Portada (mismo esquema que el informe de auditoría) + enlace al repositorio
def P(texto, tam=22, negrita=False, antes=0, despues=0, color="000000", cursiva=False):
    rpr = (f'<w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>{"<w:b/>" if negrita else ""}'
           f'{"<w:i/>" if cursiva else ""}<w:color w:val="{color}"/><w:sz w:val="{tam}"/><w:szCs w:val="{tam}"/>')
    return (f'<w:p><w:pPr><w:spacing w:before="{antes}" w:after="{despues}"/><w:jc w:val="center"/></w:pPr>'
            f'<w:r><w:rPr>{rpr}</w:rPr><w:t xml:space="preserve">{texto}</w:t></w:r></w:p>')

enlace = ('<w:p><w:pPr><w:spacing w:before="0" w:after="0"/><w:jc w:val="center"/></w:pPr>'
          '<w:hyperlink r:id="rIdRepoGitHub" w:history="1"><w:r><w:rPr><w:rStyle w:val="Hyperlink"/>'
          '<w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr>'
          f'<w:t>{REPO}</w:t></w:r></w:hyperlink></w:p>')
portada = "".join([
    P("INFORME TÉCNICO", 40, True, 1900, 200),
    P("Solución de BI contenerizada y orquestada con Docker y Kubernetes", 28, True, 0, 80),
    P("Monitoreo energético de una microrred híbrida (solar + batería + red) — OpenCEM v1.0.0", 24, False, 0, 600),
    P("Inteligencia de Negocios — Grupo 01 · Semestre 2026-II", 24, True, 0, 80),
    P("Taller 6 — Solución de BI contenerizada y orquestada", 24, False, 0, 600),
    P("Estudiante:", 22, True, 0, 40),
    P("Cristian David López Cardona", 22, False, 0, 400),
    P("Docente:", 22, True, 0, 40),
    P("Ramiro Grisales Montoya", 22, False, 0, 400),
    P("Repositorio en GitHub:", 22, True, 0, 40),
    enlace,
    P("(carpeta taller6/)", 18, False, 0, 1500, "595959"),
    P("Ingeniería en Desarrollo de Software", 22, False, 0, 80),
    P("Institución Universitaria Pascual Bravo", 22, True, 0, 800),
    P("Medellín, Colombia — Noviembre de 2026", 22, False, 0, 0),
])
doc = re.sub(r"(<w:body>)", r"\1" + portada.replace("\\", "\\\\"), doc, count=1)

# Página A4, márgenes para el banner, primera página sin pie de página
sect = ('<w:sectPr><w:headerReference w:type="default" r:id="rIdEncabezado"/>'
        '<w:headerReference w:type="first" r:id="rIdEncabezado"/>'
        '<w:footerReference w:type="default" r:id="rIdPie"/><w:footerReference w:type="first" r:id="rIdPieVacio"/>'
        '<w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="2200" w:right="1134" w:bottom="1134" w:left="1134" w:header="720" w:footer="500" w:gutter="0"/>'
        '<w:cols w:space="720"/><w:titlePg/></w:sectPr>')
doc = re.sub(r"<w:sectPr\s*/>|<w:sectPr>.*?</w:sectPr>", sect, doc, count=1, flags=re.S)
if 'xmlns:r="' not in doc[:3000]:
    doc = doc.replace("<w:document ", '<w:document xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" ', 1)
(W / "document.xml").write_text(doc, encoding="utf-8")

# ---------------------------------------------------------------- encabezado y pie
shutil.copy(encabezado, W / "header1.xml")
(W / "_rels").mkdir(exist_ok=True)
(W / "media").mkdir(exist_ok=True)
shutil.copy(banner, W / "media" / "banner_pascual.png")
(W / "_rels" / "header1.xml.rels").write_text(
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
    'Target="media/banner_pascual.png"/></Relationships>', encoding="utf-8")

NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"')
pie = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr {NS}><w:p><w:pPr>'
       '<w:pBdr><w:top w:val="single" w:sz="4" w:space="4" w:color="A6A6A6"/></w:pBdr>'
       '<w:tabs><w:tab w:val="right" w:pos="9638"/></w:tabs><w:spacing w:before="0" w:after="0"/></w:pPr>'
       '<w:r><w:rPr><w:color w:val="7F7F7F"/><w:sz w:val="16"/></w:rPr>'
       '<w:t xml:space="preserve">BI · Taller 6 · López Cardona · Inteligencia de Negocios 2026-II</w:t></w:r>'
       '<w:r><w:rPr><w:color w:val="7F7F7F"/><w:sz w:val="16"/></w:rPr><w:tab/><w:t xml:space="preserve">Página </w:t></w:r>'
       '<w:r><w:rPr><w:color w:val="7F7F7F"/><w:sz w:val="16"/></w:rPr><w:fldChar w:fldCharType="begin"/></w:r>'
       '<w:r><w:rPr><w:color w:val="7F7F7F"/><w:sz w:val="16"/></w:rPr><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
       '<w:r><w:rPr><w:color w:val="7F7F7F"/><w:sz w:val="16"/></w:rPr><w:fldChar w:fldCharType="separate"/></w:r>'
       '<w:r><w:rPr><w:color w:val="7F7F7F"/><w:sz w:val="16"/></w:rPr><w:t>2</w:t></w:r>'
       '<w:r><w:rPr><w:color w:val="7F7F7F"/><w:sz w:val="16"/></w:rPr><w:fldChar w:fldCharType="end"/></w:r>'
       '</w:p></w:ftr>')
(W / "footer1.xml").write_text(pie, encoding="utf-8")
(W / "footer2.xml").write_text(
    f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr {NS}><w:p/></w:ftr>', encoding="utf-8")

rels = (W / "_rels" / "document.xml.rels").read_text(encoding="utf-8")
T = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
rels = rels.replace("</Relationships>",
    f'<Relationship Id="rIdEncabezado" Type="{T}header" Target="header1.xml"/>'
    f'<Relationship Id="rIdPie" Type="{T}footer" Target="footer1.xml"/>'
    f'<Relationship Id="rIdPieVacio" Type="{T}footer" Target="footer2.xml"/>'
    f'<Relationship Id="rIdRepoGitHub" Type="{T}hyperlink" Target="{REPO}" TargetMode="External"/>'
    "</Relationships>")
(W / "_rels" / "document.xml.rels").write_text(rels, encoding="utf-8")

ct = (tmp / "[Content_Types].xml").read_text(encoding="utf-8")
extra = ""
if 'Extension="png"' not in ct:
    extra += '<Default Extension="png" ContentType="image/png"/>'
if 'Extension="jpg"' not in ct:
    extra += '<Default Extension="jpg" ContentType="image/jpeg"/>'
extra += ('<Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>'
          '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>'
          '<Override PartName="/word/footer2.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>')
ct = ct.replace("</Types>", extra + "</Types>")
(tmp / "[Content_Types].xml").write_text(ct, encoding="utf-8")

# Propiedades del documento
core = tmp / "docProps" / "core.xml"
if core.exists():
    c = core.read_text(encoding="utf-8")
    c = re.sub(r"<dc:title>.*?</dc:title>", "<dc:title>BI Taller 6 · López Cardona</dc:title>", c)
    c = re.sub(r"<dc:creator>.*?</dc:creator>", "<dc:creator>Cristian David López Cardona</dc:creator>", c)
    core.write_text(c, encoding="utf-8")

# Empaquetar (archivos, sin entradas de carpeta)
salida = Path(salida)
if salida.exists():
    salida.unlink()
with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as z:
    ct_path = tmp / "[Content_Types].xml"
    z.write(ct_path, "[Content_Types].xml")
    for p in sorted(tmp.rglob("*")):
        if p.is_file() and p != ct_path:
            z.write(p, p.relative_to(tmp).as_posix())
print("ok", salida)
