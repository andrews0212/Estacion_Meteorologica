#!/usr/bin/env powershell
# Quick Start Script para Pipeline ETL + Power BI
# Uso: .\quickstart.ps1 [action]

param(
    [Parameter(Position=0)]
    [ValidateSet("run", "test", "monitor", "download", "help")]
    [string]$Action = "help"
)

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPath = Join-Path $projectRoot "venv_meteo\Scripts\Activate.ps1"

function Show-Help {
    Write-Host "`n" -ForegroundColor Cyan
    Write-Host "╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║         🚀 PIPELINE ETL + POWER BI - QUICK START                  ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Uso: .\quickstart.ps1 [action]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Acciones disponibles:" -ForegroundColor White
    Write-Host "  run       Ejecuta pipeline continuo (ciclos cada 5 minutos)" -ForegroundColor Green
    Write-Host "  test      Ejecuta 1 ciclo de prueba" -ForegroundColor Green
    Write-Host "  test 3    Ejecuta 3 ciclos de prueba" -ForegroundColor Green
    Write-Host "  monitor   Monitorea cambios en tiempo real (presiona Ctrl+C para detener)" -ForegroundColor Green
    Write-Host "  download  Descarga manualmente el archivo Gold" -ForegroundColor Green
    Write-Host "  help      Muestra este mensaje" -ForegroundColor Green
    Write-Host ""
    Write-Host "Ejemplos:" -ForegroundColor Yellow
    Write-Host "  .\quickstart.ps1 run                  # Pipeline continuo" -ForegroundColor Gray
    Write-Host "  .\quickstart.ps1 test                 # Ejecutar 1 ciclo" -ForegroundColor Gray
    Write-Host "  .\quickstart.ps1 test 3               # Ejecutar 3 ciclos" -ForegroundColor Gray
    Write-Host "  .\quickstart.ps1 monitor              # Monitorear 10 segundos entre verificaciones" -ForegroundColor Gray
    Write-Host ""
    Write-Host "📊 Después de ejecutar, el archivo está en:" -ForegroundColor Cyan
    Write-Host "   file/metricas_kpi_gold.csv" -ForegroundColor White
    Write-Host ""
    Write-Host "📝 Para importar en Power BI:" -ForegroundColor Cyan
    Write-Host "   1. Home → Get Data → Text/CSV" -ForegroundColor Gray
    Write-Host "   2. Seleccionar: file/metricas_kpi_gold.csv" -ForegroundColor Gray
    Write-Host "   3. Load y crear visualizaciones" -ForegroundColor Gray
    Write-Host ""
}

function Activate-Venv {
    if (Test-Path $venvPath) {
        & $venvPath
    } else {
        Write-Host "❌ Error: No se encontró el virtual environment" -ForegroundColor Red
        Write-Host "   Ruta esperada: $venvPath" -ForegroundColor Red
        exit 1
    }
}

function Run-Pipeline {
    Write-Host "`n╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║          🚀 EJECUTANDO PIPELINE ETL (CICLOS CONTINUOS)            ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "⏱️  Ciclos cada 5 minutos (300 segundos)" -ForegroundColor Yellow
    Write-Host "📊 Archivo de salida: file/metricas_kpi_gold.csv" -ForegroundColor Yellow
    Write-Host "⏹️  Presiona Ctrl+C para detener" -ForegroundColor Yellow
    Write-Host ""
    
    Set-Location $projectRoot
    Activate-Venv
    python main.py
}

function Run-Test {
    param([int]$Cycles = 1)
    
    Write-Host "`n╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║               🧪 TEST DE PIPELINE ($Cycles ciclos)                 ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    
    Set-Location $projectRoot
    Activate-Venv
    python test_pipeline.py -c $Cycles -i 5
}

function Run-Monitor {
    Write-Host "`n╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║         📊 MONITOREO DE ACTUALIZACIONES GOLD PARA POWER BI         ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📍 Archivo: file/metricas_kpi_gold.csv" -ForegroundColor Yellow
    Write-Host "⏱️  Verificación cada 10 segundos" -ForegroundColor Yellow
    Write-Host "⏹️  Presiona Ctrl+C para detener" -ForegroundColor Yellow
    Write-Host ""
    
    Set-Location $projectRoot
    Activate-Venv
    python monitor_powerbi.py --interval 10
}

function Run-Download {
    Write-Host "`n╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║            📥 DESCARGANDO ARCHIVO GOLD DESDE MINIO                 ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    
    Set-Location $projectRoot
    Activate-Venv
    python descargar_gold.py
}

# Main
switch ($Action) {
    "run" {
        Run-Pipeline
    }
    "test" {
        $cycles = 1
        if ($args.Count -gt 0 -and $args[0] -match '^\d+$') {
            $cycles = [int]$args[0]
        }
        Run-Test -Cycles $cycles
    }
    "monitor" {
        Run-Monitor
    }
    "download" {
        Run-Download
    }
    "help" {
        Show-Help
    }
    default {
        Write-Host "❌ Acción no reconocida: $Action" -ForegroundColor Red
        Show-Help
        exit 1
    }
}
