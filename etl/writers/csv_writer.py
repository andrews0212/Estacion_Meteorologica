"""Escritor de archivos CSV."""

import pandas as pd
from .file_writer import FileWriter


class CSVWriter(FileWriter):
    """Escritor de archivos CSV.
    
    Serializa DataFrames a archivos CSV en la carpeta temporal del sistema.
    """
    
    def __init__(self, table_name: str):
        """Inicializa escritor CSV.
        
        Args:
            table_name (str): Nombre de la tabla (usado en nombre del fichero).
        """
        super().__init__(table_name, 'csv')
    
    def write(self, dataframe: pd.DataFrame) -> str:
        """Guarda DataFrame como CSV.
        
        Args:
            dataframe (pandas.DataFrame): DataFrame a serializar.
            
        Returns:
            str: Ruta absoluta al archivo generado.
        """
        dataframe.to_csv(self.local_path, index=False)
        return self.local_path
