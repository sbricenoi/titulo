# 🔧 Configurar Port Forwarding en Router VTR ARRIS - Paso a Paso

## ✅ Ya Entraste al Router

Ahora sigue estos pasos exactos:

---

## 📋 Paso 1: Ir a la Sección de Firewall

En la página que estás viendo:

1. **Click en la pestaña "Firewall"** (parte superior, sexta pestaña)
2. En el menú lateral izquierdo, busca:
   - **"Port Forwarding"** o
   - **"Reenvío de Puertos"** o
   - **"Virtual Server"** o
   - **"Aplicaciones"**

---

## 📋 Paso 2: Agregar las 3 Reglas

### Regla 1: Cámara Principal (192.168.0.8)

Click en **"Agregar"** o **"Add"** y completa:

```
Nombre/Description:     Camara_Huron_1
Tipo de Servicio:       Personalizado / Custom
Puerto Externo Inicio:  8554
Puerto Externo Fin:     8554
Puerto Interno Inicio:  554
Puerto Interno Fin:     554
Dirección IP Interna:   192.168.0.8
Protocolo:              TCP
Habilitar/Enable:       ✓ (marcado)
```

Click **"Aplicar"** o **"Apply"**

### Regla 2: Cámara Secundaria (192.168.0.9)

Click en **"Agregar"** o **"Add"** nuevamente:

```
Nombre/Description:     Camara_Huron_2
Tipo de Servicio:       Personalizado / Custom
Puerto Externo Inicio:  8555
Puerto Externo Fin:     8555
Puerto Interno Inicio:  554
Puerto Interno Fin:     554
Dirección IP Interna:   192.168.0.9
Protocolo:              TCP
Habilitar/Enable:       ✓ (marcado)
```

Click **"Aplicar"** o **"Apply"**

### Regla 3: Cámara 3 (192.168.0.7)

Click en **"Agregar"** o **"Add"** nuevamente:

```
Nombre/Description:     Camara_Huron_3
Tipo de Servicio:       Personalizado / Custom
Puerto Externo Inicio:  8556
Puerto Externo Fin:     8556
Puerto Interno Inicio:  554
Puerto Interno Fin:     554
Dirección IP Interna:   192.168.0.7
Protocolo:              TCP
Habilitar/Enable:       ✓ (marcado)
```

Click **"Aplicar"** o **"Apply"**

---

## 📋 Paso 3: Guardar Configuración

1. Después de agregar las 3 reglas, busca un botón **"Guardar"** o **"Save"** en la parte superior o inferior
2. Click en **"Guardar"**
3. **El router puede reiniciarse** (espera 1-2 minutos)

---

## ✅ Paso 4: Verificar que Funcionó

Una vez que el router reinicie:

### Desde tu Mac:
```bash
cd /Users/sbriceno/Documents/projects/titulo
./verificar_port_forwarding.sh
```

### Desde celular (datos móviles):
```bash
# Desconecta WiFi, usa datos móviles
telnet 200.104.174.206 8554
```

Si conecta, ¡funcionó! Verás algo como:
```
Trying 200.104.174.206...
Connected to 200.104.174.206.
```

Presiona `Ctrl+C` para salir.

---

## 🖼️ Capturas de Referencia

### Busca algo similar a esto en "Firewall" → "Port Forwarding":

```
┌─────────────────────────────────────────────────────────────┐
│ Port Forwarding / Reenvío de Puertos                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ [Agregar Nueva Regla]                                       │
│                                                              │
│ Nombre:         [_____________]                             │
│ Puerto Externo: [____] - [____]                            │
│ Puerto Interno: [____] - [____]                            │
│ IP Interna:     [___.___.___.___ ]                         │
│ Protocolo:      [TCP ▼] [ ] UDP [ ] Ambos                  │
│                                                              │
│ [Aplicar]  [Cancelar]                                       │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│ Reglas Existentes:                                          │
│                                                              │
│ (Aquí aparecerán las reglas que agregues)                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🐛 Si No Encuentras "Port Forwarding"

### Opción 1: Probar en "Utilidades"

1. Click en pestaña **"Utilidades"**
2. Busca opciones como:
   - **"Port Forwarding"**
   - **"Port Triggering"**
   - **"Aplicaciones"**

### Opción 2: Verificar permisos

Algunos routers VTR tienen Port Forwarding **bloqueado**.

Si no aparece la opción, tienes dos caminos:

#### A) Llamar a VTR para habilitarlo:
```
📞 600 800 9000
Decir: "Necesito que habiliten port forwarding en mi router 
        ARRIS para configurar cámaras de seguridad"
```

#### B) Usar Tailscale VPN (Recomendado):
- No necesita port forwarding
- Más seguro
- Configuración en 30 minutos
- Ver: `EXPONER_CAMARAS_LIGHTSAIL.md` → Opción 2

---

## 📊 Resumen Visual de las Reglas

```
INTERNET (200.104.174.206)          ROUTER VTR           RED LOCAL
                                  (192.168.0.1)
                                        │
     Puerto 8554 ────────────────────→ │ ────→ 192.168.0.8:554 (Cámara 1)
                                        │
     Puerto 8555 ────────────────────→ │ ────→ 192.168.0.9:554 (Cámara 2)
                                        │
     Puerto 8556 ────────────────────→ │ ────→ 192.168.0.7:554 (Cámara 3)
```

---

## 🎯 Próximo Paso Después de Configurar

Una vez que las reglas estén guardadas:

1. **Probar conexión** desde internet
2. **Iniciar grabación en Lightsail**:
   ```bash
   ssh -i ferret-recorder-key.pem ubuntu@3.147.46.191
   cd ~/titulo/video-recording-system
   source ~/venv/bin/activate
   python services/video_recorder.py
   ```

---

**¿Encontraste la sección de Port Forwarding?** 

- Si **SÍ**: Avísame cuando hayas agregado las 3 reglas
- Si **NO**: Dime qué opciones ves en el menú "Firewall"
