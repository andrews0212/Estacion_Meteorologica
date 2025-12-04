"""Carga de archivos a MinIO.

Encapsula la funcionalidad de subida de archivos a MinIO, permitiendo
almacenamiento seguro de datos en capas (Bronze, Silver, Gold).
"""

from typing import Optional
from minio import Minio
from config import MinIOConfig


class MinIOUploader:
    """Gestor de carga de archivos a MinIO.
    
    Proporciona interfaz simple para subir archivos locales al bucket Bronze
    con organización automática por tabla.
    """
    
    def __init__(self, minio_config: MinIOConfig):
        """
        Inicializa el uploader de MinIO.
        
        Args:
            minio_config: Configuración de MinIO con credenciales y endpoint
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
        Sube un archivo local al bucket Bronze en MinIO.

        Estructura de carga: ``{bucket}/{table_name}/{file_name}``

        Args:
            local_path: Ruta local absoluta del archivo a subir
            table_name: Nombre de la tabla (usada como prefijo organizador)
            file_name: Nombre del archivo destino

        Returns:
            str: URI completa en MinIO
        """
        object_name = f"{table_name}/{file_name}"
        self.client.fput_object(self.config.bucket, object_name, local_path)
        return f"{self.config.bucket}/{object_name}"
