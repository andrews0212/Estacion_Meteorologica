"""
Módulo para limpiar datos de la capa Bronce y guardarlos en Silver.
Estrategia REPLACE: Mantiene solo el dataset más reciente.
"""

import os
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional
from minio import Minio
import pandas as pd
from etl.silver_manager import SilverManager


class LimpiezaBronce:
    """Limpia datos de la capa Bronce y los guarda en Silver."""
    
    def __init__(self, minio_config=None):
        """
        Inicializa la limpieza.
        
        Args:
            minio_config: Configuración de MinIO (MinIOConfig)
        """
        if minio_config is None:
            from config import MinIOConfig
            minio_config = MinIOConfig()
        
        self.minio_config = minio_config
        self.minio_endpoint = minio_config.endpoint
        self.minio_access = minio_config.access_key
        self.minio_secret = minio_config.secret_key
        self.bucket_bronce = minio_config.bucket
        self.bucket_silver = self.bucket_bronce.replace('-bronze', '-silver')
        
        # Crear cliente MinIO
        self.client = Minio(
            self.minio_endpoint,
            access_key=self.minio_access,
            secret_key=self.minio_secret,
            secure=False
        )
        
        # Gestor de Silver (para limpiar versiones antiguas)
        self.silver_manager = SilverManager(minio_config)
    
    def obtener_archivos_tabla(self, tabla):
        """Obtiene TODOS los archivos CSV de una tabla (puede haber múltiples extracciones)."""
        try:
            objects = self.client.list_objects(self.bucket_bronce, prefix=tabla, recursive=True)
            
            archivos = []
            for obj in objects:
                if obj.object_name.endswith('.csv') and '_bronce_' in obj.object_name:
                    archivos.append(obj.object_name)
            
            if not archivos:
                return None
            
            # Ordenar por timestamp (están en el nombre)
            archivos_ordenados = sorted(archivos)
            print(f"[INFO] Encontrados {len(archivos_ordenados)} archivo(s) de {tabla}")
            for archivo in archivos_ordenados:
                print(f"       - {archivo}")
            
            return archivos_ordenados
            
        except Exception as e:
            print(f"[ERROR] Error listando archivos: {e}")
            return None
    
    def descargar_csv(self, archivo):
        """Descarga el CSV de MinIO."""
        try:
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, archivo.split('/')[-1])
            
            self.client.fget_object(self.bucket_bronce, archivo, temp_file)
            return temp_file
            
        except Exception as e:
            print(f"[ERROR] Error descargando: {e}")
            return None
    
    def combinar_csvs(self, archivos):
        """Combina múltiples CSVs en un único DataFrame."""
        try:
            dataframes = []
            
            for archivo in archivos:
                temp_file = self.descargar_csv(archivo)
                if temp_file:
                    df = pd.read_csv(temp_file)
                    dataframes.append(df)
                    print(f"[OK] Cargado: {archivo.split('/')[-1]} ({len(df)} filas)")
            
            if not dataframes:
                return None
            
            # Combinar todos los DataFrames
            df_combinado = pd.concat(dataframes, ignore_index=True)
            print(f"[OK] DataFrames combinados: {len(df_combinado)} filas totales")
            
            return df_combinado
            
        except Exception as e:
            print(f"[ERROR] Error combinando CSVs: {e}")
            return None
    
    def limpiar_sensor_readings(self, df):
        """Aplica limpieza específica para sensor_readings."""
        filas_orig = len(df)
        
        # 1. Eliminar duplicados
        df = df.drop_duplicates()
        filas_sin_dup = len(df)
        print(f"[OK] Duplicados eliminados: {filas_orig} → {filas_sin_dup}")
        
        # 2. Reemplazar outliers en temperatura con mediana
        if 'temperature' in df.columns:
            temp = df['temperature'].dropna()
            q1 = temp.quantile(0.25)
            q3 = temp.quantile(0.75)
            mediana = temp.quantile(0.50)
            iqr = q3 - q1
            
            limite_inf = q1 - (1.5 * iqr)
            limite_sup = q3 + (1.5 * iqr)
            
            outliers = ((df['temperature'] < limite_inf) | (df['temperature'] > limite_sup)).sum()
            df.loc[(df['temperature'] < limite_inf) | (df['temperature'] > limite_sup), 'temperature'] = mediana
            print(f"[OK] Outliers en temperature: {outliers} reemplazados con mediana ({mediana:.2f})")
        
        # 3. Eliminar columnas innecesarias
        cols_eliminar = ['uv_level', 'vibration', 'rain_raw', 'wind_raw', 'pressure']
        for col in cols_eliminar:
            if col in df.columns:
                df = df.drop(col, axis=1)
        print(f"[OK] Columnas innecesarias eliminadas")
        
        # 4. Filtrar valores válidos
        filas_antes_filtrado = len(df)
        if 'temperature' in df.columns:
            df = df[(df['temperature'] >= 10) & (df['temperature'] <= 50)]
        
        if 'humidity' in df.columns:
            df = df[(df['humidity'] >= 0) & (df['humidity'] <= 100)]
        
        filas_filtradas = filas_antes_filtrado - len(df)
        print(f"[OK] Valores inválidos filtrados: {filas_filtradas} eliminadas → {len(df)} filas finales")
        
        return df
    
    def guardar_csv_como_parquet(self, df, tabla):
        """Guarda el DataFrame como CSV en Silver."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            archivo_silver = f"{tabla}_silver_{timestamp}.csv"
            
            # Guardar temporalmente
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, archivo_silver)
            
            df.to_csv(temp_file, index=False)
            
            # Subir a MinIO
            self.client.fput_object(self.bucket_silver, archivo_silver, temp_file)
            
            # Limpiar temporal
            try:
                os.remove(temp_file)
            except:
                pass
            
            return archivo_silver
            
        except Exception as e:
            print(f"[ERROR] Error guardando CSV: {e}")
            return None
    
    def procesar_tabla(self, tabla: str) -> Dict[str, Any]:
        """
        Procesa una tabla: obtiene CSVs de Bronce, limpia y guarda en Silver.
        Estrategia REPLACE: Elimina versiones antiguas automáticamente.
        
        Args:
            tabla: Nombre de la tabla
            
        Returns:
            Dict con resultado del procesamiento o None
        """
        try:
            print(f"\n{'='*80}")
            print(f"[PROCESO] Limpiando {tabla}")
            print(f"{'='*80}")
            
            # 1. Obtener TODOS los archivos de la tabla
            archivos = self.obtener_archivos_tabla(tabla)
            if not archivos:
                print(f"[AVISO] No hay archivos para procesar de {tabla}")
                return None
            
            # 2. Combinar todos los CSVs
            print(f"\n[INFO] Combinando {len(archivos)} archivo(s)...")
            df = self.combinar_csvs(archivos)
            if df is None or len(df) == 0:
                print(f"[ERROR] No se pudo combinar los datos")
                return None
            
            filas_limpias = len(df)
            
            # 3. Limpiar según tabla
            print(f"\n[INFO] Limpiando datos...")
            if tabla == 'sensor_readings':
                df = self.limpiar_sensor_readings(df)
            else:
                print(f"[AVISO] No hay limpieza específica para {tabla}")
            
            # 4. Guardar como CSV
            print(f"\n[INFO] Guardando en Silver (estrategia REPLACE)...")
            archivo_nuevo = self.guardar_csv_como_parquet(df, tabla)
            
            if not archivo_nuevo:
                return None
            
            # 5. Limpiar versiones antiguas (estrategia REPLACE)
            print(f"\n[INFO] Eliminando versiones antiguas...")
            self.silver_manager.limpiar_versiones_antiguas(tabla, mantener_actual=True)
            
            # 6. Obtener estadísticas
            stats = self.silver_manager.obtener_estadisticas_tabla(tabla)
            
            resultado = {
                'tabla': tabla,
                'filas_limpias': len(df),
                'archivo_silver': archivo_nuevo,
                'estrategia': 'REPLACE',
                'timestamp': datetime.now().isoformat(),
                'estadisticas': stats
            }
            
            print(f"\n[EXITO] {tabla}: {len(df)} filas guardadas en Silver")
            print(f"[INFO] Archivo: {archivo_nuevo}")
            print(f"[INFO] Versiones activas: {stats.get('total_versiones', 1)}")
            
            return resultado
            
        except Exception as e:
            print(f"[ERROR] Error procesando {tabla}: {e}")
            import traceback
            traceback.print_exc()
            return None
