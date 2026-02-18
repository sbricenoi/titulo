"""
Multi-Camera Tracker - Tracking y re-identificación multi-cámara.

Este módulo implementa tracking de hurones dentro de cada cámara
y re-identificación entre cámaras para mantener IDs únicos globales.

Autor: Sistema de Monitoreo de Hurones
Fecha: 2025-10-28
"""

import numpy as np
import cv2
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque, defaultdict
from loguru import logger

# Deep SORT (opcional)
try:
    from deep_sort_realtime.deepsort_tracker import DeepSort
    DEEPSORT_AVAILABLE = True
except ImportError:
    DEEPSORT_AVAILABLE = False
    logger.warning("deep-sort-realtime no disponible. Usando tracker simple.")


@dataclass
class TrackedObject:
    """
    Representa un objeto tracked con ID único.
    
    Attributes:
        global_id: ID único global (across cámaras)
        local_id: ID local dentro de una cámara
        camera_id: ID de la cámara
        bbox: Bounding box [x1, y1, x2, y2]
        confidence: Confianza de la detección
        entity_type: Tipo de entidad ("ferret" o "person")
        features: Feature vector para ReID
        trajectory: Historia de posiciones
        age: Edad del track (frames)
        time_since_update: Frames desde última actualización
        state: Estado del track ('tentative', 'confirmed', 'deleted')
    """
    global_id: str
    local_id: int
    camera_id: int
    bbox: np.ndarray
    confidence: float
    entity_type: str = "ferret"  # "ferret" o "person"
    features: Optional[np.ndarray] = None
    trajectory: deque = field(default_factory=lambda: deque(maxlen=50))
    age: int = 0
    time_since_update: int = 0
    state: str = "tentative"  # tentative, confirmed, deleted
    class_id: int = 0
    
    def __post_init__(self):
        """Inicializar trayectoria con posición actual."""
        self.trajectory.append(self.center)
    
    @property
    def center(self) -> np.ndarray:
        """Centro del bounding box."""
        return np.array([
            (self.bbox[0] + self.bbox[2]) / 2,
            (self.bbox[1] + self.bbox[3]) / 2
        ])
    
    @property
    def is_confirmed(self) -> bool:
        """Si el track está confirmado."""
        return self.state == "confirmed"
    
    def update(self, bbox: np.ndarray, confidence: float, features: Optional[np.ndarray] = None):
        """Actualizar track con nueva detección."""
        self.bbox = bbox
        self.confidence = confidence
        if features is not None:
            self.features = features
        self.trajectory.append(self.center)
        self.time_since_update = 0
        self.age += 1
        
        # Confirmar track después de varias actualizaciones
        if self.age >= 3 and self.state == "tentative":
            self.state = "confirmed"
    
    def mark_missed(self):
        """Marcar que no se detectó en este frame."""
        self.time_since_update += 1
        self.age += 1
    
    def to_dict(self) -> Dict:
        """Convertir a diccionario."""
        return {
            "global_id": self.global_id,
            "local_id": self.local_id,
            "camera_id": self.camera_id,
            "bbox": self.bbox.tolist(),
            "confidence": float(self.confidence),
            "center": self.center.tolist(),
            "age": self.age,
            "time_since_update": self.time_since_update,
            "state": self.state,
            "trajectory_length": len(self.trajectory),
        }


class SimpleTracker:
    """
    Tracker simple basado en IoU (fallback si DeepSORT no está disponible).
    
    Utiliza Intersection over Union para asociar detecciones entre frames.
    """
    
    def __init__(
        self,
        max_age: int = 30,
        min_hits: int = 3,
        iou_threshold: float = 0.3
    ):
        """
        Inicializar tracker simple.
        
        Args:
            max_age: Frames máximos sin detección antes de eliminar
            min_hits: Detecciones mínimas para confirmar track
            iou_threshold: Umbral de IoU para asociación
        """
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        
        self.tracks: List[TrackedObject] = []
        self.next_id = 0
    
    def calculate_iou(self, bbox1: np.ndarray, bbox2: np.ndarray) -> float:
        """Calcular IoU entre dos bounding boxes."""
        x1 = max(bbox1[0], bbox2[0])
        y1 = max(bbox1[1], bbox2[1])
        x2 = min(bbox1[2], bbox2[2])
        y2 = min(bbox1[3], bbox2[3])
        
        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
        area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def update(
        self,
        detections: List[Tuple[np.ndarray, float, Optional[np.ndarray]]]
    ) -> List[TrackedObject]:
        """
        Actualizar tracks con nuevas detecciones.
        
        Args:
            detections: Lista de (bbox, confidence, features)
            
        Returns:
            Lista de tracks actualizados
        """
        # Asociar detecciones con tracks existentes
        if len(self.tracks) == 0:
            # No hay tracks, crear nuevos para todas las detecciones
            for bbox, conf, features in detections:
                track = TrackedObject(
                    global_id=f"T{self.next_id}",
                    local_id=self.next_id,
                    camera_id=0,
                    bbox=bbox,
                    confidence=conf,
                    features=features
                )
                self.tracks.append(track)
                self.next_id += 1
        else:
            # Asociar usando IoU
            matched_tracks = set()
            matched_detections = set()
            
            # Calcular matriz de IoU
            iou_matrix = np.zeros((len(self.tracks), len(detections)))
            for i, track in enumerate(self.tracks):
                for j, (bbox, _, _) in enumerate(detections):
                    iou_matrix[i, j] = self.calculate_iou(track.bbox, bbox)
            
            # Matching greedy
            while True:
                max_iou = iou_matrix.max()
                if max_iou < self.iou_threshold:
                    break
                
                i, j = np.unravel_index(iou_matrix.argmax(), iou_matrix.shape)
                
                # Actualizar track
                bbox, conf, features = detections[j]
                self.tracks[i].update(bbox, conf, features)
                
                matched_tracks.add(i)
                matched_detections.add(j)
                
                # Eliminar de la matriz
                iou_matrix[i, :] = -1
                iou_matrix[:, j] = -1
            
            # Tracks no matched - marcar como missed
            for i, track in enumerate(self.tracks):
                if i not in matched_tracks:
                    track.mark_missed()
            
            # Detecciones no matched - crear nuevos tracks
            for j, (bbox, conf, features) in enumerate(detections):
                if j not in matched_detections:
                    track = TrackedObject(
                        global_id=f"T{self.next_id}",
                        local_id=self.next_id,
                        camera_id=0,
                        bbox=bbox,
                        confidence=conf,
                        features=features
                    )
                    self.tracks.append(track)
                    self.next_id += 1
        
        # Eliminar tracks viejos
        self.tracks = [
            t for t in self.tracks
            if t.time_since_update < self.max_age
        ]
        
        # Retornar solo tracks confirmados
        confirmed_tracks = [
            t for t in self.tracks
            if t.age >= self.min_hits
        ]
        
        return confirmed_tracks


class MultiCameraTracker:
    """
    Tracker multi-cámara con re-identificación.
    
    Mantiene tracks independientes por cámara y utiliza features ReID
    para asignar IDs globales únicos cuando objetos se mueven entre cámaras.
    
    Ejemplo:
        >>> tracker = MultiCameraTracker()
        >>> detections_per_camera = {0: [...], 1: [...]}
        >>> tracked_objects = tracker.update(detections_per_camera)
    """
    
    def __init__(
        self,
        max_age: int = 30,
        min_hits: int = 3,
        reid_threshold: float = 0.7,
        use_deepsort: bool = True
    ):
        """
        Inicializar tracker multi-cámara.
        
        Args:
            max_age: Frames sin detección antes de eliminar
            min_hits: Detecciones mínimas para confirmar
            reid_threshold: Umbral para matching ReID
            use_deepsort: Usar DeepSORT si está disponible
        """
        self.max_age = max_age
        self.min_hits = min_hits
        self.reid_threshold = reid_threshold
        self.use_deepsort = use_deepsort and DEEPSORT_AVAILABLE
        
        # Trackers por cámara
        self.trackers: Dict[int, Any] = {}
        
        # Mapeo de local_id -> global_id por cámara
        self.local_to_global: Dict[int, Dict[int, str]] = defaultdict(dict)
        
        # Base de datos de features por global_id
        self.global_features: Dict[str, np.ndarray] = {}
        
        # Próximo ID global
        self.next_global_id = 0
        
        # Estadísticas
        self.stats = {
            "total_tracks": 0,
            "active_global_ids": 0,
            "reid_matches": 0,
            "new_ids_created": 0,
        }
        
        logger.info(
            f"MultiCameraTracker inicializado: "
            f"backend={'DeepSORT' if self.use_deepsort else 'SimpleTracker'}"
        )
    
    def _get_or_create_tracker(self, camera_id: int):
        """Obtener o crear tracker para una cámara."""
        if camera_id not in self.trackers:
            if self.use_deepsort:
                self.trackers[camera_id] = DeepSort(
                    max_age=self.max_age,
                    n_init=self.min_hits,
                    nms_max_overlap=0.3,
                    max_cosine_distance=0.2,
                    nn_budget=100,
                    embedder="mobilenet",  # Usar MobileNet para ReID
                    embedder_gpu=True
                )
            else:
                self.trackers[camera_id] = SimpleTracker(
                    max_age=self.max_age,
                    min_hits=self.min_hits
                )
            
            logger.debug(f"Tracker creado para cámara {camera_id}")
        
        return self.trackers[camera_id]
    
    def _calculate_feature_similarity(
        self,
        features1: np.ndarray,
        features2: np.ndarray
    ) -> float:
        """Calcular similaridad coseno entre features."""
        f1_norm = features1 / (np.linalg.norm(features1) + 1e-8)
        f2_norm = features2 / (np.linalg.norm(features2) + 1e-8)
        return float(np.dot(f1_norm, f2_norm))
    
    def _assign_global_id(
        self,
        local_id: int,
        camera_id: int,
        features: Optional[np.ndarray]
    ) -> str:
        """
        Asignar ID global a un track local usando ReID.
        
        Args:
            local_id: ID local del track
            camera_id: ID de la cámara
            features: Features para ReID
            
        Returns:
            ID global asignado
        """
        # Si ya tiene ID global, retornar
        if local_id in self.local_to_global[camera_id]:
            return self.local_to_global[camera_id][local_id]
        
        # Si no hay features, crear nuevo ID
        if features is None or len(self.global_features) == 0:
            global_id = f"F{self.next_global_id}"
            self.next_global_id += 1
            self.local_to_global[camera_id][local_id] = global_id
            if features is not None:
                self.global_features[global_id] = features
            self.stats["new_ids_created"] += 1
            return global_id
        
        # Buscar match con IDs globales existentes
        best_match_id = None
        best_similarity = 0.0
        
        for global_id, global_features in self.global_features.items():
            similarity = self._calculate_feature_similarity(features, global_features)
            
            if similarity > best_similarity and similarity > self.reid_threshold:
                best_similarity = similarity
                best_match_id = global_id
        
        # Si encontró match, usar ese ID
        if best_match_id is not None:
            self.local_to_global[camera_id][local_id] = best_match_id
            # Actualizar features (promedio ponderado)
            self.global_features[best_match_id] = (
                0.7 * self.global_features[best_match_id] + 0.3 * features
            )
            self.stats["reid_matches"] += 1
            logger.debug(
                f"ReID match: camera {camera_id} local {local_id} -> "
                f"global {best_match_id} (sim={best_similarity:.2f})"
            )
            return best_match_id
        
        # No hay match, crear nuevo ID global
        global_id = f"F{self.next_global_id}"
        self.next_global_id += 1
        self.local_to_global[camera_id][local_id] = global_id
        self.global_features[global_id] = features
        self.stats["new_ids_created"] += 1
        
        return global_id
    
    def update(
        self,
        detections_per_camera: Dict[int, List],
        frames_per_camera: Dict[int, np.ndarray] = None
    ) -> List[TrackedObject]:
        """
        Actualizar tracks con detecciones de múltiples cámaras.
        
        Args:
            detections_per_camera: Dict {camera_id: [Detection objects]}
            frames_per_camera: Dict {camera_id: frame} (opcional, para DeepSORT)
            
        Returns:
            Lista de objetos tracked con IDs globales
        """
        all_tracked_objects = []
        
        for camera_id, detections in detections_per_camera.items():
            if not detections:
                continue
            
            # Obtener tracker para esta cámara
            tracker = self._get_or_create_tracker(camera_id)
            
            # Preparar detecciones para el tracker
            if self.use_deepsort:
                # DeepSORT espera: [[bbox, confidence], ...]
                # y opcionalmente extrae features automáticamente
                det_list = []
                entity_types = []  # Mantener entity_type paralelo a det_list
                for det in detections:
                    bbox_ltwh = [
                        det.bbox[0],  # left
                        det.bbox[1],  # top
                        det.bbox[2] - det.bbox[0],  # width
                        det.bbox[3] - det.bbox[1]   # height
                    ]
                    det_list.append((bbox_ltwh, det.confidence, None))
                    entity_types.append(det.entity_type)
                
                # Obtener frame para esta cámara (si está disponible)
                frame = frames_per_camera.get(camera_id) if frames_per_camera else None
                
                # Actualizar tracker con frame para extraer features
                tracks = tracker.update_tracks(det_list, frame=frame)
                
                # Convertir a TrackedObject
                for idx, track in enumerate(tracks):
                    if not track.is_confirmed():
                        continue
                    
                    bbox = track.to_ltrb()  # [x1, y1, x2, y2]
                    local_id = track.track_id
                    
                    # Obtener entity_type (usar primera detección si no hay mapeo perfecto)
                    entity_type = entity_types[idx] if idx < len(entity_types) else "ferret"
                    
                    # Asignar ID global (sin features por ahora)
                    global_id = self._assign_global_id(
                        local_id, camera_id, None
                    )
                    
                    tracked_obj = TrackedObject(
                        global_id=global_id,
                        local_id=local_id,
                        camera_id=camera_id,
                        bbox=np.array(bbox),
                        confidence=0.9,  # DeepSORT no retorna confidence
                        entity_type=entity_type,
                        features=None,
                        age=track.age,
                        state="confirmed"
                    )
                    
                    all_tracked_objects.append(tracked_obj)
            else:
                # Tracker simple
                det_list = [
                    (det.bbox, det.confidence, None)
                    for det in detections
                ]
                entity_types = [det.entity_type for det in detections]
                
                tracks = tracker.update(det_list)
                
                # Asignar IDs globales y entity_type
                for idx, track in enumerate(tracks):
                    global_id = self._assign_global_id(
                        track.local_id, camera_id, track.features
                    )
                    track.global_id = global_id
                    track.camera_id = camera_id
                    # Asignar entity_type desde la detección original
                    if idx < len(entity_types):
                        track.entity_type = entity_types[idx]
                    
                    all_tracked_objects.append(track)
        
        # Actualizar estadísticas
        self.stats["total_tracks"] = len(all_tracked_objects)
        self.stats["active_global_ids"] = len(set(
            obj.global_id for obj in all_tracked_objects
        ))
        
        return all_tracked_objects
    
    def get_global_id(self, local_id: int, camera_id: int) -> Optional[str]:
        """
        Obtener ID global de un track local.
        
        Args:
            local_id: ID local del track
            camera_id: ID de la cámara
            
        Returns:
            ID global o None
        """
        return self.local_to_global[camera_id].get(local_id)
    
    def get_stats(self) -> Dict:
        """Obtener estadísticas del tracker."""
        return self.stats.copy()
    
    def reset(self):
        """Resetear todos los trackers."""
        self.trackers.clear()
        self.local_to_global.clear()
        self.global_features.clear()
        self.next_global_id = 0
        logger.info("MultiCameraTracker reseteado")


# ==================== EJEMPLO DE USO ====================
if __name__ == "__main__":
    """Ejemplo de uso del MultiCameraTracker."""
    
    from ai.detector import Detection
    
    # Configurar logging
    logger.add("tracker_test.log", rotation="10 MB")
    
    # Crear tracker
    tracker = MultiCameraTracker(
        max_age=30,
        min_hits=3,
        use_deepsort=False  # Usar tracker simple para testing
    )
    
    logger.info("Simulando detecciones...")
    
    # Simular 10 frames de 2 cámaras
    for frame_num in range(10):
        # Detecciones simuladas
        detections_per_camera = {}
        
        # Cámara 0: 2 hurones
        detections_per_camera[0] = [
            Detection(
                bbox=np.array([100 + frame_num*10, 100, 200, 300]),
                confidence=0.9,
                class_id=0,
                class_name="ferret"
            ),
            Detection(
                bbox=np.array([400, 200 + frame_num*5, 500, 400]),
                confidence=0.85,
                class_id=0,
                class_name="ferret"
            )
        ]
        
        # Cámara 1: 1 hurón (mismo que primero de cámara 0)
        detections_per_camera[1] = [
            Detection(
                bbox=np.array([150 + frame_num*10, 120, 250, 320]),
                confidence=0.88,
                class_id=0,
                class_name="ferret"
            )
        ]
        
        # Actualizar tracker
        tracked_objects = tracker.update(detections_per_camera)
        
        logger.info(f"\nFrame {frame_num}:")
        logger.info(f"  Objetos tracked: {len(tracked_objects)}")
        
        for obj in tracked_objects:
            logger.info(
                f"    {obj.global_id} (local:{obj.local_id}, cam:{obj.camera_id}) "
                f"- conf:{obj.confidence:.2f}"
            )
    
    # Estadísticas
    stats = tracker.get_stats()
    logger.info(f"\nEstadísticas finales:")
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")
    
    logger.info("\nTest finalizado")



