"""
Módulo de Utilidades del Sistema de Monitoreo.

Este paquete contiene utilidades compartidas:
- Visualizer: Visualización de detecciones y tracking
- Logger: Sistema de logging estructurado
- Synchronizer: Herramientas de sincronización

Uso:
    from utils import Visualizer, setup_logger
"""

from .visualizer import Visualizer
from .logger import setup_logger, EventLogger
from .synchronizer import TimeSync, FPSCounter, LatencyTracker
from .behavior_log import BehaviorLog, BehaviorEntry

__all__ = [
    "Visualizer",
    "setup_logger",
    "EventLogger",
    "TimeSync",
    "FPSCounter",
    "LatencyTracker",
    "BehaviorLog",
    "BehaviorEntry",
]

__version__ = "1.0.0"



