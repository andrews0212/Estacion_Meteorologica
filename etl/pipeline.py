import time
from datetime import datetime
from sqlalchemy import create_engine
from .control_manager import ETLControlManager
from .table_inspector import TableInspector
from .table_processor import TableProcessor


class ETLPipeline:
    """
    Pipeline principal de ETL que coordina todo el sistema.
    
    Responsabilidades:
    - Crear conexión a PostgreSQL
    - Procesar todas las tablas en cada batch
    - Ejecutar continuamente con intervalos configurables
    - Manejar errores de conexión
    """
    
    def __init__(self, db_config, minio_config):
        """
        Inicializa el pipeline ETL.
        
        Args:
            db_config: Configuración de PostgreSQL (DatabaseConfig)
            minio_config: Configuración de MinIO (MinIOConfig)
        """
        self.db_config = db_config
        self.minio_config = minio_config
        
        # Crear engine de SQLAlchemy para gestionar conexiones a PostgreSQL
        # El engine maneja el pool de conexiones automáticamente
        self.engine = create_engine(db_config.connection_url)
    
    def process_batch(self):
        """
        Procesa un batch completo de todas las tablas.
        
        Un "batch" es una ejecución completa del ETL que procesa todas
        las tablas de la base de datos en secuencia.
        
        Flujo:
        1. Abrir conexión a PostgreSQL
        2. Inicializar tabla etl_control
        3. Obtener lista de todas las tablas
        4. Procesar cada tabla individualmente
        5. Mostrar resumen con total de registros procesados
        6. Cerrar conexión
        """
        print(f"\n--- INICIO DE BATCH: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
        
        try:
            # Abrir conexión dentro de un context manager (se cierra automáticamente)
            with self.engine.connect() as connection:
                # Inicializar tabla de control (se crea si no existe)
                control_manager = ETLControlManager(connection)
                control_manager.initialize_table()
                
                # Obtener lista de todas las tablas del esquema 'public'
                inspector = TableInspector(connection)
                tables = inspector.get_all_tables()
                
                # Procesar cada tabla secuencialmente
                total_records_batch = 0
                for table_name in tables:
                    # Crear procesador específico para esta tabla
                    processor = TableProcessor(connection, table_name, control_manager, inspector, self.minio_config)
                    
                    # Procesar y acumular cantidad de registros
                    total_records_batch += processor.process()
                
                # Mostrar resumen del batch completo
                print(f"\n🎯 RESUMEN: {total_records_batch} registros nuevos en este batch.")
        
        except Exception as e:
            # Capturar errores críticos (conexión a PostgreSQL caída, etc.)
            print(f"❌ ERROR CRÍTICO EN CONEXIÓN: {e}")
    
    def run_continuous(self, interval_seconds=10):
        """
        Ejecuta el ETL continuamente en un bucle infinito.
        
        Args:
            interval_seconds: Tiempo de espera entre cada batch (en segundos)
            
        El bucle se puede detener con Ctrl+C (KeyboardInterrupt).
        
        Ejemplo:
            pipeline.run_continuous(interval_seconds=10)   # Cada 10 segundos
            pipeline.run_continuous(interval_seconds=60)   # Cada 1 minuto
            pipeline.run_continuous(interval_seconds=300)  # Cada 5 minutos
        """
        while True:
            # Procesar un batch completo
            self.process_batch()
            
            # Esperar el intervalo especificado antes del siguiente batch
            print(f"Esperando {interval_seconds} segundos...")
            time.sleep(interval_seconds)
