#!/usr/bin/env python3
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

import datetime
import time
from typing import Optional
from config import DatabaseConfig, MinIOConfig
from etl.pipeline import ETLPipeline
from etl.cleaners import DataCleaner


class ETLSystem:
    """Sistema de ETL - Extracción a Bronce + Limpieza automática a Silver.
    
    Flujo automático:
    1. Extrae datos de PostgreSQL → Bronce (MinIO)
    2. Limpia datos → Silver (MinIO)
    3. Repite cada N segundos
    """
    
    def __init__(self, 
                 db_config: Optional[DatabaseConfig] = None,
                 minio_config: Optional[MinIOConfig] = None,
                 extraction_interval: int = 300):
        """
        Inicializa sistema.
        
        Args:
            db_config: Configuración de BD (crea si es None)
            minio_config: Configuración de MinIO (crea si es None)
            extraction_interval: Segundos entre extracciones
        """
        self.db_config = db_config or DatabaseConfig()
        self.minio_config = minio_config or MinIOConfig()
        self.extraction_interval = extraction_interval
        self.pipeline = ETLPipeline(self.db_config, self.minio_config)
        self.cleaner = DataCleaner(self.minio_config)
    
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
        Ejecuta un ciclo completo: Extracción a Bronce + Limpieza a Silver.
        
        Args:
            cycle_num: Número del ciclo
            
        Returns:
            True si se completó exitosamente
        """
        print(f"\n--- CICLO {cycle_num}: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
        
        # Extracción a Bronce
        self.pipeline.process_batch()
        
        # Limpieza a Silver
        self._run_cleaning()
        
        return True
    
    def _run_cleaning(self) -> None:
        """Ejecuta limpieza automática de todas las tablas."""
        print(f"\n[INFO] Iniciando limpieza automática...")
        
        try:
            # Tablas a limpiar (obtenidas del inspector)
            from etl.extractors import TableInspector
            from sqlalchemy import create_engine
            
            engine = create_engine(self.db_config.connection_url)
            with engine.connect() as connection:
                inspector = TableInspector(connection)
                tables = inspector.get_all_tables()
            
            for table_name in tables:
                self.cleaner.clean_table(table_name)
        except Exception as e:
            print(f"[ERROR] Error en limpieza automática: {e}")
    
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


