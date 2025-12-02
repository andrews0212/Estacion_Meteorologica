import os
from typing import Optional
from .database_config import Config


class MinIOConfig(Config):
    """Configuración de MinIO (Object Storage S3-compatible)."""
    
    def __init__(self,
                 endpoint: Optional[str] = None,
                 access_key: Optional[str] = None,
                 secret_key: Optional[str] = None,
                 bucket: Optional[str] = None):
        """
        Inicializa configuración de MinIO.
        
        Lee de variables de entorno si no se proporcionan argumentos.
        """
        self.endpoint = endpoint or self.get_env('MINIO_ENDPOINT', 'localhost:9000')
        self.access_key = access_key or self.get_env('MINIO_ACCESS_KEY', 'minioadmin')
        self.secret_key = secret_key or self.get_env('MINIO_SECRET_KEY', 'minioadmin')
        self.bucket = bucket or self.get_env('MINIO_BUCKET', 'meteo-bronze')
    
    @property
    def silver_bucket(self) -> str:
        """Obtiene nombre del bucket Silver."""
        return self.bucket.replace('-bronze', '-silver')
    
    def __repr__(self) -> str:
        return f"MinIOConfig({self.endpoint}, bucket={self.bucket})"
