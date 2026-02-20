# 🔐 Acceso al Router VTR ARRIS - Guía Completa

## 📋 Información de tu Router

**Modelo:** ARRIS (VTR)
**SSID 2.4GHz:** ARRIS - 8E32
**SSID 5GHz:** ARRIS - 8E32 - 5G
**CMAC:** F863D9C08E32

---

## 🔑 Credenciales de Acceso

### Opción 1: Credenciales VTR por Defecto (Más Común)

**URL:** http://192.168.0.1

**Usuario:** `admin`
**Contraseña:** `VTR.2019`

### Opción 2: Alternativas

Si `VTR.2019` no funciona, prueba:

1. **Usuario:** `admin` / **Contraseña:** `admin`
2. **Usuario:** `admin` / **Contraseña:** `password`
3. **Usuario:** `admin` / **Contraseña:** `1234`
4. **Usuario:** `admin` / **Contraseña:** (dejar en blanco)
5. **Usuario:** `admin` / **Contraseña:** últimos 8 dígitos del CMAC: `D9C08E32`

### Opción 3: IP Alternativa

A veces el router VTR está en:

**URL:** http://192.168.1.1

---

## 🚀 Pasos para Acceder

### 1. Abrir el Router

```bash
# Probar primera IP
open http://192.168.0.1

# Si no funciona, probar segunda
open http://192.168.1.1
```

### 2. Iniciar Sesión

Prueba las credenciales en este orden:
1. `admin` / `VTR.2019`
2. `admin` / `admin`
3. `admin` / `D9C08E32`

### 3. Navegar a Port Forwarding

Una vez dentro, busca:
- **"Configuración Avanzada"** o **"Advanced"**
- **"Port Forwarding"** o **"Reenvío de Puertos"**
- **"Virtual Server"** o **"Servidor Virtual"**
- **"NAT"** o **"Aplicaciones y Juegos"**

---

## ⚙️ Configurar Port Forwarding en Router VTR

### Ubicación en el Menú

En routers VTR ARRIS:
```
Avanzado → Configuración de Red → Port Forwarding
o
Advanced → Network Settings → Port Forwarding
o
Gateway → Connection → Port Forwarding
```

### Configuración para las Cámaras

#### Cámara 1 (192.168.0.8)
```
Service Name:     Camara_Huron_1
External Port:    8554
Internal Port:    554
Internal IP:      192.168.0.8
Protocol:         TCP
Enable:           ✓ (marcado)
```

#### Cámara 2 (192.168.0.9)
```
Service Name:     Camara_Huron_2
External Port:    8555
Internal Port:    554
Internal IP:      192.168.0.9
Protocol:         TCP
Enable:           ✓ (marcado)
```

#### Cámara 3 (192.168.0.7)
```
Service Name:     Camara_Huron_3
External Port:    8556
Internal Port:    554
Internal IP:      192.168.0.7
Protocol:         TCP
Enable:           ✓ (marcado)
```

### Guardar Configuración

1. Click en **"Agregar"** o **"Add"** para cada regla
2. Click en **"Guardar"** o **"Save"**
3. Click en **"Aplicar"** o **"Apply"**

**⚠️ El router puede reiniciarse (espera 1-2 minutos)**

---

## 🐛 Si No Puedes Acceder

### Problema 1: No carga la página

```bash
# Verificar gateway
netstat -nr | grep default

# Debe mostrar 192.168.0.1 o 192.168.1.1

# Probar ping
ping 192.168.0.1

# Si no responde, prueba la otra IP
ping 192.168.1.1
```

### Problema 2: Contraseña incorrecta

**Llama a VTR:** 600 800 9000

Diles:
- "Necesito la contraseña de administrador de mi router"
- "Quiero configurar port forwarding para cámaras de seguridad"
- Tendrán tu contraseña en su sistema

### Problema 3: No encuentras Port Forwarding

Algunos routers VTR tienen esta opción **deshabilitada por defecto**.

**Opciones:**
1. **Llamar a VTR** y pedir que habiliten port forwarding
2. **Pedir modo bridge** (te dan acceso completo)
3. **Usar Tailscale VPN** (no necesita port forwarding)

---

## 🔧 Modo Bridge (Alternativa)

Si VTR no permite port forwarding, puedes pedir **modo bridge**:

1. Llama a VTR: 600 800 9000
2. Pide: "Quiero el modem en modo bridge"
3. Ellos lo configuran remotamente
4. Necesitarás tu propio router (ej: TP-Link, Asus)

**Ventajas del modo bridge:**
- Control total del router
- Puedes hacer cualquier configuración
- Mejor para aplicaciones avanzadas

---

## 📞 Contacto VTR

**Teléfono:** 600 800 9000
**Chat:** https://www.vtr.com
**Twitter:** @VTR_Chile

**Qué decir:**
> "Hola, necesito configurar port forwarding en mi router ARRIS
> para acceder remotamente a mis cámaras de seguridad.
> 
> Necesito abrir los puertos 8554, 8555 y 8556 (TCP)
> hacia las IPs internas 192.168.0.8, 192.168.0.9 y 192.168.0.7"

---

## 🔒 Alternativa: Tailscale VPN (Recomendado)

Si no puedes configurar port forwarding o VTR lo bloquea, **usa Tailscale**:

**Ventajas:**
- ✅ No necesitas tocar el router
- ✅ Mucho más seguro
- ✅ Gratis
- ✅ Funciona con cualquier ISP

**Tiempo de configuración:** 30 minutos

Ver guía: `EXPONER_CAMARAS_LIGHTSAIL.md` → Opción 2

---

## 📊 Tabla de Credenciales a Probar

| Orden | URL | Usuario | Contraseña |
|-------|-----|---------|------------|
| 1 | http://192.168.0.1 | admin | VTR.2019 |
| 2 | http://192.168.0.1 | admin | admin |
| 3 | http://192.168.0.1 | admin | D9C08E32 |
| 4 | http://192.168.1.1 | admin | VTR.2019 |
| 5 | http://192.168.1.1 | admin | admin |

---

## ✅ Verificar que Funcionó

Después de configurar:

```bash
# Probar desde tu Mac
./verificar_port_forwarding.sh

# Probar desde celular (datos móviles)
telnet 200.104.174.206 8554
```

---

## 🎯 Próximos Pasos

1. **Intenta acceder** con las credenciales de arriba
2. **Si no funciona**, llama a VTR
3. **Mientras tanto**, considera usar Tailscale VPN (no necesita acceso al router)

**¿Te funcionó alguna contraseña?** Avísame para continuar con la configuración.
