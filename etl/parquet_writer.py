import os
import tempfile
import pandas as pd
from datetime import datetime


class DataWriter:
    """
    Gestiona la escritura de archivos en formato CSV (sin problemas de nanosegundos).
    
    CSV es ideal para la capa Bronce porque:
    - Los timestamps se guardan como strings (sin problemas de nanosegundos)
    - Compatible con PySpark, Pandas y cualquier herramienta
    - Fácil de inspeccionar manualmente
    - Sin compresión Java (evita problemas de compatibilidad)
    """
    
    def __init__(self, table_name):
        """
        Inicializa el escritor de datos.
        
        Args:
            table_name: Nombre de la tabla (se usa para nombrar el archivo)
            
        Genera automáticamente:
        - Timestamp actual para el nombre del archivo
        - Nombre de archivo con patrón: {tabla}_bronce_{timestamp}.csv
        - Ruta temporal (multiplataforma)
        """
        self.table_name = table_name
        
        # Generar timestamp para nombre único del archivo
        # Formato: 20251201231015 (AñoMesDíaHoraMinutoSegundo)
        self.timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Nombre del archivo con identificador "bronce"
        self.file_name = f"{table_name}_bronce_{self.timestamp}.csv"
        
        # Guardar temporalmente en la carpeta temp del SO (multiplataforma)
        temp_dir = tempfile.gettempdir()
        self.local_path = os.path.join(temp_dir, self.file_name)
    
    def write(self, dataframe):
        """
        Guarda DataFrame de pandas en formato CSV.
        
        Args:
            dataframe: DataFrame de pandas con los datos extraídos
            
        Returns:
            str: Ruta local donde se guardó el archivo
            
        El archivo se guarda con:
        - index=False: No guarda el índice de pandas como columna
        - Timestamps como strings (sin problema de nanosegundos para PySpark)
        
        Ejemplo:
            writer = DataWriter('sensor_readings')
            writer.write(df)
            # Crea: /tmp/sensor_readings_bronce_20251202091819.csv
        """
        # Guardar como CSV (timestamps se convierten automáticamente a strings)
        dataframe.to_csv(self.local_path, index=False)
        return self.local_path
    
    def cleanup(self):
        """
        Elimina el archivo temporal.
        
        Se llama después de subir exitosamente a MinIO para liberar espacio.
        """
        if os.path.exists(self.local_path):
            os.remove(self.local_path)


# Mantener alias para compatibilidad con código antiguo
ParquetWriter = DataWriter
