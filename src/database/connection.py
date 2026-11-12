"""
Gestor de Conexiones a la Base de Datos SQLite del Proyecto.

Proporciona acceso centralizado y seguro a la base de datos relacional
`tesis_curricular.db`, asegurando el cumplimiento de llaves foráneas.
"""

import sqlite3
from typing import Optional
from pathlib import Path
from config.settings import DB_PATH


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """
    Obtiene una conexión activa a la base de datos SQLite.

    Habilita de manera explícita el soporte para integridad referencial
    (llaves foráneas) en SQLite mediante el comando PRAGMA foreign_keys = ON.

    Args:
        db_path (Optional[Path]): Ruta al archivo .db. Si es None, utiliza
            la ruta canónica configurada en config.settings.DB_PATH.

    Returns:
        sqlite3.Connection: Objeto de conexión con soporte para row_factory.
    """
    path_to_use = db_path or DB_PATH
    conn = sqlite3.connect(path_to_use)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn
