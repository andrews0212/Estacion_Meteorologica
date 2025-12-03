# ============================================================================
# ETL Pipeline - Estación Meteorológica
# Script para ejecutar el sistema de 3 capas: Bronce → Silver → Gold
# ============================================================================

Write-Host "
╔════════════════════════════════════════════════════════════════════════════╗
║          ETL PIPELINE - ESTACION METEOROLOGICA                             ║
║                                                                            ║
║  Capas: Bronce (crudos) → Silver (limpios) → Gold (KPIs)                  ║
╚════════════════════════════════════════════════════════════════════════════╝
" -ForegroundColor Cyan

# Obtener ruta del script
$scriptDir = Split-Path -Parent -Path $MyInvocation.MyCommand.Definition
cd $scriptDir

# Verificar si venv existe
if (-Not (Test-Path "venv_meteo\Scripts\python.exe")) {
    Write-Host "❌ ERROR: venv no encontrado en $scriptDir\venv_meteo" -ForegroundColor Red
    Write-Host "    Ejecuta: py -m venv venv_meteo" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n📋 Opciones:" -ForegroundColor Yellow
Write-Host "  1. Ejecutar pipeline completo (extracción + silver + gold)"
Write-Host "  2. Solo Silver (limpiar datos de Bronce)"
Write-Host "  3. Solo Gold (calcular KPIs de Silver)"
Write-Host "  4. Salir"
Write-Host ""

$option = Read-Host "Selecciona una opción (1-4)"

switch ($option) {
    "1" {
        Write-Host "`n🚀 Ejecutando pipeline completo..." -ForegroundColor Green
        $env:PYTHONIOENCODING = 'utf-8'
        & venv_meteo\Scripts\python.exe main.py
    }
    "2" {
        Write-Host "`n🔧 Ejecutando Silver layer (limpieza)..." -ForegroundColor Green
        $env:PYTHONIOENCODING = 'utf-8'
        & venv_meteo\Scripts\python.exe etl/scripts/silver_layer.py
    }
    "3" {
        Write-Host "`n📊 Ejecutando Gold layer (KPIs)..." -ForegroundColor Green
        $env:PYTHONIOENCODING = 'utf-8'
        & venv_meteo\Scripts\python.exe etl/scripts/gold_layer.py
    }
    "4" {
        Write-Host "`n👋 Saliendo..." -ForegroundColor Yellow
        exit 0
    }
    default {
        Write-Host "❌ Opción inválida" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n✅ Ejecución completada" -ForegroundColor Green
Write-Host "📦 Verifica los buckets en MinIO: http://localhost:9000" -ForegroundColor Cyan
