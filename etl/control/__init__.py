"""Paquete de control y gestión de estado ETL.

Módulos para rastreo y sincronización del estado del pipeline:
- control_manager: Gestor de estado usando archivo JSON (.etl_state.json)
"""

from .control_manager import ExtractionStateManager

__all__ = [
    'ExtractionStateManager',
]
