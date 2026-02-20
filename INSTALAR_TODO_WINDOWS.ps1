# ============================================
# INSTALACIÓN AUTOMÁTICA - Sistema de Cámaras
# Windows 10/11 - PowerShell
# ============================================
# 
# Este script instala TODO automáticamente:
# - Git, Python, Node.js, FFmpeg, Tailscale
# - Clona repositorio
# - Configura entorno
# - Crea scripts de inicio
#
# IMPORTANTE: Ejecutar como Administrador
#
# Uso:
#   1. Click derecho en este archivo
#   2. "Ejecutar con PowerShell"
#   3. Esperar ~30-60 minutos
#

# Verificar que se ejecuta como administrador
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "ERROR: Este script necesita permisos de Administrador" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Pasos:" -ForegroundColor Yellow
    Write-Host "1. Click derecho en este archivo" -ForegroundColor Yellow
    Write-Host "2. Seleccionar 'Ejecutar como administrador'" -ForegroundColor Yellow
    Write-Host ""
    pause
    exit 1
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  INSTALACION AUTOMATICA - SISTEMA CAMARAS" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Tiempo estimado: 30-60 minutos" -ForegroundColor Yellow
Write-Host "Presiona Ctrl+C para cancelar en cualquier momento" -ForegroundColor Yellow
Write-Host ""
pause

# Configuración
$INSTALL_DIR = "C:\titulo"
$GIT_REPO = ""  # Se pedirá al usuario

# ====================================
# PASO 1: Habilitar Winget
# ====================================
Write-Host ""
Write-Host "[1/10] Verificando Winget..." -ForegroundColor Cyan

if (Get-Command winget -ErrorAction SilentlyContinue) {
    Write-Host "OK - Winget disponible" -ForegroundColor Green
} else {
    Write-Host "ERROR - Winget no disponible" -ForegroundColor Red
    Write-Host "Instalando Winget..." -ForegroundColor Yellow
    
    # Descargar e instalar App Installer (incluye winget)
    $progressPreference = 'silentlyContinue'
    Invoke-WebRequest -Uri https://aka.ms/getwinget -OutFile $env:TEMP\winget.msixbundle
    Add-AppxPackage -Path $env:TEMP\winget.msixbundle
    
    Write-Host "OK - Winget instalado" -ForegroundColor Green
}

# ====================================
# PASO 2: Instalar Git
# ====================================
Write-Host ""
Write-Host "[2/10] Instalando Git for Windows..." -ForegroundColor Cyan

if (Get-Command git -ErrorAction SilentlyContinue) {
    Write-Host "OK - Git ya instalado: $(git --version)" -ForegroundColor Green
} else {
    winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
    
    # Refrescar PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    Write-Host "OK - Git instalado" -ForegroundColor Green
}

# ====================================
# PASO 3: Instalar Python 3.11
# ====================================
Write-Host ""
Write-Host "[3/10] Instalando Python 3.11..." -ForegroundColor Cyan

if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "OK - Python ya instalado: $(python --version)" -ForegroundColor Green
} else {
    winget install --id Python.Python.3.11 -e --source winget --accept-package-agreements --accept-source-agreements
    
    # Refrescar PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    Write-Host "OK - Python instalado" -ForegroundColor Green
}

# ====================================
# PASO 4: Instalar Node.js
# ====================================
Write-Host ""
Write-Host "[4/10] Instalando Node.js..." -ForegroundColor Cyan

if (Get-Command node -ErrorAction SilentlyContinue) {
    Write-Host "OK - Node.js ya instalado: $(node --version)" -ForegroundColor Green
} else {
    winget install --id OpenJS.NodeJS.LTS -e --source winget --accept-package-agreements --accept-source-agreements
    
    # Refrescar PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    Write-Host "OK - Node.js instalado" -ForegroundColor Green
}

# ====================================
# PASO 5: Instalar FFmpeg
# ====================================
Write-Host ""
Write-Host "[5/10] Instalando FFmpeg..." -ForegroundColor Cyan

if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
    Write-Host "OK - FFmpeg ya instalado" -ForegroundColor Green
} else {
    Write-Host "Descargando FFmpeg..." -ForegroundColor Yellow
    
    # Descargar FFmpeg
    $FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    $FFMPEG_ZIP = "$env:TEMP\ffmpeg.zip"
    $FFMPEG_DIR = "C:\ffmpeg"
    
    Invoke-WebRequest -Uri $FFMPEG_URL -OutFile $FFMPEG_ZIP
    
    # Extraer
    Expand-Archive -Path $FFMPEG_ZIP -DestinationPath $env:TEMP -Force
    
    # Mover a C:\ffmpeg
    $extractedDir = Get-ChildItem "$env:TEMP\ffmpeg-*" | Select-Object -First 1
    Move-Item -Path $extractedDir.FullName -Destination $FFMPEG_DIR -Force
    
    # Agregar al PATH
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    if ($currentPath -notlike "*$FFMPEG_DIR\bin*") {
        [Environment]::SetEnvironmentVariable("Path", "$currentPath;$FFMPEG_DIR\bin", "Machine")
    }
    
    # Refrescar PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    Write-Host "OK - FFmpeg instalado en $FFMPEG_DIR" -ForegroundColor Green
}

# ====================================
# PASO 6: Instalar Tailscale
# ====================================
Write-Host ""
Write-Host "[6/10] Instalando Tailscale..." -ForegroundColor Cyan

if (Get-Command tailscale -ErrorAction SilentlyContinue) {
    Write-Host "OK - Tailscale ya instalado" -ForegroundColor Green
} else {
    winget install --id tailscale.tailscale -e --source winget --accept-package-agreements --accept-source-agreements
    
    # Refrescar PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    Write-Host "OK - Tailscale instalado" -ForegroundColor Green
    Write-Host ""
    Write-Host "IMPORTANTE: Necesitas autenticar Tailscale:" -ForegroundColor Yellow
    Write-Host "1. Busca el icono de Tailscale en la barra de tareas" -ForegroundColor Yellow
    Write-Host "2. Click derecho > Log in" -ForegroundColor Yellow
    Write-Host "3. Autentica con tu cuenta" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Presiona Enter cuando hayas autenticado Tailscale..." -ForegroundColor Yellow
    pause
}

# ====================================
# PASO 7: Configurar Tailscale
# ====================================
Write-Host ""
Write-Host "[7/10] Configurando Tailscale como subnet router..." -ForegroundColor Cyan

try {
    tailscale up --advertise-routes=192.168.0.0/24
    Write-Host "OK - Tailscale configurado" -ForegroundColor Green
    Write-Host ""
    Write-Host "IMPORTANTE: Necesitas aprobar la ruta en Tailscale Admin:" -ForegroundColor Yellow
    Write-Host "1. Ve a: https://login.tailscale.com/admin/machines" -ForegroundColor Yellow
    Write-Host "2. Busca este equipo Windows" -ForegroundColor Yellow
    Write-Host "3. Click '...' > Edit route settings" -ForegroundColor Yellow
    Write-Host "4. Aprobar ruta 192.168.0.0/24" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Presiona Enter cuando hayas aprobado la ruta..." -ForegroundColor Yellow
    pause
} catch {
    Write-Host "ERROR configurando Tailscale: $_" -ForegroundColor Red
    Write-Host "Configura manualmente: tailscale up --advertise-routes=192.168.0.0/24" -ForegroundColor Yellow
}

# ====================================
# PASO 8: Clonar/Copiar Proyecto
# ====================================
Write-Host ""
Write-Host "[8/10] Obteniendo codigo del proyecto..." -ForegroundColor Cyan

if (Test-Path $INSTALL_DIR) {
    Write-Host "ADVERTENCIA: $INSTALL_DIR ya existe" -ForegroundColor Yellow
    $overwrite = Read-Host "Deseas sobreescribir? (s/n)"
    if ($overwrite -eq "s") {
        Remove-Item -Path $INSTALL_DIR -Recurse -Force
    } else {
        Write-Host "Instalacion cancelada" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Opciones de instalacion:" -ForegroundColor Yellow
Write-Host "1. Clonar desde GitHub" -ForegroundColor Yellow
Write-Host "2. Copiar desde directorio local/USB" -ForegroundColor Yellow
Write-Host ""
$option = Read-Host "Selecciona opcion (1 o 2)"

if ($option -eq "1") {
    $GIT_REPO = Read-Host "URL del repositorio GitHub"
    git clone $GIT_REPO $INSTALL_DIR
    Write-Host "OK - Repositorio clonado" -ForegroundColor Green
} elseif ($option -eq "2") {
    $SOURCE_DIR = Read-Host "Ruta del directorio fuente (ej: D:\titulo)"
    Copy-Item -Path $SOURCE_DIR -Destination $INSTALL_DIR -Recurse
    Write-Host "OK - Archivos copiados" -ForegroundColor Green
} else {
    Write-Host "ERROR: Opcion invalida" -ForegroundColor Red
    exit 1
}

# ====================================
# PASO 9: Configurar Entorno Python
# ====================================
Write-Host ""
Write-Host "[9/10] Configurando entorno Python..." -ForegroundColor Cyan

cd $INSTALL_DIR

# Crear entorno virtual
python -m venv venv
Write-Host "OK - Entorno virtual creado" -ForegroundColor Green

# Activar entorno
& "$INSTALL_DIR\venv\Scripts\Activate.ps1"

# Actualizar pip
python -m pip install --upgrade pip --quiet

# Instalar dependencias
Write-Host "Instalando dependencias (esto puede tomar 5-10 minutos)..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet
pip install -r requirements-recorder.txt --quiet

Write-Host "OK - Dependencias instaladas" -ForegroundColor Green

# Verificar instalación
Write-Host ""
Write-Host "Verificando instalacion:" -ForegroundColor Cyan
python -c "import ultralytics; print('  - YOLOv8: OK')"
python -c "import cv2; print('  - OpenCV: OK')"
python -c "import boto3; print('  - Boto3: OK')"
python -c "import fastapi; print('  - FastAPI: OK')"

# ====================================
# PASO 10: Crear Estructura y Scripts
# ====================================
Write-Host ""
Write-Host "[10/10] Creando estructura de directorios y scripts..." -ForegroundColor Cyan

# Crear directorios
$directories = @(
    "$INSTALL_DIR\data\videos\recordings",
    "$INSTALL_DIR\data\videos\completed",
    "$INSTALL_DIR\data\videos\uploaded",
    "$INSTALL_DIR\data\frames_for_classification",
    "$INSTALL_DIR\data\analysis_results",
    "$INSTALL_DIR\data\smart_analysis_results",
    "$INSTALL_DIR\logs"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

Write-Host "OK - Directorios creados" -ForegroundColor Green

# Crear script de inicio
$startScript = @"
@echo off
echo ============================================
echo  SISTEMA DE CAMARAS - INICIANDO
echo ============================================
echo.

REM Verificar Tailscale
echo [1/4] Verificando Tailscale...
tailscale status >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Tailscale no esta corriendo
    echo Inicia Tailscale desde la barra de tareas
    pause
    exit /b 1
)
echo OK - Tailscale activo
echo.

REM Activar entorno virtual
call $INSTALL_DIR\venv\Scripts\activate.bat

REM Iniciar Video Recorder
echo [2/4] Iniciando grabacion de camaras...
cd $INSTALL_DIR\video-recording-system
start "Video Recorder" /MIN python services\video_recorder.py
timeout /t 3 >nul
echo OK - Video Recorder iniciado
echo.

REM Iniciar S3 Uploader
echo [3/4] Iniciando uploader a S3...
start "S3 Uploader" /MIN python services\s3_uploader.py
timeout /t 3 >nul
echo OK - S3 Uploader iniciado
echo.

REM Iniciar API (opcional)
echo [4/4] Iniciando API Backend...
cd $INSTALL_DIR
start "API Backend" /MIN python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
timeout /t 3 >nul
echo OK - API iniciada
echo.

echo ============================================
echo  SISTEMA INICIADO CORRECTAMENTE
echo ============================================
echo.
echo Procesos corriendo:
echo  - Video Recorder (grabacion de camaras)
echo  - S3 Uploader (upload automatico a S3)
echo  - API Backend (puerto 8000)
echo.
echo Ver logs:
echo   $INSTALL_DIR\logs\recorder.log
echo   $INSTALL_DIR\logs\uploader.log
echo.
echo Presiona cualquier tecla para cerrar
echo (los procesos seguiran corriendo)
pause >nul
"@

$startScript | Out-File -FilePath "$INSTALL_DIR\INICIAR_SISTEMA.bat" -Encoding ASCII

# Crear script de detención
$stopScript = @"
@echo off
echo Deteniendo sistema...

REM Matar procesos de Python
taskkill /F /FI "WINDOWTITLE eq Video Recorder*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq S3 Uploader*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq API Backend*" >nul 2>&1

REM Matar procesos por nombre
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Video*" >nul 2>&1

echo Sistema detenido
timeout /t 2 >nul
"@

$stopScript | Out-File -FilePath "$INSTALL_DIR\DETENER_SISTEMA.bat" -Encoding ASCII

# Crear script de verificación
$verifyScript = @"
@echo off
echo ============================================
echo  VERIFICACION DEL SISTEMA
echo ============================================
echo.

echo [1] Verificando Tailscale...
tailscale status | findstr "100." >nul
if %errorlevel% equ 0 (
    echo OK - Tailscale activo
) else (
    echo ERROR - Tailscale NO activo
)
echo.

echo [2] Verificando camaras...
ping -n 1 192.168.0.8 >nul
if %errorlevel% equ 0 (echo OK - Camara 1 accesible) else (echo ERROR - Camara 1 NO accesible)

ping -n 1 192.168.0.9 >nul
if %errorlevel% equ 0 (echo OK - Camara 2 accesible) else (echo ERROR - Camara 2 NO accesible)

ping -n 1 192.168.0.7 >nul
if %errorlevel% equ 0 (echo OK - Camara 3 accesible) else (echo ERROR - Camara 3 NO accesible)
echo.

echo [3] Verificando procesos Python...
tasklist | findstr python.exe >nul
if %errorlevel% equ 0 (
    echo OK - Python corriendo
    tasklist | findstr python.exe | findstr /C:"Video Recorder" >nul && echo    - Video Recorder: ACTIVO
    tasklist | findstr python.exe | findstr /C:"S3 Uploader" >nul && echo    - S3 Uploader: ACTIVO
) else (
    echo ERROR - Python NO corriendo
)
echo.

echo [4] Verificando videos grabados...
dir $INSTALL_DIR\data\videos\recordings\*.mp4 >nul 2>&1
if %errorlevel% equ 0 (
    echo OK - Videos encontrados:
    dir $INSTALL_DIR\data\videos\recordings\*.mp4 /o-d | findstr ".mp4"
) else (
    echo ADVERTENCIA - No hay videos aun
)
echo.

echo [5] Verificando espacio en disco...
fsutil volume diskfree C: | findstr "Total"
echo.

echo ============================================
echo  VERIFICACION COMPLETADA
echo ============================================
pause
"@

$verifyScript | Out-File -FilePath "$INSTALL_DIR\VERIFICAR_SISTEMA.bat" -Encoding ASCII

Write-Host "OK - Scripts creados" -ForegroundColor Green

# ====================================
# CONFIGURAR .env
# ====================================
Write-Host ""
Write-Host "Configurando .env..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Necesitas configurar las credenciales AWS y URLs de camaras" -ForegroundColor Yellow
Write-Host ""

# Copiar template
Copy-Item "$INSTALL_DIR\video-recording-system\env.example" "$INSTALL_DIR\video-recording-system\.env"

Write-Host "Se abrira el archivo .env para que lo edites..." -ForegroundColor Yellow
Write-Host "Configuracion requerida:" -ForegroundColor Yellow
Write-Host "  - AWS_ACCESS_KEY_ID" -ForegroundColor Yellow
Write-Host "  - AWS_SECRET_ACCESS_KEY" -ForegroundColor Yellow
Write-Host "  - S3_BUCKET_NAME" -ForegroundColor Yellow
Write-Host "  - CAMERA_1_URL, CAMERA_2_URL, CAMERA_3_URL" -ForegroundColor Yellow
Write-Host ""
Write-Host "Presiona Enter para abrir el editor..." -ForegroundColor Yellow
pause

notepad "$INSTALL_DIR\video-recording-system\.env"

Write-Host ""
Write-Host "Presiona Enter cuando hayas guardado el .env..." -ForegroundColor Yellow
pause

# ====================================
# CONFIGURAR ENERGIA
# ====================================
Write-Host ""
Write-Host "Configurando opciones de energia..." -ForegroundColor Cyan

# Evitar que el equipo se suspenda
powercfg /change standby-timeout-ac 0
powercfg /change standby-timeout-dc 0
powercfg /change monitor-timeout-ac 30
powercfg /change monitor-timeout-dc 30

Write-Host "OK - Configuracion de energia ajustada" -ForegroundColor Green

# ====================================
# CONFIGURAR INICIO AUTOMATICO (OPCIONAL)
# ====================================
Write-Host ""
Write-Host "Deseas que el sistema inicie automaticamente con Windows? (s/n)" -ForegroundColor Yellow
$autostart = Read-Host

if ($autostart -eq "s") {
    $startupFolder = [Environment]::GetFolderPath("Startup")
    $shortcut = "$startupFolder\Sistema Camaras.lnk"
    
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($shortcut)
    $Shortcut.TargetPath = "$INSTALL_DIR\INICIAR_SISTEMA.bat"
    $Shortcut.WorkingDirectory = $INSTALL_DIR
    $Shortcut.Save()
    
    Write-Host "OK - Inicio automatico configurado" -ForegroundColor Green
} else {
    Write-Host "OK - Inicio manual" -ForegroundColor Green
}

# ====================================
# RESUMEN FINAL
# ====================================
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  INSTALACION COMPLETADA EXITOSAMENTE" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

Write-Host "Software instalado:" -ForegroundColor Cyan
Write-Host "  - Git for Windows" -ForegroundColor White
Write-Host "  - Python 3.11" -ForegroundColor White
Write-Host "  - Node.js LTS" -ForegroundColor White
Write-Host "  - FFmpeg" -ForegroundColor White
Write-Host "  - Tailscale VPN" -ForegroundColor White
Write-Host ""

Write-Host "Ubicacion del proyecto:" -ForegroundColor Cyan
Write-Host "  $INSTALL_DIR" -ForegroundColor White
Write-Host ""

Write-Host "Scripts disponibles:" -ForegroundColor Cyan
Write-Host "  - INICIAR_SISTEMA.bat" -ForegroundColor White
Write-Host "  - DETENER_SISTEMA.bat" -ForegroundColor White
Write-Host "  - VERIFICAR_SISTEMA.bat" -ForegroundColor White
Write-Host ""

Write-Host "Proximos pasos:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Verifica que Tailscale este autenticado:" -ForegroundColor White
Write-Host "   tailscale status" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Verifica que puedes ver las camaras:" -ForegroundColor White
Write-Host "   ping 192.168.0.8" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Inicia el sistema:" -ForegroundColor White
Write-Host "   $INSTALL_DIR\INICIAR_SISTEMA.bat" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Verifica que funciona:" -ForegroundColor White
Write-Host "   $INSTALL_DIR\VERIFICAR_SISTEMA.bat" -ForegroundColor Gray
Write-Host ""

Write-Host "============================================" -ForegroundColor Green
Write-Host "  LISTO PARA USAR" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

pause
