#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extraer frames de muestra para demostración de clasificación.

Crea frames manualmente desde videos locales para tener ejemplos
que el usuario pueda clasificar en el frontend.
"""

import cv2
import json
from pathlib import Path
from datetime import datetime
import sys
from loguru import logger

logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")


def extract_sample_frames_from_video(video_path: Path, num_frames: int = 5):
    """Extraer frames de muestra de un video."""
    
    logger.info(f"📹 Procesando: {video_path.name}")
    
    cap = cv2.VideoCapture(str(video_path))
    
    if not cap.isOpened():
        logger.error(f"❌ No se pudo abrir: {video_path}")
        return []
    
    # Metadata
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = total_frames / fps if fps > 0 else 0
    
    logger.info(f"   📊 {total_frames} frames, {fps:.1f} fps, {duration:.1f}s")
    
    # Seleccionar frames distribuidos uniformemente
    frame_indices = [int(i * total_frames / num_frames) for i in range(num_frames)]
    
    frames_dir = Path("data/frames_for_classification")
    frames_dir.mkdir(parents=True, exist_ok=True)
    
    results_dir = Path("data/analysis_results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    saved_frames = []
    detections_per_frame = []
    
    for i, frame_idx in enumerate(frame_indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        
        if not ret:
            continue
        
        # Guardar frame
        frame_filename = f"{video_path.stem}_frame_{frame_idx:06d}.jpg"
        frame_path = frames_dir / frame_filename
        cv2.imwrite(str(frame_path), frame)
        
        timestamp = frame_idx / fps
        
        saved_frames.append({
            "frame": frame_idx,
            "timestamp": timestamp,
            "filename": frame_filename,
            "detections_count": 0,
            "path": str(frame_path)
        })
        
        # Crear entrada vacía de detecciones (para que aparezca en el clasificador)
        detections_per_frame.append({
            "frame": frame_idx,
            "timestamp": timestamp,
            "detections": []  # Sin detecciones por ahora
        })
        
        logger.info(f"   ✓ Frame {frame_idx} extraído: {frame_filename}")
    
    cap.release()
    
    # Crear archivo de análisis
    analysis_data = {
        "video_name": video_path.name,
        "video_path": str(video_path),
        "processed_at": datetime.now().isoformat(),
        "metadata": {
            "fps": fps,
            "total_frames": total_frames,
            "resolution": [width, height],
            "duration_seconds": duration
        },
        "detections_per_frame": detections_per_frame,
        "frames_saved": saved_frames,
        "summary": {
            "total_detections": 0,
            "ferrets_detected": 0,
            "persons_detected": 0,
            "avg_confidence": 0.0,
            "frames_with_detections": 0
        }
    }
    
    analysis_filename = f"{video_path.stem}_analysis.json"
    analysis_path = results_dir / analysis_filename
    
    with open(analysis_path, 'w') as f:
        json.dump(analysis_data, f, indent=2)
    
    logger.success(f"   ✅ Análisis guardado: {analysis_filename}")
    logger.info(f"   📁 {len(saved_frames)} frames extraídos\n")
    
    return saved_frames


def main():
    """Extraer frames de varios videos."""
    
    logger.info("=" * 70)
    logger.info("🖼️  EXTRACTOR DE FRAMES DE MUESTRA")
    logger.info("=" * 70)
    logger.info("")
    
    # Buscar TODOS los videos
    recordings_dir = Path("video-recording-system/data/videos/recordings")
    
    if not recordings_dir.exists():
        logger.error("❌ No se encontró directorio de grabaciones")
        return
    
    # Obtener TODOS los videos
    videos = sorted(recordings_dir.glob("*.mp4"))
    
    if not videos:
        logger.error("❌ No se encontraron videos")
        return
    
    logger.info(f"Videos a procesar: {len(videos)}\n")
    
    total_frames = 0
    
    for video in videos:
        frames = extract_sample_frames_from_video(video, num_frames=10)  # 10 frames por video
        total_frames += len(frames)
    
    logger.info("=" * 70)
    logger.info("📊 RESUMEN")
    logger.info("=" * 70)
    logger.info(f"Videos procesados: {len(videos)}")
    logger.info(f"Frames extraídos:  {total_frames}")
    logger.info(f"")
    logger.info(f"📁 Frames: data/frames_for_classification/")
    logger.info(f"📄 Análisis: data/analysis_results/")
    logger.info("=" * 70)
    logger.info("")
    logger.success("✅ ¡Listo! Ahora puedes iniciar el frontend para clasificar frames.")


if __name__ == "__main__":
    main()
