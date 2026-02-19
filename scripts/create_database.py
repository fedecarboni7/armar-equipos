#!/usr/bin/env python3
"""
Script para crear la base de datos SQLite con todas las tablas definidas en models.py
"""

import sys
from pathlib import Path

# Agregar el directorio raíz del proyecto al path para importar módulos
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from app.db.models import Base

def create_database():
    """Crea la base de datos SQLite con todas las tablas"""

    # Ruta de la base de datos SQLite
    db_path = project_root / "armar_equipos.db"

    # Crear la URL de la base de datos
    database_url = f"sqlite:///{db_path}"

    print(f"Creando base de datos en: {db_path}")

    # Crear el engine
    engine = create_engine(database_url, echo=True)  # echo=True para ver las consultas SQL

    # Crear todas las tablas
    print("Creando tablas...")
    Base.metadata.create_all(engine)

    print("¡Base de datos creada exitosamente!")
    print(f"Archivo de base de datos: {db_path}")

if __name__ == "__main__":
    create_database()
