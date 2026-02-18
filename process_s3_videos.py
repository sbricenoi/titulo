#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Procesador de Videos desde S3 con Análisis de IA

Este script:
1. Lista videos disponibles en S3
2. Descarga videos a procesar
3. Ejecuta análisis de IA (detección + tracking + clasificación)
4. Guarda resultados en base de datos y archivos JSON

Uso:
    python process_s3_videos.py --date 2026-02-07
    python process_s3_videos.py --camera camera_1 --limit 10
    python process_s3_videos.py --all

Autor: Sistema de Monitoreo de Hurones
Fecha: 2026-02-07
"""

import os
import sys
import cv2
import json
import argparse
import boto3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from loguru import logger
from tqdm import tqdm

# Imports del sistema de IA
from ai import BehaviorDetector
from config import config

# Configurar logger
logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")
logger.add(
    config.LOGS_DIR / "video_processor_{time}.log",
    rotation="100 MB",
    retention="7 days",
    compression="zip"
)


@dataclass
class VideoMetadata:
    """Metadata de un video en S3."""
    key: str
    size_mb: float
    last_modified: datetime
    camera_id: str
    date: str
    time: str
    local_path: Optional[Path] = None


class S3VideoProcessor:
    """
    Procesador de videos desde S3.
    
    Descarga videos de S3, los procesa con el pipeline de IA,
    y guarda los resultados.
    """
    
    def __init__(
        self,
        bucket_name: str,
        download_dir: Path,
        results_dir: Path,
        frames_dir: Path,
        keep_videos: bool = False
    ):
        """
        Inicializar procesador.
        
        Args:
            bucket_name: Nombre del bucket S3
            download_dir: Directorio para descargar videos
            results_dir: Directorio para guardar resultados
            frames_dir: Directorio para guardar frames detectados
            keep_videos: Si mantener videos después de procesar
        """
        self.bucket_name = bucket_name
        self.download_dir = Path(download_dir)
        self.results_dir = Path(results_dir)
        self.frames_dir = Path(frames_dir)
        self.keep_videos = keep_videos
        
        # Crear directorios
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.frames_dir.mkdir(parents=True, exist_ok=True)
        
        # Cliente S3
        try:
            self.s3_client = boto3.client('s3')
            logger.info(f"✓ Cliente S3 inicializado (bucket: {bucket_name})")
        except Exception as e:
            logger.error(f"✗ Error inicializando S3: {e}")
            raise
        
            # Detector de IA
        try:
            logger.info("📦 Inicializando detector de IA...")
            self.detector = BehaviorDetector(
                model_path=config.DETECTION_MODEL,
                device=config.DEVICE,
                confidence_threshold=config.DETECTION_CONFIDENCE,
                iou_threshold=config.DETECTION_IOU
            )
            logger.success("✓ Detector YOLOv8 inicializado")
        except Exception as e:
            logger.error(f"✗ Error inicializando detector: {e}")
            raise
        
        # Estadísticas
        self.stats = {
            "videos_processed": 0,
            "videos_failed": 0,
            "total_detections": 0,
            "total_frames": 0
        }
    
    def list_videos(
        self,
        camera_id: Optional[str] = None,
        date: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[VideoMetadata]:
        """
        Listar videos disponibles en S3.
        
        Args:
            camera_id: Filtrar por cámara (ej: "camera_1")
            date: Filtrar por fecha (formato: YYYY-MM-DD)
            limit: Límite de videos a retornar
            
        Returns:
            Lista de VideoMetadata
        """
        logger.info(f"🔍 Listando videos en S3...")
        
        try:
            # Construir prefix de búsqueda
            prefix = ""
            if date:
                parts = date.split('-')
                prefix = f"{parts[0]}/{parts[1]}/{parts[2]}/"
                if camera_id:
                    prefix += f"{camera_id}/"
            elif camera_id:
                # Sin fecha, buscar en todo el bucket con filtro por cámara
                pass
            
            # Listar objetos
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)
            
            videos = []
            for page in pages:
                if 'Contents' not in page:
                    continue
                
                for obj in page['Contents']:
                    key = obj['Key']
                    
                    # Solo archivos .mp4
                    if not key.endswith('.mp4'):
                        continue
                    
                    # Filtrar por cámara si es necesario
                    if camera_id and camera_id not in key:
                        continue
                    
                    # Parsear metadata del nombre
                    filename = Path(key).name
                    try:
                        # Formato: camera_X_YYYY-MM-DD_HH-MM-SS.mp4
                        parts = filename.replace('.mp4', '').split('_')
                        cam_id = f"{parts[0]}_{parts[1]}"  # camera_X
                        vid_date = parts[2]  # YYYY-MM-DD
                        vid_time = parts[3]  # HH-MM-SS
                    except:
                        logger.warning(f"No se pudo parsear nombre: {filename}")
                        continue
                    
                    video = VideoMetadata(
                        key=key,
                        size_mb=obj['Size'] / (1024 * 1024),
                        last_modified=obj['LastModified'],
                        camera_id=cam_id,
                        date=vid_date,
                        time=vid_time
                    )
                    
                    videos.append(video)
                    
                    # Aplicar límite
                    if limit and len(videos) >= limit:
                        break
                
                if limit and len(videos) >= limit:
                    break
            
            logger.success(f"✓ Encontrados {len(videos)} videos")
            return videos
            
        except Exception as e:
            logger.error(f"✗ Error listando videos: {e}")
            return []
    
    def download_video(self, video: VideoMetadata) -> Optional[Path]:
        """
        Descargar video desde S3.
        
        Args:
            video: Metadata del video
            
        Returns:
            Path del archivo descargado o None si falla
        """
        filename = Path(video.key).name
        local_path = self.download_dir / filename
        
        # Si ya existe, no descargar de nuevo
        if local_path.exists():
            logger.debug(f"Video ya descargado: {filename}")
            return local_path
        
        try:
            logger.info(f"⬇️  Descargando: {filename} ({video.size_mb:.1f} MB)")
            
            self.s3_client.download_file(
                self.bucket_name,
                video.key,
                str(local_path)
            )
            
            logger.success(f"✓ Descargado: {filename}")
            return local_path
            
        except Exception as e:
            logger.error(f"✗ Error descargando {filename}: {e}")
            return None
    
    def process_video(self, video_path: Path) -> Dict:
        """
        Procesar video con el pipeline de IA.
        
        Args:
            video_path: Path del video a procesar
            
        Returns:
            Diccionario con resultados del análisis
        """
        logger.info(f"🎬 Procesando: {video_path.name}")
        
        try:
            # Abrir video
            cap = cv2.VideoCapture(str(video_path))
            
            if not cap.isOpened():
                logger.error(f"No se pudo abrir el video: {video_path}")
                return None
            
            # Metadata del video
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration_seconds = total_frames / fps if fps > 0 else 0
            
            logger.info(f"   📊 {total_frames} frames, {fps:.1f} fps, {duration_seconds:.1f}s")
            
            # Resultados
            results = {
                "video_name": video_path.name,
                "metadata": {
                    "fps": fps,
                    "total_frames": total_frames,
                    "resolution": [width, height],
                    "duration_seconds": duration_seconds
                },
                "detections_per_frame": [],
                "frames_saved": [],  # Paths de frames guardados
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
            
            # Saltar frames para procesar más rápido (procesar 1 de cada N frames)
            frame_skip = 5  # Procesar 1 de cada 5 frames
            
            with tqdm(total=total_frames, desc="Procesando frames") as pbar:
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
                    
                    # Guardar detecciones de este frame
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
                    
                    if frame_detections:
                        results["detections_per_frame"].append({
                            "frame": frame_count,
                            "timestamp": frame_count / fps,
                            "detections": frame_detections
                        })
                        
                        # Guardar frame como imagen para clasificación en frontend
                        frame_filename = f"{video_path.stem}_frame_{frame_count:06d}.jpg"
                        frame_path = self.frames_dir / frame_filename
                        cv2.imwrite(str(frame_path), frame)
                        
                        results["frames_saved"].append({
                            "frame": frame_count,
                            "filename": frame_filename,
                            "detections_count": len(frame_detections)
                        })
                        
                        results["summary"]["frames_with_detections"] += 1
            
            cap.release()
            
            # Calcular resumen
            results["summary"]["total_detections"] = total_detections
            results["summary"]["ferrets_detected"] = ferret_count
            results["summary"]["persons_detected"] = person_count
            results["summary"]["avg_confidence"] = (
                total_confidence / total_detections if total_detections > 0 else 0.0
            )
            
            # Actualizar estadísticas globales
            self.stats["total_frames"] += total_frames
            self.stats["total_detections"] += total_detections
            
            logger.success(
                f"✓ Procesado: {total_detections} detecciones "
                f"({ferret_count} hurones, {person_count} personas)"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"✗ Error procesando video: {e}")
            logger.exception(e)
            return None
    
    def save_results(self, results: Dict, video: VideoMetadata):
        """
        Guardar resultados del análisis.
        
        Args:
            results: Resultados del procesamiento
            video: Metadata del video
        """
        try:
            # Nombre del archivo de resultados
            filename = f"{video.camera_id}_{video.date}_{video.time}_analysis.json"
            output_path = self.results_dir / filename
            
            # Agregar metadata del video
            results["video_metadata"] = {
                "camera_id": video.camera_id,
                "date": video.date,
                "time": video.time,
                "s3_key": video.key,
                "processed_at": datetime.now().isoformat()
            }
            
            # Guardar JSON
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.success(f"✓ Resultados guardados: {filename}")
            
        except Exception as e:
            logger.error(f"✗ Error guardando resultados: {e}")
    
    def process_batch(
        self,
        camera_id: Optional[str] = None,
        date: Optional[str] = None,
        limit: Optional[int] = None
    ):
        """
        Procesar batch de videos.
        
        Args:
            camera_id: Filtrar por cámara
            date: Filtrar por fecha
            limit: Límite de videos a procesar
        """
        logger.info("=" * 70)
        logger.info("🎥 PROCESADOR DE VIDEOS S3 - ANÁLISIS DE IA")
        logger.info("=" * 70)
        
        # Listar videos
        videos = self.list_videos(camera_id=camera_id, date=date, limit=limit)
        
        if not videos:
            logger.warning("No se encontraron videos para procesar")
            return
        
        logger.info(f"\n📋 Videos a procesar: {len(videos)}")
        logger.info("")
        
        # Procesar cada video
        for i, video in enumerate(videos, 1):
            logger.info(f"\n[{i}/{len(videos)}] Procesando video...")
            logger.info(f"   Cámara: {video.camera_id}")
            logger.info(f"   Fecha: {video.date} {video.time}")
            logger.info(f"   Tamaño: {video.size_mb:.1f} MB")
            
            try:
                # Descargar
                local_path = self.download_video(video)
                
                if not local_path:
                    self.stats["videos_failed"] += 1
                    continue
                
                # Procesar
                results = self.process_video(local_path)
                
                if not results:
                    self.stats["videos_failed"] += 1
                    continue
                
                # Guardar resultados
                self.save_results(results, video)
                
                # Limpiar video si no se debe mantener
                if not self.keep_videos:
                    try:
                        local_path.unlink()
                        logger.debug(f"✓ Video eliminado: {local_path.name}")
                    except:
                        pass
                
                self.stats["videos_processed"] += 1
                
            except Exception as e:
                logger.error(f"✗ Error procesando video: {e}")
                self.stats["videos_failed"] += 1
                continue
        
        # Mostrar estadísticas finales
        self.print_stats()
    
    def print_stats(self):
        """Imprimir estadísticas finales."""
        logger.info("")
        logger.info("=" * 70)
        logger.info("📊 ESTADÍSTICAS FINALES")
        logger.info("=" * 70)
        logger.info(f"Videos procesados:    {self.stats['videos_processed']}")
        logger.info(f"Videos fallidos:      {self.stats['videos_failed']}")
        logger.info(f"Total detecciones:    {self.stats['total_detections']}")
        logger.info(f"Total frames:         {self.stats['total_frames']}")
        
        if self.stats['total_frames'] > 0:
            avg_detections = self.stats['total_detections'] / self.stats['total_frames']
            logger.info(f"Detecciones/frame:    {avg_detections:.2f}")
        
        logger.info("=" * 70)


def main():
    """Punto de entrada principal."""
    parser = argparse.ArgumentParser(
        description="Procesador de videos S3 con análisis de IA"
    )
    
    parser.add_argument(
        "--camera",
        type=str,
        help="Filtrar por cámara (ej: camera_1)"
    )
    
    parser.add_argument(
        "--date",
        type=str,
        help="Filtrar por fecha (formato: YYYY-MM-DD)"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        help="Límite de videos a procesar"
    )
    
    parser.add_argument(
        "--keep-videos",
        action="store_true",
        help="Mantener videos después de procesar"
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Procesar todos los videos disponibles"
    )
    
    args = parser.parse_args()
    
    # Configuración
    bucket_name = os.getenv("S3_BUCKET_NAME", "ferret-recordings")
    download_dir = config.DATA_DIR / "videos" / "processing"
    results_dir = config.DATA_DIR / "analysis_results"
    frames_dir = config.DATA_DIR / "frames_for_classification"
    
    # Crear procesador
    processor = S3VideoProcessor(
        bucket_name=bucket_name,
        download_dir=download_dir,
        results_dir=results_dir,
        frames_dir=frames_dir,
        keep_videos=args.keep_videos
    )
    
    # Procesar batch
    try:
        processor.process_batch(
            camera_id=args.camera,
            date=args.date,
            limit=args.limit if not args.all else None
        )
    except KeyboardInterrupt:
        logger.info("\n⌨️  Interrupción de usuario")
        processor.print_stats()
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        logger.exception(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
