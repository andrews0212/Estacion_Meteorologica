from sqlalchemy import text


class TableInspector:
    """
    Inspecciona la estructura de las tablas de PostgreSQL.
    
    Se encarga de:
    - Listar todas las tablas disponibles
    - Obtener columnas y tipos de datos de cada tabla
    - Detectar automáticamente la mejor columna para rastreo incremental
    """
    
    def __init__(self, connection):
        """
        Inicializa el inspector.
        
        Args:
            connection: Conexión activa a PostgreSQL
        """
        self.connection = connection
    
    def get_all_tables(self):
        """
        Obtiene lista de todas las tablas del esquema 'public'.
        
        Excluye la tabla 'etl_control' que es solo para uso interno del sistema.
        
        Returns:
            list: Lista con nombres de las tablas
            
        Ejemplo:
            ['movie', 'person', 'genre', 'keyword', ...]
        """
        tables = self.connection.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
        )).fetchall()
        return [t[0] for t in tables if t[0] != 'etl_control']
    
    def get_columns(self, table_name):
        """
        Obtiene columnas de una tabla con sus tipos de datos.
        
        Args:
            table_name: Nombre de la tabla a inspeccionar
            
        Returns:
            list: Lista de tuplas (column_name, data_type)
            
        Ejemplo:
            [('movie_id', 'integer'), ('title', 'character varying'), ...]
        """
        query = text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = :table_name 
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """)
        return self.connection.execute(query, {"table_name": table_name}).fetchall()
    
    def detect_tracking_column(self, table_name):
        """
        Detecta automáticamente la mejor columna para rastreo incremental.
        
        Estrategia de detección (en orden de prioridad):
        1. Columnas timestamp (created_at, updated_at, timestamp, etc.)
        2. PRIMARY KEY numérico (int, serial, numeric)
        3. Columna genérica 'id' (int, serial)
        
        Args:
            table_name: Nombre de la tabla a analizar
            
        Returns:
            tuple: (column_name, column_type) donde column_type es 'timestamp' o 'id'
                   o (None, None) si no encuentra columna válida
                   
        Ejemplo:
            detect_tracking_column('movie')
            # Retorna: ('movie_id', 'id') si movie_id es PRIMARY KEY
            # Retorna: ('created_at', 'timestamp') si tiene esa columna
            # Retorna: (None, None) si no hay columna válida
        """
        columns = self.get_columns(table_name)
        
        # 1. PRIORIDAD 1: Buscar columnas timestamp
        # Estas son ideales porque registran cuándo se creó o modificó cada registro
        timestamp_candidates = ['created_at', 'updated_at', 'timestamp', 'fecha_registro', 'last_update']
        for col_name, col_type in columns:
            if col_name.lower() in timestamp_candidates or 'timestamp' in col_type.lower():
                return col_name, 'timestamp'
        
        # 2. PRIORIDAD 2: Buscar PRIMARY KEY numérico
        # Consulta metadatos de PostgreSQL para encontrar la PRIMARY KEY
        pk_query = text("""
            SELECT ccu.column_name
            FROM information_schema.table_constraints tc 
            JOIN information_schema.constraint_column_usage ccu 
              ON tc.constraint_name = ccu.constraint_name 
            WHERE tc.constraint_type = 'PRIMARY KEY' 
              AND tc.table_name = :table_name
            LIMIT 1
        """)
        pk_result = self.connection.execute(pk_query, {"table_name": table_name}).fetchone()
        
        if pk_result:
            pk_col = pk_result[0]
            # Verificar que la PRIMARY KEY sea numérica (int, serial, numeric)
            for col_name, col_type in columns:
                if col_name == pk_col and ('int' in col_type.lower() or 'serial' in col_type.lower() or 'numeric' in col_type.lower()):
                    return pk_col, 'id'

        # 3. PRIORIDAD 3: Buscar columna genérica 'id'
        # Como último recurso, si hay una columna llamada 'id'
        for col_name, col_type in columns:
            if col_name.lower() == 'id' and ('int' in col_type.lower() or 'serial' in col_type.lower()):
                return col_name, 'id'
        
        # No se encontró ninguna columna válida para rastreo        
        return None, None
