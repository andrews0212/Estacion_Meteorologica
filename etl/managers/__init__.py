"""etl.managers

Gestión de procesos de negocio y orquestación de capas de datos.

Módulos:
- :mod:`silver_manager`: Gestión de versiones y limpieza de datos Silver
- :mod:`gold_manager`: Gestión de versiones y KPIs de datos Gold
"""

from .silver_manager import SilverManager
from .gold_manager import GoldManager

__all__ = [
    'SilverManager',
    'GoldManager',
]

