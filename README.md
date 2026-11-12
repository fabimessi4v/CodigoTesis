# Pipeline Computacional de Análisis Curricular USACH

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Database: SQLite3](https://img.shields.io/badge/database-SQLite3-lightgrey.svg)](https://www.sqlite.org/)
[![Tests: Passing](https://img.shields.io/badge/tests-10%2F10%20passing-brightgreen.svg)]()
[![Standard: ACM/IEEE CS2013](https://img.shields.io/badge/standard-ACM%2FIEEE%20CS2013-orange.svg)]()

Repositorio oficial del software y datos del proyecto de titulación:
> **"Método computacional basado en procesamiento de lenguaje natural para analizar la alineación curricular de Ingeniería Informática en Chile con estándares ACM/IEEE y necesidades de la industria"**  
> **Autor:** Fabián Ibarra Norambuena  
> **Institución:** Departamento de Ingeniería Informática, Universidad de Santiago de Chile (USACH)

---

## 1. ¿Para qué existe este proyecto? (Propósito)

En Chile y Latinoamérica, la evaluación de planes de estudio universitarios tradicionalmente depende de procesos manuales, cualitativos y subjetivos. Este proyecto introduce un **método cuantitativo y determinista** que utiliza Procesamiento de Lenguaje Natural (PLN) y agrupamiento semántico para evaluar con precisión matemática la coherencia curricular entre tres pilares:

1. **La Promesa Institucional:** Qué declaran formalmente las universidades que forman (los 16 *Perfiles de Egreso Oficiales*).
2. **La Práctica Docente:** Qué materias y asignaturas estructuran efectivamente sus mallas (las *746 Asignaturas* clasificadas bajo el estándar ACM/IEEE).
3. **La Demanda Laboral Real:** Qué tecnologías, competencias y roles exige el mercado productivo nacional (un corpus representativo de *200 Vacantes de LinkedIn*).

---

## 2. Mapa y Estructura del Repositorio

La arquitectura sigue una organización estándar, modular y limpia:

```text
CodigoTesis/
├── README.md                           # Documento principal del repositorio
├── requirements.txt                    # Dependencias de Python
├── .gitignore                          # Exclusiones de Git (caches, temporales)
│
├── config/                             # Configuración global y rutas canónicas
│   ├── __init__.py
│   └── settings.py                     # Definición de paths portables con Pathlib
│
├── data/                               # Almacenamiento de datos (Raw vs Processed)
│   ├── raw/                            # Insumos primarios originales inmutables
│   │   ├── acm_curricula/              # Mallas y clasificación ACM (LaTeX)
│   │   ├── perfiles_egreso/            # Fichas de perfiles de egreso oficiales (LaTeX)
│   │   ├── mallas_pdf/                 # Textos y perfiles auxiliares
│   │   └── linkedin/                   # Esquema JSON y plantilla CSV de ofertas
│   └── processed/                      # Datos consolidados y base de datos activa
│       ├── tesis_curricular.db         # Base de datos SQLite (1,000 registros, 0 errores FK)
│       ├── ofertas_consolidadas.json   # Corpus de 200 vacantes LinkedIn curadas
│       └── ofertas_consolidadas.csv    # Versión tabular sincronizada
│
├── src/                                # Código fuente modular del pipeline
│   ├── __init__.py
│   ├── database/                       # Capa de base de datos
│   │   ├── __init__.py
│   │   ├── connection.py               # Conector SQLite con soporte de Foreign Keys
│   │   └── schema.sql                  # DDL de tablas relacionales e índices
│   │
│   ├── etl/                            # Pipeline de Extracción, Transformación y Carga
│   │   ├── __init__.py
│   │   ├── parsers.py                  # Parsers sintácticos de LaTeX y normalización léxica
│   │   └── pipeline.py                 # Orquestación de ingesta masiva y auditoría
│   │
│   ├── labor_market/                   # Curaduría y herramientas de mercado laboral
│   │   ├── __init__.py
│   │   ├── extractor_bookmarklet.js    # Bookmarklet de extracción en LinkedIn
│   │   ├── ingest_offers.py            # CLI interactiva de catalogación y auto-detección
│   │   ├── import_csv.py               # Sincronizador bidireccional CSV <-> JSON
│   │   ├── stats_validator.py          # Auditor de completitud y métricas del corpus
│   │   └── nlp_preview.py              # Filtro de beneficios legales previo a SBERT
│   │
│   └── visualization/                  # Diagramas de arquitectura y visualización web
│       ├── __init__.py
│       ├── pipeline_diagrama.mmd       # Definición Mermaid de la arquitectura
│       ├── pipeline_diagrama_interactivo.html # Editor y visor interactivo en navegador
│       └── diagram_generator.py        # Generador dinámico de diagramas SVG y PDF
│
├── scripts/                            # Puntos de entrada ejecutables directos (CLI)
│   ├── run_etl.py                      # Reconstruye la BD desde los insumos raw
│   ├── run_queries.py                  # Ejecuta consultas de auditoría y reportes SQL
│   └── update_diagram.sh               # Actualiza el diagrama de arquitectura
│
├── docs/                               # Documentación técnica exhaustiva
│   ├── ARCHITECTURE.md                 # Diseño detallado, justificación y flujo de datos
│   └── DATA_DICTIONARY.md              # Diccionario de tablas, columnas y taxonomía ACM
│
└── tests/                              # Pruebas automatizadas de consistencia
    ├── __init__.py
    ├── test_database_integrity.py      # Validación de claves foráneas y conteos
    └── test_parsers.py                 # Pruebas unitarias de limpieza sintáctica
```

---

## 3. ¿Qué hace cada módulo?

| Módulo | Función Principal | ¿Por qué se diseñó así? |
| :--- | :--- | :--- |
| **`src/etl/`** | Parsea archivos LaTeX de mallas y perfiles, normaliza caracteres y los carga en SQLite. | Desacopla la lógica de parsing de la persistencia para permitir pruebas unitarias independientes. |
| **`src/database/`** | Define el esquema relacional (`schema.sql`) y administra conexiones con integridad de claves foráneas. | Garantiza que no existan asignaturas o perfiles huérfanos mediante `PRAGMA foreign_keys = ON`. |
| **`src/labor_market/`** | Captura, limpia y valida las 200 vacantes de LinkedIn (100 TI y 100 No-TI). | Incorpora filtros específicos de ruido corporativo chileno para no distorsionar las representaciones vectoriales. |
| **`src/visualization/`** | Renderiza el pipeline completo en formato interactivo (HTML) y vectorial (SVG/PDF). | Permite iterar visualmente sobre la arquitectura y exportar diagramas vectoriales para la memoria de título. |
| **`scripts/`** | Provee comandos CLI directos para operar el sistema. | Simplifica la experiencia del usuario y automatiza la ejecución sin requerir memorizar comandos complejos. |
| **`docs/`** | Documentación de arquitectura y modelo de datos. | Otorga máxima transparencia y trazabilidad a la comisión evaluadora sobre las decisiones tomadas. |

---

## 4. Guía de Instalación y Ejecución ("¿Cómo usarlo?")

### 4.1. Requisitos Previos
* **Python 3.8** o superior instalado en el sistema.
* No requiere gestores de bases de datos externos (utiliza el motor SQLite integrado en la biblioteca estándar de Python).

### 4.2. Instalación de Dependencias
Clona el repositorio e instala las dependencias base:

```bash
git clone https://github.com/fabimessi4v/CodigoTesis.git
cd CodigoTesis
pip install -r requirements.txt
```

### 4.3. Ejecución de Pruebas Automatizadas
Verifica la consistencia matemática y referencial del corpus ejecutando la suite de tests:

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```
*Salida esperada: `Ran 10 tests in 0.005s ... OK` (10 de 10 pruebas exitosas).*

---

### 4.4. Operación del Pipeline

#### 1. Reconstruir la Base de Datos desde Cero (Pipeline ETL)
Para regenerar la base de datos `data/processed/tesis_curricular.db` a partir de los documentos LaTeX primarios:

```bash
python3 scripts/run_etl.py
```
El script creará las tablas, verificará la integridad referencial y reportará los registros consolidados (exactamente 1,000 registros: 23 áreas ACM, 15 universidades, 16 programas, 746 asignaturas y 200 ofertas laborales).

#### 2. Consultas Analíticas y Verificación Curricular
Para visualizar métricas curriculares, el Top 10 de áreas ACM en Chile y distribución de ofertas:

```bash
python3 scripts/run_queries.py
```

#### 3. Auditoría de Calidad del Mercado Laboral
Para verificar el balance de la muestra laboral (100 TI / 100 No-TI) y el Top de tecnologías más demandadas:

```bash
python3 src/labor_market/stats_validator.py
```

#### 4. Previsualizar Limpieza NLP sobre Ofertas
Para observar cómo se elimina el ruido corporativo (beneficios, leyes, colación) antes de Sentence-BERT:

```bash
python3 src/labor_market/nlp_preview.py
```

#### 5. Visualizar y Editar el Diagrama de Arquitectura
Abre en tu navegador el editor visual interactivo:
```bash
# Abre src/visualization/pipeline_diagrama_interactivo.html en cualquier navegador
xdg-open src/visualization/pipeline_diagrama_interactivo.html
```

---

## 5. Documentación Adicional

Para más detalles técnicos y fundamentos metodológicos, consulta:
* 📘 [Arquitectura del Pipeline y Decisiones de Diseño](docs/ARCHITECTURE.md)
* 📊 [Diccionario de Datos y Taxonomía ACM](docs/DATA_DICTIONARY.md)
