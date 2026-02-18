"""
Módulo AI del Sistema de Monitoreo Multi-Cámara.

Este paquete contiene los componentes de inteligencia artificial:
- BehaviorDetector: Detección de hurones con YOLOv8
- MultiCameraTracker: Tracking y re-identificación multi-cámara
- BehaviorClassifier: Clasificación de comportamientos
- IncrementalTrainer: Reentrenamiento incremental

Uso:
    from ai import BehaviorDetector, MultiCameraTracker, BehaviorClassifier
"""

from .detector import BehaviorDetector
from .tracker import MultiCameraTracker, TrackedObject
from .behavior_model import BehaviorClassifier, BehaviorPrediction
from .trainer import IncrementalTrainer

__all__ = [
    "BehaviorDetector",
    "MultiCameraTracker",
    "TrackedObject",
    "BehaviorClassifier",
    "BehaviorPrediction",
    "IncrementalTrainer",
]

__version__ = "1.0.0"





