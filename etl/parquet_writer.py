"""Gestión de escritura de archivos de datos."""

import os
import tempfile
from typing import Optional
import pandas as pd
from datetime import datetime
from abc import ABC, abstractmethod


class FileWriter(ABC):
    """Clase base para escritores de archivos."""
    
    def __init__(self, table_name: str, extension: str):
        """
        Inicializa escritor.
        
        Args:
            table_name: Nombre de la tabla
            extension: Extensión del archivo (csv, parquet, etc.)
        """
        self.table_name = table_name
        self.timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.file_name = f"{table_name}_bronce_{self.timestamp}.{extension}"
        self.local_path = os.path.join(tempfile.gettempdir(), self.file_name)
    
    @abstractmethod
    def write(self, dataframe: pd.DataFrame) -> str:
        """Escribe DataFrame a archivo."""
        pass
    
    def cleanup(self) -> None:
        """Elimina archivo temporal."""
        if os.path.exists(self.local_path):
            os.remove(self.local_path)


class CSVWriter(FileWriter):
    """Escritor de archivos CSV."""
    
    def __init__(self, table_name: str):
        """Inicializa escritor CSV."""
        super().__init__(table_name, 'csv')
    
    def write(self, dataframe: pd.DataFrame) -> str:
        """Guarda DataFrame como CSV."""
        dataframe.to_csv(self.local_path, index=False)
        return self.local_path


class ParquetWriter(FileWriter):
    """Escritor de archivos Parquet."""
    
    def __init__(self, table_name: str):
        """Inicializa escritor Parquet."""
        super().__init__(table_name, 'parquet')
    
    def write(self, dataframe: pd.DataFrame) -> str:
        """Guarda DataFrame como Parquet."""
        dataframe.to_parquet(self.local_path, index=False)
        return self.local_path


# Alias para compatibilidad
DataWriter = CSVWriter

