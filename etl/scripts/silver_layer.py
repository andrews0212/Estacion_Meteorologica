"""Script de limpieza para Silver layer - ejecución directa sin Jupyter."""

import os
import sys
import tempfile
import csv
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from minio import Minio
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

# MinIO Configuration
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET_BRONCE = os.environ.get("MINIO_BUCKET", "meteo-bronze")
MINIO_BUCKET_SILVER = "meteo-silver"

def run_silver_layer():
    """Execute Silver layer cleaning using pandas (no PySpark)."""
    minio_client = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False)
    
    # Create meteo-silver bucket if not exists
    try:
        minio_client.make_bucket(MINIO_BUCKET_SILVER)
        print(f'✅ Bucket {MINIO_BUCKET_SILVER} creado')
    except:
        print(f'✅ Bucket {MINIO_BUCKET_SILVER} ya existe')
    
    # Load latest Bronce CSV
    archivo_reciente = None
    try:
        objects = list(minio_client.list_objects(MINIO_BUCKET_BRONCE, recursive=True))
        archivos_csv = [obj.object_name for obj in objects if obj.object_name.endswith('.csv')]
        if archivos_csv:
            archivo_reciente = sorted(archivos_csv)[-1]
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, 'bronce_temp.csv')
            minio_client.fget_object(MINIO_BUCKET_BRONCE, archivo_reciente, temp_file)
            
            # Use pandas instead of PySpark
            df = pd.read_csv(temp_file)
            print(f'✅ Cargados {len(df)} registros desde {archivo_reciente}')
        else:
            print('⚠️ No hay archivos en Bronce')
            df = pd.DataFrame()
    except Exception as e:
        print(f'⚠️ Error: {e}')
        return False
    
    # Clean data: drop unwanted columns
    drop_cols = ['pressure', 'uv_level', 'pm25', 'rain_raw', 'wind_raw', 'vibration', 'light']
    for col in drop_cols:
        if col in df.columns:
            df = df.drop(col, axis=1)
    
    # Remove duplicates
    df = df.drop_duplicates()
    
    print(f'✅ {len(df)} registros limpios')
    
    # Write to Silver bucket - UPDATE existing file or create with standard name
    tabla = archivo_reciente.split('_bronce_')[0] if archivo_reciente and '_bronce_' in archivo_reciente else 'datos'
    archivo_silver = f'{tabla}_silver.csv'  # Standard name without timestamp
    
    try:
        temp_file_local = os.path.join(tempfile.gettempdir(), archivo_silver)
        
        # Write using pandas with proper CSV format
        df.to_csv(temp_file_local, index=False, encoding='utf-8')
        
        # Upload to MinIO - will overwrite if exists
        minio_client.fput_object(MINIO_BUCKET_SILVER, archivo_silver, temp_file_local)
        print(f'✅ {archivo_silver} actualizado en Silver')
        os.remove(temp_file_local)
        return True
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_silver_layer()
    sys.exit(0 if success else 1)
