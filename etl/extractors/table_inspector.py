"""Inspección de estructura de tablas en PostgreSQL.

Proporciona funcionalidad para:
- Obtener lista de todas las tablas
- Inspeccionar columnas y tipos de datos
- Detectar automáticamente la mejor columna para rastreo incremental
"""

from typing import List, Tuple, Optional
from sqlalchemy import Connection
from etl.utils import DatabaseUtils, TableQueryBuilder


class TrackingColumnDetector:
    """Detector automático de columnas para rastreo incremental.
    
    Busca inteligentemente la mejor columna para usar en extracción incremental,
    siguiendo orden de preferencia: timestamp > ID primario > columna 'id'.
    """
    
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
        Detecta la mejor columna para rastreo incremental.
        
        Prioridades (en orden):
        1. Timestamp (created_at, updated_at, timestamp, etc.)
        2. Clave primaria numérica (serial, integer, etc.)
        3. Columna 'id' numérica
        
        Args:
            columns: Lista de (nombre_columna, tipo_datos)
            connection: Conexión a base de datos para consultar metadatos
            table_name: Nombre de la tabla
            
        Returns:
            tuple: (nombre_columna, tipo_rastreo) o None si no detecta
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
    """Inspector de estructura de tablas PostgreSQL.
    
    Proporciona métodos para explorar:
    - Lista de tablas disponibles
    - Columnas y tipos de datos
    - Detección automática de columna de rastreo
    """
    
    def __init__(self, connection: Connection):
        """
        Inicializa el inspector.
        
        Args:
            connection: Conexión SQLAlchemy activa a PostgreSQL
        """
        self.connection = connection
    
    def get_all_tables(self) -> List[str]:
        """
        Obtiene lista de todas las tablas en esquema 'public'.
        
        Returns:
            List[str]: Nombres de tablas
        """
        tables = DatabaseUtils.fetch_all(
            self.connection,
            TableQueryBuilder.get_list_tables_query()
        )
        return [t[0] for t in tables]
    
    def get_columns(self, table_name: str) -> List[Tuple[str, str]]:
        """
        Obtiene columnas de una tabla con sus tipos de datos.
        
        Args:
            table_name: Nombre de la tabla
            
        Returns:
            List[Tuple]: Lista de (nombre_columna, tipo_dato)
        """
        query, params = TableQueryBuilder.get_columns_query(table_name)
        return DatabaseUtils.fetch_all(self.connection, query, params)
    
    def detect_tracking_column(self, table_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Detecta automáticamente la mejor columna para rastreo incremental.
        
        Args:
            table_name: Nombre de la tabla
            
        Returns:
            Tuple: (nombre_columna, tipo) o (None, None) si no detecta
        """
        columns = self.get_columns(table_name)
        result = TrackingColumnDetector.detect(columns, self.connection, table_name)
        return result if result else (None, None)
