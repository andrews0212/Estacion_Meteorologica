"""Paquete para gestión de subidas a almacenamiento.

Módulos para subir archivos a servicios de almacenamiento:
- minio_uploader: Subida a MinIO (S3 compatible)
"""

from .minio_uploader import MinIOUploader

__all__ = [
    'MinIOUploader',
]
