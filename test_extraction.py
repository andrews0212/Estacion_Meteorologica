#!/usr/bin/env python
"""
Test: Verificar que la extracción incremental funciona correctamente.
"""

import os
import sys

os.environ['PG_DB'] = os.environ.get('PG_DB', 'postgres')
os.environ['PG_USER'] = os.environ.get('PG_USER', 'postgres')
os.environ['PG_PASS'] = os.environ.get('PG_PASS', '1234')
os.environ['PG_HOST'] = os.environ.get('PG_HOST', '10.202.50.50')

from config import DatabaseConfig
from sqlalchemy import create_engine
from etl.table_inspector import TableInspector
from etl.data_extractor import DataExtractor


def test_extraction():
    """Test de extracción incremental."""
    print("="*80)
    print("🧪 TEST: Extracción Incremental")
    print("="*80)
    
    try:
        # Conectar a BD
        db_config = DatabaseConfig()
        engine = create_engine(db_config.connection_url)
        connection = engine.connect()
        
        print(f"\n✅ Conectado a: {db_config.host}/{db_config.database}")
        
        # Inspeccionar tabla
        inspector = TableInspector(connection)
        tables = inspector.get_all_tables()
        print(f"\n📊 Tablas disponibles: {len(tables)}")
        for table in tables[:5]:
            print(f"   - {table}")
        
        # Detectar columna de rastreo
        table_name = 'sensor_readings'
        tracking_col = inspector.detect_tracking_column(table_name)
        print(f"\n🔍 Tabla: {table_name}")
        print(f"   Columna de rastreo: {tracking_col}")
        
        # Test de extracción sin parámetro (carga inicial)
        print(f"\n📥 Test 1: Carga inicial (sin last_value)")
        extractor = DataExtractor(connection, table_name, tracking_col, 'timestamp')
        df1 = extractor.extract_incremental(last_value=None)
        print(f"   ✅ {len(df1)} filas extraídas")
        
        if len(df1) > 0:
            last_val = df1[tracking_col].max()
            print(f"   Último valor: {last_val}")
            
            # Test con parámetro
            print(f"\n📥 Test 2: Extracción incremental (con last_value)")
            df2 = extractor.extract_incremental(last_value=last_val)
            print(f"   ✅ {len(df2)} filas extraídas")
            if len(df2) == 0:
                print(f"   (Normal: no hay datos después de {last_val})")
        
        connection.close()
        print(f"\n✅ TEST COMPLETADO EXITOSAMENTE")
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR EN TEST: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(test_extraction())
