import pandas as pd
from sqlalchemy import text
from datetime import datetime


class ETLControlManager:
    """
    Gestiona la tabla de control para rastreo de extracciones incrementales.
    
    La tabla 'etl_control' almacena para cada tabla procesada:
    - El último valor extraído de la columna de rastreo (timestamp o ID)
    - La fecha/hora de la última extracción
    - El nombre de la columna usada para rastreo
    
    Esto permite que cada ejecución del ETL solo extraiga datos nuevos
    desde el último valor procesado, evitando duplicados.
    """
    
    def __init__(self, connection):
        """
        Inicializa el gestor de control.
        
        Args:
            connection: Conexión activa a PostgreSQL (SQLAlchemy connection)
        """
        self.connection = connection
    
    def initialize_table(self):
        """
        Crea la tabla etl_control si no existe.
        
        Estructura de la tabla:
            - table_name: Nombre de la tabla (PRIMARY KEY)
            - last_extracted_value: Último valor procesado (puede ser fecha o número)
            - last_extracted_at: Timestamp de cuando se procesó
            - tracking_column: Nombre de la columna usada para rastreo
        """
        self.connection.execute(text("""
            CREATE TABLE IF NOT EXISTS etl_control (
                table_name VARCHAR(255) PRIMARY KEY,
                last_extracted_value VARCHAR(255),
                last_extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tracking_column VARCHAR(255)
            )
        """))
        self.connection.commit()
    
    def get_last_extracted_value(self, table_name):
        """
        Obtiene el último valor extraído de una tabla.
        
        Args:
            table_name: Nombre de la tabla a consultar
            
        Returns:
            tuple: (last_extracted_value, tracking_column) o (None, None) si no existe
            
        Ejemplo:
            last_value, col = manager.get_last_extracted_value('movie')
            # Retorna: ('5', 'movie_id') si ya se procesó la tabla
            # Retorna: (None, None) si es la primera vez
        """
        query = text("SELECT last_extracted_value, tracking_column FROM etl_control WHERE table_name = :table_name")
        result = self.connection.execute(query, {"table_name": table_name}).fetchone()
        if result:
            return result[0], result[1]
        return None, None
    
    def update_last_extracted_value(self, table_name, value, tracking_column):
        """
        Actualiza el último valor extraído usando UPSERT (INSERT o UPDATE).
        
        Si la tabla ya existe en etl_control, actualiza el registro.
        Si no existe, crea un nuevo registro.
        
        Args:
            table_name: Nombre de la tabla procesada
            value: Nuevo valor máximo extraído (puede ser Timestamp o int)
            tracking_column: Nombre de la columna de rastreo
            
        Ejemplo:
            manager.update_last_extracted_value('movie', 5, 'movie_id')
            # Guarda que el último movie_id procesado fue 5
        """
        # Convertir timestamps y datetimes a formato ISO string
        if isinstance(value, (pd.Timestamp, datetime)):
            value_str = value.isoformat()
        else:
            value_str = str(value)

        # UPSERT: Inserta si no existe, actualiza si existe (usando ON CONFLICT)
        upsert_query = text("""
            INSERT INTO etl_control (table_name, last_extracted_value, tracking_column, last_extracted_at)
            VALUES (:table_name, :val, :col, CURRENT_TIMESTAMP)
            ON CONFLICT (table_name) 
            DO UPDATE SET 
                last_extracted_value = :val,
                last_extracted_at = CURRENT_TIMESTAMP,
                tracking_column = :col
        """)
        self.connection.execute(upsert_query, {"table_name": table_name, "val": value_str, "col": tracking_column})
        self.connection.commit()
