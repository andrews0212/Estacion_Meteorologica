"""Gestión de tabla de control para rastreo de extracciones."""

from typing import Tuple, Optional, Any
import pandas as pd
from datetime import datetime
from sqlalchemy import Connection
from etl.utils import DatabaseUtils, ETLControlQueries


class ETLControlManager:
    """Gestiona tabla de control para rastreo de extracciones incrementales.
    
    La tabla ``etl_control`` almacena el último valor extraído de cada tabla,
    permitiendo reiniciar extracciones desde el último punto procesado.
    """
    
    def __init__(self, connection: Connection):
        """
        Inicializa gestor de control.
        
        Args:
            connection (sqlalchemy.Connection): Conexión a PostgreSQL.
        """
        self.connection = connection
    
    def initialize_table(self) -> None:
        """Crea tabla ``etl_control`` si no existe."""
        DatabaseUtils.execute_and_commit(
            self.connection,
            ETLControlQueries.CREATE_CONTROL_TABLE
        )
    
    def get_last_extracted_value(self, table_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Obtiene último valor extraído.
        
        Args:
            table_name (str): Nombre de la tabla.
            
        Returns:
            Tuple[Optional[str], Optional[str]]: Tupla ``(last_value, tracking_column)`` 
            o ``(None, None)`` si no existe registro.
        """
        result = DatabaseUtils.fetch_one(
            self.connection,
            ETLControlQueries.GET_LAST_VALUE,
            {"table_name": table_name}
        )
        return (result[0], result[1]) if result else (None, None)
    
    def update_last_extracted_value(self, 
                                   table_name: str,
                                   value: Any,
                                   tracking_column: str) -> None:
        """
        Actualiza último valor extraído (UPSERT).
        
        Args:
            table_name (str): Nombre de la tabla.
            value (Any): Nuevo valor máximo extraído (numérico o timestamp).
            tracking_column (str): Nombre de columna de rastreo.
        """
        # Convertir timestamps a string ISO
        if isinstance(value, (pd.Timestamp, datetime)):
            value_str = value.isoformat()
        else:
            value_str = str(value)
        
        DatabaseUtils.execute_and_commit(
            self.connection,
            ETLControlQueries.UPSERT_LAST_VALUE,
            {
                "table_name": table_name,
                "val": value_str,
                "col": tracking_column
            }
        )
