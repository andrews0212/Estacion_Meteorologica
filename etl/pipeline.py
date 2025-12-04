"""Pipeline principal de ETL que coordina extracción, transformación y carga en capas.

El pipeline orquesta las siguientes etapas:

1. **Inicialización del estado**: Carga o crea archivo `.etl_state.json` para rastreo incremental
2. **Inspección de tablas**: Detecta tablas disponibles y columnas de rastreo (timestamp o ID)
3. **Extracción incremental**: Por cada tabla, extrae solo registros nuevos desde el último valor conocido
4. **Serialización**: Escribe datos extraídos en archivos CSV temporales
5. **Carga a MinIO**: Sube archivos al bucket Bronze en MinIO (almacenamiento S3 compatible)
6. **Actualización de estado**: Registra el último valor extraído para próximos ciclos

El módulo utiliza SQLAlchemy con pooling de conexiones para mejor rendimiento y escalabilidad.

Ejemplo::

    from config import DatabaseConfig, MinIOConfig
    from etl.pipeline import ETLPipeline
    
    db_cfg = DatabaseConfig()
    minio_cfg = MinIOConfig()
    pipeline = ETLPipeline(db_cfg, minio_cfg)
    
    # Ejecutar un batch completo
    total_records = pipeline.process_batch()
    
    # O ejecutar continuamente
    pipeline.run_continuous(interval_seconds=300)
"""

import time
from typing import Optional
from datetime import datetime
from sqlalchemy import create_engine, Connection
from sqlalchemy.pool import QueuePool
from etl.control.control_manager import ExtractionStateManager
from etl.extractors import TableInspector
from etl.table_processor import TableProcessor
from etl.utils.minio_utils import MinIOUtils
from config import DatabaseConfig, MinIOConfig


class ETLPipeline:
    """Pipeline principal que coordina la extracción ETL."""
    
    def __init__(self, db_config: DatabaseConfig, minio_config: MinIOConfig):
        """
        Inicializa el pipeline ETL.
        
        Args:
            db_config: Configuración de conexión a PostgreSQL (servidor, puerto, BD, credenciales).
            minio_config: Configuración de acceso a MinIO (endpoint, credenciales, buckets).
            
        Nota:
            El engine SQLAlchemy se crea con pooling automático para reutilizar conexiones.
            El bucket Bronze se crea automáticamente si no existe.
        """
        self.db_config = db_config
        self.minio_config = minio_config
        self.engine = self._create_engine()
        
        # Crear bucket bronze si no existe
        try:
            minio_utils = MinIOUtils(minio_config)
            minio_utils.crear_bucket_si_no_existe(minio_config.bucket)
        except Exception as e:
            print(f"⚠️  Advertencia: No se pudo crear bucket Bronze: {e}")
    
    def _create_engine(self):
        """
        Crea engine SQLAlchemy con pool de conexiones.
        
        Configuración de pool:
        - **pool_size=5**: Mantiene 5 conexiones por defecto
        - **max_overflow=10**: Permite hasta 10 conexiones adicionales bajo demanda
        - **poolclass=QueuePool**: Usa cola FIFO para gestionar conexiones
        
        Returns:
            sqlalchemy.engine.Engine: Engine configurado listo para usar.
        """
        return create_engine(
            self.db_config.connection_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10
        )
    
    def process_batch(self) -> int:
        """
        Procesa un batch completo de todas las tablas disponibles.

        Workflow:
        1. Abre conexión reutilizable del pool
        2. Inicializa gestor de control (carga o crea `.etl_state.json`)
        3. Itera por cada tabla del esquema
        4. Aplica extracción incremental usando :class:`etl.table_processor.TableProcessor`
        5. Acumula total de registros nuevos

        Returns:
            int: Total de registros procesados en este batch (suma de todas las tablas).
            
        Nota:
            Si ocurre error crítico de conexión, registra el problema y retorna 0.
        """
        print(f"\n--- INICIO DE BATCH: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
        
        try:
            with self.engine.connect() as connection:
                return self._execute_batch(connection)
        except Exception as e:
            print(f"❌ ERROR CRÍTICO EN CONEXIÓN: {e}")
            # Log encoding issues specifically
            if "utf-8" in str(e) or "codec" in str(e):
                print(f"   💡 SUGERENCIA: Problemas de encoding en PostgreSQL")
                print(f"   Intente restaurar la BD con encoding UTF-8")
            return 0
    
    def _execute_batch(self, connection: Connection) -> int:
        """
        Ejecuta procesamiento de todas las tablas con una conexión activa.
        
        Pasos:
        1. Inicializa el gestor de estado (.etl_state.json) si no existe
        2. Obtiene lista de todas las tablas del esquema 'public'
        3. Para cada tabla: crea TableProcessor y ejecuta extracción incremental
        4. Suma total de registros procesados
        
        Args:
            connection: Conexión SQLAlchemy activa a PostgreSQL
            
        Returns:
            int: Total de registros nuevos procesados en todas las tablas.
        """
        # Inicializar gestor de estado (.etl_state.json)
        state_manager = ExtractionStateManager()
        state_manager.initialize_state()
        
        # Obtener tabla a procesar
        inspector = TableInspector(connection)
        tables = inspector.get_all_tables()
        
        total_records = 0
        for table_name in tables:
            processor = TableProcessor(connection, table_name, state_manager, inspector, self.minio_config)
            total_records += processor.process()
        
        print(f"\n🎯 RESUMEN: {total_records} registros nuevos en este batch.")
        return total_records
    
    def run_continuous(self, interval_seconds: int = 300) -> None:
        """
        Ejecuta el pipeline continuamente con intervalos fijos.
        
        El sistema ejecuta `process_batch()` repetidamente, esperando `interval_seconds`
        entre cada iteración. Útil para sincronización automática en producción.
        
        Args:
            interval_seconds: Intervalo en segundos entre batches (default: 300s = 5 min).
            
        Nota:
            Presione Ctrl+C para detener la ejecución.
        """
        try:
            while True:
                self.process_batch()
                print(f"Esperando {interval_seconds} segundos...")
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\n✓ Pipeline detenido")

