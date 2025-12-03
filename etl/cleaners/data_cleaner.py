"""Limpieza automática de datos (Bronce → Silver)."""

import os
import tempfile
import pandas as pd
from datetime import datetime
from typing import Optional
from minio import Minio
from config import MinIOConfig


class DataCleaner:
    """Limpia datos de Bronce y genera archivos en Silver."""
    
    def __init__(self, minio_config: MinIOConfig):
        """
        Inicializa limpiador.
        
        Args:
            minio_config: Configuración de MinIO
        """
        self.minio_config = minio_config
        self.client = Minio(
            minio_config.endpoint,
            access_key=minio_config.access_key,
            secret_key=minio_config.secret_key,
            secure=False
        )
        self.bucket_bronce = minio_config.bucket
        self.bucket_silver = minio_config.bucket.replace("-bronze", "-silver")
        
        # Crear bucket Silver si no existe
        self._ensure_silver_bucket()
    
    def _ensure_silver_bucket(self) -> None:
        """Crea bucket Silver si no existe."""
        try:
            if not self.client.bucket_exists(self.bucket_silver):
                self.client.make_bucket(self.bucket_silver)
                print(f"[OK] Bucket Silver creado: {self.bucket_silver}")
        except Exception as e:
            print(f"[ERROR] Error creando bucket Silver: {e}")
    
    def clean_table(self, table_name: str) -> int:
        """
        Limpia datos de una tabla de Bronce a Silver.
        
        Proceso:
        1. Listar archivos CSV de la tabla en Bronce
        2. Descargar y combinar los archivos
        3. Aplicar reglas de limpieza
        4. Guardar resultado en Silver
        5. Eliminar versiones antiguas (REPLACE)
        
        Args:
            table_name: Nombre de la tabla
            
        Returns:
            Cantidad de filas guardadas en Silver
        """
        print(f"\n{'='*80}")
        print(f"[PROCESO] Limpiando {table_name}")
        print(f"{'='*80}")
        
        # 1. Listar archivos
        archivos_csv = self._list_bronce_files(table_name)
        if not archivos_csv:
            print(f"[AVISO] No hay archivos para procesar")
            return 0
        
        # 2. Descargar y combinar
        df = self._download_and_combine(archivos_csv)
        if df is None or df.empty:
            print(f"[AVISO] No hay datos para limpiar")
            return 0
        
        # 3. Limpiar datos
        df = self._apply_cleaning(df)
        
        # 4. Guardar en Silver
        rows_saved = self._save_to_silver(table_name, df)
        
        # 5. Gestionar versiones
        self._manage_versions(table_name)
        
        return rows_saved
    
    def _list_bronce_files(self, table_name: str) -> list:
        """Lista TODOS los archivos CSV de una tabla en Bronce."""
        try:
            objects = self.client.list_objects(self.bucket_bronce, prefix=table_name, recursive=True)
            
            archivos = []
            for obj in objects:
                if obj.object_name.endswith('.csv') and '_bronce_' in obj.object_name:
                    archivos.append(obj.object_name)
            
            if archivos:
                archivos = sorted(archivos)
                print(f"[INFO] Encontrados {len(archivos)} archivo(s) de {table_name}")
                for archivo in archivos:
                    print(f"       - {archivo}")
            else:
                print(f"[INFO] No hay archivos de {table_name} en Bronce")
            
            return archivos
        except Exception as e:
            print(f"[ERROR] Error listando archivos: {e}")
            return []
    
    def _download_and_combine(self, archivos: list) -> Optional[pd.DataFrame]:
        """Descarga y combina TODOS los archivos CSV en un solo DataFrame."""
        print(f"[INFO] Combinando {len(archivos)} archivo(s)...")
        
        try:
            dataframes = []
            total_rows = 0
            
            for archivo in archivos:
                temp_dir = tempfile.gettempdir()
                temp_file = os.path.join(temp_dir, archivo.split('/')[-1])
                
                self.client.fget_object(self.bucket_bronce, archivo, temp_file)
                
                df = pd.read_csv(temp_file)
                dataframes.append(df)
                total_rows += len(df)
                
                print(f"[OK] Cargado: {archivo.split('/')[-1]} ({len(df)} filas)")
                
                try:
                    os.remove(temp_file)
                except:
                    pass
            
            if dataframes:
                # Combinar todos los DataFrames
                df_combined = pd.concat(dataframes, ignore_index=True)
                print(f"[OK] DataFrames combinados: {total_rows} filas totales")
                return df_combined
            
            return None
        except Exception as e:
            print(f"[ERROR] Error descargando/combinando: {e}")
            return None
    
    def _apply_cleaning(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica reglas de limpieza a los datos."""
        print(f"[INFO] Limpiando datos...")
        
        original_rows = len(df)
        
        # 1. Eliminar duplicados
        df_before = len(df)
        df = df.drop_duplicates()
        duplicates_removed = df_before - len(df)
        print(f"[OK] Duplicados eliminados: {df_before} → {len(df)}")
        
        # 2. Reemplazar outliers en temperatura
        if 'temperature' in df.columns:
            temp_data = df['temperature'].dropna()
            q1 = temp_data.quantile(0.25)
            q3 = temp_data.quantile(0.75)
            mediana = temp_data.quantile(0.50)
            iqr = q3 - q1
            
            lower_limit = q1 - (1.5 * iqr)
            upper_limit = q3 + (1.5 * iqr)
            
            outliers = ((df['temperature'] < lower_limit) | (df['temperature'] > upper_limit)).sum()
            df.loc[(df['temperature'] < lower_limit) | (df['temperature'] > upper_limit), 'temperature'] = mediana
            
            print(f"[OK] Outliers en temperature: {outliers} reemplazados con mediana ({mediana:.2f})")
        
        # 3. Eliminar columnas innecesarias
        cols_to_drop = ['uv_level', 'vibration', 'rain_raw', 'wind_raw', 'pressure']
        cols_dropped = [c for c in cols_to_drop if c in df.columns]
        df = df.drop(columns=cols_dropped)
        print(f"[OK] Columnas innecesarias eliminadas")
        
        # 4. Filtrar rangos válidos
        df_before = len(df)
        if 'temperature' in df.columns:
            df = df[(df['temperature'] >= 10) & (df['temperature'] <= 50)]
        if 'humidity' in df.columns:
            df = df[(df['humidity'] >= 0) & (df['humidity'] <= 100)]
        
        rows_filtered = df_before - len(df)
        print(f"[OK] Valores inválidos filtrados: {rows_filtered} eliminadas → {len(df)} filas finales")
        
        return df
    
    def _save_to_silver(self, table_name: str, df: pd.DataFrame) -> int:
        """Guarda datos limpios en Silver (actualiza si existe)."""
        print(f"[INFO] Guardando en Silver (estrategia REPLACE)...")
        
        try:
            # Generar nombre con timestamp
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            archivo_silver = f"{table_name}_silver_{timestamp}.csv"
            
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, archivo_silver)
            
            # Guardar como CSV
            df.to_csv(temp_file, index=False)
            
            # Subir a Silver
            self.client.fput_object(self.bucket_silver, archivo_silver, temp_file)
            
            rows = len(df)
            print(f"[EXITO] {table_name}: {rows} filas guardadas en Silver")
            print(f"[INFO] Archivo: {archivo_silver}")
            
            try:
                os.remove(temp_file)
            except:
                pass
            
            return rows
        except Exception as e:
            print(f"[ERROR] Error guardando en Silver: {e}")
            return 0
    
    def _manage_versions(self, table_name: str) -> None:
        """Gestiona versiones (REPLACE: mantiene solo la más reciente)."""
        print(f"[INFO] Eliminando versiones antiguas...")
        
        try:
            objects = self.client.list_objects(self.bucket_silver, prefix=table_name, recursive=True)
            
            versiones = []
            for obj in objects:
                if obj.object_name.endswith('.csv') and '_silver_' in obj.object_name:
                    versiones.append({
                        'nombre': obj.object_name,
                        'fecha': obj.last_modified
                    })
            
            if not versiones:
                print(f"[INFO] Primera versión en Silver (sin versiones anteriores)")
                return
            
            if len(versiones) > 1:
                versiones.sort(key=lambda x: x['fecha'])
                
                # Eliminar todas excepto la más reciente
                eliminadas = 0
                for v in versiones[:-1]:
                    try:
                        self.client.remove_object(self.bucket_silver, v['nombre'])
                        print(f"[OK] Eliminado: {v['nombre']}")
                        eliminadas += 1
                    except Exception as e:
                        print(f"[AVISO] Error eliminando: {e}")
                
                print(f"[OK] {table_name}: {eliminadas} archivos eliminados (mantiene: {versiones[-1]['nombre']})")
        except Exception as e:
            print(f"[AVISO] Error gestionando versiones: {e}")
