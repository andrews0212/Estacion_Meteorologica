"""etl.managers

Gestión de procesos de negocio y orquestación de capas de datos.

Módulos:
- :mod:`silver_manager`: Gestión de versiones y limpieza de datos Silver
"""

from .silver_manager import SilverManager

__all__ = [
    'SilverManager',
]

