#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para limpiar la cache de ETL control."""

import sys
import os
from sqlalchemy import create_engine, text

def clear_etl_cache():
    """Elimina los registros de etl_control para forzar extracción completa."""
    try:
        # Leer configuración de variables de entorno o usar defaults
        pg_host = os.environ.get('PG_HOST', '10.202.50.50')
        pg_user = os.environ.get('PG_USER', 'postgres')
        pg_pass = os.environ.get('PG_PASS', 'postgres')
        pg_db = os.environ.get('PG_DB', 'basedatos')
        
        connection_url = f"postgresql://{pg_user}:{pg_pass}@{pg_host}/{pg_db}"
        print(f"Conectando a {pg_host}@{pg_db} con usuario {pg_user}...")
        
        # Crear engine de SQLAlchemy
        engine = create_engine(connection_url)
        
        # Conectar y ejecutar
        with engine.connect() as connection:
            # Limpiar toda la tabla de control para forzar extracción completa
            print("Limpiando tabla de control...")
            result = connection.execute(text("DELETE FROM etl_control"))
            rows_deleted = result.rowcount
            connection.commit()
            
            print(f"✅ {rows_deleted} registros eliminados de etl_control")
            
            # Verificar que está vacía
            result = connection.execute(text("SELECT COUNT(*) FROM etl_control"))
            count = result.scalar()
            print(f"✅ Registros restantes en etl_control: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error limpiando cache: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = clear_etl_cache()
    sys.exit(0 if success else 1)
