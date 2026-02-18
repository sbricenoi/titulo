"""
Fusion Engine - Fusión de detecciones multi-cámara.

Este módulo maneja la fusión de detecciones de múltiples cámaras,
eliminación de duplicados, y cálculo de posiciones 3D (opcional).

Autor: Sistema de Monitoreo de Hurones
Fecha: 2025-10-28
"""

import numpy as np
import json
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path
from scipy.optimize import linear_sum_assignment
from filterpy.kalman import KalmanFilter
from loguru import logger


@dataclass
class Detection:
    """Representa una detección individual de una cámara."""
    camera_id: int
    bbox: np.ndarray  # [x1, y1, x2, y2]
    confidence: float
    class_id: int = 0
    features: Optional[np.ndarray] = None  # Features ReID
    timestamp: float = 0.0
    track_id: Optional[int] = None
    
    @property
    def center(self) -> np.ndarray:
        """Centro del bounding box."""
        return np.array([
            (self.bbox[0] + self.bbox[2]) / 2,
            (self.bbox[1] + self.bbox[3]) / 2
        ])
    
    @property
    def area(self) -> float:
        """Área del bounding box."""
        width = self.bbox[2] - self.bbox[0]
        height = self.bbox[3] - self.bbox[1]
        return width * height
    
    def to_dict(self) -> Dict:
        """Convertir a diccionario."""
        return {
            "camera_id": self.camera_id,
            "bbox": self.bbox.tolist(),
            "confidence": float(self.confidence),
            "class_id": self.class_id,
            "track_id": self.track_id,
            "timestamp": self.timestamp,
        }


@dataclass
class FusedObject:
    """Representa un objeto fusionado de múltiples cámaras."""
    global_id: str  # ID único global
    detections: List[Detection] = field(default_factory=list)
    position_3d: Optional[np.ndarray] = None  # Posición 3D [x, y, z]
    confidence: float = 0.0
    timestamp: float = 0.0
    kalman_filter: Optional[KalmanFilter] = None
    
    @property
    def camera_ids(self) -> List[int]:
        """IDs de cámaras que detectaron este objeto."""
        return [det.camera_id for det in self.detections]
    
    @property
    def num_cameras(self) -> int:
        """Número de cámaras que ven este objeto."""
        return len(self.detections)
    
    @property
    def best_detection(self) -> Optional[Detection]:
        """Detección con mayor confianza."""
        if not self.detections:
            return None
        return max(self.detections, key=lambda d: d.confidence)
    
    def get_detection_for_camera(self, camera_id: int) -> Optional[Detection]:
        """Obtener detección de una cámara específica."""
        for det in self.detections:
            if det.camera_id == camera_id:
                return det
        return None
    
    def update_confidence(self):
        """Actualizar confianza basada en detecciones."""
        if not self.detections:
            self.confidence = 0.0
        else:
            # Confianza = promedio ponderado por número de cámaras
            avg_conf = np.mean([d.confidence for d in self.detections])
            camera_bonus = min(self.num_cameras / 4.0, 1.0)  # Bonus por múltiples cámaras
            self.confidence = min(avg_conf * (1.0 + camera_bonus * 0.2), 1.0)
    
    def to_dict(self) -> Dict:
        """Convertir a diccionario."""
        return {
            "global_id": self.global_id,
            "confidence": float(self.confidence),
            "num_cameras": self.num_cameras,
            "camera_ids": self.camera_ids,
            "position_3d": self.position_3d.tolist() if self.position_3d is not None else None,
            "timestamp": self.timestamp,
            "detections": [d.to_dict() for d in self.detections],
        }


class FusionEngine:
    """
    Motor de fusión multi-cámara.
    
    Funcionalidades:
    - Fusión de detecciones de múltiples cámaras
    - Eliminación de duplicados usando features ReID
    - Cálculo de posición 3D (si hay calibración)
    - Tracking temporal con filtros de Kalman
    
    Ejemplo:
        >>> fusion = FusionEngine(feature_weight=0.7)
        >>> detections_per_camera = {0: [det1, det2], 1: [det3]}
        >>> fused_objects = fusion.merge_detections(detections_per_camera)
    """
    
    def __init__(
        self,
        spatial_threshold: float = 0.5,
        feature_weight: float = 0.7,
        enable_3d: bool = False,
        calibration_path: Optional[str] = None,
        time_window_ms: int = 200
    ):
        """
        Inicializar el motor de fusión.
        
        Args:
            spatial_threshold: Umbral para matching espacial (IoU)
            feature_weight: Peso de features vs posición (0-1)
            enable_3d: Activar cálculo de posición 3D
            calibration_path: Path a archivo de calibración
            time_window_ms: Ventana temporal para fusión (ms)
        """
        self.spatial_threshold = spatial_threshold
        self.feature_weight = feature_weight
        self.position_weight = 1.0 - feature_weight
        self.enable_3d = enable_3d
        self.time_window_ms = time_window_ms
        self.time_window_sec = time_window_ms / 1000.0
        
        # Calibración de cámaras (si está disponible)
        self.calibration = None
        if enable_3d and calibration_path:
            self.load_calibration(calibration_path)
        
        # Objetos fusionados activos (tracking temporal)
        self.active_objects: Dict[str, FusedObject] = {}
        self.next_global_id = 0
        
        # Estadísticas
        self.stats = {
            "total_detections": 0,
            "total_fused_objects": 0,
            "duplicates_eliminated": 0,
            "3d_calculations": 0,
        }
        
        logger.info(
            f"FusionEngine inicializado: spatial_threshold={spatial_threshold}, "
            f"feature_weight={feature_weight}, 3D={'enabled' if enable_3d else 'disabled'}"
        )
    
    def load_calibration(self, calibration_path: str):
        """
        Cargar parámetros de calibración de cámaras.
        
        Args:
            calibration_path: Path al archivo JSON de calibración
        """
        try:
            with open(calibration_path, 'r') as f:
                self.calibration = json.load(f)
            logger.info(f"Calibración cargada desde {calibration_path}")
        except Exception as e:
            logger.error(f"Error cargando calibración: {e}")
            self.calibration = None
    
    def calculate_iou(self, bbox1: np.ndarray, bbox2: np.ndarray) -> float:
        """
        Calcular Intersection over Union entre dos bounding boxes.
        
        Args:
            bbox1: [x1, y1, x2, y2]
            bbox2: [x1, y1, x2, y2]
            
        Returns:
            IoU score (0-1)
        """
        # Calcular intersección
        x1 = max(bbox1[0], bbox2[0])
        y1 = max(bbox1[1], bbox2[1])
        x2 = min(bbox1[2], bbox2[2])
        y2 = min(bbox1[3], bbox2[3])
        
        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        
        # Calcular unión
        area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
        area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
        union = area1 + area2 - intersection
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def calculate_feature_distance(
        self,
        features1: Optional[np.ndarray],
        features2: Optional[np.ndarray]
    ) -> float:
        """
        Calcular distancia coseno entre features ReID.
        
        Args:
            features1: Feature vector de detección 1
            features2: Feature vector de detección 2
            
        Returns:
            Distancia coseno (0 = idéntico, 2 = opuesto)
        """
        if features1 is None or features2 is None:
            return 1.0  # Distancia neutral si no hay features
        
        # Normalizar
        f1_norm = features1 / (np.linalg.norm(features1) + 1e-8)
        f2_norm = features2 / (np.linalg.norm(features2) + 1e-8)
        
        # Distancia coseno
        cos_sim = np.dot(f1_norm, f2_norm)
        cos_dist = 1.0 - cos_sim  # Convertir similaridad a distancia
        
        return cos_dist
    
    def calculate_matching_cost(
        self,
        det1: Detection,
        det2: Detection
    ) -> float:
        """
        Calcular costo de matching entre dos detecciones.
        
        Combina distancia espacial (IoU) y distancia de features.
        
        Args:
            det1: Detección 1
            det2: Detección 2
            
        Returns:
            Costo de matching (menor = mejor match)
        """
        # Si son de la misma cámara, no pueden ser el mismo objeto
        if det1.camera_id == det2.camera_id:
            return float('inf')
        
        # Distancia espacial (1 - IoU)
        # Nota: Para cámaras en posiciones muy diferentes, IoU no es útil
        # En su lugar, podríamos usar proyección 3D->2D si hay calibración
        spatial_cost = 1.0  # Costo neutral si no hay calibración
        
        # Distancia de features
        feature_cost = self.calculate_feature_distance(det1.features, det2.features)
        
        # Costo combinado
        total_cost = (
            self.position_weight * spatial_cost +
            self.feature_weight * feature_cost
        )
        
        return total_cost
    
    def build_cost_matrix(
        self,
        detections_list: List[Detection]
    ) -> np.ndarray:
        """
        Construir matriz de costos para matching.
        
        Args:
            detections_list: Lista de todas las detecciones
            
        Returns:
            Matriz de costos NxN
        """
        n = len(detections_list)
        cost_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(i + 1, n):
                cost = self.calculate_matching_cost(
                    detections_list[i],
                    detections_list[j]
                )
                cost_matrix[i, j] = cost
                cost_matrix[j, i] = cost
        
        return cost_matrix
    
    def merge_detections(
        self,
        detections_per_camera: Dict[int, List[Detection]]
    ) -> List[FusedObject]:
        """
        Fusionar detecciones de múltiples cámaras.
        
        Args:
            detections_per_camera: Dict {camera_id: [detections]}
            
        Returns:
            Lista de objetos fusionados
        """
        # Flatten todas las detecciones
        all_detections = []
        for camera_id, detections in detections_per_camera.items():
            all_detections.extend(detections)
            self.stats["total_detections"] += len(detections)
        
        if not all_detections:
            return []
        
        # Si solo hay una detección, retornar directamente
        if len(all_detections) == 1:
            fused_obj = FusedObject(
                global_id=f"F{self.next_global_id}",
                detections=[all_detections[0]],
                timestamp=all_detections[0].timestamp
            )
            fused_obj.update_confidence()
            self.next_global_id += 1
            self.stats["total_fused_objects"] += 1
            return [fused_obj]
        
        # Agrupar detecciones que pertenecen al mismo objeto
        # Estrategia: Usar features ReID para matching
        
        # Construcción de grupos usando matching greedy
        # (Para producción, considerar Hungarian algorithm)
        fused_objects = []
        used_detections = set()
        
        for i, det1 in enumerate(all_detections):
            if i in used_detections:
                continue
            
            # Iniciar nuevo grupo
            group = [det1]
            used_detections.add(i)
            
            # Buscar detecciones similares de otras cámaras
            for j, det2 in enumerate(all_detections):
                if j in used_detections:
                    continue
                
                # Verificar que no sea de la misma cámara
                if det2.camera_id in [d.camera_id for d in group]:
                    continue
                
                # Calcular costo de matching
                cost = self.calculate_matching_cost(det1, det2)
                
                # Si el costo es bajo, agregar al grupo
                if cost < 0.5:  # Umbral de matching
                    group.append(det2)
                    used_detections.add(j)
            
            # Crear objeto fusionado
            fused_obj = FusedObject(
                global_id=f"F{self.next_global_id}",
                detections=group,
                timestamp=np.mean([d.timestamp for d in group])
            )
            fused_obj.update_confidence()
            
            # Calcular posición 3D si está habilitado
            if self.enable_3d and len(group) >= 2:
                fused_obj.position_3d = self.calculate_3d_position(group)
                if fused_obj.position_3d is not None:
                    self.stats["3d_calculations"] += 1
            
            fused_objects.append(fused_obj)
            self.next_global_id += 1
        
        # Estadísticas
        self.stats["total_fused_objects"] += len(fused_objects)
        self.stats["duplicates_eliminated"] += len(all_detections) - len(fused_objects)
        
        return fused_objects
    
    def calculate_3d_position(
        self,
        detections: List[Detection]
    ) -> Optional[np.ndarray]:
        """
        Calcular posición 3D aproximada desde múltiples vistas.
        
        Requiere calibración de cámaras (matrices intrínsecas y extrínsecas).
        
        Args:
            detections: Lista de detecciones del mismo objeto
            
        Returns:
            Posición 3D [x, y, z] o None si no es posible calcular
        """
        if not self.calibration:
            return None
        
        # TODO: Implementar triangulación 3D
        # Esto requiere:
        # 1. Matrices de proyección de cada cámara
        # 2. Correspondencias 2D (centros de bounding boxes)
        # 3. Triangulación usando DLT o método similar
        
        # Por ahora, retornar None (implementación futura)
        logger.debug("Cálculo 3D no implementado aún")
        return None
    
    def eliminate_duplicates(
        self,
        fused_objects: List[FusedObject]
    ) -> List[FusedObject]:
        """
        Eliminar objetos duplicados.
        
        Args:
            fused_objects: Lista de objetos fusionados
            
        Returns:
            Lista sin duplicados
        """
        if len(fused_objects) <= 1:
            return fused_objects
        
        # Construir matriz de similaridad
        n = len(fused_objects)
        similarity_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(i + 1, n):
                # Calcular similaridad basada en detecciones compartidas
                cameras_i = set(fused_objects[i].camera_ids)
                cameras_j = set(fused_objects[j].camera_ids)
                
                # Si comparten cámaras, probablemente son duplicados
                overlap = len(cameras_i & cameras_j)
                total = len(cameras_i | cameras_j)
                
                if total > 0:
                    similarity = overlap / total
                    similarity_matrix[i, j] = similarity
                    similarity_matrix[j, i] = similarity
        
        # Marcar duplicados para eliminación
        to_remove = set()
        for i in range(n):
            if i in to_remove:
                continue
            for j in range(i + 1, n):
                if j in to_remove:
                    continue
                
                # Si similaridad > 0.5, son duplicados
                if similarity_matrix[i, j] > 0.5:
                    # Mantener el que tiene más cámaras o mayor confianza
                    if (fused_objects[i].num_cameras > fused_objects[j].num_cameras or
                        (fused_objects[i].num_cameras == fused_objects[j].num_cameras and
                         fused_objects[i].confidence > fused_objects[j].confidence)):
                        to_remove.add(j)
                    else:
                        to_remove.add(i)
        
        # Filtrar objetos a eliminar
        unique_objects = [
            obj for i, obj in enumerate(fused_objects)
            if i not in to_remove
        ]
        
        if to_remove:
            logger.debug(f"Eliminados {len(to_remove)} objetos duplicados")
        
        return unique_objects
    
    def get_stats(self) -> Dict:
        """Obtener estadísticas del motor de fusión."""
        return self.stats.copy()
    
    def reset_stats(self):
        """Resetear estadísticas."""
        self.stats = {
            "total_detections": 0,
            "total_fused_objects": 0,
            "duplicates_eliminated": 0,
            "3d_calculations": 0,
        }


# ==================== EJEMPLO DE USO ====================
if __name__ == "__main__":
    """Ejemplo de uso del FusionEngine."""
    
    from loguru import logger
    
    # Configurar logging
    logger.add("fusion_engine_test.log", rotation="10 MB")
    
    # Crear fusion engine
    fusion = FusionEngine(
        spatial_threshold=0.5,
        feature_weight=0.7,
        enable_3d=False
    )
    
    # Simular detecciones de 2 cámaras
    logger.info("Simulando detecciones...")
    
    # Cámara 0: detecta 2 hurones
    det1_cam0 = Detection(
        camera_id=0,
        bbox=np.array([100, 100, 200, 300]),
        confidence=0.9,
        features=np.random.randn(512),  # Features simuladas
        timestamp=1.0
    )
    
    det2_cam0 = Detection(
        camera_id=0,
        bbox=np.array([400, 200, 500, 400]),
        confidence=0.85,
        features=np.random.randn(512),
        timestamp=1.0
    )
    
    # Cámara 1: detecta los mismos 2 hurones (con features similares)
    det1_cam1 = Detection(
        camera_id=1,
        bbox=np.array([150, 120, 250, 320]),
        confidence=0.88,
        features=det1_cam0.features + np.random.randn(512) * 0.1,  # Similar a det1_cam0
        timestamp=1.01
    )
    
    det2_cam1 = Detection(
        camera_id=1,
        bbox=np.array([380, 180, 480, 380]),
        confidence=0.82,
        features=det2_cam0.features + np.random.randn(512) * 0.1,  # Similar a det2_cam0
        timestamp=1.01
    )
    
    detections_per_camera = {
        0: [det1_cam0, det2_cam0],
        1: [det1_cam1, det2_cam1]
    }
    
    # Fusionar detecciones
    fused_objects = fusion.merge_detections(detections_per_camera)
    
    logger.info(f"\nResultados de fusión:")
    logger.info(f"  Detecciones totales: 4")
    logger.info(f"  Objetos fusionados: {len(fused_objects)}")
    
    for obj in fused_objects:
        logger.info(f"\n  Objeto {obj.global_id}:")
        logger.info(f"    - Confianza: {obj.confidence:.2f}")
        logger.info(f"    - Cámaras: {obj.camera_ids}")
        logger.info(f"    - Detecciones: {obj.num_cameras}")
    
    # Mostrar estadísticas
    stats = fusion.get_stats()
    logger.info(f"\nEstadísticas:")
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")
    
    logger.info("\nTest finalizado")





