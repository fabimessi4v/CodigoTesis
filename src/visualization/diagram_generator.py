#!/usr/bin/env python3
"""
Script definitivo para regenerar pipeline_arquitectura.svg y pipeline_arquitectura.pdf
- Soporta edición directa en pipeline_diagrama.mmd O en pipeline_diagrama_interactivo.html (usa el archivo más reciente).
- Calcula dinámicamente el tamaño del lienzo según el SVG para que NUNCA se corte ningún nodo ni columna.
- Aplica pdfcrop para un PDF limpio de 1 sola página recortada al borde.
"""

import os
import subprocess
import sys
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MMD_PATH = os.path.join(BASE_DIR, 'pipeline_diagrama.mmd')
HTML_PATH = os.path.join(BASE_DIR, 'pipeline_diagrama_interactivo.html')
SVG_OUTPUT = os.path.join(BASE_DIR, 'pipeline_arquitectura.svg')
PDF_OUTPUT = os.path.join(BASE_DIR, 'pipeline_arquitectura.pdf')
TMP_RENDER_HTML = '/tmp/render_pipeline_dynamic.html'
TMP_RAW_PDF = '/tmp/render_pipeline_dynamic_raw.pdf'

# 1. Determinar cuál archivo fue modificado más recientemente (HTML o MMD)
source_file = None
mermaid_code = ""

mtime_mmd = os.path.getmtime(MMD_PATH) if os.path.exists(MMD_PATH) else 0
mtime_html = os.path.getmtime(HTML_PATH) if os.path.exists(HTML_PATH) else 0

if mtime_html > mtime_mmd and os.path.exists(HTML_PATH):
    # El usuario editó el HTML más recientemente
    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        html_txt = f.read()
    match = re.search(r'full:\s*`([^`]+)`', html_txt)
    if match:
        mermaid_code = match.group(1).strip()
        source_file = "pipeline_diagrama_interactivo.html"
        # Sincronizar hacia pipeline_diagrama.mmd
        with open(MMD_PATH, 'w', encoding='utf-8') as f:
            f.write(mermaid_code + "\n")
        print(f"📖 Cambios detectados en: {source_file} -> Sincronizado a pipeline_diagrama.mmd")

if not mermaid_code and os.path.exists(MMD_PATH):
    with open(MMD_PATH, 'r', encoding='utf-8') as f:
        mermaid_code = f.read().strip()
    source_file = "pipeline_diagrama.mmd"
    print(f"📖 Leyendo código Mermaid desde: {source_file}")

if not mermaid_code:
    print("❌ Error: No se encontró código Mermaid en ningún archivo.")
    sys.exit(1)

# 2. Paso 1: Renderizar SVG primero para medir dimensiones exactas
tmp_svg_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
</head>
<body>
    <div id="container"></div>
    <script>
        const code = `{mermaid_code}`;
        mermaid.initialize({{
            startOnLoad: false,
            theme: 'default',
            securityLevel: 'loose',
            flowchart: {{ htmlLabels: true, curve: 'basis', useMaxWidth: false }}
        }});
        mermaid.render('diagram-svg', code).then(({{svg}}) => {{
            document.getElementById('container').innerHTML = svg;
        }});
    </script>
</body>
</html>"""

with open('/tmp/measure_svg.html', 'w', encoding='utf-8') as f:
    f.write(tmp_svg_html)

print("🎨 Extrayendo SVG y midiendo dimensiones...")
cmd_dump = [
    'google-chrome',
    '--headless',
    '--disable-gpu',
    '--no-sandbox',
    '--virtual-time-budget=7000',
    '--dump-dom',
    'file:///tmp/measure_svg.html'
]

res_dump = subprocess.run(cmd_dump, capture_output=True, text=True)
dom = res_dump.stdout

if '<svg' not in dom:
    print("❌ Error al renderizar SVG en Chrome. Revisa si hay errores de sintaxis en Mermaid.")
    sys.exit(1)

start_idx = dom.find('<svg')
end_idx = dom.find('</svg>') + 6
svg_data = dom[start_idx:end_idx]

# Guardar SVG
with open(SVG_OUTPUT, 'w', encoding='utf-8') as f:
    f.write(svg_data)

# 3. Extraer ancho y alto exactos del SVG
m_w = re.search(r'width=\"([\d\.]+)\"', svg_data)
m_h = re.search(r'height=\"([\d\.]+)\"', svg_data)
if m_w and m_h:
    svg_w = float(m_w.group(1))
    svg_h = float(m_h.group(1))
else:
    m_vb = re.search(r'viewBox=\"[\-\d\.]+\s+[\-\d\.]+\s+([\d\.]+)\s+([\d\.]+)\"', svg_data)
    if m_vb:
        svg_w = float(m_vb.group(1))
        svg_h = float(m_vb.group(2))
    else:
        svg_w = 3000.0
        svg_h = 2000.0

# Añadir holgura de 200px
canvas_w = int(svg_w + 200)
canvas_h = int(svg_h + 200)
print(f"📐 Dimensiones detectadas del diagrama: {svg_w:.1f}px de ancho x {svg_h:.1f}px de alto")
print(f"📐 Tamaño de lienzo ajustado para PDF: {canvas_w}px x {canvas_h}px")

# 4. Crear HTML de impresión adaptado a estas dimensiones exactas
print_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@page {{
    size: {canvas_w}px {canvas_h}px;
    margin: 0;
}}
html, body {{
    margin: 0;
    padding: 0;
    width: {canvas_w}px;
    height: {canvas_h}px;
    overflow: hidden;
    background: white;
}}
#wrapper {{
    width: {canvas_w}px;
    height: {canvas_h}px;
    display: flex;
    justify-content: center;
    align-items: center;
}}
</style>
</head>
<body>
<div id="wrapper">
{svg_data}
</div>
</body>
</html>"""

with open(TMP_RENDER_HTML, 'w', encoding='utf-8') as f:
    f.write(print_html)

# 5. Generar PDF crudo sin cortes
cmd_pdf = [
    'google-chrome',
    '--headless',
    '--disable-gpu',
    '--no-sandbox',
    f'--print-to-pdf={TMP_RAW_PDF}',
    '--run-all-compositor-stages-before-draw',
    '--virtual-time-budget=7000',
    f'file://{TMP_RENDER_HTML}'
]

subprocess.run(cmd_pdf, capture_output=True)

# 6. Recortar bordes vacíos exactamente con pdfcrop
if os.path.exists(TMP_RAW_PDF):
    cmd_crop = ['pdfcrop', TMP_RAW_PDF, PDF_OUTPUT]
    res_crop = subprocess.run(cmd_crop, capture_output=True, text=True)
    if res_crop.returncode == 0 and os.path.exists(PDF_OUTPUT):
        size_pdf = os.path.getsize(PDF_OUTPUT)
        print(f"✅ PDF generado exitosamente: {PDF_OUTPUT} ({size_pdf:,} bytes, 1 sola página completa)")
    else:
        os.replace(TMP_RAW_PDF, PDF_OUTPUT)
        print(f"✅ PDF generado (sin crop): {PDF_OUTPUT}")
else:
    print("❌ Error: No se pudo generar el PDF temporal.")
    sys.exit(1)

# 7. Sincronizar HTML si veníamos de MMD
if source_file == "pipeline_diagrama.mmd" and os.path.exists(HTML_PATH):
    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        html_txt = f.read()
    new_html = re.sub(
        r'(full:\s*`)[^`]+(`)',
        lambda m: m.group(1) + mermaid_code + m.group(2),
        html_txt
    )
    if new_html != html_txt:
        with open(HTML_PATH, 'w', encoding='utf-8') as f:
            f.write(new_html)
        print("🔄 pipeline_diagrama_interactivo.html sincronizado con pipeline_diagrama.mmd.")

print(f"✅ SVG actualizado: {SVG_OUTPUT} ({os.path.getsize(SVG_OUTPUT):,} bytes)")
print("\n🎉 ¡Listo! El PDF ahora contiene el 100% del diagrama sin ningún corte en los costados ni abajo.")
