#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Previsualización y Normalización de Texto para Ofertas de LinkedIn.

Proyecto de Tesis:
"Método computacional basado en procesamiento de lenguaje natural para analizar la
alineación curricular de Ingeniería Informática en Chile con estándares ACM/IEEE y
necesidades de la industria"
Autor: Fabián Ibarra Norambuena (USACH)

¿Para qué sirve?
Demuestra la fase de limpieza léxica y normalización previa a la vectorización densa
mediante Sentence-BERT (SBERT). Filtra el "ruido corporativo" que distorsiona las
representaciones vectoriales del perfil profesional.

¿Por qué se diseñó así?
Las descripciones laborales de portales como LinkedIn contienen extensas secciones
de beneficios contractuales y normativas legales (e.g., cajas de compensación,
seguros complementarios, leyes de inclusión laboral, tarjetas de colación).
Si estos términos se proyectan en el espacio latente R^768 de SBERT, sesgan
artificialmente los vectores hacia la semántica de Recursos Humanos en lugar de
las competencias técnicas de ingeniería en informática.

¿Cómo funciona?
Aplica un conjunto curado de expresiones regulares (`PATRONES_RUIDO`) para eliminar
bloques no técnicos y compacta los espacios en blanco preservando los requisitos,
roles y funciones tecnológicas del cargo.
"""

import os
import sys
import re
import json
from pathlib import Path
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

# Expresiones regulares para ruido corporativo común en Chile
PATRONES_RUIDO = [
    r"(?i)seguro de salud complementario",
    r"(?i)caja de compensación",
    r"(?i)aguinaldo de fiestas patrias y navidad",
    r"(?i)día libre por tu cumpleaños",
    r"(?i)convenio con gimnasios?",
    r"(?i)modalidad de trabajo (híbrida|remota|presencial)",
    r"(?i)igualdad de oportunidades e inclusión laboral ley \d+",
    r"(?i)horario flexible y viernes corto",
    r"(?i)ticket(s)? de colación|tarjeta amipass|sodexo",
]


def limpiar_texto_oferta(texto: str) -> str:
    """
    Limpia el texto de la oferta eliminando beneficios y ruido administrativo.

    Args:
        texto (str): Descripción cruda en texto plano.

    Returns:
        str: Texto limpio enfocado en competencias, funciones y herramientas.
    """
    limpio = texto
    for patron in PATRONES_RUIDO:
        limpio = re.sub(patron, "", limpio)

    # Normalizar espacios y saltos de línea excesivos
    limpio = re.sub(r'\n+', '\n', limpio)
    limpio = re.sub(r'[ \t]+', ' ', limpio)
    return limpio.strip()


def preview_nlp() -> None:
    """Muestra un ejemplo comparativo entre texto en bruto y texto normalizado."""
    if not os.path.exists(JSON_PATH):
        print(f"❌ No se encontró {JSON_PATH}")
        return

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        ofertas = json.load(f)

    if not ofertas:
        print("Dataset vacío.")
        return

    print("\n" + "=" * 70)
    print(" PREVIEW DE LIMPIEZA NLP (PRE-EMBEDDINGS SBERT)")
    print("=" * 70)

    ejemplo = ofertas[0]
    texto_orig = ejemplo.get("descripcion_completa", "")
    texto_limpio = limpiar_texto_oferta(texto_orig)

    print(f"\nID: {ejemplo.get('id')} - {ejemplo.get('titulo')} ({ejemplo.get('empresa')})")
    print(f"Longitud original: {len(texto_orig)} caracteres ({len(texto_orig.split())} palabras)")
    print(f"Longitud limpia:   {len(texto_limpio)} caracteres ({len(texto_limpio.split())} palabras)")
    print(f"Reducción:         {len(texto_orig) - len(texto_limpio)} caracteres de ruido eliminados.")

    print("\n--- SNIPPET TEXTO ORIGINAL (Primeras 250 letras) ---")
    print(texto_orig[:250] + "...")

    print("\n--- SNIPPET TEXTO LIMPIO (Primeras 250 letras) ---")
    print(texto_limpio[:250] + "...")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    preview_nlp()
