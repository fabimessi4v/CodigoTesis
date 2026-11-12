"""
Pipeline de Ingesta, Transformación y Carga (ETL) para la Base de Datos Curricular.

Proyecto de Tesis:
"Método computacional basado en procesamiento de lenguaje natural para analizar la
alineación curricular de Ingeniería Informática en Chile con estándares ACM/IEEE y
necesidades de la industria"
Autor: Fabián Ibarra Norambuena (USACH)

Flujo del Pipeline:
1. Extracción de 16 perfiles de egreso oficiales desde LaTeX.
2. Extracción de taxonomía ACM (23 KAs), 16 programas y 746 asignaturas curriculares.
3. Carga y validación de 200 ofertas laborales consolidadas de LinkedIn.
4. Creación y recreación del esquema SQLite relacional con integridad referencial activa.
5. Inserción transaccional masiva (executemany) en tablas normalizadas.
6. Verificación de integridad de claves foráneas y auditoría de conteos.
"""

import sys
import sqlite3
from pathlib import Path
from typing import Optional

from config.settings import (
    DB_PATH,
    SCHEMA_PATH,
    ACM_TEX_PATH,
    PERFILES_TEX_PATH,
    LINKEDIN_JSON_PATH,
)
from src.etl.parsers import (
    cargar_perfiles_egreso,
    procesar_taxonomia_y_mallas,
    cargar_ofertas_laborales,
)


def poblar_base_datos(
    db_path: Optional[Path] = None,
    schema_path: Optional[Path] = None,
    acm_path: Optional[Path] = None,
    perfiles_path: Optional[Path] = None,
    linkedin_path: Optional[Path] = None,
) -> bool:
    """
    Ejecuta el pipeline completo de inicialización y carga de la base de datos curricular.

    ¿Por qué existe?
    Garantiza reproducibilidad determinista: ante cualquier cambio en los documentos
    LaTeX de mallas o en las ofertas recolectadas, este procedimiento recrea la base de
    datos desde cero, auditando la consistencia relacional y asegurando que no existan
    datos huérfanos o desalineados.

    ¿Cómo funciona?
    1. Resuelve las rutas utilizando los valores por defecto de config.settings o los provistos.
    2. Ejecuta los parsers sintácticos en memoria.
    3. Reinicia la base de datos SQLite y aplica el script DDL de schema.sql.
    4. Inserta en bloque los registros respetando el orden de dependencias referenciales:
       taxonomia_acm -> universidades -> programas -> asignaturas -> ofertas_laborales.
    5. Ejecuta PRAGMA foreign_key_check y conteos por tabla para certificar la integridad.

    Args:
        db_path (Optional[Path]): Ruta de destino para el archivo SQLite.
        schema_path (Optional[Path]): Ruta al archivo DDL SQL.
        acm_path (Optional[Path]): Ruta al archivo LaTeX con mallas y taxonomía ACM.
        perfiles_path (Optional[Path]): Ruta al archivo LaTeX de perfiles de egreso.
        linkedin_path (Optional[Path]): Ruta al JSON consolidado de ofertas laborales.

    Returns:
        bool: True si el proceso culminó con éxito y sin errores de integridad.
    """
    target_db = db_path or DB_PATH
    target_schema = schema_path or SCHEMA_PATH
    target_acm = acm_path or ACM_TEX_PATH
    target_perfiles = perfiles_path or PERFILES_TEX_PATH
    target_linkedin = linkedin_path or LINKEDIN_JSON_PATH

    print("=" * 70)
    print("INICIO DE INGESTA ETL: BASE DE DATOS DE ANÁLISIS CURRICULAR")
    print(f"Destino DB: {target_db}")
    print("=" * 70)

    # 1. Cargar insumos utilizando el módulo de parsers
    perfiles_dict = cargar_perfiles_egreso(target_perfiles)
    taxonomia_list, universidades_list, programas_list, asignaturas_list = procesar_taxonomia_y_mallas(
        target_acm, perfiles_dict
    )
    ofertas_list = cargar_ofertas_laborales(target_linkedin)

    # 2. Inicializar base de datos SQLite con el esquema SQL
    print("\n-> Inicializando esquema de base de datos...")
    if target_db.exists():
        target_db.unlink()

    # Asegurar que el directorio contenedor exista
    target_db.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(target_db)
    cursor = conn.cursor()

    # Activar enforcement de llaves foráneas en SQLite
    cursor.execute("PRAGMA foreign_keys = ON;")

    with open(target_schema, "r", encoding="utf-8") as f:
        cursor.executescript(f.read())
    conn.commit()
    print("   [OK] Tablas e índices creados exitosamente.")

    # 3. Inserciones transaccionales por tabla
    print("\n-> Insertando datos...")

    # Taxonomía ACM (23 KAs unificadas)
    cursor.executemany(
        "INSERT INTO taxonomia_acm (codigo, nombre_es, nombre_en, alcance_tematico) VALUES (?, ?, ?, ?);",
        taxonomia_list,
    )

    # Universidades (16 instituciones)
    cursor.executemany(
        "INSERT INTO universidades (id, nombre) VALUES (?, ?);",
        universidades_list,
    )

    # Programas (16 programas académicos con perfiles oficiales asociados)
    cursor.executemany(
        """INSERT INTO programas 
           (id, universidad_id, nombre_carrera, tipo_plan, duracion_semestres, num_asignaturas_declaradas, perfil_egreso_oficial) 
           VALUES (?, ?, ?, ?, ?, ?, ?);""",
        programas_list,
    )

    # Asignaturas (746 asignaturas etiquetadas con Ground Truth ACM)
    cursor.executemany(
        """INSERT INTO asignaturas 
           (programa_id, periodo, nombre, clasificacion_acm_raw, codigo_acm) 
           VALUES (?, ?, ?, ?, ?);""",
        asignaturas_list,
    )

    # Ofertas Laborales (200 vacantes estratificadas de LinkedIn)
    cursor.executemany(
        """INSERT INTO ofertas_laborales 
           (id, titulo, empresa, sector, subsector, rol_categoria, ubicacion, modalidad, nivel_experiencia, requisitos_tecnicos, url, descripcion_completa, fecha_recoleccion) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
        ofertas_list,
    )

    conn.commit()

    # 4. Verificación y Auditoría de Integridad
    print("\n-> Auditoría de Integridad Referencial y Conteos:")
    cursor.execute("PRAGMA foreign_key_check;")
    fk_errors = cursor.fetchall()
    if fk_errors:
        print(f"   [ERROR CRÍTICO] Errores de claves foráneas detectados: {fk_errors}")
        conn.close()
        return False

    print("   [OK] Integridad referencial (Foreign Keys): 0 errores.")

    tablas = ["taxonomia_acm", "universidades", "programas", "asignaturas", "ofertas_laborales"]
    print("\n" + "-" * 45)
    print(f"{'Tabla':<25} | {'Registros':>15}")
    print("-" * 45)
    total_filas = 0
    for tbl in tablas:
        cursor.execute(f"SELECT COUNT(*) FROM {tbl};")
        count = cursor.fetchone()[0]
        total_filas += count
        print(f"{tbl:<25} | {count:>15,}")
    print("-" * 45)
    print(f"{'TOTAL REGISTROS CONSOLIDADOS':<25} | {total_filas:>15,}")
    print("-" * 45)

    # Verificar asignaturas sin código ACM
    cursor.execute("SELECT COUNT(*) FROM asignaturas WHERE codigo_acm IS NULL;")
    sin_acm = cursor.fetchone()[0]
    print(f"\n-> Asignaturas sin código ACM: {sin_acm} / {len(asignaturas_list)}")

    conn.close()
    print("\n[ÉXITO] Pipeline ETL completado con éxito. Base de datos lista para modelado.")
    return True


if __name__ == "__main__":
    exito = poblar_base_datos()
    sys.exit(0 if exito else 1)
