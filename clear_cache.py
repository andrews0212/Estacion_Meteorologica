#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para limpiar la cache de ETL."""

import sys
from sqlalchemy import create_engine
from config import DatabaseConfig
from etl.db_utils import DatabaseUtils


class ETLCacheCleaner:
    """Limpia la cache de ETL control."""
    
    def __init__(self, db_config: DatabaseConfig):
        """
        Inicializa limpiador.
        
        Args:
            db_config: Configuración de BD
        """
        self.engine = create_engine(db_config.connection_url)
    
    def clear(self) -> bool:
        """
        Limpia tabla de control.
        
        Returns:
            True si fue exitoso
        """
        try:
            with self.engine.connect() as connection:
                print("Limpiando tabla de control...")
                rows_deleted = DatabaseUtils.execute_and_commit(
                    connection,
                    "DELETE FROM etl_control"
                )
                print(f"✅ {rows_deleted} registros eliminados de etl_control")
                
                # Verificar
                count = DatabaseUtils.fetch_scalar(
                    connection,
                    "SELECT COUNT(*) FROM etl_control"
                )
                print(f"✅ Registros restantes en etl_control: {count}")
                return True
        
        except Exception as e:
            print(f"❌ Error limpiando cache: {e}")
            return False


def main() -> int:
    """Función principal."""
    try:
        db_config = DatabaseConfig()
        cleaner = ETLCacheCleaner(db_config)
        success = cleaner.clear()
        return 0 if success else 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

