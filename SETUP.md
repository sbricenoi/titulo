# 🛠️ Guía de Instalación y Configuración

Esta guía cubre la instalación completa de los tres componentes del sistema.

## 📋 Pre-requisitos

### Software Requerido

#### 1. Python 3.9+
```bash
# Verificar versión
python3 --version

# macOS (si no está instalado)
brew install python@3.9

# Linux
sudo apt update
sudo apt install python3.9 python3.9-venv python3.9-pip
```

#### 2. FFmpeg
```bash
# Verificar instalación
ffmpeg -version

# macOS
brew install ffmpeg

# Linux (Ubuntu/Debian)
sudo apt update
sudo apt install ffmpeg

# Linux (CentOS/RHEL)
sudo yum install ffmpeg
```

#### 3. Node.js 18+ (para Frontend)
```bash
# Verificar versión
node --version

# macOS
brew install node

# Linux - usar nvm (Node Version Manager)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18
```

#### 4. Git
```bash
# Verificar instalación
git --version

# macOS
brew install git

# Linux
sudo apt install git  # Ubuntu/Debian
sudo yum install git  # CentOS/RHEL
```

### Cuentas y Credenciales

#### AWS Account (para S3)

1. Crear cuenta en [AWS](https://aws.amazon.com/)
2. Crear bucket S3:
   - Ir a S3 Console
   - Crear bucket (ej: `ferret-recordings`)
   - Región: `us-east-1` (o la que prefieras)
   - Desmarcar "Block all public access" si quieres acceso público a videos
3. Crear usuario IAM:
   - Ir a IAM Console
   - Crear usuario (ej: `ferret-uploader`)
   - Attach policy: `AmazonS3FullAccess` (o crear policy custom)
   - Generar Access Key + Secret Key
   - **Guardar credenciales de forma segura**

#### Cámaras Reolink

1. Conectar cámaras a tu red local
2. Configurar cada cámara:
   - Anotar IP local (ej: `192.168.0.5`, `192.168.0.6`, etc.)
   - Usuario: `admin` (o el que configuraste)
   - Contraseña: tu contraseña
   - **Habilitar RTSP** en configuración de cámara
3. Verificar conectividad:
   ```bash
   # Ping a la cámara
   ping 192.168.0.5
   
   # Verificar puerto RTSP (554)
   nc -zv 192.168.0.5 554
   ```

---

## 🎬 Instalación Componente 1: Sistema de Grabación

### Paso 1: Setup del Proyecto

```bash
cd /ruta/al/proyecto/titulo
cd video-recording-system

# Crear entorno virtual
python3 -m venv venv

# Activar entorno
source venv/bin/activate  # macOS/Linux
# En Windows: venv\Scripts\activate
```

### Paso 2: Instalar Dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Dependencias principales:**
- `loguru` - Logging estructurado
- `boto3` - AWS S3 client
- `watchdog` - File system monitoring
- `python-dotenv` - Environment variables

### Paso 3: Configurar `.env`

```bash
# Copiar ejemplo (si existe) o crear nuevo
nano .env
```

**Contenido del `.env`:**

```env
# ==================== AWS CREDENTIALS ====================
AWS_ACCESS_KEY_ID=AKIAXXXXXXXXXXXXXXXX
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
AWS_REGION=us-east-1
S3_BUCKET_NAME=ferret-recordings

# ==================== CÁMARAS ====================

# Cámara 1
CAMERA_1_URL=rtsp://admin:TU_PASSWORD@192.168.0.5:554/Preview_01_main
CAMERA_1_NAME=Reolink_Principal

# Cámara 2
CAMERA_2_URL=rtsp://admin:TU_PASSWORD@192.168.0.6:554/h264Preview_01_main
CAMERA_2_NAME=Reolink_Secundaria

# Cámara 3 (opcional, agregar más según necesites)
CAMERA_3_URL=rtsp://admin:TU_PASSWORD@192.168.0.7:554/Preview_01_main
CAMERA_3_NAME=Reolink_Terciaria

# ==================== CONFIGURACIÓN DE GRABACIÓN ====================
SEGMENT_DURATION=600        # Duración de cada video en segundos (600 = 10 minutos)
VIDEO_CODEC=copy            # Codec de video (copy = sin re-encoding)
VIDEO_FORMAT=mp4            # Formato de salida
LOCAL_RETENTION_HOURS=24    # Horas de retención local antes de eliminar
LOG_LEVEL=INFO              # Nivel de logging: DEBUG, INFO, WARNING, ERROR

# Directorio base (ajustar si es necesario)
BASE_DIR=/Users/TU_USUARIO/Documents/projects/titulo/video-recording-system
```

**Notas importantes:**
- Reemplazar `TU_PASSWORD` con la contraseña real de las cámaras
- Ajustar IPs según tu red
- El path RTSP puede variar según modelo Reolink:
  - `Preview_01_main` - Algunos modelos
  - `h264Preview_01_main` - Otros modelos
  - Consultar manual de tu cámara

### Paso 4: Crear Directorios Necesarios

```bash
# Estos directorios se crean automáticamente, pero puedes verificar
mkdir -p recordings uploaded data/logs
```

### Paso 5: Probar Sistema

```bash
# Verificar que FFmpeg puede conectar a cámaras
ffmpeg -rtsp_transport tcp -i "rtsp://admin:PASSWORD@192.168.0.5:554/Preview_01_main" -t 5 -f null -

# Si funciona, verás output de FFmpeg procesando el stream
```

### Paso 6: Iniciar Sistema

```bash
# Script principal de inicio
./INICIAR_SISTEMA_FINAL.sh

# El script mostrará:
# - Verificación de configuración
# - Estado de conectividad a cámaras
# - PIDs de procesos iniciados
# - Ubicación de logs
```

**Monitoreo:**
```bash
# Ver logs en tiempo real
tail -f data/logs/recorder_*.log
tail -f data/logs/uploader_*.log

# Ver procesos activos
ps aux | grep python
ps aux | grep ffmpeg

# Ver archivos grabados
ls -lh recordings/
ls -lh uploaded/
```

### Paso 7: Detener Sistema

```bash
# Detener de forma robusta
./stop_recorder_robusto.sh

# O reiniciar limpio (borra logs y archivos parciales)
./REINICIAR_SISTEMA_LIMPIO.sh
```

---

## 🤖 Instalación Componente 2: Motor de Análisis IA

### Paso 1: Setup del Proyecto

```bash
cd /ruta/al/proyecto/titulo  # Raíz del proyecto

# Crear entorno virtual (diferente al de grabación)
python3 -m venv venv
source venv/bin/activate
```

### Paso 2: Instalar Dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Dependencias principales:**
- `torch` - PyTorch para deep learning
- `ultralytics` - YOLOv8
- `opencv-python` - Procesamiento de video
- `fastapi` - API REST
- `uvicorn` - ASGI server
- `numpy`, `scipy` - Procesamiento numérico

**Nota GPU (opcional pero recomendado):**

Si tienes GPU NVIDIA con CUDA:
```bash
# Desinstalar torch CPU
pip uninstall torch torchvision

# Instalar torch con CUDA (ajustar versión según tu CUDA)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Paso 3: Configurar `config.py`

```bash
nano config.py
```

**Ajustar parámetros según tu setup:**
- `CAMERA_URLS` - URLs RTSP de tus cámaras
- `DEVICE` - `"cuda"` si tienes GPU, `"cpu"` si no
- `MODEL_PATH` - Path al modelo YOLOv8 (se descarga automáticamente)
- `LOG_LEVEL` - Nivel de logging

### Paso 4: Descargar Modelo YOLOv8

```bash
# El modelo se descarga automáticamente al ejecutar
# O puedes pre-descargarlo:
python -c "from ultralytics import YOLO; model = YOLO('yolov8n.pt')"
```

### Paso 5: Iniciar Sistema

```bash
# Modo análisis completo
python main.py

# O solo API server
python api/main.py
```

El sistema:
- Iniciará captura de cámaras
- Comenzará detección con YOLOv8
- Ejecutará tracking multi-objeto
- Clasificará comportamientos
- Levantará API en `http://localhost:8000`

### Paso 6: Verificar API

```bash
# Health check
curl http://localhost:8000/health

# Ver documentación interactiva
# Abrir en navegador: http://localhost:8000/docs
```

---

## 🌐 Instalación Componente 3: Frontend Dashboard

### Paso 1: Setup del Proyecto

```bash
cd /ruta/al/proyecto/titulo/frontend
```

### Paso 2: Instalar Dependencias

```bash
npm install
```

### Paso 3: Configurar Endpoints

```bash
nano src/environments/environment.ts
```

**Ajustar URLs:**
```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000',  // API del motor IA
  wsUrl: 'ws://localhost:8000/ws',  // WebSocket para live updates
};
```

### Paso 4: Iniciar Servidor de Desarrollo

```bash
npm start
# O
ng serve
```

Abrir navegador en `http://localhost:4200`

### Paso 5: Build para Producción

```bash
npm run build
# Output en: dist/
```

---

## ✅ Verificación de Instalación Completa

### Checklist

- [ ] Sistema de Grabación corriendo
  - [ ] Videos grabándose en `recordings/`
  - [ ] Videos subiéndose a S3
  - [ ] Logs sin errores críticos
  
- [ ] Motor IA corriendo
  - [ ] API respondiendo en `http://localhost:8000`
  - [ ] Detección funcionando
  - [ ] Logs mostrando inferencias
  
- [ ] Frontend corriendo
  - [ ] Dashboard carga en `http://localhost:4200`
  - [ ] Conexión a API exitosa
  - [ ] Streams visualizándose

### Comandos de Verificación

```bash
# 1. Verificar grabación
ls -lh video-recording-system/recordings/
aws s3 ls s3://ferret-recordings/  # Verificar S3

# 2. Verificar API IA
curl http://localhost:8000/health

# 3. Verificar Frontend
curl http://localhost:4200
```

---

## 🐛 Troubleshooting

### Problema: FFmpeg no puede conectar a cámara

**Síntomas:** Error `Connection refused` o `timeout`

**Soluciones:**
1. Verificar IP de cámara: `ping 192.168.0.X`
2. Verificar puerto RTSP: `nc -zv 192.168.0.X 554`
3. Probar URL RTSP manualmente:
   ```bash
   ffplay "rtsp://admin:PASSWORD@192.168.0.5:554/Preview_01_main"
   ```
4. Verificar que RTSP está habilitado en cámara
5. Probar path alternativo (`h264Preview_01_main` vs `Preview_01_main`)

### Problema: Videos no suben a S3

**Síntomas:** Videos en `recordings/` pero no en S3

**Soluciones:**
1. Verificar credenciales AWS en `.env`
2. Probar upload manual:
   ```bash
   python3 -c "import boto3; s3 = boto3.client('s3'); print(s3.list_buckets())"
   ```
3. Verificar permisos del usuario IAM
4. Revisar logs: `tail -f data/logs/uploader_*.log`

### Problema: YOLOv8 muy lento (CPU)

**Síntomas:** FPS muy bajo, alta latencia

**Soluciones:**
1. Instalar PyTorch con CUDA (si tienes GPU)
2. Usar modelo más ligero: `yolov8n.pt` en vez de `yolov8x.pt`
3. Reducir resolución de entrada en `config.py`
4. Procesar menos frames por segundo

### Problema: Frontend no conecta a API

**Síntomas:** Error de CORS o conexión rechazada

**Soluciones:**
1. Verificar que API está corriendo: `curl http://localhost:8000/health`
2. Verificar URL en `environment.ts`
3. Verificar CORS en `api/main.py`:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:4200"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

---

## 📞 Soporte

Para problemas adicionales:
1. Revisar logs en `data/logs/`
2. Verificar documentación en README.md
3. Consultar `.cursorrules` para principios de desarrollo

---

**✅ ¡Instalación completa! Sistema listo para operar.**
