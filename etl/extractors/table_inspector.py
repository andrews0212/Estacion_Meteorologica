"""Inspección de estructuras de tablas en PostgreSQL."""

from typing import List, Tuple, Optional
from sqlalchemy import Connection
from etl.utils import DatabaseUtils, TableQueryBuilder


class TrackingColumnDetector:
    """Detecta automáticamente la mejor columna para rastreo."""
    
    # Prioridad 1: Columnas timestamp
    TIMESTAMP_CANDIDATES = ['created_at', 'updated_at', 'timestamp', 'fecha_registro', 'last_update']
    
    @staticmethod
    def is_numeric_type(col_type: str) -> bool:
        """Verifica si tipo es numérico."""
        return any(t in col_type.lower() for t in ['int', 'serial', 'numeric'])
    
    @staticmethod
    def is_timestamp_type(col_type: str) -> bool:
        """Verifica si tipo es timestamp."""
        return 'timestamp' in col_type.lower()
    
    @staticmethod
    def detect(columns: List[Tuple[str, str]], 
               connection: Connection,
               table_name: str) -> Optional[Tuple[str, str]]:
        """
        Detecta mejor columna para rastreo.
        
        Prioridades:
        1. Timestamp (created_at, updated_at, etc.)
        2. PRIMARY KEY numérico
        3. Columna 'id' numérica
        
        Returns:
            (column_name, column_type) o None
        """
        # 1. Buscar timestamp
        for col_name, col_type in columns:
            if (col_name.lower() in TrackingColumnDetector.TIMESTAMP_CANDIDATES or
                TrackingColumnDetector.is_timestamp_type(col_type)):
                return col_name, 'timestamp'
        
        # 2. Buscar PRIMARY KEY numérico
        pk_col = TrackingColumnDetector._get_primary_key(connection, table_name)
        if pk_col:
            for col_name, col_type in columns:
                if col_name == pk_col and TrackingColumnDetector.is_numeric_type(col_type):
                    return col_name, 'id'
        
        # 3. Buscar 'id'
        for col_name, col_type in columns:
            if col_name.lower() == 'id' and TrackingColumnDetector.is_numeric_type(col_type):
                return col_name, 'id'
        
        return None
    
    @staticmethod
    def _get_primary_key(connection: Connection, table_name: str) -> Optional[str]:
        """Obtiene nombre de PRIMARY KEY."""
        result = DatabaseUtils.fetch_one(
            connection,
            *TableQueryBuilder.get_primary_key_query(table_name)
        )
        return result[0] if result else None


class TableInspector:
    """Inspecciona estructura de tablas PostgreSQL."""
    
    def __init__(self, connection: Connection):
        """
        Inicializa inspector.
        
        Args:
            connection: Conexión a PostgreSQL
        """
        self.connection = connection
    
    def get_all_tables(self) -> List[str]:
        """
        Obtiene lista de todas las tablas.
        
        Returns:
            Lista de nombres de tablas
        """
        tables = DatabaseUtils.fetch_all(
            self.connection,
            TableQueryBuilder.get_list_tables_query()
        )
        return [t[0] for t in tables]
    
    def get_columns(self, table_name: str) -> List[Tuple[str, str]]:
        """
        Obtiene columnas con tipos de datos.
        
        Args:
            table_name: Nombre de la tabla
            
        Returns:
            Lista de (column_name, data_type)
        """
        query, params = TableQueryBuilder.get_columns_query(table_name)
        return DatabaseUtils.fetch_all(self.connection, query, params)
    
    def detect_tracking_column(self, table_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Detecta mejor columna para rastreo.
        
        Returns:
            (column_name, column_type) o (None, None)
        """
        columns = self.get_columns(table_name)
        result = TrackingColumnDetector.detect(columns, self.connection, table_name)
        return result if result else (None, None)
