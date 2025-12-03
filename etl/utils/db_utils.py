"""Utilidades para operaciones de base de datos y construcción de queries.

Contiene funciones reutilizables para ejecutar queries con SQLAlchemy y
construir consultas usadas por el pipeline (listar tablas, obtener columnas,
consulta incremental, etc.).
"""

from typing import List, Tuple, Optional, Any
from sqlalchemy import text, Connection
from sqlalchemy.sql import bindparam


class DatabaseUtils:
    """Métodos reutilizables para operaciones de BD.

    Este wrapper ofrece manejo básico de errores y trazas para facilitar
    el debugging durante la generación de documentación y la ejecución.
    """
    
    @staticmethod
    def execute_query(connection: Connection, query: str, params: dict = None) -> Any:
        """
        Ejecuta una query y retorna resultado.
        
        Args:
            connection (sqlalchemy.Connection): Conexión SQLAlchemy activa
            query (str): Query SQL con parámetros nombrados (:nombre)
            params (dict | None): Diccionario con parámetros
            
        Returns:
            Any: Resultado de la query (CursorResult)
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
        """Obtiene un resultado.
        
        Args:
            connection (sqlalchemy.Connection): Conexión activa
            query (str): Query SQL
            params (dict | None): Parámetros
            
        Returns:
            tuple | None: Primera fila o None
        """
        result = DatabaseUtils.execute_query(connection, query, params)
        return result.fetchone()
    
    @staticmethod
    def fetch_all(connection: Connection, query: str, params: dict = None) -> List[Tuple]:
        """Obtiene todos los resultados.
        
        Args:
            connection (sqlalchemy.Connection): Conexión activa
            query (str): Query SQL
            params (dict | None): Parámetros
            
        Returns:
            list: Lista de tuplas
        """
        result = DatabaseUtils.execute_query(connection, query, params)
        return result.fetchall()
    
    @staticmethod
    def fetch_scalar(connection: Connection, query: str, params: dict = None) -> Optional[Any]:
        """Obtiene un valor escalar.
        
        Args:
            connection (sqlalchemy.Connection): Conexión activa
            query (str): Query SQL
            params (dict | None): Parámetros
            
        Returns:
            Any | None: Valor escalar o None
        """
        result = DatabaseUtils.execute_query(connection, query, params)
        return result.scalar()
    
    @staticmethod
    def execute_and_commit(connection: Connection, query: str, params: dict = None) -> int:
        """Ejecuta query y hace commit. Retorna filas afectadas.
        
        Args:
            connection (sqlalchemy.Connection): Conexión activa
            query (str): Query SQL
            params (dict | None): Parámetros
            
        Returns:
            int: Cantidad de filas afectadas
        """
        result = DatabaseUtils.execute_query(connection, query, params)
        connection.commit()
        return result.rowcount


class TableQueryBuilder:
    """Constructor de queries para operaciones con tablas.
    
    Proporciona métodos estáticos para construir queries comunes
    de inspección de tablas y extracción incremental.
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
        """Retorna query para listar tablas.
        
        Returns:
            str: Query SQL para listar todas las tablas en esquema 'public'
        """
        return TableQueryBuilder.QUERY_LIST_TABLES
    
    @staticmethod
    def get_columns_query(table_name: str) -> Tuple[str, dict]:
        """Retorna query y params para obtener columnas.
        
        Args:
            table_name (str): Nombre de la tabla
            
        Returns:
            tuple: (query, params_dict)
        """
        return (
            TableQueryBuilder.QUERY_GET_COLUMNS,
            {"table_name": table_name}
        )
    
    @staticmethod
    def get_primary_key_query(table_name: str) -> Tuple[str, dict]:
        """Retorna query y params para obtener primary key.
        
        Args:
            table_name (str): Nombre de la tabla
            
        Returns:
            tuple: (query, params_dict)
        """
        return (
            TableQueryBuilder.QUERY_GET_PRIMARY_KEY,
            {"table_name": table_name}
        )
    


