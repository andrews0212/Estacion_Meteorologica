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
    
    @staticmethod
    def get_incremental_extract_query(table_name: str, 
                                     tracking_column: str,
                                     last_value: Any = None) -> Tuple[str, dict]:
        """
        Construye query para extracción incremental.
        
        Args:
            table_name (str): Nombre de la tabla
            tracking_column (str): Columna de rastreo (timestamp o id)
            last_value (Any | None): Último valor extraído
            
        Returns:
            tuple: (query_sql, params_dict)
            
        Ejemplo::
        
            query, params = TableQueryBuilder.get_incremental_extract_query(
                'sensor_readings', 'created_at', '2025-01-01T10:00:00'
            )
        """
        if last_value:
            query = (
                f"SELECT * FROM {table_name} "
                f"WHERE {tracking_column} > :val "
                f"ORDER BY {tracking_column} ASC LIMIT 10000"
            )
            return query, {"val": last_value}
        else:
            query = (
                f"SELECT * FROM {table_name} "
                f"ORDER BY {tracking_column} ASC LIMIT 10000"
            )
            return query, {}


class ETLControlQueries:
    """Queries para tabla de control ETL.
    
    Define sentencias SQL para crear, consultar y actualizar
    la tabla de control que rastrea extracciones incrementales.
    """
    
    CREATE_CONTROL_TABLE = """
        CREATE TABLE IF NOT EXISTS etl_control (
            table_name VARCHAR(255) PRIMARY KEY,
            last_extracted_value VARCHAR(255),
            last_extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tracking_column VARCHAR(255)
        )
    """
    
    GET_LAST_VALUE = """
        SELECT last_extracted_value, tracking_column 
        FROM etl_control 
        WHERE table_name = :table_name
    """
    
    UPSERT_LAST_VALUE = """
        INSERT INTO etl_control (table_name, last_extracted_value, tracking_column, last_extracted_at)
        VALUES (:table_name, :val, :col, CURRENT_TIMESTAMP)
        ON CONFLICT (table_name) 
        DO UPDATE SET 
            last_extracted_value = :val,
            last_extracted_at = CURRENT_TIMESTAMP,
            tracking_column = :col
    """
