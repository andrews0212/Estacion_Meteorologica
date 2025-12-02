"""Clase base para escritores de archivos.

Proporciona la interfaz abstracta para serializar DataFrames a disco.
"""

import os
import tempfile
from typing import Optional
import pandas as pd
from datetime import datetime
from abc import ABC, abstractmethod


class FileWriter(ABC):
    """Clase base para escritores de archivos.

    Proporciona la lógica común de nombre de fichero temporal y eliminación
    del archivo cuando ya no es necesario.
    """
    
    def __init__(self, table_name: str, extension: str):
        """
        Inicializa escritor.
        
        Args:
            table_name (str): Nombre de la tabla.
            extension (str): Extensión del archivo (csv, parquet, etc.).
        """
        self.table_name = table_name
        self.timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.file_name = f"{table_name}_bronce_{self.timestamp}.{extension}"
        self.local_path = os.path.join(tempfile.gettempdir(), self.file_name)
    
    @abstractmethod
    def write(self, dataframe: pd.DataFrame) -> str:
        """Escribe DataFrame a archivo.

        Debe ser implementado por subclases y retornar la ruta local del
        archivo generado.

        Args:
            dataframe (pandas.DataFrame): DataFrame a serializar.

        Returns:
            str: Ruta absoluta al archivo generado.

        Ejemplo::

            writer = CSVWriter('sensor_readings')
            path = writer.write(df)
            # path -> 'C:\\Windows\\Temp\\sensor_readings_bronce_20250101120000.csv'
        """
        pass
    
    def cleanup(self) -> None:
        """Elimina archivo temporal."""
        if os.path.exists(self.local_path):
            os.remove(self.local_path)
