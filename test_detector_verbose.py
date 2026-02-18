#!/usr/bin/env python3
"""Test del detector con threshold bajo y más detalle"""

import cv2
import sys
from pathlib import Path
from loguru import logger
from ai.detector import BehaviorDetector

logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")

def test_detector_verbose(video_path: str):
    """Probar detector con threshold bajo."""
    
    logger.info("=" * 70)
    logger.info("🧪 TEST DETECTOR - MODO VERBOSE")
    logger.info("=" * 70)
    
    # Detector con threshold MUY bajo para capturar todo
    logger.info("📦 Inicializando YOLOv8 con threshold=0.25...")
    detector = BehaviorDetector(
        model_path="yolov8n.pt",
        device="cpu",
        confidence_threshold=0.25,  # Muy bajo para capturar todo
        iou_threshold=0.45
    )
    logger.success("✓ Detector listo\n")
    
    # Abrir video
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    logger.info(f"🎬 Video: {Path(video_path).name}")
    logger.info(f"   FPS: {fps:.1f}, Total frames: {total_frames}\n")
    
    # Procesar frames estratégicamente
    frames_to_check = [0, 50, 100, 500, 1000, 1500, 2000]
    
    results = []
    
    for frame_num in frames_to_check:
        if frame_num >= total_frames:
            break
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        
        if not ret:
            continue
        
        # Analizar frame
        brightness = frame.mean()
        logger.info(f"Frame {frame_num}:")
        logger.info(f"   Brillo promedio: {brightness:.1f}/255")
        
        # Detectar
        detections = detector.detect(frame)
        
        if detections:
            logger.success(f"   ✓ {len(detections)} detecciones!")
            for i, det in enumerate(detections):
                logger.info(f"      {i+1}. {det.class_name} (conf: {det.confidence:.2f}) → {det.entity_type}")
                results.append(det)
        else:
            logger.info("   Sin detecciones")
        
        logger.info("")
    
    cap.release()
    
    # Resumen
    logger.info("=" * 70)
    logger.info("📊 RESUMEN FINAL")
    logger.info("=" * 70)
    logger.info(f"Frames analizados: {len(frames_to_check)}")
    logger.info(f"Total detecciones: {len(results)}")
    
    if results:
        # Contar por tipo
        types = {}
        for det in results:
            types[det.entity_type] = types.get(det.entity_type, 0) + 1
        
        for entity_type, count in types.items():
            logger.info(f"  • {entity_type}: {count}")
        
        # Mostrar confianzas
        confidences = [det.confidence for det in results]
        logger.info(f"\nConfianza promedio: {sum(confidences)/len(confidences):.2f}")
        logger.info(f"Confianza mín: {min(confidences):.2f}")
        logger.info(f"Confianza máx: {max(confidences):.2f}")
        
        logger.success("\n✅ DETECTOR FUNCIONANDO - Objetos detectados")
    else:
        logger.warning("⚠️  NINGUNA DETECCIÓN")
        logger.info("\nPosibles razones:")
        logger.info("  1. Video de cámara apuntando a área vacía (sin hurones/personas)")
        logger.info("  2. Video muy oscuro o sobreexpuesto")
        logger.info("  3. Modelo YOLOv8n necesita fine-tuning para hurones")
        logger.info("\n💡 Recomendación: Probar con un video con personas/animales visibles")
    
    logger.info("=" * 70)

if __name__ == "__main__":
    video = "video-recording-system/data/videos/recordings/camera_1_2026-02-07_22-51-19.mp4"
    test_detector_verbose(video)
