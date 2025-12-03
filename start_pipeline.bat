@echo off
REM Batch script para ejecutar pipeline ETL con Power BI
REM Compatible con Windows Command Prompt

setlocal enabledelayedexpansion

set "PROJECT_ROOT=%~dp0"
set "VENV_PATH=%PROJECT_ROOT%venv_meteo\Scripts\activate.bat"

echo.
echo ================================================================================
echo    PIPELINE ETL + POWER BI INTEGRATION
echo ================================================================================
echo.

if not exist "%VENV_PATH%" (
    echo ERROR: No se encontro el virtual environment
    echo        Ruta esperada: %VENV_PATH%
    exit /b 1
)

REM Menu
:menu
echo.
echo Selecciona una opcion:
echo   1. Ejecutar pipeline continuo (recomendado)
echo   2. Ejecutar 1 ciclo de prueba
echo   3. Ejecutar 3 ciclos de prueba
echo   4. Monitorear cambios en tiempo real
echo   5. Descargar manualmente Gold CSV
echo   6. Salir
echo.

set /p choice=Opcion [1-6]: 

if "%choice%"=="1" goto run_pipeline
if "%choice%"=="2" goto test_1
if "%choice%"=="3" goto test_3
if "%choice%"=="4" goto monitor
if "%choice%"=="5" goto download
if "%choice%"=="6" goto end

echo ERROR: Opcion invalida
goto menu

:run_pipeline
echo.
echo ================================================================================
echo    EJECUTANDO PIPELINE ETL (ciclos continuos cada 5 minutos)
echo ================================================================================
echo.
echo Archivo de salida: file/metricas_kpi_gold.csv
echo Presiona Ctrl+C para detener
echo.
cd /d "%PROJECT_ROOT%"
call "%VENV_PATH%"
python main.py
goto menu

:test_1
echo.
echo ================================================================================
echo    TEST DE PIPELINE (1 ciclo)
echo ================================================================================
echo.
cd /d "%PROJECT_ROOT%"
call "%VENV_PATH%"
python test_pipeline.py -c 1 -i 5
goto menu

:test_3
echo.
echo ================================================================================
echo    TEST DE PIPELINE (3 ciclos)
echo ================================================================================
echo.
cd /d "%PROJECT_ROOT%"
call "%VENV_PATH%"
python test_pipeline.py -c 3 -i 5
goto menu

:monitor
echo.
echo ================================================================================
echo    MONITOREO DE ARCHIVO GOLD PARA POWER BI
echo ================================================================================
echo.
echo Archivo: file/metricas_kpi_gold.csv
echo Verificacion cada 10 segundos
echo Presiona Ctrl+C para detener
echo.
cd /d "%PROJECT_ROOT%"
call "%VENV_PATH%"
python monitor_powerbi.py --interval 10
goto menu

:download
echo.
echo ================================================================================
echo    DESCARGANDO GOLD CSV DESDE MINIO
echo ================================================================================
echo.
cd /d "%PROJECT_ROOT%"
call "%VENV_PATH%"
python descargar_gold.py
echo.
pause
goto menu

:end
echo.
echo Hasta luego!
echo.
exit /b 0
