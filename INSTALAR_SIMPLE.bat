@echo off
REM ============================================
REM INSTALACION SIMPLIFICADA
REM ============================================
REM
REM Este script ejecuta el instalador de PowerShell
REM

echo.
echo ============================================
echo   INSTALADOR AUTOMATICO - SISTEMA CAMARAS
echo ============================================
echo.
echo Este instalador hara TODO automaticamente:
echo.
echo  - Git for Windows
echo  - Python 3.11
echo  - Node.js
echo  - FFmpeg
echo  - Tailscale VPN
echo  - Configuracion del proyecto
echo  - Scripts de inicio
echo.
echo Tiempo estimado: 30-60 minutos
echo.
echo IMPORTANTE: Necesitas conexion a internet
echo.
pause

echo.
echo Ejecutando instalador de PowerShell...
echo.

PowerShell -ExecutionPolicy Bypass -File "%~dp0INSTALAR_TODO_WINDOWS.ps1"

if %errorlevel% neq 0 (
    echo.
    echo ERROR en la instalacion
    echo Ver detalles arriba
    pause
    exit /b 1
)

echo.
echo ============================================
echo   INSTALACION COMPLETADA
echo ============================================
echo.
pause
