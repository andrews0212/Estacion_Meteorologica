"""Paquete extractores.

Módulos para extracción de datos desde PostgreSQL:
- data_extractor: Extracción incremental usando ventanas de tiempo/ID
- table_inspector: Inspección de estructura y detección de columnas de rastreo
"""

from .data_extractor import DataExtractor
from .table_inspector import TableInspector, TrackingColumnDetector

__all__ = [
    'DataExtractor',
    'TableInspector',
    'TrackingColumnDetector',
]
