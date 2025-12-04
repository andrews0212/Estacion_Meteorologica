"""Procesamiento incremental de tablas individuales en el pipeline ETL.

Este módulo orquesta la extracción incremental tabla por tabla:

1. Detecta la columna de rastreo (timestamp o ID) automáticamente
2. Consulta el estado anterior (.etl_state.json)
3. Extrae solo registros nuevos desde el último procesado
4. Serializa a CSV temporal
5. Sube a MinIO (Bronze)
6. Actualiza estado para próximo ciclo

Ejemplo::

    from sqlalchemy import create_engine
    from etl.table_processor import TableProcessor
    from etl.extractors import TableInspector
    from etl.control.control_manager import ExtractionStateManager
    
    engine = create_engine("postgresql://...")
    with engine.connect() as conn:
        inspector = TableInspector(conn)
        state_mgr = ExtractionStateManager()
        state_mgr.initialize_state()
        
        processor = TableProcessor(conn, "sensor_readings", state_mgr, inspector, minio_cfg)
        records = processor.process()
        print(f"Procesados {records} registros")
"""

from typing import Optional
from sqlalchemy import Connection
import pandas as pd
from etl.extractors import DataExtractor, TableInspector
from etl.writers import DataWriter
from etl.uploaders import MinIOUploader
from etl.control.control_manager import ExtractionStateManager
from config import MinIOConfig


class TableProcessor:
    """Procesa una tabla individual con extracción incremental.

    Responsabilidades:
    - Detectar automáticamente columna de rastreo (timestamp o ID)
    - Recuperar último valor procesado del archivo de estado
    - Extraer nuevos registros usando :class:`etl.extractors.DataExtractor`
    - Serializar a archivo CSV temporal
    - Subir a MinIO bucket Bronze
    - Actualizar estado (.etl_state.json) con máximo valor procesado
    
    El procesamiento es incremental: nunca reprocesa los mismos datos dos veces.
    """
    
    def __init__(self,
                 connection: Connection,
                 table_name: str,
                 state_manager: ExtractionStateManager,
                 inspector: TableInspector,
                 minio_config: MinIOConfig):
        """
        Inicializa el procesador para una tabla específica.
        
        Args:
            connection: Conexión SQLAlchemy activa a PostgreSQL
            table_name: Nombre de la tabla a procesar (ej: 'sensor_readings')
            state_manager: Gestor de estado para rastrear progreso (.etl_state.json)
            inspector: Inspector de tablas para detectar estructura
            minio_config: Configuración de MinIO para cargar datos
        """
        self.connection = connection
        self.table_name = table_name
        self.state_manager = state_manager
        self.inspector = inspector
        self.minio_config = minio_config
    
    def process(self) -> int:
        """
        Procesa tabla completa con extracción incremental.

        Workflow:
        1. **Detectar columna incremental**: Busca timestamp o ID automáticamente (ej: created_at, id)
        2. **Consultar estado anterior**: Obtiene último valor procesado desde .etl_state.json
        3. **Extraer registros nuevos**: Ejecuta query para > último_valor
        4. **Si hay datos**: Serializa a CSV, sube a MinIO y actualiza estado

        Returns:
            int: Cantidad de registros nuevos procesados en esta tabla
            
        Nota:
            Si no detecta columna de rastreo, retorna 0 y registra advertencia.
        """
        print(f"\nProcesando tabla: {self.table_name}")
        
        # 1. Detectar columna de rastreo
        tracking_column, tracking_type = self.inspector.detect_tracking_column(self.table_name)
        if not tracking_column:
            return self._handle_no_tracking_column()
        
        # 2. Obtener último valor procesado
        last_value, stored_column = self.state_manager.get_last_extracted_value(self.table_name)
        if stored_column and stored_column != tracking_column:
            last_value = None
        
        # 3. Extraer datos nuevos
        extractor = DataExtractor(self.connection, self.table_name, tracking_column, tracking_type)
        df = extractor.extract_incremental(last_value)
        
        # 4. Procesar si hay datos
        if df.empty:
            print("   ✓ No hay datos nuevos.")
            return 0
        
        return self._process_extracted_data(df, tracking_column)
    
    def _handle_no_tracking_column(self) -> int:
        """Maneja caso sin columna de rastreo."""
        print(f"⚠️  SKIPPING: No se detectó columna incremental.")
        cols = self.inspector.get_columns(self.table_name)
        col_names = [f"{c[0]}({c[1]})" for c in cols]
        print(f"   🔎 Columnas disponibles: {', '.join(col_names)}")
        return 0
    
    def _process_extracted_data(self, df: pd.DataFrame, tracking_column: str) -> int:
        """
        Procesa datos extraídos y los sube a MinIO.

        Pasos:
        1. Serializar el DataFrame a archivo CSV temporal
        2. Subir el archivo al bucket Bronze en MinIO
        3. Actualizar estado (.etl_state.json) con valor máximo de columna de rastreo
        4. Limpiar archivo temporal

        Args:
            df: DataFrame con registros nuevos a procesar
            tracking_column: Nombre de la columna usada para rastreo incremental

        Returns:
            int: Cantidad de registros procesados (len(df))

        Nota:
            La limpieza de archivo temporal ocurre incluso si la subida a MinIO falla,
            evitando acumulación de archivos temporales.
        """
        count = len(df)
        print(f"   📦 Registros nuevos: {count}")
        
        # Guardar en archivo temporal
        writer = DataWriter(self.table_name)
        local_path = writer.write(df)
        
        # Subir a MinIO
        uploader = MinIOUploader(self.minio_config)
        try:
            uploader.upload(local_path, self.table_name, writer.file_name)
            print(f"   ✅ Subido a MinIO: {writer.file_name}")
            
            # Actualizar estado
            max_val = df[tracking_column].max()
            self.state_manager.update_extraction_state(
                self.table_name,
                max_val,
                tracking_column,
                rows_extracted=count
            )
        except Exception as e:
            print(f"   ❌ Error subiendo a MinIO: {e}")
        finally:
            writer.cleanup()
        
        return count

