"""Paquete etl: Pipeline de extracción, transformación y carga en capas.

Pipeline ETL completo con arquitectura en capas (Bronze → Silver → Gold)
y organización por responsabilidad en subpaquetes.

**Subpaquetes principales**:

- :mod:`etl.extractors`: Extracción incremental de datos desde PostgreSQL
- :mod:`etl.writers`: Serialización de DataFrames a archivos (CSV, etc.)
- :mod:`etl.uploaders`: Carga de archivos a MinIO (almacenamiento S3)
- :mod:`etl.managers`: Gestión de versiones en capas Silver y Gold
- :mod:`etl.control`: Tracking de estado de extracciones (.etl_state.json)
- :mod:`etl.utils`: Utilidades de BD, queries y MinIO

**Módulos principales**:

- :mod:`etl.pipeline`: Pipeline de orquestación (punto de entrada)
- :mod:`etl.table_processor`: Procesamiento por tabla con extracción incremental
- :mod:`etl.notebook_executor`: Ejecución de notebooks PySpark
- :mod:`etl.etl_state`: Gestor de estado en archivo JSON

**Flujo de datos**:

Bronze (extracción bruta) → Silver (limpieza) → Gold (KPIs)
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
