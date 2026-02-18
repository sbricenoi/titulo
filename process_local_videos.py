#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Procesador de Videos Locales con IA y Extracción de Frames

Procesa videos locales con YOLOv8 y guarda:
1. Resultados JSON con detecciones
2. Frames con detecciones para clasificación en frontend
3. Estadísticas de análisis

Uso:
    python process_local_videos.py --input video.mp4
    python process_local_videos.py --dir recordings/ --limit 3
"""

import os
import sys
import cv2
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict
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


class LocalVideoProcessor:
    """Procesador de videos locales con IA."""
    
    def __init__(self, results_dir: Path, frames_dir: Path):
        """
        Inicializar procesador.
        
        Args:
            results_dir: Directorio para resultados JSON
            frames_dir: Directorio para frames detectados
        """
        self.results_dir = Path(results_dir)
        self.frames_dir = Path(frames_dir)
        
        # Crear directorios
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.frames_dir.mkdir(parents=True, exist_ok=True)
        
        # Inicializar detector
        logger.info("📦 Inicializando detector YOLOv8...")
        self.detector = BehaviorDetector(
            model_path="yolov8n.pt",
            device="cpu",  # Usar CPU por ahora
            confidence_threshold=0.3,  # Threshold bajo para capturar más
            iou_threshold=0.45
        )
        logger.success("✓ Detector inicializado\n")
        
        # Estadísticas
        self.stats = {
            "videos_processed": 0,
            "videos_failed": 0,
            "total_detections": 0,
            "total_frames": 0,
            "frames_saved": 0
        }
    
    def process_video(self, video_path: Path) -> Dict:
        """
        Procesar video con detector IA.
        
        Args:
            video_path: Path del video
            
        Returns:
            Diccionario con resultados
        """
        logger.info(f"🎬 Procesando: {video_path.name}")
        
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
            
            # Resultados
            results = {
                "video_name": video_path.name,
                "video_path": str(video_path),
                "processed_at": datetime.now().isoformat(),
                "metadata": {
                    "fps": fps,
                    "total_frames": total_frames,
                    "resolution": [width, height],
                    "duration_seconds": duration
                },
                "detections_per_frame": [],
                "frames_saved": [],
                "summary": {
                    "total_detections": 0,
                    "ferrets_detected": 0,
                    "persons_detected": 0,
                    "avg_confidence": 0.0,
                    "frames_with_detections": 0
                }
            }
            
            # Procesar frames
            frame_count = 0
            total_detections = 0
            total_confidence = 0
            ferret_count = 0
            person_count = 0
            frames_with_detections = 0
            
            frame_skip = 10  # Procesar 1 de cada 10 frames (más rápido)
            
            with tqdm(total=total_frames, desc="   Frames", leave=False) as pbar:
                while True:
                    ret, frame = cap.read()
                    
                    if not ret:
                        break
                    
                    frame_count += 1
                    pbar.update(1)
                    
                    # Saltar frames
                    if frame_count % frame_skip != 0:
                        continue
                    
                    # Detectar
                    detections = self.detector.detect(frame)
                    
                    if detections:
                        frames_with_detections += 1
                        
                        # Guardar detecciones
                        frame_detections = []
                        for det in detections:
                            detection_dict = {
                                "bbox": det.bbox.tolist(),
                                "confidence": float(det.confidence),
                                "class_name": det.class_name,
                                "entity_type": det.entity_type
                            }
                            frame_detections.append(detection_dict)
                            
                            total_detections += 1
                            total_confidence += det.confidence
                            
                            if det.entity_type == "ferret":
                                ferret_count += 1
                            elif det.entity_type == "person":
                                person_count += 1
                        
                        # Guardar info de frame
                        results["detections_per_frame"].append({
                            "frame": frame_count,
                            "timestamp": frame_count / fps,
                            "detections": frame_detections
                        })
                        
                        # Guardar frame como imagen para clasificación
                        frame_filename = f"{video_path.stem}_frame_{frame_count:06d}.jpg"
                        frame_path = self.frames_dir / frame_filename
                        
                        # Dibujar bounding boxes en el frame
                        frame_with_boxes = frame.copy()
                        for det in detections:
                            x1, y1, x2, y2 = det.bbox.astype(int)
                            color = (0, 255, 0) if det.entity_type == "ferret" else (0, 0, 255)
                            cv2.rectangle(frame_with_boxes, (x1, y1), (x2, y2), color, 3)
                            
                            # Label
                            label = f"{det.entity_type} {det.confidence:.2f}"
                            cv2.putText(
                                frame_with_boxes, label, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2
                            )
                        
                        cv2.imwrite(str(frame_path), frame_with_boxes)
                        
                        results["frames_saved"].append({
                            "frame": frame_count,
                            "timestamp": frame_count / fps,
                            "filename": frame_filename,
                            "detections_count": len(frame_detections),
                            "path": str(frame_path)
                        })
                        
                        self.stats["frames_saved"] += 1
            
            cap.release()
            
            # Resumen
            results["summary"]["total_detections"] = total_detections
            results["summary"]["ferrets_detected"] = ferret_count
            results["summary"]["persons_detected"] = person_count
            results["summary"]["frames_with_detections"] = frames_with_detections
            results["summary"]["avg_confidence"] = (
                total_confidence / total_detections if total_detections > 0 else 0.0
            )
            
            self.stats["total_frames"] += total_frames
            self.stats["total_detections"] += total_detections
            
            logger.success(
                f"   ✓ {total_detections} detecciones "
                f"({ferret_count} hurones, {person_count} personas) "
                f"en {frames_with_detections} frames"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"✗ Error procesando: {e}")
            logger.exception(e)
            return None
    
    def save_results(self, results: Dict):
        """Guardar resultados en JSON."""
        try:
            filename = f"{Path(results['video_name']).stem}_analysis.json"
            output_path = self.results_dir / filename
            
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.success(f"   ✓ Resultados: {filename}")
            
        except Exception as e:
            logger.error(f"✗ Error guardando: {e}")
    
    def process_batch(self, video_paths: List[Path]):
        """Procesar múltiples videos."""
        logger.info("=" * 70)
        logger.info("🎥 PROCESADOR DE VIDEOS LOCALES - ANÁLISIS IA")
        logger.info("=" * 70)
        logger.info(f"Videos a procesar: {len(video_paths)}\n")
        
        for i, video_path in enumerate(video_paths, 1):
            logger.info(f"[{i}/{len(video_paths)}]")
            
            try:
                results = self.process_video(video_path)
                
                if results:
                    self.save_results(results)
                    self.stats["videos_processed"] += 1
                else:
                    self.stats["videos_failed"] += 1
                
                logger.info("")
                
            except Exception as e:
                logger.error(f"✗ Error: {e}")
                self.stats["videos_failed"] += 1
        
        self.print_stats()
    
    def print_stats(self):
        """Mostrar estadísticas."""
        logger.info("=" * 70)
        logger.info("📊 ESTADÍSTICAS FINALES")
        logger.info("=" * 70)
        logger.info(f"Videos procesados:    {self.stats['videos_processed']}")
        logger.info(f"Videos fallidos:      {self.stats['videos_failed']}")
        logger.info(f"Total detecciones:    {self.stats['total_detections']}")
        logger.info(f"Frames guardados:     {self.stats['frames_saved']}")
        logger.info(f"Total frames:         {self.stats['total_frames']}")
        
        if self.stats['total_frames'] > 0:
            detection_rate = self.stats['total_detections'] / self.stats['total_frames']
            logger.info(f"Tasa detección:       {detection_rate:.4f} det/frame")
        
        logger.info("")
        logger.info(f"📁 Resultados JSON: {self.results_dir}")
        logger.info(f"🖼️  Frames guardados: {self.frames_dir}")
        logger.info("=" * 70)


def main():
    """Punto de entrada."""
    parser = argparse.ArgumentParser(description="Procesador de videos locales")
    
    parser.add_argument("--input", type=str, help="Video individual a procesar")
    parser.add_argument("--dir", type=str, help="Directorio con videos")
    parser.add_argument("--limit", type=int, help="Límite de videos")
    
    args = parser.parse_args()
    
    # Directorios de salida
    results_dir = config.DATA_DIR / "analysis_results"
    frames_dir = config.DATA_DIR / "frames_for_classification"
    
    # Crear procesador
    processor = LocalVideoProcessor(
        results_dir=results_dir,
        frames_dir=frames_dir
    )
    
    # Obtener videos a procesar
    videos = []
    
    if args.input:
        videos = [Path(args.input)]
    elif args.dir:
        dir_path = Path(args.dir)
        videos = list(dir_path.glob("*.mp4"))
        
        if args.limit:
            videos = videos[:args.limit]
    else:
        # Por defecto, procesar videos de hoy en recordings
        recordings_dir = Path("video-recording-system/data/videos/recordings")
        if recordings_dir.exists():
            all_videos = list(recordings_dir.glob("camera_*_2026-02-07_*.mp4"))
            videos = sorted(all_videos, key=lambda x: x.stat().st_mtime, reverse=True)
            
            if args.limit:
                videos = videos[:args.limit]
            else:
                videos = videos[:3]  # Por defecto, 3 videos
    
    if not videos:
        logger.error("❌ No se encontraron videos para procesar")
        sys.exit(1)
    
    # Procesar
    try:
        processor.process_batch(videos)
    except KeyboardInterrupt:
        logger.info("\n⌨️  Interrupción de usuario")
        processor.print_stats()
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        logger.exception(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
