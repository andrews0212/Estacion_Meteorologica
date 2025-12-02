"""Pipeline principal de ETL que coordina todo el sistema."""

import time
from typing import Optional
from datetime import datetime
from sqlalchemy import create_engine, Connection
from sqlalchemy.pool import QueuePool
from .control_manager import ETLControlManager
from .table_inspector import TableInspector
from .table_processor import TableProcessor
from config import DatabaseConfig, MinIOConfig


class ETLPipeline:
    """Pipeline principal que coordina la extracción ETL."""
    
    def __init__(self, db_config: DatabaseConfig, minio_config: MinIOConfig):
        """
        Inicializa pipeline ETL.
        
        Args:
            db_config: Configuración de PostgreSQL
            minio_config: Configuración de MinIO
        """
        self.db_config = db_config
        self.minio_config = minio_config
        self.engine = self._create_engine()
    
    def _create_engine(self):
        """Crea engine SQLAlchemy con pool de conexiones."""
        return create_engine(
            self.db_config.connection_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10
        )
    
    def process_batch(self) -> int:
        """
        Procesa un batch completo de todas las tablas.
        
        Returns:
            Total de registros procesados
        """
        print(f"\n--- INICIO DE BATCH: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
        
        try:
            with self.engine.connect() as connection:
                return self._execute_batch(connection)
        except Exception as e:
            print(f"❌ ERROR CRÍTICO EN CONEXIÓN: {e}")
            return 0
    
    def _execute_batch(self, connection: Connection) -> int:
        """
        Ejecuta procesamiento de todas las tablas.
        
        Args:
            connection: Conexión activa
            
        Returns:
            Total de registros procesados
        """
        # Inicializar tabla de control
        control_manager = ETLControlManager(connection)
        control_manager.initialize_table()
        
        # Obtener tabla a procesar
        inspector = TableInspector(connection)
        tables = inspector.get_all_tables()
        
        total_records = 0
        for table_name in tables:
            processor = TableProcessor(connection, table_name, control_manager, inspector, self.minio_config)
            total_records += processor.process()
        
        print(f"\n🎯 RESUMEN: {total_records} registros nuevos en este batch.")
        return total_records
    
    def run_continuous(self, interval_seconds: int = 300) -> None:
        """
        Ejecuta pipeline continuamente.
        
        Args:
            interval_seconds: Segundos entre batches
        """
        try:
            while True:
                self.process_batch()
                print(f"Esperando {interval_seconds} segundos...")
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\n✓ Pipeline detenido")

