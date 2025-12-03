"""
Script para descargar el CSV de KPIs desde MinIO (Gold layer) a tu ordenador
para procesarlo en Power BI
"""

import os
from minio import Minio

# Configuración MinIO
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET_GOLD = "meteo-gold"

# Carpeta local donde guardar el archivo
CARPETA_LOCAL = "file"
os.makedirs(CARPETA_LOCAL, exist_ok=True)

# Conectar a MinIO
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

print("=" * 70)
print("📥 DESCARGANDO ARCHIVO GOLD DESDE MINIO")
print("=" * 70)

try:
    # Listar archivos en Gold
    print(f"\n🔍 Buscando archivos en {MINIO_BUCKET_GOLD}...")
    objects = list(minio_client.list_objects(MINIO_BUCKET_GOLD, recursive=True))
    
    archivos_csv = [obj.object_name for obj in objects if obj.object_name.endswith(".csv")]
    
    if archivos_csv:
        # Tomar el archivo más reciente
        archivo_gold = sorted(archivos_csv)[-1]
        print(f"✅ Archivo encontrado: {archivo_gold}")
        
        # Ruta local
        ruta_local = os.path.join(CARPETA_LOCAL, os.path.basename(archivo_gold))
        
        # Descargar
        print(f"\n📥 Descargando a: {os.path.abspath(ruta_local)}")
        minio_client.fget_object(MINIO_BUCKET_GOLD, archivo_gold, ruta_local)
        
        print(f"✅ Archivo descargado exitosamente")
        
        # Mostrar info del archivo
        file_size = os.path.getsize(ruta_local)
        print(f"\n" + "=" * 70)
        print(f"📊 Información del archivo:")
        print(f"📍 Nombre: {os.path.basename(ruta_local)}")
        print(f"📍 Ubicación: {os.path.abspath(ruta_local)}")
        print(f"📊 Tamaño: {file_size} bytes")
        print(f"=" * 70)
        
        # Mostrar primeras líneas del CSV
        print(f"\n📋 Primeras líneas del CSV:")
        print("-" * 70)
        with open(ruta_local, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i < 6:
                    print(line.rstrip())
                else:
                    break
        print("-" * 70)
        print(f"\n✅ Archivo listo para Power BI")
        
    else:
        print("⚠️ No hay archivos CSV en Gold")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
