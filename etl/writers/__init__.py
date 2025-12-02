"""Paquete para escritores de archivos.

Módulos para serializar DataFrames a diferentes formatos:
- file_writer: Clase base abstracta
- csv_writer: Escritor CSV concreto
"""

from .file_writer import FileWriter
from .csv_writer import CSVWriter

# Alias para compatibilidad
DataWriter = CSVWriter

__all__ = [
    'FileWriter',
    'CSVWriter',
    'DataWriter',
]
