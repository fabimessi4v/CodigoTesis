#!/usr/bin/env python3
"""
Punto de Entrada CLI: Ejecución del Pipeline ETL de Análisis Curricular.

Uso:
    python3 scripts/run_etl.py

Permite reconstruir la base de datos `data/processed/tesis_curricular.db`
directamente a partir de los insumos LaTeX y JSON situados en `data/raw/`.
"""

import sys
from pathlib import Path

# Añadir la raíz del repositorio al PYTHONPATH para importaciones absolutas
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.etl.pipeline import poblar_base_datos


def main():
    """Ejecuta el pipeline ETL y retorna el código de salida adecuado."""
    exito = poblar_base_datos()
    if not exito:
        print("\n❌ El pipeline ETL finalizó con inconsistencias.", file=sys.stderr)
        sys.exit(1)
    print("\n✅ Proceso completado exitosamente.")
    sys.exit(0)


if __name__ == "__main__":
    main()
