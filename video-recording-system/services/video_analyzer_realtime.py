#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analizador de Video en Tiempo Real con Tracking Multi-Individuo

Este servicio:
- Analiza frames en tiempo real durante la grabación
- Detecta y rastrea múltiples hurones (individuos)
- Asigna IDs únicos a cada hurón
- Guarda estadísticas de comportamiento por individuo
- Integra con el sistema de grabación existente

Autor: Sistema de Monitoreo de Hurones
Fecha: 2026-02-08
Versión: 2.0.0
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict, deque
import cv2
import numpy as np
from loguru import logger

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai.detector import BehaviorDetector
from ai.tracker import MultiCameraTracker, TrackedObject
from recorder_config import config


class RealtimeVideoAnalyzer:
    """
    Analizador de video en tiempo real con tracking multi-individuo.
    
    Características:
    - Detección con YOLOv8 (modelo entrenado)
    - Tracking multi-cámara con IDs persistentes
    - Identificación de individuos únicos
    - Estadísticas por individuo y comportamiento
    - Guardado incremental de resultados
    """
    
    def __init__(
        self,
        model_path: str = "models/ferret_detector_v1.pt",
        confidence_threshold: float = 0.30,
        analysis_interval: int = 30,  # Analizar cada 30 frames
        save_interval: int = 300      # Guardar estadísticas cada 5 min
    ):
        """
        Inicializar analizador.
        
        Args:
            model_path: Path al modelo YOLOv8 entrenado
            confidence_threshold: Umbral de confianza para detecciones
            analysis_interval: Frames entre análisis
            save_interval: Segundos entre guardado de estadísticas
        """
        self.model_path = Path(model_path)
        self.confidence_threshold = confidence_threshold
        self.analysis_interval = analysis_interval
        self.save_interval = save_interval
        
        # Directorio de salida
        self.output_dir = config.DATA_DIR / "realtime_analysis"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Inicializar detector con modelo entrenado
        logger.info(f"📦 Inicializando detector con modelo: {model_path}")
        
        try:
            self.detector = BehaviorDetector(
                model_path=str(self.model_path) if self.model_path.exists() else "yolov8n.pt",
                device="cpu",
                confidence_threshold=confidence_threshold,
                iou_threshold=0.45
            )
            logger.success("✓ Detector inicializado")
        except Exception as e:
            logger.warning(f"⚠️ Error cargando modelo entrenado, usando base: {e}")
            self.detector = BehaviorDetector(
                model_path="yolov8n.pt",
                device="cpu",
                confidence_threshold=confidence_threshold
            )
        
        # Inicializar tracker multi-cámara
        logger.info("🎯 Inicializando tracker multi-cámara...")
        self.tracker = MultiCameraTracker(
            max_age=90,        # 3 segundos a 30 FPS
            min_hits=3,        # Confirmar después de 3 detecciones
            use_deepsort=False # Usar tracker simple por ahora
        )
        logger.success("✓ Tracker inicializado")
        
        # Estadísticas por individuo
        self.individual_stats = defaultdict(lambda: {
            "first_seen": None,
            "last_seen": None,
            "total_detections": 0,
            "cameras_seen": set(),
            "behaviors": defaultdict(int),
            "activity_timeline": deque(maxlen=1000)
        })
        
        # Contadores globales
        self.global_stats = {
            "start_time": datetime.now(),
            "total_frames_analyzed": 0,
            "total_detections": 0,
            "unique_individuals": 0,
            "frames_processed": 0,
            "last_save": time.time()
        }
        
        # Frame buffers por cámara
        self.frame_buffers = {}
        
        logger.info("")
        logger.success("✅ Analizador en tiempo real listo")
        logger.info(f"   Modelo: {self.model_path.name}")
        logger.info(f"   Confidence: {confidence_threshold}")
        logger.info(f"   Análisis cada {analysis_interval} frames")
        logger.info("")
    
    def analyze_frame(
        self,
        camera_id: int,
        frame: np.ndarray,
        frame_number: int,
        timestamp: float
    ) -> Optional[Dict]:
        """
        Analizar un frame de video.
        
        Args:
            camera_id: ID de la cámara
            frame: Frame de video (numpy array)
            frame_number: Número de frame
            timestamp: Timestamp del frame
        
        Returns:
            Diccionario con resultados del análisis o None
        """
        # Solo analizar cada N frames
        if frame_number % self.analysis_interval != 0:
            return None
        
        self.global_stats["frames_processed"] += 1
        
        try:
            # Detectar con YOLOv8
            detections = self.detector.detect(frame)
            
            # Filtrar solo hurones (si el modelo detecta múltiples clases)
            ferret_detections = [
                det for det in detections
                if det.entity_type in ["ferret", "cat", "dog"]  # Proxy para hurones
            ]
            
            if not ferret_detections:
                return None
            
            # Actualizar tracker con detecciones de esta cámara
            detections_per_camera = {camera_id: ferret_detections}
            frames_per_camera = {camera_id: frame}
            
            tracked_objects = self.tracker.update(
                detections_per_camera,
                frames_per_camera
            )
            
            # Procesar objetos tracked
            results = {
                "camera_id": camera_id,
                "frame_number": frame_number,
                "timestamp": timestamp,
                "datetime": datetime.now().isoformat(),
                "individuals": []
            }
            
            for obj in tracked_objects:
                if obj.camera_id != camera_id:
                    continue
                
                # Actualizar estadísticas del individuo
                self._update_individual_stats(obj, timestamp)
                
                # Agregar a resultados
                results["individuals"].append({
                    "id": obj.global_id,
                    "local_id": obj.local_id,
                    "bbox": obj.bbox.tolist(),
                    "confidence": float(obj.confidence),
                    "center": obj.center.tolist(),
                    "age": obj.age
                })
            
            self.global_stats["total_frames_analyzed"] += 1
            self.global_stats["total_detections"] += len(tracked_objects)
            
            # Guardar estadísticas periódicamente
            if time.time() - self.global_stats["last_save"] > self.save_interval:
                self.save_stats()
            
            return results if results["individuals"] else None
            
        except Exception as e:
            logger.error(f"Error analizando frame {frame_number} de cámara {camera_id}: {e}")
            return None
    
    def _update_individual_stats(
        self,
        obj: TrackedObject,
        timestamp: float
    ):
        """
        Actualizar estadísticas de un individuo.
        
        Args:
            obj: Objeto tracked
            timestamp: Timestamp actual
        """
        individual_id = obj.global_id
        stats = self.individual_stats[individual_id]
        
        # Primera vez que se ve
        if stats["first_seen"] is None:
            stats["first_seen"] = timestamp
            self.global_stats["unique_individuals"] = len(self.individual_stats)
        
        # Actualizar última vez visto
        stats["last_seen"] = timestamp
        stats["total_detections"] += 1
        stats["cameras_seen"].add(obj.camera_id)
        
        # Timeline de actividad
        stats["activity_timeline"].append({
            "timestamp": timestamp,
            "camera_id": obj.camera_id,
            "bbox": obj.bbox.tolist(),
            "confidence": float(obj.confidence)
        })
    
    def classify_behavior(
        self,
        tracked_object: TrackedObject,
        frame: np.ndarray
    ) -> str:
        """
        Clasificar comportamiento basado en el objeto tracked.
        
        TODO: Implementar clasificador de comportamiento
        Por ahora retorna "active" como placeholder.
        
        Args:
            tracked_object: Objeto tracked
            frame: Frame actual
        
        Returns:
            Behavior string
        """
        # Placeholder - en el futuro aquí iría un clasificador
        # que analiza la pose, movimiento, etc.
        return "active"
    
    def save_stats(self, force: bool = False):
        """
        Guardar estadísticas acumuladas.
        
        Args:
            force: Forzar guardado sin importar intervalo
        """
        if not force and time.time() - self.global_stats["last_save"] < self.save_interval:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"analysis_stats_{timestamp}.json"
            
            # Preparar datos para guardar
            stats_to_save = {
                "metadata": {
                    "saved_at": datetime.now().isoformat(),
                    "start_time": self.global_stats["start_time"].isoformat(),
                    "duration_seconds": (datetime.now() - self.global_stats["start_time"]).total_seconds()
                },
                "global_stats": {
                    "frames_processed": self.global_stats["frames_processed"],
                    "frames_analyzed": self.global_stats["total_frames_analyzed"],
                    "total_detections": self.global_stats["total_detections"],
                    "unique_individuals": self.global_stats["unique_individuals"]
                },
                "individuals": {}
            }
            
            # Estadísticas por individuo
            for individual_id, stats in self.individual_stats.items():
                stats_to_save["individuals"][individual_id] = {
                    "first_seen": stats["first_seen"],
                    "last_seen": stats["last_seen"],
                    "total_detections": stats["total_detections"],
                    "cameras_seen": list(stats["cameras_seen"]),
                    "behaviors": dict(stats["behaviors"]),
                    "activity_timeline": list(stats["activity_timeline"])[-100:]  # Últimas 100
                }
            
            # Guardar
            with open(output_file, 'w') as f:
                json.dump(stats_to_save, f, indent=2)
            
            logger.info(f"💾 Estadísticas guardadas: {output_file.name}")
            self.global_stats["last_save"] = time.time()
            
        except Exception as e:
            logger.error(f"Error guardando estadísticas: {e}")
    
    def get_current_individuals(self) -> List[str]:
        """
        Obtener lista de individuos actualmente activos.
        
        Returns:
            Lista de IDs de individuos
        """
        current_time = time.time()
        active_threshold = 60  # Considerar activo si se vio en últimos 60s
        
        active_individuals = []
        for individual_id, stats in self.individual_stats.items():
            if stats["last_seen"] and (current_time - stats["last_seen"]) < active_threshold:
                active_individuals.append(individual_id)
        
        return active_individuals
    
    def get_summary(self) -> Dict:
        """
        Obtener resumen de estadísticas actuales.
        
        Returns:
            Diccionario con resumen
        """
        return {
            "unique_individuals": self.global_stats["unique_individuals"],
            "active_individuals": len(self.get_current_individuals()),
            "total_detections": self.global_stats["total_detections"],
            "frames_analyzed": self.global_stats["total_frames_analyzed"],
            "uptime_seconds": (datetime.now() - self.global_stats["start_time"]).total_seconds()
        }
    
    def cleanup(self):
        """Limpiar recursos y guardar estadísticas finales."""
        logger.info("🧹 Limpiando analizador...")
        self.save_stats(force=True)
        logger.success("✓ Limpieza completada")


# ==================== EJEMPLO DE USO ====================
if __name__ == "__main__":
    """Ejemplo de uso con video grabado."""
    
    # Configurar logging
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
    )
    
    # Crear analizador
    analyzer = RealtimeVideoAnalyzer(
        model_path="models/ferret_detector_v1.pt",
        confidence_threshold=0.30,
        analysis_interval=10  # Analizar cada 10 frames para demo
    )
    
    # Video de prueba
    test_video = Path("video-recording-system/data/videos/recordings/camera_1_2026-02-07_23-00-08.mp4")
    
    if not test_video.exists():
        logger.error(f"Video de prueba no encontrado: {test_video}")
        sys.exit(1)
    
    logger.info(f"🎬 Analizando video: {test_video.name}")
    logger.info("")
    
    # Abrir video
    cap = cv2.VideoCapture(str(test_video))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    frame_number = 0
    detections_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            
            if not ret:
                break
            
            timestamp = frame_number / fps
            
            # Analizar frame
            result = analyzer.analyze_frame(
                camera_id=1,
                frame=frame,
                frame_number=frame_number,
                timestamp=timestamp
            )
            
            if result:
                detections_count += 1
                logger.info(
                    f"Frame {frame_number}: {len(result['individuals'])} individuos "
                    f"[{', '.join(ind['id'] for ind in result['individuals'])}]"
                )
            
            frame_number += 1
            
            # Progress cada 100 frames
            if frame_number % 100 == 0:
                progress = (frame_number / total_frames) * 100
                logger.info(f"   Progreso: {progress:.1f}% ({frame_number}/{total_frames})")
    
    except KeyboardInterrupt:
        logger.warning("⚠️ Análisis interrumpido")
    
    finally:
        cap.release()
        
        # Resumen final
        summary = analyzer.get_summary()
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("📊 RESUMEN DEL ANÁLISIS")
        logger.info("=" * 70)
        logger.info(f"Frames procesados:     {frame_number}")
        logger.info(f"Frames analizados:     {summary['frames_analyzed']}")
        logger.info(f"Detecciones totales:   {summary['total_detections']}")
        logger.info(f"Individuos únicos:     {summary['unique_individuals']}")
        logger.info(f"Individuos activos:    {summary['active_individuals']}")
        logger.info("=" * 70)
        
        # Cleanup
        analyzer.cleanup()
        
        logger.success("\n✅ Análisis completado")
