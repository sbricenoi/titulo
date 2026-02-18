#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
System Bridge - Puente entre el sistema principal y la API FastAPI

Permite compartir datos en tiempo real:
- Frames de cámaras
- Detecciones y tracking
- Métricas del sistema
- Comportamientos

Autor: Sistema de Monitoreo de Hurones
Fecha: 2025-11-08
"""

import asyncio
import cv2
import numpy as np
import base64
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from loguru import logger
import threading


@dataclass
class FrameData:
    """Datos de un frame procesado."""
    camera_id: int
    timestamp: float
    frame: np.ndarray
    detections: List[Dict] = None
    frame_number: int = 0


class SystemBridge:
    """
    Puente de comunicación entre el sistema principal y la API.
    
    Mantiene el estado actualizado del sistema y permite acceso
    thread-safe desde la API FastAPI.
    """
    
    def __init__(self):
        """Inicializar bridge."""
        self._lock = threading.RLock()
        
        # Estado del sistema
        self.cameras = {}
        self.individuals = {}
        self.behaviors = {}
        self.metrics = {
            "fps": 0.0,
            "total_frames": 0,
            "active_cameras": 0,
            "active_individuals": 0,
            "total_detections": 0,
            "uptime": 0.0
        }
        self.alerts = []
        
        # Frames más recientes de cada cámara
        self._latest_frames: Dict[int, FrameData] = {}
        
        # Cola para broadcasting
        self._frame_subscribers = []
        
        # Event logger (se configurará desde main.py)
        self.event_logger = None
        
        logger.info("SystemBridge inicializado")
    
    # ==================== CÁMARAS ====================
    
    def update_camera(self, camera_id: int, **kwargs):
        """
        Actualizar información de una cámara.
        
        Args:
            camera_id: ID de la cámara
            **kwargs: Datos a actualizar (status, fps, etc.)
        """
        with self._lock:
            if camera_id not in self.cameras:
                self.cameras[camera_id] = {}
            
            self.cameras[camera_id].update(kwargs)
            
            # Actualizar timestamp
            self.cameras[camera_id]["last_update"] = datetime.now().isoformat()
    
    def get_camera(self, camera_id: int) -> Optional[Dict]:
        """Obtener información de una cámara."""
        with self._lock:
            return self.cameras.get(camera_id, {}).copy()
    
    def get_all_cameras(self) -> Dict[int, Dict]:
        """Obtener todas las cámaras."""
        with self._lock:
            return {k: v.copy() for k, v in self.cameras.items()}
    
    # ==================== FRAMES ====================
    
    def update_frame(self, camera_id: int, frame: np.ndarray, 
                    timestamp: float, detections: List[Dict] = None,
                    frame_number: int = 0):
        """
        Actualizar el frame más reciente de una cámara.
        
        Args:
            camera_id: ID de la cámara
            frame: Frame como numpy array
            timestamp: Timestamp del frame
            detections: Lista de detecciones (opcional)
            frame_number: Número de frame
        """
        with self._lock:
            self._latest_frames[camera_id] = FrameData(
                camera_id=camera_id,
                timestamp=timestamp,
                frame=frame,
                detections=detections or [],
                frame_number=frame_number
            )
            
            # Actualizar info de cámara
            self.update_camera(
                camera_id,
                last_frame_time=datetime.fromtimestamp(timestamp).isoformat(),
                frame_number=frame_number
            )
    
    def get_latest_frame(self, camera_id: int, encode: bool = False) -> Optional[Dict]:
        """
        Obtener el frame más reciente de una cámara.
        
        Args:
            camera_id: ID de la cámara
            encode: Si True, codificar frame como base64 JPEG
            
        Returns:
            Dict con datos del frame o None
        """
        with self._lock:
            frame_data = self._latest_frames.get(camera_id)
            
            if frame_data is None:
                return None
            
            result = {
                "camera_id": frame_data.camera_id,
                "timestamp": frame_data.timestamp,
                "frame_number": frame_data.frame_number,
                "detections": frame_data.detections
            }
            
            if encode:
                # Codificar frame como JPEG y luego a base64
                _, buffer = cv2.imencode('.jpg', frame_data.frame, 
                                        [cv2.IMWRITE_JPEG_QUALITY, 85])
                result["frame"] = base64.b64encode(buffer).decode('utf-8')
            else:
                result["frame"] = frame_data.frame
            
            return result
    
    def get_all_latest_frames(self, encode: bool = False) -> Dict[int, Dict]:
        """Obtener frames más recientes de todas las cámaras."""
        with self._lock:
            return {
                camera_id: self.get_latest_frame(camera_id, encode=encode)
                for camera_id in self._latest_frames.keys()
            }
    
    # ==================== INDIVIDUOS ====================
    
    def update_individual(self, individual_id: str, **kwargs):
        """
        Actualizar información de un individuo.
        
        Args:
            individual_id: ID global del individuo
            **kwargs: Datos a actualizar
        """
        with self._lock:
            if individual_id not in self.individuals:
                self.individuals[individual_id] = {
                    "id": individual_id,
                    "first_seen": datetime.now().isoformat(),
                    "trajectory": []
                }
            
            self.individuals[individual_id].update(kwargs)
            self.individuals[individual_id]["last_seen"] = datetime.now().isoformat()
    
    def get_individual(self, individual_id: str) -> Optional[Dict]:
        """Obtener información de un individuo."""
        with self._lock:
            return self.individuals.get(individual_id, {}).copy()
    
    def get_all_individuals(self) -> Dict[str, Dict]:
        """Obtener todos los individuos."""
        with self._lock:
            return {k: v.copy() for k, v in self.individuals.items()}
    
    def remove_individual(self, individual_id: str):
        """Remover un individuo (cuando sale de escena)."""
        with self._lock:
            if individual_id in self.individuals:
                del self.individuals[individual_id]
    
    # ==================== COMPORTAMIENTOS ====================
    
    def log_behavior(self, individual_id: str, behavior: str, 
                    confidence: float, timestamp: Optional[float] = None):
        """
        Registrar un evento de comportamiento.
        
        Args:
            individual_id: ID del individuo
            behavior: Nombre del comportamiento
            confidence: Confianza de la clasificación
            timestamp: Timestamp (opcional, usa now si no se provee)
        """
        with self._lock:
            behavior_id = f"{individual_id}_{len(self.behaviors)}"
            
            self.behaviors[behavior_id] = {
                "id": behavior_id,
                "individual_id": individual_id,
                "behavior": behavior,
                "confidence": confidence,
                "timestamp": datetime.fromtimestamp(timestamp).isoformat() 
                           if timestamp else datetime.now().isoformat()
            }
            
            # Actualizar comportamiento actual del individuo
            self.update_individual(
                individual_id,
                current_behavior=behavior,
                behavior_confidence=confidence
            )
    
    def get_behaviors(self, limit: int = 100) -> List[Dict]:
        """Obtener historial de comportamientos."""
        with self._lock:
            return list(self.behaviors.values())[-limit:]
    
    # ==================== MÉTRICAS ====================
    
    def update_metrics(self, **kwargs):
        """
        Actualizar métricas del sistema.
        
        Args:
            **kwargs: Métricas a actualizar (fps, total_frames, etc.)
        """
        with self._lock:
            self.metrics.update(kwargs)
            self.metrics["last_update"] = datetime.now().isoformat()
    
    def get_metrics(self) -> Dict:
        """Obtener métricas actuales."""
        with self._lock:
            return self.metrics.copy()
    
    # ==================== ALERTAS ====================
    
    def add_alert(self, alert_type: str, message: str, 
                 individual_id: Optional[str] = None):
        """
        Agregar una alerta.
        
        Args:
            alert_type: Tipo de alerta ("warning", "error", "info")
            message: Mensaje de la alerta
            individual_id: ID del individuo relacionado (opcional)
        """
        with self._lock:
            alert = {
                "id": f"alert_{len(self.alerts)}",
                "type": alert_type,
                "message": message,
                "individual_id": individual_id,
                "timestamp": datetime.now().isoformat(),
                "acknowledged": False
            }
            
            self.alerts.append(alert)
            
            # Mantener solo las últimas 100 alertas
            if len(self.alerts) > 100:
                self.alerts = self.alerts[-100:]
    
    def get_alerts(self, limit: int = 50) -> List[Dict]:
        """Obtener alertas recientes."""
        with self._lock:
            return self.alerts[-limit:]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Marcar alerta como reconocida."""
        with self._lock:
            for alert in self.alerts:
                if alert["id"] == alert_id:
                    alert["acknowledged"] = True
                    return True
            return False
    
    # ==================== ESTADO COMPLETO ====================
    
    def get_full_state(self) -> Dict[str, Any]:
        """Obtener estado completo del sistema."""
        with self._lock:
            return {
                "cameras": self.get_all_cameras(),
                "individuals": self.get_all_individuals(),
                "behaviors": self.get_behaviors(limit=50),
                "metrics": self.get_metrics(),
                "alerts": self.get_alerts(limit=20),
                "timestamp": datetime.now().isoformat()
            }


# Instancia global del bridge (singleton)
_bridge_instance = None
_bridge_lock = threading.Lock()


def get_system_bridge() -> SystemBridge:
    """
    Obtener instancia global del SystemBridge (singleton).
    
    Returns:
        Instancia única de SystemBridge
    """
    global _bridge_instance
    
    if _bridge_instance is None:
        with _bridge_lock:
            if _bridge_instance is None:
                _bridge_instance = SystemBridge()
    
    return _bridge_instance


# Alias para facilitar importación
bridge = get_system_bridge()



