"""etl.managers

Gestión de procesos de negocio y orquestación de capas de datos.

Módulos:
- :mod:`silver_manager`: Gestión de versiones y limpieza de datos Silver
- :mod:`limpieza_bronce`: Procesamiento y limpieza de datos Bronce (pandas)
- :mod:`silver_layer_spark`: Procesamiento y limpieza de datos Bronce (PySpark, alternativa)
"""

from .silver_manager import SilverManager
from .limpieza_bronce import LimpiezaBronce

__all__ = [
    'SilverManager',
    'LimpiezaBronce',
]

# Importar la alternativa Spark de forma opcional
try:
    from .silver_layer_spark import SilverLayerSpark, DataCleaner, SensorReadingsCleaner
    __all__.extend(['SilverLayerSpark', 'DataCleaner', 'SensorReadingsCleaner'])
except ImportError:
    pass  # PySpark no está instalado

