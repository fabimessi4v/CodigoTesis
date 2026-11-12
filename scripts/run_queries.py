#!/usr/bin/env python3
"""
Punto de Entrada CLI: Consultas Analíticas y Verificación Curricular.

Proyecto de Tesis:
"Método computacional basado en procesamiento de lenguaje natural para analizar la
alineación curricular de Ingeniería Informática en Chile con estándares ACM/IEEE y
necesidades de la industria"
Autor: Fabián Ibarra Norambuena (USACH)

Propósito:
Demuestra consultas SQL analíticas directamente sobre `tesis_curricular.db`
y expone la estructura de extracción de datos para las fases subsiguientes
de generación de Embeddings SBERT y Clustering Curricular.

Uso:
    python3 scripts/run_queries.py
"""

import sys
from pathlib import Path

# Asegurar disponibilidad de imports desde la raíz del proyecto
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.connection import get_connection
from config.settings import DB_PATH


def ejecutar_consultas() -> None:
    """
    Ejecuta el set de consultas analíticas de auditoría y extracción.

    Consultas ejecutadas:
    1. Consolidación de programas académicos, universidades y extensión de perfiles.
    2. Áreas de Conocimiento ACM/IEEE (Top 10 KAs) más prevalentes en mallas chilenas.
    3. Distribución estratificada de vacantes de LinkedIn según sector y modalidad.
    4. Muestreo de entidades de texto unificadas para proyección en SBERT.
    """
    if not DB_PATH.exists():
        print(f"❌ Base de datos no encontrada en: {DB_PATH}")
        print("Por favor, ejecuta primero: python3 scripts/run_etl.py")
        sys.exit(1)

    conn = get_connection(DB_PATH)
    cursor = conn.cursor()

    print("=" * 75)
    print("CONSULTAS ANALÍTICAS - BASE DE DATOS DE ANÁLISIS CURRICULAR")
    print(f"Fuente: {DB_PATH}")
    print("=" * 75)

    # -------------------------------------------------------------------------
    # Consulta 1: Resumen de programas y volumen de asignaturas
    # -------------------------------------------------------------------------
    print("\n1. PROGRAMAS CATALOGADOS Y VOLUMEN DE ASIGNATURAS:")
    print("-" * 75)
    query_programas = """
    SELECT 
        p.id AS programa_id,
        u.nombre AS universidad,
        p.nombre_carrera,
        p.tipo_plan,
        p.duracion_semestres,
        COUNT(a.id) AS total_asignaturas_malla,
        LENGTH(p.perfil_egreso_oficial) AS largo_perfil_caracteres
    FROM programas p
    JOIN universidades u ON p.universidad_id = u.id
    LEFT JOIN asignaturas a ON p.id = a.programa_id
    GROUP BY p.id
    ORDER BY p.id;
    """
    cursor.execute(query_programas)
    for row in cursor.fetchall():
        print(
            f"[{row['programa_id']}] {row['universidad']} - {row['nombre_carrera']} ({row['tipo_plan']}) "
            f"| {row['total_asignaturas_malla']} asig. | Perfil: {row['largo_perfil_caracteres']} chars"
        )

    # -------------------------------------------------------------------------
    # Consulta 2: Top 10 Áreas ACM más frecuentes en todo el país
    # -------------------------------------------------------------------------
    print("\n2. TOP 10 ÁREAS ACM/IEEE CON MAYOR PRESENCIA EN MALLAS NACIONALES:")
    print("-" * 75)
    query_top_acm = """
    SELECT 
        t.codigo,
        t.nombre_es,
        COUNT(a.id) AS num_asignaturas,
        ROUND(COUNT(a.id) * 100.0 / (SELECT COUNT(*) FROM asignaturas), 2) AS porcentaje_global
    FROM taxonomia_acm t
    JOIN asignaturas a ON t.codigo = a.codigo_acm
    GROUP BY t.codigo
    ORDER BY num_asignaturas DESC
    LIMIT 10;
    """
    cursor.execute(query_top_acm)
    for idx, row in enumerate(cursor.fetchall(), 1):
        print(
            f"{idx:2d}. [{row['codigo']}] {row['nombre_es']:<45} : "
            f"{row['num_asignaturas']:3d} asig. ({row['porcentaje_global']}%)"
        )

    # -------------------------------------------------------------------------
    # Consulta 3: Distribución del Mercado Laboral por Sector y Modalidad
    # -------------------------------------------------------------------------
    print("\n3. DISTRIBUCIÓN DEL MERCADO LABORAL LINKEDIN POR SECTOR Y MODALIDAD:")
    print("-" * 75)
    query_ofertas = """
    SELECT 
        COALESCE(sector, 'Sin clasificar') AS sector,
        COALESCE(modalidad, 'Sin clasificar') AS modalidad,
        COUNT(*) AS total_vacantes
    FROM ofertas_laborales
    GROUP BY sector, modalidad
    ORDER BY sector, total_vacantes DESC;
    """
    cursor.execute(query_ofertas)
    for row in cursor.fetchall():
        print(
            f"Sector: {row['sector']:<25} | Modalidad: {row['modalidad']:<20} | {row['total_vacantes']:3d} vacantes"
        )

    # -------------------------------------------------------------------------
    # Consulta 4: Muestra para proyección en espacio vectorial SBERT
    # -------------------------------------------------------------------------
    print("\n4. EJEMPLO DE EXTRACCIÓN DE TEXTOS PARA EMBEDDINGS (SBERT):")
    print("-" * 75)
    cursor.execute("SELECT id, nombre, clasificacion_acm_raw FROM asignaturas LIMIT 3;")
    print("-> Muestra de Asignaturas:")
    for row in cursor.fetchall():
        print(f"   [ID {row['id']}] {row['nombre']} -> Ground Truth: {row['clasificacion_acm_raw']}")

    cursor.execute(
        "SELECT id, titulo, empresa, SUBSTR(descripcion_completa, 1, 90) AS snippet FROM ofertas_laborales LIMIT 2;"
    )
    print("\n-> Muestra de Ofertas Laborales:")
    for row in cursor.fetchall():
        print(f"   [{row['id']}] {row['titulo']} en {row['empresa']}: {row['snippet']}...")

    conn.close()
    print("\n" + "=" * 75)


if __name__ == "__main__":
    ejecutar_consultas()
