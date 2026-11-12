#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Validación, Control de Calidad y Estadísticas del Corpus Laboral.

Proyecto de Tesis:
"Método computacional basado en procesamiento de lenguaje natural para analizar la
alineación curricular de Ingeniería Informática en Chile con estándares ACM/IEEE y
necesidades de la industria"
Autor: Fabián Ibarra Norambuena (USACH)

¿Para qué sirve?
Inspecciona la integridad del corpus de 200 vacantes de LinkedIn, reportando:
1. Cobertura de la meta muestral estratificada (100 ofertas TI y 100 ofertas No-TI).
2. Detección de anomalías de calidad: campos obligatorios vacíos, descripciones cortas (<50 palabras)
   o URLs duplicadas.
3. Top 15 de tecnologías más demandadas por el mercado nacional.
4. Distribución por modalidad contractual y niveles de experiencia laboral.

¿Cómo funciona?
Lee `ofertas_consolidadas.json` desde la ruta canónica del proyecto, aplica
agregaciones con `collections.Counter` y emite un informe estructurado por consola.
"""

import os
import sys
import json
from pathlib import Path
from collections import Counter
from typing import Dict, Any

# Permitir importaciones absolutas del proyecto
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from config.settings import LINKEDIN_JSON_PATH
    JSON_PATH = str(LINKEDIN_JSON_PATH)
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    JSON_PATH = os.path.join(BASE_DIR, "data", "processed", "ofertas_consolidadas.json")


def analizar_dataset() -> None:
    """
    Ejecuta el diagnóstico de integridad y métricas estadísticas sobre el dataset de ofertas.
    """
    if not os.path.exists(JSON_PATH):
        print(f"❌ No se encontró el archivo consolidado en {JSON_PATH}")
        print("Ejecuta 'python3 src/labor_market/ingest_offers.py' o 'python3 src/labor_market/import_csv.py' primero.")
        return

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        ofertas = json.load(f)

    total = len(ofertas)
    ti = [o for o in ofertas if o.get("sector") == "TI"]
    noti = [o for o in ofertas if o.get("sector") == "No-TI"]

    print("\n" + "=" * 65)
    print(" 📊 DIAGNÓSTICO DEL CORPUS LABORAL LINKEDIN (TESIS USACH)")
    print("=" * 65)
    print(f"Total ofertas recolectadas: {total} / 200 ({(total/200)*100:.1f}%)")
    print(f"├─ Sector TI:    {len(ti):3d} / 100 [{(len(ti)/100)*100:5.1f}%]")
    print(f"└─ Sector No-TI: {len(noti):3d} / 100 [{(len(noti)/100)*100:5.1f}%]")

    if total == 0:
        print("\nEl dataset está vacío actualmente.")
        return

    # 1. Chequeo de calidad y campos vacíos
    faltantes = []
    longitudes_palabras = []
    urls = []

    for o in ofertas:
        oid = o.get("id", "SIN_ID")
        desc = o.get("descripcion_completa", "")
        palabras = len(desc.split())
        longitudes_palabras.append(palabras)

        if palabras < 50:
            faltantes.append(f"⚠️ {oid}: Descripción muy corta ({palabras} palabras). Puede afectar embeddings SBERT.")

        if not o.get("titulo") or not o.get("empresa"):
            faltantes.append(f"❌ {oid}: Falta título o empresa.")

        url = o.get("url", "")
        if url:
            urls.append(url)

    # Detección de duplicados en URLs
    url_counts = Counter(urls)
    duplicadas = [u for u, c in url_counts.items() if c > 1]

    print("\n--- 1. CONTROL DE CALIDAD DE DATOS ---")
    if not faltantes and not duplicadas:
        print("✅ Todas las ofertas cumplen los estándares mínimos de completitud.")
    else:
        for f_msg in faltantes[:10]:
            print(f_msg)
        if len(faltantes) > 10:
            print(f"... y {len(faltantes) - 10} observaciones más.")
        if duplicadas:
            print(f"⚠️ Hay {len(duplicadas)} URLs duplicadas.")

    promedio_palabras = sum(longitudes_palabras) / len(longitudes_palabras) if longitudes_palabras else 0
    print(f"Longitud promedio de descripción: {promedio_palabras:.0f} palabras por oferta.")

    # 2. Análisis de Tecnologías
    tecnologias_totales = []
    tec_ti = []
    tec_noti = []

    for o in ofertas:
        reqs = o.get("requisitos_tecnicos", [])
        if isinstance(reqs, str):
            reqs = [r.strip() for r in reqs.split(",") if r.strip()]
        tecnologias_totales.extend(reqs)
        if o.get("sector") == "TI":
            tec_ti.extend(reqs)
        else:
            tec_noti.extend(reqs)

    top_global = Counter(tecnologias_totales).most_common(15)
    print("\n--- 2. TOP 15 TECNOLOGÍAS MÁS DEMANDADAS (TOTAL) ---")
    for tec, count in top_global:
        barra = "█" * int(count / 2)
        print(f" {tec:<15} | {count:2d} ({count/total*100:4.1f}%) {barra}")

    # 3. Distribución por Modalidad
    modalidades = Counter(o.get("modalidad", "No declarada") for o in ofertas)
    print("\n--- 3. MODALIDAD DE TRABAJO ---")
    for mod, count in modalidades.items():
        print(f" {mod:<15}: {count:2d} ({count/total*100:4.1f}%)")

    # 4. Distribución por Nivel de Experiencia
    niveles = Counter(o.get("nivel_experiencia", "No especificado") for o in ofertas)
    print("\n--- 4. NIVEL DE EXPERIENCIA SOLICITADO ---")
    for niv, count in niveles.items():
        print(f" {niv:<15}: {count:2d} ({count/total*100:4.1f}%)")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    analizar_dataset()
