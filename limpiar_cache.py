#!/usr/bin/env python
"""
Script para limpiar tabla de control y caché.
Simula una primera extracción borrando el histórico.
"""

import os
import sys
import shutil
from pathlib import Path

os.environ['PG_HOST'] = '10.202.50.50'
os.environ['PG_USER'] = 'postgres'
os.environ['PG_PASS'] = '1234'
os.environ['PG_DB'] = 'postgres'


def limpiar_tabla_control():
    """Elimina tabla de control en PostgreSQL."""
    print("1️⃣  Eliminando tabla etl_control...")
    
    try:
        from sqlalchemy import create_engine, text
        
        engine = create_engine('postgresql://postgres:1234@10.202.50.50:5432/postgres')
        with engine.connect() as conn:
            conn.execute(text('DROP TABLE IF EXISTS etl_control CASCADE'))
            conn.commit()
        
        engine.dispose()
        print("   ✅ etl_control eliminada")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def limpiar_cache_python():
    """Elimina directorios __pycache__."""
    print("\n2️⃣  Eliminando __pycache__...")
    
    eliminados = 0
    for pycache_dir in Path('.').rglob('__pycache__'):
        try:
            shutil.rmtree(pycache_dir)
            eliminados += 1
        except Exception as e:
            print(f"   ⚠️  {e}")
    
    print(f"   ✅ {eliminados} directorio(s) __pycache__ eliminado(s)")
    return True


def limpiar_archivos_pyc():
    """Elimina archivos .pyc."""
    print("\n3️⃣  Eliminando archivos .pyc...")
    
    eliminados = 0
    for pyc_file in Path('.').rglob('*.pyc'):
        try:
            pyc_file.unlink()
            eliminados += 1
        except Exception as e:
            print(f"   ⚠️  {e}")
    
    print(f"   ✅ {eliminados} archivo(s) .pyc eliminado(s)")
    return True


def main():
    """Ejecutar limpieza completa."""
    print("="*80)
    print("🧹 LIMPIEZA COMPLETA PARA PRIMERA EXTRACCIÓN")
    print("="*80)
    print()
    
    try:
        limpiar_tabla_control()
        limpiar_cache_python()
        limpiar_archivos_pyc()
        
        print()
        print("="*80)
        print("✅ LIMPIEZA COMPLETADA")
        print("="*80)
        print()
        print("📝 Próximos pasos:")
        print("   1. La tabla etl_control se creará automáticamente")
        print("   2. La siguiente ejecución será 'Carga Inicial'")
        print("   3. Se extraerán TODOS los datos de sensor_readings")
        print()
        print("Para ejecutar:")
        print("   python main.py")
        print("   # o")
        print("   .\\run_scheduler.ps1")
        print()
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
