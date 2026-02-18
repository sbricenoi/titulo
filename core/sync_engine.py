"""
Sync Engine - Sincronización temporal entre múltiples cámaras.

Este módulo maneja la sincronización de frames de múltiples cámaras usando
timestamps, permitiendo obtener conjuntos de frames alineados temporalmente.

Autor: Sistema de Monitoreo de Hurones
Fecha: 2025-10-28
"""

import numpy as np
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque
from loguru import logger


@dataclass
class SyncedFrame:
    """Representa un frame sincronizado con metadata."""
    camera_id: int
    frame: np.ndarray
    timestamp: float
    frame_number: int = 0
    
    @property
    def age(self) -> float:
        """Edad del frame en segundos."""
        return time.time() - self.timestamp


@dataclass
class FrameBuffer:
    """Buffer temporal para frames de una cámara."""
    camera_id: int
    max_size: int = 30
    frames: deque = field(default_factory=deque)
    
    def add_frame(self, frame: np.ndarray, timestamp: float, frame_number: int):
        """Agregar frame al buffer."""
        synced_frame = SyncedFrame(
            camera_id=self.camera_id,
            frame=frame,
            timestamp=timestamp,
            frame_number=frame_number
        )
        
        self.frames.append(synced_frame)
        
        # Mantener tamaño máximo
        while len(self.frames) > self.max_size:
            self.frames.popleft()
    
    def get_closest_frame(self, target_timestamp: float) -> Optional[SyncedFrame]:
        """
        Obtener el frame más cercano a un timestamp dado.
        
        Args:
            target_timestamp: Timestamp objetivo
            
        Returns:
            SyncedFrame más cercano o None
        """
        if not self.frames:
            return None
        
        # Buscar frame más cercano
        closest_frame = min(
            self.frames,
            key=lambda f: abs(f.timestamp - target_timestamp)
        )
        
        return closest_frame
    
    def get_frames_in_window(
        self,
        center_timestamp: float,
        window_ms: float
    ) -> List[SyncedFrame]:
        """
        Obtener frames dentro de una ventana temporal.
        
        Args:
            center_timestamp: Timestamp central
            window_ms: Ventana en milisegundos
            
        Returns:
            Lista de frames dentro de la ventana
        """
        window_sec = window_ms / 1000.0
        
        frames_in_window = [
            f for f in self.frames
            if abs(f.timestamp - center_timestamp) <= window_sec
        ]
        
        return frames_in_window
    
    def clear_old_frames(self, max_age_sec: float = 2.0):
        """Eliminar frames más viejos que max_age_sec."""
        current_time = time.time()
        
        while self.frames and (current_time - self.frames[0].timestamp) > max_age_sec:
            self.frames.popleft()
    
    def get_latest_timestamp(self) -> Optional[float]:
        """Obtener timestamp del frame más reciente."""
        if not self.frames:
            return None
        return self.frames[-1].timestamp
    
    def __len__(self) -> int:
        """Número de frames en el buffer."""
        return len(self.frames)


class SyncEngine:
    """
    Motor de sincronización temporal para múltiples cámaras.
    
    Mantiene buffers temporales de frames de cada cámara y permite
    obtener conjuntos de frames sincronizados por timestamp.
    
    Estrategias de sincronización:
    1. CLOSEST: Seleccionar frames más cercanos a un timestamp de referencia
    2. INTERPOLATE: Interpolar entre frames (futuro)
    3. WAIT: Esperar hasta tener frames de todas las cámaras
    
    Ejemplo:
        >>> sync_engine = SyncEngine(tolerance_ms=100)
        >>> sync_engine.add_frame(camera_id=0, frame=frame1, timestamp=t1)
        >>> sync_engine.add_frame(camera_id=1, frame=frame2, timestamp=t2)
        >>> synced_frames = sync_engine.get_synced_frames()
    """
    
    def __init__(
        self,
        tolerance_ms: int = 100,
        buffer_size: int = 30,
        max_delay_ms: int = 500,
        strategy: str = "closest"
    ):
        """
        Inicializar el motor de sincronización.
        
        Args:
            tolerance_ms: Tolerancia de sincronización en milisegundos
            buffer_size: Tamaño del buffer por cámara
            max_delay_ms: Máximo delay aceptable entre cámaras (ms)
            strategy: Estrategia de sincronización ('closest', 'wait')
        """
        self.tolerance_ms = tolerance_ms
        self.tolerance_sec = tolerance_ms / 1000.0
        self.buffer_size = buffer_size
        self.max_delay_ms = max_delay_ms
        self.max_delay_sec = max_delay_ms / 1000.0
        self.strategy = strategy
        
        # Buffers por cámara
        self.buffers: Dict[int, FrameBuffer] = {}
        
        # Estadísticas
        self.stats = {
            "total_frames_added": 0,
            "total_synced_sets": 0,
            "sync_failures": 0,
            "average_sync_error": 0.0,
        }
        
        self.frame_counters: Dict[int, int] = {}
        
        logger.info(
            f"SyncEngine inicializado: tolerancia={tolerance_ms}ms, "
            f"buffer={buffer_size}, estrategia='{strategy}'"
        )
    
    def register_camera(self, camera_id: int):
        """
        Registrar una nueva cámara en el sistema de sincronización.
        
        Args:
            camera_id: ID de la cámara
        """
        if camera_id not in self.buffers:
            self.buffers[camera_id] = FrameBuffer(
                camera_id=camera_id,
                max_size=self.buffer_size
            )
            self.frame_counters[camera_id] = 0
            logger.debug(f"Cámara {camera_id} registrada en SyncEngine")
    
    def add_frame(
        self,
        camera_id: int,
        frame: np.ndarray,
        timestamp: Optional[float] = None
    ):
        """
        Agregar un frame al buffer de sincronización.
        
        Args:
            camera_id: ID de la cámara
            frame: Frame capturado (numpy array)
            timestamp: Timestamp del frame (si None, usa time.time())
        """
        # Registrar cámara si no existe
        if camera_id not in self.buffers:
            self.register_camera(camera_id)
        
        # Usar timestamp actual si no se proporciona
        if timestamp is None:
            timestamp = time.time()
        
        # Incrementar contador de frames
        self.frame_counters[camera_id] += 1
        frame_number = self.frame_counters[camera_id]
        
        # Agregar al buffer
        self.buffers[camera_id].add_frame(frame, timestamp, frame_number)
        
        # Actualizar estadísticas
        self.stats["total_frames_added"] += 1
        
        # Limpiar frames viejos
        self.buffers[camera_id].clear_old_frames(max_age_sec=2.0)
    
    def get_reference_timestamp(self) -> Optional[float]:
        """
        Obtener timestamp de referencia para sincronización.
        
        Estrategia: Usar el timestamp más reciente de la cámara con
        el timestamp más antiguo (para asegurar que todas tengan frames).
        
        Returns:
            Timestamp de referencia o None si no hay frames
        """
        if not self.buffers:
            return None
        
        # Obtener últimos timestamps de cada cámara
        latest_timestamps = []
        for buffer in self.buffers.values():
            ts = buffer.get_latest_timestamp()
            if ts is not None:
                latest_timestamps.append(ts)
        
        if not latest_timestamps:
            return None
        
        # Usar el timestamp más antiguo de los más recientes
        # Esto asegura que todas las cámaras tengan frames disponibles
        reference_timestamp = min(latest_timestamps)
        
        return reference_timestamp
    
    def get_synced_frames(
        self,
        camera_ids: Optional[List[int]] = None,
        reference_timestamp: Optional[float] = None
    ) -> Dict[int, SyncedFrame]:
        """
        Obtener conjunto de frames sincronizados.
        
        Args:
            camera_ids: Lista de IDs de cámaras (None = todas)
            reference_timestamp: Timestamp de referencia (None = auto)
            
        Returns:
            Diccionario {camera_id: SyncedFrame} con frames sincronizados
        """
        # Determinar cámaras a sincronizar
        if camera_ids is None:
            camera_ids = list(self.buffers.keys())
        
        # Verificar que hay cámaras
        if not camera_ids:
            return {}
        
        # Obtener timestamp de referencia
        if reference_timestamp is None:
            reference_timestamp = self.get_reference_timestamp()
        
        if reference_timestamp is None:
            logger.debug("No hay timestamp de referencia disponible")
            return {}
        
        # Obtener frames más cercanos al timestamp de referencia
        synced_frames = {}
        sync_errors = []
        
        for camera_id in camera_ids:
            if camera_id not in self.buffers:
                logger.warning(f"Cámara {camera_id} no registrada")
                continue
            
            buffer = self.buffers[camera_id]
            
            # Obtener frame más cercano
            closest_frame = buffer.get_closest_frame(reference_timestamp)
            
            if closest_frame is None:
                logger.debug(f"No hay frame disponible para cámara {camera_id}")
                continue
            
            # Verificar tolerancia
            time_diff = abs(closest_frame.timestamp - reference_timestamp)
            
            if time_diff <= self.tolerance_sec:
                synced_frames[camera_id] = closest_frame
                sync_errors.append(time_diff * 1000)  # en ms
            else:
                logger.debug(
                    f"Frame de cámara {camera_id} fuera de tolerancia: "
                    f"{time_diff*1000:.1f}ms"
                )
                self.stats["sync_failures"] += 1
        
        # Actualizar estadísticas
        if synced_frames:
            self.stats["total_synced_sets"] += 1
            if sync_errors:
                avg_error = np.mean(sync_errors)
                self.stats["average_sync_error"] = (
                    0.9 * self.stats["average_sync_error"] + 0.1 * avg_error
                )
        
        return synced_frames
    
    def get_synced_frames_dict(
        self,
        camera_ids: Optional[List[int]] = None,
        reference_timestamp: Optional[float] = None
    ) -> Dict[int, Tuple[np.ndarray, float]]:
        """
        Obtener frames sincronizados en formato simple (frame, timestamp).
        
        Args:
            camera_ids: Lista de IDs de cámaras (None = todas)
            reference_timestamp: Timestamp de referencia (None = auto)
            
        Returns:
            Diccionario {camera_id: (frame, timestamp)}
        """
        synced_frames = self.get_synced_frames(camera_ids, reference_timestamp)
        
        return {
            camera_id: (sf.frame, sf.timestamp)
            for camera_id, sf in synced_frames.items()
        }
    
    def wait_for_synced_frames(
        self,
        camera_ids: Optional[List[int]] = None,
        timeout: float = 1.0,
        min_cameras: Optional[int] = None
    ) -> Dict[int, SyncedFrame]:
        """
        Esperar hasta obtener frames sincronizados de las cámaras.
        
        Args:
            camera_ids: Lista de IDs de cámaras (None = todas)
            timeout: Timeout en segundos
            min_cameras: Mínimo número de cámaras requeridas
            
        Returns:
            Diccionario con frames sincronizados
        """
        if camera_ids is None:
            camera_ids = list(self.buffers.keys())
        
        if min_cameras is None:
            min_cameras = len(camera_ids)
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            synced_frames = self.get_synced_frames(camera_ids)
            
            if len(synced_frames) >= min_cameras:
                return synced_frames
            
            time.sleep(0.01)  # 10ms
        
        # Timeout - devolver lo que se tenga
        logger.warning(
            f"Timeout esperando frames sincronizados: "
            f"{len(synced_frames)}/{min_cameras} cámaras"
        )
        return self.get_synced_frames(camera_ids)
    
    def get_buffer_info(self) -> Dict[int, Dict]:
        """
        Obtener información de los buffers.
        
        Returns:
            Diccionario con info por cámara
        """
        info = {}
        
        for camera_id, buffer in self.buffers.items():
            latest_ts = buffer.get_latest_timestamp()
            
            info[camera_id] = {
                "buffer_size": len(buffer),
                "latest_timestamp": latest_ts,
                "age_sec": time.time() - latest_ts if latest_ts else None,
                "frame_count": self.frame_counters.get(camera_id, 0),
            }
        
        return info
    
    def get_stats(self) -> Dict:
        """Obtener estadísticas del motor de sincronización."""
        stats = self.stats.copy()
        stats["buffer_info"] = self.get_buffer_info()
        stats["num_cameras"] = len(self.buffers)
        
        return stats
    
    def reset(self):
        """Resetear todos los buffers y estadísticas."""
        for buffer in self.buffers.values():
            buffer.frames.clear()
        
        self.stats = {
            "total_frames_added": 0,
            "total_synced_sets": 0,
            "sync_failures": 0,
            "average_sync_error": 0.0,
        }
        
        logger.info("SyncEngine reseteado")


# ==================== EJEMPLO DE USO ====================
if __name__ == "__main__":
    """Ejemplo de uso del SyncEngine."""
    
    from loguru import logger
    import cv2
    
    # Configurar logging
    logger.add("sync_engine_test.log", rotation="10 MB")
    
    # Crear sync engine
    sync_engine = SyncEngine(
        tolerance_ms=100,
        buffer_size=30,
        strategy="closest"
    )
    
    # Simular 2 cámaras
    logger.info("Simulando captura de 2 cámaras...")
    
    for i in range(100):
        # Simular frames de 2 cámaras con ligero desync
        t1 = time.time()
        frame1 = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        sync_engine.add_frame(camera_id=0, frame=frame1, timestamp=t1)
        
        time.sleep(0.01)  # 10ms de delay
        
        t2 = time.time()
        frame2 = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        sync_engine.add_frame(camera_id=1, frame=frame2, timestamp=t2)
        
        # Cada 10 frames, obtener frames sincronizados
        if i % 10 == 0:
            synced = sync_engine.get_synced_frames()
            
            if len(synced) == 2:
                time_diff = abs(synced[0].timestamp - synced[1].timestamp) * 1000
                logger.info(f"Frame {i}: Sincronización exitosa, diff={time_diff:.2f}ms")
            else:
                logger.warning(f"Frame {i}: Solo {len(synced)} cámaras sincronizadas")
        
        time.sleep(0.02)  # ~30 FPS
    
    # Mostrar estadísticas
    stats = sync_engine.get_stats()
    logger.info(f"\nEstadísticas finales:")
    logger.info(f"  Total frames: {stats['total_frames_added']}")
    logger.info(f"  Sets sincronizados: {stats['total_synced_sets']}")
    logger.info(f"  Fallos de sync: {stats['sync_failures']}")
    logger.info(f"  Error promedio: {stats['average_sync_error']:.2f}ms")
    
    logger.info("Test finalizado")





