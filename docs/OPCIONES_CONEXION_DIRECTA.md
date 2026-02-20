# 🎥 Opciones de Conexión Directa desde Lightsail

## 📋 Configuración Actual de la Cámara

Basado en la captura de pantalla:

```
IP Address: 192.168.0.9
Subnet Mask: 255.255.255.0
Gateway: 192.168.0.1
Preferred DNS: 190.160.0.15
Alternate DNS: 200.83.1.5
MAC Address: d8:74:ef:55:00:f0
Connection Type: DHCP
```

**RTSP URL actual:**
```
rtsp://admin:Sb123456@192.168.0.9:554/h264Preview_01_main
```

---

## ⚠️ El Problema

La IP `192.168.0.9` es una **IP privada** (clase C) que **NO es accesible desde internet**.

```
[Lightsail 3.147.46.191]  ❌  →  [192.168.0.9]
    (Internet)                    (Red privada)
```

Para que Lightsail pueda acceder a esta cámara, necesitas **exponer** la cámara de alguna forma a internet.

---

## 🔧 Opciones Técnicas Viables

### Opción 1: Port Forwarding + IP Pública (Más Simple)

**Descripción:** Configurar tu router para reenviar el puerto RTSP de la cámara

#### Pasos:

1. **Verificar IP pública de tu internet:**
   ```bash
   curl ifconfig.me
   # Ejemplo: 181.45.67.123 (tu IP pública)
   ```

2. **Acceder al router** (192.168.0.1)
   - Usuario/password de tu ISP o router
   - Buscar sección "Port Forwarding" o "NAT"

3. **Configurar regla de Port Forwarding:**
   ```
   External Port: 8554 (cualquier puerto libre > 1024)
   Internal Port: 554 (RTSP)
   Internal IP: 192.168.0.9
   Protocol: TCP
   ```

4. **Probar desde fuera:**
   ```bash
   # Desde tu Mac o cualquier red externa
   ffmpeg -i rtsp://admin:Sb123456@TU_IP_PUBLICA:8554/h264Preview_01_main -frames 1 test.jpg
   ```

5. **Configurar en Lightsail:**
   ```bash
   # .env en Lightsail
   CAMERA_1_URL=rtsp://admin:Sb123456@TU_IP_PUBLICA:8554/h264Preview_01_main
   ```

#### Ventajas:
- ✅ Conexión directa desde Lightsail
- ✅ Simple de configurar (solo router)
- ✅ No requiere software adicional

#### Desventajas:
- ❌ **MUY INSEGURO** (cámara expuesta a internet)
- ❌ IP pública puede cambiar (si no es estática)
- ❌ Vulnerable a ataques
- ❌ Ancho de banda: streams constantes consumen mucho

#### Seguridad Adicional:
```bash
# En router, restringir acceso solo a IP de Lightsail
Source IP: 3.147.46.191 (solo Lightsail puede conectar)
```

---

### Opción 2: DDNS (Dynamic DNS)

**Descripción:** Usar un servicio DDNS para tener un dominio que siempre apunte a tu IP pública

#### Si la cámara soporta DDNS:

1. **Verificar si tu cámara Reolink soporta DDNS:**
   - Acceder a la configuración web de la cámara
   - Buscar sección "Network" → "DDNS"
   
2. **Servicios DDNS gratuitos:**
   - No-IP (https://www.noip.com/)
   - DuckDNS (https://www.duckdns.org/)
   - Dynu (https://www.dynu.com/)

3. **Configurar:**
   ```
   Servicio: No-IP
   Hostname: mi-camara-huron.ddns.net
   Username: tu-usuario-noip
   Password: tu-password-noip
   ```

4. **Port Forwarding en router** (igual que Opción 1)

5. **URL final:**
   ```
   rtsp://admin:Sb123456@mi-camara-huron.ddns.net:8554/h264Preview_01_main
   ```

#### Ventajas:
- ✅ No te afecta si cambia tu IP pública
- ✅ Más fácil de recordar

#### Desventajas:
- ❌ Igual de inseguro que Opción 1
- ❌ Depende de servicio externo (DDNS)

---

### Opción 3: Túnel SSH Reverso (Más Seguro pero Complejo)

**Descripción:** Tu Mac local crea un túnel hacia Lightsail

```
[Cámara] ← [Mac Local] ←─ SSH Tunnel ─→ [Lightsail]
192.168.0.9   (siempre encendido)      3.147.46.191
```

#### Pasos:

1. **En tu Mac (mantener corriendo 24/7):**
   ```bash
   # Crear túnel reverso
   ssh -i /Users/sbriceno/Documents/projects/titulo/ferret-recorder-key.pem \
       -R 8554:192.168.0.9:554 \
       -N \
       ubuntu@3.147.46.191
   
   # -R: Reverse tunnel
   # 8554: Puerto en Lightsail
   # 192.168.0.9:554: Cámara local
   # -N: No ejecutar comandos
   ```

2. **En Lightsail, la cámara estará disponible en:**
   ```
   rtsp://admin:Sb123456@localhost:8554/h264Preview_01_main
   ```

3. **Para múltiples cámaras:**
   ```bash
   # Cámara 1
   ssh -R 8554:192.168.0.8:554 ubuntu@3.147.46.191 -N &
   
   # Cámara 2
   ssh -R 8555:192.168.0.9:554 ubuntu@3.147.46.191 -N &
   
   # Cámara 3
   ssh -R 8556:192.168.0.7:554 ubuntu@3.147.46.191 -N &
   ```

4. **Mantener túnel activo con autossh:**
   ```bash
   # Instalar autossh
   brew install autossh
   
   # Ejecutar con auto-reconexión
   autossh -M 0 -f \
       -i /Users/sbriceno/Documents/projects/titulo/ferret-recorder-key.pem \
       -R 8554:192.168.0.9:554 \
       ubuntu@3.147.46.191 \
       -N
   ```

#### Ventajas:
- ✅ **Seguro** (encriptado con SSH)
- ✅ No requiere abrir puertos en router
- ✅ No expone cámaras directamente

#### Desventajas:
- ⚠️ Requiere Mac local siempre encendido
- ⚠️ **Alto consumo de ancho de banda** (streams 24/7)
- ⚠️ Latencia adicional de red
- ⚠️ Túnel puede caerse (necesita autossh)

#### Consumo estimado:
```
3 cámaras × 2 Mbps × 24h/día × 30 días
= ~650 GB/mes de transferencia

Lightsail incluye 2 TB/mes, pero es un uso intensivo
```

---

### Opción 4: VPN con Tailscale (Moderna y Simple)

**Descripción:** Crear una red privada virtual entre tu red local y Lightsail

```
[Red Local 100.x.x.x] ←─ Tailscale VPN ─→ [Lightsail 100.y.y.y]
     |                                            |
  Cámaras                                   Accede por VPN
```

#### Pasos:

1. **Crear cuenta en Tailscale** (https://tailscale.com/)
   - Plan gratuito: 100 dispositivos
   - No requiere configuración de router

2. **En tu Mac:**
   ```bash
   # Instalar Tailscale
   brew install --cask tailscale
   
   # Iniciar y autenticar
   sudo tailscale up
   
   # Ver tu IP de Tailscale
   tailscale ip -4
   # Ejemplo: 100.101.102.103
   ```

3. **En Lightsail:**
   ```bash
   ssh ubuntu@3.147.46.191
   
   # Instalar Tailscale
   curl -fsSL https://tailscale.com/install.sh | sh
   
   # Iniciar
   sudo tailscale up
   
   # Ver IP
   tailscale ip -4
   # Ejemplo: 100.101.102.104
   ```

4. **Habilitar subnet routing en Mac:**
   ```bash
   # Anunciar tu red local (192.168.0.0/24) a Tailscale
   sudo tailscale up --advertise-routes=192.168.0.0/24
   ```

5. **Aprobar en Tailscale Admin:**
   - https://login.tailscale.com/admin/machines
   - Buscar tu Mac
   - Click "Edit route settings"
   - Aprobar subnet route

6. **En Lightsail, ahora puedes acceder:**
   ```bash
   # Las cámaras son accesibles directamente
   ping 192.168.0.9  # ✅ Funciona
   
   # RTSP URL
   rtsp://admin:Sb123456@192.168.0.9:554/h264Preview_01_main
   ```

#### Ventajas:
- ✅ **Muy seguro** (WireGuard encryption)
- ✅ **Fácil de configurar**
- ✅ **Gratis** para uso personal
- ✅ No requiere configurar router
- ✅ Funciona detrás de NAT
- ✅ Bajas latencias

#### Desventajas:
- ⚠️ Requiere Mac local como gateway (siempre encendido)
- ⚠️ **Alto consumo de ancho de banda** (igual que túnel SSH)
- ⚠️ Depende de servicio externo (Tailscale)

---

## 📊 Comparación de Opciones

| Opción | Seguridad | Dificultad | Costo | Ancho de Banda | Mac 24/7 |
|--------|-----------|------------|-------|----------------|----------|
| **Port Forwarding** | ❌ Baja | ⭐ Fácil | Gratis | 🔴 Alto | No |
| **DDNS** | ❌ Baja | ⭐⭐ Media | Gratis | 🔴 Alto | No |
| **Túnel SSH** | ✅ Alta | ⭐⭐⭐ Difícil | Gratis | 🔴 Alto | ✅ Sí |
| **Tailscale VPN** | ✅ Alta | ⭐⭐ Media | Gratis | 🔴 Alto | ✅ Sí |
| **Arquitectura Híbrida** | ✅ Alta | ⭐⭐ Media | $10-15/mes | 🟢 Bajo | ✅ Sí |

---

## 🎯 Recomendación Final

### Para tu caso específico:

Dado que:
- Tienes 3 cámaras (192.168.0.7, 192.168.0.8, 192.168.0.9)
- Ya tienes sistema de grabación local funcionando
- Ya subes a S3 automáticamente
- Es un proyecto de tesis (no producción crítica)

**Sigue con la Arquitectura Híbrida** 🏆

### ¿Por qué NO usar conexión directa?

1. **Ancho de banda:**
   ```
   3 cámaras × 2 Mbps × 24h × 30 días = ~650 GB/mes
   Solo en streaming constante (sin contar uploads)
   ```

2. **Seguridad:**
   - Port Forwarding expone cámaras a internet
   - Riesgo de accesos no autorizados

3. **Confiabilidad:**
   - Si cae internet, pierdes todo
   - Con híbrido, sigues grabando localmente

4. **Costo:**
   - Conexión directa: Gratis pero arriesgado
   - Híbrido: ~$10-15/mes pero seguro y confiable

---

## 🚀 Si AÚN quieres Conexión Directa

La **mejor opción técnica** sería:

### Tailscale VPN (Opción 4)

```bash
# 1. En tu Mac
brew install --cask tailscale
sudo tailscale up --advertise-routes=192.168.0.0/24

# 2. En Lightsail
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# 3. Aprobar subnet en Tailscale admin

# 4. En Lightsail .env
CAMERA_1_URL=rtsp://admin:Sb123456@192.168.0.8:554/h264Preview_01_main
CAMERA_2_URL=rtsp://admin:Sb123456@192.168.0.9:554/h264Preview_01_main
CAMERA_3_URL=rtsp://admin:Sb123456@192.168.0.7:554/h264Preview_01_main
```

**Tiempo de configuración:** 15-20 minutos  
**Requiere:** Mac encendido 24/7

---

## 🤔 ¿Qué Prefieres?

### Opción A: Arquitectura Híbrida (Recomendada)
- ✅ Ya funciona
- ✅ Segura
- ✅ Confiable
- ✅ Económica en ancho de banda
- ❌ Videos con delay (hasta que suban a S3)

### Opción B: Tailscale VPN (Conexión Directa)
- ✅ Acceso directo a cámaras
- ✅ Streaming en tiempo real
- ✅ Segura
- ❌ Alto consumo de bandwidth
- ❌ Requiere Mac 24/7
- ❌ Más complejo

### Opción C: Port Forwarding (Rápido pero Inseguro)
- ✅ Simple de configurar
- ✅ Acceso directo
- ❌ **MUY INSEGURO**
- ❌ Alto consumo de bandwidth
- ❌ No recomendado

---

## 📝 Conclusión

Con la configuración actual de tu cámara (`192.168.0.9`), **SÍ es técnicamente posible** conectar desde Lightsail, pero:

1. **Port Forwarding**: Funciona pero es inseguro
2. **Tailscale**: Funciona, es seguro, pero consume mucho bandwidth
3. **Túnel SSH**: Funciona, es seguro, pero es complejo

**Mi recomendación:** Mantén la arquitectura híbrida actual. Si necesitas acceso en tiempo real, considera Tailscale.

¿Quieres que te ayude a configurar alguna de estas opciones?
