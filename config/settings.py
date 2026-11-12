"""
Módulo de Configuración Global del Proyecto de Tesis.

Define las rutas canónicas del sistema, garantizando portabilidad absoluta
e independencia del directorio desde donde se ejecuten los scripts.
"""

from pathlib import Path

# Raíz absoluta del proyecto (directorio CodigoTesis)
BASE_DIR = Path(__file__).resolve().parent.parent

# Rutas del directorio de datos
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Insumos primarios (Raw Data)
ACM_TEX_PATH = RAW_DATA_DIR / "acm_curricula" / "Clasificacion_ACM_Mallas_Curriculares.tex"
PERFILES_TEX_PATH = RAW_DATA_DIR / "perfiles_egreso" / "Corpus_y_Perfiles_Egreso_16_Universidades.tex"
LINKEDIN_RAW_DIR = RAW_DATA_DIR / "linkedin"
LINKEDIN_SCHEMA_PATH = LINKEDIN_RAW_DIR / "schema_ofertas.json"
LINKEDIN_CSV_TEMPLATE = LINKEDIN_RAW_DIR / "plantilla_ofertas.csv"

# Datos procesados y bases de datos
DB_PATH = PROCESSED_DATA_DIR / "tesis_curricular.db"
LINKEDIN_JSON_PATH = PROCESSED_DATA_DIR / "ofertas_consolidadas.json"
LINKEDIN_CSV_PATH = PROCESSED_DATA_DIR / "ofertas_consolidadas.csv"

# Esquema de base de datos
SCHEMA_PATH = BASE_DIR / "src" / "database" / "schema.sql"

# Rutas de visualización y diagramas
VISUALIZATION_DIR = BASE_DIR / "src" / "visualization"
MMD_DIAGRAM_PATH = VISUALIZATION_DIR / "pipeline_diagrama.mmd"
HTML_DIAGRAM_PATH = VISUALIZATION_DIR / "pipeline_diagrama_interactivo.html"
