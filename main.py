#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Punto de entrada del sistema ETL.

Este módulo contiene la clase :class:`ETLSystem` que orquesta el pipeline
de extracción incremental y la limpieza automática (Estrategia REPLACE).

Flujo general:
- Extrae datos de PostgreSQL usando :class:`etl.pipeline.ETLPipeline`
- Escribe resultados en Bronce (MinIO)
- Ejecuta limpieza y publica datasets limpios en Silver

Ejecutar en modo continuo::
    python main.py
"""

import sys
import datetime
import time
import subprocess
from typing import Optional
from pathlib import Path
from minio import Minio

# Configurar UTF-8 en Windows
if sys.platform == 'win32':
    import os
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8')
from config import DatabaseConfig, MinIOConfig
from etl.pipeline import ETLPipeline


class ETLSystem:
    """Sistema de ETL - Extracción a Bronce + Limpieza con Notebook.
    
    Flujo automático:
    1. Extrae datos de PostgreSQL → Bronce (MinIO)
    2. Ejecuta notebook de limpieza → Silver (MinIO)
    3. Repite cada N segundos
    """
    
    def __init__(self, 
                 db_config: Optional[DatabaseConfig] = None,
                 minio_config: Optional[MinIOConfig] = None,
                 extraction_interval: int = 300,
                 notebook_path: str = "notebooks/templates/limpieza_template.ipynb",
                 notebook_kpi_path: str = "notebooks/templates/generacion_KPI.ipynb"):
        """
        Inicializa sistema.
        
        Args:
            db_config: Configuración de BD (crea si es None)
            minio_config: Configuración de MinIO (crea si es None)
            extraction_interval: Segundos entre extracciones
            notebook_path: Ruta al notebook de limpieza (Silver)
            notebook_kpi_path: Ruta al notebook de KPIs (Gold)
        """
        self.db_config = db_config or DatabaseConfig()
        self.minio_config = minio_config or MinIOConfig()
        self.extraction_interval = extraction_interval
        self.notebook_path = notebook_path
        self.notebook_kpi_path = notebook_kpi_path
        self.pipeline = ETLPipeline(self.db_config, self.minio_config)
    
    def display_config(self) -> None:
        """Muestra configuración cargada."""
        print("=" * 80)
        print("INICIANDO SISTEMA ETL + LIMPIEZA AUTOMATICA")
        print("=" * 80)
        print(f"\n{self.db_config}")
        print(f"{self.minio_config}")
        print(f"[OK] Intervalo de extracción: {self.extraction_interval}s")
        print("=" * 80)
    
    def run_cycle(self, cycle_num: int) -> bool:
        """
        Ejecuta un ciclo completo: Extracción a Bronce + Limpieza Silver + KPI Gold + Descarga.
        
        Args:
            cycle_num: Número del ciclo
            
        Returns:
            True si se completó exitosamente
        """
        print(f"\n--- CICLO {cycle_num}: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
        
        # Extracción a Bronce
        self.pipeline.process_batch()
        
        # Limpieza con Notebook (Silver)
        self._run_notebook_cleaning()
        
        # Generación de KPIs (Gold)
        self._run_notebook_kpi()
        
        # Descargar Gold a carpeta file/ para Power BI
        self._download_gold_for_powerbi()
        
        return True
    
    def _run_notebook_cleaning(self) -> bool:
        """
        Ejecuta el script de limpieza (Silver layer).
        
        Returns:
            True si se ejecutó exitosamente
        """
        print(f"\n[INFO] Ejecutando limpieza Silver...")
        
        try:
            script_path = Path(__file__).parent / "etl" / "scripts" / "silver_layer.py"
            result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                if result.stdout:
                    print(result.stdout)
                print(f"[OK] Silver layer ejecutado exitosamente")
                return True
            else:
                print(f"[ERROR] Fallo al ejecutar Silver layer")
                if result.stderr:
                    print(f"STDERR: {result.stderr}")
                if result.stdout:
                    print(f"STDOUT: {result.stdout}")
                return False
            
        except subprocess.TimeoutExpired:
            print(f"[ERROR] Silver layer timeout (>600s)")
            return False
        except Exception as e:
            print(f"[ERROR] Error ejecutando Silver: {e}")
            return False
    
    def _run_notebook_kpi(self) -> bool:
        """
        Ejecuta el script de generación de KPIs (Gold layer).
        
        Returns:
            True si se ejecutó exitosamente
        """
        print(f"\n[INFO] Ejecutando Gold KPI...")
        
        try:
            script_path = Path(__file__).parent / "etl" / "scripts" / "gold_layer.py"
            result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                if result.stdout:
                    print(result.stdout)
                print(f"[OK] Gold layer ejecutado exitosamente")
                return True
            else:
                print(f"[ERROR] Fallo al ejecutar Gold layer")
                if result.stderr:
                    print(f"STDERR: {result.stderr}")
                if result.stdout:
                    print(f"STDOUT: {result.stdout}")
                return False
            
        except subprocess.TimeoutExpired:
            print(f"[ERROR] Gold layer timeout (>600s)")
            return False
        except Exception as e:
            print(f"[ERROR] Error ejecutando Gold: {e}")
            return False
    
    def _download_gold_for_powerbi(self) -> bool:
        """
        Descarga el archivo CSV de Gold desde MinIO a la carpeta file/ para Power BI.
        Se ejecuta después de cada ciclo para análisis en tiempo real.
        
        Returns:
            True si se descargó exitosamente
        """
        print(f"\n[INFO] Descargando Gold CSV para Power BI...")
        
        try:
            # Crear cliente MinIO
            client = Minio(
                self.minio_config.endpoint,
                access_key=self.minio_config.access_key,
                secret_key=self.minio_config.secret_key,
                secure=self.minio_config.secure
            )
            
            # Crear carpeta file/ si no existe
            file_dir = Path(__file__).parent / "file"
            file_dir.mkdir(exist_ok=True)
            
            # Descargar archivo
            bucket = "meteo-gold"
            object_name = "metricas_kpi_gold.csv"
            local_path = file_dir / object_name
            
            client.fget_object(bucket, object_name, str(local_path))
            
            print(f"[OK] Gold CSV descargado a: {local_path}")
            return True
            
        except Exception as e:
            print(f"[AVISO] Error descargando Gold CSV: {e}")
            return False
    
    def run_continuous(self) -> None:
        """Ejecuta sistema continuamente."""
        try:
            self.display_config()
            print("\n[INFO] Presione Ctrl+C para detener\n")
            
            cycle_num = 0
            while True:
                cycle_num += 1
                self.run_cycle(cycle_num)
                
                print(f"\n[INFO] Esperando {self.extraction_interval}s...")
                time.sleep(self.extraction_interval)
        
        except KeyboardInterrupt:
            self._handle_shutdown()
    
    def _handle_shutdown(self) -> None:
        """Maneja apagado limpio."""
        print("\n\n" + "=" * 80)
        print("DETENIENDO SISTEMA")
        print("=" * 80)
        print("[INFO] Pipeline detenido por el usuario")
        print("[INFO] Hasta luego! no se extrajo nada")


def main() -> None:
    """Función principal."""
    system = ETLSystem(extraction_interval=300)
    system.run_continuous()


if __name__ == "__main__":
    main()


