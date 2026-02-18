"""
Visualizer - Visualización de detecciones y tracking.

Este módulo proporciona herramientas para visualizar resultados del sistema
en tiempo real, incluyendo bounding boxes, IDs, trayectorias y comportamientos.

Autor: Sistema de Monitoreo de Hurones
Fecha: 2025-10-28
"""

import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
from collections import deque, defaultdict
from loguru import logger


class Visualizer:
    """
    Visualizador de detecciones y tracking multi-cámara.
    
    Características:
    - Bounding boxes con IDs
    - Trayectorias de movimiento
    - Labels de comportamiento
    - Mosaico de múltiples cámaras
    - Overlay de información del sistema
    
    Ejemplo:
        >>> viz = Visualizer(show_trajectories=True)
        >>> viz.draw_detections(frame, tracked_objects)
        >>> mosaic = viz.create_mosaic(frames_per_camera)
    """
    
    def __init__(
        self,
        show_ids: bool = True,
        show_confidence: bool = True,
        show_behavior: bool = True,
        show_trajectories: bool = True,
        trajectory_length: int = 50,
        colors: Optional[List[Tuple[int, int, int]]] = None
    ):
        """
        Inicializar visualizador.
        
        Args:
            show_ids: Mostrar IDs de objetos
            show_confidence: Mostrar confianza
            show_behavior: Mostrar comportamiento
            show_trajectories: Mostrar trayectorias
            trajectory_length: Longitud de trayectorias (frames)
            colors: Lista de colores BGR para diferentes IDs
        """
        self.show_ids = show_ids
        self.show_confidence = show_confidence
        self.show_behavior = show_behavior
        self.show_trajectories = show_trajectories
        self.trajectory_length = trajectory_length
        
        # Colores por defecto
        self.colors = colors or [
            (255, 0, 0),      # Azul
            (0, 255, 0),      # Verde
            (0, 0, 255),      # Rojo
            (255, 255, 0),    # Cyan
            (255, 0, 255),    # Magenta
            (0, 255, 255),    # Amarillo
            (128, 0, 128),    # Púrpura
            (255, 165, 0),    # Naranja
            (0, 128, 128),    # Teal
            (128, 128, 0),    # Oliva
        ]
        
        # Historial de trayectorias por ID
        self.trajectories: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=trajectory_length)
        )
        
        # Mapeo de ID a color
        self.id_to_color: Dict[str, Tuple[int, int, int]] = {}
        self.next_color_idx = 0
    
    def _get_color_for_id(self, object_id: str) -> Tuple[int, int, int]:
        """Obtener color consistente para un ID."""
        if object_id not in self.id_to_color:
            self.id_to_color[object_id] = self.colors[
                self.next_color_idx % len(self.colors)
            ]
            self.next_color_idx += 1
        
        return self.id_to_color[object_id]
    
    def draw_bbox(
        self,
        frame: np.ndarray,
        bbox: np.ndarray,
        color: Tuple[int, int, int],
        thickness: int = 2
    ):
        """
        Dibujar bounding box.
        
        Args:
            frame: Frame donde dibujar
            bbox: [x1, y1, x2, y2]
            color: Color BGR
            thickness: Grosor de la línea
        """
        x1, y1, x2, y2 = bbox.astype(int)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
    
    def draw_label(
        self,
        frame: np.ndarray,
        text: str,
        position: Tuple[int, int],
        bg_color: Tuple[int, int, int],
        text_color: Tuple[int, int, int] = (255, 255, 255),
        font_scale: float = 0.6,
        thickness: int = 2
    ):
        """
        Dibujar label con fondo.
        
        Args:
            frame: Frame donde dibujar
            text: Texto a mostrar
            position: Posición (x, y)
            bg_color: Color de fondo BGR
            text_color: Color del texto BGR
            font_scale: Escala de la fuente
            thickness: Grosor del texto
        """
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Calcular tamaño del texto
        (text_w, text_h), baseline = cv2.getTextSize(
            text, font, font_scale, thickness
        )
        
        x, y = position
        
        # Dibujar fondo
        cv2.rectangle(
            frame,
            (x, y - text_h - baseline - 5),
            (x + text_w + 5, y),
            bg_color,
            -1
        )
        
        # Dibujar texto
        cv2.putText(
            frame,
            text,
            (x + 2, y - baseline - 2),
            font,
            font_scale,
            text_color,
            thickness
        )
    
    def draw_trajectory(
        self,
        frame: np.ndarray,
        trajectory: deque,
        color: Tuple[int, int, int],
        thickness: int = 2
    ):
        """
        Dibujar trayectoria de movimiento.
        
        Args:
            frame: Frame donde dibujar
            trajectory: Deque de posiciones [(x, y), ...]
            color: Color BGR
            thickness: Grosor de la línea
        """
        if len(trajectory) < 2:
            return
        
        # Dibujar líneas conectando posiciones
        points = np.array(trajectory, dtype=np.int32)
        
        for i in range(len(points) - 1):
            # Alpha blending para efecto de fade
            alpha = (i + 1) / len(points)
            line_color = tuple(int(c * alpha) for c in color)
            
            cv2.line(
                frame,
                tuple(points[i]),
                tuple(points[i + 1]),
                line_color,
                thickness
            )
        
        # Dibujar punto actual
        if len(points) > 0:
            cv2.circle(frame, tuple(points[-1]), 4, color, -1)
    
    def draw_detections(
        self,
        frame: np.ndarray,
        tracked_objects: List,
        behaviors: Optional[Dict[str, str]] = None
    ) -> np.ndarray:
        """
        Dibujar detecciones tracked en un frame.
        
        Args:
            frame: Frame original
            tracked_objects: Lista de TrackedObject
            behaviors: Dict {object_id: behavior_name} (opcional)
            
        Returns:
            Frame con visualizaciones
        """
        vis_frame = frame.copy()
        
        for obj in tracked_objects:
            # Color para este ID
            color = self._get_color_for_id(obj.global_id)
            
            # Bounding box
            self.draw_bbox(vis_frame, obj.bbox, color)
            
            # Label
            label_parts = []
            
            if self.show_ids:
                label_parts.append(f"ID:{obj.global_id}")
            
            if self.show_confidence:
                label_parts.append(f"{obj.confidence:.2f}")
            
            if self.show_behavior and behaviors and obj.global_id in behaviors:
                label_parts.append(behaviors[obj.global_id])
            
            if label_parts:
                label = " | ".join(label_parts)
                x1, y1 = obj.bbox[:2].astype(int)
                self.draw_label(vis_frame, label, (x1, y1), color)
            
            # Trayectoria
            if self.show_trajectories:
                # Actualizar historial
                self.trajectories[obj.global_id].append(tuple(obj.center.astype(int)))
                
                # Dibujar
                self.draw_trajectory(
                    vis_frame,
                    self.trajectories[obj.global_id],
                    color
                )
        
        return vis_frame
    
    def create_mosaic(
        self,
        frames_per_camera: Dict[int, np.ndarray],
        camera_names: Optional[Dict[int, str]] = None,
        grid_cols: int = 2
    ) -> np.ndarray:
        """
        Crear mosaico de múltiples cámaras.
        
        Args:
            frames_per_camera: Dict {camera_id: frame}
            camera_names: Dict {camera_id: name} (opcional)
            grid_cols: Número de columnas en el grid
            
        Returns:
            Frame mosaico
        """
        if not frames_per_camera:
            return np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Obtener dimensiones
        camera_ids = sorted(frames_per_camera.keys())
        num_cameras = len(camera_ids)
        
        # Calcular grid
        grid_rows = (num_cameras + grid_cols - 1) // grid_cols
        
        # Redimensionar frames al mismo tamaño
        target_size = (640, 480)  # width, height
        resized_frames = []
        
        for camera_id in camera_ids:
            frame = frames_per_camera[camera_id]
            resized = cv2.resize(frame, target_size)
            
            # Agregar nombre de cámara
            if camera_names and camera_id in camera_names:
                name = camera_names[camera_id]
                self.draw_label(
                    resized,
                    name,
                    (10, 30),
                    (0, 0, 0),
                    (255, 255, 255),
                    font_scale=0.8
                )
            
            resized_frames.append(resized)
        
        # Rellenar con frames negros si es necesario
        total_slots = grid_rows * grid_cols
        while len(resized_frames) < total_slots:
            blank = np.zeros((target_size[1], target_size[0], 3), dtype=np.uint8)
            resized_frames.append(blank)
        
        # Crear grid
        rows = []
        for i in range(grid_rows):
            row_frames = resized_frames[i * grid_cols:(i + 1) * grid_cols]
            row = np.hstack(row_frames)
            rows.append(row)
        
        mosaic = np.vstack(rows)
        
        return mosaic
    
    def draw_info_overlay(
        self,
        frame: np.ndarray,
        info: Dict[str, any],
        position: Tuple[int, int] = (10, 30)
    ) -> np.ndarray:
        """
        Dibujar overlay de información del sistema.
        
        Args:
            frame: Frame donde dibujar
            info: Diccionario con información a mostrar
            position: Posición inicial (x, y)
            
        Returns:
            Frame con overlay
        """
        vis_frame = frame.copy()
        x, y = position
        line_height = 25
        
        # Fondo semi-transparente
        overlay = vis_frame.copy()
        cv2.rectangle(
            overlay,
            (x - 5, y - 20),
            (x + 400, y + len(info) * line_height + 5),
            (0, 0, 0),
            -1
        )
        cv2.addWeighted(overlay, 0.6, vis_frame, 0.4, 0, vis_frame)
        
        # Dibujar información
        for key, value in info.items():
            text = f"{key}: {value}"
            cv2.putText(
                vis_frame,
                text,
                (x, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )
            y += line_height
        
        return vis_frame
    
    def draw_heatmap(
        self,
        frame_shape: Tuple[int, int],
        positions: List[Tuple[int, int]],
        sigma: int = 50
    ) -> np.ndarray:
        """
        Generar heatmap de posiciones (densidad de actividad).
        
        Args:
            frame_shape: (height, width)
            positions: Lista de posiciones (x, y)
            sigma: Sigma del Gaussian blur
            
        Returns:
            Heatmap como imagen BGR
        """
        h, w = frame_shape
        heatmap = np.zeros((h, w), dtype=np.float32)
        
        # Acumular posiciones
        for x, y in positions:
            if 0 <= x < w and 0 <= y < h:
                heatmap[int(y), int(x)] += 1
        
        # Blur para suavizar
        if sigma > 0:
            heatmap = cv2.GaussianBlur(heatmap, (0, 0), sigma)
        
        # Normalizar
        if heatmap.max() > 0:
            heatmap = heatmap / heatmap.max()
        
        # Convertir a color (jet colormap)
        heatmap_uint8 = (heatmap * 255).astype(np.uint8)
        heatmap_color = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
        
        return heatmap_color
    
    def reset_trajectories(self):
        """Limpiar historial de trayectorias."""
        self.trajectories.clear()
    
    def remove_trajectory(self, object_id: str):
        """Eliminar trayectoria de un objeto específico."""
        if object_id in self.trajectories:
            del self.trajectories[object_id]
        if object_id in self.id_to_color:
            del self.id_to_color[object_id]


# ==================== EJEMPLO DE USO ====================
if __name__ == "__main__":
    """Ejemplo de uso del Visualizer."""
    
    from dataclasses import dataclass
    import time
    
    @dataclass
    class MockTrackedObject:
        """Mock de TrackedObject para testing."""
        global_id: str
        bbox: np.ndarray
        confidence: float
        center: np.ndarray
    
    # Crear visualizador
    viz = Visualizer(
        show_ids=True,
        show_confidence=True,
        show_trajectories=True
    )
    
    logger.info("Generando visualización de prueba...")
    
    # Frame de prueba
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Simular objetos tracked en movimiento
    for i in range(100):
        # Frame negro
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Crear objetos simulados
        tracked_objects = []
        
        for j in range(2):
            # Movimiento circular
            angle = (i + j * 50) * 0.05
            x = int(320 + 150 * np.cos(angle))
            y = int(240 + 150 * np.sin(angle))
            
            obj = MockTrackedObject(
                global_id=f"F{j}",
                bbox=np.array([x - 30, y - 30, x + 30, y + 30]),
                confidence=0.9,
                center=np.array([x, y])
            )
            tracked_objects.append(obj)
        
        # Dibujar
        vis_frame = viz.draw_detections(frame, tracked_objects)
        
        # Agregar info
        info = {
            "Frame": i,
            "Objects": len(tracked_objects),
            "FPS": "30.0"
        }
        vis_frame = viz.draw_info_overlay(vis_frame, info)
        
        # Mostrar
        cv2.imshow("Visualizer Test", vis_frame)
        
        if cv2.waitKey(30) & 0xFF == ord('q'):
            break
    
    cv2.destroyAllWindows()
    logger.info("Test finalizado")





