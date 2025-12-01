import subprocess


class MinIOUploader:
    """
    Gestiona la subida de archivos a MinIO (Object Storage).
    
    MinIO es compatible con S3 y se usa como Data Lake (capa bronze).
    Usa el cliente de línea de comandos 'mc' (MinIO Client) para subir archivos.
    """
    
    def __init__(self, minio_config):
        """
        Inicializa el uploader.
        
        Args:
            minio_config: Instancia de MinIOConfig con alias y bucket
        """
        self.config = minio_config
    
    def upload(self, local_path, table_name, file_name):
        """
        Sube archivo a MinIO usando el cliente 'mc'.
        
        Args:
            local_path: Ruta local del archivo (ej: /tmp/movie_20251201231015.parquet)
            table_name: Nombre de la tabla (se usa para crear carpeta en MinIO)
            file_name: Nombre del archivo (ej: movie_20251201231015.parquet)
            
        Returns:
            str: Ruta completa en MinIO donde se subió el archivo
            
        Estructura de carpetas en MinIO:
            mi_minio/meteo-bronze/movie/movie_20251201231015.parquet
            mi_minio/meteo-bronze/person/person_20251201231015.parquet
            
        El comando ejecutado es equivalente a:
            mc cp /tmp/movie_20251201231015.parquet mi_minio/meteo-bronze/movie/movie_20251201231015.parquet
            
        Raises:
            CalledProcessError: Si el comando 'mc' falla (MinIO no disponible, credenciales incorrectas, etc.)
        """
        # Construir ruta en MinIO: alias/bucket/tabla/archivo
        minio_path = f"{self.config.alias}/{self.config.bucket}/{table_name}/{file_name}"
        
        # Ejecutar comando: mc cp <origen> <destino>
        # check=True: Lanza excepción si el comando falla
        # capture_output=True: Captura stdout/stderr para evitar mostrar en consola
        subprocess.run(["mc", "cp", local_path, minio_path], check=True, capture_output=True)
        
        return minio_path
