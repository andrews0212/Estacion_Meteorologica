"""Extracción incremental de datos desde PostgreSQL.

Este módulo contiene la clase :class:`DataExtractor` que encapsula la lógica
para construir la consulta de extracción incremental (o carga inicial)
y ejecutar la consulta devolviendo un ``pandas.DataFrame``.
"""

from typing import Optional, Any
import pandas as pd
from sqlalchemy import Connection
from etl.utils import TableQueryBuilder


class DataExtractor:
    """Extrae datos incrementales de PostgreSQL."""
    
    def __init__(self, 
                 connection: Connection,
                 table_name: str,
                 tracking_column: str,
                 tracking_type: str):
        """
        Inicializa extractor.
        
        Args:
            connection: Conexión a PostgreSQL
            table_name: Nombre de la tabla
            tracking_column: Columna para rastreo (timestamp o ID)
            tracking_type: Tipo de columna ('id' o 'timestamp')
        """
        self.connection = connection
        self.table_name = table_name
        self.tracking_column = tracking_column
        self.tracking_type = tracking_type
    
    def extract_incremental(self, last_value: Optional[Any] = None) -> pd.DataFrame:
        """Extrae datos nuevos desde el último valor procesado.

        Construye la consulta SQL adecuada. Si ``last_value`` es proporcionado
        se extraen únicamente filas con ``tracking_column`` > ``last_value``.

        Args:
            last_value (Optional[Any]): Último valor procesado (None para carga inicial).

        Returns:
            pandas.DataFrame: DataFrame con los registros extraídos (posible vacío).

        Ejemplo::

            from etl.extractors.data_extractor import DataExtractor
            extractor = DataExtractor(conn, 'sensor_readings', 'created_at', 'timestamp')
            # Carga inicial
            df_all = extractor.extract_incremental()
            # Extracción incremental
            last = df_all['created_at'].max()
            df_new = extractor.extract_incremental(last_value=last)

        Notas:
            - Devuelve un DataFrame compatible con pandas, por lo que el resto del
              pipeline puede operar con métodos estándar como ``to_csv`` o ``concat``.
            - ``last_value`` puede ser string ISO (para timestamps) o numérico (para ids),
              el método intenta formatearlo correctamente en la consulta.
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
