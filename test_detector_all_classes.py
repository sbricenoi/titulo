#!/usr/bin/env python3
"""Test del detector detectando TODAS las clases de COCO"""

import cv2
import sys
from pathlib import Path
from loguru import logger
from ultralytics import YOLO

logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")

def test_all_classes(video_path: str):
    """Detectar TODAS las clases para ver qué hay en el video."""
    
    logger.info("=" * 70)
    logger.info("🔍 TEST DETECTOR - TODAS LAS CLASES COCO")
    logger.info("=" * 70)
    
    # Cargar modelo
    logger.info("📦 Cargando YOLOv8n...")
    model = YOLO("yolov8n.pt")
    logger.success("✓ Modelo cargado\n")
    
    # Abrir video
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    logger.info(f"🎬 Video: {Path(video_path).name}")
    logger.info(f"   FPS: {fps:.1f}, Total: {total_frames} frames\n")
    
    # Procesar frames estratégicos
    frames_to_check = [0, 100, 500, 1000, 1500, 2000]
    all_detections = []
    
    for frame_num in frames_to_check:
        if frame_num >= total_frames:
            break
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        
        if not ret:
            continue
        
        # Detectar con threshold MUY bajo
        results = model(frame, conf=0.1, verbose=False)
        
        logger.info(f"Frame {frame_num}:")
        
        if len(results[0].boxes) > 0:
            logger.success(f"   ✓ {len(results[0].boxes)} detecciones!")
            
            for box in results[0].boxes:
                class_id = int(box.cls[0])
                class_name = model.names[class_id]
                confidence = float(box.conf[0])
                
                logger.info(f"      • {class_name} (conf: {confidence:.2f})")
                all_detections.append((class_name, confidence))
        else:
            logger.info("   Sin detecciones")
        
        logger.info("")
    
    cap.release()
    
    # Resumen
    logger.info("=" * 70)
    logger.info("📊 RESUMEN")
    logger.info("=" * 70)
    logger.info(f"Frames analizados: {len(frames_to_check)}")
    logger.info(f"Total detecciones: {len(all_detections)}")
    
    if all_detections:
        # Contar clases únicas
        class_counts = {}
        for class_name, conf in all_detections:
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
        
        logger.info("\nDetecciones por clase:")
        for class_name, count in sorted(class_counts.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"   • {class_name}: {count}")
        
        logger.success("\n✅ HAY OBJETOS DETECTABLES EN EL VIDEO")
    else:
        logger.warning("⚠️  NINGÚN OBJETO DETECTADO")
        logger.info("\nPosibles razones:")
        logger.info("   1. 🌙 Video nocturno en infrarrojo (modelo no entrenado para esto)")
        logger.info("   2. 📹 Área vacía sin animales ni personas")
        logger.info("   3. 🐾 Objetos muy pequeños o borrosos")
        logger.info("\n💡 Solución: Entrenar modelo YOLOv8 custom con:")
        logger.info("   • Imágenes de hurones en infrarrojo")
        logger.info("   • Imágenes de hurones con iluminación normal")
        logger.info("   • Anotaciones específicas de hurones")
    
    logger.info("=" * 70)

if __name__ == "__main__":
    video = "video-recording-system/data/videos/recordings/camera_1_2026-02-07_22-51-19.mp4"
    test_all_classes(video)
