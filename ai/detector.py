"""
Behavior Detector - Detección de hurones usando YOLOv8.

Este módulo utiliza YOLOv8 (ultralytics) para detectar hurones en frames
de video, proporcionando bounding boxes y scores de confianza.

Autor: Sistema de Monitoreo de Hurones
Fecha: 2025-10-28
"""

import cv2
import numpy as np
import torch
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from loguru import logger

# Ultralytics YOLO
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logger.warning("ultralytics no disponible. Instalar con: pip install ultralytics")


@dataclass
class Detection:
    """
    Representa una detección individual.
    
    Attributes:
        bbox: Bounding box [x1, y1, x2, y2]
        confidence: Score de confianza (0-1)
        class_id: ID de la clase detectada
        class_name: Nombre de la clase (ej: "person", "cat", "dog")
        entity_type: Tipo de entidad ("person" o "ferret")
        track_id: ID de tracking (opcional)
        keypoints: Puntos clave si disponibles
    """
    bbox: np.ndarray  # [x1, y1, x2, y2]
    confidence: float
    class_id: int
    class_name: str = "ferret"
    entity_type: str = "ferret"  # "person" o "ferret"
    track_id: Optional[int] = None
    keypoints: Optional[np.ndarray] = None
    
    @property
    def center(self) -> np.ndarray:
        """Centro del bounding box."""
        return np.array([
            (self.bbox[0] + self.bbox[2]) / 2,
            (self.bbox[1] + self.bbox[3]) / 2
        ])
    
    @property
    def width(self) -> float:
        """Ancho del bounding box."""
        return self.bbox[2] - self.bbox[0]
    
    @property
    def height(self) -> float:
        """Alto del bounding box."""
        return self.bbox[3] - self.bbox[1]
    
    @property
    def area(self) -> float:
        """Área del bounding box."""
        return self.width * self.height
    
    def to_dict(self) -> Dict:
        """Convertir a diccionario."""
        return {
            "bbox": self.bbox.tolist(),
            "confidence": float(self.confidence),
            "class_id": int(self.class_id),
            "class_name": self.class_name,
            "entity_type": self.entity_type,
            "track_id": self.track_id,
            "center": self.center.tolist(),
            "area": float(self.area),
        }
    
    def extract_patch(self, frame: np.ndarray, padding: int = 0) -> np.ndarray:
        """
        Extraer patch del frame correspondiente a esta detección.
        
        Args:
            frame: Frame completo
            padding: Píxeles de padding alrededor del bbox
            
        Returns:
            Patch recortado
        """
        h, w = frame.shape[:2]
        
        x1 = int(max(0, self.bbox[0] - padding))
        y1 = int(max(0, self.bbox[1] - padding))
        x2 = int(min(w, self.bbox[2] + padding))
        y2 = int(min(h, self.bbox[3] + padding))
        
        return frame[y1:y2, x1:x2]


class BehaviorDetector:
    """
    Detector de hurones basado en YOLOv8.
    
    Características:
    - Detección en tiempo real
    - Soporte para GPU y CPU
    - Configuración de confianza y NMS
    - Batch processing
    - Tracking integrado (opcional)
    
    Ejemplo:
        >>> detector = BehaviorDetector(model_path="yolov8n.pt")
        >>> detections = detector.detect(frame)
        >>> for det in detections:
        ...     print(f"Hurón detectado con confianza {det.confidence:.2f}")
    """
    
    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        device: Optional[str] = None,
        input_size: int = 640,
        class_names: Optional[List[str]] = None
    ):
        """
        Inicializar el detector.
        
        Args:
            model_path: Path al modelo YOLO (.pt file)
            confidence_threshold: Umbral de confianza mínimo
            iou_threshold: Umbral de IoU para NMS
            device: Dispositivo ('cuda', 'cpu', 'mps' o None=auto)
            input_size: Tamaño de entrada del modelo (640, 1280, etc)
            class_names: Nombres de clases personalizados
        """
        if not YOLO_AVAILABLE:
            raise ImportError(
                "ultralytics no está instalado. "
                "Instalar con: pip install ultralytics"
            )
        
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.input_size = input_size
        self.class_names = class_names or ["ferret"]
        
        # Determinar dispositivo
        if device is None:
            device = self._get_device()
        self.device = device
        
        # Cargar modelo
        logger.info(f"Cargando modelo YOLO desde {model_path}...")
        self.model = YOLO(model_path)
        
        # Configurar dispositivo
        if self.device != 'cpu':
            self.model.to(self.device)
        
        logger.info(
            f"BehaviorDetector inicializado: "
            f"modelo={model_path}, device={self.device}, "
            f"conf={confidence_threshold}, iou={iou_threshold}"
        )
        
        # Estadísticas
        self.stats = {
            "total_frames": 0,
            "total_detections": 0,
            "avg_inference_time": 0.0,
        }
    
    def _get_device(self) -> str:
        """Determinar mejor dispositivo disponible."""
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    def detect(
        self,
        frame: np.ndarray,
        return_raw: bool = False,
        camera_id: int = 0
    ) -> List[Detection]:
        """
        Detectar hurones en un frame.
        
        Args:
            frame: Frame de entrada (numpy array BGR)
            return_raw: Si True, retorna resultados raw de YOLO también
            camera_id: ID de la cámara (para logging)
            
        Returns:
            Lista de detecciones
        """
        import time
        start_time = time.time()
        
        # Inferencia
        results = self.model.predict(
            frame,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            imgsz=self.input_size,
            verbose=False,
            device=self.device
        )
        
        # Procesar resultados
        detections = []
        
        if len(results) > 0:
            result = results[0]  # Primer resultado (un solo frame)
            
            if result.boxes is not None and len(result.boxes) > 0:
                boxes = result.boxes
                
                for i in range(len(boxes)):
                    # Extraer datos
                    bbox = boxes.xyxy[i].cpu().numpy()  # [x1, y1, x2, y2]
                    conf = float(boxes.conf[i].cpu().numpy())
                    cls = int(boxes.cls[i].cpu().numpy())
                    
                    # Nombre de clase
                    class_name = (
                        self.class_names[cls] if cls < len(self.class_names)
                        else f"class_{cls}"
                    )
                    
                    # Filtrar solo las clases que nos interesan
                    from config import config
                    if class_name not in config.DETECTION_CLASSES:
                        continue
                    
                    # Determinar tipo de entidad (person o ferret)
                    entity_type = config.CLASS_TO_ENTITY_TYPE.get(class_name, "ferret")
                    
                    # Crear detección
                    detection = Detection(
                        bbox=bbox,
                        confidence=conf,
                        class_id=cls,
                        class_name=class_name,
                        entity_type=entity_type
                    )
                    
                    # Logging especial para detección de humanos
                    if entity_type == "person":
                        from api.system_bridge import bridge
                        if bridge.event_logger:
                            bridge.event_logger.log_human_detection(
                                camera_id=camera_id,
                                bbox=bbox.tolist(),
                                confidence=conf,
                                position=(float(detection.center[0]), float(detection.center[1])),
                                size=(float(detection.width), float(detection.height))
                            )
                        logger.warning(
                            f"🚨 HUMANO DETECTADO - "
                            f"Cámara: {camera_id}, "
                            f"Confianza: {conf:.2%}, "
                            f"Posición: ({detection.center[0]:.0f}, {detection.center[1]:.0f})"
                        )
                    
                    detections.append(detection)
        
        # Actualizar estadísticas
        inference_time = time.time() - start_time
        self.stats["total_frames"] += 1
        self.stats["total_detections"] += len(detections)
        self.stats["avg_inference_time"] = (
            0.9 * self.stats["avg_inference_time"] + 0.1 * inference_time
        )
        
        if return_raw:
            return detections, results
        
        return detections
    
    def batch_detect(
        self,
        frames: List[np.ndarray]
    ) -> List[List[Detection]]:
        """
        Detectar en múltiples frames (batch processing).
        
        Args:
            frames: Lista de frames
            
        Returns:
            Lista de listas de detecciones
        """
        all_detections = []
        
        # YOLOv8 soporta batch nativo
        results = self.model.predict(
            frames,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            imgsz=self.input_size,
            verbose=False,
            device=self.device
        )
        
        # Procesar cada resultado
        for result in results:
            detections = []
            
            if result.boxes is not None and len(result.boxes) > 0:
                boxes = result.boxes
                
                for i in range(len(boxes)):
                    bbox = boxes.xyxy[i].cpu().numpy()
                    conf = float(boxes.conf[i].cpu().numpy())
                    cls = int(boxes.cls[i].cpu().numpy())
                    
                    class_name = (
                        self.class_names[cls] if cls < len(self.class_names)
                        else f"class_{cls}"
                    )
                    
                    detection = Detection(
                        bbox=bbox,
                        confidence=conf,
                        class_id=cls,
                        class_name=class_name
                    )
                    
                    detections.append(detection)
            
            all_detections.append(detections)
            self.stats["total_frames"] += 1
            self.stats["total_detections"] += len(detections)
        
        return all_detections
    
    def visualize(
        self,
        frame: np.ndarray,
        detections: List[Detection],
        show_confidence: bool = True,
        show_class: bool = True,
        color: Tuple[int, int, int] = (0, 255, 0)
    ) -> np.ndarray:
        """
        Visualizar detecciones en un frame.
        
        Args:
            frame: Frame original
            detections: Lista de detecciones
            show_confidence: Mostrar score de confianza
            show_class: Mostrar nombre de clase
            color: Color BGR del bounding box
            
        Returns:
            Frame con detecciones dibujadas
        """
        vis_frame = frame.copy()
        
        for det in detections:
            # Bounding box
            x1, y1, x2, y2 = det.bbox.astype(int)
            cv2.rectangle(vis_frame, (x1, y1), (x2, y2), color, 2)
            
            # Label
            label_parts = []
            if show_class:
                label_parts.append(det.class_name)
            if show_confidence:
                label_parts.append(f"{det.confidence:.2f}")
            
            if label_parts:
                label = " ".join(label_parts)
                
                # Fondo del texto
                (label_w, label_h), baseline = cv2.getTextSize(
                    label,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    2
                )
                cv2.rectangle(
                    vis_frame,
                    (x1, y1 - label_h - baseline - 5),
                    (x1 + label_w, y1),
                    color,
                    -1
                )
                
                # Texto
                cv2.putText(
                    vis_frame,
                    label,
                    (x1, y1 - baseline - 2),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2
                )
        
        return vis_frame
    
    def get_stats(self) -> Dict:
        """Obtener estadísticas del detector."""
        stats = self.stats.copy()
        
        if stats["total_frames"] > 0:
            stats["avg_detections_per_frame"] = (
                stats["total_detections"] / stats["total_frames"]
            )
            stats["fps"] = 1.0 / stats["avg_inference_time"] if stats["avg_inference_time"] > 0 else 0
        else:
            stats["avg_detections_per_frame"] = 0
            stats["fps"] = 0
        
        return stats
    
    def reset_stats(self):
        """Resetear estadísticas."""
        self.stats = {
            "total_frames": 0,
            "total_detections": 0,
            "avg_inference_time": 0.0,
        }


# ==================== EJEMPLO DE USO ====================
if __name__ == "__main__":
    """Ejemplo de uso del BehaviorDetector."""
    
    from loguru import logger
    import time
    
    # Configurar logging
    logger.add("detector_test.log", rotation="10 MB")
    
    # Crear detector
    detector = BehaviorDetector(
        model_path="yolov8n.pt",  # Modelo nano para testing
        confidence_threshold=0.5,
        device=None  # Auto-detectar
    )
    
    # Test con imagen sintética
    logger.info("Generando frame de prueba...")
    test_frame = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    
    # Detectar
    logger.info("Ejecutando detección...")
    detections = detector.detect(test_frame)
    
    logger.info(f"Detecciones encontradas: {len(detections)}")
    for i, det in enumerate(detections, 1):
        logger.info(f"  {i}. {det.class_name} - confianza: {det.confidence:.2f}")
    
    # Test de rendimiento
    logger.info("\nTest de rendimiento (100 frames)...")
    start = time.time()
    
    for _ in range(100):
        _ = detector.detect(test_frame)
    
    elapsed = time.time() - start
    fps = 100 / elapsed
    
    logger.info(f"Tiempo total: {elapsed:.2f}s")
    logger.info(f"FPS promedio: {fps:.2f}")
    
    # Estadísticas
    stats = detector.get_stats()
    logger.info(f"\nEstadísticas:")
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")
    
    logger.info("\nTest finalizado")





