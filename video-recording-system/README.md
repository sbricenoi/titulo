# 🎥 Sistema de Grabación y Upload a S3

Sistema automatizado de grabación continua desde cámaras Reolink con upload automático a AWS S3.

## 📋 Descripción

Este módulo captura streams RTSP de múltiples cámaras Reolink, los segmenta en archivos MP4 de duración configurable, y los sube automáticamente a AWS S3 manteniendo retención local configurable.

### Características

- ✅ Grabación continua 24/7 desde múltiples cámaras
- ✅ Segmentación automática de videos (duración configurable)
- ✅ Upload automático a S3 con retry logic
- ✅ Retención local configurable (por defecto 24 horas)
- ✅ Monitoreo y reinicio automático de procesos
- ✅ Detección de procesos "zombie" (FFmpeg colgado)
- ✅ Logs estructurados con Loguru
- ✅ Metadata correcto para reproducción directa en navegador

## 🏗️ Arquitectura

```
Cámaras Reolink (RTSP)
         |
         v
  video_recorder.py
    (FFmpeg Process)
         |
         v
    recordings/
         |
         v
   s3_uploader.py
    (Watchdog)
         |
         v
      AWS S3
         |
         v
    uploaded/
    (retention)
```

## 📂 Estructura

```
video-recording-system/
├── services/
│   ├── video_recorder.py      # Servicio principal de grabación
│   ├── s3_uploader.py          # Servicio de upload a S3
│   └── recorder_config.py      # Configuración compartida
├── scripts/
│   └── (scripts auxiliares)
├── data/
│   └── logs/                   # Logs del sistema
├── recordings/                 # Videos grabados (temporal)
├── uploaded/                   # Videos ya subidos (retención local)
├── .env                        # Configuración (NO subir a git)
├── requirements.txt            # Dependencias Python
├── INICIAR_SISTEMA_FINAL.sh    # Script de inicio
├── stop_recorder_robusto.sh    # Script de detención
└── REINICIAR_SISTEMA_LIMPIO.sh # Script de reinicio limpio
```

## 🚀 Inicio Rápido

### 1. Instalar Dependencias

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configurar `.env`

```env
# AWS
AWS_ACCESS_KEY_ID=AKIAXXXXXXXX
AWS_SECRET_ACCESS_KEY=xxxxxxxxxx
AWS_REGION=us-east-1
S3_BUCKET_NAME=ferret-recordings

# Cámaras
CAMERA_1_URL=rtsp://admin:PASSWORD@192.168.0.5:554/Preview_01_main
CAMERA_1_NAME=Reolink_Principal
CAMERA_2_URL=rtsp://admin:PASSWORD@192.168.0.6:554/h264Preview_01_main
CAMERA_2_NAME=Reolink_Secundaria

# Configuración
SEGMENT_DURATION=600        # 10 minutos
LOG_LEVEL=INFO
LOCAL_RETENTION_HOURS=24
```

### 3. Iniciar Sistema

```bash
./INICIAR_SISTEMA_FINAL.sh
```

### 4. Monitorear

```bash
# Ver logs en tiempo real
tail -f data/logs/recorder_*.log
tail -f data/logs/uploader_*.log

# Ver procesos
ps aux | grep python
ps aux | grep ffmpeg

# Ver archivos
ls -lh recordings/
```

### 5. Detener Sistema

```bash
./stop_recorder_robusto.sh
```

## ⚙️ Configuración

### Variables de Entorno (`.env`)

#### AWS Credentials
- `AWS_ACCESS_KEY_ID` - Access Key del usuario IAM
- `AWS_SECRET_ACCESS_KEY` - Secret Key del usuario IAM
- `AWS_REGION` - Región de AWS (ej: `us-east-1`)
- `S3_BUCKET_NAME` - Nombre del bucket S3

#### Cámaras
Para cada cámara (1, 2, 3, ...):
- `CAMERA_N_URL` - URL RTSP completa
- `CAMERA_N_NAME` - Nombre descriptivo (usado en nombres de archivo)

**Formato URL RTSP:**
```
rtsp://[usuario]:[password]@[ip]:[puerto]/[path]
```

**Ejemplos de paths según modelo Reolink:**
- `Preview_01_main` - Stream principal (algunos modelos)
- `h264Preview_01_main` - Stream H264 (otros modelos)
- `Preview_01_sub` - Stream de baja resolución (substream)

#### Configuración de Grabación
- `SEGMENT_DURATION` - Duración de cada segmento en segundos (ej: `600` = 10 min)
- `VIDEO_CODEC` - Codec de video:
  - `copy` - Sin re-encoding (recomendado, menor CPU)
  - `h264` - Re-encode a H264
- `VIDEO_FORMAT` - Formato de salida (ej: `mp4`)
- `LOCAL_RETENTION_HOURS` - Horas que los videos permanecen localmente después de subirse
- `LOG_LEVEL` - Nivel de logging: `DEBUG`, `INFO`, `WARNING`, `ERROR`
- `BASE_DIR` - Directorio base del sistema

## 🔧 Componentes

### video_recorder.py

**Funciones principales:**
- Gestiona procesos FFmpeg para cada cámara
- Monitorea salud de procesos (detección de "zombies")
- Reinicia automáticamente procesos caídos o colgados
- Genera nombres de archivo con timestamp

**Algoritmo de detección de "zombie":**
1. Verificar si proceso existe (`poll()`)
2. Verificar si FFmpeg tiene archivos `.mp4` abiertos (`lsof`)
3. Verificar si hay archivos `.mp4` recientes (últimos 3 minutos)
4. Si ninguna condición se cumple → reiniciar proceso

**Comando FFmpeg generado:**
```bash
ffmpeg -rtsp_transport tcp \
       -i "rtsp://..." \
       -c:v copy \
       -c:a aac \
       -f segment \
       -segment_time 600 \
       -segment_format mp4 \
       -strftime 1 \
       -reset_timestamps 1 \
       "recordings/CameraName_%Y%m%d_%H%M%S.mp4"
```

### s3_uploader.py

**Funciones principales:**
- Monitorea directorio `recordings/` con Watchdog
- Detecta nuevos archivos `.mp4`
- Verifica estabilidad de archivos (no están siendo escritos)
- Sube a S3 con metadata correcto
- Mueve archivos subidos a `uploaded/`
- Elimina archivos antiguos según retención

**Metadata S3 configurado:**
```python
ExtraArgs={
    'StorageClass': 'STANDARD',
    'ServerSideEncryption': 'AES256',
    'ContentType': 'video/mp4',
    'ContentDisposition': 'inline',  # Reproducción directa en navegador
    'CacheControl': 'max-age=31536000'
}
```

**Retry Logic:**
- Archivos incompletos se revisan cada 30 segundos
- Un archivo se considera "completo" si:
  - No ha sido modificado en 60+ segundos
  - Tiene tamaño > 1MB

### recorder_config.py

**Funciones principales:**
- Carga configuración desde `.env`
- Valida presencia de variables requeridas
- Proporciona configuración a otros módulos

## 📝 Logs

Los logs se almacenan en `data/logs/` con rotación automática:

- `recorder_YYYY-MM-DD_HH-MM-SS.log` - Logs del grabador
- `uploader_YYYY-MM-DD_HH-MM-SS.log` - Logs del uploader

**Formato de log:**
```
2025-01-25 15:30:45.123 | INFO     | Reolink_Principal: Iniciando grabación
2025-01-25 15:30:45.456 | INFO     | FFmpeg PID: 12345
2025-01-25 15:40:50.789 | INFO     | Archivo completado: CameraName_20250125_153045.mp4
2025-01-25 15:40:51.012 | INFO     | Upload exitoso a S3: recordings/2025/01/25/...
```

## 🐛 Troubleshooting

### Problema: FFmpeg no conecta a cámara

**Error:** `Connection refused` o `timeout`

**Solución:**
```bash
# 1. Verificar conectividad
ping 192.168.0.5
nc -zv 192.168.0.5 554

# 2. Probar RTSP manualmente
ffplay "rtsp://admin:PASSWORD@192.168.0.5:554/Preview_01_main"

# 3. Verificar RTSP habilitado en cámara
```

### Problema: Videos no suben a S3

**Error:** `AccessDenied` o `NoSuchBucket`

**Solución:**
```bash
# 1. Verificar credenciales
aws s3 ls s3://ferret-recordings/

# 2. Verificar permisos IAM (debe tener S3 FullAccess o custom policy)

# 3. Revisar logs
tail -f data/logs/uploader_*.log
```

### Problema: Proceso FFmpeg "zombie" (0% CPU, no graba)

**Síntomas:** Proceso existe pero no crea nuevos archivos

**Solución:**
El sistema detecta esto automáticamente y reinicia el proceso. Si persiste:
```bash
# Ver procesos FFmpeg
ps aux | grep ffmpeg

# Ver archivos abiertos por FFmpeg
lsof -p [PID_FFMPEG] | grep .mp4

# Reiniciar limpio
./REINICIAR_SISTEMA_LIMPIO.sh
```

### Problema: Alto uso de CPU

**Causa:** Re-encoding de video

**Solución:**
```env
# Cambiar en .env:
VIDEO_CODEC=copy  # Sin re-encoding (recomendado)
```

### Problema: Archivos quedan en `recordings/` sin subirse

**Causa:** Archivo siendo escrito o inestable

**Solución:**
El uploader reintenta automáticamente cada 30 segundos. Verifica logs:
```bash
tail -f data/logs/uploader_*.log | grep "pendiente\|retry"
```

## 📊 Monitoreo

### Verificar que todo funciona

```bash
# 1. Procesos corriendo
ps aux | grep "video_recorder.py"
ps aux | grep "s3_uploader.py"
ps aux | grep ffmpeg

# 2. Archivos generándose
watch -n 5 'ls -lht recordings/ | head -5'

# 3. Archivos en S3
aws s3 ls s3://ferret-recordings/recordings/ --recursive

# 4. Logs sin errores
tail -n 100 data/logs/recorder_*.log | grep ERROR
tail -n 100 data/logs/uploader_*.log | grep ERROR
```

## 🔒 Seguridad

### Proteger credenciales

```bash
# NUNCA subir .env a git
# Verificar que está en .gitignore
grep .env .gitignore

# Permisos restrictivos
chmod 600 .env
```

### IAM Policy Mínima (AWS)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl",
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::ferret-recordings",
        "arn:aws:s3:::ferret-recordings/*"
      ]
    }
  ]
}
```

## 📈 Optimizaciones

### Reducir ancho de banda a S3
- Usar `VIDEO_CODEC=h264` con bitrate bajo
- Reducir resolución de cámaras
- Aumentar `SEGMENT_DURATION` (menos uploads)

### Reducir uso de CPU
- Usar `VIDEO_CODEC=copy` (sin re-encoding)
- Reducir número de cámaras simultáneas

### Reducir almacenamiento local
- Reducir `LOCAL_RETENTION_HOURS`
- Aumentar frecuencia de limpieza

## 🆘 Scripts de Mantenimiento

### Reinicio limpio
```bash
./REINICIAR_SISTEMA_LIMPIO.sh
```
- Detiene procesos
- Limpia logs antiguos
- Elimina archivos parciales
- Verifica configuración
- Reinicia sistema

### Detención robusta
```bash
./stop_recorder_robusto.sh
```
- Intenta detención graceful (SIGTERM)
- Espera 10 segundos
- Fuerza kill si necesario (SIGKILL)

### Inicio final
```bash
./INICIAR_SISTEMA_FINAL.sh
```
- Verifica configuración
- Verifica conectividad a cámaras
- Inicia procesos en background
- Muestra PIDs y ubicación de logs

---

**Desarrollado para grabación continua y confiable 24/7**
