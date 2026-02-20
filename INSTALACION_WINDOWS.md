# 🪟 Instalación Completa en Windows - Sistema de Cámaras

## 🎯 Objetivo

Configurar un equipo Windows dedicado que funcione 24/7 como gateway para las cámaras, permitiendo que Lightsail grabe sin depender de tu Mac.

---

## 📋 Requisitos del Equipo Windows

- Windows 10 o 11
- 4 GB RAM mínimo (8 GB recomendado)
- 50 GB espacio en disco
- Conexión ethernet al router (recomendado) o WiFi estable
- Siempre conectado a la corriente

---

## 🚀 Instalación Paso a Paso

### PASO 1: Instalar Software Base (30 minutos)

#### 1.1 Git for Windows

```powershell
# Descargar desde:
https://git-scm.com/download/win

# O instalar con winget (Windows 11):
winget install Git.Git
```

**Durante instalación:**
- Dejar opciones por defecto
- Marcar "Add to PATH"

#### 1.2 Python 3.10+

```powershell
# Descargar desde:
https://www.python.org/downloads/

# O instalar con winget:
winget install Python.Python.3.11
```

**⚠️ IMPORTANTE durante instalación:**
- ✅ Marcar "Add Python to PATH"
- ✅ Marcar "Install pip"

**Verificar instalación:**
```powershell
python --version
pip --version
```

#### 1.3 Node.js (para frontend Angular)

```powershell
# Descargar desde:
https://nodejs.org/

# O instalar con winget:
winget install OpenJS.NodeJS.LTS
```

**Verificar instalación:**
```powershell
node --version
npm --version
```

#### 1.4 FFmpeg

```powershell
# Descargar desde:
https://www.gyan.dev/ffmpeg/builds/

# Descargar: ffmpeg-release-essentials.zip
# Extraer a: C:\ffmpeg
```

**Agregar FFmpeg al PATH:**
1. Buscar "Variables de entorno" en inicio
2. Click en "Variables de entorno"
3. En "Path" de usuario, click "Editar"
4. Click "Nuevo"
5. Agregar: `C:\ffmpeg\bin`
6. Click "Aceptar"

**Verificar:**
```powershell
ffmpeg -version
```

---

### PASO 2: Instalar Tailscale VPN (10 minutos)

```powershell
# Descargar desde:
https://tailscale.com/download/windows

# O instalar con winget:
winget install Tailscale.Tailscale
```

**Configuración:**
1. Ejecutar Tailscale
2. Click en "Log in"
3. Autenticar con tu cuenta Tailscale (la que creaste)
4. Una vez autenticado, abrir PowerShell como **Administrador**:

```powershell
# Habilitar subnet routing (CRÍTICO)
tailscale up --advertise-routes=192.168.0.0/24

# Verificar IP de Tailscale
tailscale ip -4
```

5. **Ir a Tailscale Admin** (https://login.tailscale.com/admin/machines)
6. Buscar el equipo Windows
7. Click en "..." → "Edit route settings"
8. **Aprobar** la ruta `192.168.0.0/24`

---

### PASO 3: Clonar el Proyecto (5 minutos)

```powershell
# Abrir PowerShell
cd C:\
git clone https://github.com/TU-USUARIO/titulo.git
cd titulo
```

**Si no tienes GitHub aún:**

Desde tu Mac, copia el proyecto al Windows:
```bash
# Comprimir proyecto (en Mac)
cd /Users/sbriceno/Documents/projects/titulo
tar -czf titulo-proyecto.tar.gz \
    --exclude='node_modules' \
    --exclude='venv' \
    --exclude='*.mp4' \
    --exclude='*.jpg' \
    --exclude='*.db' \
    --exclude='logs/*' \
    --exclude='data/videos/*' \
    .

# Copiar al Windows (ajusta IP del Windows)
scp titulo-proyecto.tar.gz usuario@IP_WINDOWS:C:\
```

En Windows:
```powershell
cd C:\
tar -xzf titulo-proyecto.tar.gz
cd titulo
```

---

### PASO 4: Configurar Entorno Python (15 minutos)

```powershell
# En C:\titulo
cd C:\titulo

# Crear entorno virtual
python -m venv venv

# Activar entorno
.\venv\Scripts\Activate.ps1

# Si da error de ejecución, ejecutar primero:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Luego activar de nuevo:
.\venv\Scripts\Activate.ps1

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-recorder.txt

# Verificar instalación
python -c "import ultralytics; print('YOLOv8 OK')"
```

---

### PASO 5: Configurar .env (5 minutos)

```powershell
# Copiar configuración
cd C:\titulo\video-recording-system
copy env.example .env

# Editar .env con Notepad
notepad .env
```

**Configuración del .env:**
```ini
# AWS S3
AWS_ACCESS_KEY_ID=<TU_AWS_ACCESS_KEY>
AWS_SECRET_ACCESS_KEY=<TU_AWS_SECRET_KEY>
AWS_REGION=us-east-1
S3_BUCKET_NAME=ferret-recordings

# CÁMARAS (acceso local, Tailscale permite esto)
CAMERA_1_URL=rtsp://admin:Sb123456@192.168.0.8:554/h264Preview_01_main
CAMERA_1_NAME=Reolink_Huron_Principal

CAMERA_2_URL=rtsp://admin:Sb123456@192.168.0.9:554/h264Preview_01_main
CAMERA_2_NAME=Reolink_Huron_Secundaria

CAMERA_3_URL=rtsp://admin:Sb123456@192.168.0.7:554/h264Preview_01_main
CAMERA_3_NAME=Reolink_Huron_3

# Configuración de grabación
SEGMENT_DURATION=600
VIDEO_CODEC=copy
LOCAL_RETENTION_HOURS=24
LOG_LEVEL=INFO

# Paths Windows
BASE_DIR=C:/titulo
RECORDINGS_DIR=C:/titulo/data/videos/recordings
COMPLETED_DIR=C:/titulo/data/videos/completed
UPLOADED_DIR=C:/titulo/data/videos/uploaded
```

**Guardar** y cerrar Notepad.

---

### PASO 6: Crear Directorios (2 minutos)

```powershell
# Crear estructura de directorios
cd C:\titulo
mkdir -p data\videos\recordings
mkdir -p data\videos\completed
mkdir -p data\videos\uploaded
mkdir -p data\frames_for_classification
mkdir -p data\analysis_results
mkdir -p data\smart_analysis_results
mkdir -p logs
```

---

### PASO 7: Crear Scripts de Inicio Automático (10 minutos)

#### 7.1 Script para Iniciar Todo

```powershell
# Crear archivo
cd C:\titulo
notepad INICIAR_SISTEMA_WINDOWS.bat
```

**Contenido del archivo:**
```batch
@echo off
echo ============================================
echo  SISTEMA DE CAMARAS - INICIANDO
echo ============================================
echo.

REM Activar entorno virtual
call C:\titulo\venv\Scripts\activate.bat

REM Verificar Tailscale
echo [1/3] Verificando Tailscale...
tailscale status
if %errorlevel% neq 0 (
    echo ERROR: Tailscale no esta corriendo
    echo Inicia Tailscale primero
    pause
    exit /b 1
)
echo OK - Tailscale activo
echo.

REM Iniciar Video Recorder
echo [2/3] Iniciando grabacion de camaras...
cd C:\titulo\video-recording-system
start "Video Recorder" /MIN python services\video_recorder.py
timeout /t 3
echo OK - Video Recorder iniciado
echo.

REM Iniciar S3 Uploader
echo [3/3] Iniciando uploader a S3...
start "S3 Uploader" /MIN python services\s3_uploader.py
timeout /t 3
echo OK - S3 Uploader iniciado
echo.

echo ============================================
echo  SISTEMA INICIADO CORRECTAMENTE
echo ============================================
echo.
echo Procesos corriendo en segundo plano:
echo  - Video Recorder (grabacion)
echo  - S3 Uploader (upload a S3)
echo.
echo Para ver logs:
echo   C:\titulo\logs\recorder.log
echo   C:\titulo\logs\uploader.log
echo.
echo Presiona cualquier tecla para cerrar esta ventana
echo (los procesos seguiran corriendo en segundo plano)
pause > nul
```

**Guardar** y cerrar.

#### 7.2 Script para Detener Todo

```powershell
notepad DETENER_SISTEMA_WINDOWS.bat
```

**Contenido:**
```batch
@echo off
echo Deteniendo sistema...

REM Matar procesos de Python relacionados
taskkill /F /FI "WINDOWTITLE eq Video Recorder*" 2>nul
taskkill /F /FI "WINDOWTITLE eq S3 Uploader*" 2>nul

echo Sistema detenido
pause
```

**Guardar** y cerrar.

#### 7.3 Script de Verificación

```powershell
notepad VERIFICAR_SISTEMA_WINDOWS.bat
```

**Contenido:**
```batch
@echo off
echo ============================================
echo  VERIFICACION DEL SISTEMA
echo ============================================
echo.

echo [1] Verificando Tailscale...
tailscale status | findstr "100."
if %errorlevel% equ 0 (
    echo OK - Tailscale activo
) else (
    echo ERROR - Tailscale no activo
)
echo.

echo [2] Verificando camaras...
ping -n 1 192.168.0.8 > nul
if %errorlevel% equ 0 (
    echo OK - Camara 1 accesible
) else (
    echo ERROR - Camara 1 NO accesible
)

ping -n 1 192.168.0.9 > nul
if %errorlevel% equ 0 (
    echo OK - Camara 2 accesible
) else (
    echo ERROR - Camara 2 NO accesible
)

ping -n 1 192.168.0.7 > nul
if %errorlevel% equ 0 (
    echo OK - Camara 3 accesible
) else (
    echo ERROR - Camara 3 NO accesible
)
echo.

echo [3] Verificando procesos...
tasklist | findstr python > nul
if %errorlevel% equ 0 (
    echo OK - Python corriendo
) else (
    echo ERROR - Python NO corriendo
)
echo.

echo [4] Verificando videos...
dir C:\titulo\data\videos\recordings | findstr ".mp4"
echo.

echo ============================================
echo  VERIFICACION COMPLETADA
echo ============================================
pause
```

**Guardar** y cerrar.

---

### PASO 8: Configurar Inicio Automático con Windows (15 minutos)

Para que el sistema inicie automáticamente al encender Windows:

#### Opción 1: Inicio Simple

1. Presiona `Win + R`
2. Escribe: `shell:startup`
3. Se abre carpeta de "Inicio"
4. Click derecho → "Nuevo" → "Acceso directo"
5. Ubicación: `C:\titulo\INICIAR_SISTEMA_WINDOWS.bat`
6. Nombre: "Sistema Cámaras"
7. Click "Finalizar"

**Ahora el sistema se iniciará automáticamente al arrancar Windows**

#### Opción 2: Como Servicio de Windows (Más profesional)

```powershell
# Instalar NSSM (Non-Sucking Service Manager)
winget install NSSM.NSSM

# O descargar manualmente:
# https://nssm.cc/download

# Crear servicio para Video Recorder
nssm install CameraRecorder "C:\titulo\venv\Scripts\python.exe" "C:\titulo\video-recording-system\services\video_recorder.py"
nssm set CameraRecorder AppDirectory "C:\titulo\video-recording-system"
nssm set CameraRecorder Start SERVICE_AUTO_START

# Crear servicio para S3 Uploader
nssm install S3Uploader "C:\titulo\venv\Scripts\python.exe" "C:\titulo\video-recording-system\services\s3_uploader.py"
nssm set S3Uploader AppDirectory "C:\titulo\video-recording-system"
nssm set S3Uploader Start SERVICE_AUTO_START

# Iniciar servicios
nssm start CameraRecorder
nssm start S3Uploader
```

---

### PASO 9: Configurar Lightsail (Ya hecho ✅)

La configuración de Lightsail ya está lista. Solo necesitas:

```bash
# En Lightsail, las cámaras ahora son accesibles vía Tailscale
# usando las IPs locales: 192.168.0.8, .9, .7
```

El `.env` en Lightsail ya tiene las URLs correctas.

---

## ✅ PRUEBA FINAL

### 1. Iniciar Sistema

```powershell
cd C:\titulo
.\INICIAR_SISTEMA_WINDOWS.bat
```

### 2. Verificar

```powershell
.\VERIFICAR_SISTEMA_WINDOWS.bat
```

### 3. Ver Logs

```powershell
# Ver grabación
type C:\titulo\logs\recorder.log

# Ver uploads
type C:\titulo\logs\uploader.log
```

### 4. Verificar Videos

```powershell
dir C:\titulo\data\videos\recordings
```

Deberías ver archivos `.mp4` nuevos cada 10 minutos.

---

## 🔧 Mantenimiento

### Reiniciar Sistema

```powershell
.\DETENER_SISTEMA_WINDOWS.bat
.\INICIAR_SISTEMA_WINDOWS.bat
```

### Ver Estado

```powershell
.\VERIFICAR_SISTEMA_WINDOWS.bat
```

### Limpiar Videos Viejos

```powershell
# Los videos se eliminan automáticamente después de 24h
# Si quieres limpiar manualmente:
del /Q C:\titulo\data\videos\uploaded\*.mp4
```

---

## 📊 Configuración de Energía

Para que Windows no se duerma:

1. `Win + X` → "Opciones de energía"
2. "Configuración adicional de energía"
3. "Cambiar la configuración del plan"
4. "Suspender el equipo": **Nunca**
5. "Apagar pantalla": 30 minutos (opcional)

---

## 🐛 Troubleshooting

### Python no se encuentra

```powershell
# Verificar PATH
python --version

# Si falla, agregar manualmente:
# Variables de entorno → Path → Agregar:
# C:\Users\TU_USUARIO\AppData\Local\Programs\Python\Python311
```

### Tailscale no conecta

```powershell
# Reiniciar Tailscale
net stop Tailscale
net start Tailscale

# Verificar
tailscale status
```

### FFmpeg no se encuentra

```powershell
# Verificar PATH
ffmpeg -version

# Si falla, verificar que C:\ffmpeg\bin esté en PATH
```

### No graba videos

```powershell
# Verificar que Tailscale esté corriendo
tailscale status

# Verificar que puedes ver las cámaras
ping 192.168.0.8

# Ver logs
type C:\titulo\logs\recorder.log
```

---

## 📝 Resumen de Comandos Rápidos

```powershell
# Iniciar sistema
C:\titulo\INICIAR_SISTEMA_WINDOWS.bat

# Detener sistema
C:\titulo\DETENER_SISTEMA_WINDOWS.bat

# Verificar sistema
C:\titulo\VERIFICAR_SISTEMA_WINDOWS.bat

# Ver logs
type C:\titulo\logs\recorder.log
type C:\titulo\logs\uploader.log

# Ver videos
dir C:\titulo\data\videos\recordings
```

---

## 🎯 Checklist Final

- [ ] Git instalado y en PATH
- [ ] Python instalado y en PATH
- [ ] Node.js instalado
- [ ] FFmpeg instalado y en PATH
- [ ] Tailscale instalado y autenticado
- [ ] Subnet routes aprobado en Tailscale Admin
- [ ] Proyecto clonado en C:\titulo
- [ ] Entorno virtual creado
- [ ] Dependencias instaladas
- [ ] .env configurado
- [ ] Directorios creados
- [ ] Scripts .bat creados
- [ ] Scripts agregados a Inicio (opcional)
- [ ] Configuración de energía ajustada
- [ ] Sistema probado y funcionando

---

**¡Listo! El sistema Windows quedará funcionando 24/7 sin intervención.**
