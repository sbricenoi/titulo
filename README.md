# Sistema de Monitoreo de Hurones con IA

Sistema completo para grabación, análisis y clasificación de videos de hurones usando YOLOv8 y arquitectura híbrida (local + cloud).

## 📦 Contenido

- **`video-recording-system/`**: Sistema de grabación local multi-cámara con upload automático a S3
- **`frontend/`**: Backoffice Angular para clasificación de comportamientos detectados
- **Scripts de instalación Windows**: Instalador automático completo

## 🚀 Instalación Rápida (Windows)

### Instalación Automática (Recomendado)

1. Clonar el repositorio:
```bash
git clone https://github.com/sbricenoi/titulo.git
cd titulo
```

2. Ejecutar instalador (click derecho > Ejecutar como administrador):
```bash
INSTALAR_SIMPLE.bat
```

3. Esperar 30-60 minutos (instalación automática de todo)

### Instalación Manual

Ver `INSTALACION_WINDOWS.md` para instrucciones detalladas.

## 📋 Requisitos

- Windows 10/11
- Conexión a internet
- Permisos de administrador
- 20 GB espacio en disco

## 🎥 Cámaras

El sistema soporta múltiples cámaras RTSP:
- Protocolo RTSP
- Grabación en segmentos de 2 minutos
- Upload automático a AWS S3
- Eliminación automática post-upload (ahorra espacio)

## ☁️ Arquitectura

### Local (Grabación)
- FFmpeg para captura RTSP
- Python watchdog para monitoreo
- Boto3 para upload a S3
- Logs con Loguru

### Cloud (Procesamiento)
- AWS S3 para almacenamiento
- YOLOv8 para detección
- FastAPI para clasificación
- Angular para backoffice

## 🔧 Configuración

Después de la instalación, editar `.env` en `video-recording-system/`:

```ini
# Cámaras
CAMERA_1_URL=rtsp://admin:PASSWORD@IP:554/h264Preview_01_main
CAMERA_2_URL=rtsp://admin:PASSWORD@IP:554/h264Preview_01_main
CAMERA_3_URL=rtsp://admin:PASSWORD@IP:554/h264Preview_01_main

# AWS
AWS_ACCESS_KEY_ID=<TU_AWS_ACCESS_KEY>
AWS_SECRET_ACCESS_KEY=<TU_AWS_SECRET_KEY>
AWS_REGION=us-east-1
S3_BUCKET_NAME=ferret-recordings

# Grabación
RECORDING_DURATION=120
DELETE_IMMEDIATELY_AFTER_UPLOAD=true
```

## 📝 Uso

### Iniciar sistema:
```bash
cd video-recording-system
python services/video_recorder.py
python services/s3_uploader.py
```

### Frontend (clasificación):
```bash
cd frontend
npm start
```

Abrir: `http://localhost:4200`

## 🆘 Soporte

Ver documentación:
- `INSTALACION_WINDOWS.md` - Guía completa
- `README_WINDOWS.txt` - Inicio rápido
- `INSTRUCCIONES_WINDOWS.txt` - Pasos resumidos

## 🔒 Seguridad

- ⚠️ **NO committear** archivos `.env` con credenciales
- ⚠️ **NO committear** archivos `.pem` o `.key`
- ✅ Usar `env.example` como plantilla
