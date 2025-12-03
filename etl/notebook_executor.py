"""Ejecutor de notebooks Jupyter dentro del pipeline ETL."""

import subprocess
import sys
import os
from pathlib import Path
from typing import Optional


class NotebookExecutor:
    """Ejecuta notebooks Jupyter como parte del pipeline ETL."""
    
    def __init__(self, notebook_path: str, output_path: Optional[str] = None):
        """
        Inicializa el ejecutor.
        
        Args:
            notebook_path: Ruta al notebook (.ipynb)
            output_path: Ruta para guardar el notebook ejecutado (opcional)
        """
        self.notebook_path = Path(notebook_path)
        self.output_path = Path(output_path) if output_path else None
        
        if not self.notebook_path.exists():
            raise FileNotFoundError(f"Notebook no encontrado: {self.notebook_path}")
    
    def execute(self, timeout: int = 600) -> bool:
        """
        Ejecuta el notebook usando papermill.
        
        Args:
            timeout: Tiempo máximo de ejecución en segundos
            
        Returns:
            True si se ejecutó exitosamente
        """
        try:
            # Limpiar JVM antes de ejecutar (para evitar problemas con PySpark en Windows)
            self._cleanup_jvm()
            
            print(f"\n{'='*80}")
            print(f"[EJECUTANDO NOTEBOOK] {self.notebook_path.name}")
            print(f"{'='*80}\n")
            
            # Comando: papermill input.ipynb output.ipynb
            cmd = [
                sys.executable, "-m", "papermill",
                str(self.notebook_path),
                str(self.output_path) if self.output_path else str(self.notebook_path),
                "--kernel", "venv_meteo",
                "--execution-timeout", str(timeout)
            ]
            
            result = subprocess.run(cmd, capture_output=False, text=True)
            
            if result.returncode == 0:
                print(f"\n[OK] Notebook ejecutado exitosamente")
                if self.output_path:
                    print(f"[INFO] Resultado guardado en: {self.output_path}")
                return True
            else:
                print(f"\n[ERROR] El notebook falló con código: {result.returncode}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Error ejecutando notebook: {e}")
            return False
    
    def _cleanup_jvm(self):
        """Limpia procesos JVM anteriores para evitar problemas con PySpark en Windows."""
        import platform
        if platform.system() == 'Windows':
            os.system('taskkill /F /IM java.exe 2>nul >nul || true')
    
    def execute_with_papermill(self, parameters: dict = None, timeout: int = 600) -> bool:
        """
        Ejecuta el notebook con parámetros usando papermill.
        
        Args:
            parameters: Diccionario con parámetros a pasar al notebook
            timeout: Tiempo máximo de ejecución en segundos
            
        Returns:
            True si se ejecutó exitosamente
        """
        try:
            # Limpiar JVM antes de ejecutar (para evitar problemas con PySpark en Windows)
            self._cleanup_jvm()
            
            print(f"\n{'='*80}")
            print(f"[EJECUTANDO NOTEBOOK] {self.notebook_path.name}")
            if parameters:
                print(f"[PARÁMETROS] {parameters}")
            print(f"{'='*80}\n")
            
            # Comando base
            cmd = [
                sys.executable, "-m", "papermill",
                str(self.notebook_path),
                str(self.output_path) if self.output_path else str(self.notebook_path),
                "--kernel", "venv_meteo",
                "--execution-timeout", str(timeout)
            ]
            
            # Agregar parámetros si existen
            if parameters:
                for key, value in parameters.items():
                    cmd.extend(["-p", key, str(value)])
            
            result = subprocess.run(cmd, capture_output=False, text=True)
            
            if result.returncode == 0:
                print(f"\n[OK] Notebook ejecutado exitosamente")
                if self.output_path:
                    print(f"[INFO] Resultado guardado en: {self.output_path}")
                return True
            else:
                print(f"\n[ERROR] El notebook falló con código: {result.returncode}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Error ejecutando notebook: {e}")
            return False


def ejecutar_notebook_limpieza(tabla: str, minio_config) -> bool:
    """
    Ejecuta el notebook de limpieza para una tabla específica.
    
    Args:
        tabla: Nombre de la tabla a limpiar
        minio_config: Configuración de MinIO
        
    Returns:
        True si se ejecutó exitosamente
    """
    notebook_path = Path(__file__).parent.parent / "notebooks" / "templates" / "limpieza_template.ipynb"
    output_path = Path(__file__).parent.parent / "notebooks" / "outputs" / f"limpieza_{tabla}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.ipynb"
    
    # Crear directorio de outputs si no existe
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Parámetros para el notebook
    parameters = {
        "tabla": tabla,
        "minio_endpoint": minio_config.endpoint,
        "minio_bucket": minio_config.bucket
    }
    
    executor = NotebookExecutor(notebook_path, output_path)
    return executor.execute_with_papermill(parameters=parameters)
