"""Escritor de archivos CSV para DataFrames.

Serializa pandas DataFrames a archivos CSV en carpeta temporal del sistema.
"""

import pandas as pd
from .file_writer import FileWriter


class CSVWriter(FileWriter):
    """Escritor de DataFrames a archivos CSV.
    
    Hereda de FileWriter y proporciona serialización a formato CSV.
    """
    
    def __init__(self, table_name: str):
        """
        Inicializa el escritor CSV.
        
        Args:
            table_name: Nombre de la tabla (usado en nombre del archivo)
        """
        super().__init__(table_name, 'csv')
    
    def write(self, dataframe: pd.DataFrame) -> str:
        """
        Guarda un DataFrame como archivo CSV.
        
        Args:
            dataframe: DataFrame a serializar
            
        Returns:
            str: Ruta absoluta al archivo CSV generado
        """
        dataframe.to_csv(self.local_path, index=False)
        return self.local_path
