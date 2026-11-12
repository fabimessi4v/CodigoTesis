-- ====================================================================
-- ESQUEMA RELACIONAL: BASE DE DATOS ESTRUCTURADA DE ANÁLISIS CURRICULAR
-- Proyecto de Tesis: Método Computacional de Análisis Curricular USACH
-- Autor: Fabián Ibarra Norambuena
-- ====================================================================

PRAGMA foreign_keys = ON;

-- 1. Marco Taxonómico ACM/IEEE-CS (23 Áreas de Conocimiento)
DROP TABLE IF EXISTS asignaturas;
DROP TABLE IF EXISTS programas;
DROP TABLE IF EXISTS universidades;
DROP TABLE IF EXISTS taxonomia_acm;
DROP TABLE IF EXISTS ofertas_laborales;

CREATE TABLE taxonomia_acm (
    codigo VARCHAR(10) PRIMARY KEY,
    nombre_es TEXT NOT NULL,
    nombre_en TEXT NOT NULL,
    alcance_tematico TEXT NOT NULL
);

-- 2. Instituciones Universitarias Catalogadas
CREATE TABLE universidades (
    id VARCHAR(20) PRIMARY KEY,
    nombre TEXT NOT NULL
);

-- 3. Programas Universitarios de Estudio y Perfiles de Egreso Declarados
CREATE TABLE programas (
    id VARCHAR(30) PRIMARY KEY,
    universidad_id VARCHAR(20) NOT NULL,
    nombre_carrera TEXT NOT NULL,
    tipo_plan TEXT NOT NULL,
    duracion_semestres INTEGER,
    num_asignaturas_declaradas INTEGER,
    perfil_egreso_oficial TEXT NOT NULL,
    FOREIGN KEY (universidad_id) REFERENCES universidades(id) ON UPDATE CASCADE ON DELETE RESTRICT
);

-- 4. Mallas Curriculares y Asignaturas con Ground Truth ACM
CREATE TABLE asignaturas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    programa_id VARCHAR(30) NOT NULL,
    periodo VARCHAR(10) NOT NULL,
    nombre TEXT NOT NULL,
    clasificacion_acm_raw TEXT NOT NULL,
    codigo_acm VARCHAR(10),
    FOREIGN KEY (programa_id) REFERENCES programas(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (codigo_acm) REFERENCES taxonomia_acm(codigo) ON UPDATE CASCADE ON DELETE SET NULL
);

-- 5. Mercado Laboral (Ofertas de Empleo LinkedIn)
CREATE TABLE ofertas_laborales (
    id VARCHAR(50) PRIMARY KEY,
    titulo TEXT NOT NULL,
    empresa TEXT NOT NULL,
    sector TEXT,
    subsector TEXT,
    rol_categoria TEXT,
    ubicacion TEXT,
    modalidad TEXT,
    nivel_experiencia TEXT,
    requisitos_tecnicos TEXT,
    url TEXT,
    descripcion_completa TEXT NOT NULL,
    fecha_recoleccion TEXT
);

-- Índices de optimización para consultas analíticas y generación de embeddings
CREATE INDEX idx_asignaturas_programa ON asignaturas(programa_id);
CREATE INDEX idx_asignaturas_acm ON asignaturas(codigo_acm);
CREATE INDEX idx_programas_uni ON programas(universidad_id);
CREATE INDEX idx_ofertas_sector ON ofertas_laborales(sector);
CREATE INDEX idx_ofertas_rol ON ofertas_laborales(rol_categoria);
