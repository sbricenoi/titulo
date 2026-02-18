#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entrenamiento de Modelo YOLOv8 Personalizado para Hurones

Este script:
1. Exporta frames clasificados en formato YOLO
2. Genera anotaciones automáticamente
3. Fine-tuning de YOLOv8 con tus datos
4. Valida el modelo entrenado

Uso:
    python train_ferret_model.py
    python train_ferret_model.py --epochs 100 --batch 16
"""

import os
import sys
import json
import shutil
import sqlite3
import random
from pathlib import Path
from typing import List, Dict, Tuple
import cv2
import numpy as np
import yaml
from loguru import logger
from tqdm import tqdm

from config import config

# Configurar logger
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
)


class YOLODatasetExporter:
    """Exportador de dataset en formato YOLO."""
    
    def __init__(
        self,
        db_path: Path,
        frames_dir: Path,
        output_dir: Path
    ):
        """
        Inicializar exportador.
        
        Args:
            db_path: Path a classifications.db
            frames_dir: Directorio con frames clasificados
            output_dir: Directorio de salida para dataset YOLO
        """
        self.db_path = db_path
        self.frames_dir = frames_dir
        self.output_dir = Path(output_dir)
        
        # Mapeo de behaviors a class IDs
        self.class_mapping = {
            "exploring": 0,
            "eating": 0,
            "resting": 0,
            "playing": 0,
            "grooming": 0,
            "drinking": 0,
            # Todos los comportamientos se mapean a clase 0: "ferret"
        }
        
        # Crear directorios
        self.setup_directories()
    
    def setup_directories(self):
        """Crear estructura de directorios YOLO."""
        for split in ['train', 'val']:
            (self.output_dir / split / 'images').mkdir(parents=True, exist_ok=True)
            (self.output_dir / split / 'labels').mkdir(parents=True, exist_ok=True)
        
        logger.info(f"📁 Directorio dataset: {self.output_dir}")
    
    def get_classified_frames(self) -> List[Tuple[str, str]]:
        """
        Obtener frames con hurones clasificados de la BD.
        
        Returns:
            Lista de tuplas (filename, behavior)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Solo frames con hurones (excluir no_ferret y unknown)
        cursor.execute("""
            SELECT filename, behavior
            FROM frame_classifications
            WHERE behavior NOT IN ('no_ferret', 'unknown')
            ORDER BY filename
        """)
        
        frames = cursor.fetchall()
        conn.close()
        
        logger.info(f"✓ {len(frames)} frames con hurones encontrados")
        return frames
    
    def create_bbox_annotation(
        self,
        frame: np.ndarray,
        class_id: int = 0
    ) -> str:
        """
        Crear anotación YOLO automática.
        
        Como no tenemos bboxes originales, usamos heurística:
        - Detectar región con mayor actividad/contraste
        - O usar bbox central como aproximación
        
        Args:
            frame: Frame de imagen
            class_id: ID de clase (0 = ferret)
        
        Returns:
            Línea de anotación YOLO: "class x_center y_center width height"
        """
        h, w = frame.shape[:2]
        
        # Convertir a escala de grises
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detectar contornos (objetos)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # Usar el contorno más grande como aproximación del hurón
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, cw, ch = cv2.boundingRect(largest_contour)
            
            # Filtrar contornos muy pequeños o muy grandes (ruido o fondo)
            area = cw * ch
            if area < (w * h * 0.01) or area > (w * h * 0.9):
                # Usar bbox central como fallback
                x, y = int(w * 0.25), int(h * 0.25)
                cw, ch = int(w * 0.5), int(h * 0.5)
        else:
            # No se detectaron contornos, usar bbox central
            x, y = int(w * 0.25), int(h * 0.25)
            cw, ch = int(w * 0.5), int(h * 0.5)
        
        # Normalizar a formato YOLO [0-1]
        x_center = (x + cw / 2) / w
        y_center = (y + ch / 2) / h
        width = cw / w
        height = ch / h
        
        # Asegurar valores en rango [0, 1]
        x_center = max(0, min(1, x_center))
        y_center = max(0, min(1, y_center))
        width = max(0, min(1, width))
        height = max(0, min(1, height))
        
        return f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"
    
    def export_dataset(self, val_split: float = 0.3) -> Dict:
        """
        Exportar dataset completo en formato YOLO.
        
        Args:
            val_split: Porcentaje de validación (0.3 = 30%)
        
        Returns:
            Estadísticas del dataset
        """
        logger.info("=" * 70)
        logger.info("📦 EXPORTANDO DATASET EN FORMATO YOLO")
        logger.info("=" * 70)
        
        # Obtener frames clasificados
        frames = self.get_classified_frames()
        
        if len(frames) == 0:
            logger.error("❌ No hay frames clasificados")
            return {}
        
        # Mezclar y dividir en train/val
        random.shuffle(frames)
        split_idx = int(len(frames) * (1 - val_split))
        
        train_frames = frames[:split_idx]
        val_frames = frames[split_idx:]
        
        logger.info(f"   Train: {len(train_frames)} frames")
        logger.info(f"   Val:   {len(val_frames)} frames")
        logger.info("")
        
        stats = {
            "total": len(frames),
            "train": 0,
            "val": 0,
            "skipped": 0
        }
        
        # Exportar train
        logger.info("📸 Exportando train set...")
        for filename, behavior in tqdm(train_frames, desc="   Train"):
            if self._export_frame(filename, behavior, 'train'):
                stats["train"] += 1
            else:
                stats["skipped"] += 1
        
        # Exportar val
        logger.info("📸 Exportando validation set...")
        for filename, behavior in tqdm(val_frames, desc="   Val"):
            if self._export_frame(filename, behavior, 'val'):
                stats["val"] += 1
            else:
                stats["skipped"] += 1
        
        logger.success(f"\n✓ Dataset exportado:")
        logger.info(f"   Train: {stats['train']} imágenes")
        logger.info(f"   Val:   {stats['val']} imágenes")
        logger.info(f"   Saltados: {stats['skipped']}")
        
        return stats
    
    def _export_frame(
        self,
        filename: str,
        behavior: str,
        split: str
    ) -> bool:
        """
        Exportar un frame individual.
        
        Args:
            filename: Nombre del archivo
            behavior: Comportamiento clasificado
            split: 'train' o 'val'
        
        Returns:
            True si se exportó exitosamente
        """
        # Encontrar frame en el directorio
        frame_path = self.frames_dir / filename
        
        if not frame_path.exists():
            logger.warning(f"Frame no encontrado: {filename}")
            return False
        
        try:
            # Leer frame
            frame = cv2.imread(str(frame_path))
            
            if frame is None:
                logger.warning(f"No se pudo leer: {filename}")
                return False
            
            # Crear anotación YOLO
            class_id = self.class_mapping.get(behavior, 0)
            annotation = self.create_bbox_annotation(frame, class_id)
            
            # Paths de salida
            img_out = self.output_dir / split / 'images' / filename
            label_out = self.output_dir / split / 'labels' / f"{Path(filename).stem}.txt"
            
            # Copiar imagen
            shutil.copy2(frame_path, img_out)
            
            # Guardar anotación
            with open(label_out, 'w') as f:
                f.write(annotation + '\n')
            
            return True
            
        except Exception as e:
            logger.error(f"Error exportando {filename}: {e}")
            return False
    
    def create_yaml_config(self) -> Path:
        """
        Crear archivo de configuración YAML para YOLO.
        
        Returns:
            Path al archivo YAML
        """
        yaml_path = self.output_dir / 'ferret_dataset.yaml'
        
        config = {
            'path': str(self.output_dir.absolute()),
            'train': 'train/images',
            'val': 'val/images',
            'nc': 1,  # Número de clases
            'names': ['ferret']  # Nombres de clases
        }
        
        with open(yaml_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        logger.success(f"✓ Config YAML: {yaml_path}")
        
        return yaml_path


class FerretModelTrainer:
    """Entrenador de modelo YOLOv8 para hurones."""
    
    def __init__(
        self,
        dataset_yaml: Path,
        output_dir: Path = Path("runs/train")
    ):
        """
        Inicializar entrenador.
        
        Args:
            dataset_yaml: Path al YAML del dataset
            output_dir: Directorio de salida para runs
        """
        self.dataset_yaml = dataset_yaml
        self.output_dir = output_dir
        
        try:
            from ultralytics import YOLO
            self.YOLO = YOLO
            logger.success("✓ Ultralytics YOLO cargado")
        except ImportError:
            logger.error("❌ ultralytics no disponible")
            logger.info("   Instalar: pip install ultralytics")
            sys.exit(1)
    
    def train(
        self,
        base_model: str = "yolov8n.pt",
        epochs: int = 50,
        batch: int = 16,
        imgsz: int = 640,
        device: str = "cpu"
    ) -> Dict:
        """
        Entrenar modelo YOLOv8.
        
        Args:
            base_model: Modelo base para fine-tuning
            epochs: Número de épocas
            batch: Tamaño de batch
            imgsz: Tamaño de imagen
            device: 'cpu' o 'cuda'
        
        Returns:
            Resultados del entrenamiento
        """
        logger.info("=" * 70)
        logger.info("🚀 ENTRENANDO MODELO YOLOV8 PERSONALIZADO")
        logger.info("=" * 70)
        logger.info(f"Base model:  {base_model}")
        logger.info(f"Epochs:      {epochs}")
        logger.info(f"Batch:       {batch}")
        logger.info(f"Image size:  {imgsz}")
        logger.info(f"Device:      {device}")
        logger.info(f"Dataset:     {self.dataset_yaml}")
        logger.info("")
        
        try:
            # Cargar modelo base
            model = self.YOLO(base_model)
            
            # Entrenar
            results = model.train(
                data=str(self.dataset_yaml),
                epochs=epochs,
                batch=batch,
                imgsz=imgsz,
                device=device,
                project=str(self.output_dir.parent),
                name=self.output_dir.name,
                patience=10,  # Early stopping
                save=True,
                plots=True,
                verbose=True
            )
            
            logger.success("\n✓ Entrenamiento completado!")
            logger.info(f"   Modelo guardado en: {self.output_dir}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error durante entrenamiento: {e}")
            logger.exception(e)
            return {}
    
    def validate(self, model_path: Path) -> Dict:
        """
        Validar modelo entrenado.
        
        Args:
            model_path: Path al modelo (.pt)
        
        Returns:
            Métricas de validación
        """
        logger.info("\n📊 VALIDANDO MODELO...")
        
        try:
            model = self.YOLO(str(model_path))
            
            results = model.val(
                data=str(self.dataset_yaml),
                split='val'
            )
            
            logger.success("✓ Validación completada")
            
            # Mostrar métricas clave
            if hasattr(results, 'box'):
                box_metrics = results.box
                logger.info(f"   mAP50:     {box_metrics.map50:.3f}")
                logger.info(f"   mAP50-95:  {box_metrics.map:.3f}")
                logger.info(f"   Precision: {box_metrics.mp:.3f}")
                logger.info(f"   Recall:    {box_metrics.mr:.3f}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error durante validación: {e}")
            return {}


def main():
    """Punto de entrada."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Entrenar modelo YOLOv8 personalizado para hurones"
    )
    
    parser.add_argument("--epochs", type=int, default=50,
                       help="Número de épocas (default: 50)")
    parser.add_argument("--batch", type=int, default=16,
                       help="Tamaño de batch (default: 16)")
    parser.add_argument("--imgsz", type=int, default=640,
                       help="Tamaño de imagen (default: 640)")
    parser.add_argument("--device", type=str, default="cpu",
                       help="Device: cpu o cuda (default: cpu)")
    parser.add_argument("--val-split", type=float, default=0.3,
                       help="Split de validación (default: 0.3)")
    parser.add_argument("--export-only", action="store_true",
                       help="Solo exportar dataset sin entrenar")
    
    args = parser.parse_args()
    
    # Paths
    db_path = config.DATA_DIR / "classifications.db"
    frames_dir = config.DATA_DIR / "frames_for_classification"
    dataset_dir = config.DATA_DIR / "yolo_dataset"
    
    # 1. Exportar dataset
    logger.info("🎯 PASO 1: EXPORTAR DATASET")
    logger.info("")
    
    exporter = YOLODatasetExporter(
        db_path=db_path,
        frames_dir=frames_dir,
        output_dir=dataset_dir
    )
    
    stats = exporter.export_dataset(val_split=args.val_split)
    
    if stats.get('train', 0) == 0:
        logger.error("❌ No se exportaron frames de entrenamiento")
        sys.exit(1)
    
    # Crear YAML config
    yaml_path = exporter.create_yaml_config()
    
    logger.info("")
    
    if args.export_only:
        logger.info("✓ Dataset exportado (--export-only activado)")
        return
    
    # 2. Entrenar modelo
    logger.info("\n🎯 PASO 2: ENTRENAR MODELO")
    logger.info("")
    
    trainer = FerretModelTrainer(
        dataset_yaml=yaml_path,
        output_dir=Path("runs/train/ferret_detector_v1")
    )
    
    results = trainer.train(
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        device=args.device
    )
    
    # 3. Validar modelo
    best_model_path = Path("runs/train/ferret_detector_v1/weights/best.pt")
    
    if best_model_path.exists():
        trainer.validate(best_model_path)
        
        # Copiar a modelos
        models_dir = config.BASE_DIR / "models"
        models_dir.mkdir(exist_ok=True)
        
        final_model_path = models_dir / "ferret_detector_v1.pt"
        shutil.copy2(best_model_path, final_model_path)
        
        logger.success(f"\n🎉 MODELO LISTO: {final_model_path}")
        logger.info("\n📋 Para usar el nuevo modelo:")
        logger.info(f"   1. Actualizar config.py:")
        logger.info(f'      DETECTION_MODEL = "models/ferret_detector_v1.pt"')
        logger.info(f"   2. Reiniciar procesamiento de videos")
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ ENTRENAMIENTO COMPLETADO")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
