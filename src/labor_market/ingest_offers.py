#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Asistente Interactivo de Ingesta y Curaduría de Ofertas Laborales de LinkedIn.

Proyecto de Tesis:
"Método computacional basado en procesamiento de lenguaje natural para analizar la
alineación curricular de Ingeniería Informática en Chile con estándares ACM/IEEE y
necesidades de la industria"
Autor: Fabián Ibarra Norambuena (USACH)

¿Para qué sirve?
Proporciona una interfaz de línea de comandos (CLI) interactiva para catalogar,
etiquetar y validar nuevas vacantes de empleo provenientes de LinkedIn u otros portales.

¿Por qué se diseñó así?
El muestreo de 200 vacantes requirió una estratificación estricta:
- 100 ofertas de empresas pertenecientes a la industria tecnológica pura (TI).
- 100 ofertas de departamentos de informática en sectores productivos no-TI
  (Banca, Retail, Minería, Telecomunicaciones, Gobierno, Salud).
Para acelerar la curaduría manual sin perder rigor, este script implementa:
1. Generación automática y consecutiva de ID correlativos (e.g., `JOB-TI-001`, `JOB-NOTI-045`).
2. Reconocimiento automático de entidades tecnológicas mediante un vocabulario predefinido
   de 50+ tecnologías y frameworks modernos.
3. Validación de campos obligatorios para prevenir registros incompletos.

¿Cómo funciona?
Solicita al evaluador los campos esenciales (título, empresa, sector, subsector,
rol, modalidad, URL y descripción completa). Analiza el texto mediante regex para
sugerir tecnologías detectadas, y guarda el resultado tanto en JSON como en CSV.
"""

import os
import sys
import json
import csv
import re
from pathlib import Path
from datetime import datetime
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

# Diccionario de tecnologías comunes para auto-detección
TECNOLOGIAS_VOCABULARIO = [
    "Python", "Java", "JavaScript", "TypeScript", "C#", "C++", "Go", "Golang", "Rust", "PHP", "Ruby", "Kotlin", "Swift",
    "React", "Angular", "Vue", "Node.js", "Django", "Flask", "FastAPI", "Spring Boot", ".NET",
    "SQL", "PostgreSQL", "MySQL", "Oracle", "MongoDB", "Redis", "Elasticsearch", "Cassandra",
    "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Terraform", "Git", "CI/CD", "Linux",
    "Pandas", "NumPy", "Scikit-Learn", "TensorFlow", "PyTorch", "Airflow", "Kafka", "Spark", "PySpark", "Databricks", "PowerBI", "Tableau",
    "Scrum", "Agile", "DevOps", "Microservicios", "REST", "GraphQL", "Ciberseguridad"
]


def cargar_ofertas() -> List[Dict[str, Any]]:
    """Carga las ofertas existentes desde el archivo consolidado JSON."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(JSON_PATH):
        try:
            with open(JSON_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error al leer JSON existente: {e}")
            return []
    return []


def guardar_ofertas(ofertas: List[Dict[str, Any]]) -> None:
    """Persiste las ofertas sincronizadamente en JSON y CSV."""
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


def obtener_siguiente_id(ofertas: List[Dict[str, Any]], sector: str) -> str:
    """
    Calcula el siguiente identificador correlativo según el sector.
    
    Prefijos:
    - Sector TI: JOB-TI-XXX (del 001 al 100)
    - Sector No-TI: JOB-NOTI-XXX (del 001 al 100)
    """
    prefijo = "JOB-TI-" if sector == "TI" else "JOB-NOTI-"
    max_num = 0
    for o in ofertas:
        oid = o.get("id", "")
        if oid.startswith(prefijo):
            try:
                num = int(oid.replace(prefijo, ""))
                if num > max_num:
                    max_num = num
            except ValueError:
                pass
    return f"{prefijo}{str(max_num + 1).zfill(3)}"


def detectar_tecnologias(texto: str) -> List[str]:
    """Identifica tecnologías mencionadas en el texto usando límites de palabra."""
    encontradas = []
    texto_lower = texto.lower()
    for tec in TECNOLOGIAS_VOCABULARIO:
        patron = r'\b' + re.escape(tec.lower()) + r'\b'
        if tec.lower() in [".net", "c#", "c++"]:
            if tec.lower() in texto_lower:
                encontradas.append(tec)
        else:
            if re.search(patron, texto_lower):
                encontradas.append(tec)
    return list(dict.fromkeys(encontradas))


def capturar_texto_multilinea(prompt: str) -> str:
    """Permite ingresar descripciones extensas finalizando con Ctrl+D o EOF."""
    print(prompt + " (Escribe o pega el texto. Presiona Enter y luego Ctrl+D en Linux para finalizar):")
    lineas = []
    try:
        while True:
            linea = input()
            lineas.append(linea)
    except EOFError:
        pass
    return "\n".join(lineas).strip()


def menu_ingesta() -> None:
    """Bucle principal de ingesta asistida de ofertas laborales."""
    ofertas = cargar_ofertas()
    
    while True:
        ti_count = sum(1 for o in ofertas if o.get("sector") == "TI")
        noti_count = sum(1 for o in ofertas if o.get("sector") == "No-TI")
        
        print("\n" + "="*50)
        print("  SISTEMA DE INGESTA DE OFERTAS LINKEDIN")
        print(f"  Progreso: {len(ofertas)}/200 ofertas registradas")
        print(f"  ├─ Sector TI:    {ti_count}/100")
        print(f"  └─ Sector No-TI: {noti_count}/100")
        print("="*50)
        print("1. Ingresar nueva oferta manual")
        print("2. Ver últimas ofertas agregadas")
        print("3. Salir")
        
        opc = input("\nSeleccione una opción: ").strip()
        
        if opc == "1":
            print("\n--- Selección de Sector ---")
            print("1. TI (Empresa nativa de desarrollo/servicios software)")
            print("2. No-TI (Banca, Retail, Minería, Telecom, etc.)")
            sec_opc = input("Sector (1/2): ").strip()
            sector = "TI" if sec_opc == "1" else "No-TI"
            
            siguiente_id = obtener_siguiente_id(ofertas, sector)
            print(f"\n>> Asignando ID: {siguiente_id}")
            
            titulo = input("Título del cargo: ").strip()
            empresa = input("Empresa: ").strip()
            
            subsector = ""
            if sector == "No-TI":
                subsector = input("Subsector (Banca, Retail, Minería, Telecom, etc.): ").strip()
            else:
                subsector = input("Subsector TI (Software Factory, Fintech, SaaS, etc.) [Opcional]: ").strip()
            
            print("\nRoles comunes: Backend, Frontend, Fullstack, DevOps, Data Engineer, QA, Data Scientist, etc.")
            rol_categoria = input("Categoría de Rol: ").strip()
            
            modalidad = input("Modalidad (Remoto / Híbrido / Presencial): ").strip()
            ubicacion = input("Ubicación (ej: Santiago, Chile / Región de Valparaíso): ").strip()
            nivel_experiencia = input("Nivel (Junior / Semi-Senior / Senior / Lead): ").strip()
            url = input("URL de la oferta en LinkedIn: ").strip()
            
            print("\n")
            descripcion = capturar_texto_multilinea("Descripción completa de la oferta")
            
            tec_detectadas = detectar_tecnologias(descripcion)
            print(f"\n🔍 Tecnologías detectadas automáticamente: {', '.join(tec_detectadas) if tec_detectadas else 'Ninguna'}")
            
            tec_adicionales = input("Agregar tecnologías adicionales separadas por coma (o Enter para mantener las detectadas): ").strip()
            if tec_adicionales:
                adicionales = [t.strip() for t in tec_adicionales.split(",") if t.strip()]
                tec_detectadas.extend(adicionales)
                tec_detectadas = list(dict.fromkeys(tec_detectadas))
            
            nueva_oferta = {
                "id": siguiente_id,
                "titulo": titulo,
                "empresa": empresa,
                "sector": sector,
                "subsector": subsector,
                "rol_categoria": rol_categoria,
                "ubicacion": ubicacion,
                "modalidad": modalidad,
                "nivel_experiencia": nivel_experiencia,
                "requisitos_tecnicos": tec_detectadas,
                "url": url,
                "descripcion_completa": descripcion,
                "fecha_recoleccion": datetime.now().strftime("%Y-%m-%d")
            }
            
            ofertas.append(nueva_oferta)
            guardar_ofertas(ofertas)
            print(f"\n✅ Oferta {siguiente_id} guardada con éxito en JSON y CSV.")
            
        elif opc == "2":
            print("\n--- Últimas 5 ofertas ingresadas ---")
            for of in ofertas[-5:]:
                print(f"[{of.get('id')}] {of.get('titulo')} - {of.get('empresa')} ({of.get('sector')})")
        elif opc == "3":
            print("\nSaliendo...")
            break
        else:
            print("Opción inválida.")


if __name__ == "__main__":
    menu_ingesta()
