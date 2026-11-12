"""
Módulo de Procesamiento y Análisis Sintáctico (Parsers) de Insumos Curriculares.

Este módulo encapsula la lógica de extracción de texto y transformación sintáctica
desde fuentes no estructuradas y semiestructuradas (archivos LaTeX y JSON):
- Extracción de taxonomía ACM/IEEE CS2013/CC2020 (23 Áreas de Conocimiento).
- Extracción de 16 programas universitarios y 746 asignaturas con ground truth.
- Extracción y normalización de los 16 Perfiles de Egreso Declarados oficiales.
- Extracción de 200 vacantes del mercado laboral recopiladas en LinkedIn.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any


def clean_latex(text: str) -> str:
    """
    Limpia comandos, macros y caracteres de control sintácticos de código LaTeX.

    ¿Por qué existe?
    Los insumos curriculares y tablas de asignaturas provienen de documentos
    LaTeX compilados para la memoria y anexos técnicos. El texto crudo contiene
    comandos tipográficos (e.g. \\textbf, \\texttt, & para separador tabular,
    escapes de caracteres especiales como \\&, \\_, etc.) que introducirían
    ruido semántico en los modelos de lenguaje (SBERT) y en las consultas SQL.

    ¿Cómo funciona?
    1. Reemplaza entidades comunes (\\& -> 'y', \\_ -> '_').
    2. Elimina entornos estructurales (\\begin{...}, \\end{...}, \\item).
    3. Remueve macros con expresiones regulares preservando el argumento interior.
    4. Elimina llaves y barras invertidas residuales.
    5. Normaliza secuencias de espacios en blanco a un espacio simple.

    Args:
        text (str): Cadena de texto cruda con sintaxis LaTeX.

    Returns:
        str: Cadena limpia en texto plano UTF-8.
    """
    if not text:
        return ""
    # Reemplazar comandos de formato frecuentes
    t = text.replace(r"\&", " y ")
    t = t.replace(r"\_", "_")
    t = re.sub(r"\\begin\{[^\}]+\}|\\end\{[^\}]+\}|\\item", " ", t)
    t = re.sub(r"\\[a-zA-Z]+(\[[^\]]*\])?(\{([^}]*)\})?", r"\3", t)
    t = re.sub(r"[{}\\]", "", t)
    # Normalizar espacios en blanco
    return " ".join(t.split())


def cargar_perfiles_egreso(tex_path: Path) -> Dict[str, str]:
    """
    Extrae las fichas de perfiles de egreso oficiales desde el documento LaTeX.

    ¿Por qué existe?
    La tesis contrasta la promesa institucional declarada por cada universidad
    frente a la estructura práctica de sus mallas. Este método lee las 16 fichas
    institucionales declaradas en el documento oficial de corpus curricular.

    Reglas de negocio y consideraciones técnicas:
    - Cada ficha está delimitada por un entorno LaTeX `tcolorbox[fichaStyle]`.
    - Se extrae el ID de la universidad mediante la etiqueta `\\textbf{ID:}`.
    - Se maneja el caso de homonimia institucional: 'UAUTONOMA_16' se normaliza a 'UA_16'
      para mantener consistencia con la clave foránea de la tabla `programas`.
    - Se prioriza la sección 'Texto Oficial del Perfil de Egreso Declarado'.

    Args:
        tex_path (Path): Ruta al archivo LaTeX de corpus y perfiles de egreso.

    Returns:
        Dict[str, str]: Diccionario donde la llave es el código del programa (e.g. 'USACH_01')
        y el valor es el texto íntegro y limpio del perfil de egreso oficial.
    """
    print(f"-> Leyendo perfiles de egreso declarados oficiales desde {tex_path.name}...")
    with open(tex_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"\\begin\{tcolorbox\}\[fichaStyle,\s*title=\{([^}]+)\}\](.*?)\\end\{tcolorbox\}"
    fichas = re.findall(pattern, content, re.DOTALL)
    perfiles: Dict[str, str] = {}

    for title, body in fichas:
        id_m = re.search(r"\\textbf\{ID:\}\s*\\texttt\{([^}]+)\}", body)
        if not id_m:
            continue
        raw_id = id_m.group(1).replace(r"\_", "_").strip()
        # Normalizar ID de Universidad Autónoma para alinear con tabla de programas
        if raw_id == "UAUTONOMA_16":
            raw_id = "UA_16"

        # Extraer el texto oficial
        txt_m = re.search(r"\\textbf\{Texto Oficial del Perfil de Egreso Declarado:\}(.*)", body, re.DOTALL)
        if txt_m:
            texto_perfil = clean_latex(txt_m.group(1))
            perfiles[raw_id] = texto_perfil
        else:
            perfiles[raw_id] = clean_latex(body)

    print(f"   [OK] {len(perfiles)} perfiles de egreso extraídos correctamente.")
    return perfiles


def procesar_taxonomia_y_mallas(
    tex_path: Path, perfiles_dict: Dict[str, str]
) -> Tuple[List[Tuple[str, str, str, str]], List[Tuple[str, str]], List[Tuple[Any, ...]], List[Tuple[Any, ...]]]:
    """
    Parsea la taxonomía ACM, universidades, programas y las 746 asignaturas con Ground Truth.

    ¿Por qué existe?
    Constituye el núcleo de parsing de la memoria. Procesa las tablas `longtable`
    en LaTeX donde se encuentran:
    1. La taxonomía nacional unificada de 23 Áreas de Conocimiento ACM/IEEE (Tabla 3).
    2. El resumen tabular de los 16 programas universitarios chilenos (Tabla 1).
    3. Las 16 mallas curriculares completas (Tablas 4 a 19), donde cada fila representa
       una asignatura catalogada con su periodo y área ACM asignada por juicio experto.

    Decisiones técnicas:
    - Se valida que existan al menos 19 tablas `longtable` para garantizar integridad del insumo.
    - Se filtran filas auxiliares y cabeceras de repetición (`\\toprule`, `\\midrule`, `\\endhead`).
    - Se infiere el tipo de plan ('Civil', 'Ejecución', 'Profesional') y la duración semestral.
    - Se mapea cada nombre en español de área hacia su código canónico (e.g. 'AL', 'SE', 'IS').

    Args:
        tex_path (Path): Ruta al archivo LaTeX de mallas curriculares y taxonomía ACM.
        perfiles_dict (Dict[str, str]): Diccionario de perfiles oficiales para asociar a cada programa.

    Returns:
        Tuple:
            - taxonomia_list: Lista de tuplas (codigo, nombre_es, nombre_en, alcance_tematico).
            - universidades_list: Lista de tuplas (id, nombre).
            - programas_list: Lista de tuplas (id, uni_id, nombre_carrera, tipo_plan, duracion, num_asig, perfil_texto).
            - asignaturas_list: Lista de tuplas (prog_id, periodo, nombre, clasif_raw, codigo_acm).
    """
    print(f"-> Procesando clasificación ACM, programas y mallas curriculares desde {tex_path.name}...")
    with open(tex_path, "r", encoding="utf-8") as f:
        content = f.read().replace(r"\&", " y ")

    tables = re.findall(r"\\begin\{longtable\}\{([^}]+)\}(.*?)\\end\{longtable\}", content, re.DOTALL)
    if len(tables) < 19:
        raise ValueError(f"Se esperaban al menos 19 tablas en {tex_path}, encontradas: {len(tables)}")

    # 1. Taxonomía de 23 Áreas (Tabla 3, índice 2)
    tax_table = tables[2][1]
    if "\\endlastfoot" in tax_table:
        tax_table = tax_table.split("\\endlastfoot", 1)[1]

    taxonomia_list = []
    nombre_es_to_code = {}

    for line in tax_table.split(r"\\"):
        parts = [p.strip() for p in line.split("&")]
        if len(parts) >= 4:
            raw_code = re.sub(r"[{}\\\s]|textbf", "", parts[0]).strip()
            code_match = re.search(r"[A-Z]{2,4}", raw_code)
            if not code_match:
                continue
            code = code_match.group(0)

            es_name = clean_latex(parts[1]).upper()
            en_name = clean_latex(parts[2])
            scope = clean_latex(parts[3])

            if code and es_name and "CÓD" not in code and "ÁREA" not in es_name:
                taxonomia_list.append((code, es_name, en_name, scope))
                nombre_es_to_code[es_name] = code

    print(f"   [OK] {len(taxonomia_list)} áreas de la taxonomía ACM unificada catalogadas.")

    # 2. Resumen de Programas (Tabla 1, índice 0)
    prog_table = tables[0][1]
    if "\\endlastfoot" in prog_table:
        prog_table = prog_table.split("\\endlastfoot", 1)[1]

    programas_list = []
    universidades_set = {}
    id_a_orden = []

    for line in prog_table.split(r"\\"):
        parts = [p.strip() for p in line.split("&")]
        if len(parts) >= 5:
            raw_id = re.sub(r"[{}\\\s]|texttt", "", parts[0]).replace("_", "_").strip()
            # filtrar cabeceras
            if any(ign in raw_id.upper() for ign in ["ID", "TOPRULE", "MIDRULE", "ENDHEAD"]):
                match_id = re.search(r"[A-Z0-9]+_[0-9]{2}", raw_id)
                if match_id:
                    raw_id = match_id.group(0)
                else:
                    continue

            uni_nombre = clean_latex(parts[1])
            carrera_nombre = clean_latex(parts[2])
            regimen = clean_latex(parts[3])
            num_asig_raw = re.sub(r"[^\d]", "", parts[4])
            num_asig = int(num_asig_raw) if num_asig_raw else 0

            # Derivar tipo de plan y duración
            tipo_plan = "Civil" if "Civil" in carrera_nombre or "Civil" in regimen else ("Ejecución" if "Ejecución" in carrera_nombre or "Ejecución" in regimen else "Profesional")
            semestres_m = re.search(r"(\d+)\s*Semestres", regimen, re.IGNORECASE)
            duracion_sem = int(semestres_m.group(1)) if semestres_m else (11 if tipo_plan == "Civil" else (8 if tipo_plan == "Ejecución" else 8))

            # ID Universidad base (ej: USACH, UCHILE, etc.)
            uni_id = raw_id.split("_")[0]
            universidades_set[uni_id] = uni_nombre

            # Perfil oficial
            perfil_texto = perfiles_dict.get(raw_id, perfiles_dict.get("UAUTONOMA_16" if raw_id == "UA_16" else raw_id, ""))

            programas_list.append((raw_id, uni_id, carrera_nombre, tipo_plan, duracion_sem, num_asig, perfil_texto))
            id_a_orden.append(raw_id)

    print(f"   [OK] {len(universidades_set)} universidades y {len(programas_list)} programas catalogados.")

    # 3. Asignaturas de las 16 Mallas (Tablas 4 a 19, índices 3 a 18)
    asignaturas_list = []
    for idx in range(3, 19):
        prog_id = id_a_orden[idx - 3]
        content_table = tables[idx][1]
        if "\\endlastfoot" in content_table:
            content_table = content_table.split("\\endlastfoot", 1)[1]

        lines = content_table.split(r"\\")
        for line in lines:
            line_str = line.strip()
            if not line_str or any(ign in line_str for ign in ["\\caption", "\\toprule", "\\midrule", "\\bottomrule", "\\endfirsthead", "\\endhead", "\\endfoot", "Continuación", "Continúa en la siguiente"]):
                continue

            parts = [p.strip() for p in line_str.split("&")]
            if len(parts) >= 3:
                periodo = clean_latex(parts[0])
                nombre = clean_latex(parts[1])
                clasif_raw = clean_latex(parts[2]).upper()

                if not periodo or not nombre or not clasif_raw or "ASIGNATURA" in nombre.upper():
                    continue

                # Mapear al código canónico
                code_acm = nombre_es_to_code.get(clasif_raw, None)
                if not code_acm:
                    print(f"      [ALERTA] Sin mapeo ACM para: '{clasif_raw}' en {prog_id} - {nombre}")

                asignaturas_list.append((prog_id, periodo, nombre, clasif_raw, code_acm))

    print(f"   [OK] {len(asignaturas_list)} asignaturas con Ground Truth procesadas (esperadas: 746).")

    return taxonomia_list, list(universidades_set.items()), programas_list, asignaturas_list


def cargar_ofertas_laborales(json_path: Path) -> List[Tuple[Any, ...]]:
    """
    Carga y normaliza las 200 vacantes del mercado laboral recopiladas en LinkedIn.

    ¿Por qué existe?
    Para calcular la alineación curricular con la industria tecnológica y
    productiva chilena, el pipeline integra un corpus estratificado de 200 ofertas
    (100 sector TI y 100 sectores no TI).

    Decisiones técnicas:
    - Normaliza la lista de requisitos técnicos como una cadena separada por comas.
    - Asegura que ningún campo contenga valores nulos (None) que violen restricciones NOT NULL.

    Args:
        json_path (Path): Ruta al archivo JSON con el corpus consolidado de ofertas.

    Returns:
        List[Tuple[Any, ...]]: Lista de tuplas preparada para inserción masiva en la tabla ofertas_laborales.
    """
    print(f"-> Leyendo ofertas laborales consolidadas de LinkedIn desde {json_path.name}...")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    ofertas_list = []
    for ofe in data:
        req_tech = ofe.get("requisitos_tecnicos", [])
        if isinstance(req_tech, list):
            req_str = ", ".join(str(r) for r in req_tech)
        else:
            req_str = str(req_tech)

        ofertas_list.append((
            str(ofe.get("id", "")),
            str(ofe.get("titulo", "")),
            str(ofe.get("empresa", "")),
            str(ofe.get("sector", "")),
            str(ofe.get("subsector", "")),
            str(ofe.get("rol_categoria", "")),
            str(ofe.get("ubicacion", "")),
            str(ofe.get("modalidad", "")),
            str(ofe.get("nivel_experiencia", "")),
            req_str,
            str(ofe.get("url", "")),
            str(ofe.get("descripcion_completa", "")),
            str(ofe.get("fecha_recoleccion", ""))
        ))

    print(f"   [OK] {len(ofertas_list)} ofertas laborales cargadas.")
    return ofertas_list
