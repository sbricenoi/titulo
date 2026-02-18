"""
Video Analyzer - Procesamiento de videos con detección y tracking visualizado.

Este módulo procesa videos grabados aplicando detección de hurones con YOLOv8
y tracking visual, generando una vista simulada de análisis de IA.

Autor: Sistema de Monitoreo de Hurones
Fecha: 2026-01-26
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from loguru import logger
import time
from collections import deque

# Imports locales
try:
    from ai.detector import BehaviorDetector, Detection
    from ai.tracker import MultiCameraTracker, TrackedObject
except ImportError:
    logger.warning("No se pudieron importar módulos de AI, usando versión simplificada")
    BehaviorDetector = None
    MultiCameraTracker = None


@dataclass
class AnalysisMetrics:
    """Métricas de análisis para visualización."""
    frame_number: int = 0
    fps: float = 0.0
    detection_count: int = 0
    tracking_count: int = 0
    avg_confidence: float = 0.0
    processing_time_ms: float = 0.0


class VideoAnalyzer:
    """
    Analizador de videos con visualización de IA.
    
    Procesa videos aplicando detección y tracking, y genera
    una visualización profesional del análisis.
    """
    
    def __init__(
        self,
        model_path: str = "data/models/yolov8n.pt",
        confidence_threshold: float = 0.3,
        output_resolution: Tuple[int, int] = (1280, 720)
    ):
        """
        Inicializar analizador de videos.
        
        Args:
            model_path: Ruta al modelo YOLO
            confidence_threshold: Umbral de confianza para detecciones
            output_resolution: Resolución de salida (ancho, alto)
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.output_resolution = output_resolution
        
        # Inicializar detector
        if BehaviorDetector:
            try:
                self.detector = BehaviorDetector(
                    model_path=model_path,
                    confidence_threshold=confidence_threshold,
                    device="cpu"  # Usar CPU para compatibilidad
                )
                logger.info(f"✓ Detector inicializado con modelo: {model_path}")
            except Exception as e:
                logger.warning(f"No se pudo inicializar detector: {e}")
                self.detector = None
        else:
            self.detector = None
        
        # Inicializar tracker
        if MultiCameraTracker and self.detector:
            self.tracker = MultiCameraTracker(
                max_age=30,
                min_hits=3,
                use_deepsort=False  # Usar tracker simple para demo
            )
            logger.info("✓ Tracker inicializado")
        else:
            self.tracker = None
        
        # Colores para visualización (BGR)
        self.colors = [
            (255, 100, 100),  # Azul claro
            (100, 255, 100),  # Verde claro
            (100, 100, 255),  # Rojo claro
            (255, 255, 100),  # Cyan claro
            (255, 100, 255),  # Magenta claro
            (100, 255, 255),  # Amarillo claro
        ]
        
        # Métricas
        self.metrics = AnalysisMetrics()
        self.trajectory_history: Dict[str, deque] = {}
    
    def process_video(
        self,
        input_path: Path,
        output_path: Path,
        camera_id: int = 0,
        camera_name: str = "Cámara",
        max_frames: Optional[int] = None,
        show_preview: bool = False
    ) -> bool:
        """
        Procesar video con análisis de IA.
        
        Args:
            input_path: Ruta del video de entrada
            output_path: Ruta del video de salida
            camera_id: ID de la cámara
            camera_name: Nombre de la cámara
            max_frames: Número máximo de frames a procesar (None = todos)
            show_preview: Mostrar preview durante procesamiento
            
        Returns:
            True si el procesamiento fue exitoso
        """
        logger.info(f"📹 Procesando video: {input_path.name}")
        
        # Abrir video
        cap = cv2.VideoCapture(str(input_path))
        if not cap.isOpened():
            logger.error(f"❌ No se pudo abrir video: {input_path}")
            return False
        
        # Obtener propiedades del video
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        input_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        input_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        logger.info(f"  FPS: {fps}, Frames: {total_frames}, Resolución: {input_width}x{input_height}")
        
        # Configurar writer de video
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(
            str(output_path),
            fourcc,
            fps,
            self.output_resolution
        )
        
        if not out.isOpened():
            logger.error(f"❌ No se pudo crear video de salida: {output_path}")
            cap.release()
            return False
        
        # Procesar frames
        frame_count = 0
        start_time = time.time()
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Limitar número de frames si se especifica
            if max_frames and frame_count >= max_frames:
                break
            
            frame_start = time.time()
            
            # Redimensionar frame a resolución de salida
            frame_resized = cv2.resize(frame, self.output_resolution)
            
            # Procesar frame (detección + tracking)
            detections = []
            if self.detector:
                try:
                    detections = self.detector.detect(frame_resized)
                except Exception as e:
                    logger.debug(f"Error en detección: {e}")
            
            # Tracking
            tracked_objects = []
            if self.tracker and detections:
                try:
                    # Preparar detecciones para tracker
                    detections_dict = {camera_id: detections}
                    tracked_objects = self.tracker.update(detections_dict)
                except Exception as e:
                    logger.debug(f"Error en tracking: {e}")
            
            # Calcular métricas
            frame_time = (time.time() - frame_start) * 1000
            self.metrics.frame_number = frame_count
            self.metrics.fps = fps
            self.metrics.detection_count = len(detections)
            self.metrics.tracking_count = len(tracked_objects)
            self.metrics.processing_time_ms = frame_time
            
            if detections:
                self.metrics.avg_confidence = np.mean([d.confidence for d in detections])
            else:
                self.metrics.avg_confidence = 0.0
            
            # Dibujar visualización
            frame_analyzed = self._draw_analysis_overlay(
                frame_resized,
                detections,
                tracked_objects,
                camera_name,
                camera_id
            )
            
            # Escribir frame
            out.write(frame_analyzed)
            
            # Mostrar preview si se solicita
            if show_preview:
                cv2.imshow(f'Análisis - {camera_name}', frame_analyzed)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            frame_count += 1
            
            # Log de progreso
            if frame_count % 100 == 0:
                elapsed = time.time() - start_time
                progress = (frame_count / total_frames) * 100 if total_frames > 0 else 0
                logger.info(f"  Progreso: {frame_count}/{total_frames} ({progress:.1f}%) - {elapsed:.1f}s")
        
        # Limpiar
        cap.release()
        out.release()
        if show_preview:
            cv2.destroyAllWindows()
        
        elapsed_total = time.time() - start_time
        logger.info(f"✓ Video procesado: {frame_count} frames en {elapsed_total:.1f}s")
        logger.info(f"  Guardado en: {output_path}")
        
        return True
    
    def _draw_analysis_overlay(
        self,
        frame: np.ndarray,
        detections: List,
        tracked_objects: List,
        camera_name: str,
        camera_id: int
    ) -> np.ndarray:
        """
        Dibujar overlay de análisis de IA en el frame.
        
        Args:
            frame: Frame a procesar
            detections: Lista de detecciones
            tracked_objects: Lista de objetos tracked
            camera_name: Nombre de la cámara
            camera_id: ID de la cámara
            
        Returns:
            Frame con overlay dibujado
        """
        overlay = frame.copy()
        h, w = frame.shape[:2]
        
        # Dibujar detecciones y tracking
        if tracked_objects:
            for obj in tracked_objects:
                if obj.camera_id != camera_id:
                    continue
                
                # Obtener color para este ID
                color_idx = hash(obj.global_id) % len(self.colors)
                color = self.colors[color_idx]
                
                # Bounding box
                bbox = obj.bbox.astype(int)
                x1, y1, x2, y2 = bbox
                
                # Dibujar rectángulo con sombra
                cv2.rectangle(overlay, (x1+2, y1+2), (x2+2, y2+2), (0, 0, 0), 3)
                cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 3)
                
                # Etiqueta con ID y confianza
                label = f"ID: {obj.global_id} ({obj.confidence:.2f})"
                
                # Fondo para texto
                (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                cv2.rectangle(overlay, (x1, y1-30), (x1+text_w+10, y1), color, -1)
                cv2.putText(overlay, label, (x1+5, y1-8), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                # Dibujar trayectoria
                if obj.global_id not in self.trajectory_history:
                    self.trajectory_history[obj.global_id] = deque(maxlen=50)
                
                center = obj.center.astype(int)
                self.trajectory_history[obj.global_id].append(tuple(center))
                
                # Dibujar línea de trayectoria
                points = list(self.trajectory_history[obj.global_id])
                for i in range(1, len(points)):
                    alpha = i / len(points)  # Fade effect
                    thickness = max(1, int(3 * alpha))
                    cv2.line(overlay, points[i-1], points[i], color, thickness)
                
                # Punto central
                cv2.circle(overlay, tuple(center), 5, color, -1)
                cv2.circle(overlay, tuple(center), 5, (255, 255, 255), 2)
        
        elif detections:
            # Si no hay tracking, solo mostrar detecciones
            for i, det in enumerate(detections):
                color = self.colors[i % len(self.colors)]
                bbox = det.bbox.astype(int)
                x1, y1, x2, y2 = bbox
                
                cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 2)
                label = f"{det.class_name} ({det.confidence:.2f})"
                cv2.putText(overlay, label, (x1, y1-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Panel de información (estilo futurista)
        self._draw_info_panel(overlay, camera_name)
        
        return overlay
    
    def _draw_info_panel(self, frame: np.ndarray, camera_name: str):
        """Dibujar panel de información con métricas."""
        h, w = frame.shape[:2]
        
        # Panel principal (esquina superior derecha)
        panel_width = 350
        panel_height = 200
        panel_x = w - panel_width - 20
        panel_y = 20
        
        # Fondo semi-transparente con borde
        overlay = frame.copy()
        cv2.rectangle(overlay, (panel_x, panel_y), 
                     (panel_x + panel_width, panel_y + panel_height),
                     (20, 20, 20), -1)
        cv2.rectangle(overlay, (panel_x, panel_y), 
                     (panel_x + panel_width, panel_y + panel_height),
                     (0, 255, 255), 2)
        
        # Mezclar con el frame original (transparencia)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Título del panel
        title = "🤖 ANÁLISIS IA - MONITOREO HURÓN"
        cv2.putText(frame, title, (panel_x + 10, panel_y + 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        # Línea separadora
        cv2.line(frame, (panel_x + 10, panel_y + 35), 
                (panel_x + panel_width - 10, panel_y + 35), (0, 255, 255), 1)
        
        # Información
        y_offset = panel_y + 55
        line_height = 22
        
        info_lines = [
            f"Camara: {camera_name}",
            f"Frame: {self.metrics.frame_number}",
            f"FPS: {self.metrics.fps:.1f}",
            f"Detecciones: {self.metrics.detection_count}",
            f"Hurones tracked: {self.metrics.tracking_count}",
            f"Confianza: {self.metrics.avg_confidence:.2%}",
            f"Tiempo proc: {self.metrics.processing_time_ms:.1f}ms"
        ]
        
        for i, line in enumerate(info_lines):
            y = y_offset + (i * line_height)
            
            # Separar label y valor
            if ": " in line:
                label, value = line.split(": ", 1)
                cv2.putText(frame, f"{label}:", (panel_x + 15, y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
                cv2.putText(frame, value, (panel_x + 180, y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
            else:
                cv2.putText(frame, line, (panel_x + 15, y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
        
        # Indicador de estado (parte inferior)
        status_text = "🟢 SISTEMA ACTIVO - ANÁLISIS EN TIEMPO REAL"
        status_y = panel_y + panel_height - 15
        cv2.putText(frame, status_text, (panel_x + 15, status_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 0), 1)
        
        # Barra de actividad (animada)
        bar_width = int((self.metrics.frame_number % 100) / 100 * (panel_width - 30))
        cv2.rectangle(frame, (panel_x + 15, panel_y + panel_height - 30),
                     (panel_x + 15 + bar_width, panel_y + panel_height - 25),
                     (0, 255, 255), -1)
        
        # Marca de agua
        watermark = "Ferret AI Monitoring System v1.0"
        cv2.putText(frame, watermark, (20, h - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 100, 100), 1)


def process_camera_videos(
    input_dir: Path,
    output_dir: Path,
    num_cameras: int = 3,
    max_frames: Optional[int] = None
):
    """
    Procesar un video de cada cámara para análisis simulado.
    
    Args:
        input_dir: Directorio con videos de entrada
        output_dir: Directorio para videos procesados
        num_cameras: Número de cámaras a procesar
        max_frames: Número máximo de frames por video
    """
    logger.info(f"🎬 Iniciando procesamiento de videos de {num_cameras} cámaras")
    
    # Crear directorio de salida
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Inicializar analizador
    analyzer = VideoAnalyzer(
        model_path="data/models/yolov8n.pt",
        confidence_threshold=0.3,
        output_resolution=(1280, 720)
    )
    
    # Procesar un video de cada cámara
    for camera_id in range(num_cameras):
        # Buscar videos de esta cámara
        camera_videos = sorted(input_dir.glob(f"camera_{camera_id+1}_*.mp4"))
        
        if not camera_videos:
            logger.warning(f"⚠️  No se encontraron videos para cámara {camera_id+1}")
            continue
        
        # Tomar el primer video
        input_video = camera_videos[0]
        output_video = output_dir / f"analyzed_camera_{camera_id+1}.mp4"
        
        logger.info(f"\n📹 Cámara {camera_id+1}: {input_video.name}")
        
        # Procesar video
        success = analyzer.process_video(
            input_path=input_video,
            output_path=output_video,
            camera_id=camera_id,
            camera_name=f"Cámara {camera_id+1}",
            max_frames=max_frames,
            show_preview=False
        )
        
        if success:
            logger.info(f"✓ Cámara {camera_id+1} procesada exitosamente")
        else:
            logger.error(f"❌ Error procesando cámara {camera_id+1}")
    
    logger.info(f"\n🎉 Procesamiento completado. Videos en: {output_dir}")


if __name__ == "__main__":
    """Ejecutar procesamiento de videos."""
    from utils.logger import setup_logger
    
    # Configurar logging
    setup_logger()
    
    # Rutas
    input_dir = Path("video-recording-system/data/videos/uploaded")
    output_dir = Path("data/videos/analyzed")
    
    # Procesar videos (limitar a 300 frames por video para demo rápida)
    process_camera_videos(
        input_dir=input_dir,
        output_dir=output_dir,
        num_cameras=3,
        max_frames=300  # ~10 segundos a 30 FPS
    )
