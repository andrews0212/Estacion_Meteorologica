import os
import tempfile
from datetime import datetime


class ParquetWriter:
    """
    Gestiona la escritura de archivos Parquet.
    
    Parquet es un formato columnar comprimido ideal para Data Lakes.
    Ventajas:
    - Compresión eficiente (ocupa menos espacio que CSV)
    - Lectura rápida de columnas específicas
    - Preserva tipos de datos
    - Compatible con herramientas Big Data (Spark, Hive, etc.)
    """
    
    def __init__(self, table_name):
        """
        Inicializa el escritor de Parquet.
        
        Args:
            table_name: Nombre de la tabla (se usa para nombrar el archivo)
            
        Genera automáticamente:
        - Timestamp actual para el nombre del archivo
        - Nombre de archivo con patrón: {tabla}_{timestamp}.parquet
        - Ruta temporal (multiplataforma: /tmp en Linux, AppData\\Temp en Windows)
        """
        self.table_name = table_name
        
        # Generar timestamp para nombre único del archivo
        # Formato: 20251201231015 (AñoMesDíaHoraMinutoSegundo)
        self.timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Nombre del archivo: movie_20251201231015.parquet
        self.file_name = f"{table_name}_{self.timestamp}.parquet"
        
        # Guardar temporalmente en la carpeta temp del SO (multiplataforma)
        # En Linux: /tmp/, en Windows: C:\Users\...\AppData\Local\Temp\
        temp_dir = tempfile.gettempdir()
        self.local_path = os.path.join(temp_dir, self.file_name)
    
    def write(self, dataframe):
        """
        Guarda DataFrame de pandas en formato Parquet.
        
        Args:
            dataframe: DataFrame de pandas con los datos extraídos
            
        Returns:
            str: Ruta local donde se guardó el archivo
            
        El archivo se guarda con:
        - index=False: No guarda el índice de pandas como columna
        - Compresión por defecto (Snappy)
        
        Ejemplo:
            writer = ParquetWriter('movie')
            writer.write(df)
            # Crea: /tmp/movie_20251201231015.parquet
        """
        dataframe.to_parquet(self.local_path, index=False)
        return self.local_path
    
    def cleanup(self):
        """
        Elimina el archivo temporal.
        
        Se llama después de subir exitosamente a MinIO para liberar espacio.
        Es importante limpiar archivos temporales para evitar llenar el disco.
        """
        if os.path.exists(self.local_path):
            os.remove(self.local_path)
