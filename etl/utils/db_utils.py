"""Utilidades para operaciones de base de datos y construcción de queries SQL.

Encapsula operaciones comunes de ejecución de queries y construcción de sentencias SQL
usadas por el pipeline ETL para inspección de tablas y extracción incremental.

Proporciona:
- Ejecución de queries con manejo robusto de errores
- Métodos para fetch (uno, todos, escalar)
- Constructor de queries reutilizables para operaciones típicas
"""

from typing import List, Tuple, Optional, Any
from sqlalchemy import text, Connection
from sqlalchemy.sql import bindparam


class DatabaseUtils:
    """Métodos utilitarios reutilizables para operaciones de base de datos.

    Wrapper sobre SQLAlchemy que proporciona:
    - Ejecución de queries con parámetros nombrados
    - Métodos fetch convenientes (uno, todos, escalar)
    - Manejo de errores y trazas para debugging
    """
    
    @staticmethod
    def execute_query(connection: Connection, query: str, params: dict = None) -> Any:
        """
        Ejecuta una query SQL y retorna resultado.
        
        Args:
            connection: Conexión SQLAlchemy activa
            query: Query SQL con parámetros nombrados (formato :nombre)
            params: Diccionario con valores de parámetros
            
        Returns:
            Any: CursorResult con los resultados
            
        Raises:
            Exception: Si hay error en ejecución de query
        """
        try:
            # SQLAlchemy text() requiere parámetros nombrados
            sql_text = text(query)
            result = connection.execute(sql_text, params or {})
            return result
        except Exception as e:
            print(f"[ERROR] Error ejecutando query: {e}")
            print(f"[DEBUG] Query: {query}")
            print(f"[DEBUG] Params: {params}")
            raise
    
    @staticmethod
    def fetch_one(connection: Connection, query: str, params: dict = None) -> Optional[Tuple]:
        """
        Obtiene una única fila.
        
        Args:
            connection: Conexión SQLAlchemy activa
            query: Query SQL
            params: Diccionario de parámetros
            
        Returns:
            tuple | None: Primera fila o None
        """
        result = DatabaseUtils.execute_query(connection, query, params)
        return result.fetchone()
    
    @staticmethod
    def fetch_all(connection: Connection, query: str, params: dict = None) -> List[Tuple]:
        """
        Obtiene todas las filas del resultado.
        
        Args:
            connection: Conexión SQLAlchemy activa
            query: Query SQL
            params: Diccionario de parámetros
            
        Returns:
            list: Lista de tuplas (filas)
        """
        result = DatabaseUtils.execute_query(connection, query, params)
        return result.fetchall()
    
    @staticmethod
    def fetch_scalar(connection: Connection, query: str, params: dict = None) -> Optional[Any]:
        """
        Obtiene un valor escalar (primera columna de primera fila).
        
        Args:
            connection: Conexión SQLAlchemy activa
            query: Query SQL
            params: Diccionario de parámetros
            
        Returns:
            Any | None: Valor escalar o None
        """
        result = DatabaseUtils.execute_query(connection, query, params)
        return result.scalar()
    
    @staticmethod
    def execute_and_commit(connection: Connection, query: str, params: dict = None) -> int:
        """
        Ejecuta query de modificación y confirma los cambios.
        
        Args:
            connection: Conexión SQLAlchemy activa
            query: Query SQL (INSERT, UPDATE, DELETE)
            params: Diccionario de parámetros
            
        Returns:
            int: Cantidad de filas afectadas
        """
        result = DatabaseUtils.execute_query(connection, query, params)
        connection.commit()
        return result.rowcount


class TableQueryBuilder:
    """Constructor de queries SQL comunes para operaciones con tablas.
    
    Proporciona métodos estáticos para construir queries SQL reutilizables
    para inspección de estructura de tablas en PostgreSQL.
    """
    
    # Queries reutilizables
    QUERY_LIST_TABLES = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
    """
    
    QUERY_GET_COLUMNS = """
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = :table_name 
        AND table_schema = 'public'
        ORDER BY ordinal_position
    """
    
    QUERY_GET_PRIMARY_KEY = """
        SELECT ccu.column_name
        FROM information_schema.table_constraints tc 
        JOIN information_schema.constraint_column_usage ccu 
          ON tc.constraint_name = ccu.constraint_name 
        WHERE tc.constraint_type = 'PRIMARY KEY' 
          AND tc.table_name = :table_name
        LIMIT 1
    """
    
    @staticmethod
    def get_list_tables_query() -> str:
        """
        Retorna query para listar todas las tablas del esquema público.
        
        Returns:
            str: Query SQL para obtener lista de tablas
        """
        return TableQueryBuilder.QUERY_LIST_TABLES
    
    @staticmethod
    def get_columns_query(table_name: str) -> Tuple[str, dict]:
        """
        Retorna query y parámetros para obtener columnas de una tabla.
        
        Args:
            table_name: Nombre de la tabla
            
        Returns:
            tuple: (query_sql, params_dict)
        """
        return (
            TableQueryBuilder.QUERY_GET_COLUMNS,
            {"table_name": table_name}
        )
    
    @staticmethod
    def get_primary_key_query(table_name: str) -> Tuple[str, dict]:
        """
        Retorna query y parámetros para obtener nombre de clave primaria.
        
        Args:
            table_name: Nombre de la tabla
            
        Returns:
            tuple: (query_sql, params_dict)
        """
        return (
            TableQueryBuilder.QUERY_GET_PRIMARY_KEY,
            {"table_name": table_name}
        )
    


