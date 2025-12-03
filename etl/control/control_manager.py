"""Gestión de estado de extracciones: Archivo JSON en lugar de tabla SQL."""

from typing import Tuple, Optional, Any
import pandas as pd
from datetime import datetime
from etl.etl_state import StateManager


class ExtractionStateManager:
    """Gestiona el estado de extracciones ETL usando archivo JSON.
    
    Almacena y recupera el último valor extraído de cada tabla,
    permitiendo reiniciar extracciones desde el último punto procesado.
    Reemplaza la tabla ``etl_control`` de la base de datos.
    """
    
    def __init__(self, state_file: str = ".etl_state.json"):
        """
        Inicializa gestor de estado de extracciones.
        
        Args:
            state_file (str): Ruta del archivo JSON de estado.
        """
        self.state_manager = StateManager(state_file)
    
    def initialize_state(self) -> None:
        """Inicializa el archivo de estado (se crea automáticamente si no existe)."""
        # El StateManager crea el archivo automáticamente al guardar
        pass
    
    def get_last_extracted_value(self, table_name: str) -> Tuple[Optional[Any], Optional[str]]:
        """
        Obtiene último valor extraído de una tabla.
        
        Args:
            table_name (str): Nombre de la tabla.
            
        Returns:
            Tuple[Optional[Any], Optional[str]]: Tupla ``(last_value, tracking_column)`` 
            o ``(None, None)`` si no existe registro.
        """
        extraction = self.state_manager.get_last_extraction(table_name)
        if extraction:
            return (extraction.get('last_value'), extraction.get('tracking_column'))
        return (None, None)
    
    def update_extraction_state(self, 
                               table_name: str,
                               value: Any,
                               tracking_column: str,
                               rows_extracted: int = 0) -> None:
        """
        Actualiza el estado de extracción de una tabla.
        
        Args:
            table_name (str): Nombre de la tabla.
            value (Any): Nuevo valor máximo extraído (numérico o timestamp).
            tracking_column (str): Nombre de columna de rastreo.
            rows_extracted (int): Cantidad de filas extraídas en este ciclo.
        """
        # Convertir timestamps a string ISO
        if isinstance(value, (pd.Timestamp, datetime)):
            value_str = value.isoformat()
        else:
            value_str = str(value)
        
        self.state_manager.update_extraction_state(
            table_name=table_name,
            last_value=value_str,
            tracking_column=tracking_column,
            rows_extracted=rows_extracted
        )
    
    def display_current_state(self) -> None:
        """Muestra el estado actual de todas las extracciones."""
        self.state_manager.display_state()
    
    def reset_extraction_state(self, table_name: Optional[str] = None) -> None:
        """
        Limpia el estado de extracción de una tabla (o todas).
        
        Args:
            table_name (str, optional): Tabla a limpiar. Si None, limpia todas.
        """
        self.state_manager.reset_state(table_name)

