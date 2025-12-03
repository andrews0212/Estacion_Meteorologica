# Script para generar y servir documentación Sphinx
# Uso: .\docs.ps1 [comando]

param(
    [string]$Command = "help"
)

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$DocsDir = Join-Path $ProjectRoot "docs"
$BuildDir = Join-Path $DocsDir "build\html"
$VenvPython = Join-Path $ProjectRoot "venv_meteo\Scripts\python.exe"

function Show-Help {
    @"
╔════════════════════════════════════════════════════════╗
║   Estación Meteorológica - Documentación Sphinx        ║
╚════════════════════════════════════════════════════════╝

Comandos disponibles:

  .\docs.ps1 build      Genera la documentación HTML
  .\docs.ps1 open       Abre la documentación en navegador
  .\docs.ps1 serve      Inicia servidor HTTP (puerto 8000)
  .\docs.ps1 clean      Elimina archivos generados
  .\docs.ps1 all        Build + Open
  .\docs.ps1 help       Muestra esta ayuda

Ejemplos:

  # Generar documentación
  .\docs.ps1 build

  # Generar y abrir
  .\docs.ps1 all

  # Limpiar y regenerar
  .\docs.ps1 clean
  .\docs.ps1 build

"@
}

function Build-Docs {
    Write-Host "Generando documentación..." -ForegroundColor Cyan
    & $VenvPython -m sphinx -b html $DocsDir $BuildDir
    Write-Host "Documentación generada en: $BuildDir/index.html" -ForegroundColor Green
}

function Open-Docs {
    if (Test-Path "$BuildDir/index.html") {
        Write-Host "Abriendo documentación..." -ForegroundColor Cyan
        & "$BuildDir/index.html"
    }
    else {
        Write-Host "Error: Documentación no generada. Ejecuta: .\docs.ps1 build" -ForegroundColor Red
    }
}

function Serve-Docs {
    if (Test-Path $BuildDir) {
        Write-Host "Iniciando servidor en http://localhost:8000" -ForegroundColor Cyan
        Write-Host "Presiona Ctrl+C para detener" -ForegroundColor Yellow
        Push-Location $BuildDir
        & $VenvPython -m http.server 8000
        Pop-Location
    }
    else {
        Write-Host "Error: Documentación no generada. Ejecuta: .\docs.ps1 build" -ForegroundColor Red
    }
}

function Clean-Docs {
    Write-Host "Eliminando archivos generados..." -ForegroundColor Cyan
    if (Test-Path "$DocsDir\build") {
        Remove-Item -Recurse -Force "$DocsDir\build"
        Write-Host "Limpieza completada" -ForegroundColor Green
    }
}

# Ejecutar comando
switch ($Command.ToLower()) {
    "build"   { Build-Docs }
    "open"    { Open-Docs }
    "serve"   { Serve-Docs }
    "clean"   { Clean-Docs }
    "all"     { Build-Docs; Open-Docs }
    "help"    { Show-Help }
    default   { Write-Host "Comando desconocido: $Command`n"; Show-Help }
}
