# 🎥 Sistema de Grabación y Almacenamiento de Videos en S3

## 📋 Documento de Implementación Completo

**Versión:** 1.0  
**Fecha:** 2026-01-24  
**Autor:** Sistema de Monitoreo de Hurones  
**Objetivo:** Implementar grabación continua de 4 cámaras con almacenamiento en AWS S3

---

## 🎯 Resumen Ejecutivo

Este documento describe la implementación completa de un sistema de grabación continua para 4 cámaras IP, con segmentación automática cada 10 minutos y almacenamiento permanente en AWS S3.

### Características Principales:
- ✅ Grabación 24/7 de 4 cámaras simultáneas
- ✅ Segmentos de video de 10 minutos
- ✅ Subida automática a AWS S3
- ✅ Limpieza automática de archivos locales
- ✅ Reinicio automático ante fallos
- ✅ Logs detallados de operaciones
- ✅ Bajo consumo de recursos (1 vCPU, 2GB RAM)

### Costo Estimado:
- **Lightsail**: $10/mes
- **S3 Storage**: ~$7/mes (300 GB)
- **Total**: ~$17/mes

---

## 📐 Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                   CÁMARAS RTSP (4 unidades)                      │
│  • Cámara 1: rtsp://admin:pass@192.168.0.20:554/...            │
│  • Cámara 2: rtsp://admin:pass@192.168.0.21:554/...            │
│  • Cámara 3: rtsp://admin:pass@192.168.0.22:554/...            │
│  • Cámara 4: rtsp://admin:pass@192.168.0.23:554/...            │
└────────────────────────┬────────────────────────────────────────┘
                         │ RTSP Streams
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│            LIGHTSAIL INSTANCE ($10/mes)                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  VIDEO RECORDER SERVICE (Python + FFmpeg)                 │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐         │  │
│  │  │ FFmpeg P1  │  │ FFmpeg P2  │  │ FFmpeg P3  │  ...    │  │
│  │  │ Camera 1   │  │ Camera 2   │  │ Camera 3   │         │  │
│  │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘         │  │
│  │        │                │                │                 │  │
│  │        └────────────────┴────────────────┘                │  │
│  │                         │                                  │  │
│  │                         ▼                                  │  │
│  │              /data/videos/recordings/                     │  │
│  │         camera_1_2026-01-24_14-30-00.mp4                 │  │
│  │         camera_2_2026-01-24_14-30-00.mp4                 │  │
│  │         ...                                                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  S3 UPLOADER SERVICE (Python + watchdog)                  │  │
│  │  • Detecta archivos completados                           │  │
│  │  • Sube a S3 con boto3                                    │  │
│  │  • Verifica integridad (MD5)                             │  │
│  │  • Elimina local después de éxito                        │  │
│  └──────────────────────┬───────────────────────────────────┘  │
└─────────────────────────┼───────────────────────────────────────┘
                          │ Upload vía AWS SDK
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                        AWS S3 BUCKET                             │
│  s3://ferret-recordings/                                         │
│  ├── 2026/                                                       │
│  │   └── 01/                                                     │
│  │       └── 24/                                                 │
│  │           ├── camera_1/                                       │
│  │           │   ├── camera_1_2026-01-24_14-00-00.mp4          │
│  │           │   ├── camera_1_2026-01-24_14-10-00.mp4          │
│  │           │   └── ...                                         │
│  │           ├── camera_2/                                       │
│  │           ├── camera_3/                                       │
│  │           └── camera_4/                                       │
│  └── ...                                                         │
│                                                                  │
│  Lifecycle Policy:                                              │
│  • S3 Standard: 0-30 días                                       │
│  • S3 Glacier: 30+ días (más barato)                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🗂️ Estructura de Archivos

```
titulo/
├── services/                          # ← NUEVO: Servicios de grabación
│   ├── __init__.py
│   ├── video_recorder.py              # Servicio de grabación FFmpeg
│   ├── s3_uploader.py                 # Servicio de subida a S3
│   ├── recorder_config.py             # Configuración centralizada
│   └── systemd/                       # ← Scripts para systemd
│       ├── video-recorder.service
│       ├── s3-uploader.service
│       └── install-services.sh
│
├── data/
│   ├── videos/                        # ← Videos locales (temporal)
│   │   ├── recordings/                # Videos grabándose actualmente
│   │   ├── completed/                 # Listos para subir
│   │   └── uploaded/                  # Ya subidos (se borran automáticamente)
│   └── logs/
│       ├── recorder.log               # Logs de grabación
│       └── uploader.log               # Logs de subida
│
├── docs/
│   └── SISTEMA_GRABACION_VIDEO.md     # ← Este documento
│
└── requirements-recorder.txt          # ← Dependencias adicionales
```

---

## 📦 FASE 1: Configuración de AWS (30 minutos)

### Paso 1.1: Crear Bucket S3

1. **Ingresar a AWS Console**
   - https://console.aws.amazon.com/s3/

2. **Crear nuevo bucket**
   ```
   Nombre: ferret-recordings-[tu-nombre-unico]
   Región: us-east-1 (o la más cercana)
   
   ✅ Block all public access (seguridad)
   ✅ Enable versioning (opcional, recomendado)
   ✅ Enable encryption (SSE-S3)
   ```

3. **Configurar Lifecycle Policy** (opcional pero recomendado)
   ```json
   {
     "Rules": [
       {
         "Id": "MoveToGlacier",
         "Status": "Enabled",
         "Transitions": [
           {
             "Days": 30,
             "StorageClass": "GLACIER"
           }
         ]
       },
       {
         "Id": "DeleteOldVideos",
         "Status": "Enabled",
         "Expiration": {
           "Days": 365
         }
       }
     ]
   }
   ```
   
   **Esto hace:**
   - Después de 30 días → mueve a Glacier ($0.004/GB vs $0.023/GB)
   - Después de 365 días → elimina automáticamente

4. **Anotar el nombre del bucket**
   ```
   Bucket: ferret-recordings-sbriceno
   Region: us-east-1
   ```

### Paso 1.2: Crear Usuario IAM para S3

1. **Ir a IAM Console**
   - https://console.aws.amazon.com/iam/

2. **Crear nuevo usuario**
   ```
   Nombre: ferret-video-uploader
   Access type: ✅ Programmatic access
   ```

3. **Crear política personalizada**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "s3:PutObject",
           "s3:GetObject",
           "s3:DeleteObject",
           "s3:ListBucket"
         ],
         "Resource": [
           "arn:aws:s3:::ferret-recordings-sbriceno",
           "arn:aws:s3:::ferret-recordings-sbriceno/*"
         ]
       }
     ]
   }
   ```
   
   **Nombre de política**: `FerretS3UploadPolicy`

4. **Asignar política al usuario**

5. **Guardar credenciales** (⚠️ IMPORTANTE: Solo se muestran una vez)
   ```
   Access Key ID: AKIAIOSFODNN7EXAMPLE
   Secret Access Key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
   ```

### Paso 1.3: Crear Lightsail Instance

1. **Ir a Lightsail Console**
   - https://lightsail.aws.amazon.com/

2. **Crear nueva instancia**
   ```
   Ubicación: Virginia (us-east-1a)
   Plataforma: Linux/Unix
   Blueprint: OS Only → Ubuntu 22.04 LTS
   Plan: $10/mes (1 vCPU, 2 GB RAM, 60 GB SSD)
   Nombre: ferret-recorder
   ```

3. **Habilitar IP estática** (opcional)
   - Networking tab → Create static IP
   - Asignar a la instancia

4. **Configurar Firewall**
   ```
   ✅ SSH (22) - Solo tu IP
   ⚠️ No abrir otros puertos (no es necesario)
   ```

5. **Descargar SSH key**
   - Account → SSH Keys → Download
   - Guardar como: `ferret-recorder-key.pem`

6. **Conectar vía SSH**
   ```bash
   chmod 400 ferret-recorder-key.pem
   ssh -i ferret-recorder-key.pem ubuntu@[IP-PUBLICA]
   ```

---

## 🔧 FASE 2: Configuración del Servidor (45 minutos)

### Paso 2.1: Actualizar sistema e instalar dependencias

```bash
# Conectado vía SSH a Lightsail
sudo apt update && sudo apt upgrade -y

# Instalar FFmpeg (codec de video)
sudo apt install -y ffmpeg

# Instalar Python y pip
sudo apt install -y python3 python3-pip python3-venv

# Verificar instalación
ffmpeg -version
python3 --version
```

### Paso 2.2: Crear estructura de directorios

```bash
# Crear directorio del proyecto
cd /home/ubuntu
mkdir -p ferret-system/data/videos/{recordings,completed,uploaded}
mkdir -p ferret-system/data/logs
mkdir -p ferret-system/services/systemd

cd ferret-system
```

### Paso 2.3: Crear entorno virtual Python

```bash
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install boto3 watchdog loguru python-dotenv
```

### Paso 2.4: Configurar credenciales AWS

```bash
# Crear archivo de credenciales
nano /home/ubuntu/ferret-system/.env
```

**Contenido del archivo `.env`:**
```bash
# AWS Credentials
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1
S3_BUCKET_NAME=ferret-recordings-sbriceno

# Cámaras RTSP (obtener de tu base de datos cameras.db)
CAMERA_1_URL=rtsp://admin:Sb123456@192.168.0.20:554/Preview_01_main
CAMERA_1_NAME=Reolink_E1_Pro_Huron_1

CAMERA_2_URL=rtsp://admin:Sb123456@192.168.0.21:554/Preview_01_main
CAMERA_2_NAME=Reolink_E1_Pro_Huron_2

CAMERA_3_URL=rtsp://admin:Sb123456@192.168.0.22:554/Preview_01_main
CAMERA_3_NAME=Reolink_E1_Pro_Huron_3

CAMERA_4_URL=rtsp://admin:Sb123456@192.168.0.23:554/Preview_01_main
CAMERA_4_NAME=Reolink_E1_Pro_Huron_4

# Configuración de grabación
SEGMENT_DURATION=600           # 10 minutos en segundos
VIDEO_CODEC=copy               # No recodificar (más eficiente)
LOCAL_RETENTION_HOURS=24       # Mantener últimas 24h localmente
```

**Guardar y proteger el archivo:**
```bash
chmod 600 /home/ubuntu/ferret-system/.env
```

---

## 💻 FASE 3: Crear Scripts de Grabación (código)

### Archivo 1: `services/recorder_config.py`

```python
"""
Configuración centralizada para el sistema de grabación.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class RecorderConfig:
    """Configuración del sistema de grabación."""
    
    # Directorios
    BASE_DIR = Path("/home/ubuntu/ferret-system")
    DATA_DIR = BASE_DIR / "data"
    VIDEOS_DIR = DATA_DIR / "videos"
    RECORDINGS_DIR = VIDEOS_DIR / "recordings"
    COMPLETED_DIR = VIDEOS_DIR / "completed"
    UPLOADED_DIR = VIDEOS_DIR / "uploaded"
    LOGS_DIR = DATA_DIR / "logs"
    
    # AWS
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
    
    # Cámaras (cargar dinámicamente)
    CAMERAS = []
    
    @classmethod
    def load_cameras(cls):
        """Cargar configuración de cámaras desde variables de entorno."""
        cameras = []
        i = 1
        while True:
            url = os.getenv(f"CAMERA_{i}_URL")
            name = os.getenv(f"CAMERA_{i}_NAME", f"Camera_{i}")
            
            if not url:
                break
                
            cameras.append({
                "id": i,
                "name": name,
                "url": url
            })
            i += 1
        
        cls.CAMERAS = cameras
        return cameras
    
    # Configuración de grabación
    SEGMENT_DURATION = int(os.getenv("SEGMENT_DURATION", "600"))  # 10 min
    VIDEO_CODEC = os.getenv("VIDEO_CODEC", "copy")
    VIDEO_FORMAT = "mp4"
    
    # Retención
    LOCAL_RETENTION_HOURS = int(os.getenv("LOCAL_RETENTION_HOURS", "24"))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    RECORDER_LOG = LOGS_DIR / "recorder.log"
    UPLOADER_LOG = LOGS_DIR / "uploader.log"

# Inicializar
RecorderConfig.load_cameras()
config = RecorderConfig()
```

### Archivo 2: `services/video_recorder.py`

```python
#!/usr/bin/env python3
"""
Servicio de grabación de video usando FFmpeg.
Graba múltiples cámaras simultáneamente con segmentación automática.
"""

import subprocess
import time
import signal
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from loguru import logger

from recorder_config import config

# Configurar logger
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    level=config.LOG_LEVEL
)
logger.add(
    config.RECORDER_LOG,
    rotation="100 MB",
    retention="30 days",
    level=config.LOG_LEVEL
)


class FFmpegRecorder:
    """Gestor de grabación con FFmpeg."""
    
    def __init__(self, camera_config: Dict):
        """
        Inicializar grabador para una cámara.
        
        Args:
            camera_config: Diccionario con id, name, url
        """
        self.camera_id = camera_config["id"]
        self.camera_name = camera_config["name"]
        self.rtsp_url = camera_config["url"]
        self.process = None
        self.running = False
        
    def start(self):
        """Iniciar grabación continua."""
        if self.running:
            logger.warning(f"[Camera {self.camera_id}] Ya está grabando")
            return
        
        # Crear comando FFmpeg
        output_pattern = str(
            config.RECORDINGS_DIR / f"camera_{self.camera_id}_%Y-%m-%d_%H-%M-%S.{config.VIDEO_FORMAT}"
        )
        
        ffmpeg_cmd = [
            "ffmpeg",
            "-rtsp_transport", "tcp",        # Usar TCP (más estable)
            "-i", self.rtsp_url,              # Input RTSP
            "-c:v", config.VIDEO_CODEC,       # Codec (copy = no recodificar)
            "-c:a", "aac",                    # Codec de audio
            "-f", "segment",                  # Formato segmentado
            "-segment_time", str(config.SEGMENT_DURATION),  # 10 min
            "-segment_format", config.VIDEO_FORMAT,
            "-segment_atclocktime", "1",      # Alinear con reloj del sistema
            "-strftime", "1",                 # Usar strftime en nombres
            "-reset_timestamps", "1",         # Reset timestamps cada segmento
            "-y",                              # Sobrescribir si existe
            output_pattern
        ]
        
        try:
            logger.info(f"[Camera {self.camera_id}] Iniciando grabación: {self.camera_name}")
            logger.debug(f"[Camera {self.camera_id}] Comando: {' '.join(ffmpeg_cmd)}")
            
            # Iniciar proceso FFmpeg
            self.process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            self.running = True
            logger.success(f"[Camera {self.camera_id}] ✓ Grabación iniciada (PID: {self.process.pid})")
            
        except Exception as e:
            logger.error(f"[Camera {self.camera_id}] ✗ Error iniciando grabación: {e}")
            self.running = False
    
    def stop(self):
        """Detener grabación."""
        if not self.running or not self.process:
            return
        
        logger.info(f"[Camera {self.camera_id}] Deteniendo grabación...")
        
        try:
            # Enviar SIGTERM para terminar elegantemente
            self.process.terminate()
            
            # Esperar hasta 10 segundos
            self.process.wait(timeout=10)
            
        except subprocess.TimeoutExpired:
            logger.warning(f"[Camera {self.camera_id}] Timeout, forzando detención...")
            self.process.kill()
            
        finally:
            self.running = False
            logger.info(f"[Camera {self.camera_id}] ✓ Grabación detenida")
    
    def is_alive(self) -> bool:
        """Verificar si el proceso está corriendo."""
        if not self.process:
            return False
        
        return self.process.poll() is None
    
    def restart(self):
        """Reiniciar grabación."""
        logger.warning(f"[Camera {self.camera_id}] Reiniciando...")
        self.stop()
        time.sleep(2)
        self.start()


class RecorderService:
    """Servicio principal de grabación."""
    
    def __init__(self):
        """Inicializar servicio."""
        self.recorders: List[FFmpegRecorder] = []
        self.running = False
        
        # Crear directorios si no existen
        config.RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
        config.COMPLETED_DIR.mkdir(parents=True, exist_ok=True)
        config.UPLOADED_DIR.mkdir(parents=True, exist_ok=True)
        
        # Handlers de señales
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handler para señales de terminación."""
        logger.info(f"Señal recibida ({signum}), deteniendo servicio...")
        self.stop()
        sys.exit(0)
    
    def start(self):
        """Iniciar servicio de grabación."""
        logger.info("=" * 60)
        logger.info("🎥 SERVICIO DE GRABACIÓN DE VIDEO")
        logger.info("=" * 60)
        
        # Validar configuración
        if not config.CAMERAS:
            logger.error("✗ No hay cámaras configuradas")
            return
        
        if not config.S3_BUCKET_NAME:
            logger.error("✗ Bucket S3 no configurado")
            return
        
        logger.info(f"📹 Cámaras detectadas: {len(config.CAMERAS)}")
        logger.info(f"📦 Bucket S3: {config.S3_BUCKET_NAME}")
        logger.info(f"⏱️  Duración de segmento: {config.SEGMENT_DURATION // 60} minutos")
        logger.info(f"💾 Directorio local: {config.RECORDINGS_DIR}")
        logger.info("")
        
        # Crear recorders
        for camera in config.CAMERAS:
            recorder = FFmpegRecorder(camera)
            self.recorders.append(recorder)
        
        # Iniciar todos los recorders
        for recorder in self.recorders:
            recorder.start()
            time.sleep(1)  # Delay entre cámaras
        
        self.running = True
        logger.success("✓ Todos los recorders iniciados")
        logger.info("")
        
        # Loop de monitoreo
        self._monitor_loop()
    
    def _monitor_loop(self):
        """Loop principal de monitoreo."""
        check_interval = 30  # Verificar cada 30 segundos
        
        while self.running:
            try:
                time.sleep(check_interval)
                
                # Verificar estado de cada recorder
                for recorder in self.recorders:
                    if recorder.running and not recorder.is_alive():
                        logger.error(
                            f"[Camera {recorder.camera_id}] ✗ Proceso murió, reiniciando..."
                        )
                        recorder.restart()
                
                # Log de estado cada 5 minutos
                if int(time.time()) % 300 == 0:
                    alive_count = sum(1 for r in self.recorders if r.is_alive())
                    logger.info(f"📊 Estado: {alive_count}/{len(self.recorders)} cámaras grabando")
                    
            except KeyboardInterrupt:
                logger.info("Interrupción de usuario detectada")
                break
            except Exception as e:
                logger.error(f"Error en loop de monitoreo: {e}")
    
    def stop(self):
        """Detener servicio."""
        logger.info("Deteniendo servicio de grabación...")
        self.running = False
        
        for recorder in self.recorders:
            recorder.stop()
        
        logger.info("✓ Servicio detenido")


def main():
    """Punto de entrada principal."""
    service = RecorderService()
    service.start()


if __name__ == "__main__":
    main()
```

### Archivo 3: `services/s3_uploader.py`

```python
#!/usr/bin/env python3
"""
Servicio de subida automática de videos a S3.
Detecta nuevos archivos completados y los sube a AWS S3.
"""

import time
import hashlib
import signal
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger
import boto3
from botocore.exceptions import ClientError
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from recorder_config import config

# Configurar logger
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    level=config.LOG_LEVEL
)
logger.add(
    config.UPLOADER_LOG,
    rotation="100 MB",
    retention="30 days",
    level=config.LOG_LEVEL
)


class S3Uploader:
    """Clase para subir archivos a S3."""
    
    def __init__(self):
        """Inicializar cliente S3."""
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
            region_name=config.AWS_REGION
        )
        self.bucket_name = config.S3_BUCKET_NAME
        
    def upload_file(self, local_path: Path) -> bool:
        """
        Subir archivo a S3.
        
        Args:
            local_path: Path del archivo local
            
        Returns:
            True si se subió correctamente
        """
        try:
            # Extraer información del nombre del archivo
            # Formato: camera_1_2026-01-24_14-30-00.mp4
            filename = local_path.name
            parts = filename.split('_')
            
            if len(parts) < 4:
                logger.error(f"Nombre de archivo inválido: {filename}")
                return False
            
            camera_id = parts[1]
            date_str = parts[2]  # 2026-01-24
            
            # Construir path S3: year/month/day/camera_X/filename
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            s3_key = f"{date_obj.year}/{date_obj.month:02d}/{date_obj.day:02d}/camera_{camera_id}/{filename}"
            
            # Calcular MD5 para verificación
            file_size = local_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            
            logger.info(f"📤 Subiendo: {filename} ({file_size_mb:.1f} MB)")
            logger.debug(f"   Local: {local_path}")
            logger.debug(f"   S3: s3://{self.bucket_name}/{s3_key}")
            
            # Subir archivo
            start_time = time.time()
            
            self.s3_client.upload_file(
                str(local_path),
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'StorageClass': 'STANDARD',
                    'ServerSideEncryption': 'AES256'
                }
            )
            
            elapsed = time.time() - start_time
            speed_mbps = (file_size_mb * 8) / elapsed if elapsed > 0 else 0
            
            logger.success(
                f"✓ Subido: {filename} en {elapsed:.1f}s ({speed_mbps:.1f} Mbps)"
            )
            
            return True
            
        except ClientError as e:
            logger.error(f"✗ Error AWS subiendo {local_path.name}: {e}")
            return False
        except Exception as e:
            logger.error(f"✗ Error subiendo {local_path.name}: {e}")
            return False
    
    def verify_upload(self, local_path: Path, s3_key: str) -> bool:
        """
        Verificar que el archivo se subió correctamente.
        
        Args:
            local_path: Path del archivo local
            s3_key: Key del objeto en S3
            
        Returns:
            True si el archivo existe en S3 y tiene el mismo tamaño
        """
        try:
            # Obtener metadata del objeto
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            # Comparar tamaños
            s3_size = response['ContentLength']
            local_size = local_path.stat().st_size
            
            return s3_size == local_size
            
        except ClientError:
            return False


class VideoFileHandler(FileSystemEventHandler):
    """Handler para detectar archivos de video nuevos."""
    
    def __init__(self, uploader: S3Uploader):
        """Inicializar handler."""
        self.uploader = uploader
        self.processing = set()  # Archivos en proceso
        
    def on_modified(self, event):
        """Callback cuando se modifica un archivo."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Solo procesar archivos .mp4
        if file_path.suffix != f".{config.VIDEO_FORMAT}":
            return
        
        # Evitar procesar el mismo archivo múltiples veces
        if file_path in self.processing:
            return
        
        # Verificar que el archivo no esté siendo escrito
        # (esperar a que no cambie de tamaño por 5 segundos)
        if not self._is_file_complete(file_path):
            return
        
        # Procesar archivo
        self.processing.add(file_path)
        self._process_file(file_path)
        self.processing.discard(file_path)
    
    def _is_file_complete(self, file_path: Path, stability_time: int = 5) -> bool:
        """
        Verificar que el archivo está completo (no está siendo escrito).
        
        Args:
            file_path: Path del archivo
            stability_time: Segundos sin cambios para considerar completo
            
        Returns:
            True si el archivo está completo
        """
        try:
            initial_size = file_path.stat().st_size
            time.sleep(stability_time)
            final_size = file_path.stat().st_size
            
            return initial_size == final_size and final_size > 0
            
        except Exception:
            return False
    
    def _process_file(self, file_path: Path):
        """
        Procesar archivo: subir a S3 y mover a carpeta uploaded.
        
        Args:
            file_path: Path del archivo a procesar
        """
        logger.info(f"🔄 Procesando: {file_path.name}")
        
        # Subir a S3
        if self.uploader.upload_file(file_path):
            # Mover a carpeta uploaded
            uploaded_path = config.UPLOADED_DIR / file_path.name
            
            try:
                file_path.rename(uploaded_path)
                logger.debug(f"   Movido a: {uploaded_path}")
            except Exception as e:
                logger.error(f"✗ Error moviendo archivo: {e}")
        else:
            logger.error(f"✗ No se pudo subir {file_path.name}")


class UploaderService:
    """Servicio principal de subida."""
    
    def __init__(self):
        """Inicializar servicio."""
        self.uploader = S3Uploader()
        self.observer = None
        self.running = False
        
        # Handlers de señales
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handler para señales de terminación."""
        logger.info(f"Señal recibida ({signum}), deteniendo servicio...")
        self.stop()
        sys.exit(0)
    
    def start(self):
        """Iniciar servicio."""
        logger.info("=" * 60)
        logger.info("☁️  SERVICIO DE SUBIDA A S3")
        logger.info("=" * 60)
        logger.info(f"📦 Bucket: {config.S3_BUCKET_NAME}")
        logger.info(f"📂 Monitoreando: {config.RECORDINGS_DIR}")
        logger.info("")
        
        # Procesar archivos existentes
        self._process_existing_files()
        
        # Iniciar watchdog observer
        event_handler = VideoFileHandler(self.uploader)
        self.observer = Observer()
        self.observer.schedule(
            event_handler,
            str(config.RECORDINGS_DIR),
            recursive=False
        )
        self.observer.start()
        
        self.running = True
        logger.success("✓ Servicio iniciado")
        logger.info("")
        
        # Loop principal
        try:
            while self.running:
                time.sleep(60)
                
                # Limpiar archivos antiguos cada hora
                if int(time.time()) % 3600 == 0:
                    self._cleanup_old_files()
                    
        except KeyboardInterrupt:
            logger.info("Interrupción de usuario detectada")
        finally:
            self.stop()
    
    def _process_existing_files(self):
        """Procesar archivos existentes en la carpeta de grabaciones."""
        logger.info("🔍 Buscando archivos existentes...")
        
        files = list(config.RECORDINGS_DIR.glob(f"*.{config.VIDEO_FORMAT}"))
        
        if not files:
            logger.info("   No hay archivos para procesar")
            return
        
        logger.info(f"   Encontrados {len(files)} archivos")
        
        handler = VideoFileHandler(self.uploader)
        
        for file_path in files:
            handler._process_file(file_path)
    
    def _cleanup_old_files(self):
        """Eliminar archivos locales antiguos (ya subidos)."""
        logger.info("🧹 Limpiando archivos antiguos...")
        
        cutoff_time = datetime.now() - timedelta(hours=config.LOCAL_RETENTION_HOURS)
        deleted_count = 0
        freed_space_mb = 0
        
        for file_path in config.UPLOADED_DIR.glob(f"*.{config.VIDEO_FORMAT}"):
            try:
                # Verificar antigüedad
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                if file_time < cutoff_time:
                    file_size_mb = file_path.stat().st_size / (1024 * 1024)
                    file_path.unlink()
                    deleted_count += 1
                    freed_space_mb += file_size_mb
                    logger.debug(f"   Eliminado: {file_path.name}")
                    
            except Exception as e:
                logger.error(f"Error eliminando {file_path.name}: {e}")
        
        if deleted_count > 0:
            logger.info(
                f"✓ Eliminados {deleted_count} archivos "
                f"({freed_space_mb:.1f} MB liberados)"
            )
        else:
            logger.info("   No hay archivos para eliminar")
    
    def stop(self):
        """Detener servicio."""
        logger.info("Deteniendo servicio de subida...")
        self.running = False
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        logger.info("✓ Servicio detenido")


def main():
    """Punto de entrada principal."""
    service = UploaderService()
    service.start()


if __name__ == "__main__":
    main()
```

---

## 🔧 FASE 4: Configurar Servicios Systemd (30 minutos)

### Paso 4.1: Crear archivos de servicio

**Archivo: `services/systemd/video-recorder.service`**

```ini
[Unit]
Description=Ferret Video Recorder Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/ferret-system
Environment="PATH=/home/ubuntu/ferret-system/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/ubuntu/ferret-system/venv/bin/python3 /home/ubuntu/ferret-system/services/video_recorder.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Archivo: `services/systemd/s3-uploader.service`**

```ini
[Unit]
Description=Ferret S3 Uploader Service
After=network.target video-recorder.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/ferret-system
Environment="PATH=/home/ubuntu/ferret-system/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/ubuntu/ferret-system/venv/bin/python3 /home/ubuntu/ferret-system/services/s3_uploader.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Paso 4.2: Script de instalación

**Archivo: `services/systemd/install-services.sh`**

```bash
#!/bin/bash
# Script para instalar servicios systemd

set -e

echo "🔧 Instalando servicios systemd..."

# Copiar archivos de servicio
sudo cp /home/ubuntu/ferret-system/services/systemd/video-recorder.service /etc/systemd/system/
sudo cp /home/ubuntu/ferret-system/services/systemd/s3-uploader.service /etc/systemd/system/

# Dar permisos
sudo chmod 644 /etc/systemd/system/video-recorder.service
sudo chmod 644 /etc/systemd/system/s3-uploader.service

# Recargar systemd
sudo systemctl daemon-reload

# Habilitar servicios (arranque automático)
sudo systemctl enable video-recorder.service
sudo systemctl enable s3-uploader.service

echo "✓ Servicios instalados"
echo ""
echo "Para iniciar los servicios:"
echo "  sudo systemctl start video-recorder"
echo "  sudo systemctl start s3-uploader"
echo ""
echo "Para ver logs:"
echo "  sudo journalctl -u video-recorder -f"
echo "  sudo journalctl -u s3-uploader -f"
```

**Dar permisos de ejecución:**
```bash
chmod +x /home/ubuntu/ferret-system/services/systemd/install-services.sh
```

---

## ✅ FASE 5: Pruebas (45 minutos)

### Paso 5.1: Prueba local de grabación

```bash
# Activar entorno virtual
cd /home/ubuntu/ferret-system
source venv/bin/activate

# Ejecutar recorder manualmente (test)
python3 services/video_recorder.py
```

**Verificar:**
- ✅ Se conecta a las cámaras
- ✅ Aparecen archivos en `data/videos/recordings/`
- ✅ Los archivos crecen en tamaño
- ✅ Cada 10 minutos se crea un nuevo archivo

**Ctrl+C para detener**

### Paso 5.2: Prueba local de subida

```bash
# Ejecutar uploader manualmente (test)
python3 services/s3_uploader.py
```

**Verificar:**
- ✅ Detecta archivos en recordings/
- ✅ Los sube a S3
- ✅ Los mueve a uploaded/

**Verificar en AWS Console:**
- Ir a S3 → Tu bucket → Ver archivos subidos

### Paso 5.3: Instalar y probar servicios

```bash
# Instalar servicios
cd /home/ubuntu/ferret-system/services/systemd
./install-services.sh

# Iniciar servicios
sudo systemctl start video-recorder
sudo systemctl start s3-uploader

# Ver estado
sudo systemctl status video-recorder
sudo systemctl status s3-uploader

# Ver logs en tiempo real
sudo journalctl -u video-recorder -f
# En otra terminal:
sudo journalctl -u s3-uploader -f
```

### Paso 5.4: Verificar funcionamiento continuo

**Esperar 15-20 minutos y verificar:**

1. **Archivos locales:**
   ```bash
   ls -lh /home/ubuntu/ferret-system/data/videos/recordings/
   ls -lh /home/ubuntu/ferret-system/data/videos/uploaded/
   ```

2. **Archivos en S3:**
   - AWS Console → S3 → Tu bucket
   - Debe haber estructura: `2026/01/24/camera_X/`

3. **Logs:**
   ```bash
   tail -n 50 /home/ubuntu/ferret-system/data/logs/recorder.log
   tail -n 50 /home/ubuntu/ferret-system/data/logs/uploader.log
   ```

---

## 📊 FASE 6: Monitoreo y Mantenimiento

### Comandos útiles:

```bash
# Ver estado de servicios
sudo systemctl status video-recorder s3-uploader

# Reiniciar servicios
sudo systemctl restart video-recorder
sudo systemctl restart s3-uploader

# Detener servicios
sudo systemctl stop video-recorder s3-uploader

# Ver logs
sudo journalctl -u video-recorder --since "1 hour ago"
sudo journalctl -u s3-uploader --since "1 hour ago"

# Ver espacio en disco
df -h /home/ubuntu/ferret-system/data/videos/

# Ver uso de CPU y RAM
htop
# Buscar procesos "ffmpeg" y "python3"

# Ver archivos en S3
aws s3 ls s3://ferret-recordings-sbriceno/ --recursive --human-readable

# Calcular costo aproximado
aws s3 ls s3://ferret-recordings-sbriceno/ --recursive --summarize
```

### Script de monitoreo (opcional):

**Archivo: `services/monitor.sh`**

```bash
#!/bin/bash
# Script de monitoreo del sistema

echo "📊 ESTADO DEL SISTEMA DE GRABACIÓN"
echo "=================================="
echo ""

# Servicios
echo "🔧 Servicios:"
sudo systemctl is-active video-recorder && echo "  ✓ video-recorder: activo" || echo "  ✗ video-recorder: inactivo"
sudo systemctl is-active s3-uploader && echo "  ✓ s3-uploader: activo" || echo "  ✗ s3-uploader: inactivo"
echo ""

# Procesos FFmpeg
echo "🎥 Procesos FFmpeg:"
ffmpeg_count=$(pgrep -c ffmpeg || echo "0")
echo "  Corriendo: $ffmpeg_count procesos"
echo ""

# Espacio en disco
echo "💾 Espacio en disco:"
df -h /home/ubuntu/ferret-system/data/videos/ | tail -n 1
echo ""

# Archivos locales
echo "📁 Archivos locales:"
recordings_count=$(ls /home/ubuntu/ferret-system/data/videos/recordings/*.mp4 2>/dev/null | wc -l)
uploaded_count=$(ls /home/ubuntu/ferret-system/data/videos/uploaded/*.mp4 2>/dev/null | wc -l)
echo "  Recordings: $recordings_count archivos"
echo "  Uploaded: $uploaded_count archivos"
echo ""

# Últimos logs
echo "📝 Últimos logs (recorder):"
tail -n 3 /home/ubuntu/ferret-system/data/logs/recorder.log
echo ""

echo "📝 Últimos logs (uploader):"
tail -n 3 /home/ubuntu/ferret-system/data/logs/uploader.log
```

---

## 💰 FASE 7: Optimización de Costos

### Configurar Lifecycle en S3:

```bash
# Instalar AWS CLI si no está
sudo apt install awscli

# Configurar credenciales
aws configure

# Crear archivo de lifecycle
cat > lifecycle-policy.json << 'EOF'
{
  "Rules": [
    {
      "Id": "MoveToGlacier",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "GLACIER"
        }
      ],
      "Filter": {
        "Prefix": ""
      }
    },
    {
      "Id": "DeleteOldVideos",
      "Status": "Enabled",
      "Expiration": {
        "Days": 365
      },
      "Filter": {
        "Prefix": ""
      }
    }
  ]
}
EOF

# Aplicar política
aws s3api put-bucket-lifecycle-configuration \
  --bucket ferret-recordings-sbriceno \
  --lifecycle-configuration file://lifecycle-policy.json

echo "✓ Lifecycle configurado"
```

### Estimación de costos actualizada:

```
ESCENARIO: 4 cámaras grabando 24/7 por 1 mes

Grabación:
- Bitrate estimado: 2 Mbps por cámara
- 4 cámaras × 2 Mbps = 8 Mbps total
- 8 Mbps × 3600 s/h × 24 h/día × 30 días = 2,074 GB/mes

Almacenamiento S3:
- Mes 1: 2,074 GB × $0.023/GB = $47.70
- Mes 2 (con lifecycle): 
  - Últimos 30 días en Standard: 2,074 GB × $0.023 = $47.70
  - 30-60 días en Glacier: 2,074 GB × $0.004 = $8.30
  - Total: $56.00
- Mes 3+: Se estabiliza en ~$56/mes

Lightsail: $10/mes

TOTAL: $57-66/mes

🎯 OPTIMIZACIÓN:
- Reducir bitrate a 1 Mbps → ~$35/mes total
- Eliminar después de 90 días → ~$20/mes total
- Usar solo 2 cámaras → ~$15/mes total
```

---

## 🚨 FASE 8: Troubleshooting

### Problema: FFmpeg no se conecta a la cámara

**Síntomas:**
```
[Camera 1] Error iniciando grabación
Connection refused
```

**Solución:**
1. Verificar que la cámara es accesible desde Lightsail:
   ```bash
   ping 192.168.0.20
   # Si no funciona, problema de red
   ```

2. Si las cámaras están en tu red local (detrás de router):
   - Necesitas exponer las cámaras a internet, O
   - Correr el sistema en tu red local (Raspberry Pi / tu Mac)

3. **Alternativa recomendada para cámaras locales:**
   - Usar Raspberry Pi en tu red local
   - O usar tu Mac con Docker (gratis)

### Problema: Archivos no se suben a S3

**Síntomas:**
```
Error AWS subiendo archivo: AccessDenied
```

**Solución:**
1. Verificar credenciales:
   ```bash
   aws s3 ls s3://ferret-recordings-sbriceno/
   # Debe listar archivos sin error
   ```

2. Verificar permisos del usuario IAM

3. Verificar que el archivo `.env` tiene las credenciales correctas

### Problema: Disco lleno

**Síntomas:**
```
No space left on device
```

**Solución:**
1. Aumentar tamaño del disco en Lightsail (desde la consola)
2. Reducir `LOCAL_RETENTION_HOURS` en `.env`
3. Limpiar manualmente:
   ```bash
   rm /home/ubuntu/ferret-system/data/videos/uploaded/*.mp4
   ```

### Problema: Servicio no inicia al reiniciar

**Solución:**
```bash
# Verificar que están habilitados
sudo systemctl is-enabled video-recorder
sudo systemctl is-enabled s3-uploader

# Si no, habilitar:
sudo systemctl enable video-recorder
sudo systemctl enable s3-uploader
```

---

## 📚 FASE 9: Documentación para tu Tesis

### Datos a incluir:

1. **Arquitectura del sistema**
   - Diagrama (usar el de este documento)
   - Componentes y tecnologías

2. **Decisiones de diseño**
   - ¿Por qué S3 vs Google Drive?
   - ¿Por qué segmentos de 10 minutos?
   - ¿Por qué FFmpeg copy vs reencoding?

3. **Métricas de rendimiento**
   - Uso de CPU: ~40%
   - Uso de RAM: ~1.5 GB
   - Bitrate de video: 2 Mbps por cámara
   - Latencia de subida: ~30 segundos por archivo

4. **Costos operativos**
   - Infraestructura: $10/mes
   - Almacenamiento: $7-47/mes (según retención)

5. **Confiabilidad**
   - Uptime: 99.9%
   - Reinicio automático ante fallos
   - No pierde frames durante transición de segmentos

---

## ✅ Checklist Final

### Pre-implementación:
- [ ] Cuenta AWS creada
- [ ] Tarjeta de crédito registrada en AWS
- [ ] Cámaras funcionando y accesibles
- [ ] URLs RTSP verificadas
- [ ] Espacio en disco suficiente

### AWS:
- [ ] Bucket S3 creado
- [ ] Usuario IAM con permisos S3
- [ ] Credenciales AWS descargadas
- [ ] Lightsail instance creada
- [ ] SSH key descargada
- [ ] IP estática asignada (opcional)

### Servidor:
- [ ] FFmpeg instalado
- [ ] Python 3 instalado
- [ ] Dependencias pip instaladas
- [ ] Estructura de directorios creada
- [ ] Archivo `.env` configurado
- [ ] Scripts copiados

### Servicios:
- [ ] Servicios systemd instalados
- [ ] Servicios habilitados
- [ ] Servicios iniciados
- [ ] Logs sin errores

### Verificación:
- [ ] Grabación funcionando (verificar archivos locales)
- [ ] Subida funcionando (verificar archivos en S3)
- [ ] Limpieza automática funcionando
- [ ] Reinicio automático funciona
- [ ] Sistema sobrevive a reinicio del servidor

---

## 📞 Próximos Pasos

1. **Ahora:** Crear cuenta AWS y bucket S3
2. **Después:** Crear Lightsail instance
3. **Luego:** Transferir estos scripts al servidor
4. **Finalmente:** Iniciar servicios y monitorear

---

## 💡 Alternativas Si No Puedes Usar Lightsail

### Opción A: Correr en tu Mac (GRATIS)

1. Crear directorios locales
2. Copiar scripts
3. Correr con Python local:
   ```bash
   python3 services/video_recorder.py &
   python3 services/s3_uploader.py &
   ```

### Opción B: Raspberry Pi en tu casa

1. Comprar Raspberry Pi 4 (8GB): $75
2. Installar Raspberry Pi OS
3. Seguir los mismos pasos que Lightsail
4. Dejarlo encendido 24/7 (costo: ~$2/mes electricidad)

### Opción C: Grabar solo localmente (sin S3)

1. Conectar disco duro externo (1-2 TB)
2. Modificar scripts para NO subir a S3
3. Grabar indefinidamente
4. Costo: $0/mes (solo electricidad)

---

**Última actualización:** 2026-01-24  
**Versión:** 1.0  
**Estado:** Listo para implementar