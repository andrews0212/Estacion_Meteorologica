"""Procesamiento de tablas individuales con extracción incremental."""

from typing import Optional
from sqlalchemy import Connection
import pandas as pd
from .data_extractor import DataExtractor
from .parquet_writer import DataWriter
from .minio_uploader import MinIOUploader
from .control_manager import ETLControlManager
from .table_inspector import TableInspector
from config import MinIOConfig


class TableProcessor:
    """Procesa una tabla individual con extracción incremental."""
    
    def __init__(self,
                 connection: Connection,
                 table_name: str,
                 control_manager: ETLControlManager,
                 inspector: TableInspector,
                 minio_config: MinIOConfig):
        """
        Inicializa procesador de tabla.
        
        Args:
            connection: Conexión a PostgreSQL
            table_name: Nombre de la tabla
            control_manager: Gestor de control ETL
            inspector: Inspector de tablas
            minio_config: Configuración de MinIO
        """
        self.connection = connection
        self.table_name = table_name
        self.control_manager = control_manager
        self.inspector = inspector
        self.minio_config = minio_config
    
    def process(self) -> int:
        """
        Procesa tabla completa con extracción incremental.
        
        Returns:
            Cantidad de registros procesados
        """
        print(f"\nProcesando tabla: {self.table_name}")
        
        # 1. Detectar columna de rastreo
        tracking_column, tracking_type = self.inspector.detect_tracking_column(self.table_name)
        if not tracking_column:
            return self._handle_no_tracking_column()
        
        # 2. Obtener último valor procesado
        last_value, stored_column = self.control_manager.get_last_extracted_value(self.table_name)
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
        Procesa datos extraídos.
        
        Args:
            df: DataFrame extraído
            tracking_column: Columna de rastreo
            
        Returns:
            Cantidad de registros procesados
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
            
            # Actualizar control
            max_val = df[tracking_column].max()
            self.control_manager.update_last_extracted_value(
                self.table_name,
                max_val,
                tracking_column
            )
        except Exception as e:
            print(f"   ❌ Error subiendo a MinIO: {e}")
        finally:
            writer.cleanup()
        
        return count

