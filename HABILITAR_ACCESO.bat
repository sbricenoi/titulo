@echo off
REM =============================================
REM Habilitar TODO acceso remoto
REM =============================================

echo ==========================================
echo   HABILITAR TODO ACCESO REMOTO
echo ==========================================
echo.

REM Verificar permisos de administrador
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo [X] Este script debe ejecutarse como Administrador
    echo.
    echo Como hacerlo:
    echo 1. Click DERECHO en este archivo
    echo 2. Seleccionar "Ejecutar como administrador"
    echo.
    pause
    exit /b 1
)

echo [OK] Ejecutando como Administrador
echo.
echo Descargando y ejecutando script de configuracion...
echo.

powershell -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/sbricenoi/titulo/main/HABILITAR_TODO_ACCESO_REMOTO.ps1' -OutFile '%TEMP%\acceso_remoto.ps1'; & '%TEMP%\acceso_remoto.ps1'"

if %errorLevel% EQU 0 (
    echo.
    echo [OK] Configuracion completada
) else (
    echo.
    echo [X] Hubo un error
    echo.
    echo Intenta ejecutar manualmente:
    echo 1. Descargar: https://github.com/sbricenoi/titulo
    echo 2. Ejecutar: HABILITAR_TODO_ACCESO_REMOTO.ps1 como administrador
)

echo.
pause
