"""Paquete de control y gestión de estado ETL.

Módulos para rastreo y sincronización del estado del pipeline:
- control_manager: Gestor de tabla de control (etl_control)
"""

from .control_manager import ETLControlManager

__all__ = [
    'ETLControlManager',
]
