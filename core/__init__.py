"""
Módulo Core del Sistema de Monitoreo Multi-Cámara.

Este paquete contiene los componentes centrales del sistema:
- CameraManager: Gestión de streams RTSP de múltiples cámaras
- SyncEngine: Sincronización temporal entre cámaras
- FusionEngine: Fusión de detecciones multi-cámara

Uso:
    from core import CameraManager, SyncEngine, FusionEngine
"""

from .camera_manager import CameraManager, Camera, CameraStatus
from .sync_engine import SyncEngine, SyncedFrame
from .fusion_engine import FusionEngine, FusedObject

__all__ = [
    "CameraManager",
    "Camera",
    "CameraStatus",
    "SyncEngine",
    "SyncedFrame",
    "FusionEngine",
    "FusedObject",
]

__version__ = "1.0.0"





