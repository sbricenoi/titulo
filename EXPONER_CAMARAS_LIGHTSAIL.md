# 🎥 Exponer Cámaras para Lightsail - Guía Práctica

## 🎯 Objetivo

Hacer que las cámaras locales (192.168.0.7, 192.168.0.8, 192.168.0.9) sean accesibles desde el servidor Lightsail para que pueda grabar directamente.

---

## ⚡ Opción 1: Port Forwarding (Rápido - 15 minutos)

Esta es la forma más rápida de exponer las cámaras. **Importante:** Toma medidas de seguridad adicionales.

### Paso 1: Obtener tu IP Pública

```bash
curl ifconfig.me
# Ejemplo: 181.45.67.123
```

**Anota esta IP**, la necesitarás para configurar Lightsail.

### Paso 2: Acceder a tu Router

1. Abre navegador web
2. Ve a: `http://192.168.0.1`
3. Usuario/contraseña de tu router (busca en etiqueta del router)

### Paso 3: Configurar Port Forwarding

Busca la sección **"Port Forwarding"**, **"Virtual Server"** o **"NAT"** en tu router.

Crea estas 3 reglas:

#### Cámara 1 (192.168.0.8)
```
Service Name: Camara_Huron_1
External Port: 8554
Internal Port: 554
Internal IP: 192.168.0.8
Protocol: TCP
```

#### Cámara 2 (192.168.0.9)
```
Service Name: Camara_Huron_2
External Port: 8555
Internal Port: 554
Internal IP: 192.168.0.9
Protocol: TCP
```

#### Cámara 3 (192.168.0.7)
```
Service Name: Camara_Huron_3
External Port: 8556
Internal Port: 554
Internal IP: 192.168.0.7
Protocol: TCP
```

### Paso 4: Verificar desde Internet

Desde tu Mac, usa una conexión **diferente** (celular con datos móviles):

```bash
# Reemplaza TU_IP_PUBLICA con la IP del paso 1
ffmpeg -i rtsp://admin:Sb123456@TU_IP_PUBLICA:8554/h264Preview_01_main \
       -frames 1 test.jpg

# Si funciona, verás "Output #0" y se creará test.jpg
```

### Paso 5: Configurar Lightsail

```bash
# Conectar a Lightsail
ssh -i ferret-recorder-key.pem ubuntu@3.147.46.191

# Editar .env
nano ~/titulo/video-recording-system/.env
```

Agregar (reemplaza TU_IP_PUBLICA):

```bash
# Cámaras accesibles desde internet
CAMERA_1_URL=rtsp://admin:Sb123456@TU_IP_PUBLICA:8554/h264Preview_01_main
CAMERA_1_NAME=Reolink_Huron_Principal

CAMERA_2_URL=rtsp://admin:Sb123456@TU_IP_PUBLICA:8555/h264Preview_01_main
CAMERA_2_NAME=Reolink_Huron_Secundaria

CAMERA_3_URL=rtsp://admin:Sb123456@TU_IP_PUBLICA:8556/h264Preview_01_main
CAMERA_3_NAME=Reolink_Huron_3

# Configuración
SEGMENT_DURATION=600
VIDEO_CODEC=copy
LOCAL_RETENTION_HOURS=24

# AWS S3
AWS_ACCESS_KEY_ID=<tu-key>
AWS_SECRET_ACCESS_KEY=<tu-secret>
AWS_REGION=us-east-2
S3_BUCKET_NAME=ferret-recordings-bucket
```

### Paso 6: Iniciar en Lightsail

```bash
cd ~/titulo/video-recording-system
python services/video_recorder.py
```

### ⚠️ Medidas de Seguridad CRÍTICAS

1. **Restringir acceso solo a Lightsail** (en router si es posible):
   - Source IP: `3.147.46.191`
   - Solo esta IP puede acceder

2. **Cambiar contraseña de cámaras:**
   ```bash
   # Usar contraseña más fuerte que "Sb123456"
   # Accede a cada cámara y cambia en:
   # Settings → User Management → Change Password
   ```

3. **Firewall en Lightsail:**
   ```bash
   # Verificar que solo puerto 22 (SSH) esté abierto
   sudo ufw status
   
   # Si no está configurado:
   sudo ufw allow 22/tcp
   sudo ufw enable
   ```

4. **Monitorear accesos:**
   ```bash
   # Revisar logs de cámaras periódicamente
   # Buscar intentos de acceso no autorizados
   ```

### 🔴 Desventajas de Port Forwarding

- ❌ **Inseguro** - Cámaras expuestas a internet
- ❌ **IP dinámica** - Si cambia tu IP, deja de funcionar
- ❌ **Alto bandwidth** - Streaming constante 24/7
- ❌ **Vulnerable** - Posibles ataques si no se asegura bien

### Consumo de Bandwidth Estimado

```
3 cámaras × 2 Mbps × 24h × 30 días
= ~50 GB/día
= ~1,500 GB/mes

Lightsail incluye 2 TB/mes, así que estás dentro del límite.
```

---

## 🔒 Opción 2: Tailscale VPN (Seguro - 30 minutos)

Esta opción es **mucho más segura** y no expone tus cámaras a internet.

### Ventajas sobre Port Forwarding

- ✅ **Muy seguro** (WireGuard encryption)
- ✅ **No expone cámaras** a internet
- ✅ **IP estable** (IP virtual de Tailscale)
- ✅ **Fácil de mantener**
- ✅ **Gratis** para uso personal

### Paso 1: Crear Cuenta Tailscale

1. Ve a: https://tailscale.com/
2. Click en "Get Started"
3. Registra con Google/GitHub/Email
4. Es **gratis** para uso personal (hasta 100 dispositivos)

### Paso 2: Instalar en Mac (Gateway)

```bash
# Instalar Tailscale
brew install --cask tailscale

# Iniciar aplicación Tailscale
# Se abrirá un ícono en la barra de menú

# Autenticar (se abrirá navegador)
sudo tailscale up

# Habilitar subnet routing (IMPORTANTE)
sudo tailscale up --advertise-routes=192.168.0.0/24

# Verificar IP asignada
tailscale ip -4
# Ejemplo: 100.101.102.103
```

### Paso 3: Aprobar Subnet Routes

1. Ve a: https://login.tailscale.com/admin/machines
2. Busca tu Mac en la lista
3. Click en los 3 puntos (⋮) → "Edit route settings..."
4. **Aprobar** la ruta `192.168.0.0/24`
5. Marcar "Use as exit node" (opcional)

### Paso 4: Instalar en Lightsail

```bash
# Conectar a Lightsail
ssh -i ferret-recorder-key.pem ubuntu@3.147.46.191

# Instalar Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Iniciar y autenticar
sudo tailscale up

# Se abrirá un link, cópialo y ábrelo en tu navegador
# Autenticar el servidor

# Verificar IP
tailscale ip -4
# Ejemplo: 100.101.102.104

# Verificar que puede ver tu red local
ping 192.168.0.8
ping 192.168.0.9
ping 192.168.0.7
```

### Paso 5: Probar Conexión RTSP

```bash
# Desde Lightsail
ffmpeg -i rtsp://admin:Sb123456@192.168.0.8:554/h264Preview_01_main \
       -frames 1 test.jpg

# Si funciona, verás "Output #0" y se creará test.jpg
```

### Paso 6: Configurar en Lightsail

```bash
# Editar .env
nano ~/titulo/video-recording-system/.env
```

Agregar (usa las IPs locales, NO necesitas la IP pública):

```bash
# Cámaras accesibles vía Tailscale
CAMERA_1_URL=rtsp://admin:Sb123456@192.168.0.8:554/h264Preview_01_main
CAMERA_1_NAME=Reolink_Huron_Principal

CAMERA_2_URL=rtsp://admin:Sb123456@192.168.0.9:554/h264Preview_01_main
CAMERA_2_NAME=Reolink_Huron_Secundaria

CAMERA_3_URL=rtsp://admin:Sb123456@192.168.0.7:554/h264Preview_01_main
CAMERA_3_NAME=Reolink_Huron_3

# Configuración
SEGMENT_DURATION=600
VIDEO_CODEC=copy
LOCAL_RETENTION_HOURS=24

# AWS S3
AWS_ACCESS_KEY_ID=<tu-key>
AWS_SECRET_ACCESS_KEY=<tu-secret>
AWS_REGION=us-east-2
S3_BUCKET_NAME=ferret-recordings-bucket
```

### Paso 7: Iniciar en Lightsail

```bash
cd ~/titulo/video-recording-system
python services/video_recorder.py
```

### ✅ Ventajas de Tailscale

- ✅ **Muy seguro** - Encriptación WireGuard
- ✅ **Sin Port Forwarding** - No tocar router
- ✅ **IP estable** - No importa si cambia tu IP pública
- ✅ **Fácil de usar** - Click y listo
- ✅ **Gratis** - Plan personal sin costo

### 📝 Mantener Tailscale Activo

En tu Mac:

```bash
# Verificar que Tailscale está corriendo
tailscale status

# Si se detiene, reiniciar
sudo tailscale up --advertise-routes=192.168.0.0/24

# Para que inicie automáticamente al arrancar Mac
# (ya configurado por la aplicación)
```

En Lightsail:

```bash
# Verificar status
sudo tailscale status

# Reiniciar si es necesario
sudo tailscale up
```

---

## 🆚 Comparación Final

| Aspecto | Port Forwarding | Tailscale VPN |
|---------|----------------|---------------|
| **Seguridad** | ❌ Baja | ✅ Alta |
| **Tiempo Setup** | ⏱️ 15 min | ⏱️ 30 min |
| **Complejidad** | ⭐ Fácil | ⭐⭐ Media |
| **Costo** | 💰 Gratis | 💰 Gratis |
| **Expone cámaras** | ❌ Sí | ✅ No |
| **Requiere Mac 24/7** | ❌ No | ✅ Sí |
| **Configuración router** | ✅ Sí | ❌ No |
| **Mantención** | 🔴 Media | 🟢 Baja |

---

## 🎯 Mi Recomendación

### Para Desarrollo/Testing
**Opción 1: Port Forwarding**
- Más rápido de configurar
- Puedes empezar ahora mismo
- **IMPORTANTE**: Cambiar contraseñas y restringir IPs

### Para Producción/Largo Plazo
**Opción 2: Tailscale VPN**
- Más seguro
- No expone cámaras
- Más estable
- Vale la pena los 15 minutos extra

---

## 📋 Checklist de Implementación

### Si eliges Port Forwarding:

- [ ] Obtener IP pública
- [ ] Acceder a router
- [ ] Configurar 3 reglas de port forwarding
- [ ] Probar desde internet (celular)
- [ ] Configurar .env en Lightsail
- [ ] **CAMBIAR contraseñas de cámaras**
- [ ] **Restringir acceso solo a IP de Lightsail**
- [ ] Iniciar video_recorder.py
- [ ] Verificar que graba correctamente

### Si eliges Tailscale:

- [ ] Crear cuenta Tailscale
- [ ] Instalar en Mac
- [ ] Habilitar subnet routing
- [ ] Aprobar rutas en admin
- [ ] Instalar en Lightsail
- [ ] Autenticar Lightsail
- [ ] Probar ping a cámaras
- [ ] Configurar .env en Lightsail
- [ ] Iniciar video_recorder.py
- [ ] Verificar que graba correctamente

---

## 🐛 Troubleshooting

### Port Forwarding: No funciona desde internet

```bash
# Verificar que router tiene IP pública real
curl ifconfig.me
# Si es 192.168.x.x o 10.x.x.x, estás detrás de CGNAT

# Probar conectividad
telnet TU_IP_PUBLICA 8554
# Debe conectar, si no, el puerto no está abierto

# Verificar firewall de Mac
sudo pfctl -s rules | grep 8554
```

### Tailscale: No puede ver cámaras

```bash
# En Mac, verificar que subnet está anunciada
tailscale status | grep 192.168.0.0

# Verificar en Lightsail
ping 192.168.0.1  # Gateway debe responder
ping 192.168.0.8  # Cámaras deben responder

# Si no funciona, reiniciar Tailscale en Mac
sudo tailscale down
sudo tailscale up --advertise-routes=192.168.0.0/24
```

### Lightsail: FFmpeg no puede conectar

```bash
# Probar conectividad RTSP
ffmpeg -rtsp_transport tcp \
       -i rtsp://admin:Sb123456@IP_CAMARA:PUERTO/h264Preview_01_main \
       -frames 1 test.jpg

# Ver logs detallados
ffmpeg -loglevel debug -i rtsp://...
```

---

## ⚠️ IMPORTANTE: Mac debe estar encendido 24/7

Con ambas opciones:

- ✅ **Port Forwarding**: Mac NO necesita estar encendido (router hace el forward)
- ❌ **Tailscale**: Mac SÍ necesita estar encendido (hace de gateway)

Si tu Mac se apaga:
- **Port Forwarding**: ✅ Cámaras siguen accesibles
- **Tailscale**: ❌ Lightsail pierde acceso a cámaras

---

## 🚀 Iniciar Sistema en Lightsail

Una vez configurada cualquiera de las opciones:

```bash
# Conectar a Lightsail
ssh -i ferret-recorder-key.pem ubuntu@3.147.46.191

# Ir al directorio
cd ~/titulo/video-recording-system

# Activar entorno virtual
source ~/venv/bin/activate

# Iniciar grabación
python services/video_recorder.py &

# Iniciar uploader S3
python services/s3_uploader.py &

# Ver logs
tail -f ~/titulo/logs/recorder.log
```

---

## 📊 Monitoreo

```bash
# Ver procesos
ps aux | grep video_recorder

# Ver videos grabándose
ls -lh ~/titulo/video-recording-system/data/videos/recordings/

# Ver recursos del servidor
htop
```

---

**¿Cuál opción prefieres implementar?**

1. **Port Forwarding** (15 min, menos seguro)
2. **Tailscale VPN** (30 min, muy seguro)

Te guiaré paso a paso en la configuración de la que elijas.
