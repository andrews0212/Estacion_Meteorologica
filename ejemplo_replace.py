#!/usr/bin/env python
"""
Ejemplo de uso: Estrategia REPLACE en acción.
Demuestra cómo se usan limpieza_bronce.py y silver_layer.py con limpieza automática.
"""

import os
import sys

# Configurar variables de entorno
os.environ['PG_DB'] = os.environ.get('PG_DB', 'postgres')
os.environ['PG_USER'] = os.environ.get('PG_USER', 'postgres')
os.environ['PG_PASS'] = os.environ.get('PG_PASS', '1234')
os.environ['PG_HOST'] = os.environ.get('PG_HOST', '10.202.50.50')
os.environ['MINIO_ENDPOINT'] = os.environ.get('MINIO_ENDPOINT', 'localhost:9000')
os.environ['MINIO_ACCESS_KEY'] = os.environ.get('MINIO_ACCESS_KEY', 'minioadmin')
os.environ['MINIO_SECRET_KEY'] = os.environ.get('MINIO_SECRET_KEY', 'minioadmin')
os.environ['MINIO_BUCKET'] = os.environ.get('MINIO_BUCKET', 'meteo-bronze')

from config import MinIOConfig
from etl.limpieza_bronce import LimpiezaBronce
from etl.silver_layer import SilverLayer
from etl.silver_manager import SilverManager


def ejemplo_limpieza_bronce():
    """Ejemplo: Usar limpieza_bronce.py con estrategia REPLACE."""
    print("\n" + "="*80)
    print("📝 EJEMPLO 1: LimpiezaBronce con REPLACE")
    print("="*80)
    
    config = MinIOConfig()
    cleaner = LimpiezaBronce(config)
    
    # Procesar tabla
    resultado = cleaner.procesar_tabla('sensor_readings')
    
    if resultado:
        print(f"\n✅ Resultado:")
        print(f"   Tabla: {resultado['tabla']}")
        print(f"   Filas limpias: {resultado['filas_limpias']}")
        print(f"   Archivo: {resultado['archivo_silver']}")
        print(f"   Estrategia: {resultado['estrategia']}")
        print(f"   Versiones activas: {resultado['estadisticas'].get('total_versiones', 1)}")
    else:
        print(f"\n❌ Error en el procesamiento")


def ejemplo_silver_layer():
    """Ejemplo: Usar silver_layer.py con estrategia REPLACE."""
    print("\n" + "="*80)
    print("📝 EJEMPLO 2: SilverLayer con REPLACE")
    print("="*80)
    
    config = MinIOConfig()
    silver = SilverLayer(config)
    
    # Procesar tabla
    resultado = silver.process('sensor_readings')
    
    if resultado:
        print(f"\n✅ Resultado:")
        print(f"   Tabla: {resultado['tabla']}")
        print(f"   Filas limpias: {resultado['filas_limpias']}")
        print(f"   Estrategia: {resultado['estrategia']}")
        print(f"   Versiones activas: {resultado['estadisticas'].get('total_versiones', 1)}")
    else:
        print(f"\n❌ Error en el procesamiento")


def ejemplo_silver_manager():
    """Ejemplo: Usar SilverManager directamente para gestionar versiones."""
    print("\n" + "="*80)
    print("📝 EJEMPLO 3: SilverManager - Gestión de versiones")
    print("="*80)
    
    config = MinIOConfig()
    manager = SilverManager(config)
    
    # Ver todas las versiones
    versiones = manager.obtener_versiones_tabla('sensor_readings')
    print(f"\n📊 Versiones existentes: {len(versiones)}")
    for v in versiones:
        print(f"   - {v}")
    
    # Ver versión más reciente
    reciente = manager.obtener_archivo_reciente('sensor_readings')
    print(f"\n🔝 Versión más reciente: {reciente}")
    
    # Ver estadísticas
    stats = manager.obtener_estadisticas_tabla('sensor_readings')
    print(f"\n📈 Estadísticas:")
    print(f"   Total versiones: {stats.get('total_versiones', 0)}")
    print(f"   Espacio total: {stats.get('espacio_total_mb', 0)} MB")
    print(f"   Versión antigua: {stats.get('version_antigua', 'N/A')}")
    print(f"   Versión reciente: {stats.get('version_reciente', 'N/A')}")


def main():
    """Ejecutar ejemplos según parámetro."""
    if len(sys.argv) < 2:
        print("\n" + "="*80)
        print("🎯 EJEMPLOS DE USO - ESTRATEGIA REPLACE")
        print("="*80)
        print("\nUso: python ejemplo_replace.py [opcion]")
        print("\nOpciones:")
        print("  1 - Ejemplo LimpiezaBronce (limpia Bronce → Silver)")
        print("  2 - Ejemplo SilverLayer (limpia con PySpark)")
        print("  3 - Ejemplo SilverManager (gestión de versiones)")
        print("  all - Ejecutar todos los ejemplos")
        print("\nEjemplo:")
        print("  python ejemplo_replace.py 1")
        print("  python ejemplo_replace.py all")
        return
    
    opcion = sys.argv[1].lower()
    
    try:
        if opcion == '1':
            ejemplo_limpieza_bronce()
        elif opcion == '2':
            ejemplo_silver_layer()
        elif opcion == '3':
            ejemplo_silver_manager()
        elif opcion == 'all':
            ejemplo_limpieza_bronce()
            ejemplo_silver_layer()
            ejemplo_silver_manager()
        else:
            print(f"❌ Opción no válida: {opcion}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
