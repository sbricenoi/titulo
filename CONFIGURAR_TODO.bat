@echo off
REM =============================================
REM Script Ultra Simple - Configurar SSH
REM =============================================

echo ==========================================
echo   CONFIGURACION AUTOMATICA SSH
echo ==========================================
echo.

REM Verificar si es administrador
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo [X] Este script debe ejecutarse como Administrador
    echo.
    echo Como ejecutar:
    echo 1. Click DERECHO en este archivo
    echo 2. Seleccionar "Ejecutar como administrador"
    echo.
    pause
    exit /b 1
)

echo [OK] Ejecutando como Administrador
echo.

echo Descargando script de configuracion...
powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/sbricenoi/titulo/main/HABILITAR_SSH_PASSWORD.ps1' -OutFile '%TEMP%\habilitar_ssh.ps1'"

if exist "%TEMP%\habilitar_ssh.ps1" (
    echo [OK] Script descargado
    echo.
    echo Ejecutando configuracion...
    echo.
    powershell -ExecutionPolicy Bypass -File "%TEMP%\habilitar_ssh.ps1"
) else (
    echo [X] Error al descargar el script
    echo.
    echo Intenta manualmente:
    echo 1. Ir a: https://github.com/sbricenoi/titulo
    echo 2. Descargar HABILITAR_SSH_PASSWORD.ps1
    echo 3. Ejecutar como administrador
    echo.
    pause
)
