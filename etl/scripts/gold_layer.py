"""Script de generación de KPI para Gold layer - ejecución directa sin Jupyter."""

import os
import sys
import pandas as pd
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

# Add parent to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.minio_config import MinIOConfig
from etl.utils.minio_utils import MinIOUtils

def run_gold_layer():
    """Execute Gold layer KPI generation using pandas (no PySpark)."""
    # Load MinIO configuration from config module
    config = MinIOConfig()
    minio = MinIOUtils(config.endpoint, config.access_key, config.secret_key)
    
    # Get bucket names
    bucket_silver = config.silver_bucket
    bucket_gold = config.bucket.replace('-bronze', '-gold')
    
    # Create meteo-gold bucket if not exists
    minio.crear_bucket_si_no_existe(bucket_gold)
    
    # Load latest Silver CSV
    archivo_silver = minio.obtener_archivo_reciente_csv(bucket_silver)
    
    if not archivo_silver:
        print('⚠️ No hay archivos en Silver')
        return False
    
    # Descargar archivo
    df = minio.descargar_csv(bucket_silver, archivo_silver)
    
    if df is None or df.empty:
        print('⚠️ No se pudo descargar archivo de Silver')
        return False
    
    print(f'✅ Cargados {len(df)} registros desde {archivo_silver}')
    
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
    
    # Write KPI to Gold bucket - UPDATE existing file or create with standard name
    archivo_gold = 'metricas_kpi_gold.csv'  # Standard name without timestamp
    
    try:
        if minio.subir_dataframe(bucket_gold, archivo_gold, kpi_df):
            print(f'✅ {archivo_gold} actualizado en Gold')
            return True
        else:
            print(f'❌ Error subiendo archivo a Gold')
            return False
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_gold_layer()
    sys.exit(0 if success else 1)
