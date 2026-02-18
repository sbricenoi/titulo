# 🎥 Servicios de Grabación de Video

Este directorio contiene los servicios para grabación continua y almacenamiento de videos de las cámaras en AWS S3.

## 📁 Estructura

```
services/
├── README.md                    # Este archivo
├── recorder_config.py           # Configuración centralizada
├── video_recorder.py            # Servicio de grabación (FFmpeg)
├── s3_uploader.py               # Servicio de subida a S3
├── monitor.sh                   # Script de monitoreo (opcional)
└── systemd/                     # Archivos para systemd
    ├── video-recorder.service
    ├── s3-uploader.service
    └── install-services.sh
```

## 🔧 Componentes

### 1. `recorder_config.py`
Configuración centralizada del sistema. Lee variables de entorno desde `.env` y define paths, configuración de AWS, cámaras, etc.

### 2. `video_recorder.py`
Servicio principal de grabación. Lanza procesos FFmpeg para cada cámara, graba en segmentos de 10 minutos, y reinicia automáticamente ante fallos.

**Características:**
- ✅ Grabación 24/7
- ✅ Segmentos de 10 minutos
- ✅ Reinicio automático
- ✅ Monitoreo de procesos
- ✅ Logs detallados

### 3. `s3_uploader.py`
Servicio de subida a S3. Detecta nuevos archivos completados, los sube a S3, verifica integridad y limpia archivos antiguos.

**Características:**
- ✅ Detección automática de archivos nuevos
- ✅ Subida a S3 con estructura organizada
- ✅ Verificación de integridad
- ✅ Limpieza automática de archivos antiguos
- ✅ Logs detallados

### 4. `systemd/`
Archivos para configurar los servicios como servicios de sistema Linux (arranque automático, reinicio ante fallas, etc.)

## 🚀 Instalación

Ver documentación completa en:
- `docs/SISTEMA_GRABACION_VIDEO.md` (guía completa)
- `INICIO_RAPIDO_GRABACION.md` (inicio rápido)

### Instalación rápida:

```bash
# 1. Instalar dependencias
pip install -r requirements-recorder.txt

# 2. Configurar .env (ver ejemplo más abajo)

# 3. Instalar servicios systemd
cd services/systemd
./install-services.sh

# 4. Iniciar servicios
sudo systemctl start video-recorder
sudo systemctl start s3-uploader
```

## 🔑 Configuración (.env)

Crear archivo `.env` en la raíz del proyecto:

```bash
# AWS
AWS_ACCESS_KEY_ID=tu-access-key
AWS_SECRET_ACCESS_KEY=tu-secret-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=ferret-recordings-tu-nombre

# Cámaras
CAMERA_1_URL=rtsp://admin:pass@192.168.0.20:554/Preview_01_main
CAMERA_1_NAME=Camera_1

CAMERA_2_URL=rtsp://admin:pass@192.168.0.21:554/Preview_01_main
CAMERA_2_NAME=Camera_2

# Configuración
SEGMENT_DURATION=600           # 10 minutos
VIDEO_CODEC=copy               # No recodificar (más eficiente)
LOCAL_RETENTION_HOURS=24       # Retención local
```

## 📊 Uso

### Comandos básicos:

```bash
# Ver estado
sudo systemctl status video-recorder s3-uploader

# Ver logs
sudo journalctl -u video-recorder -f
sudo journalctl -u s3-uploader -f

# Reiniciar
sudo systemctl restart video-recorder
sudo systemctl restart s3-uploader

# Detener
sudo systemctl stop video-recorder s3-uploader
```

### Monitoreo:

```bash
# Ver archivos locales
ls -lh /home/ubuntu/ferret-system/data/videos/recordings/

# Ver archivos en S3
aws s3 ls s3://tu-bucket/ --recursive

# Ver logs
tail -f data/logs/recorder.log
tail -f data/logs/uploader.log

# Ver uso de recursos
htop  # buscar procesos "ffmpeg" y "python3"
```

## 🏗️ Arquitectura

```
Cámaras RTSP
    ↓
video_recorder.py (FFmpeg) → /data/videos/recordings/
    ↓
s3_uploader.py → AWS S3 → /data/videos/uploaded/ → Limpieza
```

## 💰 Recursos

**Consumo por cámara:**
- CPU: ~10%
- RAM: ~250 MB
- Disco: ~650 MB por 10 minutos
- Red: ~2 Mbps

**Total (4 cámaras):**
- CPU: ~40%
- RAM: ~1.5 GB
- Disco: ~80 GB por 24h (con limpieza)
- Red: ~8 Mbps

## 🐛 Troubleshooting

### FFmpeg no se conecta a cámaras
```bash
# Verificar que la URL es accesible
ffmpeg -i "rtsp://admin:pass@ip:port/path" -t 5 test.mp4
```

### No sube a S3
```bash
# Verificar credenciales AWS
aws s3 ls s3://tu-bucket/
```

### Disco lleno
```bash
# Limpiar manualmente
rm /home/ubuntu/ferret-system/data/videos/uploaded/*.mp4

# O reducir retención en .env
LOCAL_RETENTION_HOURS=12
```

## 📚 Documentación

- **Guía completa**: `docs/SISTEMA_GRABACION_VIDEO.md`
- **Inicio rápido**: `INICIO_RAPIDO_GRABACION.md`
- **Dependencias**: `requirements-recorder.txt`

## 📝 Notas

- Los servicios se reinician automáticamente ante fallos
- Los logs rotan automáticamente (100 MB, 30 días retención)
- Los archivos locales se limpian después de 24h por defecto
- S3 tiene lifecycle policy para mover a Glacier después de 30 días

---

**Versión**: 1.0  
**Fecha**: 2026-01-24  
**Estado**: Listo para producción
