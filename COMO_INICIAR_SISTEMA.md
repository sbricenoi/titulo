# 🚀 CÓMO INICIAR EL SISTEMA COMPLETO

## ✅ Respuesta Rápida

**Ejecuta UN solo comando:**

```bash
cd /Users/sbriceno/Documents/projects/titulo && ./INICIAR_SISTEMA_FINAL.sh
```

Este script automáticamente:
- ✅ Verifica las cámaras disponibles
- ✅ Limpia procesos anteriores
- ✅ Inicia grabación de video (PID guardado)
- ✅ Inicia upload a S3 automático
- ✅ Muestra estado completo del sistema

---

## 📋 SCRIPTS DISPONIBLES

### 1. `INICIAR_SISTEMA_FINAL.sh` ⭐ **RECOMENDADO**
**Para qué:** Iniciar el sistema de grabación y upload a S3

```bash
./INICIAR_SISTEMA_FINAL.sh
```

**Verifica:**
- Conexión de cámaras RTSP
- Limpia procesos anteriores
- Inicia servicios en el orden correcto
- Muestra PIDs para control

### 2. Frontend Angular (Manual)
**Para qué:** Ver la interfaz web de análisis

```bash
cd frontend && npm start
```

- Abre automáticamente en: http://localhost:4201
- Tarda ~15 segundos en iniciar

### 3. API Backend (Manual)
**Para qué:** Si necesitas la API para el frontend

```bash
source venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

- URL: http://localhost:8000
- Docs: http://localhost:8000/docs

---

## 🎯 FLUJO COMPLETO DE INICIO

```bash
# 1. Iniciar grabación y upload (automático)
./INICIAR_SISTEMA_FINAL.sh

# 2. En otra terminal: Frontend (si quieres ver la interfaz)
cd frontend && npm start

# 3. En otra terminal: API (si el frontend la necesita)
source venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

---

## 📊 VERIFICAR QUE TODO FUNCIONA

### Ver procesos activos
```bash
ps aux | grep -E "(video_recorder|s3_uploader|ffmpeg)"
```

### Ver logs en tiempo real
```bash
# Grabación
tail -f video-recording-system/data/logs/video_recorder.log

# Upload S3
tail -f video-recording-system/data/logs/s3_uploader.log
```

### Ver videos grabándose
```bash
ls -lh video-recording-system/data/videos/recordings/
```

Deberías ver archivos `.mp4` creciendo de tamaño cada 2 minutos.

---

## 🛑 DETENER EL SISTEMA

### Opción 1: Usando el script
```bash
./stop_recorder_robusto.sh
```

### Opción 2: Usando los PIDs
```bash
# Los PIDs se muestran al iniciar
kill <PID_RECORDER> <PID_UPLOADER>
```

### Opción 3: Matar todos los procesos
```bash
pkill -9 -f "video_recorder|s3_uploader|ffmpeg"
```

---

## ⚠️ PROBLEMAS COMUNES

### "No se está grabando nada"

**Causa:** Las cámaras no responden o FFmpeg no puede conectarse

**Solución:**
1. Verifica las cámaras:
   ```bash
   nc -z -w 2 192.168.0.5 554  # Cámara 1
   nc -z -w 2 192.168.0.6 554  # Cámara 2
   nc -z -w 2 192.168.0.7 554  # Cámara 3
   ```

2. Revisa el log:
   ```bash
   tail -50 video-recording-system/data/logs/video_recorder.log
   ```

3. Busca errores tipo:
   - "Connection refused" → Cámara apagada/red
   - "Invalid credentials" → Usuario/contraseña incorrecta
   - "Connection timeout" → Firewall o red lenta

### "Los procesos mueren constantemente"

**Causa:** FFmpeg no puede mantener la conexión RTSP

**Solución:**
1. Verifica la URL RTSP en:
   ```bash
   cat video-recording-system/.env | grep RTSP
   ```

2. Prueba la URL manualmente:
   ```bash
   ffmpeg -rtsp_transport tcp -i "rtsp://admin:PASSWORD@192.168.0.X:554/..." -t 5 test.mp4
   ```

### "Frontend no carga"

**Causa:** Node/npm no compiló correctamente

**Solución:**
```bash
cd frontend
rm -rf node_modules
npm install
npm start
```

---

## 📁 UBICACIONES IMPORTANTES

```
titulo/
├── INICIAR_SISTEMA_FINAL.sh          ← Script principal ⭐
├── stop_recorder_robusto.sh          ← Detener sistema
│
├── video-recording-system/
│   ├── data/
│   │   ├── videos/
│   │   │   ├── recordings/          ← Videos grabándose
│   │   │   └── uploaded/            ← Videos ya subidos a S3
│   │   └── logs/
│   │       ├── video_recorder.log   ← Log de grabación
│   │       └── s3_uploader.log      ← Log de uploads
│   └── .env                          ← Configuración cámaras
│
├── frontend/                         ← Interfaz web Angular
└── api/                              ← Backend FastAPI
```

---

## 🎬 TIMELINE TÍPICO

```
00:00 → Ejecutar INICIAR_SISTEMA_FINAL.sh
00:05 → Sistema iniciado, FFmpeg grabando
02:00 → Primer segmento de video completo (2 min)
03:00 → Primer archivo subido a S3 (espera 1 min estabilidad)
04:00 → Segundo segmento grabándose
...   → Ciclo continuo cada 2 minutos
```

---

## ✅ CHECKLIST DE INICIO

- [ ] Cámaras encendidas y en red
- [ ] Ejecutar `./INICIAR_SISTEMA_FINAL.sh`
- [ ] Ver "✅ SISTEMA INICIADO CORRECTAMENTE"
- [ ] Ver "FFmpeg: X cámara(s) grabando"
- [ ] Esperar 2-3 minutos
- [ ] Verificar archivos en `recordings/`
- [ ] (Opcional) Iniciar frontend: `cd frontend && npm start`
- [ ] (Opcional) Abrir http://localhost:4201

---

## 💡 CONSEJOS

1. **Siempre usa el script:** No inicies los servicios manualmente, usa `INICIAR_SISTEMA_FINAL.sh`

2. **Espera 2 minutos:** Los videos se crean cada 2 minutos, ten paciencia

3. **Monitorea los logs:** Si algo falla, los logs tienen la respuesta

4. **Una cámara es suficiente:** Si solo 1 cámara funciona, el sistema igual opera correctamente

5. **El frontend es opcional:** El sistema graba y sube videos sin necesidad del frontend

---

**¡Listo! Con `./INICIAR_SISTEMA_FINAL.sh` todo debería funcionar.**
