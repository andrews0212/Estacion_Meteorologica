"""Gestor de la capa Silver y gestión de versiones.

Este módulo implementa una estrategia simple de versiones (REPLACE) donde
solo se mantiene la versión más reciente de cada tabla en el bucket Silver.

Nota: Hereda de LayerManager para eliminar redundancia de código.

Funciones principales:
- listar versiones por tabla
- obtener la versión más reciente
- eliminar versiones antiguas
- obtener estadísticas (tamaño total, número de versiones)
"""

from .layer_manager import LayerManager


class SilverManager(LayerManager):
    """Gestiona archivos en capa Silver - Limpia versiones antiguas.

    Hereda todas las funcionalidades de LayerManager configurando el sufijo
    '-silver' para trabajar con el bucket meteo-silver.

    Args:
        minio_config: Instancia de configuración de MinIO con atributos
            ``endpoint``, ``access_key``, ``secret_key`` y ``bucket``.

    Ejemplo::

        from config import MinIOConfig
        cfg = MinIOConfig()
        sm = SilverManager(cfg)
        sm.limpiar_versiones_antiguas('sensor_readings')
    """
    
    def __init__(self, minio_config):
        """
        Inicializa el gestor de Silver.
        
        Args:
            minio_config: Configuración de MinIO (MinIOConfig)
        """
        super().__init__(minio_config, bucket_suffix='-silver')
