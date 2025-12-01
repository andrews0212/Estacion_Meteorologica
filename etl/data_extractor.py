import pandas as pd
from sqlalchemy import text


class DataExtractor:
    """
    Extrae datos incrementales de PostgreSQL.
    
    Se encarga de extraer SOLO los registros nuevos desde la última extracción,
    usando una columna de rastreo (timestamp o ID numérico).
    """
    
    def __init__(self, connection, table_name, tracking_column, tracking_type):
        """
        Inicializa el extractor de datos.
        
        Args:
            connection: Conexión activa a PostgreSQL
            table_name: Nombre de la tabla a extraer
            tracking_column: Nombre de la columna para rastreo (ej: 'movie_id', 'created_at')
            tracking_type: Tipo de columna ('id' o 'timestamp')
        """
        self.connection = connection
        self.table_name = table_name
        self.tracking_column = tracking_column
        self.tracking_type = tracking_type
    
    def extract_incremental(self, last_value=None):
        """
        Extrae datos nuevos desde el último valor procesado.
        
        Si last_value existe, hace extracción incremental (WHERE col > last_value).
        Si last_value es None, hace carga inicial (extrae todo).
        
        Args:
            last_value: Último valor procesado (puede ser timestamp o número)
            
        Returns:
            DataFrame: DataFrame de pandas con los datos extraídos
            
        Ejemplo carga incremental:
            extrac        query = text("SELECT last_extracted_value, tracking_column FROM etl_control WHERE table_name = :table_name")
tor = DataExtractor(conn, 'movie', 'movie_id', 'id')
            df = extractor.extract_incremental(last_value=5)
            # Extrae: SELECT * FROM movie WHERE movie_id > 5
            
        Ejemplo carga inicial:
            df = extractor.extract_incremental(last_value=None)
            # Extrae: SELECT * FROM movie (todos los registros)
        """
        if last_value:
            # Extracción INCREMENTAL: Solo registros nuevos
            print(f"   📊 Incremental ({self.tracking_column}) > {last_value}")
            
            # WHERE {tracking_column} > last_value para obtener solo nuevos
            # ORDER BY para procesar en orden ascendente
            # LIMIT 10000 como seguridad para no extraer demasiados registros de una vez
            query = text(f"SELECT * FROM {self.table_name} WHERE {self.tracking_column} > :val ORDER BY {self.tracking_column} ASC LIMIT 10000")
            return pd.read_sql(query, self.connection, params={"val": last_value})
        else:
            # Carga INICIAL: Primera vez que se procesa esta tabla
            print(f"   🆕 Carga Inicial ({self.tracking_column})")
            
            # SELECT * sin WHERE para obtener todos los registros
            # LIMIT 10000 para primera carga controlada
            query = text(f"SELECT * FROM {self.table_name} ORDER BY {self.tracking_column} ASC LIMIT 10000")
            return pd.read_sql(query, self.connection)
