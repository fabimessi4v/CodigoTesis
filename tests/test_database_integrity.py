"""
Suite de Pruebas de Integridad de la Base de Datos y Consistencia Curricular.

Proyecto de Tesis:
"Método computacional basado en procesamiento de lenguaje natural para analizar la
alineación curricular de Ingeniería Informática en Chile con estándares ACM/IEEE y
necesidades de la industria"
Autor: Fabián Ibarra Norambuena (USACH)

Verifica que el estado de la base de datos `tesis_curricular.db` cumpla de forma
estricta con todas las hipótesis de datos y reglas de negocio del informe escrito.
"""

import unittest
import sqlite3
import sys
from pathlib import Path

# Configurar ruta del proyecto
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import DB_PATH
from src.database.connection import get_connection


class TestDatabaseIntegrity(unittest.TestCase):
    """Pruebas de integridad referencial y conteos de datos de la tesis."""

    def setUp(self):
        """Verifica que la base de datos exista antes de cada prueba."""
        self.assertTrue(DB_PATH.exists(), f"La base de datos {DB_PATH} debe existir.")
        self.conn = get_connection(DB_PATH)

    def tearDown(self):
        """Cierra la conexión al finalizar cada prueba."""
        self.conn.close()

    def test_foreign_keys_integrity(self):
        """Audita que no existan inconsistencias de claves foráneas en ninguna tabla."""
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA foreign_key_check;")
        fk_violations = cursor.fetchall()
        self.assertEqual(len(fk_violations), 0, f"Violaciones de Foreign Keys detectadas: {fk_violations}")

    def test_taxonomia_acm_count(self):
        """Verifica que existan exactamente las 23 áreas de conocimiento ACM unificadas."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM taxonomia_acm;")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 23, "Deben existir exactamente 23 áreas de conocimiento ACM catalogadas.")

    def test_programas_y_universidades_count(self):
        """Verifica el número de universidades (15) y programas evaluados (16)."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM universidades;")
        uni_count = cursor.fetchone()[0]
        self.assertEqual(uni_count, 15, "Deben existir 15 universidades registradas.")

        cursor.execute("SELECT COUNT(*) FROM programas;")
        prog_count = cursor.fetchone()[0]
        self.assertEqual(prog_count, 16, "Deben existir 16 programas académicos registrados.")

    def test_perfiles_egreso_no_vacios(self):
        """Verifica que los 16 programas cuenten con su texto oficial de perfil de egreso."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM programas WHERE LENGTH(TRIM(perfil_egreso_oficial)) > 50;")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 16, "Los 16 programas deben tener su perfil oficial de egreso cargado (>50 caracteres).")

    def test_asignaturas_ground_truth_count(self):
        """Verifica que existan exactamente 746 asignaturas curriculares y 100% etiquetadas."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM asignaturas;")
        total_asig = cursor.fetchone()[0]
        self.assertEqual(total_asig, 746, f"Se esperaban 746 asignaturas, encontradas: {total_asig}")

        cursor.execute("SELECT COUNT(*) FROM asignaturas WHERE codigo_acm IS NULL;")
        sin_acm = cursor.fetchone()[0]
        self.assertEqual(sin_acm, 0, "No debe existir ninguna asignatura sin código ACM asignado (Ground Truth).")

    def test_ofertas_laborales_estratificacion(self):
        """Verifica la muestra de 200 vacantes y su estratificación 100 TI / 100 No-TI."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ofertas_laborales;")
        total_ofertas = cursor.fetchone()[0]
        self.assertEqual(total_ofertas, 200, f"Se esperaban 200 ofertas laborales, encontradas: {total_ofertas}")

        cursor.execute("SELECT COUNT(*) FROM ofertas_laborales WHERE sector = 'TI';")
        ti_count = cursor.fetchone()[0]
        self.assertEqual(ti_count, 100, "Deben existir exactamente 100 ofertas del sector TI.")

        cursor.execute("SELECT COUNT(*) FROM ofertas_laborales WHERE sector = 'No-TI';")
        noti_count = cursor.fetchone()[0]
        self.assertEqual(noti_count, 100, "Deben existir exactamente 100 ofertas de sectores productivos No-TI.")


if __name__ == "__main__":
    unittest.main()
