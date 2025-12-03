"""Utilidades comunes para operaciones con MinIO.

Elimina redundancia en las operaciones de descarga, carga y procesamiento
de archivos CSV desde/hacia MinIO.
"""

import os
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from minio import Minio
import pandas as pd


class MinIOUtils:
    """Utilidades para operaciones comunes con MinIO."""
    
    def __init__(self, endpoint: str, access_key: str, secret_key: str):
        """
        Inicializa el cliente MinIO.
        
        Args:
            endpoint: Dirección de MinIO (ej: localhost:9000)
            access_key: Clave de acceso
            secret_key: Clave secreta
        """
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False
        )
    
    def crear_bucket_si_no_existe(self, bucket: str) -> bool:
        """
        Crea un bucket si no existe.
        
        Args:
            bucket: Nombre del bucket
            
        Returns:
            bool: True si se creó o ya existía
        """
        try:
            self.client.make_bucket(bucket)
            print(f'✅ Bucket {bucket} creado')
            return True
        except:
            print(f'✅ Bucket {bucket} ya existe')
            return True
    
    def obtener_archivo_reciente_csv(self, bucket: str, prefix: Optional[str] = None) -> Optional[str]:
        """
        Obtiene el archivo CSV más reciente de un bucket.
        
        Args:
            bucket: Nombre del bucket
            prefix: Prefijo opcional para filtrar
            
        Returns:
            Optional[str]: Nombre del archivo más reciente o None
        """
        try:
            objects = list(self.client.list_objects(bucket, prefix=prefix, recursive=True))
            archivos_csv = [obj.object_name for obj in objects if obj.object_name.endswith('.csv')]
            return sorted(archivos_csv)[-1] if archivos_csv else None
        except Exception as e:
            print(f'⚠️ Error obteniendo archivo reciente: {e}')
            return None
    
    def descargar_csv(self, bucket: str, objeto: str) -> Optional[pd.DataFrame]:
        """
        Descarga un archivo CSV desde MinIO y lo retorna como DataFrame.
        
        Args:
            bucket: Nombre del bucket
            objeto: Nombre del objeto en MinIO
            
        Returns:
            Optional[pd.DataFrame]: DataFrame con los datos o None si hay error
        """
        try:
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, f'{objeto}_{id(self)}.csv')
            
            self.client.fget_object(bucket, objeto, temp_file)
            df = pd.read_csv(temp_file)
            
            # Limpiar archivo temporal
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            return df
        except Exception as e:
            print(f'⚠️ Error descargando archivo: {e}')
            return None
    
    def subir_dataframe(self, bucket: str, objeto: str, df: pd.DataFrame) -> bool:
        """
        Sube un DataFrame como archivo CSV a MinIO.
        
        Args:
            bucket: Nombre del bucket
            objeto: Nombre del objeto en MinIO
            df: DataFrame a subir
            
        Returns:
            bool: True si se subió correctamente
        """
        try:
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, f'{objeto}_{id(df)}.csv')
            
            # Escribir DataFrame a CSV
            df.to_csv(temp_file, index=False, encoding='utf-8')
            
            # Subir a MinIO
            self.client.fput_object(bucket, objeto, temp_file)
            
            # Limpiar archivo temporal
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            return True
        except Exception as e:
            print(f'❌ Error subiendo archivo: {e}')
            return False
    
    def listar_archivos_csv(self, bucket: str, prefix: Optional[str] = None) -> list:
        """
        Lista todos los archivos CSV en un bucket.
        
        Args:
            bucket: Nombre del bucket
            prefix: Prefijo opcional para filtrar
            
        Returns:
            list: Lista de nombres de archivos CSV
        """
        try:
            objects = list(self.client.list_objects(bucket, prefix=prefix, recursive=True))
            return [obj.object_name for obj in objects if obj.object_name.endswith('.csv')]
        except Exception as e:
            print(f'⚠️ Error listando archivos: {e}')
            return []
