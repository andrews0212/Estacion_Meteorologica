import os


class MinIOConfig:
    """
    Configuración de MinIO (Object Storage compatible con S3).
    
    MinIO se usa como capa bronze del Data Lake para almacenar
    archivos Parquet extraídos de PostgreSQL.
    
    Variables de entorno requeridas:
        - MINIO_ENDPOINT: URL del servidor MinIO (ej: localhost:9000)
        - MINIO_ACCESS_KEY: Clave de acceso (ej: minioadmin)
        - MINIO_SECRET_KEY: Clave secreta (ej: minioadmin)
        - MINIO_BUCKET: Nombre del bucket donde se guardarán los archivos
    """
    
    def __init__(self):
        """
        Inicializa la configuración leyendo variables de entorno.
        
        Ejemplo de configuración en run_scheduler.ps1:
            $env:MINIO_ENDPOINT = "localhost:9000"
            $env:MINIO_ACCESS_KEY = "minioadmin"
            $env:MINIO_SECRET_KEY = "minioadmin"
            $env:MINIO_BUCKET = "meteo-bronze"
        """
        # Endpoint del servidor MinIO
        self.endpoint = os.environ.get('MINIO_ENDPOINT', 'localhost:9000')
        
        # Credenciales de acceso
        self.access_key = os.environ.get('MINIO_ACCESS_KEY', 'minioadmin')
        self.secret_key = os.environ.get('MINIO_SECRET_KEY', 'minioadmin')
        
        # Nombre del bucket donde se almacenarán los archivos Parquet
        self.bucket = os.environ.get('MINIO_BUCKET', 'meteo-bronze')
