"""Gestión de subida de archivos a MinIO.

Proporciona una pequeña envoltura sobre la librería ``minio`` para
subir archivos locales al bucket configurado en ``MinIOConfig``.
"""

from typing import Optional
from minio import Minio
from config import MinIOConfig


class MinIOUploader:
    """Gestiona subida de archivos a MinIO.

    Args:
        minio_config (config.minio_config.MinIOConfig): Instancia de configuración de MinIO.
    """
    
    def __init__(self, minio_config: MinIOConfig):
        """
        Inicializa uploader.
        
        Args:
            minio_config (MinIOConfig): Configuración de MinIO.
        """
        self.config = minio_config
        self.client = Minio(
            minio_config.endpoint,
            access_key=minio_config.access_key,
            secret_key=minio_config.secret_key,
            secure=False
        )
    
    def upload(self, local_path: str, table_name: str, file_name: str) -> str:
        """Sube archivo a MinIO y retorna la ruta en el bucket.

        Args:
            local_path (str): Ruta local del archivo.
            table_name (str): Nombre lógico de la tabla (se usa como prefijo).
            file_name (str): Nombre del archivo objetivo.

        Returns:
            str: Ruta completa en MinIO: ``{bucket}/{table_name}/{file_name}``.

        Ejemplo::

            uploader = MinIOUploader(cfg)
            uri = uploader.upload('C:/tmp/sensor.csv', 'sensor_readings', 'sensor_bronce_20250101.csv')
            # uri -> 'meteo-bronze/sensor_readings/sensor_bronce_20250101.csv'
        """
        object_name = f"{table_name}/{file_name}"
        self.client.fput_object(self.config.bucket, object_name, local_path)
        return f"{self.config.bucket}/{object_name}"
