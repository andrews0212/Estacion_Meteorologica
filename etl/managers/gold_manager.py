"""Gestor de capa Gold: KPIs y métricas agregadas.

Este módulo implementa GoldManager, especialización de LayerManager para trabajar
con el bucket Gold que contiene KPIs y métricas agregadas calculadas con PySpark.

Estrategia: **REPLACE**
- Mantiene solo la versión más reciente de cada tabla
- Elimina automáticamente versiones antiguas para optimizar espacio
"""

from .layer_manager import LayerManager


class GoldManager(LayerManager):
    """Gestor especial para la capa Gold: KPIs y métricas agregadas.

    Hereda todas las funcionalidades de LayerManager, especializado para trabajar
    con el bucket 'meteo-gold' que contiene KPIs, métricas agregadas y análisis
    calculados con PySpark sobre los datos de Silver.
    
    La estrategia de versiones es REPLACE: solo mantiene la versión más reciente
    de cada tabla para optimizar espacio de almacenamiento.

    Ejemplo::

        from config import MinIOConfig
        cfg = MinIOConfig()
        gm = GoldManager(cfg)
        
        # Listar versiones de una tabla
        versiones = gm.obtener_versiones_tabla('metricas_kpi')
        
        # Obtener la más reciente
        archivo = gm.obtener_archivo_reciente('metricas_kpi')
        
        # Limpiar versiones antiguas
        eliminados = gm.limpiar_versiones_antiguas('metricas_kpi')
    """
    
    def __init__(self, minio_config):
        """
        Inicializa el gestor de la capa Gold.
        
        Args:
            minio_config: Configuración de MinIO
            
        Note:
            Configura automáticamente el bucket '-gold' según la configuración
        """
        super().__init__(minio_config, bucket_suffix='-gold')
