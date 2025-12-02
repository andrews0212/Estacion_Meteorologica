"""Paquete `etl`.

Pipeline ETL completo con arquitectura en capas (Bronce/Silver) y organización
en subpaquetes por responsabilidad.

Subpaquetes:
- :mod:`etl.extractors`: Extracción de datos desde PostgreSQL
- :mod:`etl.writers`: Serialización de datos a formatos (CSV, Parquet)
- :mod:`etl.uploaders`: Carga de datos a MinIO (S3 compatible)
- :mod:`etl.control`: Gestión de estado incremental (etl_control)
- :mod:`etl.managers`: Procesos de negocio (Silver, limpieza Bronce)
- :mod:`etl.utils`: Utilidades de BD y constructores de queries

Módulos principales:
- :mod:`etl.pipeline`: Pipeline de orquestación
- :mod:`etl.table_processor`: Procesamiento incremental por tabla
"""

# Utilidades
from .utils import DatabaseUtils, TableQueryBuilder, ETLControlQueries

# Extractores
from .extractors import DataExtractor, TableInspector, TrackingColumnDetector

# Escritores
from .writers import FileWriter, CSVWriter, DataWriter

# Cargadores
from .uploaders import MinIOUploader

# Control
from .control import ETLControlManager

# Managers
from .managers import SilverManager, LimpiezaBronce

# Procesadores
from .table_processor import TableProcessor
from .pipeline import ETLPipeline

__all__ = [
    # Utilidades
    'DatabaseUtils',
    'TableQueryBuilder',
    'ETLControlQueries',
    
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
    
    # Control
    'ETLControlManager',
    
    # Managers
    'SilverManager',
    'LimpiezaBronce',
    
    # Procesadores
    'TableProcessor',
    'ETLPipeline',
]
