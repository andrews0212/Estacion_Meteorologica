from .data_extractor import DataExtractor
from .parquet_writer import ParquetWriter
from .minio_uploader import MinIOUploader


class TableProcessor:
    """
    Procesa una tabla individual con extracción incremental.
    
    Orquesta todo el flujo ETL para una tabla:
    1. Detectar columna de rastreo
    2. Obtener último valor procesado
    3. Extraer datos nuevos
    4. Guardar en Parquet
    5. Subir a MinIO
    6. Actualizar control
    """
    
    def __init__(self, connection, table_name, control_manager, inspector, minio_config):
        """
        Inicializa el procesador de tabla.
        
        Args:
            connection: Conexión a PostgreSQL
            table_name: Nombre de la tabla a procesar
            control_manager: Instancia de ETLControlManager
            inspector: Instancia de TableInspector
            minio_config: Configuración de MinIO
        """
        self.connection = connection
        self.table_name = table_name
        self.control_manager = control_manager
        self.inspector = inspector
        self.minio_config = minio_config
    
    def process(self):
        """
        Procesa la tabla completa con extracción incremental.
        
        Flujo completo:
        1. Detectar columna para rastreo (timestamp o PRIMARY KEY)
        2. Si no hay columna válida, OMITIR la tabla
        3. Consultar último valor procesado en etl_control
        4. Extraer solo datos nuevos desde ese valor
        5. Si no hay datos nuevos, OMITIR procesamiento
        6. Guardar datos en archivo Parquet temporal
        7. Subir Parquet a MinIO
        8. Actualizar etl_control con nuevo último valor
        9. Limpiar archivo temporal
        
        Returns:
            int: Cantidad de registros procesados (0 si no hay datos nuevos o si se omitió)
        """
        print(f"\nProcesando tabla: {self.table_name}")
        
        # PASO 1: Detectar columna de rastreo (timestamp o PRIMARY KEY)
        tracking_column, tracking_type = self.inspector.detect_tracking_column(self.table_name)
        
        if not tracking_column:
            # Sin columna de rastreo, no se puede hacer extracción incremental
            # IMPORTANTE: Se omite la tabla en lugar de extraer todo cada vez
            print(f"⚠️  SKIPPING: No se detectó columna incremental (ID numérico o Timestamp).")
            cols = self.inspector.get_columns(self.table_name)
            col_names = [f"{c[0]}({c[1]})" for c in cols]
            print(f"   🔎 Columnas disponibles: {', '.join(col_names)}")
            return 0
        
        # PASO 2: Obtener último valor procesado de etl_control
        last_value, stored_column = self.control_manager.get_last_extracted_value(self.table_name)
        
        # Si cambió la columna de rastreo, reiniciar extracción (carga inicial)
        if stored_column and stored_column != tracking_column:
            last_value = None
        
        # PASO 3: Extraer datos nuevos desde last_value
        extractor = DataExtractor(self.connection, self.table_name, tracking_column, tracking_type)
        df = extractor.extract_incremental(last_value)
        
        # Si no hay datos nuevos, terminar aquí
        if df.empty:
            print("   ✓ No hay datos nuevos.")
            return 0
        
        count = len(df)
        print(f"   📦 Registros nuevos: {count}")
        
        # PASO 4: Guardar en Parquet temporal
        writer = ParquetWriter(self.table_name)
        local_path = writer.write(df)
        
        # PASO 5: Subir a MinIO
        uploader = MinIOUploader(self.minio_config)
        try:
            uploader.upload(local_path, self.table_name, writer.file_name)
            print(f"   ✅ Subido a MinIO: {writer.file_name}")
            
            # PASO 6: Actualizar control con el valor máximo extraído
            max_val = df[tracking_column].max()
            self.control_manager.update_last_extracted_value(self.table_name, max_val, tracking_column)
            
        except Exception as e:
            # Si falla la subida a MinIO, mostrar error
            print(f"   ❌ Error subiendo a MinIO: {e}")
        finally:
            # PASO 7: Siempre limpiar archivo temporal (exito o error)
            writer.cleanup()
        
        return count
