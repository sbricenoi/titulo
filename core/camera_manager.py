"""
Camera Manager - Gestión de múltiples streams RTSP.

Este módulo maneja la conexión, captura y gestión de múltiples cámaras IP
en paralelo, con reconexión automática y buffering de frames.

Autor: Sistema de Monitoreo de Hurones
Fecha: 2025-10-28
"""

import cv2
import numpy as np
import time
import threading
from queue import Queue, Empty
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from loguru import logger
import sys
from pathlib import Path

# Importar FFmpegCamera
sys.path.append(str(Path(__file__).parent.parent))
from camera_ffmpeg import FFmpegCamera


class CameraStatus(Enum):
    """Estados posibles de una cámara."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class Camera:
    """Representa una cámara individual del sistema."""
    id: int
    url: str
    name: str
    status: CameraStatus = CameraStatus.DISCONNECTED
    capture: Optional[FFmpegCamera] = None  # Cambio: usar FFmpegCamera
    thread: Optional[threading.Thread] = None
    frame_queue: Queue = None
    last_frame_time: float = 0.0
    fps: float = 0.0
    frame_count: int = 0
    error_count: int = 0
    width: int = 2880  # Resolución real de la cámara
    height: int = 1616
    target_fps: int = 20
    
    def __post_init__(self):
        """Inicializar queue si no existe."""
        if self.frame_queue is None:
            self.frame_queue = Queue(maxsize=30)


class CameraManager:
    """
    Gestor de múltiples cámaras RTSP con captura asíncrona.
    
    Características:
    - Captura asíncrona en threads separados
    - Reconexión automática ante fallos
    - Buffering de frames para evitar bloqueos
    - Monitoreo de FPS y estado de cada cámara
    
    Ejemplo:
        >>> manager = CameraManager(
        ...     camera_urls=["rtsp://cam1", "rtsp://cam2"],
        ...     camera_names=["Superior", "Inferior"]
        ... )
        >>> manager.start_all()
        >>> frames = manager.get_frames()
        >>> manager.stop_all()
    """
    
    def __init__(
        self,
        camera_urls: List[str],
        camera_names: Optional[List[str]] = None,
        buffer_size: int = 30,
        reconnect_delay: int = 5,
        timeout: int = 10,
        target_fps: int = 30
    ):
        """
        Inicializar el gestor de cámaras.
        
        Args:
            camera_urls: Lista de URLs RTSP de las cámaras
            camera_names: Nombres descriptivos (opcional)
            buffer_size: Tamaño del buffer de frames por cámara
            reconnect_delay: Segundos entre intentos de reconexión
            timeout: Timeout de conexión en segundos
            target_fps: FPS objetivo de captura
        """
        self.cameras: Dict[int, Camera] = {}
        self.buffer_size = buffer_size
        self.reconnect_delay = reconnect_delay
        self.timeout = timeout
        self.target_fps = target_fps
        self.running = False
        
        # Crear objetos Camera
        if camera_names is None:
            camera_names = [f"Cámara {i+1}" for i in range(len(camera_urls))]
        
        # Usar CAMERA_IDS de config si está disponible, sino usar índices
        from config import config as cfg
        camera_ids = cfg.CAMERA_IDS if cfg.CAMERA_IDS else list(range(len(camera_urls)))
        
        for cam_id, url, name in zip(camera_ids, camera_urls, camera_names):
            self.cameras[cam_id] = Camera(
                id=cam_id,
                url=url,
                name=name,
                frame_queue=Queue(maxsize=buffer_size)
            )
        
        logger.info(f"CameraManager inicializado con {len(self.cameras)} cámaras")
    
    def connect_camera(self, camera: Camera) -> bool:
        """
        Conectar a una cámara específica usando FFmpegCamera.
        
        Args:
            camera: Objeto Camera a conectar
            
        Returns:
            bool: True si la conexión fue exitosa
        """
        try:
            camera.status = CameraStatus.CONNECTING
            logger.info(f"Conectando a {camera.name} ({camera.url})...")
            
            # Crear captura con FFmpegCamera
            capture = FFmpegCamera(
                camera.url,
                width=camera.width,
                height=camera.height,
                fps=camera.target_fps
            )
            
            # Iniciar captura
            if capture.start():
                # Esperar y reintentar lectura del primer frame (hasta 10 segundos)
                logger.info(f"  Esperando primer frame de {camera.name}...")
                max_attempts = 50  # 50 intentos x 0.2s = 10 segundos
                
                for attempt in range(max_attempts):
                    ret, frame = capture.read()
                    
                    if ret and frame is not None:
                        camera.capture = capture
                        camera.status = CameraStatus.CONNECTED
                        camera.error_count = 0
                        
                        height, width = frame.shape[:2]
                        
                        logger.success(
                            f"✓ {camera.name} conectada - {width}x{height} @ {camera.target_fps} FPS (FFmpeg)"
                        )
                        return True
                    
                    time.sleep(0.2)  # Esperar 200ms antes de reintentar
                
                # Si llegamos aquí, no se pudo obtener frame
                capture.release()
                raise Exception(f"No se recibió frame después de {max_attempts * 0.2:.1f}s")
            else:
                raise Exception("No se pudo iniciar FFmpegCamera")
                
        except Exception as e:
            camera.status = CameraStatus.ERROR
            camera.error_count += 1
            logger.error(f"✗ Error conectando {camera.name}: {e}")
            return False
    
    def capture_loop(self, camera: Camera):
        """
        Loop de captura para una cámara (ejecutado en thread).
        
        Args:
            camera: Objeto Camera a capturar
        """
        logger.info(f"Thread de captura iniciado para {camera.name}")
        
        frame_delay = 1.0 / self.target_fps if self.target_fps > 0 else 0
        last_capture_time = time.time()
        
        while self.running:
            # Si está desconectada, intentar reconectar
            if camera.status != CameraStatus.CONNECTED:
                if camera.capture is not None:
                    camera.capture.release()
                    camera.capture = None
                
                time.sleep(self.reconnect_delay)
                self.connect_camera(camera)
                continue
            
            try:
                # Capturar frame con FFmpegCamera
                success, frame = camera.capture.read()
                
                if not success or frame is None:
                    logger.debug(f"Frame perdido en {camera.name}")
                    # No marcar como error inmediatamente, FFmpeg puede tardar
                    continue
                
                # Timestamp del frame
                timestamp = time.time()
                
                # Calcular FPS real
                elapsed = timestamp - camera.last_frame_time
                if elapsed > 0:
                    camera.fps = 0.9 * camera.fps + 0.1 * (1.0 / elapsed)
                
                camera.last_frame_time = timestamp
                camera.frame_count += 1
                
                # Agregar a queue (no bloqueante)
                try:
                    camera.frame_queue.put_nowait((frame.copy(), timestamp))
                except:
                    # Si el queue está lleno, eliminar el frame más viejo
                    try:
                        camera.frame_queue.get_nowait()
                        camera.frame_queue.put_nowait((frame.copy(), timestamp))
                    except:
                        pass
                
                # Control de FPS
                capture_time = time.time() - timestamp
                sleep_time = max(0, frame_delay - capture_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                logger.error(f"Error en captura de {camera.name}: {e}")
                camera.status = CameraStatus.ERROR
                time.sleep(1)
        
        # Limpiar al salir
        if camera.capture is not None:
            camera.capture.release()
        camera.status = CameraStatus.STOPPED
        logger.info(f"Thread de captura detenido para {camera.name}")
    
    def start_camera(self, camera_id: int) -> bool:
        """
        Iniciar captura de una cámara específica.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            bool: True si se inició correctamente
        """
        if camera_id not in self.cameras:
            logger.error(f"Cámara {camera_id} no existe")
            return False
        
        camera = self.cameras[camera_id]
        
        # Conectar si no está conectada
        if camera.status != CameraStatus.CONNECTED:
            if not self.connect_camera(camera):
                return False
        
        # Iniciar thread de captura
        if camera.thread is None or not camera.thread.is_alive():
            camera.thread = threading.Thread(
                target=self.capture_loop,
                args=(camera,),
                daemon=True,
                name=f"Camera-{camera_id}-{camera.name}"
            )
            camera.thread.start()
            logger.info(f"Thread iniciado para {camera.name}")
            return True
        
        return False
    
    def start_all(self):
        """Iniciar captura de todas las cámaras."""
        logger.info("Iniciando todas las cámaras...")
        self.running = True
        
        for camera_id in self.cameras:
            self.start_camera(camera_id)
        
        # Esperar un momento para que se conecten
        time.sleep(2)
        
        # Reportar estado
        connected = sum(1 for cam in self.cameras.values() 
                       if cam.status == CameraStatus.CONNECTED)
        logger.info(f"Cámaras conectadas: {connected}/{len(self.cameras)}")
    
    def stop_camera(self, camera_id: int):
        """
        Detener captura de una cámara específica.
        
        Args:
            camera_id: ID de la cámara
        """
        if camera_id not in self.cameras:
            return
        
        camera = self.cameras[camera_id]
        
        if camera.capture is not None:
            camera.capture.release()
            camera.capture = None
        
        camera.status = CameraStatus.STOPPED
        logger.info(f"Cámara {camera.name} detenida")
    
    def stop_all(self):
        """Detener captura de todas las cámaras."""
        logger.info("Deteniendo todas las cámaras...")
        self.running = False
        
        # Esperar a que los threads terminen
        for camera in self.cameras.values():
            if camera.thread is not None and camera.thread.is_alive():
                camera.thread.join(timeout=5)
            
            if camera.capture is not None:
                camera.capture.release()
                camera.capture = None
        
        logger.info("Todas las cámaras detenidas")
    
    def get_frame(self, camera_id: int, timeout: float = 0.5) -> Optional[Tuple[np.ndarray, float]]:
        """
        Obtener el frame más reciente de una cámara.
        
        Args:
            camera_id: ID de la cámara
            timeout: Timeout en segundos
            
        Returns:
            Tupla (frame, timestamp) o None si no hay frame disponible
        """
        if camera_id not in self.cameras:
            return None
        
        camera = self.cameras[camera_id]
        
        try:
            frame, timestamp = camera.frame_queue.get(timeout=timeout)
            return frame, timestamp
        except Empty:
            return None
    
    def get_frames(self, timeout: float = 0.5) -> Dict[int, Tuple[np.ndarray, float]]:
        """
        Obtener frames de todas las cámaras.
        
        Args:
            timeout: Timeout en segundos
            
        Returns:
            Diccionario {camera_id: (frame, timestamp)}
        """
        frames = {}
        
        for camera_id in self.cameras:
            frame_data = self.get_frame(camera_id, timeout)
            if frame_data is not None:
                frames[camera_id] = frame_data
        
        return frames
    
    def is_camera_alive(self, camera_id: int) -> bool:
        """
        Verificar si una cámara está funcionando.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            bool: True si la cámara está conectada y capturando
        """
        if camera_id not in self.cameras:
            return False
        
        camera = self.cameras[camera_id]
        
        # Verificar status y actividad reciente
        is_connected = camera.status == CameraStatus.CONNECTED
        is_recent = (time.time() - camera.last_frame_time) < 5.0
        
        return is_connected and is_recent
    
    def get_stats(self) -> Dict[int, Dict]:
        """
        Obtener estadísticas de todas las cámaras.
        
        Returns:
            Diccionario con stats por cámara
        """
        stats = {}
        
        for camera_id, camera in self.cameras.items():
            stats[camera_id] = {
                "name": camera.name,
                "status": camera.status.value,
                "fps": camera.fps,
                "frame_count": camera.frame_count,
                "error_count": camera.error_count,
                "queue_size": camera.frame_queue.qsize(),
                "alive": self.is_camera_alive(camera_id),
                "last_frame_age": time.time() - camera.last_frame_time,
            }
        
        return stats
    
    def __del__(self):
        """Destructor - asegurar limpieza."""
        self.stop_all()
    
    def __enter__(self):
        """Context manager - entrada."""
        self.start_all()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager - salida."""
        self.stop_all()


# ==================== EJEMPLO DE USO ====================
if __name__ == "__main__":
    """Ejemplo de uso del CameraManager."""
    
    # Configurar logging
    logger.add("camera_manager_test.log", rotation="10 MB")
    
    # URLs de ejemplo (cambiar por URLs reales)
    camera_urls = [
        "rtsp://admin:admin123@192.168.1.10:554/stream1",
        "rtsp://admin:admin123@192.168.1.11:554/stream1",
    ]
    
    camera_names = ["Cámara Superior", "Cámara Inferior"]
    
    # Crear manager
    manager = CameraManager(
        camera_urls=camera_urls,
        camera_names=camera_names,
        target_fps=30
    )
    
    try:
        # Iniciar captura
        manager.start_all()
        
        # Capturar durante 30 segundos
        start_time = time.time()
        frame_count = 0
        
        while time.time() - start_time < 30:
            frames = manager.get_frames()
            
            # Mostrar frames
            for camera_id, (frame, timestamp) in frames.items():
                camera = manager.cameras[camera_id]
                
                # Agregar info al frame
                cv2.putText(
                    frame,
                    f"{camera.name} - {camera.fps:.1f} FPS",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2
                )
                
                # Mostrar
                cv2.imshow(camera.name, frame)
                frame_count += 1
            
            # Tecla 'q' para salir
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            # Mostrar stats cada 5 segundos
            if int(time.time() - start_time) % 5 == 0:
                stats = manager.get_stats()
                logger.info(f"Stats: {stats}")
        
        logger.info(f"Total de frames procesados: {frame_count}")
        
    except KeyboardInterrupt:
        logger.info("Interrumpido por usuario")
    
    finally:
        # Detener
        manager.stop_all()
        cv2.destroyAllWindows()
        logger.info("Test finalizado")



