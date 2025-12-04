#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Punto de entrada del sistema ETL.

Este módulo contiene la clase :class:`ETLSystem` que orquesta el pipeline
de extracción incremental y el procesamiento con notebooks PySpark.

Flujo general:
- Extrae datos de PostgreSQL usando :class:`etl.pipeline.ETLPipeline`
- Escribe resultados en Bronce (MinIO)
- Ejecuta notebook de limpieza con PySpark → Silver
- Ejecuta notebook de KPI con PySpark → Gold
- Descarga Gold a carpeta file/ para Power BI

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
from etl.notebook_executor import NotebookExecutor


class ETLSystem:
    """Sistema de ETL - Extracción a Bronce + Procesamiento con Notebooks PySpark.
    
    Flujo automático:
    1. Extrae datos de PostgreSQL → Bronce (MinIO)
    2. Ejecuta notebook de limpieza (PySpark) → Silver (MinIO)
    3. Ejecuta notebook de KPIs (PySpark) → Gold (MinIO)
    4. Descarga archivos a Power BI (file/)
    5. Repite cada N segundos
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
        
        # Limpieza y KPIs con Notebooks
        self._run_notebooks()
        
        # Descargar Gold a carpeta file/ para Power BI
        self._download_gold_for_powerbi()
        
        return True
    
    def _run_notebooks(self) -> bool:
        """
        Ejecuta notebooks de limpieza (Silver) y KPIs (Gold).
        
        Returns:
            True si ambos se ejecutaron exitosamente
        """
        notebooks = [
            (self.notebook_path, "Silver"),
            (self.notebook_kpi_path, "Gold")
        ]
        
        for notebook_rel_path, layer_name in notebooks:
            try:
                notebook_path = Path(__file__).parent / notebook_rel_path
                executor = NotebookExecutor(str(notebook_path))
                if not executor.execute(timeout=600):
                    print(f"[AVISO] Notebook {layer_name} retornó error, continuando...")
                    
            except Exception as e:
                print(f"[ERROR] Error ejecutando notebook {layer_name}: {e}")
                return False
        
        return True
    
    def _download_gold_for_powerbi(self) -> bool:
        """
        Descarga los archivos CSV desde MinIO a la carpeta file/ para Power BI.
        - Silver: datos_principales_silver.csv (datos limpios)
        - Gold: metricas_kpi_gold.csv (KPIs)
        Se ejecuta después de cada ciclo para análisis en tiempo real.
        
        Returns:
            True si se descargó exitosamente
        """
        print(f"\n[INFO] Descargando archivos para Power BI...")
        
        try:
            import os as os_module
            
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
            
            # Archivos a descargar: (bucket, archivo_remoto, nombre_local)
            descargas = [
                ("meteo-silver", "datos_principales_silver.csv", "datos_principales_silver.csv"),
                ("meteo-gold", "metricas_kpi_gold.csv", "metricas_kpi_gold.csv"),
            ]
            
            # Descargar cada archivo
            for bucket, archivo_remoto, archivo_local in descargas:
                try:
                    local_path = file_dir / archivo_local
                    
                    # Eliminar archivo anterior si existe (para forzar actualización)
                    if local_path.exists():
                        os_module.remove(str(local_path))
                    
                    client.fget_object(bucket, archivo_remoto, str(local_path))
                    print(f"[OK] {archivo_local} descargado desde {bucket}/")
                    
                except Exception as e:
                    print(f"[AVISO] No se pudo descargar {archivo_local} de {bucket}: {e}")
                    continue
            
            return True
            
        except Exception as e:
            print(f"[AVISO] Error descargando archivos: {e}")
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


def insert_simulation_data(num_records: int = 1000) -> None:
    """
    Inserta datos simulados de estación meteorológica en PostgreSQL.
    
    Genera 1000 registros aleatorios con:
    - temperatura: 15-35°C
    - humedad: 30-95%
    - velocidad_viento: 0-25 km/h
    - presion: 990-1030 hPa
    - nivel_uv: 0-11
    - pm25: 0-300 µg/m³
    - lluvia: 0-50 mm
    - vibracion: 0-10 Hz
    
    Args:
        num_records: Cantidad de registros a insertar (default 1000)
    """
    import random
    from datetime import datetime, timedelta
    from sqlalchemy import create_engine, text
    
    print("=" * 80)
    print(f"INSERTANDO {num_records} REGISTROS DE SIMULACIÓN")
    print("=" * 80)
    
    try:
        # Configuración de BD
        db_config = DatabaseConfig()
        engine = create_engine(db_config.connection_url)
        
        with engine.connect() as conn:
            # Verificar que tabla existe
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'sensor_readings'
                )
            """))
            
            if not result.scalar():
                print("[ERROR] Tabla 'sensor_readings' no existe")
                return
            
            print(f"[OK] Tabla 'sensor_readings' encontrada\n")
            
            # Generar datos simulados
            print(f"[INFO] Generando {num_records} registros aleatorios...")
            
            base_time = datetime.now() - timedelta(days=30)
            registros = []
            
            for i in range(num_records):
                fecha = base_time + timedelta(minutes=i)
                
                registro = {
                    'timestamp': fecha,
                    'temperatura': round(random.uniform(15, 35), 2),
                    'humedad': round(random.uniform(30, 95), 2),
                    'velocidad_viento': round(random.uniform(0, 25), 2),
                    'presion': round(random.uniform(990, 1030), 2),
                    'nivel_uv': random.randint(0, 11),
                    'pm25': round(random.uniform(0, 300), 2),
                    'lluvia': round(random.uniform(0, 50), 2),
                    'vibracion': round(random.uniform(0, 10), 2),
                }
                registros.append(registro)
            
            # Insertar en batches para mejor rendimiento
            batch_size = 100
            total_insertados = 0
            
            for batch_num in range(0, len(registros), batch_size):
                batch = registros[batch_num:batch_num + batch_size]
                
                # Construir INSERT con múltiples VALUES
                placeholders = ", ".join([
                    f"(%(timestamp_{i})s, %(temperatura_{i})s, %(humedad_{i})s, "
                    f"%(velocidad_viento_{i})s, %(presion_{i})s, %(nivel_uv_{i})s, "
                    f"%(pm25_{i})s, %(lluvia_{i})s, %(vibracion_{i})s)"
                    for i in range(len(batch))
                ])
                
                # Preparar parámetros
                params = {}
                for i, reg in enumerate(batch):
                    for key, value in reg.items():
                        params[f"{key}_{i}"] = value
                
                sql = text(f"""
                    INSERT INTO sensor_readings 
                    (timestamp, temperatura, humedad, velocidad_viento, presion, 
                     nivel_uv, pm25, lluvia, vibracion)
                    VALUES {placeholders}
                    ON CONFLICT DO NOTHING
                """)
                
                conn.execute(sql, params)
                total_insertados += len(batch)
                
                porcentaje = (total_insertados / num_records) * 100
                print(f"[...] Progreso: {total_insertados}/{num_records} ({porcentaje:.1f}%)", end='\r')
            
            conn.commit()
            
            print(f"\n[OK] Se insertaron {total_insertados} registros exitosamente")
            
            # Verificar cantidad total
            result = conn.execute(text("SELECT COUNT(*) FROM sensor_readings"))
            total = result.scalar()
            print(f"[OK] Total de registros en tabla: {total}")
            
        print("\n" + "=" * 80)
        print("✅ SIMULACIÓN COMPLETADA")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n[ERROR] Error insertando datos: {e}")
        import traceback
        traceback.print_exc()


def main() -> None:
    """Función principal."""
    import sys
    
    # Verificar argumentos
    if len(sys.argv) > 1:
        if sys.argv[1] == "simulate":
            # Modo simulación
            num_registros = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
            insert_simulation_data(num_registros)
            return
    
    # Modo normal: ejecutar sistema ETL
    system = ETLSystem(extraction_interval=300)
    system.run_continuous()


if __name__ == "__main__":
    main()


