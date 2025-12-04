"""Clase base para escritores de archivos.

Define interfaz abstracta para serialización de DataFrames a diferentes
formatos (CSV, Parquet, etc) en archivos temporales.
"""

import os
import tempfile
from typing import Optional
import pandas as pd
from datetime import datetime
from abc import ABC, abstractmethod


class FileWriter(ABC):
    """Clase base abstracta para escritores de archivos.
    
    Responsabilidades:
    - Generar nombres únicos de archivos con timestamp
    - Almacenar en carpeta temporal del sistema
    - Proporcionar interfaz de limpieza
    
    Las subclases deben implementar el método write() para format específico.
    """
    
    def __init__(self, table_name: str, extension: str):
        """
        Inicializa el escritor de archivos.
        
        Args:
            table_name: Nombre de la tabla (base para nombre del archivo)
            extension: Extensión del archivo (csv, parquet, json, etc.)
            
        Note:
            El archivo se guarda en la carpeta temporal del sistema con timestamp.
        """
        self.table_name = table_name
        self.timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.file_name = f"{table_name}_bronce_{self.timestamp}.{extension}"
        self.local_path = os.path.join(tempfile.gettempdir(), self.file_name)
    
    @abstractmethod
    def write(self, dataframe: pd.DataFrame) -> str:
        """
        Escribe DataFrame a archivo en formato específico.

        Debe ser implementado por subclases. Ejemplo: CSVWriter, ParquetWriter.

        Args:
            dataframe: DataFrame a serializar a disco

        Returns:
            str: Ruta absoluta al archivo generado
        """
        pass
    
    def cleanup(self) -> None:
        """Elimina el archivo temporal después de usar."""
        if os.path.exists(self.local_path):
            os.remove(self.local_path)
