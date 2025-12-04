"""Gestor de capa Silver: datos limpios después de transformación.

Este módulo implements SilverManager, especialización de LayerManager para trabajar
con el bucket Silver que contiene datos después de limpieza y transformación con PySpark.

Estrategia: **REPLACE**
- Mantiene solo la versión más reciente de cada tabla
- Elimina automáticamente versiones antiguas para optimizar espacio
"""

from .layer_manager import LayerManager


class SilverManager(LayerManager):
    """Gestor especial para la capa Silver: datos limpios y transformados.

    Hereda todas las funcionalidades de LayerManager, especializado para trabajar
    con el bucket 'meteo-silver' que contiene datos después del procesamiento
    PySpark de limpieza y normalización.
    
    La estrategia de versiones es REPLACE: solo mantiene la versión más reciente
    de cada tabla para optimizar espacio de almacenamiento.

    Ejemplo::

        from config import MinIOConfig
        cfg = MinIOConfig()
        sm = SilverManager(cfg)
        
        # Listar versiones de una tabla
        versiones = sm.obtener_versiones_tabla('sensor_readings')
        
        # Obtener la más reciente
        archivo = sm.obtener_archivo_reciente('sensor_readings')
        
        # Limpiar versiones antiguas
        eliminados = sm.limpiar_versiones_antiguas('sensor_readings')
    """
    
    def __init__(self, minio_config):
        """
        Inicializa el gestor de la capa Silver.
        
        Args:
            minio_config: Configuración de MinIO
            
        Note:
            Configura automáticamente el bucket '-silver' según la configuración
        """
        super().__init__(minio_config, bucket_suffix='-silver')
