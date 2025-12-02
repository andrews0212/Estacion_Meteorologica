"""Paquete `config`.

Contiene las clases de configuración para la base de datos y MinIO.
Se exportan `DatabaseConfig` y `MinIOConfig` para uso por el resto del
proyecto y para que Sphinx documente la configuración centralizada.
"""

from .database_config import DatabaseConfig
from .minio_config import MinIOConfig

__all__ = ['DatabaseConfig', 'MinIOConfig']
