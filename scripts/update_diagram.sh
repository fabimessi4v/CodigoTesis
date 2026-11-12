#!/usr/bin/env bash
# =============================================================================
# Script de Automatización: Generación y Actualización de Diagramas de Arquitectura
# Proyecto de Tesis USACH
# Autor: Fabián Ibarra Norambuena
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🎨 Ejecutando generador de diagramas de arquitectura..."
cd "$PROJECT_ROOT"
python3 "$PROJECT_ROOT/src/visualization/diagram_generator.py"
echo "✅ Diagramas actualizados en src/visualization/"
