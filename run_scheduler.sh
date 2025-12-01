#!/bin/bash


# ----------------------------------------------------
# 1. CONFIGURACIÓN DE CONEXIONES
# ----------------------------------------------------
# Base de Datos PostgreSQL
export PG_DB="cine"
export PG_USER="postgres"
export PG_PASS="1234" # <--- ¡CÁMBIALA!
export PG_HOST="127.0.0.1"           # <--- ¡IP DEL SERVIDOR DB!

# MinIO (Capa Bronce)
export MINIO_ALIAS="mi_minio"
export MINIO_BUCKET="meteo-bronze"

# Rutas locales
PYTHON_SCRIPT="procces_data.py" # <--- ¡AJUSTA ESTA RUTA!
PYTHON_VENV="venv_meteo/bin/python" # <--- ¡AJUSTA ESTA RUTA!
SLEEP_INTERVAL=10  # 10 segundos (ajusta según la frecuencia de llegada de datos)

# ----------------------------------------------------
# 2. BUCLE DE EJECUCIÓN CONSTANTE (BATCH)
# ----------------------------------------------------

echo "Iniciando el proceso de batch de datos. Actualización cada $SLEEP_INTERVAL segundos."
echo "Presiona Ctrl+C para detener."

while true; do
    TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
    echo "----------------------------------------------------"
    echo "--- INICIO DE BATCH: $TIMESTAMP ---"
    
    # Ejecuta el script de Python con el entorno virtual
    $PYTHON_VENV $PYTHON_SCRIPT
    
    echo "--- FIN DE BATCH ---"
    echo "Esperando $SLEEP_INTERVAL segundos..."
    echo "----------------------------------------------------"
    sleep $SLEEP_INTERVAL
done