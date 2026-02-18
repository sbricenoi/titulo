# 📹 Mantenedor de Cámaras - Sistema de Monitoreo

## 📋 Resumen

El **Mantenedor de Cámaras** permite gestionar dinámicamente las cámaras del sistema de monitoreo, sin necesidad de modificar código o reiniciar el servicio completo.

---

## 🏗️ Arquitectura

### Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (Angular)                       │
│  - Componente de gestión de cámaras (pendiente desarrollo)  │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP REST API
┌──────────────────────▼──────────────────────────────────────┐
│               BACKEND (FastAPI)                              │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ api/cameras_endpoints.py                             │  │
│  │ - GET    /api/cameras      (Listar)                  │  │
│  │ - GET    /api/cameras/{id} (Obtener)                 │  │
│  │ - POST   /api/cameras      (Crear)                   │  │
│  │ - PUT    /api/cameras/{id} (Actualizar)              │  │
│  │ - DELETE /api/cameras/{id} (Eliminar)                │  │
│  │ - POST   /api/cameras/{id}/start (Iniciar stream)    │  │
│  │ - POST   /api/cameras/{id}/stop  (Detener stream)    │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                      │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │ utils/camera_manager.py                              │  │
│  │ - Modelo CameraConfig                                │  │
│  │ - Clase CameraDatabase                               │  │
│  │ - CRUD en SQLite (cameras.db)                        │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                      │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │ api/hls_server.py                                    │  │
│  │ - Clase HLSStreamServer                              │  │
│  │ - Gestión dinámica de streams FFmpeg                 │  │
│  │ - start_camera_stream_async()                        │  │
│  │ - stop_camera_stream_async()                         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 💾 Modelo de Datos

### Tabla `cameras` (SQLite)

```sql
CREATE TABLE cameras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    rtsp_url TEXT NOT NULL UNIQUE,
    description TEXT DEFAULT '',
    location TEXT DEFAULT '',
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Ejemplo de Registro

```json
{
  "id": 1,
  "name": "Cámara Hurón 1",
  "rtsp_url": "rtsp://admin:***@192.168.0.20:554/Preview_01_main",
  "description": "Cámara principal del área de juego",
  "location": "Sala principal",
  "is_active": true,
  "created_at": "2026-01-10T10:00:00",
  "updated_at": "2026-01-10T10:30:00",
  "stream_status": "running"
}
```

---

## 🔌 API Endpoints

### 1. Listar Cámaras

**GET** `/api/cameras?only_active=false`

**Respuesta:**

```json
{
  "trace_id": "list-cameras",
  "code": 200,
  "message": "2 cámara(s) encontrada(s)",
  "data": [
    {
      "id": 1,
      "name": "Cámara Hurón 1",
      "rtsp_url": "rtsp://***@192.168.0.20:554/Preview_01_main",
      "description": "Cámara principal",
      "location": "Sala 1",
      "is_active": true,
      "created_at": "2026-01-10T10:00:00",
      "stream_status": "running"
    }
  ]
}
```

---

### 2. Obtener Cámara por ID

**GET** `/api/cameras/1`

**Respuesta:** Igual que arriba pero con un solo registro.

---

### 3. Crear Nueva Cámara

**POST** `/api/cameras`

**Body:**

```json
{
  "name": "Cámara Sala 2",
  "rtsp_url": "rtsp://admin:password@192.168.0.21:554/stream1",
  "description": "Segunda cámara",
  "location": "Sala 2",
  "is_active": true
}
```

**Respuesta:** `201 Created`

```json
{
  "trace_id": "create-camera-2",
  "code": 201,
  "message": "Cámara 'Cámara Sala 2' creada exitosamente",
  "data": { ... }
}
```

**Comportamiento:**
- Se guarda en la BD
- Si `is_active = true`, se inicia automáticamente el stream HLS
- El stream estará disponible en `/hls/camera_{id}/stream.m3u8`

---

### 4. Actualizar Cámara

**PUT** `/api/cameras/1`

**Body:**

```json
{
  "name": "Cámara Principal Actualizada",
  "description": "Nueva descripción"
}
```

**Comportamiento:**
- Solo los campos presentes se actualizan
- Si cambió `rtsp_url` o `is_active`, se reinicia el stream

---

### 5. Eliminar Cámara

**DELETE** `/api/cameras/1?hard_delete=false`

**Parámetros:**
- `hard_delete=false` (default): Soft delete (marca `is_active = false`)
- `hard_delete=true`: Eliminación permanente de BD

**Comportamiento:**
- Se detiene el stream HLS
- Se limpia el directorio `/tmp/hls_streams/camera_{id}/`

---

### 6. Iniciar Stream Manualmente

**POST** `/api/cameras/1/start`

**Respuesta:**

```json
{
  "trace_id": "start-stream-1",
  "code": 200,
  "message": "Stream iniciado para cámara 1",
  "data": {
    "camera_id": 1,
    "status": "running"
  }
}
```

---

### 7. Detener Stream Manualmente

**POST** `/api/cameras/1/stop`

**Respuesta:**

```json
{
  "trace_id": "stop-stream-1",
  "code": 200,
  "message": "Stream detenido para cámara 1",
  "data": {
    "camera_id": 1,
    "status": "stopped"
  }
}
```

---

## 🔄 Flujo de Operación

### Agregar Nueva Cámara

```mermaid
sequenceDiagram
    participant U as Usuario/Frontend
    participant API as FastAPI
    participant DB as SQLite
    participant HLS as HLS Server
    
    U->>API: POST /api/cameras
    API->>DB: INSERT camera
    DB-->>API: camera_id
    
    alt is_active = true
        API->>HLS: start_camera_stream_async(id, url)
        HLS->>HLS: Iniciar proceso FFmpeg
        HLS-->>API: Stream iniciado
    end
    
    API-->>U: 201 Created
```

### Actualizar Cámara (cambio de URL)

```mermaid
sequenceDiagram
    participant U as Usuario/Frontend
    participant API as FastAPI
    participant DB as SQLite
    participant HLS as HLS Server
    
    U->>API: PUT /api/cameras/1
    API->>DB: UPDATE camera
    
    API->>HLS: stop_camera_stream(1)
    HLS->>HLS: Terminar FFmpeg
    
    API->>HLS: start_camera_stream_async(1, new_url)
    HLS->>HLS: Nuevo proceso FFmpeg
    HLS-->>API: Stream reiniciado
    
    API-->>U: 200 OK
```

---

## 🚀 Migración desde Configuración Hardcodeada

En el `startup_event` de `api/main.py`, el sistema:

1. **Verifica si hay cámaras en la BD**
2. **Si no hay**, importa desde `config.py`:
   ```python
   for url, name in zip(config.CAMERA_URLS, config.CAMERA_NAMES):
       camera_db.add_camera(name=name, rtsp_url=url, ...)
   ```
3. **Lee cámaras activas desde BD** en lugar de `config.py`
4. **Inicializa HLS server** con las URLs activas

**Ventaja:** Migración transparente, sin romper configuración existente.

---

## 🧪 Pruebas con cURL

### Listar cámaras

```bash
curl http://localhost:8000/api/cameras
```

### Agregar cámara

```bash
curl -X POST http://localhost:8000/api/cameras \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Cámara Test",
    "rtsp_url": "rtsp://admin:pass@192.168.0.22:554/stream",
    "description": "Prueba",
    "location": "Laboratorio",
    "is_active": true
  }'
```

### Actualizar cámara

```bash
curl -X PUT http://localhost:8000/api/cameras/1 \
  -H "Content-Type: application/json" \
  -d '{"description": "Actualizada desde API"}'
```

### Eliminar cámara (soft delete)

```bash
curl -X DELETE http://localhost:8000/api/cameras/1
```

### Verificar stream HLS

```bash
curl http://localhost:8000/hls/camera_1/stream.m3u8
```

---

## 📝 Notas Importantes

1. **IDs de Cámaras**: 
   - Los IDs se asignan secuencialmente desde la BD
   - Si se elimina una cámara (soft delete), el ID no se reutiliza
   - El sistema mapea `camera_id` (BD) con el índice del array de URLs

2. **Seguridad**:
   - Las credenciales RTSP se ocultan en las respuestas API
   - `rtsp://admin:pass@...` → `rtsp://***@...`

3. **Persistencia**:
   - BD ubicada en: `data/cameras.db`
   - Logs HLS en: `/tmp/hls_streams/`

4. **Performance**:
   - Agregar/quitar cámaras no requiere reiniciar toda la API
   - Solo se reinicia el stream específico

---

## 🎯 Pendientes

- [ ] Desarrollar componente frontend Angular para el mantenedor
- [ ] Agregar validación de conectividad RTSP antes de guardar
- [ ] Implementar autenticación/autorización para endpoints de gestión
- [ ] Agregar endpoint de test de conexión: `POST /api/cameras/test`
- [ ] Soporte para múltiples streams por cámara (main/sub)

---

## 📚 Referencias

- **Backend API**: `api/cameras_endpoints.py`
- **Gestión BD**: `utils/camera_manager.py`
- **HLS Server**: `api/hls_server.py`
- **Main Entry**: `api/main.py` (línea ~749 startup_event)

---

**Última actualización**: 2026-01-10  
**Autor**: Sistema de Monitoreo de Hurones
