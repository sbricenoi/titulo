"""
Logger - Sistema de logging estructurado para el sistema de monitoreo.

Este módulo configura logging usando loguru con rotación, retención
y formateo personalizado.

Autor: Sistema de Monitoreo de Hurones
Fecha: 2025-10-28
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger
import json
from datetime import datetime


def setup_logger(
    log_file: str = "data/logs/system.log",
    log_level: str = "INFO",
    rotation: str = "100 MB",
    retention: str = "30 days",
    format_string: Optional[str] = None,
    backtrace: bool = True,
    diagnose: bool = True
) -> logger:
    """
    Configurar sistema de logging con loguru.
    
    Args:
        log_file: Path al archivo de log
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR)
        rotation: Criterio de rotación ("100 MB", "1 day", etc.)
        retention: Tiempo de retención ("30 days", "1 week", etc.)
        format_string: Formato personalizado (None = usar default)
        backtrace: Mostrar traceback completo en errores
        diagnose: Mostrar variables en traceback
        
    Returns:
        Logger configurado
    """
    # Remover handlers por defecto
    logger.remove()
    
    # Formato por defecto
    if format_string is None:
        format_string = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )
    
    # Handler para consola (con colores)
    logger.add(
        sys.stderr,
        format=format_string,
        level=log_level,
        colorize=True,
        backtrace=backtrace,
        diagnose=diagnose
    )
    
    # Handler para archivo (sin colores)
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        log_file,
        format=format_string,
        level=log_level,
        rotation=rotation,
        retention=retention,
        compression="zip",
        backtrace=backtrace,
        diagnose=diagnose
    )
    
    logger.info(f"Sistema de logging configurado: {log_file} (nivel={log_level})")
    
    return logger


class EventLogger:
    """
    Logger especializado para eventos del sistema.
    
    Registra eventos estructurados como detecciones, comportamientos,
    alertas, etc. en formato JSON para análisis posterior.
    
    Ejemplo:
        >>> event_logger = EventLogger("data/logs/events.log")
        >>> event_logger.log_detection("F1", "playing", 0.9)
        >>> event_logger.log_alert("F1", "sleeping_too_long", 300)
    """
    
    def __init__(
        self,
        log_file: str = "data/logs/events.log",
        rotation: str = "500 MB",
        retention: str = "90 days"
    ):
        """
        Inicializar event logger.
        
        Args:
            log_file: Path al archivo de eventos
            rotation: Criterio de rotación
            retention: Tiempo de retención
        """
        self.log_file = log_file
        
        # Crear directorio si no existe
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Configurar logger específico para eventos
        self.logger = logger.bind(name="events")
        
        # Agregar handler para eventos (formato JSON)
        self.logger.add(
            log_file,
            format="{message}",  # Solo el mensaje (JSON)
            rotation=rotation,
            retention=retention,
            compression="zip",
            filter=lambda record: record["extra"].get("name") == "events"
        )
        
        logger.info(f"EventLogger inicializado: {log_file}")
    
    def _log_event(self, event_type: str, data: Dict[str, Any]):
        """
        Registrar evento genérico.
        
        Args:
            event_type: Tipo de evento
            data: Datos del evento
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            **data
        }
        
        # Convertir a JSON y registrar
        json_str = json.dumps(event, ensure_ascii=False)
        self.logger.info(json_str)
    
    def log_detection(
        self,
        object_id: str,
        camera_id: int,
        bbox: list,
        confidence: float
    ):
        """
        Registrar detección de objeto.
        
        Args:
            object_id: ID del objeto detectado
            camera_id: ID de la cámara
            bbox: Bounding box [x1, y1, x2, y2]
            confidence: Confianza de la detección
        """
        self._log_event("detection", {
            "object_id": object_id,
            "camera_id": camera_id,
            "bbox": bbox,
            "confidence": confidence
        })
    
    def log_behavior(
        self,
        object_id: str,
        behavior: str,
        confidence: float,
        duration: Optional[float] = None
    ):
        """
        Registrar comportamiento detectado.
        
        Args:
            object_id: ID del objeto
            behavior: Nombre del comportamiento
            confidence: Confianza de la predicción
            duration: Duración del comportamiento en segundos (opcional)
        """
        data = {
            "object_id": object_id,
            "behavior": behavior,
            "confidence": confidence
        }
        
        if duration is not None:
            data["duration"] = duration
        
        self._log_event("behavior", data)
    
    def log_interaction(
        self,
        object_id_1: str,
        object_id_2: str,
        interaction_type: str = "proximity",
        distance: Optional[float] = None
    ):
        """
        Registrar interacción entre objetos.
        
        Args:
            object_id_1: ID del primer objeto
            object_id_2: ID del segundo objeto
            interaction_type: Tipo de interacción
            distance: Distancia entre objetos (píxeles)
        """
        data = {
            "object_id_1": object_id_1,
            "object_id_2": object_id_2,
            "interaction_type": interaction_type
        }
        
        if distance is not None:
            data["distance"] = distance
        
        self._log_event("interaction", data)
    
    def log_alert(
        self,
        object_id: str,
        alert_type: str,
        severity: str = "warning",
        details: Optional[Dict] = None
    ):
        """
        Registrar alerta del sistema.
        
        Args:
            object_id: ID del objeto relacionado
            alert_type: Tipo de alerta
            severity: Severidad (info, warning, error, critical)
            details: Detalles adicionales
        """
        data = {
            "object_id": object_id,
            "alert_type": alert_type,
            "severity": severity
        }
        
        if details:
            data["details"] = details
        
        self._log_event("alert", data)
    
    def log_human_detection(
        self,
        camera_id: int,
        bbox: list,
        confidence: float,
        position: tuple,
        size: tuple
    ):
        """
        Registrar detección de humano.
        
        Args:
            camera_id: ID de la cámara donde se detectó
            bbox: Bounding box [x1, y1, x2, y2]
            confidence: Confianza de la detección
            position: Posición central (x, y)
            size: Tamaño del bbox (width, height)
        """
        self._log_event("human_detection", {
            "camera_id": camera_id,
            "bbox": bbox,
            "confidence": confidence,
            "position": {"x": position[0], "y": position[1]},
            "size": {"width": size[0], "height": size[1]},
            "severity": "warning",
            "alert": "Presencia humana detectada en el área de monitoreo"
        })
    
    def log_camera_event(
        self,
        camera_id: int,
        event_type: str,
        status: str,
        details: Optional[Dict] = None
    ):
        """
        Registrar evento de cámara.
        
        Args:
            camera_id: ID de la cámara
            event_type: Tipo de evento (connected, disconnected, error)
            status: Estado de la cámara
            details: Detalles adicionales
        """
        data = {
            "camera_id": camera_id,
            "event_type": event_type,
            "status": status
        }
        
        if details:
            data["details"] = details
        
        self._log_event("camera", data)
    
    def log_system_metric(
        self,
        metric_name: str,
        value: float,
        unit: Optional[str] = None
    ):
        """
        Registrar métrica del sistema.
        
        Args:
            metric_name: Nombre de la métrica
            value: Valor de la métrica
            unit: Unidad (fps, ms, etc.)
        """
        data = {
            "metric_name": metric_name,
            "value": value
        }
        
        if unit:
            data["unit"] = unit
        
        self._log_event("metric", data)
    
    def log_reid_match(
        self,
        object_id: str,
        camera_from: int,
        camera_to: int,
        confidence: float
    ):
        """
        Registrar match de re-identificación entre cámaras.
        
        Args:
            object_id: ID global del objeto
            camera_from: Cámara origen
            camera_to: Cámara destino
            confidence: Confianza del match
        """
        self._log_event("reid_match", {
            "object_id": object_id,
            "camera_from": camera_from,
            "camera_to": camera_to,
            "confidence": confidence
        })


class PerformanceLogger:
    """
    Logger para métricas de rendimiento del sistema.
    
    Rastrea FPS, latencias, uso de memoria, etc.
    """
    
    def __init__(self):
        """Inicializar performance logger."""
        self.metrics: Dict[str, list] = {}
        self.logger = logger.bind(name="performance")
    
    def log_metric(self, name: str, value: float):
        """
        Registrar métrica de rendimiento.
        
        Args:
            name: Nombre de la métrica
            value: Valor
        """
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append(value)
        
        # Mantener solo últimas 1000 muestras
        if len(self.metrics[name]) > 1000:
            self.metrics[name] = self.metrics[name][-1000:]
    
    def get_stats(self, name: str) -> Dict[str, float]:
        """
        Obtener estadísticas de una métrica.
        
        Args:
            name: Nombre de la métrica
            
        Returns:
            Dict con min, max, avg, std
        """
        if name not in self.metrics or not self.metrics[name]:
            return {}
        
        import numpy as np
        
        values = np.array(self.metrics[name])
        
        return {
            "min": float(values.min()),
            "max": float(values.max()),
            "mean": float(values.mean()),
            "std": float(values.std()),
            "count": len(values)
        }
    
    def print_summary(self):
        """Imprimir resumen de todas las métricas."""
        self.logger.info("=== Performance Summary ===")
        
        for name in sorted(self.metrics.keys()):
            stats = self.get_stats(name)
            self.logger.info(
                f"{name}: "
                f"avg={stats['mean']:.2f} "
                f"min={stats['min']:.2f} "
                f"max={stats['max']:.2f} "
                f"std={stats['std']:.2f} "
                f"(n={stats['count']})"
            )


# ==================== EJEMPLO DE USO ====================
if __name__ == "__main__":
    """Ejemplo de uso del sistema de logging."""
    
    # Configurar logger principal
    setup_logger(
        log_file="test_system.log",
        log_level="DEBUG"
    )
    
    logger.info("Test del sistema de logging")
    logger.debug("Mensaje de debug")
    logger.warning("Mensaje de advertencia")
    
    # Event logger
    event_logger = EventLogger("test_events.log")
    
    logger.info("\nRegistrando eventos...")
    
    event_logger.log_detection(
        object_id="F1",
        camera_id=0,
        bbox=[100, 100, 200, 300],
        confidence=0.95
    )
    
    event_logger.log_behavior(
        object_id="F1",
        behavior="playing",
        confidence=0.87,
        duration=15.5
    )
    
    event_logger.log_interaction(
        object_id_1="F1",
        object_id_2="F2",
        interaction_type="playing_together",
        distance=45.3
    )
    
    event_logger.log_alert(
        object_id="F2",
        alert_type="sleeping_too_long",
        severity="warning",
        details={"duration": 3600}
    )
    
    # Performance logger
    perf_logger = PerformanceLogger()
    
    logger.info("\nRegistrando métricas de rendimiento...")
    
    import random
    for _ in range(100):
        perf_logger.log_metric("fps", random.uniform(25, 35))
        perf_logger.log_metric("latency_ms", random.uniform(10, 50))
    
    perf_logger.print_summary()
    
    logger.info("\nTest completado")





