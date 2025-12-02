from minio import Minio


class MinIOUploader:
    """
    Gestiona la subida de archivos a MinIO (Object Storage).
    
    MinIO es compatible con S3 y se usa como Data Lake (capa bronze).
    Usa la biblioteca de Python 'minio' para subir archivos directamente.
    """
    
    def __init__(self, minio_config):
        """
        Inicializa el uploader.
        
        Args:
            minio_config: Instancia de MinIOConfig con alias, bucket, endpoint, access_key, secret_key
        """
        self.config = minio_config
        
        # Crear cliente MinIO
        self.client = Minio(
            minio_config.endpoint,
            access_key=minio_config.access_key,
            secret_key=minio_config.secret_key,
            secure=False  # usar HTTP en lugar de HTTPS
        )
    
    def upload(self, local_path, table_name, file_name):
        """
        Sube archivo a MinIO usando el cliente Python.
        
        Args:
            local_path: Ruta local del archivo (ej: C:\\Users\\...\\AppData\\Local\\Temp\\movie_20251201231015.parquet)
            table_name: Nombre de la tabla (se usa para crear carpeta en MinIO)
            file_name: Nombre del archivo (ej: movie_20251201231015.parquet)
            
        Returns:
            str: Ruta completa en MinIO donde se subió el archivo
            
        Estructura de carpetas en MinIO:
            meteo-bronze/movie/movie_20251201231015.parquet
            meteo-bronze/person/person_20251201231015.parquet
            
        Raises:
            Exception: Si hay error en la conexión o subida a MinIO
        """
        # Construir ruta en MinIO: tabla/archivo
        object_name = f"{table_name}/{file_name}"
        
        # Subir archivo
        self.client.fput_object(
            self.config.bucket,
            object_name,
            local_path
        )
        
        return f"{self.config.bucket}/{object_name}"
