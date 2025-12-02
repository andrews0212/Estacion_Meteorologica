"""Gestión de tabla de control para rastreo de extracciones."""

from typing import Tuple, Optional, Any
import pandas as pd
from datetime import datetime
from sqlalchemy import Connection
from .db_utils import DatabaseUtils, ETLControlQueries


class ETLControlManager:
    """Gestiona tabla de control para rastreo de extracciones incrementales."""
    
    def __init__(self, connection: Connection):
        """
        Inicializa gestor de control.
        
        Args:
            connection: Conexión a PostgreSQL
        """
        self.connection = connection
    
    def initialize_table(self) -> None:
        """Crea tabla etl_control si no existe."""
        DatabaseUtils.execute_and_commit(
            self.connection,
            ETLControlQueries.CREATE_CONTROL_TABLE
        )
    
    def get_last_extracted_value(self, table_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Obtiene último valor extraído.
        
        Args:
            table_name: Nombre de la tabla
            
        Returns:
            (last_value, tracking_column) o (None, None) si no existe
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
            table_name: Nombre de la tabla
            value: Nuevo valor máximo extraído
            tracking_column: Nombre de columna de rastreo
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

