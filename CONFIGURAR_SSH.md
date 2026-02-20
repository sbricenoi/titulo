# Configurar SSH para Windows (192.168.0.15)

Guía rápida para conectarte desde tu Mac al Windows de grabación.

## 🚀 Configuración Inicial (Una sola vez)

### 1. Generar Clave SSH en tu Mac

```bash
# Generar clave (si no tienes):
ssh-keygen -t ed25519 -C "mac_to_windows"

# Presiona Enter 3 veces (sin contraseña para facilidad)
# La clave se guarda en ~/.ssh/id_ed25519
```

### 2. Primera Conexión (con contraseña)

```bash
# Conectar por primera vez:
ssh Administrator@192.168.0.15

# Te pedirá:
# 1. Aceptar fingerprint (escribe: yes)
# 2. Contraseña de Windows
```

### 3. Copiar tu Clave Pública al Windows

```bash
# Opción A: Automática (recomendado)
ssh-copy-id Administrator@192.168.0.15

# Opción B: Manual
# En tu Mac:
cat ~/.ssh/id_ed25519.pub

# Copiar el contenido y en Windows (conectado por SSH):
mkdir C:\Users\Administrator\.ssh
echo <CONTENIDO_COPIADO> > C:\Users\Administrator\.ssh\authorized_keys
```

### 4. Configurar Alias para Conexión Rápida

```bash
# Agregar configuración SSH:
cat ssh_config_windows >> ~/.ssh/config

# O manualmente:
nano ~/.ssh/config

# Y pegar:
Host windows-grabacion
    HostName 192.168.0.15
    User Administrator
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

### 5. Hacer Ejecutables los Scripts

```bash
chmod +x conectar_windows.sh
chmod +x verificar_windows.sh
chmod +x monitorear_grabacion.sh
chmod +x ver_logs_remoto.sh
```

---

## ✅ Verificar Configuración

```bash
# Verificar que todo está bien:
./verificar_windows.sh
```

Debería mostrar:
- ✅ Windows está en línea
- ✅ SSH está disponible
- Estado de procesos
- Espacio en disco
- Etc.

---

## 🎯 Uso Diario

### Conectarte al Windows

```bash
# Opción 1: Con el script:
./conectar_windows.sh

# Opción 2: Directo con alias:
ssh windows-grabacion

# Opción 3: Directo con IP:
ssh Administrator@192.168.0.15
```

### Ver Estado del Sistema

```bash
./verificar_windows.sh
```

### Monitorear Grabación en Vivo

```bash
./monitorear_grabacion.sh
```

Actualiza cada 5 segundos:
- Procesos activos
- Últimos videos grabados
- Total de videos pendientes
- Uso de CPU/RAM

### Ver Logs en Tiempo Real

```bash
./ver_logs_remoto.sh
```

Opciones:
1. Log de grabación
2. Log de subida a S3
3. Ambos

---

## 📝 Comandos Útiles

### Ejecutar Comandos Remotos

```bash
# Ver procesos:
ssh windows-grabacion "tasklist | findstr python"

# Ver archivos en carpeta:
ssh windows-grabacion "dir C:\Users\Administrator\titulo"

# Ver logs rápido:
ssh windows-grabacion "type C:\Users\Administrator\titulo\video-recording-system\logs\recorder.log"
```

### Transferir Archivos

```bash
# Enviar archivo a Windows:
scp archivo.txt windows-grabacion:C:/Users/Administrator/titulo/

# Descargar archivo desde Windows:
scp windows-grabacion:C:/Users/Administrator/titulo/video-recording-system/.env ./

# Enviar carpeta completa:
scp -r ./carpeta windows-grabacion:C:/Users/Administrator/titulo/
```

### Iniciar/Detener Sistema

```bash
# Detener todos los procesos Python:
ssh windows-grabacion "taskkill /F /IM python.exe"

# Iniciar grabación:
ssh windows-grabacion "cd C:\Users\Administrator\titulo\video-recording-system && start /B python services\video_recorder.py"

# Iniciar uploader:
ssh windows-grabacion "cd C:\Users\Administrator\titulo\video-recording-system && start /B python services\s3_uploader.py"
```

---

## 🆘 Troubleshooting

### No puedo conectar

```bash
# 1. Verificar que Windows está encendido:
ping 192.168.0.15

# 2. Verificar que SSH está corriendo en Windows:
nc -zv 192.168.0.15 22

# 3. Si el puerto no responde, en Windows (PowerShell como Admin):
Start-Service sshd
```

### "Permission denied"

```bash
# Verificar permisos de tu clave:
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub

# Verificar que la clave pública está en Windows:
ssh Administrator@192.168.0.15 "type C:\Users\Administrator\.ssh\authorized_keys"
```

### Conexión lenta o se cae

```bash
# Editar ~/.ssh/config y agregar:
Host windows-grabacion
    # ... resto de config ...
    Compression yes
    ServerAliveInterval 30
    ServerAliveCountMax 10
```

---

## 📋 Scripts Disponibles

| Script | Descripción |
|--------|-------------|
| `conectar_windows.sh` | Conexión SSH interactiva |
| `verificar_windows.sh` | Verificar estado completo del sistema |
| `monitorear_grabacion.sh` | Monitor en tiempo real (actualiza cada 5s) |
| `ver_logs_remoto.sh` | Ver logs en tiempo real |
| `ssh_config_windows` | Configuración SSH para copiar a ~/.ssh/config |

---

## ✅ Checklist de Configuración

- [ ] Generar clave SSH en Mac
- [ ] Primera conexión con contraseña
- [ ] Copiar clave pública al Windows
- [ ] Configurar alias en ~/.ssh/config
- [ ] Hacer ejecutables los scripts
- [ ] Probar `./verificar_windows.sh`
- [ ] Probar conexión sin contraseña: `ssh windows-grabacion`

¡Listo! Ya puedes administrar el Windows remotamente desde tu Mac.
