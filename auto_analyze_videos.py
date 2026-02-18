#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analizador Automático de Videos con Filtro Inteligente

Flujo:
1. Analiza video con YOLOv8
2. SOLO guarda frames que detectan animales (ferret, cat, dog)
3. Auto-clasifica si el comportamiento es conocido (basado en BD)
4. Envía a clasificación manual SOLO frames con animales desconocidos

Uso:
    python auto_analyze_videos.py --video camera_1_2026-02-07_23-00-08.mp4
    python auto_analyze_videos.py --dir recordings/ --auto
"""

import os
import sys
import cv2
import json
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from loguru import logger
from tqdm import tqdm

from ai.detector import BehaviorDetector
from config import config

# Configurar logger
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
)


class SmartVideoAnalyzer:
    """Analizador inteligente de videos con filtro de animales."""
    
    def __init__(
        self,
        results_dir: Path,
        frames_dir: Path,
        db_path: Path,
        confidence_threshold: float = 0.25,
        model_path: str = "yolov8n.pt"
    ):
        """
        Inicializar analizador.
        
        Args:
            results_dir: Directorio para resultados JSON
            frames_dir: Directorio para frames con animales
            db_path: Path a la base de datos de clasificaciones
            confidence_threshold: Umbral de confianza para detecciones
        """
        self.results_dir = Path(results_dir)
        self.frames_dir = Path(frames_dir)
        self.db_path = Path(db_path)
        
        # Crear directorios
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.frames_dir.mkdir(parents=True, exist_ok=True)
        
        # Inicializar detector
        logger.info(f"📦 Inicializando detector YOLOv8 con {model_path}...")
        self.detector = BehaviorDetector(
            model_path=model_path,
            device="cpu",
            confidence_threshold=confidence_threshold,
            iou_threshold=0.45
        )
        logger.success("✓ Detector inicializado\n")
        
        # Estadísticas
        self.stats = {
            "total_frames_analyzed": 0,
            "frames_with_animals": 0,
            "frames_auto_classified": 0,
            "frames_for_manual": 0,
            "frames_discarded": 0
        }
    
    def get_similar_classifications(
        self,
        video_name: str,
        timestamp: float,
        camera_id: str
    ) -> Optional[str]:
        """
        Buscar clasificaciones similares en la BD para auto-clasificar.
        
        Args:
            video_name: Nombre del video
            timestamp: Timestamp del frame
            camera_id: ID de la cámara
        
        Returns:
            Behavior sugerido o None
        """
        try:
            if not self.db_path.exists():
                return None
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Buscar frames similares:
            # - Misma cámara
            # - Timestamp similar (±30 segundos)
            # - Con clasificación
            cursor.execute("""
                SELECT behavior, COUNT(*) as count
                FROM frame_classifications
                WHERE video_name LIKE ?
                  AND ABS(timestamp - ?) < 30
                  AND behavior NOT IN ('unknown', 'no_ferret')
                GROUP BY behavior
                ORDER BY count DESC
                LIMIT 1
            """, (f"{camera_id}%", timestamp))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[1] >= 2:  # Al menos 2 clasificaciones similares
                return result[0]
            
            return None
            
        except Exception as e:
            logger.warning(f"Error buscando clasificaciones: {e}")
            return None
    
    def analyze_video(self, video_path: Path, save_all: bool = False) -> Dict:
        """
        Analizar video con filtro inteligente.
        
        Args:
            video_path: Path del video
            save_all: Si True, guarda todos los frames (útil para testing)
        
        Returns:
            Diccionario con resultados
        """
        logger.info(f"🎬 Analizando: {video_path.name}")
        
        try:
            # Abrir video
            cap = cv2.VideoCapture(str(video_path))
            
            if not cap.isOpened():
                logger.error(f"✗ No se pudo abrir: {video_path}")
                return None
            
            # Metadata
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = total_frames / fps if fps > 0 else 0
            
            logger.info(f"   📊 {total_frames} frames, {fps:.1f} fps, {duration:.1f}s")
            
            # Extraer ID de cámara del nombre
            camera_id = video_path.stem.split('_')[0] + "_" + video_path.stem.split('_')[1]
            
            # Resultados
            results = {
                "video_name": video_path.name,
                "video_path": str(video_path),
                "processed_at": datetime.now().isoformat(),
                "camera_id": camera_id,
                "metadata": {
                    "fps": fps,
                    "total_frames": total_frames,
                    "resolution": [width, height],
                    "duration_seconds": duration
                },
                "detections": [],
                "frames_saved": [],
                "frames_auto_classified": [],
                "frames_discarded": 0,
                "summary": {
                    "total_frames_analyzed": 0,
                    "frames_with_animals": 0,
                    "frames_auto_classified": 0,
                    "frames_for_manual_classification": 0,
                    "frames_discarded": 0
                }
            }
            
            # Procesar frames (cada 10 para velocidad)
            frame_skip = 10
            frames_with_animals = 0
            auto_classified = 0
            for_manual = 0
            discarded = 0
            
            with tqdm(total=total_frames, desc="   Frames", leave=False) as pbar:
                frame_count = 0
                
                while True:
                    ret, frame = cap.read()
                    
                    if not ret:
                        break
                    
                    frame_count += 1
                    pbar.update(1)
                    
                    # Saltar frames
                    if frame_count % frame_skip != 0:
                        continue
                    
                    self.stats["total_frames_analyzed"] += 1
                    
                    # Detectar con YOLOv8
                    detections = self.detector.detect(frame)
                    
                    # FILTRO 1: ¿Hay animales?
                    animal_detections = [
                        det for det in detections 
                        if det.entity_type in ["ferret", "cat", "dog"]
                    ]
                    
                    if not animal_detections and not save_all:
                        # NO HAY ANIMALES → Descartar frame
                        discarded += 1
                        self.stats["frames_discarded"] += 1
                        continue
                    
                    # HAY ANIMALES → Procesar frame
                    frames_with_animals += 1
                    self.stats["frames_with_animals"] += 1
                    
                    timestamp = frame_count / fps
                    
                    # Guardar detecciones
                    frame_detections = []
                    for det in animal_detections:
                        frame_detections.append({
                            "bbox": det.bbox.tolist(),
                            "confidence": float(det.confidence),
                            "class_name": det.class_name,
                            "entity_type": det.entity_type
                        })
                    
                    results["detections"].append({
                        "frame": frame_count,
                        "timestamp": timestamp,
                        "detections": frame_detections
                    })
                    
                    # FILTRO 2: ¿Comportamiento conocido?
                    suggested_behavior = self.get_similar_classifications(
                        video_path.name,
                        timestamp,
                        camera_id
                    )
                    
                    if suggested_behavior:
                        # AUTO-CLASIFICACIÓN
                        auto_classified += 1
                        self.stats["frames_auto_classified"] += 1
                        
                        results["frames_auto_classified"].append({
                            "frame": frame_count,
                            "timestamp": timestamp,
                            "behavior": suggested_behavior,
                            "confidence": "auto",
                            "detections_count": len(frame_detections)
                        })
                        
                    else:
                        # CLASIFICACIÓN MANUAL REQUERIDA
                        for_manual += 1
                        self.stats["frames_for_manual"] += 1
                        
                        # Guardar frame para clasificación manual
                        frame_filename = f"{video_path.stem}_frame_{frame_count:06d}.jpg"
                        frame_path = self.frames_dir / frame_filename
                        
                        # Dibujar bounding boxes
                        frame_with_boxes = frame.copy()
                        for det in animal_detections:
                            x1, y1, x2, y2 = det.bbox.astype(int)
                            color = (0, 255, 0)  # Verde para animales
                            cv2.rectangle(frame_with_boxes, (x1, y1), (x2, y2), color, 3)
                            
                            label = f"{det.entity_type} {det.confidence:.2f}"
                            cv2.putText(
                                frame_with_boxes, label, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2
                            )
                        
                        cv2.imwrite(str(frame_path), frame_with_boxes)
                        
                        results["frames_saved"].append({
                            "frame": frame_count,
                            "timestamp": timestamp,
                            "filename": frame_filename,
                            "detections_count": len(frame_detections),
                            "path": str(frame_path)
                        })
            
            cap.release()
            
            # Actualizar resumen
            results["frames_discarded"] = discarded
            results["summary"]["total_frames_analyzed"] = self.stats["total_frames_analyzed"]
            results["summary"]["frames_with_animals"] = frames_with_animals
            results["summary"]["frames_auto_classified"] = auto_classified
            results["summary"]["frames_for_manual_classification"] = for_manual
            results["summary"]["frames_discarded"] = discarded
            
            logger.success(
                f"   ✓ {frames_with_animals} frames con animales "
                f"({auto_classified} auto, {for_manual} manual, {discarded} descartados)"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"✗ Error analizando: {e}")
            logger.exception(e)
            return None
    
    def save_results(self, results: Dict):
        """Guardar resultados en JSON."""
        try:
            filename = f"{Path(results['video_name']).stem}_smart_analysis.json"
            output_path = self.results_dir / filename
            
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.success(f"   ✓ Análisis guardado: {filename}")
            
        except Exception as e:
            logger.error(f"✗ Error guardando: {e}")
    
    def print_stats(self):
        """Mostrar estadísticas."""
        logger.info("=" * 70)
        logger.info("📊 ESTADÍSTICAS DEL ANÁLISIS INTELIGENTE")
        logger.info("=" * 70)
        logger.info(f"Frames analizados:          {self.stats['total_frames_analyzed']}")
        logger.info(f"Frames con animales:        {self.stats['frames_with_animals']}")
        logger.info(f"Auto-clasificados:          {self.stats['frames_auto_classified']}")
        logger.info(f"Para clasificación manual:  {self.stats['frames_for_manual']}")
        logger.info(f"Descartados (sin animales): {self.stats['frames_discarded']}")
        
        if self.stats['total_frames_analyzed'] > 0:
            animal_rate = self.stats['frames_with_animals'] / self.stats['total_frames_analyzed'] * 100
            logger.info(f"Tasa de animales:           {animal_rate:.1f}%")
        
        logger.info("")
        logger.info(f"📁 Para clasificar manualmente: {self.frames_dir}")
        logger.info("=" * 70)


def main():
    """Punto de entrada."""
    parser = argparse.ArgumentParser(
        description="Analizador inteligente de videos con filtro de animales"
    )
    
    parser.add_argument("--video", type=str, help="Video individual a analizar")
    parser.add_argument("--dir", type=str, help="Directorio con videos")
    parser.add_argument("--limit", type=int, help="Límite de videos")
    parser.add_argument("--confidence", type=float, default=0.25, 
                       help="Umbral de confianza (default: 0.25)")
    parser.add_argument("--model", type=str, default=None,
                       help="Modelo YOLO a usar (ej: yolov8n.pt, models/ferret_detector_v1.pt)")
    parser.add_argument("--save-all", action="store_true",
                       help="Guardar todos los frames (para testing)")
    
    args = parser.parse_args()
    
    # Directorios
    results_dir = config.DATA_DIR / "smart_analysis_results"
    frames_dir = config.DATA_DIR / "frames_for_classification"
    db_path = config.DATA_DIR / "classifications.db"
    
    # Determinar modelo a usar
    base_dir = Path(__file__).parent
    
    if args.model:
        # Usar modelo especificado
        model_path = args.model
        logger.info(f"✅ Usando modelo especificado: {model_path}")
    else:
        # Auto-seleccionar: custom si existe, sino base
        trained_model = base_dir / "models" / "ferret_detector_v1.pt"
        model_path = str(trained_model) if trained_model.exists() else "yolov8n.pt"
        
        if trained_model.exists():
            logger.info(f"✅ Usando modelo entrenado: {trained_model.name}")
        else:
            logger.warning("⚠️ Modelo entrenado no encontrado, usando base")
    
    # Crear analizador
    analyzer = SmartVideoAnalyzer(
        results_dir=results_dir,
        frames_dir=frames_dir,
        db_path=db_path,
        confidence_threshold=args.confidence,
        model_path=model_path
    )
    
    # Obtener videos
    videos = []
    
    if args.video:
        videos = [Path(args.video)]
    elif args.dir:
        dir_path = Path(args.dir)
        videos = sorted(dir_path.glob("*.mp4"))
        if args.limit:
            videos = videos[:args.limit]
    else:
        # Por defecto, videos recientes de recordings
        recordings_dir = Path("video-recording-system/data/videos/recordings")
        if recordings_dir.exists():
            all_videos = sorted(
                recordings_dir.glob("camera_*_2026-*.mp4"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            videos = all_videos[:3] if not args.limit else all_videos[:args.limit]
    
    if not videos:
        logger.error("❌ No se encontraron videos")
        sys.exit(1)
    
    logger.info("=" * 70)
    logger.info("🤖 ANALIZADOR INTELIGENTE DE VIDEOS")
    logger.info("=" * 70)
    logger.info(f"Videos a procesar: {len(videos)}")
    logger.info(f"Confidence threshold: {args.confidence}")
    logger.info(f"Modo: {'TESTING (guarda todos)' if args.save_all else 'PRODUCCIÓN (solo animales)'}")
    logger.info("")
    
    # Procesar cada video
    for i, video in enumerate(videos, 1):
        logger.info(f"[{i}/{len(videos)}]")
        
        try:
            results = analyzer.analyze_video(video, save_all=args.save_all)
            
            if results:
                analyzer.save_results(results)
            
            logger.info("")
            
        except Exception as e:
            logger.error(f"✗ Error: {e}")
            logger.exception(e)
    
    # Estadísticas finales
    analyzer.print_stats()


if __name__ == "__main__":
    main()
