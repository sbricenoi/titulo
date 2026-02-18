#!/usr/bin/env python3
"""Extraer frames de un video para inspección visual"""

import cv2
import sys
from pathlib import Path

def extract_frames(video_path: str, output_dir: str = "data/frame_samples"):
    """Extraer frames de ejemplo del video."""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Extraer frames en diferentes momentos
    frame_positions = [0, total_frames//4, total_frames//2, total_frames*3//4, total_frames-1]
    
    print(f"📹 Video: {Path(video_path).name}")
    print(f"   Total frames: {total_frames}")
    print(f"   Extrayendo frames en posiciones: {frame_positions}\n")
    
    for i, pos in enumerate(frame_positions):
        cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
        ret, frame = cap.read()
        
        if ret:
            # Nombre del archivo
            video_name = Path(video_path).stem
            output_file = output_path / f"{video_name}_frame_{pos:05d}.jpg"
            
            # Guardar frame
            cv2.imwrite(str(output_file), frame)
            
            # Estadísticas
            brightness = frame.mean()
            print(f"✓ Frame {pos:5d} guardado: {output_file.name}")
            print(f"  Brillo: {brightness:.1f}/255")
    
    cap.release()
    
    print(f"\n✅ Frames guardados en: {output_path}/")
    print(f"   Total: {len(frame_positions)} imágenes")
    print(f"\n💡 Revisa las imágenes para ver qué está grabando la cámara")

if __name__ == "__main__":
    video = "video-recording-system/data/videos/recordings/camera_1_2026-02-07_22-51-19.mp4"
    
    if len(sys.argv) > 1:
        video = sys.argv[1]
    
    extract_frames(video)
