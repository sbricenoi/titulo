# 🎥 Conexión de Cámaras al Servidor Lightsail

## 📊 Situación Actual

### Cámaras (Red Local)
- **Ubicación**: Red local 192.168.0.x
- **Cámaras activas**:
  - Cámara 1: `192.168.0.8` (Reolink_Huron_Principal)
  - Cámara 2: `192.168.0.9` (Reolink_Huron_Secundaria)
  - Cámara 3: `192.168.0.7` (activa)
- **Protocolo**: RTSP (puerto 554)
- **Stream**: `rtsp://admin:Sb123456@192.168.0.X:554/h264Preview_01_main`

### Servidor Lightsail (AWS)
- **IP Pública**: `3.147.46.191`
- **Ubicación**: AWS us-east-2 (Ohio)
- **Recursos**: 1 vCPU, 1 GB RAM, 40 GB SSD
- **Sistema**: Ubuntu 22.04 LTS
- **Software**: FFmpeg, Python 3.10, Git

### ⚠️ El Problema

Las cámaras están en una **red privada local** (192.168.0.x) y el servidor Lightsail está en **AWS con IP pública**. 

**El servidor NO puede acceder directamente** a las cámaras porque:
1. Las IPs 192.168.0.x son privadas (no accesibles desde internet)
2. No hay ruta de red entre AWS y tu red local
3. Las cámaras están detrás de un router/firewall

---

## 🎯 Soluciones Posibles

### ✅ Opción 1: Arquitectura Híbrida (RECOMENDADA)

**Descripción:** Grabar localmente y usar Lightsail solo para procesamiento y almacenamiento

```
[Cámaras] → [Mac Local] → [Grabación Local] → [Upload a S3] → [Lightsail procesa desde S3]
              ↑                                                      ↓
         Video Recorder                                      AI Analysis + API
```

**Ventajas:**
- ✅ **No necesita VPN ni configuración de red compleja**
- ✅ **Funciona ahora mismo** (ya lo tienes configurado)
- ✅ **Menor latencia** de red (graba en LAN)
- ✅ **Confiable** (no depende de conexión a internet para grabar)
- ✅ **Menor costo** de ancho de banda
- ✅ **Redundancia** (tienes copia local y en S3)

**Desventajas:**
- ⚠️ Requiere Mac/PC local siempre encendido
- ⚠️ Duplica almacenamiento temporalmente

**Implementación:**
1. **Local (Mac)**: Sistema de grabación actual sigue funcionando
2. **S3**: Videos se suben automáticamente
3. **Lightsail**: 
   - Descarga videos desde S3
   - Ejecuta análisis con YOLOv8
   - Sirve API para frontend
   - Almacena resultados

**Costo estimado:**
- Lightsail: $5-10/mes
- S3: ~$1-5/mes (depende de retención)
- Total: ~$10-15/mes

---

### 🔧 Opción 2: Túnel SSH Reverso

**Descripción:** Crear túnel desde tu red local hacia Lightsail

```
[Cámaras] ← [Mac Local con túnel] ← [Lightsail]
             |                         |
             | SSH Reverse Tunnel      |
             └─────────────────────────┘
```

**Ventajas:**
- ✅ Conexión segura (SSH)
- ✅ No requiere abrir puertos en router
- ✅ Todo procesado en Lightsail

**Desventajas:**
- ⚠️ **Muy alto uso de ancho de banda** (múltiples streams RTSP constantes)
- ⚠️ **Latencia** de red puede causar problemas
- ⚠️ Requiere Mac local siempre conectado
- ⚠️ Complicado de mantener
- ❌ **NO recomendado para video 24/7**

**Costo:**
- Posible sobrecargo de ancho de banda en Lightsail
- 2-3 cámaras x 2 Mbps x 24h = ~6 GB/hora = ~150 GB/día
- Lightsail incluye 2 TB/mes, pero es justo

---

### 🌐 Opción 3: Port Forwarding (NO RECOMENDADA)

**Descripción:** Exponer cámaras directamente a internet

```
[Internet] → [Router público] → [Cámaras]
              puerto 554
```

**Ventajas:**
- ✅ Lightsail puede conectar directamente

**Desventajas:**
- ❌ **MUY INSEGURO** (cámaras expuestas a internet)
- ❌ Riesgo de acceso no autorizado
- ❌ IP pública dinámica (puede cambiar)
- ❌ Requiere abrir puertos en router
- ❌ **NO RECOMENDADO PARA PRODUCCIÓN**

---

### 🏢 Opción 4: VPN Site-to-Site

**Descripción:** Conectar tu red local con AWS VPC vía VPN

```
[Red Local] ←─VPN─→ [AWS VPC] ─→ [Lightsail]
   192.168.0.x         10.0.0.x
```

**Ventajas:**
- ✅ Conexión permanente y segura
- ✅ Todas las cámaras accesibles
- ✅ Baja latencia

**Desventajas:**
- ⚠️ **Complejo de configurar**
- ⚠️ **Costo adicional** (AWS VPN Gateway ~$36/mes)
- ⚠️ Requiere router compatible o gateway VPN
- ⚠️ Overkill para proyecto de tesis

---

### 🔄 Opción 5: Streaming Gateway Local

**Descripción:** Servidor local que reenvía streams a Lightsail

```
[Cámaras] → [Gateway Local] → [Re-stream RTMP/HLS] → [Lightsail]
            (Mac o Raspberry Pi)
```

**Ventajas:**
- ✅ Puede optimizar ancho de banda
- ✅ Más control sobre streams

**Desventajas:**
- ⚠️ Requiere configuración adicional
- ⚠️ Mayor complejidad
- ⚠️ Punto de falla adicional

---

## 🎖️ Recomendación Final: Opción 1 (Arquitectura Híbrida)

### ¿Por qué?

1. **Ya funciona**: Tu sistema actual ya graba localmente y sube a S3
2. **Confiable**: No depende de conexión constante a internet
3. **Económico**: Usa recursos eficientemente
4. **Seguro**: No expone cámaras a internet
5. **Escalable**: Fácil agregar más cámaras
6. **Simple**: No requiere VPN ni túneles complejos

### 🚀 Implementación Propuesta

#### Componente Local (Ya funciona ✅)
```bash
# En tu Mac
./INICIAR_SISTEMA_FINAL.sh

# Servicios:
- video_recorder.py  → Graba de cámaras a archivos .mp4
- s3_uploader.py     → Sube automáticamente a S3
```

#### Componente Cloud (Por configurar)
```bash
# En Lightsail
1. Clonar repositorio
2. Instalar dependencias
3. Configurar .env (sin cámaras, solo S3)
4. Ejecutar servicios:
   - process_s3_videos.py  → Descarga videos de S3
   - auto_analyze_videos.py → Analiza con YOLOv8
   - api/main.py           → Sirve API
   - frontend              → Angular backoffice
```

### 📂 Flujo de Datos

```mermaid
graph LR
    A[Cámaras] -->|RTSP| B[Mac Local]
    B -->|Grabar| C[Videos .mp4]
    C -->|Upload| D[S3 Bucket]
    D -->|Download| E[Lightsail]
    E -->|Analizar| F[YOLOv8]
    F -->|Detectar| G[Frames + JSON]
    G -->|API| H[Frontend]
```

### ⚙️ Configuración del Sistema

#### Local (.env)
```bash
# Cámaras (solo local)
CAMERA_1_URL=rtsp://admin:Sb123456@192.168.0.8:554/h264Preview_01_main
CAMERA_2_URL=rtsp://admin:Sb123456@192.168.0.9:554/h264Preview_01_main
CAMERA_3_URL=rtsp://admin:Sb123456@192.168.0.7:554/h264Preview_01_main

# S3
AWS_ACCESS_KEY_ID=<tu-key>
AWS_SECRET_ACCESS_KEY=<tu-secret>
S3_BUCKET_NAME=ferret-recordings-bucket
AWS_REGION=us-east-2

# Grabación local
SEGMENT_DURATION=600  # 10 minutos
VIDEO_CODEC=copy
LOCAL_RETENTION_HOURS=24
```

#### Lightsail (.env)
```bash
# NO incluir CAMERA_X_URL (no accesibles desde cloud)

# S3 (para descargar videos)
AWS_ACCESS_KEY_ID=<tu-key>
AWS_SECRET_ACCESS_KEY=<tu-secret>
S3_BUCKET_NAME=ferret-recordings-bucket
AWS_REGION=us-east-2

# Configuración de análisis
YOLO_MODEL=yolov8n.pt
CONFIDENCE_THRESHOLD=0.4
TARGET_CLASSES=cat,dog  # o el que uses para hurones
```

---

## 📋 Plan de Implementación

### Fase 1: Verificar Sistema Local (Ya hecho ✅)
- [x] Cámaras grabando correctamente
- [x] Videos subiéndose a S3
- [x] Análisis local funcionando

### Fase 2: Configurar Lightsail
- [ ] Subir código a GitHub
- [ ] Clonar repo en Lightsail
- [ ] Instalar dependencias
- [ ] Configurar .env (sin cámaras)
- [ ] Probar descarga desde S3

### Fase 3: Migrar Análisis a Cloud
- [ ] Configurar `process_s3_videos.py` en Lightsail
- [ ] Instalar YOLOv8
- [ ] Probar análisis de un video
- [ ] Automatizar con cron/systemd

### Fase 4: Configurar API y Frontend
- [ ] Iniciar API FastAPI
- [ ] Configurar base de datos SQLite
- [ ] Iniciar frontend Angular
- [ ] Verificar acceso desde internet

### Fase 5: Producción
- [ ] Configurar dominio (opcional)
- [ ] Configurar SSL/HTTPS
- [ ] Monitoreo y alertas
- [ ] Backup de base de datos

---

## 💡 Alternativas para el Futuro

Si más adelante necesitas acceso directo desde Lightsail:

1. **Raspberry Pi como Gateway**
   - Costo: ~$50-100
   - Conectado 24/7 en tu red
   - Ejecuta túnel SSH reverso o VPN
   
2. **Cámaras con DDNS**
   - Algunas Reolink soportan DDNS
   - Permite acceso remoto directo
   - Aún requiere port forwarding (menos seguro)

3. **Upgrade a AWS VPN**
   - Si el proyecto crece
   - Si necesitas múltiples ubicaciones
   - Costo: +$36/mes

---

## 🔍 Próximos Pasos Inmediatos

1. **Crear script de configuración para Lightsail**
2. **Modificar `process_s3_videos.py` si es necesario**
3. **Documentar proceso de deploy**
4. **Testear con un video de prueba**

¿Te parece bien proceder con la Opción 1 (Arquitectura Híbrida)?
