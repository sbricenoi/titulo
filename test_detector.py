#!/usr/bin/env python3
"""Script de prueba rápida del detector de IA"""

import cv2
import sys
from pathlib import Path
from loguru import logger
from ai.detector import BehaviorDetector
from config import config

logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")

def test_detector(video_path: str, max_frames: int = 50):
    """Probar detector con un video local."""
    
    logger.info("=" * 70)
    logger.info("🧪 TEST RÁPIDO DEL DETECTOR DE IA")
    logger.info("=" * 70)
    logger.info(f"Video: {Path(video_path).name}")
    logger.info(f"Frames a procesar: {max_frames}")
    logger.info("")
    
    # Inicializar detector
    logger.info("📦 Inicializando YOLOv8...")
    try:
        detector = BehaviorDetector(
            model_path=config.DETECTION_MODEL,
            device="cpu",  # Forzar CPU para esta prueba
            confidence_threshold=0.5,
            iou_threshold=0.45,
            class_names=["person", "cat", "dog"]
        )
        logger.success("✓ Detector inicializado")
    except Exception as e:
        logger.error(f"✗ Error inicializando detector: {e}")
        return
    
    # Abrir video
    logger.info(f"\n🎬 Abriendo video...")
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        logger.error(f"✗ No se pudo abrir el video")
        return
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    logger.success(f"✓ Video abierto")
    logger.info(f"   Resolución: {width}x{height}")
    logger.info(f"   FPS: {fps:.1f}")
    logger.info(f"   Total frames: {total_frames}")
    logger.info("")
    
    # Procesar frames
    logger.info("🔍 Procesando frames...")
    frame_count = 0
    total_detections = 0
    detections_by_type = {"ferret": 0, "person": 0}
    
    while frame_count < max_frames:
        ret, frame = cap.read()
        
        if not ret:
            break
        
        frame_count += 1
        
        # Detectar (solo cada 5 frames para ser más rápido)
        if frame_count % 5 != 0:
            continue
        
        detections = detector.detect(frame)
        
        if detections:
            total_detections += len(detections)
            
            logger.info(f"Frame {frame_count}: {len(detections)} detecciones")
            
            for det in detections:
                detections_by_type[det.entity_type] += 1
                logger.info(
                    f"   • {det.entity_type} "
                    f"(confianza: {det.confidence:.2f}) "
                    f"bbox: {det.bbox.astype(int).tolist()}"
                )
    
    cap.release()
    
    # Resumen
    logger.info("")
    logger.info("=" * 70)
    logger.info("📊 RESUMEN")
    logger.info("=" * 70)
    logger.info(f"Frames procesados:    {frame_count}")
    logger.info(f"Total detecciones:    {total_detections}")
    logger.info(f"  • Hurones:          {detections_by_type['ferret']}")
    logger.info(f"  • Personas:         {detections_by_type['person']}")
    logger.info("")
    
    if total_detections > 0:
        logger.success("✅ Detector funcionando correctamente")
    else:
        logger.warning("⚠️  No se detectaron objetos (puede ser normal si el video no tiene hurones/personas)")
    
    logger.info("=" * 70)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        # Usar video por defecto
        video_path = "video-recording-system/data/videos/recordings/camera_1_2026-02-07_22-51-19.mp4"
        logger.info(f"Usando video por defecto: {video_path}")
    else:
        video_path = sys.argv[1]
    
    test_detector(video_path, max_frames=100)
