"""Script de generación de KPI para Gold layer - ejecución directa sin Jupyter."""

import os
import sys
import tempfile
from datetime import datetime
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
MINIO_BUCKET_SILVER = "meteo-silver"
MINIO_BUCKET_GOLD = "meteo-gold"

def run_gold_layer():
    """Execute Gold layer KPI generation using pandas (no PySpark)."""
    minio_client = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False)
    
    # Create meteo-gold bucket if not exists
    try:
        minio_client.make_bucket(MINIO_BUCKET_GOLD)
        print(f'✅ Bucket {MINIO_BUCKET_GOLD} creado')
    except:
        print(f'✅ Bucket {MINIO_BUCKET_GOLD} ya existe')
    
    # Load latest Silver CSV
    try:
        objects = list(minio_client.list_objects(MINIO_BUCKET_SILVER, recursive=True))
        archivos_csv = [obj.object_name for obj in objects if obj.object_name.endswith('.csv')]
        if archivos_csv:
            archivo_silver = sorted(archivos_csv)[-1]
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, 'silver_temp.csv')
            minio_client.fget_object(MINIO_BUCKET_SILVER, archivo_silver, temp_file)
            
            # Use pandas instead of PySpark
            df = pd.read_csv(temp_file)
            print(f'✅ Cargados {len(df)} registros desde {archivo_silver}')
        else:
            print('⚠️ No hay archivos en Silver')
            return False
    except Exception as e:
        print(f'⚠️ Error: {e}')
        return False
    
    # Calculate per-sensor aggregations with pandas
    try:
        # Convert numeric columns
        numeric_cols = ['temperature', 'humidity']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        kpi_df = df.groupby('id').agg(
            lecturas=('id', 'count'),
            temp_avg=('temperature', 'mean'),
            temp_max=('temperature', 'max'),
            temp_min=('temperature', 'min'),
            temp_std=('temperature', 'std'),
            hum_avg=('humidity', 'mean'),
            hum_max=('humidity', 'max'),
            hum_min=('humidity', 'min')
        ).reset_index()
        
        print(f'✅ {len(kpi_df)} KPI generados')
    except Exception as e:
        print(f'⚠️ Error en agregaciones: {e}')
        import traceback
        traceback.print_exc()
        return False
    
    # Write KPI to Gold bucket
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    archivo_gold = f'metricas_kpi_gold_{timestamp}.csv'
    
    try:
        temp_file_local = os.path.join(tempfile.gettempdir(), archivo_gold)
        
        # Write using pandas with proper CSV format
        kpi_df.to_csv(temp_file_local, index=False, encoding='utf-8')
        
        minio_client.fput_object(MINIO_BUCKET_GOLD, archivo_gold, temp_file_local)
        print(f'✅ {archivo_gold} guardado en Gold')
        os.remove(temp_file_local)
        return True
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_gold_layer()
    sys.exit(0 if success else 1)
