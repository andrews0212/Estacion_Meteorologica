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
    """Sistema automatizado de ETL con procesamiento PySpark en capas (Bronze-Silver-Gold).
    
    Orquesta el flujo completo de extracción, transformación y carga de datos:
    
    1. **Extracción a Bronze**: Descarga incremental desde PostgreSQL → MinIO
    2. **Transformación a Silver**: Ejecuta notebook de limpieza (PySpark) → MinIO
    3. **Agregación a Gold**: Ejecuta notebook de KPIs (PySpark) → MinIO
    4. **Descarga**: Sincroniza archivos Gold a carpeta local (file/) para Power BI
    5. **Repetición**: Ejecuta ciclos automáticos cada N segundos
    
    El sistema opera en modo continuo con manejo robusto de errores y reintentos.
    """
    
    def __init__(self, 
                 db_config: Optional[DatabaseConfig] = None,
                 minio_config: Optional[MinIOConfig] = None,
                 extraction_interval: int = 300,
                 notebook_path: str = "notebooks/templates/limpieza_template.ipynb",
                 notebook_kpi_path: str = "notebooks/templates/generacion_KPI.ipynb"):
        """
        Inicializa el sistema ETL con configuraciones opcionales.
        
        Si no se proporcionan configuraciones, se cargan automáticamente desde variables
        de entorno o valores por defecto.
        
        Args:
            db_config: Configuración de PostgreSQL. Si es None, se carga automáticamente.
            minio_config: Configuración de MinIO. Si es None, se carga automáticamente.
            extraction_interval: Intervalo en segundos entre ciclos de extracción (default: 300s).
            notebook_path: Ruta relativa al notebook de limpieza Silver.
            notebook_kpi_path: Ruta relativa al notebook de generación de KPIs Gold.
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
        Ejecuta un ciclo completo de ETL: Extracción → Limpieza → KPIs → Sincronización.
        
        Workflow del ciclo:
        1. Extrae datos nuevos desde PostgreSQL (Bronze)
        2. Ejecuta notebook de limpieza con PySpark (Silver)
        3. Ejecuta notebook de generación de KPIs (Gold)
        4. Descarga archivos a carpeta local para Power BI
        
        Args:
            cycle_num: Número identificador del ciclo actual.
            
        Returns:
            bool: True si el ciclo completó exitosamente (incluso con advertencias).
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
        Ejecuta notebooks de transformación PySpark en secuencia.
        
        Ejecuta:
        1. **Notebook Silver**: Limpieza y transformación de datos Bronze
        2. **Notebook Gold**: Generación de KPIs y métricas agregadas
        
        Ambos notebooks tienen timeout de 600s (10 minutos). Si alguno falla,
        se registra una advertencia pero el ciclo continúa.
        
        Returns:
            bool: True si ambos completaron sin errores críticos.
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
        Descarga archivos transformados de MinIO a carpeta local para análisis en Power BI.
        
        Archivos descargados:
        - **datos_principales_silver.csv**: Datos limpios después de transformación Silver
        - **metricas_kpi_gold.csv**: Métricas y KPIs agregados de la capa Gold
        
        Los archivos se guardan en la carpeta `file/` para fácil acceso con Power BI Desktop.
        Incluye reintentos automáticos (máx 3 intentos por archivo) para mayor confiabilidad.
        
        Returns:
            bool: True si al menos uno de los archivos se descargó exitosamente.
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
            descargas_exitosas = 0
            for bucket, archivo_remoto, archivo_local in descargas:
                try:
                    local_path = file_dir / archivo_local
                    
                    # Eliminar archivo anterior si existe (para forzar actualización)
                    if local_path.exists():
                        os_module.remove(str(local_path))
                    
                    # Intentar descargar con reintentos
                    max_intentos = 3
                    for intento in range(max_intentos):
                        try:
                            client.fget_object(bucket, archivo_remoto, str(local_path))
                            print(f"[OK] {archivo_local} descargado desde {bucket}/")
                            descargas_exitosas += 1
                            break
                        except Exception as e_intento:
                            if intento < max_intentos - 1:
                                print(f"[REINTENTANDO] {archivo_local} (intento {intento + 1}/{max_intentos})")
                            else:
                                raise e_intento
                    
                except Exception as e:
                    print(f"[AVISO] No se pudo descargar {archivo_local} de {bucket}: {e}")
                    continue
            
            if descargas_exitosas > 0:
                print(f"[OK] {descargas_exitosas}/{len(descargas)} archivos descargados exitosamente")
            
            return True
            
        except Exception as e:
            print(f"[AVISO] Error descargando archivos: {e}")
            return False
    
    def run_continuous(self) -> None:
        """
        Ejecuta el sistema en modo continuo con ciclos automatizados.
        
        El sistema:
        - Muestra la configuración cargada
        - Ejecuta ciclos ETL repetidamente cada `extraction_interval` segundos
        - Maneja apagado limpio si el usuario presiona Ctrl+C
        - Registra el progreso con timestamps para monitoreo
        
        Runs indefinidamente hasta interrupción del usuario.
        """
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
        """
        Maneja el apagado limpio del sistema cuando el usuario presiona Ctrl+C.
        
        Imprime mensaje de despedida y detiene los ciclos de forma ordenada.
        """
        print("\n\n" + "=" * 80)
        print("DETENIENDO SISTEMA")
        print("=" * 80)
        print("[INFO] Pipeline detenido por el usuario")
        print("[INFO] Hasta luego! no se extrajo nada")


def insert_simulation_data(num_records: int = 1000) -> None:
    """
    Inserta datos simulados realistas en la tabla sensor_readings de PostgreSQL.
    
    Genera registros con valores aleatorios que simulan lecturas de una estación
    meteorológica durante los últimos 30 días. Útil para pruebas del pipeline.
    
    Parámetros de datos generados:
    - **temperatura**: 15-35°C (rango típico)
    - **humedad**: 30-95% (rango relativo)
    - **velocidad_viento**: 0-25 km/h
    - **presion**: 990-1030 hPa (rango barométrico)
    - **nivel_uv**: 0-11 (escala UV)
    - **pm25**: 0-300 µg/m³ (concentración de partículas)
    - **lluvia**: 0-50 mm (precipitación)
    - **vibracion**: 0-10 Hz (frecuencia)
    
    El sistema inserta en batches de 100 registros para optimizar rendimiento.
    Los registros se distribuyen uniformemente en el período de 30 días.
    
    Args:
        num_records: Cantidad de registros simulados a insertar (default: 1000).
        
    Raises:
        DatabaseError: Si la tabla 'sensor_readings' no existe.
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
            # PASO 1: Verificar que tabla existe
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
            
            # PASO 2: Generar datos simulados realistas
            print(f"[INFO] Generando {num_records} registros aleatorios...")
            
            # Distribuir registros en los últimos 30 días
            base_time = datetime.now() - timedelta(days=30)
            registros = []
            
            for i in range(num_records):
                fecha = base_time + timedelta(minutes=i)
                
                # Generar valores aleatorios dentro de rangos realistas
                registro = {
                    'timestamp': fecha,
                    'temperatura': round(random.uniform(15, 35), 2),        # 15-35°C
                    'humedad': round(random.uniform(30, 95), 2),             # 30-95%
                    'velocidad_viento': round(random.uniform(0, 25), 2),     # 0-25 km/h
                    'presion': round(random.uniform(990, 1030), 2),          # 990-1030 hPa
                    'nivel_uv': random.randint(0, 11),                       # 0-11 (escala UV)
                    'pm25': round(random.uniform(0, 300), 2),                # 0-300 µg/m³
                    'lluvia': round(random.uniform(0, 50), 2),               # 0-50 mm
                    'vibracion': round(random.uniform(0, 10), 2),            # 0-10 Hz
                }
                registros.append(registro)
            
            # PASO 3: Insertar en batches para optimizar rendimiento
            batch_size = 100
            total_insertados = 0
            
            for batch_num in range(0, len(registros), batch_size):
                batch = registros[batch_num:batch_num + batch_size]
                
                # Construir multi-value INSERT dinámicamente para mejor rendimiento
                # Genera: (%(timestamp_0)s, ...), (%(timestamp_1)s, ...), etc.
                placeholders = ", ".join([
                    f"(%(timestamp_{i})s, %(temperatura_{i})s, %(humedad_{i})s, "
                    f"%(velocidad_viento_{i})s, %(presion_{i})s, %(nivel_uv_{i})s, "
                    f"%(pm25_{i})s, %(lluvia_{i})s, %(vibracion_{i})s)"
                    for i in range(len(batch))
                ])
                
                # Preparar diccionario de parámetros nombrados para SQLAlchemy
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
            
            # Confirmar transacción
            conn.commit()
            
            print(f"\n[OK] Insertados {total_insertados} registros simulados")
            
            # VERIFICACIÓN: Confirmar cantidad total en tabla
            result = conn.execute(text("SELECT COUNT(*) FROM sensor_readings"))
            total = result.scalar()
            print(f"[OK] Total de registros en tabla sensor_readings: {total:,}")
            
        print("\n" + "=" * 80)
        print("✅ SIMULACIÓN COMPLETADA")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n[ERROR] Error insertando datos: {e}")
        import traceback
        traceback.print_exc()


def main() -> None:
    """
    Punto de entrada del programa.
    
    Modos de ejecución:
    - Sin argumentos: Ejecuta sistema ETL en modo continuo
    - "python main.py simulate": Inserta 1000 registros de prueba
    - "python main.py simulate N": Inserta N registros de prueba
    """
    import sys
    
    # Procesar argumentos de línea de comandos
    if len(sys.argv) > 1:
        if sys.argv[1] == "simulate":
            # MODO SIMULACIÓN: Generar datos de prueba
            num_registros = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
            insert_simulation_data(num_registros)
            return
    
    # MODO NORMAL: Ejecutar sistema ETL continuo
    system = ETLSystem(extraction_interval=300)
    system.run_continuous()


if __name__ == "__main__":
    main()


