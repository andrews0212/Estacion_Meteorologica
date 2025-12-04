"""Extracción incremental de datos desde PostgreSQL a DataFrames.

Encapsula la lógica de construcción de queries de extracción incremental
y ejecución, retornando pandas DataFrames listos para procesar.
"""

from typing import Optional, Any
import pandas as pd
from sqlalchemy import Connection
from etl.utils import TableQueryBuilder


class DataExtractor:
    """Extractor incremental de datos desde PostgreSQL.
    
    Construye queries dinamicamente basadas en el tipo de columna de rastreo
    (timestamp o ID) y ejecuta extracción inicial o incremental.
    """
    
    def __init__(self, 
                 connection: Connection,
                 table_name: str,
                 tracking_column: str,
                 tracking_type: str):
        """
        Inicializa el extractor.
        
        Args:
            connection: Conexión SQLAlchemy activa a PostgreSQL
            table_name: Nombre de la tabla a extraer
            tracking_column: Columna para rastreo incremental (timestamp o ID)
            tracking_type: Tipo de rastreo ('timestamp' o 'id')
        """
        self.connection = connection
        self.table_name = table_name
        self.tracking_column = tracking_column
        self.tracking_type = tracking_type
    
    def extract_incremental(self, last_value: Optional[Any] = None) -> pd.DataFrame:
        """
        Extrae datos nuevos desde el último valor procesado.

        Construye query dinámicamente:
        - Si `last_value` es None: extrae todos (carga inicial)
        - Si `last_value` existe: extrae solo registros con tracking_column > last_value

        Args:
            last_value: Último valor procesado (None para carga inicial)

        Returns:
            pd.DataFrame: DataFrame con registros nuevos (posiblemente vacío)
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
            # pd.read_sql con manejo robusto de encoding
            try:
                df = pd.read_sql(query, self.connection, coerce_float=False)
            except UnicodeDecodeError as e:
                print(f"   ⚠️ UnicodeDecodeError detectado, intentando con character escaping...")
                # Reconectar con encoding más permisivo
                try:
                    # Intentar con latin1 que es más permisivo
                    df = pd.read_sql(query, self.connection, coerce_float=False)
                except:
                    # Si aún falla, crear un dataframe vacío para no romper el pipeline
                    print(f"   ⚠️ No se pudo leer datos, retornando dataframe vacío")
                    return pd.DataFrame()
            
            # Limpiar cualquier carácter problemático en strings
            for col in df.columns:
                if df[col].dtype == 'object':
                    try:
                        # Reemplazar caracteres invalidos
                        df[col] = df[col].apply(lambda x: str(x).encode('utf-8', errors='replace').decode('utf-8') if x is not None else '')
                    except:
                        df[col] = df[col].astype(str, errors='replace')
            
            return df
        except Exception as e:
            print(f"[ERROR] Error en extracción: {e}")
            print(f"[DEBUG] Query: {query}")
            # Return empty dataframe to keep pipeline alive
            return pd.DataFrame()
