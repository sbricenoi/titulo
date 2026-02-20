# Acceso Remoto al Equipo Windows

Guía para conectarte desde tu Mac al equipo Windows que ejecutará el sistema de grabación.

## 🎯 Configuración Recomendada: SSH (OpenSSH)

### Ventajas
- ✅ Nativo en Windows 10/11 (ya incluido)
- ✅ Terminal completo desde tu Mac
- ✅ Transferencia de archivos (SCP/SFTP)
- ✅ Seguro y encriptado
- ✅ Bajo consumo de recursos
- ✅ Funciona en misma red local

---

## 📋 PASO 1: Configurar OpenSSH en Windows

### A) Habilitar OpenSSH Server en Windows

```powershell
# Abrir PowerShell como Administrador y ejecutar:

# Instalar OpenSSH Server
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0

# Iniciar el servicio
Start-Service sshd

# Configurar inicio automático
Set-Service -Name sshd -StartupType 'Automatic'

# Verificar que está corriendo
Get-Service sshd
```

### B) Configurar Firewall

```powershell
# Abrir PowerShell como Administrador:

# Permitir SSH en el firewall (puerto 22)
New-NetFirewallRule -Name sshd -DisplayName 'OpenSSH Server (sshd)' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22

# Verificar la regla
Get-NetFirewallRule -Name sshd
```

### C) Obtener IP del Windows

```powershell
# Ver la IP del equipo Windows:
ipconfig | findstr IPv4
```

**Ejemplo de salida:**
```
   IPv4 Address. . . . . . . . . . . : 192.168.0.15
```

Anota esta IP, la necesitarás para conectarte desde tu Mac.

---

## 📋 PASO 2: Conectarte desde tu Mac

### A) Conexión SSH básica

```bash
# Desde tu Mac (Terminal):
ssh <USUARIO_WINDOWS>@<IP_WINDOWS>

# Ejemplo:
ssh Administrator@192.168.0.15
# o
ssh sbriceno@192.168.0.15
```

**Primera conexión:**
- Te pedirá aceptar la huella digital del servidor (escribe `yes`)
- Te pedirá la contraseña de Windows

### B) Simplificar la conexión (sin escribir contraseña cada vez)

```bash
# 1. En tu Mac, generar clave SSH (si no tienes):
ssh-keygen -t ed25519 -C "mac_to_windows"
# Presiona Enter 3 veces (sin contraseña)

# 2. Copiar la clave al Windows:
ssh-copy-id <USUARIO_WINDOWS>@<IP_WINDOWS>

# Ejemplo:
ssh-copy-id Administrator@192.168.0.15
```

**Ahora puedes conectarte sin contraseña:**
```bash
ssh Administrator@192.168.0.15
```

### C) Crear alias para conectarte más rápido

Edita `~/.ssh/config` en tu Mac:

```bash
# Abrir editor:
nano ~/.ssh/config

# Agregar esta configuración:
Host windows-grabacion
    HostName 192.168.0.15
    User Administrator
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

**Ahora puedes conectarte simplemente con:**
```bash
ssh windows-grabacion
```

---

## 🚀 Operaciones Comunes

### 1. Ejecutar Comandos Remotos

```bash
# Ejecutar comando sin entrar a la sesión:
ssh windows-grabacion "cd C:\Users\Administrator\titulo && dir"

# Ver procesos del sistema de grabación:
ssh windows-grabacion "tasklist | findstr python"

# Ver logs:
ssh windows-grabacion "type C:\Users\Administrator\titulo\video-recording-system\logs\recorder.log"
```

### 2. Transferir Archivos (SCP)

```bash
# Enviar archivo desde Mac a Windows:
scp archivo.txt windows-grabacion:C:/Users/Administrator/titulo/

# Descargar archivo desde Windows a Mac:
scp windows-grabacion:C:/Users/Administrator/titulo/video-recording-system/.env ./

# Enviar directorio completo:
scp -r ./carpeta windows-grabacion:C:/Users/Administrator/titulo/
```

### 3. Iniciar/Detener el Sistema de Grabación

```bash
# Iniciar grabación (desde tu Mac):
ssh windows-grabacion "cd C:\Users\Administrator\titulo\video-recording-system && python services\video_recorder.py"

# Ver si está corriendo:
ssh windows-grabacion "tasklist | findstr python"

# Detener proceso (obtener PID primero):
ssh windows-grabacion "taskkill /F /PID <PID>"
```

### 4. Monitorear en Tiempo Real

```bash
# Ver logs en vivo:
ssh windows-grabacion "powershell Get-Content C:\Users\Administrator\titulo\video-recording-system\logs\recorder.log -Wait"

# Ver uso de CPU/RAM:
ssh windows-grabacion "wmic cpu get loadpercentage && wmic OS get FreePhysicalMemory"
```

---

## 🔧 Automatización con Scripts

### Script para verificar estado del sistema remoto

Crea `verificar_windows.sh` en tu Mac:

```bash
#!/bin/bash

# verificar_windows.sh
# Verifica el estado del sistema de grabación en Windows

WINDOWS_HOST="windows-grabacion"
PROJECT_PATH="C:\Users\Administrator\titulo"

echo "======================================"
echo "🔍 VERIFICACIÓN SISTEMA WINDOWS"
echo "======================================"
echo ""

echo "📊 1. ESTADO DE PROCESOS:"
ssh $WINDOWS_HOST "tasklist | findstr python"
echo ""

echo "💾 2. ESPACIO EN DISCO:"
ssh $WINDOWS_HOST "wmic logicaldisk get caption,freespace,size /format:list | findstr :"
echo ""

echo "📹 3. ÚLTIMOS VIDEOS GRABADOS:"
ssh $WINDOWS_HOST "dir $PROJECT_PATH\video-recording-system\data\videos\recordings /O-D /B | findstr .mp4"
echo ""

echo "📁 4. VIDEOS PENDIENTES DE SUBIR:"
ssh $WINDOWS_HOST "dir $PROJECT_PATH\video-recording-system\data\videos\recordings /B | find /C \".mp4\""
echo ""

echo "🌐 5. CONEXIÓN A INTERNET:"
ssh $WINDOWS_HOST "ping -n 2 8.8.8.8"
echo ""

echo "✅ Verificación completada"
```

**Usar:**
```bash
chmod +x verificar_windows.sh
./verificar_windows.sh
```

### Script para reiniciar el sistema

Crea `reiniciar_grabacion_remoto.sh` en tu Mac:

```bash
#!/bin/bash

# reiniciar_grabacion_remoto.sh
# Reinicia el sistema de grabación remotamente

WINDOWS_HOST="windows-grabacion"
PROJECT_PATH="C:\Users\Administrator\titulo\video-recording-system"

echo "🛑 Deteniendo procesos..."
ssh $WINDOWS_HOST "taskkill /F /IM python.exe"

sleep 3

echo "🚀 Iniciando sistema de grabación..."
ssh $WINDOWS_HOST "cd $PROJECT_PATH && start /B python services\video_recorder.py"
ssh $WINDOWS_HOST "cd $PROJECT_PATH && start /B python services\s3_uploader.py"

sleep 2

echo "✅ Sistema reiniciado"
echo ""
echo "📊 Verificando procesos:"
ssh $WINDOWS_HOST "tasklist | findstr python"
```

**Usar:**
```bash
chmod +x reiniciar_grabacion_remoto.sh
./reiniciar_grabacion_remoto.sh
```

---

## 🔐 Seguridad Adicional

### 1. Cambiar Puerto SSH (Opcional pero Recomendado)

En Windows, edita `C:\ProgramData\ssh\sshd_config`:

```powershell
# Abrir como Administrador:
notepad C:\ProgramData\ssh\sshd_config

# Cambiar línea:
#Port 22
# Por:
Port 2222

# Guardar y reiniciar servicio:
Restart-Service sshd
```

**Actualizar firewall:**
```powershell
Remove-NetFirewallRule -Name sshd
New-NetFirewallRule -Name sshd -DisplayName 'OpenSSH Server (sshd)' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 2222
```

**Conectar desde Mac con nuevo puerto:**
```bash
ssh -p 2222 windows-grabacion
# O actualizar ~/.ssh/config agregando: Port 2222
```

### 2. Deshabilitar Autenticación por Contraseña (Solo Clave)

En `C:\ProgramData\ssh\sshd_config`:

```
PasswordAuthentication no
PubkeyAuthentication yes
```

Reiniciar servicio:
```powershell
Restart-Service sshd
```

---

## 🔄 ALTERNATIVA: RDP (Escritorio Remoto)

Si eventualmente necesitas ver la pantalla completa:

### En Windows:

```powershell
# Habilitar RDP:
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name "fDenyTSConnections" -Value 0

# Habilitar en firewall:
Enable-NetFirewallRule -DisplayGroup "Remote Desktop"
```

### Desde tu Mac:

1. Descargar "Microsoft Remote Desktop" desde App Store
2. Agregar conexión:
   - PC name: `192.168.0.15`
   - User account: `Administrator`

---

## 🆘 Troubleshooting

### No puedo conectar por SSH

```bash
# 1. Verificar que el servicio está corriendo en Windows:
ssh windows-grabacion "Get-Service sshd"

# 2. Verificar firewall en Windows:
ssh windows-grabacion "Get-NetFirewallRule -Name sshd"

# 3. Probar conexión básica:
ping 192.168.0.15
telnet 192.168.0.15 22

# 4. Ver logs de SSH en Windows:
ssh windows-grabacion "type C:\ProgramData\ssh\logs\sshd.log"
```

### Conexión se cae constantemente

Edita `~/.ssh/config` en tu Mac:

```
Host windows-grabacion
    # ... configuración existente ...
    ServerAliveInterval 30
    ServerAliveCountMax 5
    TCPKeepAlive yes
```

### "Permission denied" al conectar

```bash
# Verificar permisos de tu clave privada:
chmod 600 ~/.ssh/id_ed25519

# Verificar que la clave pública está en Windows:
ssh windows-grabacion "type C:\Users\Administrator\.ssh\authorized_keys"
```

---

## 📝 Resumen de Comandos Útiles

```bash
# Conectar:
ssh windows-grabacion

# Ejecutar comando:
ssh windows-grabacion "COMANDO"

# Transferir archivo:
scp archivo.txt windows-grabacion:C:/destino/

# Ver logs en vivo:
ssh windows-grabacion "powershell Get-Content ARCHIVO.log -Wait"

# Ver procesos Python:
ssh windows-grabacion "tasklist | findstr python"

# Reiniciar servicio:
ssh windows-grabacion "Restart-Service NOMBRE_SERVICIO"
```

---

## ✅ Checklist de Configuración

### En Windows:
- [ ] Instalar OpenSSH Server
- [ ] Iniciar servicio sshd
- [ ] Configurar inicio automático
- [ ] Abrir puerto en firewall
- [ ] Anotar IP del equipo
- [ ] Configurar clave pública SSH

### En Mac:
- [ ] Generar clave SSH
- [ ] Copiar clave al Windows
- [ ] Configurar alias en ~/.ssh/config
- [ ] Probar conexión
- [ ] Crear scripts de automatización

---

## 🎯 Próximos Pasos

1. **Habilitar SSH en Windows** (PASO 1)
2. **Probar conexión desde Mac** (PASO 2)
3. **Configurar alias** para conexión rápida
4. **Crear scripts** de monitoreo y administración
5. **(Opcional)** Habilitar RDP como backup

¿Listo para empezar con la configuración?
