"""Gestor de la capa Gold y gestión de versiones.

Este módulo implementa una estrategia simple de versiones (REPLACE) donde
solo se mantiene la versión más reciente de cada tabla en el bucket Gold.

Nota: Hereda de LayerManager para eliminar redundancia de código.

Funciones principales:
- listar versiones por tabla
- obtener la versión más reciente
- eliminar versiones antiguas
- obtener estadísticas (tamaño total, número de versiones)
"""

from .layer_manager import LayerManager


class GoldManager(LayerManager):
    """Gestiona archivos en capa Gold - Limpia versiones antiguas.

    Hereda todas las funcionalidades de LayerManager configurando el sufijo
    '-gold' para trabajar con el bucket meteo-gold.

    Args:
        minio_config: Instancia de configuración de MinIO con atributos
            ``endpoint``, ``access_key``, ``secret_key`` y ``bucket``.

    Ejemplo::

        from config import MinIOConfig
        cfg = MinIOConfig()
        gm = GoldManager(cfg)
        gm.limpiar_versiones_antiguas('metricas_kpi')
    """
    
    def __init__(self, minio_config):
        """
        Inicializa el gestor de Gold.
        
        Args:
            minio_config: Configuración de MinIO (MinIOConfig)
        """
        super().__init__(minio_config, bucket_suffix='-gold')
