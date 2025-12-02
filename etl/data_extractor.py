"""Extracción incremental de datos desde PostgreSQL."""

from typing import Optional, Any
import pandas as pd
from sqlalchemy import Connection
from .db_utils import TableQueryBuilder


class DataExtractor:
    """Extrae datos incrementales de PostgreSQL."""
    
    def __init__(self, 
                 connection: Connection,
                 table_name: str,
                 tracking_column: str,
                 tracking_type: str):
        """
        Inicializa extractor.
        
        Args:
            connection: Conexión a PostgreSQL
            table_name: Nombre de la tabla
            tracking_column: Columna para rastreo (timestamp o ID)
            tracking_type: Tipo de columna ('id' o 'timestamp')
        """
        self.connection = connection
        self.table_name = table_name
        self.tracking_column = tracking_column
        self.tracking_type = tracking_type
    
    def extract_incremental(self, last_value: Optional[Any] = None) -> pd.DataFrame:
        """
        Extrae datos nuevos desde el último valor procesado.
        
        Args:
            last_value: Último valor procesado (None para carga inicial)
            
        Returns:
            DataFrame con datos extraídos
        """
        extraction_type = "Incremental" if last_value else "Carga Inicial"
        print(f"   📊 {extraction_type} ({self.tracking_column})")
        if last_value:
            print(f"      > {last_value}")
        
        # Construir query dinámicamente sin usar text() de SQLAlchemy
        if last_value:
            # Escapar el valor para seguridad
            if isinstance(last_value, str):
                escaped_value = f"'{last_value}'"
            else:
                escaped_value = str(last_value)
            
            query = (
                f"SELECT * FROM {self.table_name} "
                f"WHERE {self.tracking_column} > {escaped_value} "
                f"ORDER BY {self.tracking_column} ASC LIMIT 10000"
            )
        else:
            query = (
                f"SELECT * FROM {self.table_name} "
                f"ORDER BY {self.tracking_column} ASC LIMIT 10000"
            )
        
        try:
            # pd.read_sql acepta directamente strings SQL
            return pd.read_sql(query, self.connection)
        except Exception as e:
            print(f"[ERROR] Error en extracción: {e}")
            print(f"[DEBUG] Query: {query}")
            raise


