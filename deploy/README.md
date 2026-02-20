# 🚀 Deploy a Lightsail

Scripts y configuración para desplegar el sistema en AWS Lightsail.

## 📋 Arquitectura

```
[Cámaras Local] → [Mac] → [S3] → [Lightsail]
                    ↓              ↓
                 Grabar      Analizar + API
```

## 📁 Archivos

- `lightsail-setup.sh` - Script de instalación inicial
- `lightsail-env.example` - Plantilla de .env para cloud
- `README.md` - Este archivo

## 🚀 Instalación

### 1. Conectar al Servidor

```bash
ssh -i /Users/sbriceno/Documents/projects/titulo/ferret-recorder-key.pem ubuntu@3.147.46.191
```

O con alias:
```bash
ssh ferret-recorder
```

### 2. Clonar Repositorio

```bash
cd ~
git clone <URL_DE_TU_REPO> titulo
cd titulo
```

### 3. Ejecutar Setup

```bash
chmod +x deploy/lightsail-setup.sh
./deploy/lightsail-setup.sh
```

### 4. Configurar Credenciales

```bash
cp deploy/lightsail-env.example .env
nano .env
```

Configurar:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `S3_BUCKET_NAME`
- `AWS_REGION`

**⚠️ NO incluir `CAMERA_X_URL`** - Las cámaras no son accesibles desde cloud

### 5. Probar Conexión a S3

```bash
source ~/venv/bin/activate
python process_s3_videos.py --test
```

### 6. Iniciar Servicios

```bash
# API
./start_api_classification.sh

# Procesador de S3 (en otra terminal)
python process_s3_videos.py

# Frontend (en otra terminal)
cd frontend
npm install
npm start
```

## 🔧 Servicios Systemd (Opcional)

Para que los servicios se inicien automáticamente:

```bash
cd ~/titulo/video-recording-system/services/systemd
sudo ./install-services.sh
```

## 📊 Monitoreo

```bash
# Ver recursos
htop

# Ver logs de API
tail -f ~/titulo/logs/api_backend.log

# Ver logs del procesador S3
tail -f ~/titulo/logs/s3_processor.log

# Ver espacio en disco
df -h
```

## 🐛 Troubleshooting

### No puede descargar de S3
- Verificar credenciales AWS en .env
- Verificar permisos del bucket S3
- Verificar región AWS correcta

### Poco espacio en disco
```bash
# Ver uso
du -sh ~/titulo/data/*

# Limpiar videos procesados
rm ~/titulo/data/videos/from_s3/*.mp4

# Limpiar logs viejos
find ~/titulo/logs -name "*.log" -mtime +7 -delete
```

### RAM insuficiente
- Reducir número de workers de API
- Procesar videos de uno en uno
- Considerar upgrade a $10/mes (2 GB RAM)

## 📝 Notas Importantes

1. **Este servidor NO graba de cámaras**
   - Solo procesa videos desde S3
   - La grabación se hace en local (Mac)

2. **Flujo de datos:**
   - Local: Cámaras → Grabar → S3
   - Cloud: S3 → Descargar → Analizar → API

3. **Seguridad:**
   - Credenciales solo en .env (no en repo)
   - .env está en .gitignore
   - SSH key no se sube a GitHub

## 🔗 Referencias

- [LIGHTSAIL_CAMERA_CONNECTION.md](../docs/LIGHTSAIL_CAMERA_CONNECTION.md) - Arquitectura completa
- [SERVIDOR_INFO.md](../video-recording-system/SERVIDOR_INFO.md) - Info del servidor
