@echo off
REM ============================================================
REM   FLOWGUARD · Launcher 1-click (NO necesita Python global)
REM   Utiliza el Python embebido del entorno virtual venv.
REM ============================================================

chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ============================================================
echo    FLOWGUARD  -  Network Operations Center  (v2 NOC)
echo ============================================================
echo.

REM -- Comprobación 1: Python del venv
if not exist ".\venv\Scripts\python.exe" (
    echo [ERROR] No se encuentra .\venv\Scripts\python.exe
    echo.
    echo SOLUCION: Crea el entorno virtual ejecutando dentro de esta carpeta:
    echo     py -3.10 -m venv venv
    echo     .\venv\Scripts\python.exe -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM -- Comprobación 2: GNS3 disponible (solo aviso)
echo [INFO] Asegurate de tener GNS3 ABIERTO y tu proyecto CARGADO.
echo        API GNS3 esperada en http://localhost:3080/v2
echo        Grafana (opcional) en http://localhost:3000
echo        PuTTY (opcional) en C:\Program Files\PuTTY\putty.exe
echo.

REM -- Lanzar el programa
echo [OK] Iniciando FLOWGUARD ...
echo.
".\venv\Scripts\python.exe" ".\flowguard.py"

set EXITCODE=%ERRORLEVEL%
echo.
if %EXITCODE% NEQ 0 (
    echo [ERROR] FLOWGUARD finalizo con codigo %EXITCODE%
) else (
    echo [INFO] FLOWGUARD finalizado correctamente.
)
echo.
pause
exit /b %EXITCODE%
