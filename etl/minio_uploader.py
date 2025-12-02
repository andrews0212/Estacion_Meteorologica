"""Gestión de subida de archivos a MinIO."""

from typing import Optional
from minio import Minio
from config import MinIOConfig


class MinIOUploader:
    """Gestiona subida de archivos a MinIO."""
    
    def __init__(self, minio_config: MinIOConfig):
        """
        Inicializa uploader.
        
        Args:
            minio_config: Configuración de MinIO
        """
        self.config = minio_config
        self.client = Minio(
            minio_config.endpoint,
            access_key=minio_config.access_key,
            secret_key=minio_config.secret_key,
            secure=False
        )
    
    def upload(self, local_path: str, table_name: str, file_name: str) -> str:
        """
        Sube archivo a MinIO.
        
        Args:
            local_path: Ruta local del archivo
            table_name: Nombre de la tabla
            file_name: Nombre del archivo
            
        Returns:
            Ruta completa en MinIO
        """
        object_name = f"{table_name}/{file_name}"
        self.client.fput_object(self.config.bucket, object_name, local_path)
        return f"{self.config.bucket}/{object_name}"

