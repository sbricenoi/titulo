# 🖥️ Información del Servidor Lightsail

## ✅ Conexión Establecida

**Fecha de configuración:** 2026-01-24  
**Estado:** ✅ Operativo y listo para despliegue

---

## 📡 Credenciales de Acceso

### SSH
```bash
IP: 3.147.46.191
Usuario: ubuntu
Key: /Users/sbriceno/Documents/projects/titulo/ferret-recorder-key.pem
Permisos del key: 400 (configurado)
```

### Comando de Conexión
```bash
ssh -i /Users/sbriceno/Documents/projects/titulo/ferret-recorder-key.pem ubuntu@3.147.46.191
```

### Alias Recomendado (agregar a ~/.ssh/config)
```bash
Host ferret-recorder
    HostName 3.147.46.191
    User ubuntu
    IdentityFile /Users/sbriceno/Documents/projects/titulo/ferret-recorder-key.pem
    ServerAliveInterval 60
```

Después de configurar, conectar simplemente con:
```bash
ssh ferret-recorder
```

---

## 🖥️ Especificaciones del Servidor

| Componente | Especificación | Estado |
|------------|---------------|--------|
| **Proveedor** | AWS Lightsail | ✅ |
| **Región** | us-east-2 (Ohio) | ✅ |
| **IP Pública** | 3.147.46.191 | ✅ |
| **Sistema Operativo** | Ubuntu 22.04 LTS | ✅ |
| **Kernel** | 6.8.0-1044-aws | ✅ |
| **Arquitectura** | x86_64 | ✅ |
| **vCPU** | 1 core | ✅ |
| **RAM** | 914 MB (~1 GB) | ⚠️ Ver nota |
| **Disco** | 40 GB SSD | ✅ |
| **Usado** | 2.7 GB (7%) | ✅ |
| **Disponible** | 36 GB | ✅ |

### ⚠️ Nota sobre la RAM

El servidor tiene **~1 GB de RAM**, lo que corresponde al plan de **$5/mes**, no al plan de $10/mes (2 GB) que recomendamos.

**Implicaciones:**
- ✅ **Funcionará** para 2-3 cámaras sin problema
- ⚠️ **Puede ser justo** para 4 cámaras simultáneas
- ⚠️ **Memoria disponible actual:** 541 MB

**Recomendación:**
1. **Probar primero** con 2 cámaras
2. **Monitorear uso** de RAM con `htop`
3. **Upgrade a $10/mes** si es necesario más adelante

Para actualizar el plan:
```
Lightsail Console → Instancia → Manage → Upgrade plan
```

---

## 🔧 Software Instalado

### ✅ Verificado y Funcionando

| Software | Versión | Propósito |
|----------|---------|-----------|
| **FFmpeg** | 4.4.2 | Grabación de video |
| **Python** | 3.10.12 | Runtime del sistema |
| **pip** | 22.0.2 | Gestor de paquetes Python |
| **Git** | 2.34.1 | Control de versiones |
| **htop** | 3.0.5 | Monitor de recursos |

### Comandos de Verificación
```bash
ffmpeg -version    # FFmpeg 4.4.2
python3 --version  # Python 3.10.12
pip3 --version     # pip 22.0.2
git --version      # git 2.34.1
```

---

## 📊 Estado Actual del Sistema

### Recursos
```
CPU: 1 core x86_64
RAM: 914 MB total
     - Usado: 201 MB (22%)
     - Libre: 159 MB
     - Buff/Cache: 553 MB
     - Disponible: 541 MB

Disco: 40 GB total
     - Usado: 2.7 GB (7%)
     - Disponible: 36 GB
     - Punto de montaje: /

Uptime: ~15 minutos (recién creado)
Load Average: 0.00, 0.01, 0.00
```

### Proceso de Creación
```
1. ✅ Instancia Lightsail creada
2. ✅ SSH key configurado (permisos 400)
3. ✅ Conexión SSH verificada
4. ✅ Sistema actualizado (apt update)
5. ✅ Software instalado (FFmpeg, Python, Git)
6. ✅ Verificación completada
```

---

## 🚀 Próximos Pasos

### 1. Clonar el Repositorio
```bash
# Conectar al servidor
ssh -i /Users/sbriceno/Documents/projects/titulo/ferret-recorder-key.pem ubuntu@3.147.46.191

# Clonar proyecto (cuando esté en GitHub)
git clone https://github.com/TU-USUARIO/video-recording-system.git
cd video-recording-system
```

### 2. Configurar el Proyecto
```bash
# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# Configurar .env
cp env.example .env
nano .env
# Agregar credenciales AWS y URLs de cámaras
```

### 3. Verificar Configuración
```bash
python services/recorder_config.py
# Debe mostrar configuración sin errores
```

### 4. Instalar Servicios
```bash
cd services/systemd
sudo ./install-services.sh
```

### 5. Iniciar Sistema
```bash
sudo systemctl start video-recorder
sudo systemctl start s3-uploader

# Ver logs
sudo journalctl -u video-recorder -f
```

---

## 🔐 Seguridad

### Firewall Configurado en Lightsail
```
SSH (22): Abierto a todas las IPs
HTTP (80): Cerrado
HTTPS (443): Cerrado
```

**Recomendación:** Restringir SSH solo a tu IP:
```
Lightsail Console → Networking → IPv4 Firewall
Edit SSH rule → Restrict to IP address → [Tu IP]
```

### Archivo SSH Key
```bash
Ubicación: /Users/sbriceno/Documents/projects/titulo/ferret-recorder-key.pem
Permisos: 400 (solo lectura para ti)
Estado: ✅ Configurado correctamente
```

**⚠️ IMPORTANTE:**
- NO compartir el archivo .pem
- NO subir el .pem a GitHub
- Hacer backup en lugar seguro

---

## 📊 Monitoreo del Servidor

### Ver Recursos en Tiempo Real
```bash
# Conectar al servidor
ssh -i /Users/sbriceno/Documents/projects/titulo/ferret-recorder-key.pem ubuntu@3.147.46.191

# Monitorear con htop
htop
# Presionar F10 o 'q' para salir

# Ver uso de disco
df -h

# Ver uso de RAM
free -h

# Ver procesos
ps aux | grep ffmpeg
```

### Script de Monitoreo (después de clonar repo)
```bash
./scripts/monitor.sh
```

### Métricas en Lightsail Console
```
https://lightsail.aws.amazon.com/
→ Instancia → Metrics tab

Métricas disponibles:
- CPU utilization
- Network in/out
- Disk read/write
- Status check failures
```

---

## 🐛 Troubleshooting

### No puedo conectar vía SSH
```bash
# Verificar permisos del key
ls -lah /Users/sbriceno/Documents/projects/titulo/ferret-recorder-key.pem
# Debe mostrar: -r-------- (400)

# Si no, corregir:
chmod 400 /Users/sbriceno/Documents/projects/titulo/ferret-recorder-key.pem

# Verificar que el servidor está corriendo
# Lightsail Console → Instancia → debe estar "Running"

# Intentar conexión con verbose
ssh -v -i /Users/sbriceno/Documents/projects/titulo/ferret-recorder-key.pem ubuntu@3.147.46.191
```

### Servidor lento o sin respuesta
```bash
# Conectar y verificar recursos
htop

# Si RAM está al 100%:
# - Upgrade a plan $10/mes (2 GB RAM)
# - Reducir número de cámaras

# Si CPU está al 100%:
# - Verificar que VIDEO_CODEC=copy (no recodifica)
# - Reducir número de cámaras
```

### Disco lleno
```bash
# Ver uso de disco
df -h

# Limpiar archivos uploaded
rm ~/video-recording-system/data/videos/uploaded/*.mp4

# Limpiar logs antiguos
sudo journalctl --vacuum-time=7d

# Considerar agregar disco adicional
# Lightsail Console → Storage → Create disk
```

---

## 💰 Costos

### Plan Actual: $5/mes
```
1 vCPU
1 GB RAM
40 GB SSD
2 TB transferencia/mes
```

### Plan Recomendado: $10/mes
```
1 vCPU
2 GB RAM
60 GB SSD
3 TB transferencia/mes
```

**Diferencia:** +$5/mes (+100% RAM, +50% disco, +50% transferencia)

### Cómo Actualizar
```
1. Lightsail Console
2. Click en instancia
3. Manage → Upgrade plan
4. Seleccionar $10/mes
5. Upgrade (sin downtime)
```

---

## 📝 Notas Importantes

### ✅ Completado
- [x] Servidor creado y configurado
- [x] SSH key configurado
- [x] Conexión verificada
- [x] FFmpeg instalado
- [x] Python 3.10 instalado
- [x] Git instalado
- [x] Sistema actualizado

### ⏳ Pendiente
- [ ] Subir código a GitHub
- [ ] Clonar repositorio en servidor
- [ ] Configurar .env con credenciales
- [ ] Instalar dependencias Python
- [ ] Configurar servicios systemd
- [ ] Iniciar sistema
- [ ] Verificar grabación

### 📋 Checklist de Despliegue

Seguir la guía: `INSTALL_QUICK.md`

Tiempo estimado: 1-2 horas

---

## 🔗 Enlaces Útiles

- **Lightsail Console:** https://lightsail.aws.amazon.com/
- **Documentación:** Ver `README.md`
- **Instalación Rápida:** Ver `INSTALL_QUICK.md`
- **Configuración Lightsail:** Ver `LIGHTSAIL_SETUP.md`
- **Setup Git:** Ver `GIT_SETUP.md`

---

**Fecha de creación:** 2026-01-24  
**IP del servidor:** 3.147.46.191  
**Plan actual:** $5/mes (1 GB RAM)  
**Plan recomendado:** $10/mes (2 GB RAM)  
**Estado:** ✅ Listo para despliegue del código

---

## 📞 Quick Commands

```bash
# Conectar
ssh -i /Users/sbriceno/Documents/projects/titulo/ferret-recorder-key.pem ubuntu@3.147.46.191

# Ver recursos
htop

# Ver logs del sistema
sudo journalctl -f

# Reiniciar servidor
sudo reboot

# Actualizar sistema
sudo apt update && sudo apt upgrade -y
```

**¡El servidor está listo! 🎉**
