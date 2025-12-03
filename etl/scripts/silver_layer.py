"""Script de limpieza para Silver layer - ejecución directa sin Jupyter."""

import os
import sys
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

# Add parent to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.minio_config import MinIOConfig
from etl.utils.minio_utils import MinIOUtils

def run_silver_layer():
    """Execute Silver layer cleaning using pandas (no PySpark)."""
    # Load MinIO configuration from config module
    config = MinIOConfig()
    minio = MinIOUtils(config.endpoint, config.access_key, config.secret_key)
    
    # Get bucket names
    bucket_bronze = config.bucket
    bucket_silver = config.silver_bucket
    
    # Create meteo-silver bucket if not exists
    minio.crear_bucket_si_no_existe(bucket_silver)
    
    # Load latest Bronce CSV
    archivo_reciente = minio.obtener_archivo_reciente_csv(bucket_bronze)
    
    if not archivo_reciente:
        print('⚠️ No hay archivos en Bronce')
        return False
    
    # Descargar archivo
    df = minio.descargar_csv(bucket_bronze, archivo_reciente)
    
    if df is None or df.empty:
        print('⚠️ No se pudo descargar archivo de Bronce')
        return False
    
    print(f'✅ Cargados {len(df)} registros desde {archivo_reciente}')
    
    # Clean data: drop unwanted columns
    drop_cols = ['pressure', 'uv_level', 'pm25', 'rain_raw', 'wind_raw', 'vibration', 'light']
    for col in drop_cols:
        if col in df.columns:
            df = df.drop(col, axis=1)
    
    # Remove duplicates
    df = df.drop_duplicates()
    
    print(f'✅ {len(df)} registros limpios')
    
    # Write to Silver bucket - UPDATE existing file or create with standard name
    tabla = archivo_reciente.split('_bronce_')[0] if '_bronce_' in archivo_reciente else 'datos'
    archivo_silver = f'{tabla}_silver.csv'  # Standard name without timestamp
    
    try:
        if minio.subir_dataframe(bucket_silver, archivo_silver, df):
            print(f'✅ {archivo_silver} actualizado en Silver')
            return True
        else:
            print(f'❌ Error subiendo archivo a Silver')
            return False
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_silver_layer()
    sys.exit(0 if success else 1)
