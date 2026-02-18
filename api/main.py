"""
FastAPI Backend - API REST y WebSocket para el Dashboard Angular.

Proporciona endpoints para:
- Estado del sistema
- Información de cámaras
- Individuos tracked
- Comportamientos
- Streaming de frames via WebSocket
- Métricas en tiempo real

Autor: Sistema de Monitoreo de Hurones
Fecha: 2025-10-28
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional, Set
from datetime import datetime
import asyncio
import json
import time
import cv2
import numpy as np
import base64
from loguru import logger

# Imports locales
from api.hls_server import initialize_hls_server, shutdown_hls_server, hls_server
from api.cameras_endpoints import router as cameras_router
from api.classification_endpoints import router as classification_router
from config import config
from api.system_bridge import bridge
from utils.behavior_log import BehaviorLog
from utils.camera_manager import camera_db

# Inicializar BehaviorLog para consultas
behavior_log = BehaviorLog(db_path=str(config.DATA_DIR / "behavior_log.db"))

# Crear app FastAPI
app = FastAPI(
    title="Ferret Monitoring API",
    description="API para el sistema de monitoreo multi-cámara de hurones",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.API_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar directorio de archivos HLS (para streaming de video)
# Crear directorio HLS si no existe
import os
hls_dir = "/tmp/hls_streams"
os.makedirs(hls_dir, exist_ok=True)
app.mount("/hls", StaticFiles(directory=hls_dir), name="hls")

# Incluir routers
app.include_router(cameras_router)
app.include_router(classification_router)

# Manager de WebSocket connections
class ConnectionManager:
    """Gestiona conexiones WebSocket activas."""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket conectado. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket desconectado. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Enviar mensaje a todos los clientes conectados."""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error enviando a WebSocket: {e}")
                disconnected.add(connection)
        
        # Limpiar conexiones muertas
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

# Manager de streams RTSP con broadcast (UNA lectura, MUCHOS clientes)
class StreamManager:
    """Gestiona conexiones RTSP con un solo loop de lectura por cámara."""
    
    def __init__(self):
        self.active_streams: Dict[int, cv2.VideoCapture] = {}
        self.stream_tasks: Dict[int, asyncio.Task] = {}
        self.latest_frames: Dict[int, Optional[bytes]] = {}
        self.frame_events: Dict[int, asyncio.Event] = {}
        self.client_counts: Dict[int, int] = {}
        self.stream_locks: Dict[int, asyncio.Lock] = {}
        self.last_request_time: Dict[int, float] = {}  # Timestamp de última petición
        self.INACTIVE_TIMEOUT = 5.0  # Segundos sin peticiones antes de detener loop
        
    async def _read_loop(self, camera_id: int):
        """Loop de lectura continua OPTIMIZADO para una cámara."""
        camera_url = config.CAMERA_URLS[camera_id]
        logger.info(f"🎥 Iniciando loop de lectura RTSP OPTIMIZADO para cámara {camera_id}")
        
        cap = cv2.VideoCapture(camera_url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # OPTIMIZACIÓN: Reducir resolución en la cámara si es posible
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        if not cap.isOpened():
            logger.error(f"❌ No se pudo abrir cámara {camera_id}")
            return
        
        self.active_streams[camera_id] = cap
        logger.info(f"✓ Conexión RTSP establecida para cámara {camera_id}")
        
        frame_count = 0
        error_count = 0
        max_errors = 5
        
        try:
            # Loop continuo que se detiene solo si no hay peticiones recientes
            while error_count < max_errors:
                # Verificar si han pasado más de INACTIVE_TIMEOUT segundos sin peticiones
                if camera_id in self.last_request_time:
                    time_since_last_request = time.time() - self.last_request_time[camera_id]
                    if time_since_last_request > self.INACTIVE_TIMEOUT:
                        logger.info(f"⏰ Loop de cámara {camera_id} detenido por inactividad ({time_since_last_request:.1f}s)")
                        break
                
                ret, frame = cap.read()
                
                if not ret:
                    error_count += 1
                    logger.warning(f"⚠️  Error leyendo frame de cámara {camera_id} ({error_count}/{max_errors})")
                    await asyncio.sleep(0.2)
                    continue
                
                error_count = 0  # Reset
                
                # OPTIMIZACIÓN: Redimensionar al 50% del tamaño original
                frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
                
                # OPTIMIZACIÓN: Menor calidad JPEG para reducir carga
                ret, buffer = cv2.imencode('.jpg', frame, [
                    cv2.IMWRITE_JPEG_QUALITY, 70,  # Reducido de 85 a 70
                    cv2.IMWRITE_JPEG_OPTIMIZE, 1
                ])
                
                if ret:
                    self.latest_frames[camera_id] = buffer.tobytes()
                    
                    frame_count += 1
                    if frame_count % 50 == 0:
                        logger.info(f"📊 Cámara {camera_id}: {frame_count} frames leídos y cacheados")
                
                # OPTIMIZACIÓN: Solo 10 FPS para reducir carga
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"❌ Error en loop de lectura cámara {camera_id}: {e}")
        finally:
            cap.release()
            logger.info(f"🔒 Loop de lectura cerrado para cámara {camera_id}")
            if camera_id in self.active_streams:
                del self.active_streams[camera_id]
            if camera_id in self.stream_tasks:
                del self.stream_tasks[camera_id]
    
    async def start_stream(self, camera_id: int):
        """Iniciar stream para una cámara si no existe."""
        if camera_id not in self.stream_locks:
            self.stream_locks[camera_id] = asyncio.Lock()
            self.frame_events[camera_id] = asyncio.Event()
        
        async with self.stream_locks[camera_id]:
            self.client_counts[camera_id] = self.client_counts.get(camera_id, 0) + 1
            logger.info(f"👥 Cliente conectado a cámara {camera_id}. Total: {self.client_counts[camera_id]}")
            
            # Iniciar loop de lectura si es el primer cliente
            if camera_id not in self.stream_tasks or self.stream_tasks[camera_id].done():
                self.latest_frames[camera_id] = None
                self.stream_tasks[camera_id] = asyncio.create_task(self._read_loop(camera_id))
    
    async def stop_stream(self, camera_id: int):
        """Decrementar contador y detener stream si es el último cliente."""
        if camera_id not in self.stream_locks:
            return
            
        async with self.stream_locks[camera_id]:
            self.client_counts[camera_id] = max(0, self.client_counts.get(camera_id, 1) - 1)
            logger.info(f"👋 Cliente desconectado de cámara {camera_id}. Quedan: {self.client_counts[camera_id]}")
            
            # El loop se detendrá automáticamente cuando client_count llegue a 0
    
    async def get_latest_frame(self, camera_id: int) -> Optional[bytes]:
        """Obtener el último frame disponible."""
        return self.latest_frames.get(camera_id)

stream_manager = StreamManager()

# Nota: system_state ahora se maneja vía SystemBridge
# El bridge es thread-safe y compartido con main.py


# ==================== MODELOS PYDANTIC ====================

class CameraInfo(BaseModel):
    """Información de una cámara."""
    id: int
    name: str
    status: str  # "connected", "disconnected", "error"
    fps: float
    resolution: tuple
    last_frame_time: Optional[str] = None

class TrackedIndividual(BaseModel):
    """Información de un individuo tracked."""
    id: str
    confidence: float
    cameras: List[int]  # IDs de cámaras donde se ve
    current_behavior: Optional[str] = None
    behavior_confidence: Optional[float] = None
    position: Optional[Dict[str, float]] = None  # {x, y, z}
    trajectory: List[Dict[str, float]] = []
    first_seen: str
    last_seen: str
    total_time: float  # segundos

class BehaviorEvent(BaseModel):
    """Evento de comportamiento."""
    id: str
    individual_id: str
    behavior: str
    confidence: float
    timestamp: str
    duration: Optional[float] = None

class SystemMetrics(BaseModel):
    """Métricas del sistema."""
    fps: float
    total_frames: int
    active_cameras: int
    total_cameras: int
    active_individuals: int
    total_detections: int
    uptime: float  # segundos
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    gpu_usage: Optional[float] = None

class Alert(BaseModel):
    """Alerta del sistema."""
    id: str
    type: str  # "warning", "error", "info"
    message: str
    individual_id: Optional[str] = None
    timestamp: str
    acknowledged: bool = False


# ==================== ENDPOINTS REST ====================

@app.get("/")
async def root():
    """Endpoint raíz."""
    return {
        "name": "Ferret Monitoring API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "traceId": "root-001",
        "code": 200,
        "message": "API funcionando correctamente",
        "data": {
            "endpoints": {
                "cameras": "/api/cameras",
                "individuals": "/api/individuals",
                "behaviors": "/api/behaviors",
                "metrics": "/api/metrics",
                "websocket": "/ws/stream"
            }
        }
    }

@app.get("/api/cameras", response_model=List[CameraInfo])
async def get_cameras():
    """Obtener información de todas las cámaras."""
    cameras = []
    
    # Con streaming directo FFmpeg, asumimos que las cámaras configuradas están disponibles
    for i, name in enumerate(config.CAMERA_NAMES):
        cameras.append(CameraInfo(
            id=i,
            name=name,
            status="connected",  # La API hace streaming directo, asumimos disponible
            fps=20.0,
            resolution=config.CAMERA_RESOLUTION,
            last_frame_time=None
        ))
    
    return cameras

@app.get("/api/cameras/{camera_id}")
async def get_camera(camera_id: int):
    """Obtener información de una cámara específica."""
    if camera_id >= len(config.CAMERA_NAMES):
        raise HTTPException(status_code=404, detail="Cámara no encontrada")
    
    camera_info = bridge.get_camera(camera_id) or {}
    
    return {
        "traceId": f"camera-{camera_id}",
        "code": 200,
        "message": "Información de cámara obtenida",
        "data": {
            "id": camera_id,
            "name": camera_info.get("name", config.CAMERA_NAMES[camera_id]),
            "status": camera_info.get("status", "disconnected"),
            "fps": camera_info.get("fps", 0.0),
            "resolution": camera_info.get("resolution", config.CAMERA_RESOLUTION),
            "last_frame_time": camera_info.get("last_frame_time")
        }
    }

@app.get("/api/individuals", response_model=List[TrackedIndividual])
async def get_individuals():
    """Obtener todos los individuos tracked."""
    individuals_data = bridge.get_all_individuals()
    individuals = []
    
    for individual_id, data in individuals_data.items():
        individuals.append(TrackedIndividual(
            id=individual_id,
            confidence=data.get("confidence", 0.0),
            cameras=data.get("cameras", []),
            current_behavior=data.get("current_behavior"),
            behavior_confidence=data.get("behavior_confidence"),
            position=data.get("position"),
            trajectory=data.get("trajectory", []),
            first_seen=data.get("first_seen", datetime.now().isoformat()),
            last_seen=data.get("last_seen", datetime.now().isoformat()),
            total_time=data.get("total_time", 0.0)
        ))
    
    return individuals

@app.get("/api/individuals/{individual_id}")
async def get_individual(individual_id: str):
    """Obtener información de un individuo específico."""
    data = bridge.get_individual(individual_id)
    
    if not data:
        raise HTTPException(status_code=404, detail="Individuo no encontrado")
    
    return {
        "traceId": f"individual-{individual_id}",
        "code": 200,
        "message": "Información de individuo obtenida",
        "data": {
            "id": individual_id,
            "confidence": data.get("confidence", 0.0),
            "cameras": data.get("cameras", []),
            "current_behavior": data.get("current_behavior"),
            "behavior_confidence": data.get("behavior_confidence"),
            "position": data.get("position"),
            "trajectory": data.get("trajectory", []),
            "first_seen": data.get("first_seen"),
            "last_seen": data.get("last_seen"),
            "total_time": data.get("total_time", 0.0)
        }
    }

@app.get("/api/behaviors", response_model=List[BehaviorEvent])
async def get_behaviors(limit: int = 100):
    """Obtener historial de comportamientos."""
    behaviors_data = bridge.get_behaviors(limit=limit)
    behaviors = []
    
    for data in behaviors_data:
        behaviors.append(BehaviorEvent(
            id=data["id"],
            individual_id=data["individual_id"],
            behavior=data["behavior"],
            confidence=data["confidence"],
            timestamp=data["timestamp"],
            duration=data.get("duration")
        ))
    
    return behaviors

@app.get("/api/metrics", response_model=SystemMetrics)
async def get_metrics():
    """Obtener métricas del sistema."""
    # Intentar leer métricas del archivo JSON (compartido entre procesos)
    metrics = {}
    try:
        metrics_path = config.DATA_DIR / "temp_metrics.json"
        if metrics_path.exists():
            import json
            with open(metrics_path, 'r') as f:
                metrics = json.load(f)
            logger.debug(f"Métricas leídas del archivo: {metrics}")
    except Exception as e:
        logger.debug(f"Error leyendo métricas del archivo: {e}")
        # Fallback al bridge (aunque no funcionará entre procesos)
        metrics = bridge.get_metrics()
    
    return SystemMetrics(
        fps=metrics.get("fps", 0.0),
        total_frames=metrics.get("total_frames", 0),
        active_cameras=metrics.get("active_cameras", 0),
        total_cameras=len(config.CAMERA_NAMES),
        active_individuals=metrics.get("active_individuals", 0),
        total_detections=metrics.get("total_detections", 0),
        uptime=metrics.get("uptime", 0.0),
        cpu_usage=metrics.get("cpu_usage"),
        memory_usage=metrics.get("memory_usage"),
        gpu_usage=metrics.get("gpu_usage")
    )

@app.get("/api/alerts", response_model=List[Alert])
async def get_alerts(limit: int = 50):
    """Obtener alertas del sistema."""
    return bridge.get_alerts(limit=limit)

@app.post("/api/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Marcar alerta como reconocida."""
    success = bridge.acknowledge_alert(alert_id)
    
    if success:
        return {
            "traceId": f"alert-ack-{alert_id}",
            "code": 200,
            "message": "Alerta reconocida",
            "data": {"alert_id": alert_id, "acknowledged": True}
        }
    
    raise HTTPException(status_code=404, detail="Alerta no encontrada")


# ==================== STREAMING ENDPOINTS (HLS) ====================

@app.get("/api/stream/hls/{camera_id}")
async def get_hls_url(camera_id: int):
    """
    Obtener URL del stream HLS para una cámara.
    
    Args:
        camera_id: ID de la cámara
        
    Returns:
        JSON con la URL del playlist HLS
    """
    if camera_id >= len(config.CAMERA_URLS):
        raise HTTPException(status_code=404, detail="Cámara no encontrada")
    
    if not hls_server or not hls_server.is_stream_active(camera_id):
        raise HTTPException(status_code=503, detail="Stream HLS no disponible")
    
    hls_url = f"/hls/camera_{camera_id}/stream.m3u8"
    
    return {
        "cameraId": camera_id,
        "hlsUrl": hls_url,
        "status": "active"
    }

@app.get("/api/stream/frame/{camera_id}")
async def get_frame(camera_id: int):
    """
    Obtener el frame más reciente de una cámara usando StreamManager optimizado.
    
    Args:
        camera_id: ID de la cámara
        
    Returns:
        Frame como imagen JPEG
    """
    if camera_id >= len(config.CAMERA_URLS):
        raise HTTPException(status_code=404, detail="Cámara no encontrada")
    
    # ACTUALIZAR timestamp de última petición (mantiene el loop activo)
    stream_manager.last_request_time[camera_id] = time.time()
    
    # Asegurar que el loop de lectura está activo
    if camera_id not in stream_manager.stream_tasks or stream_manager.stream_tasks[camera_id].done():
        if camera_id not in stream_manager.stream_locks:
            stream_manager.stream_locks[camera_id] = asyncio.Lock()
            stream_manager.frame_events[camera_id] = asyncio.Event()
        
        # Iniciar loop
        logger.info(f"🚀 Iniciando loop de lectura para cámara {camera_id}")
        stream_manager.stream_tasks[camera_id] = asyncio.create_task(stream_manager._read_loop(camera_id))
        
        # Esperar a que el primer frame esté disponible
        for _ in range(20):  # 2 segundos máximo
            await asyncio.sleep(0.1)
            if await stream_manager.get_latest_frame(camera_id):
                break
    
    # Obtener frame del cache
    frame_bytes = await stream_manager.get_latest_frame(camera_id)
    
    if not frame_bytes:
        raise HTTPException(status_code=503, detail="Frame no disponible aún, intente nuevamente")
    
    return StreamingResponse(
        iter([frame_bytes]),
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Access-Control-Allow-Origin": "*"
        }
    )

@app.get("/api/stream/mjpeg/{camera_id}")
async def stream_mjpeg(camera_id: int):
    """
    DESHABILITADO: Este endpoint causa múltiples conexiones.
    Use /api/stream/frame/{camera_id} con polling en su lugar.
    """
    raise HTTPException(
        status_code=410, 
        detail="Endpoint deshabilitado. Use /api/stream/frame/{camera_id} con polling"
    )

@app.get("/api/stream/mjpeg_old/{camera_id}")
async def stream_mjpeg_old(camera_id: int):
    """
    Stream MJPEG compartido desde la cámara (LEGACY - NO USAR).
    Usa StreamManager para evitar múltiples conexiones RTSP.
    
    Args:
        camera_id: ID de la cámara
        
    Returns:
        Stream MJPEG multipart
    """
    if camera_id >= len(config.CAMERA_URLS):
        raise HTTPException(status_code=404, detail="Cámara no encontrada")
    
    async def generate():
        """Generador de frames MJPEG usando broadcast desde el loop de lectura."""
        logger.info(f"📺 Cliente solicitando stream de cámara {camera_id}")
        
        try:
            # Registrar cliente y asegurar que el loop de lectura está corriendo
            await stream_manager.start_stream(camera_id)
            
            # Esperar a que haya frames disponibles
            for _ in range(50):  # Timeout de 5 segundos
                if await stream_manager.get_latest_frame(camera_id):
                    break
                await asyncio.sleep(0.1)
            
            frame_count = 0
            consecutive_errors = 0
            max_errors = 30
            
            while consecutive_errors < max_errors:
                try:
                    # Obtener último frame disponible del broadcast
                    frame_bytes = await stream_manager.get_latest_frame(camera_id)
                    
                    if not frame_bytes:
                        consecutive_errors += 1
                        await asyncio.sleep(0.1)
                        continue
                    
                    consecutive_errors = 0
                    
                    # Formato MJPEG multipart estándar
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                    
                    frame_count += 1
                    if frame_count % 100 == 0:
                        logger.debug(f"📤 Cámara {camera_id}: {frame_count} frames enviados a este cliente")
                    
                    # Control de FPS del cliente (~20 FPS)
                    await asyncio.sleep(0.05)
                    
                except asyncio.CancelledError:
                    logger.info(f"⚠️  Cliente canceló stream de cámara {camera_id}")
                    break
                except Exception as e:
                    logger.error(f"Error enviando frame: {e}")
                    consecutive_errors += 1
                    await asyncio.sleep(0.1)
            
            if consecutive_errors >= max_errors:
                logger.warning(f"⚠️  Máximo de errores alcanzado para cliente de cámara {camera_id}")
                
        except Exception as e:
            logger.error(f"❌ Error en stream MJPEG: {e}", exc_info=True)
        finally:
            await stream_manager.stop_stream(camera_id)
            logger.info(f"🔚 Cliente desconectado del stream de cámara {camera_id}")
    
    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

# ==================== WEBSOCKET ====================

@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """
    WebSocket para streaming de frames en tiempo real.
    
    Envía frames procesados con detecciones y tracking en base64.
    """
    await manager.connect(websocket)
    
    try:
        # Recibir configuración del cliente
        config_msg = await websocket.receive_json()
        camera_id = config_msg.get("camera_id", 0)
        fps_limit = config_msg.get("fps", 10)  # Limitar FPS para WebSocket
        
        logger.info(f"WebSocket stream iniciado para cámara {camera_id} @ {fps_limit} FPS")
        
        frame_delay = 1.0 / fps_limit
        
        while True:
            start_time = asyncio.get_event_loop().time()
            
            # Obtener frame más reciente
            frame_data = bridge.get_latest_frame(camera_id, encode=True)
            
            if frame_data:
                # Enviar frame con metadatos
                await websocket.send_json({
                    "type": "frame",
                    "camera_id": frame_data["camera_id"],
                    "timestamp": frame_data["timestamp"],
                    "frame_number": frame_data["frame_number"],
                    "frame": frame_data["frame"],  # Ya está en base64
                    "detections": frame_data.get("detections", [])
                })
            
            # Controlar FPS
            elapsed = asyncio.get_event_loop().time() - start_time
            sleep_time = max(0, frame_delay - elapsed)
            await asyncio.sleep(sleep_time)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Cliente WebSocket desconectado")
    except Exception as e:
        logger.error(f"Error en WebSocket: {e}")
        manager.disconnect(websocket)

@app.websocket("/ws/data")
async def websocket_data(websocket: WebSocket):
    """
    WebSocket para datos en tiempo real (métricas, individuos, etc.).
    
    Envía actualizaciones de estado sin frames de video.
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # Obtener estado actualizado del bridge
            # Leer métricas del archivo JSON (compartido entre procesos)
            metrics = {}
            try:
                metrics_path = config.DATA_DIR / "temp_metrics.json"
                if metrics_path.exists():
                    import json
                    with open(metrics_path, 'r') as f:
                        metrics = json.load(f)
            except Exception as e:
                logger.debug(f"Error leyendo métricas: {e}")
                metrics = bridge.get_metrics()
            
            individuals = bridge.get_all_individuals()
            cameras_bridge = bridge.get_all_cameras()
            behaviors = bridge.get_behaviors(limit=10)  # Últimos 10 comportamientos
            alerts = bridge.get_alerts(limit=10)  # Últimas 10 alertas
            
            # Obtener info real de cámaras (de la base de datos)
            cameras_real = {}
            try:
                cameras_from_db = camera_db.get_all_cameras()
                for cam in cameras_from_db:
                    cam_id = cam.get("id", 0)
                    cameras_real[cam_id] = {
                        "id": cam_id,
                        "name": cam.get("name", f"Cámara {cam_id}"),
                        "status": "connected" if cam.get("active") else "disconnected",
                        "fps": cameras_bridge.get(cam_id, {}).get("fps", 0.0),
                        "resolution": f"{cam.get('width', 0)}x{cam.get('height', 0)}"
                    }
            except Exception as e:
                logger.debug(f"Error obteniendo cámaras de DB: {e}")
                # Fallback a configuración
                for i, name in enumerate(config.CAMERA_NAMES):
                    cameras_real[i] = {
                        "id": i,
                        "name": name,
                        "status": "connected",
                        "fps": 20.0,
                        "resolution": config.CAMERA_RESOLUTION
                    }
            
            # Enviar estado actualizado con más información
            update = {
                "type": "state_update",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "metrics": metrics,
                    "individuals": len(individuals),
                    "active_cameras": sum(
                        1 for cam in cameras_real.values()
                        if cam.get("status") == "connected"
                    ),
                    "individuals_list": list(individuals.keys()),
                    "individuals_details": individuals,  # Detalles completos de individuos
                    "cameras": cameras_real,
                    "behaviors": behaviors,  # Comportamientos recientes
                    "alerts": alerts  # Alertas recientes (incluye detecciones de humanos si se agregan)
                }
            }
            
            await websocket.send_json(update)
            await asyncio.sleep(1.0)  # Actualizar cada segundo
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error en WebSocket de datos: {e}")
        manager.disconnect(websocket)


# ==================== FUNCIONES AUXILIARES ====================

def update_system_state(
    cameras: Optional[Dict] = None,
    individuals: Optional[Dict] = None,
    metrics: Optional[Dict] = None
):
    """
    Actualizar estado del sistema.
    
    Esta función sería llamada desde main.py para actualizar el estado.
    """
    if cameras:
        system_state["cameras"].update(cameras)
    
    if individuals:
        system_state["individuals"].update(individuals)
    
    if metrics:
        system_state["metrics"].update(metrics)

async def broadcast_update(update_type: str, data: dict):
    """Broadcast de actualización a todos los clientes WebSocket."""
    message = {
        "type": update_type,
        "timestamp": datetime.now().isoformat(),
        "data": data
    }
    await manager.broadcast(message)


# ==================== STARTUP/SHUTDOWN ====================

@app.on_event("startup")
async def startup_event():
    """Evento de inicio de la aplicación."""
    logger.info("🚀 API FastAPI iniciada")
    logger.info(f"📡 Escuchando en http://{config.API_HOST}:{config.API_PORT}")
    logger.info(f"📚 Docs disponibles en http://{config.API_HOST}:{config.API_PORT}/docs")
    
    # Inicializar cámaras en BD si no existen (migración desde config.py)
    if camera_db.count_cameras() == 0:
        logger.info("📹 Inicializando cámaras desde config.py...")
        for i, (url, name) in enumerate(zip(config.CAMERA_URLS, config.CAMERA_NAMES)):
            camera_db.add_camera(
                name=name,
                rtsp_url=url,
                description=f"Cámara importada desde configuración",
                location="Sin especificar",
                is_active=True
            )
        logger.info(f"✅ {len(config.CAMERA_URLS)} cámara(s) migrada(s) a BD")
    
    # Obtener URLs de cámaras activas desde BD
    camera_urls = camera_db.get_active_camera_urls()
    logger.info(f"📊 {len(camera_urls)} cámara(s) activa(s) en la base de datos")
    
    # Inicializar servidor HLS para streaming de video
    if camera_urls:
        logger.info("🎬 Inicializando servidor HLS...")
        initialize_hls_server(camera_urls)
        logger.info("✅ Servidor HLS listo")
    else:
        logger.warning("⚠️  No hay cámaras activas. Agrega cámaras desde /api/cameras")

@app.on_event("shutdown")
async def shutdown_event():
    """Evento de cierre de la aplicación."""
    logger.info("🔄 API FastAPI cerrándose...")
    
    # Detener servidor HLS
    logger.info("🛑 Deteniendo servidor HLS...")
    shutdown_hls_server()
    logger.info("✓ Servidor HLS detenido")


# ==================== ENDPOINTS DE BITÁCORA ====================

@app.get("/api/behaviors/individuals")
async def get_behavior_individuals():
    """
    Obtener lista de todos los individuos registrados en la bitácora.
    
    Returns:
        Lista de IDs de individuos con conteo de registros
    """
    try:
        individuals = behavior_log.get_all_individuals()
        
        # Obtener conteo por individuo (formato camelCase)
        data = []
        for individual_id in individuals:
            count = behavior_log.get_count(individual_id)
            last_behavior = behavior_log.get_last_behavior(individual_id)
            
            data.append({
                "individualId": individual_id,
                "totalBehaviors": count,
                "lastBehavior": last_behavior.behavior if last_behavior else None,
                "lastBehaviorEs": config.BEHAVIOR_NAMES_ES.get(last_behavior.behavior, last_behavior.behavior) if last_behavior else None,
                "lastSeen": last_behavior.timestamp if last_behavior else None
            })
        
        return {
            "traceId": "behavior-individuals",
            "code": 200,
            "message": "Lista de individuos obtenida",
            "data": data
        }
    except Exception as e:
        logger.error(f"Error obteniendo individuos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/behaviors/individual/{individual_id}")
async def get_individual_behavior_history(
    individual_id: str,
    limit: int = 50,
    offset: int = 0
):
    """
    Obtener historial de comportamientos de un individuo específico.
    
    Args:
        individual_id: ID del hurón
        limit: Número máximo de resultados
        offset: Offset para paginación
    """
    try:
        entries = behavior_log.get_by_individual(
            individual_id=individual_id,
            limit=limit,
            offset=offset,
            order_by="timestamp DESC"
        )
        
        # Convertir a formato compatible con frontend (camelCase)
        behaviors = []
        for entry in entries:
            behaviors.append({
                "id": str(entry.id),
                "individualId": entry.individual_id,  # camelCase
                "behavior": entry.behavior,
                "behaviorEs": config.BEHAVIOR_NAMES_ES.get(entry.behavior, entry.behavior),
                "confidence": entry.confidence,
                "timestamp": entry.timestamp,
                "duration": entry.duration,
                "cameraId": entry.camera_id,
                "metadata": entry.metadata
            })
        
        # Obtener conteo total
        total_count = behavior_log.get_count(individual_id)
        
        return {
            "traceId": f"behavior-history-{individual_id}",
            "code": 200,
            "message": f"Historial de {individual_id} obtenido",
            "data": {
                "individualId": individual_id,
                "behaviors": behaviors,
                "totalCount": total_count,
                "pageSize": limit,
                "offset": offset
            }
        }
    except Exception as e:
        logger.error(f"Error obteniendo historial: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/behaviors/individual/{individual_id}/statistics")
async def get_individual_statistics(
    individual_id: str,
    time_range_hours: Optional[int] = None
):
    """
    Obtener estadísticas de comportamiento de un individuo.
    
    Args:
        individual_id: ID del hurón
        time_range_hours: Horas hacia atrás (None = todo el tiempo)
    """
    try:
        stats = behavior_log.get_statistics(
            individual_id=individual_id,
            time_range_hours=time_range_hours
        )
        
        # Agregar nombres en español
        behaviors_with_es = {}
        for behavior, data in stats["behaviors"].items():
            behavior_es = config.BEHAVIOR_NAMES_ES.get(behavior, behavior)
            behaviors_with_es[behavior] = {
                **data,
                "name_es": behavior_es
            }
        
        stats["behaviors"] = behaviors_with_es
        
        return {
            "traceId": f"behavior-stats-{individual_id}",
            "code": 200,
            "message": f"Estadísticas de {individual_id} obtenidas",
            "data": stats
        }
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/behaviors/recent")
async def get_recent_behaviors(
    minutes: int = 60,
    individual_id: Optional[str] = None
):
    """
    Obtener comportamientos recientes.
    
    Args:
        minutes: Minutos hacia atrás
        individual_id: Filtrar por individuo (opcional)
    """
    try:
        entries = behavior_log.get_recent(
            minutes=minutes,
            individual_id=individual_id
        )
        
        # Convertir a diccionarios con nombres en español
        data = []
        for entry in entries:
            entry_dict = entry.to_dict()
            entry_dict["behavior_es"] = config.BEHAVIOR_NAMES_ES.get(
                entry.behavior, 
                entry.behavior
            )
            data.append(entry_dict)
        
        return {
            "traceId": "behavior-recent",
            "code": 200,
            "message": f"Comportamientos recientes obtenidos ({minutes} minutos)",
            "data": {
                "behaviors": data,
                "minutes": minutes,
                "individual_id": individual_id,
                "count": len(data)
            }
        }
    except Exception as e:
        logger.error(f"Error obteniendo comportamientos recientes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/behaviors/by-type/{behavior}")
async def get_behaviors_by_type(
    behavior: str,
    individual_id: Optional[str] = None,
    limit: int = 50
):
    """
    Obtener registros de un comportamiento específico.
    
    Args:
        behavior: Nombre del comportamiento (en inglés)
        individual_id: Filtrar por individuo (opcional)
        limit: Número máximo de resultados
    """
    try:
        entries = behavior_log.get_by_behavior(
            behavior=behavior,
            individual_id=individual_id,
            limit=limit
        )
        
        # Convertir a diccionarios
        data = []
        for entry in entries:
            entry_dict = entry.to_dict()
            entry_dict["behavior_es"] = config.BEHAVIOR_NAMES_ES.get(
                entry.behavior, 
                entry.behavior
            )
            data.append(entry_dict)
        
        return {
            "traceId": f"behavior-type-{behavior}",
            "code": 200,
            "message": f"Registros de '{behavior}' obtenidos",
            "data": {
                "behavior": behavior,
                "behavior_es": config.BEHAVIOR_NAMES_ES.get(behavior, behavior),
                "individual_id": individual_id,
                "behaviors": data,
                "count": len(data)
            }
        }
    except Exception as e:
        logger.error(f"Error obteniendo comportamientos por tipo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/behaviors/export/{individual_id}")
async def export_individual_behaviors(individual_id: str):
    """
    Exportar bitácora completa de un individuo a JSON.
    
    Args:
        individual_id: ID del hurón
    """
    try:
        import tempfile
        from fastapi.responses import FileResponse
        
        # Crear archivo temporal
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            delete=False,
            suffix='.json',
            prefix=f'bitacora_{individual_id}_'
        )
        temp_file.close()
        
        # Exportar
        behavior_log.export_to_json(temp_file.name, individual_id=individual_id)
        
        # Retornar archivo
        return FileResponse(
            path=temp_file.name,
            filename=f"bitacora_{individual_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            media_type="application/json"
        )
    except Exception as e:
        logger.error(f"Error exportando bitácora: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== DESARROLLO Y TESTING ====================

if __name__ == "__main__":
    import uvicorn
    
    # Configurar logging
    from utils.logger import setup_logger
    setup_logger()
    
    logger.info("Iniciando servidor de desarrollo...")
    
    uvicorn.run(
        "api.main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.API_RELOAD,
        log_level="info"
    )



