# Arquitectura de Streaming HLS - Sistema Separado

## 📋 Resumen

Se implementó una **arquitectura completamente separada** donde el streaming de video y el análisis AI funcionan de manera independiente, evitando interferencias y sobrecarga del sistema.

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                     CÁMARA RTSP                             │
│                 rtsp://192.168.0.20:554                     │
└──────────────┬───────────────────────┬──────────────────────┘
               │                       │
               │                       │
        ┌──────▼──────┐       ┌────────▼─────────┐
        │  ANÁLISIS AI │       │  STREAMING HLS   │
        │  (main.py)   │       │ (hls_server.py)  │
        └──────┬──────┘       └────────┬─────────┘
               │                       │
               │                       │
        ┌──────▼──────────────┐  ┌─────▼──────────┐
        │  Detección          │  │  FFmpeg        │
        │  Tracking           │  │  Conversión    │
        │  Comportamientos    │  │  RTSP → HLS    │
        └─────────────────────┘  └─────┬──────────┘
                                       │
                                  ┌────▼─────────┐
                                  │  Archivos HLS │
                                  │  /tmp/hls_    │
                                  │   streams/    │
                                  └────┬──────────┘
                                       │
                                  ┌────▼─────────┐
                                  │  API FastAPI │
                                  │  StaticFiles │
                                  └────┬──────────┘
                                       │
                                  ┌────▼─────────┐
                                  │  Frontend    │
                                  │  Angular +   │
                                  │  HLS.js      │
                                  └──────────────┘
```

## 🔧 Componentes

### 1. Backend AI (Análisis) - `main.py`
- **Propósito**: Análisis de video en tiempo real
- **Conexión**: RTSP directo a la cámara
- **Funciones**:
  - Detección de hurones (YOLOv8)
  - Tracking multi-cámara (DeepSORT)
  - Clasificación de comportamientos (CNN+LSTM)
  - Almacenamiento en base de datos

### 2. Servidor HLS - `api/hls_server.py`
- **Propósito**: Streaming de video para visualización
- **Conexión**: RTSP directo a la cámara (independiente del AI)
- **Tecnología**: FFmpeg
- **Funciones**:
  - Conversión RTSP → HLS en tiempo real
  - Segmentación de video (2 segundos por segmento)
  - Buffer de 5 segmentos (10 segundos)
  - Monitoreo y reconexión automática

**Parámetros de optimización**:
```python
- Codec: H.264 (libx264)
- Preset: ultrafast (baja latencia)
- Bitrate: 2 Mbps
- Keyframe interval: 60 frames (2s @ 30fps)
- Segmento: 2 segundos
- Buffer: 5 segmentos
```

### 3. API FastAPI - `api/main.py`
- **Propósito**: Servir archivos HLS y endpoints REST
- **Endpoints nuevos**:
  - `GET /api/stream/hls/{camera_id}` - URL del stream HLS
  - `/hls/` - Directorio estático con archivos HLS
- **Eventos**:
  - `startup`: Inicializa servidor HLS
  - `shutdown`: Detiene servidor HLS

### 4. Frontend Angular
- **Cambios principales**:
  - Reemplazó `<img>` por `<video>` HTML5
  - Eliminó polling de frames
  - Implementó HLS.js para reproducción
- **Archivos modificados**:
  - `camera-grid.component.html`: Video player
  - `camera-grid.component.ts`: Lógica HLS.js
  - `api.service.ts`: Métodos HLS
  - `index.html`: CDN de HLS.js

## 📦 Flujo de Datos

### Streaming de Video
```
1. FFmpeg lee RTSP de la cámara
2. FFmpeg convierte a HLS (segmentos .ts + playlist .m3u8)
3. Archivos guardados en /tmp/hls_streams/camera_X/
4. FastAPI sirve archivos vía StaticFiles en /hls
5. Frontend solicita playlist.m3u8
6. HLS.js descarga y reproduce segmentos automáticamente
```

### Análisis AI (Paralelo e Independiente)
```
1. CameraManager lee RTSP de la cámara
2. Frames enviados a Detector (YOLOv8)
3. Detecciones enviadas a Tracker (DeepSORT)
4. Secuencias enviadas a BehaviorClassifier (CNN+LSTM)
5. Comportamientos guardados en SQLite
6. API sirve datos vía REST endpoints
```

## 🎯 Ventajas de Esta Arquitectura

1. **Separación de Responsabilidades**
   - Streaming para visualización
   - AI para análisis
   - Sin interferencia mutua

2. **Eficiencia**
   - Una sola conexión RTSP por propósito
   - Sin polling infinito del frontend
   - Buffer adaptativo en el cliente

3. **Escalabilidad**
   - Múltiples clientes pueden ver el mismo stream
   - FFmpeg maneja el broadcast eficientemente
   - HLS es el estándar de la industria

4. **Confiabilidad**
   - Reconexión automática si el stream se cae
   - Monitor de salud de streams
   - Manejo robusto de errores

5. **Compatibilidad**
   - HLS soportado nativamente en Safari (iOS/macOS)
   - HLS.js para Chrome, Firefox, Edge
   - Funciona en móviles

## 📊 Monitoreo

El servidor HLS incluye un monitor que:
- Verifica cada 10 segundos el estado de los streams
- Reinicia automáticamente streams caídos
- Registra eventos en logs

```python
def monitor_streams(self):
    """Monitorear y reiniciar streams si se caen."""
    while self.running:
        for camera_id in range(len(self.camera_urls)):
            if not self.is_stream_active(camera_id):
                logger.warning(f"Stream caído para cámara {camera_id}, reiniciando...")
                self.stop_camera_stream(camera_id)
                time.sleep(1)
                self.start_camera_stream(camera_id)
        time.sleep(10)
```

## 🔄 Inicio y Cierre

### Inicio del Sistema
1. Usuario ejecuta `uvicorn api.main:app`
2. FastAPI dispara evento `startup`
3. Se inicializa `HLSStreamServer` con las URLs de cámaras
4. FFmpeg inicia conversión RTSP → HLS para cada cámara
5. Monitor de streams comienza a vigilar
6. API queda lista para servir archivos HLS

### Cierre del Sistema
1. Usuario interrumpe con Ctrl+C
2. FastAPI dispara evento `shutdown`
3. Monitor de streams se detiene
4. Cada proceso FFmpeg recibe SIGTERM
5. Archivos temporales permanecen en /tmp (se limpian automáticamente)

## 🐛 Debugging

### Verificar que HLS está generando archivos:
```bash
ls -lh /tmp/hls_streams/camera_0/
# Debería mostrar:
# - stream.m3u8 (playlist)
# - segment_XXX.ts (segmentos de video)
```

### Ver el playlist:
```bash
cat /tmp/hls_streams/camera_0/stream.m3u8
```

### Monitorear logs del backend:
```bash
tail -f /tmp/ferret_api.log | grep -E "🎬|✅|HLS|stream"
```

### Verificar en el navegador:
1. Abrir DevTools (F12)
2. Ir a Network tab
3. Filtrar por ".m3u8" y ".ts"
4. Deberías ver descargas continuas de segmentos

## 📈 Próximas Mejoras

1. **Adaptive Bitrate Streaming (ABR)**
   - Múltiples calidades (480p, 720p, 1080p)
   - Cliente selecciona según ancho de banda

2. **WebRTC** (alternativa futura)
   - Latencia ultra-baja (<500ms)
   - Para casos de uso en tiempo real crítico

3. **Grabación de Eventos**
   - Guardar segmentos HLS cuando se detectan comportamientos importantes

4. **Multi-cámara optimizada**
   - Mosaico de 4+ cámaras
   - Grid adaptativo según número de cámaras

## 📝 Notas Importantes

- **Directorio temporal**: `/tmp/hls_streams` se limpia automáticamente en reinicio del sistema
- **Latencia**: ~6-10 segundos (2s por segmento × 3 segmentos de buffer)
- **Ancho de banda**: ~2 Mbps por cámara
- **Recursos**: FFmpeg consume ~5-10% CPU por cámara en macOS M1

## 🔗 Referencias

- [HLS Specification (RFC 8216)](https://tools.ietf.org/html/rfc8216)
- [HLS.js Documentation](https://github.com/video-dev/hls.js/)
- [FFmpeg HLS Options](https://ffmpeg.org/ffmpeg-formats.html#hls-2)

