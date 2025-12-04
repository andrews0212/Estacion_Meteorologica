"""Gestión de estado de extracciones incrementales usando archivo JSON.

Reemplaza la tabla SQL etl_control tradicional con un archivo JSON local,
simplificando la persistencia de estado sin depender de la base de datos.
"""

from typing import Tuple, Optional, Any
import pandas as pd
from datetime import datetime
from etl.etl_state import StateManager


class ExtractionStateManager:
    """Gestor de estado para extracciones ETL usando archivo JSON local.
    
    Almacena y recupera:
    - Último valor extraído de cada tabla
    - Columna de rastreo utilizada
    - Timestamp de última extracción
    - Cantidad de registros procesados
    
    Reemplaza la tabla ``etl_control`` de la base de datos.
    """
    
    def __init__(self, state_file: str = ".etl_state.json"):
        """
        Inicializa el gestor de estado de extracciones.
        
        Args:
            state_file: Ruta del archivo JSON de estado (default: .etl_state.json en raíz del proyecto)
        """
        self.state_manager = StateManager(state_file)
    
    def initialize_state(self) -> None:
        """Inicializa el archivo de estado (se crea automáticamente si no existe)."""
        # El StateManager crea el archivo automáticamente al guardar
        pass
    
    def get_last_extracted_value(self, table_name: str) -> Tuple[Optional[Any], Optional[str]]:
        """
        Obtiene último valor extraído de una tabla y su columna de rastreo.
        
        Args:
            table_name: Nombre de la tabla
            
        Returns:
            Tuple: (último_valor, columna_rastreo) o (None, None) si no existe registro
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
            table_name: Nombre de la tabla
            value: Nuevo valor máximo extraído (numérico o timestamp)
            tracking_column: Nombre de columna de rastreo
            rows_extracted: Cantidad de filas extraídas en este ciclo
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

