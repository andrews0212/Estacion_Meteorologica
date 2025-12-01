#!/usr/bin/env python3
"""
Sistema ETL Incremental PostgreSQL → MinIO

Punto de entrada principal para ejecutar el pipeline ETL que extrae
datos incrementales de PostgreSQL y los carga en MinIO.

Uso:
    python main.py
    
Para detener:
    Ctrl+C
"""

from config import DatabaseConfig, MinIOConfig
from etl.pipeline import ETLPipeline


def main():
    """
    Función principal que inicializa y ejecuta el pipeline ETL.
    
    Pasos:
    1. Carga configuraciones de PostgreSQL y MinIO desde variables de entorno
    2. Crea instancia del pipeline ETL con esas configuraciones
    3. Ejecuta el pipeline en modo continuo (cada 10 segundos)
    4. Maneja la interrupción del usuario (Ctrl+C)
    """
    print("=" * 60)
    print("🚀 Iniciando Sistema ETL Incremental")
    print("=" * 60)
    
    # Cargar configuraciones desde variables de entorno
    # DatabaseConfig lee: PG_DB, PG_USER, PG_PASS, PG_HOST
    db_config = DatabaseConfig()
    
    # MinIOConfig lee: MINIO_ALIAS, MINIO_BUCKET
    minio_config = MinIOConfig()
    
    # Mostrar configuración cargada
    print(f"📊 Base de datos: {db_config.database}@{db_config.host}")
    print(f"🗄️  MinIO Bucket: {minio_config.bucket}")
    print("=" * 60)
    
    # Crear instancia del pipeline con las configuraciones
    pipeline = ETLPipeline(db_config, minio_config)
    
    try:
        # Ejecutar en bucle infinito cada 10 segundos
        # interval_seconds: tiempo de espera entre cada batch completo
        pipeline.run_continuous(interval_seconds=10)
    except KeyboardInterrupt:
        # Capturar Ctrl+C para salida limpia
        print("\n\n⏹️  Pipeline detenido por el usuario.")
        print("👋 ¡Hasta luego!")


if __name__ == "__main__":
    main()
