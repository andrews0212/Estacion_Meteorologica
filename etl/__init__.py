"""Paquete `etl`.

Pipeline ETL completo con arquitectura en capas (Bronce/Silver) y organización
en subpaquetes por responsabilidad.

Subpaquetes:
- :mod:`etl.extractors`: Extracción de datos desde PostgreSQL
- :mod:`etl.writers`: Serialización de datos a formatos (CSV, Parquet)
- :mod:`etl.uploaders`: Carga de datos a MinIO (S3 compatible)
- :mod:`etl.control`: Gestión de estado incremental (.etl_state.json)
- :mod:`etl.managers`: Procesos de negocio (Silver, limpieza Bronce)
- :mod:`etl.utils`: Utilidades de BD y constructores de queries

Módulos principales:
- :mod:`etl.pipeline`: Pipeline de orquestación
- :mod:`etl.table_processor`: Procesamiento incremental por tabla
- :mod:`etl.etl_state`: Gestor de estado usando archivo JSON
"""

# Utilidades
from .utils import DatabaseUtils, TableQueryBuilder

# Extractores
from .extractors import DataExtractor, TableInspector, TrackingColumnDetector

# Escritores
from .writers import FileWriter, CSVWriter, DataWriter

# Control y Estado (estos NO dependen de dependencias externas)
from .control import ExtractionStateManager
from .etl_state import StateManager

# Cargadores (lazy import - opcional)
def __getattr__(name):
    if name == 'MinIOUploader':
        try:
            from .uploaders import MinIOUploader
            return MinIOUploader
        except ImportError as e:
            raise ImportError(f"MinIOUploader requiere 'minio' instalado: {e}")
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

# Managers (lazy import - pueden requerir dependencias)
def _get_managers():
    from .managers import SilverManager, LimpiezaBronce
    return SilverManager, LimpiezaBronce

# Procesadores (lazy import - dependen de managers)
def _get_processors():
    from .table_processor import TableProcessor
    from .pipeline import ETLPipeline
    return TableProcessor, ETLPipeline

__all__ = [
    # Utilidades
    'DatabaseUtils',
    'TableQueryBuilder',
    
    # Extractores
    'DataExtractor',
    'TableInspector',
    'TrackingColumnDetector',
    
    # Escritores
    'FileWriter',
    'CSVWriter',
    'DataWriter',
    
    # Cargadores
    'MinIOUploader',
    
    # Control y Estado
    'ExtractionStateManager',
    'StateManager',
    
    # Managers
    'SilverManager',
    'LimpiezaBronce',
    
    # Procesadores
    'TableProcessor',
    'ETLPipeline',
]
