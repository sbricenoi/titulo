# 💾 Configuración de Ahorro de Espacio

## ✅ Eliminación Automática Configurada

He modificado el sistema para que **elimine videos inmediatamente** después de subirlos exitosamente a S3.

---

## 🔧 Cómo Funciona

### Antes:
```
Video grabado → Sube a S3 → Mueve a uploaded/ → Espera 24h → Elimina
```

### Ahora (por defecto):
```
Video grabado → Sube a S3 → Verifica integridad → ✅ ELIMINA INMEDIATAMENTE
```

---

## ⚙️ Configuración en .env

### Para Eliminar Inmediatamente (Recomendado)

```bash
# En .env
DELETE_IMMEDIATELY_AFTER_UPLOAD=true
```

**Ventajas:**
- ✅ Ahorra espacio en disco
- ✅ Solo videos en proceso ocupan espacio
- ✅ Videos seguros en S3
- ✅ Menos mantenimiento

**Espacio usado:**
- Solo videos pendientes de subir (~1-2 GB máximo)

### Para Mantener Backup Local

```bash
# En .env
DELETE_IMMEDIATELY_AFTER_UPLOAD=false
LOCAL_RETENTION_HOURS=24
```

**Ventajas:**
- ✅ Backup local por 24 horas
- ✅ Redundancia adicional

**Espacio usado:**
- ~4 GB por cámara × 3 = ~12 GB

---

## 📊 Estimación de Espacio en Disco

### Con DELETE_IMMEDIATELY_AFTER_UPLOAD=true (Recomendado)

| Componente | Espacio Usado |
|------------|---------------|
| Videos en grabación | ~300 MB (en proceso) |
| Videos pendientes de upload | ~300-600 MB |
| Frames para clasificación | ~500 MB - 2 GB |
| Base de datos | < 100 MB |
| Logs | ~100 MB |
| **TOTAL** | **~2-3 GB** |

### Con DELETE_IMMEDIATELY_AFTER_UPLOAD=false

| Componente | Espacio Usado |
|------------|---------------|
| Videos últimas 24h | ~12 GB (3 cámaras) |
| Frames | ~500 MB - 2 GB |
| Base de datos | < 100 MB |
| Logs | ~100 MB |
| **TOTAL** | **~15-20 GB** |

---

## 🔄 Flujo Completo de Video

```
1. 📹 FFmpeg graba segmento (10 min)
   ↓
2. 📁 Guarda en recordings/
   Archivo: camera_1_2026-02-18_12-00-00.mp4 (~100 MB)
   ↓
3. 🔍 S3 Uploader detecta archivo nuevo
   ↓
4. ⏳ Espera 60 segundos (verificar que está completo)
   ↓
5. ☁️ Sube a S3
   Ubicación: s3://ferret-recordings/2026/02/18/camera_1/
   ↓
6. ✅ Verifica integridad (compara tamaños)
   ↓
7. 🗑️ ELIMINA archivo local inmediatamente
   (liberando ~100 MB)
   ↓
8. 📊 Video disponible solo en S3
```

**Tiempo total:** ~2-3 minutos después de completar grabación

---

## 🔐 Seguridad de los Datos

### Videos en S3:
- ✅ Encriptación AES-256
- ✅ Durabilidad: 99.999999999%
- ✅ Disponibilidad: 99.99%
- ✅ Backup automático de AWS

### Si se pierde conexión:
- ⚠️ Videos quedan en `recordings/`
- ✅ Se subirán cuando vuelva conexión
- ✅ No se eliminan hasta subir exitosamente

---

## 🧪 Pruebas de Verificación

### Verificar que elimina correctamente:

```bash
# 1. Ver videos en grabación
ls -lh video-recording-system/data/videos/recordings/

# 2. Esperar ~2-3 minutos después de que se complete

# 3. Verificar que desapareció
ls -lh video-recording-system/data/videos/recordings/

# 4. Verificar que está en S3
aws s3 ls s3://ferret-recordings/ --recursive | tail -5
```

### Ver logs de eliminación:

```bash
tail -f logs/uploader.log | grep "Eliminado localmente"
```

Deberías ver líneas como:
```
✓ Eliminado localmente (98.5 MB liberados)
✅ Procesado y eliminado: camera_1_2026-02-18_12-00-00.mp4
```

---

## 🛠️ Cambiar Configuración

### En Windows:

```powershell
# Editar .env
cd C:\titulo\video-recording-system
notepad .env

# Cambiar línea a:
DELETE_IMMEDIATELY_AFTER_UPLOAD=true

# Reiniciar sistema
C:\titulo\DETENER_SISTEMA_WINDOWS.bat
C:\titulo\INICIAR_SISTEMA_WINDOWS.bat
```

### En Mac/Linux:

```bash
# Editar .env
nano video-recording-system/.env

# Cambiar línea a:
DELETE_IMMEDIATELY_AFTER_UPLOAD=true

# Reiniciar
pkill -f s3_uploader
python video-recording-system/services/s3_uploader.py &
```

---

## ⚠️ Consideraciones

### ✅ Ventajas de Eliminar Inmediatamente:
- Ahorra mucho espacio en disco
- Sistema puede funcionar con menos almacenamiento
- Más económico (discos más pequeños)
- Menos mantenimiento

### ⚠️ Desventajas:
- Sin backup local después de subir
- Si S3 falla, no hay redundancia
- Necesitas conexión estable a internet

### 🎯 Recomendación:

**Para equipos con poco espacio (Windows dedicado):** ✅ `DELETE_IMMEDIATELY_AFTER_UPLOAD=true`

**Para servidores con mucho espacio:** `DELETE_IMMEDIATELY_AFTER_UPLOAD=false`

---

## 📝 Archivos Actualizados

- ✅ `video-recording-system/services/s3_uploader.py` - Lógica de eliminación
- ✅ `video-recording-system/services/recorder_config.py` - Variable de configuración
- ✅ `video-recording-system/env.example` - Documentación
- ✅ `deploy/lightsail-env.example` - Template para cloud

---

**La configuración está lista. Por defecto eliminará inmediatamente después de subir a S3.**
