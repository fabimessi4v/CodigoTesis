# Arquitectura del Sistema de Análisis Curricular

**Proyecto de Tesis:**  
*"Método computacional basado en procesamiento de lenguaje natural para analizar la alineación curricular de Ingeniería Informática en Chile con estándares ACM/IEEE y necesidades de la industria"*  
**Autor:** Fabián Ibarra Norambuena  
**Institución:** Universidad de Santiago de Chile (USACH)

---

## 1. Visión General y Propósito

El sistema es un **pipeline computacional reproducible** diseñado para resolver el problema de la evaluación y alineación curricular universitaria mediante técnicas avanzadas de Procesamiento de Lenguaje Natural (PLN) y aprendizaje no supervisado.

Tradicionalmente, la evaluación de planes de estudio es un proceso manual, cualitativo y propenso a sesgos subjetivos. Este software implementa una metodología cuantitativa, determinista y auditable que contrasta tres dimensiones curriculares fundamentales:

1. **La Promesa Institucional:** Perfiles de Egreso Declarados normativamente por las 16 carreras analizadas.
2. **La Práctica Curricular:** 746 asignaturas estructuradas en mallas curriculares, contrastadas contra el Ground Truth del estándar internacional ACM/IEEE CS2013 / CC2020.
3. **La Demanda Laboral Real:** Muestra representativa y estratificada de 200 vacantes profesionales de LinkedIn en Chile.

---

## 2. Diagrama de Arquitectura End-to-End

```mermaid
flowchart TD
    %% ========================================================
    %% PIPELINE COMPUTACIONAL: INGESTA -> BD RELACIONAL -> PLN/SBERT -> CLUSTERING -> DASHBOARD
    %% ========================================================

    subgraph F1["Fase 1: Ingesta de Datos Heterogéneos (Raw Data)"]
        direction TB
        A1["16 Mallas Curriculares<br/><b>746 Asignaturas</b><br/><i>(Semestres, Nombres, Áreas)</i>"]
        A2["Curaduría Ground Truth ACM<br/><b>23 Áreas de Conocimiento</b><br/><i>(Juicio experto nacional)</i>"]
        A3["16 Perfiles de Egreso Declarados<br/><b>Textos Oficiales</b><br/><i>(Fichas institucionales)</i>"]
        A4["Mercado Laboral LinkedIn<br/><b>200 Ofertas Estratificadas</b><br/><i>(100 TI / 100 No-TI)</i>"]
    end

    subgraph F2["Fase 2: Capa de Persistencia Relacional y Normalización"]
        direction TB
        B1["Parsers Sintácticos & Limpieza LaTeX<br/><code>src.etl.parsers</code>"]
        B2[("Base de Datos Relacional<br/><b>SQLite: tesis_curricular.db</b><br/><i>(1,000 registros consolidados)</i>")]
        B3["Auditoría de Integridad<br/><code>PRAGMA foreign_key_check</code>"]
    end

    subgraph F3["Fase 3: Vectorización Semántica en Espacio Latente"]
        direction TB
        C1["Limpieza Léxica y Filtro de Beneficios<br/><code>src.labor_market.nlp_preview</code>"]
        C2["Modelo Preentrenado Sentence-BERT<br/><b>paraphrase-multilingual-mpnet-base-v2</b>"]
        C3["Vectores Densos en R^768<br/><b>v_malla, v_perfil, v_acm, v_laboral</b>"]
    end

    subgraph F4["Fase 4: Modelamiento Curricular y Métricas Trilaterales"]
        direction TB
        D1["Agrupamiento No Supervisado<br/><b>K-Means & Jerárquico Aglomerativo</b>"]
        D2["Reducción Dimensional UMAP<br/><b>Proyección 2D/3D (Trustworthiness ≥ 0.85)</b>"]
        D3["Métricas de Alineación Trilateral<br/><b>Similitud Coseno, Cobertura %, Brecha</b>"]
        D4["Validación vs Ground Truth<br/><b>Adjusted Rand Index (ARI), NMI, Pureza</b>"]
    end

    subgraph F5["Fase 5: Consumo y Visualización Arquitectural"]
        direction TB
        E1["Editor & Visor Interactivo<br/><code>src.visualization.pipeline_diagrama_interactivo.html</code>"]
        E2["Generador Vectorial SVG/PDF<br/><code>src.visualization.diagram_generator</code>"]
        E3["Consultas Analíticas y Verificación CLI<br/><code>scripts.run_queries</code>"]
    end

    %% Conexiones
    A1 --> B1
    A2 --> B1
    A3 --> B1
    A4 --> B1
    B1 --> B2
    B2 --> B3
    B2 --> C1
    C1 --> C2
    C2 --> C3
    C3 --> D1
    C3 --> D2
    C3 --> D3
    B2 -.-> D4
    D1 --> D4
    D3 --> E3
    E1 --> E2
```

---

## 3. Decisiones Arquitecturales y Justificación Técnica ("Por qué")

### 3.1. Separación Estricta entre Datos Crudos (`data/raw`) y Procesados (`data/processed`)
* **Por qué:** Los archivos LaTeX originales (`Clasificacion_ACM_Mallas_Curriculares.tex` y `Corpus_y_Perfiles_Egreso_16_Universidades.tex`) son fuentes primarias de verdad que no deben ser mutadas en tiempo de ejecución.
* **Beneficio:** Garantiza inmutabilidad y reproducibilidad. El pipeline puede recrear la base de datos completa de forma determinista ante cualquier re-ejecución.

### 3.2. Persistencia en SQLite Relacional con `PRAGMA foreign_keys = ON`
* **Por qué:** Frente a archivos CSV o JSON dispersos propensos a inconsistencias léxicas, SQLite ofrece tipado estructurado, consultas analíticas SQL instantáneas y cumplimiento estricto de integridad referencial.
* **Beneficio:** Imposibilita la existencia de asignaturas huérfanas o programas sin universidad asociada.

### 3.3. Configuración Canónica Centralizada con `Pathlib` (`config/settings.py`)
* **Por qué:** El uso de rutas relativas frágiles (`../../data`) genera fallos cuando un script es invocado desde un subdirectorio o desde terminales remotas.
* **Beneficio:** Portabilidad total. Cualquier script puede ejecutarse desde la raíz o cualquier submódulo sin romper las rutas del sistema de archivos.

### 3.4. Desacoplamiento de Parsers Sintácticos (`src/etl/parsers.py`) y Pipeline (`src/etl/pipeline.py`)
* **Por qué:** El parsing de expresiones regulares complejas en código LaTeX debe ser testeable de manera unitaria e independiente de la base de datos.
* **Beneficio:** Facilita la creación de tests unitarios rápidos (`tests/test_parsers.py`) y aísla posibles cambios en la tipografía de los documentos fuente.

### 3.5. Filtrado de Ruido Corporativo previo a SBERT (`src/labor_market/nlp_preview.py`)
* **Por qué:** Las ofertas laborales de LinkedIn contienen párrafos extensos de beneficios legales o corporativos chilenos (cajas de compensación, convenios, aguinaldos, leyes de inclusión).
* **Beneficio:** Evita que el modelo Sentence-BERT ubique ofertas técnicas en regiones del espacio latente dominadas por términos de Recursos Humanos o Bienestar, preservando la pureza semántica de las competencias tecnológicas.

---

## 4. Estructura de Módulos del Repositorio

| Módulo | Responsabilidad |
| :--- | :--- |
| `config/settings.py` | Definición de rutas canónicas inmutables del proyecto. |
| `src/database/` | Conexión contextual a SQLite y DDL de creación de tablas e índices (`schema.sql`). |
| `src/etl/parsers.py` | Parsers sintácticos para extracción desde LaTeX y JSON. |
| `src/etl/pipeline.py` | Orquestador ETL con validaciones de integridad referencial. |
| `src/labor_market/` | Curaduría, validación estadística, ingesta interactiva y bookmarklet de LinkedIn. |
| `src/visualization/` | Visor interactivo web en Mermaid y renderizador vectorial (SVG/PDF). |
| `scripts/` | Puntos de entrada CLI de ejecución directa (`run_etl.py`, `run_queries.py`, `update_diagram.sh`). |
| `tests/` | Suite automatizada de pruebas de consistencia referencial y pruebas unitarias. |
| `docs/` | Documentación exhaustiva (Arquitectura y Diccionario de Datos). |
