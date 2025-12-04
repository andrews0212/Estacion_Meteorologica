import os
from typing import Optional
from .database_config import Config


class MinIOConfig(Config):
    """Configuración de MinIO (almacenamiento de objetos compatible con S3).
    
    MinIO proporciona almacenamiento escalable de objetos para datos en las
    tres capas: Bronze (datos brutos), Silver (limpio) y Gold (KPIs).
    """
    
    def __init__(self,
                 endpoint: Optional[str] = None,
                 access_key: Optional[str] = None,
                 secret_key: Optional[str] = None,
                 bucket: Optional[str] = None):
        """
        Inicializa la configuración de MinIO.
        
        Lee credenciales desde variables de entorno si no se proporcionan:
        - MINIO_ENDPOINT (default: localhost:9000)
        - MINIO_ACCESS_KEY (default: minioadmin)
        - MINIO_SECRET_KEY (default: minioadmin)
        - MINIO_BUCKET (default: meteo-bronze)
        - MINIO_SECURE (default: false)
        
        Args:
            endpoint: Dirección y puerto de MinIO
            access_key: Clave de acceso
            secret_key: Clave secreta
            bucket: Nombre del bucket Bronze
        """
        self.endpoint = endpoint or self.get_env('MINIO_ENDPOINT', 'localhost:9000')
        self.access_key = access_key or self.get_env('MINIO_ACCESS_KEY', 'minioadmin')
        self.secret_key = secret_key or self.get_env('MINIO_SECRET_KEY', 'minioadmin')
        self.bucket = bucket or self.get_env('MINIO_BUCKET', 'meteo-bronze')
        self.secure = self.get_env('MINIO_SECURE', 'false').lower() == 'true'
    
    @property
    def silver_bucket(self) -> str:
        """
        Obtiene nombre del bucket Silver automáticamente.
        
        Reemplaza '-bronze' por '-silver' en el nombre del bucket.
        
        Returns:
            str: Nombre del bucket Silver (ej: 'meteo-silver')
        """
        return self.bucket.replace('-bronze', '-silver')
    
    def __repr__(self) -> str:
        """Representación de la configuración."""
        return f"MinIOConfig({self.endpoint}, bucket={self.bucket})"
