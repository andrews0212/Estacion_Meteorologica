# ====================================================
# Sistema ETL Incremental PostgreSQL → MinIO
# Script de ejecución para Windows (PowerShell)
# ====================================================

# Configuración de conexiones
$env:PG_DB = "postgres"
$env:PG_USER = "postgres"
$env:PG_PASS = "1234"           # ¡CÁMBIALA!
$env:PG_HOST = "10.202.50.50"   # ¡IP DEL SERVIDOR DB!

# MinIO (Capa Bronce)
$env:MINIO_ENDPOINT = "localhost:9000"      # ¡CÁMBIALA A LA IP/PUERTO DE TU MINIO!
$env:MINIO_ACCESS_KEY = "minioadmin"        # ¡CÁMBIALA A TU CLAVE DE ACCESO!
$env:MINIO_SECRET_KEY = "minioadmin"        # ¡CÁMBIALA A TU CLAVE SECRETA!
$env:MINIO_BUCKET = "meteo-bronze"

# Rutas locales
$PYTHON_SCRIPT = "main.py"
$PYTHON_VENV = ".\venv_meteo\Scripts\python.exe"

Write-Host "════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "🚀 Iniciando Sistema ETL Incremental PostgreSQL → MinIO" -ForegroundColor Green
Write-Host "Presiona Ctrl+C para detener." -ForegroundColor Yellow
Write-Host "════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Ejecuta el script principal de Python con el entorno virtual
# El bucle está dentro de main.py, no se necesita bucle en PowerShell
& $PYTHON_VENV $PYTHON_SCRIPT
