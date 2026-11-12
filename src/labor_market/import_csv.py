#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Importación y Sincronización de Ofertas Laborales (CSV / JSON).

Proyecto de Tesis:
"Método computacional basado en procesamiento de lenguaje natural para analizar la
alineación curricular de Ingeniería Informática en Chile con estándares ACM/IEEE y
necesidades de la industria"
Autor: Fabián Ibarra Norambuena (USACH)

¿Para qué sirve?
Permite importar y sincronizar vacantes laborales obtenidas desde fuentes externas
(por ejemplo, descargas masivas desde el Bookmarklet en el navegador, planillas
colaborativas en Google Sheets o archivos CSV curados manualmente).

¿Por qué se diseñó así?
El proceso de levantamiento de 200 vacantes requirió recolección semi-automatizada.
Para evitar inconsistencias entre formatos tabulares (CSV) y semiestructurados (JSON),
este módulo asegura la bidireccionalidad: cualquier carga o modificación en CSV
se valida y sincroniza automáticamente hacia el archivo canónico `ofertas_consolidadas.json`.

¿Cómo funciona?
1. Detecta si el archivo de entrada es CSV o JSON.
2. Si es CSV, normaliza las columnas hacia el esquema canónico (13 campos).
3. Convierte el campo `requisitos_tecnicos` a lista tipada si viene como string separado por comas.
4. Aplica deduplicación basada en el identificador único `id` de la oferta.
5. Actualiza tanto `ofertas_consolidadas.json` como `ofertas_consolidadas.csv`.
"""

import os
import sys
import json
import csv
from pathlib import Path
from typing import List, Dict, Any

# Permitir importaciones absolutas del proyecto
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from config.settings import LINKEDIN_JSON_PATH, LINKEDIN_CSV_PATH, PROCESSED_DATA_DIR
    JSON_PATH = str(LINKEDIN_JSON_PATH)
    CSV_PATH = str(LINKEDIN_CSV_PATH)
    DATA_DIR = str(PROCESSED_DATA_DIR)
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DATA_DIR = os.path.join(BASE_DIR, "data", "processed")
    JSON_PATH = os.path.join(DATA_DIR, "ofertas_consolidadas.json")
    CSV_PATH = os.path.join(DATA_DIR, "ofertas_consolidadas.csv")


def cargar_consolidadas() -> List[Dict[str, Any]]:
    """
    Carga el listado consolidado actual de ofertas desde el archivo JSON.

    Returns:
        List[Dict[str, Any]]: Lista de diccionarios de ofertas existentes o lista vacía.
    """
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(JSON_PATH):
        try:
            with open(JSON_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def guardar_consolidadas(ofertas: List[Dict[str, Any]]) -> None:
    """
    Persiste las ofertas sincronizadamente en JSON y CSV normalizado.

    Args:
        ofertas (List[Dict[str, Any]]): Lista de diccionarios con el esquema completo.
    """
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(ofertas, f, ensure_ascii=False, indent=2)

    fieldnames = [
        "id", "titulo", "empresa", "sector", "subsector", "rol_categoria",
        "ubicacion", "modalidad", "nivel_experiencia", "requisitos_tecnicos",
        "url", "descripcion_completa", "fecha_recoleccion"
    ]
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for o in ofertas:
            fila = dict(o)
            if isinstance(fila.get("requisitos_tecnicos"), list):
                fila["requisitos_tecnicos"] = ", ".join(fila["requisitos_tecnicos"])
            writer.writerow(fila)


def importar_desde_archivo(ruta_archivo: str) -> None:
    """
    Importa ofertas desde una ruta externa y las une al conjunto consolidado.

    Args:
        ruta_archivo (str): Ruta al archivo .csv o .json fuente.
    """
    if not os.path.exists(ruta_archivo):
        print(f"❌ Error: El archivo {ruta_archivo} no existe.")
        return

    ofertas_actuales = cargar_consolidadas()
    ids_existentes = {o.get("id") for o in ofertas_actuales if "id" in o}

    nuevas_ofertas = []

    if ruta_archivo.endswith(".json"):
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            datos = json.load(f)
            if isinstance(datos, list):
                nuevas_ofertas = datos
            elif isinstance(datos, dict):
                nuevas_ofertas = [datos]

    elif ruta_archivo.endswith(".csv"):
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            # Detectar delimitador automáticamente (, o ;)
            muestra = f.read(2048)
            delimitador = ";" if ";" in muestra and muestra.count(";") > muestra.count(",") else ","
            f.seek(0)
            lector = csv.DictReader(f, delimiter=delimitador)
            for fila in lector:
                # Convertir requisitos_tecnicos a lista
                reqs_str = fila.get("requisitos_tecnicos", "")
                if reqs_str:
                    fila["requisitos_tecnicos"] = [r.strip() for r in reqs_str.split(",") if r.strip()]
                else:
                    fila["requisitos_tecnicos"] = []
                nuevas_ofertas.append(fila)

    agregadas = 0
    actualizadas = 0

    for of in nuevas_ofertas:
        oid = of.get("id")
        if not oid:
            continue

        if oid in ids_existentes:
            for idx, item in enumerate(ofertas_actuales):
                if item.get("id") == oid:
                    ofertas_actuales[idx] = of
                    actualizadas += 1
                    break
        else:
            ofertas_actuales.append(of)
            ids_existentes.add(oid)
            agregadas += 1

    guardar_consolidadas(ofertas_actuales)
    print(f"✅ Sincronización exitosa desde {ruta_archivo}:")
    print(f"   - Agregadas nuevas: {agregadas}")
    print(f"   - Actualizadas: {actualizadas}")
    print(f"   - Total en corpus consolidado: {len(ofertas_actuales)} ofertas.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 import_csv.py <archivo_a_importar.csv|json>")
    else:
        importar_desde_archivo(sys.argv[1])
