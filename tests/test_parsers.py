"""
Suite de Pruebas Unitarias para Parsers Sintácticos y Limpieza de Texto.

Proyecto de Tesis USACH
Autor: Fabián Ibarra Norambuena
"""

import unittest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.etl.parsers import clean_latex


class TestParsers(unittest.TestCase):
    """Pruebas unitarias de limpieza y normalización sintáctica."""

    def test_clean_latex_ampersand_and_underscore(self):
        """Verifica el reemplazo correcto de entidades y escapes LaTeX."""
        raw = r"Arquitectura \& Organización \_ Computacional"
        cleaned = clean_latex(raw)
        self.assertEqual(cleaned, "Arquitectura y Organización _ Computacional")

    def test_clean_latex_formatting_commands(self):
        """Verifica la eliminación de comandos tipográficos como textbf, texttt."""
        raw = r"\textbf{Algoritmos} y \texttt{Estructuras de Datos}"
        cleaned = clean_latex(raw)
        self.assertEqual(cleaned, "Algoritmos y Estructuras de Datos")

    def test_clean_latex_environments(self):
        """Verifica la remoción de entornos \\begin y \\end."""
        raw = r"\begin{itemize}\item Redes de Datos \item Sistemas Operativos\end{itemize}"
        cleaned = clean_latex(raw)
        self.assertEqual(cleaned, "Redes de Datos Sistemas Operativos")

    def test_clean_latex_empty_and_whitespace(self):
        """Verifica el manejo de cadenas vacías y compactación de espacios."""
        self.assertEqual(clean_latex(""), "")
        self.assertEqual(clean_latex(None), "")
        self.assertEqual(clean_latex("  Ingeniería    de    Software   "), "Ingeniería de Software")


if __name__ == "__main__":
    unittest.main()
