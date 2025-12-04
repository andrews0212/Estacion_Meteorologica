"""Ejecutor de notebooks Jupyter para transformaciones PySpark en ETL.

Este módulo encapsula la ejecución de notebooks usando papermill, permitiendo
parametrización, captura de salida y manejo de errores robusto.

Ejemplo::

    from etl.notebook_executor import NotebookExecutor
    
    executor = NotebookExecutor("notebooks/templates/limpieza_template.ipynb")
    success = executor.execute(timeout=600)
    if success:
        print("Notebook ejecutado exitosamente")
"""

import subprocess
import sys
import os
import platform
from pathlib import Path
from typing import Optional


class NotebookExecutor:
    """Ejecuta notebooks Jupyter como parte del pipeline ETL."""
    
    def __init__(self, notebook_path: str, output_path: Optional[str] = None):
        """
        Inicializa el ejecutor de notebooks.
        
        Args:
            notebook_path: Ruta absoluta o relativa al notebook (.ipynb)
            output_path: Ruta para guardar el notebook ejecutado (opcional). 
                        Si es None, sobrescribe el notebook original.
                        
        Raises:
            FileNotFoundError: Si el archivo notebook_path no existe.
        """
        self.notebook_path = Path(notebook_path)
        self.output_path = Path(output_path) if output_path else None
        
        if not self.notebook_path.exists():
            raise FileNotFoundError(f"Notebook no encontrado: {self.notebook_path}")
    
    def execute(self, parameters: dict = None, timeout: int = 600) -> bool:
        """
        Ejecuta el notebook usando papermill con parámetros opcionales.
        
        Workflow:
        1. Limpia procesos JVM previos en Windows (para evitar conflictos con PySpark)
        2. Construye comando papermill con parámetros
        3. Ejecuta el notebook con timeout configurado
        4. Captura salida estándar y de errores
        
        Args:
            parameters: Diccionario con parámetros a pasar al notebook 
                       (ej: {"mode": "production", "batch_size": 1000})
            timeout: Tiempo máximo de ejecución en segundos (default: 600s = 10 min)
            
        Returns:
            bool: True si el notebook se ejecutó exitosamente (returncode == 0)
            
        Ejemplo::
        
            executor = NotebookExecutor("notebook.ipynb")
            params = {"table": "sensor_readings", "limit": 5000}
            success = executor.execute(parameters=params, timeout=1200)
        """
        try:
            self._cleanup_jvm()
            
            print(f"\n{'='*80}")
            print(f"[EJECUTANDO NOTEBOOK] {self.notebook_path.name}")
            if parameters:
                print(f"[PARÁMETROS] {parameters}")
            print(f"{'='*80}\n")
            
            # Comando base de papermill
            cmd = [
                sys.executable, "-m", "papermill",
                str(self.notebook_path),
                str(self.output_path) if self.output_path else str(self.notebook_path),
                "--kernel", "venv_meteo",
                "--execution-timeout", str(timeout)
            ]
            
            # Agregar parámetros nombrados si existen
            if parameters:
                for key, value in parameters.items():
                    cmd.extend(["-p", key, str(value)])
            
            result = subprocess.run(cmd, capture_output=False, text=True)
            
            if result.returncode == 0:
                print(f"\n[OK] Notebook ejecutado exitosamente")
                return True
            else:
                print(f"\n[ERROR] El notebook falló con código: {result.returncode}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Error ejecutando notebook: {e}")
            return False
    
    def _cleanup_jvm(self) -> None:
        """
        Limpia procesos JVM anteriores para evitar conflictos con PySpark.
        
        En Windows, los procesos java.exe pueden quedar en memoria después de
        ejecuciones previas, causando problemas de puerto y memoria.
        Este método los termina forzadamente (sin afectar procesos futuros).
        
        Solo se ejecuta en Windows; en Linux/Mac no es necesario.
        """
        if platform.system() == 'Windows':
            os.system('taskkill /F /IM java.exe 2>nul >nul || true')
