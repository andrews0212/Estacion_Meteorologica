"""
Gestor de estado ETL: Almacena y recupera estado de extracciones en archivo JSON.
Reemplaza la tabla etl_control de la BD.
"""

import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path


class StateManager:
    """Gestiona el estado de extracciones ETL usando archivo JSON local."""
    
    def __init__(self, state_file: str = ".etl_state.json"):
        """
        Inicializa el gestor de estado.
        
        Args:
            state_file: Ruta del archivo JSON de estado (default: .etl_state.json)
        """
        self.state_file = state_file
        self.state_data = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """
        Carga el estado desde el archivo JSON.
        
        Returns:
            Diccionario con el estado, o {} si no existe
        """
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data if data else {}
            except Exception as e:
                print(f"[AVISO] Error cargando estado: {e}")
                return {}
        return {}
    
    def _save_state(self) -> bool:
        """
        Guarda el estado en archivo JSON.
        
        Returns:
            True si se guardó correctamente
        """
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state_data, f, indent=2, ensure_ascii=False, default=str)
            return True
        except Exception as e:
            print(f"[ERROR] No se pudo guardar estado: {e}")
            return False
    
    def get_last_extraction(self, table_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el último estado de extracción de una tabla.
        
        Args:
            table_name: Nombre de la tabla
            
        Returns:
            Dict con los datos {'last_value': ..., 'tracking_column': ..., 'timestamp': ...}
            o None si no hay registro
        """
        if table_name in self.state_data:
            return self.state_data[table_name]
        return None
    
    def get_last_extracted_value(self, table_name: str) -> Optional[Any]:
        """
        Obtiene el último valor extraído de una tabla.
        
        Args:
            table_name: Nombre de la tabla
            
        Returns:
            El último valor extraído o None
        """
        extraction = self.get_last_extraction(table_name)
        return extraction.get('last_value') if extraction else None
    
    def get_tracking_column(self, table_name: str) -> Optional[str]:
        """
        Obtiene la columna de rastreo de una tabla.
        
        Args:
            table_name: Nombre de la tabla
            
        Returns:
            Nombre de la columna de rastreo o None
        """
        extraction = self.get_last_extraction(table_name)
        return extraction.get('tracking_column') if extraction else None
    
    def update_extraction_state(self, 
                               table_name: str,
                               last_value: Any,
                               tracking_column: str,
                               rows_extracted: int = 0) -> bool:
        """
        Actualiza el estado de extracción de una tabla.
        
        Args:
            table_name: Nombre de la tabla
            last_value: Último valor extraído
            tracking_column: Columna de rastreo
            rows_extracted: Cantidad de filas extraídas
            
        Returns:
            True si se actualizó correctamente
        """
        self.state_data[table_name] = {
            'last_value': last_value,
            'tracking_column': tracking_column,
            'last_extracted_at': datetime.now().isoformat(),
            'rows_extracted': rows_extracted
        }
        return self._save_state()
    
    def get_all_states(self) -> Dict[str, Any]:
        """
        Obtiene el estado completo de todas las tablas.
        
        Returns:
            Diccionario con estado de todas las tablas
        """
        return self.state_data.copy()
    
    def reset_state(self, table_name: Optional[str] = None) -> bool:
        """
        Limpia el estado de una tabla (o todas).
        
        Args:
            table_name: Tabla a limpiar. Si None, limpia todas.
            
        Returns:
            True si se limpió correctamente
        """
        if table_name:
            if table_name in self.state_data:
                del self.state_data[table_name]
                print(f"[OK] Estado limpiado: {table_name}")
        else:
            self.state_data = {}
            print(f"[OK] Estado completamente limpiado")
        
        return self._save_state()
    
    def display_state(self) -> None:
        """Muestra el estado actual de forma legible."""
        print("\n" + "="*80)
        print("📋 ESTADO ACTUAL DE EXTRACCIONES")
        print("="*80)
        
        if not self.state_data:
            print("[AVISO] Sin datos de extracción")
            return
        
        for table_name, data in self.state_data.items():
            print(f"\n📊 Tabla: {table_name}")
            print(f"   Columna de rastreo: {data.get('tracking_column')}")
            print(f"   Último valor: {data.get('last_value')}")
            print(f"   Última extracción: {data.get('last_extracted_at')}")
            print(f"   Filas extraídas: {data.get('rows_extracted', 0)}")
        
        print("\n" + "="*80)


def reset_etl_state(state_file: str = ".etl_state.json") -> bool:
    """
    Función helper para limpiar completamente el estado.
    Útil para simular primera extracción.
    
    Args:
        state_file: Ruta del archivo de estado
        
    Returns:
        True si se limpió correctamente
    """
    manager = StateManager(state_file)
    return manager.reset_state()
