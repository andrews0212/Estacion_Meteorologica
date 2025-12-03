@echo off
REM Makefile para generar y servir documentación Sphinx
REM Uso: make help

setlocal enabledelayedexpansion

if "%1"=="help" goto help
if "%1"=="docs" goto docs
if "%1"=="serve" goto serve
if "%1"=="clean" goto clean
if "%1"=="all" goto all

:help
echo.
echo Estacion Meteorologica - Documentacion Sphinx
echo.
echo Comandos disponibles:
echo   make docs       Genera la documentacion HTML
echo   make serve      Abre la documentacion en el navegador
echo   make clean      Elimina los archivos generados
echo   make all        Genera y abre la documentacion
echo   make help       Muestra esta ayuda
echo.
goto end

:docs
echo Generando documentacion Sphinx...
call venv_meteo\Scripts\python.exe -m sphinx -b html docs docs/build/html
echo.
echo Documentacion generada en: docs/build/html/index.html
goto end

:serve
echo Abriendo documentacion en navegador...
start docs/build/html/index.html
goto end

:clean
echo Eliminando archivos generados...
if exist docs\build rmdir /s /q docs\build
echo Limpieza completada
goto end

:all
call :docs
call :serve
goto end

:end
endlocal
