"""Utilidades para operaciones de base de datos."""

from typing import List, Tuple, Optional, Any
from sqlalchemy import text, Connection
from sqlalchemy.sql import bindparam


class DatabaseUtils:
    """Métodos reutilizables para operaciones de BD."""
    
    @staticmethod
    def execute_query(connection: Connection, query: str, params: dict = None) -> Any:
        """
        Ejecuta una query y retorna resultado.
        
        Args:
            connection: Conexión SQLAlchemy
            query: Query SQL con parámetros nombrados (:nombre)
            params: Diccionario con parámetros
            
        Returns:
            Resultado de la query
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
        """Obtiene un resultado."""
        result = DatabaseUtils.execute_query(connection, query, params)
        return result.fetchone()
    
    @staticmethod
    def fetch_all(connection: Connection, query: str, params: dict = None) -> List[Tuple]:
        """Obtiene todos los resultados."""
        result = DatabaseUtils.execute_query(connection, query, params)
        return result.fetchall()
    
    @staticmethod
    def fetch_scalar(connection: Connection, query: str, params: dict = None) -> Optional[Any]:
        """Obtiene un valor escalar."""
        result = DatabaseUtils.execute_query(connection, query, params)
        return result.scalar()
    
    @staticmethod
    def execute_and_commit(connection: Connection, query: str, params: dict = None) -> int:
        """Ejecuta query y hace commit. Retorna filas afectadas."""
        result = DatabaseUtils.execute_query(connection, query, params)
        connection.commit()
        return result.rowcount


class TableQueryBuilder:
    """Constructor de queries para operaciones con tablas."""
    
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
        """Retorna query para listar tablas."""
        return TableQueryBuilder.QUERY_LIST_TABLES
    
    @staticmethod
    def get_columns_query(table_name: str) -> Tuple[str, dict]:
        """Retorna query y params para obtener columnas."""
        return (
            TableQueryBuilder.QUERY_GET_COLUMNS,
            {"table_name": table_name}
        )
    
    @staticmethod
    def get_primary_key_query(table_name: str) -> Tuple[str, dict]:
        """Retorna query y params para obtener primary key."""
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
            table_name: Nombre de la tabla
            tracking_column: Columna de rastreo
            last_value: Último valor extraído
            
        Returns:
            (query, params)
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
    """Queries para tabla de control ETL."""
    
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
