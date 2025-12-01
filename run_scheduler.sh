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
PYTHON_SCRIPT="main.py"
PYTHON_VENV="venv_meteo/bin/python"

# ----------------------------------------------------
# 2. EJECUCIÓN DEL ETL
# ----------------------------------------------------

echo "🚀 Iniciando Sistema ETL Incremental PostgreSQL → MinIO"
echo "Presiona Ctrl+C para detener."
echo "----------------------------------------------------"

# Ejecuta el script principal de Python con el entorno virtual
# El bucle está dentro de main.py, no se necesita bucle en bash
$PYTHON_VENV $PYTHON_SCRIPT