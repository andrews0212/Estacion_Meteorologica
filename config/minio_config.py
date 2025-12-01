import os


class MinIOConfig:
    """
    Configuración de MinIO (Object Storage compatible con S3).
    
    MinIO se usa como capa bronze del Data Lake para almacenar
    archivos Parquet extraídos de PostgreSQL.
    
    Variables de entorno requeridas:
        - MINIO_ALIAS: Alias configurado con el cliente 'mc' (ej: mi_minio)
        - MINIO_BUCKET: Nombre del bucket donde se guardarán los archivos
    """
    
    def __init__(self):
        """
        Inicializa la configuración leyendo variables de entorno.
        
        El alias debe estar previamente configurado con el comando:
            mc alias set mi_minio http://localhost:9000 minioadmin minioadmin
        
        El bucket debe existir o crearse con:
            mc mb mi_minio/meteo-bronze
        """
        # Alias de MinIO configurado con el cliente 'mc'
        self.alias = os.environ.get('MINIO_ALIAS', 'myminio')
        
        # Nombre del bucket donde se almacenarán los archivos Parquet
        self.bucket = os.environ.get('MINIO_BUCKET', 'meteo-bronze')
