# 🔧 Configuración Port Forwarding - Guía Paso a Paso

## 📋 Tu Información

**IP Pública detectada:** Se obtendrá en tiempo real

**Cámaras a exponer:**
- Cámara 1: `192.168.0.8` → Puerto externo: `8554`
- Cámara 2: `192.168.0.9` → Puerto externo: `8555`
- Cámara 3: `192.168.0.7` → Puerto externo: `8556`

**Gateway (Router):** `192.168.0.1`

---

## 🚀 Paso 1: Obtener IP Pública

Ejecuta en tu terminal:

```bash
curl ifconfig.me
```

**Anota esta IP**, la necesitarás para configurar Lightsail.

---

## 🔧 Paso 2: Acceder al Router

### 2.1 Abrir navegador

```bash
# Opción 1: Abrir automáticamente
open http://192.168.0.1

# Opción 2: Copia y pega en navegador
# http://192.168.0.1
```

### 2.2 Iniciar sesión

El usuario y contraseña dependen de tu ISP/router:

**Opciones comunes:**
- Usuario: `admin` / Password: `admin`
- Usuario: `admin` / Password: (en blanco)
- Usuario: `admin` / Password: `1234`
- Busca en la etiqueta del router

---

## 🎯 Paso 3: Configurar Port Forwarding en Router

### 3.1 Buscar la sección

La opción puede llamarse:
- **"Port Forwarding"**
- **"Virtual Server"**
- **"NAT"**
- **"Applications"**
- **"Port Mapping"**

Usualmente está en:
- `Advanced` → `Port Forwarding`
- `NAT` → `Virtual Server`
- `Firewall` → `Port Forwarding`

### 3.2 Agregar 3 Reglas

#### Regla 1: Cámara Principal (192.168.0.8)

```
Nombre/Description:    Camara_Huron_1
Service Type:          Custom / Manual
External Port:         8554
Internal Port:         554
Internal IP Address:   192.168.0.8
Protocol:             TCP (o TCP/UDP)
Enable/Active:        ✓ (marcado)
```

#### Regla 2: Cámara Secundaria (192.168.0.9)

```
Nombre/Description:    Camara_Huron_2
Service Type:          Custom / Manual
External Port:         8555
Internal Port:         554
Internal IP Address:   192.168.0.9
Protocol:             TCP (o TCP/UDP)
Enable/Active:        ✓ (marcado)
```

#### Regla 3: Cámara 3 (192.168.0.7)

```
Nombre/Description:    Camara_Huron_3
Service Type:          Custom / Manual
External Port:         8556
Internal Port:         554
Internal IP Address:   192.168.0.7
Protocol:             TCP (o TCP/UDP)
Enable/Active:        ✓ (marcado)
```

### 3.3 Guardar cambios

- Click en **"Save"** o **"Apply"**
- Puede que el router se reinicie (espera 1-2 minutos)

---

## ✅ Paso 4: Verificar que Funciona

### 4.1 Desde tu Mac (mismo wifi)

```bash
cd /Users/sbriceno/Documents/projects/titulo
./verificar_port_forwarding.sh
```

Este script verificará:
- ✅ IP pública obtenida
- ✅ Puertos abiertos
- ✅ Conexión RTSP funcionando

### 4.2 Desde Internet (celular con datos)

Desconecta tu celular del WiFi y usa datos móviles:

```bash
# Reemplaza TU_IP_PUBLICA con la IP del paso 1
telnet TU_IP_PUBLICA 8554
```

Si conecta, ¡funciona! (Presiona Ctrl+C para salir)

---

## 🔐 Paso 5: Medidas de Seguridad CRÍTICAS

### 5.1 Cambiar Contraseñas de Cámaras

**IMPORTANTE:** La contraseña actual `Sb123456` es vulnerable.

Para cada cámara:

1. Accede a la cámara en navegador:
   - http://192.168.0.8
   - http://192.168.0.9
   - http://192.168.0.7

2. Login: `admin` / `Sb123456`

3. Ve a: `Settings` → `User Management` → `Change Password`

4. Nueva contraseña (ejemplo):
   ```
   H@r0n#2026!Cam1
   H@r0n#2026!Cam2
   H@r0n#2026!Cam3
   ```

5. Actualiza el archivo `.env` con las nuevas contraseñas

### 5.2 Restringir Acceso (Si tu router lo permite)

Si tu router tiene opción de **"Source IP Restriction"**:

```
Source IP:  3.147.46.191  (IP de Lightsail)
Action:     Allow
```

Esto permite que **SOLO** Lightsail acceda a las cámaras.

### 5.3 Habilitar Firewall en Mac

```bash
# Habilitar firewall
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on

# Bloquear conexiones entrantes
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setblockall off

# Modo stealth (no responde a ping)
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setstealthmode on
```

---

## 🌐 Paso 6: Configurar Lightsail

### 6.1 Crear archivo .env para Lightsail

El archivo ya está preparado en:
`deploy/lightsail-cameras.env`

### 6.2 Subir a Lightsail

```bash
# Conectar a Lightsail
ssh -i ferret-recorder-key.pem ubuntu@3.147.46.191

# Crear directorio si no existe
mkdir -p ~/titulo/video-recording-system

# Salir
exit
```

Desde tu Mac:

```bash
# Copiar archivo .env
scp -i ferret-recorder-key.pem \
    deploy/lightsail-cameras.env \
    ubuntu@3.147.46.191:~/titulo/video-recording-system/.env
```

### 6.3 Iniciar Grabación en Lightsail

```bash
# Conectar
ssh -i ferret-recorder-key.pem ubuntu@3.147.46.191

# Activar entorno
cd ~/titulo/video-recording-system
source ~/venv/bin/activate

# Iniciar grabación
python services/video_recorder.py &

# Ver logs
tail -f ~/titulo/logs/recorder.log
```

---

## 📊 Paso 7: Monitorear

### Verificar que está grabando

```bash
# En Lightsail
ls -lh ~/titulo/video-recording-system/data/videos/recordings/

# Debe mostrar archivos .mp4 recientes
```

### Ver uso de recursos

```bash
htop
```

Busca procesos `ffmpeg` (debe haber 3, uno por cámara)

---

## 🐛 Troubleshooting

### Problema: No puedo acceder al router (192.168.0.1)

```bash
# Verificar gateway
netstat -nr | grep default

# Probar ping
ping 192.168.0.1
```

### Problema: Puerto no abre desde internet

```bash
# Verificar que tienes IP pública real (no CGNAT)
curl ifconfig.me
# Si empieza con 100.x.x.x o 192.168.x.x, estás detrás de CGNAT
# Contacta a tu ISP

# Verificar firewall del router
# Busca en configuración: "Firewall" o "Security"
# Asegúrate que no bloquea puertos 8554-8556
```

### Problema: FFmpeg no conecta desde Lightsail

```bash
# Probar con más verbosidad
ffmpeg -loglevel debug \
       -rtsp_transport tcp \
       -i rtsp://admin:PASSWORD@IP_PUBLICA:8554/h264Preview_01_main \
       -frames 1 test.jpg

# Ver qué dice el error
```

### Problema: Cámaras no responden

```bash
# Desde tu Mac, verificar que cámaras están online
ping 192.168.0.8
ping 192.168.0.9
ping 192.168.0.7

# Probar RTSP localmente
ffmpeg -i rtsp://admin:Sb123456@192.168.0.8:554/h264Preview_01_main \
       -frames 1 test.jpg
```

---

## ⚠️ Advertencias Finales

1. **Cámaras expuestas:** Ahora están accesibles desde internet
2. **Cambia contraseñas:** CRÍTICO hacer esto
3. **Monitorea accesos:** Revisa logs de cámaras regularmente
4. **IP dinámica:** Si cambia tu IP, actualiza configuración
5. **Backup .env:** Guarda copia de las credenciales

---

## 📝 Información para Soporte

Si necesitas ayuda de tu ISP, diles:

```
Necesito abrir los siguientes puertos para cámaras de seguridad:
- Puerto 8554 (TCP) → 192.168.0.8:554
- Puerto 8555 (TCP) → 192.168.0.9:554
- Puerto 8556 (TCP) → 192.168.0.7:554

Es para acceso remoto a mis cámaras de vigilancia.
```

---

**¿Listo para continuar? Ejecuta el script de verificación cuando hayas configurado el router.**

```bash
./verificar_port_forwarding.sh
```
