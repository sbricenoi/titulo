"""
Behavior Classifier - Clasificación de comportamientos de hurones.

Este módulo implementa clasificación de comportamientos usando modelos
de deep learning que analizan secuencias temporales de frames.

Autor: Sistema de Monitoreo de Hurones
Fecha: 2025-10-28
"""

import torch
import torch.nn as nn
import numpy as np
import cv2
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from collections import deque
from pathlib import Path
from loguru import logger


@dataclass
class BehaviorPrediction:
    """
    Predicción de comportamiento.
    
    Attributes:
        behavior: Nombre del comportamiento
        confidence: Confianza de la predicción (0-1)
        probabilities: Probabilidades de todas las clases
        timestamp: Timestamp de la predicción
    """
    behavior: str
    confidence: float
    probabilities: Dict[str, float]
    timestamp: float
    
    def to_dict(self) -> Dict:
        """Convertir a diccionario."""
        return {
            "behavior": self.behavior,
            "confidence": float(self.confidence),
            "probabilities": {
                k: float(v) for k, v in self.probabilities.items()
            },
            "timestamp": self.timestamp,
        }


class CNN_LSTM_Classifier(nn.Module):
    """
    Modelo CNN+LSTM para clasificación de comportamientos.
    
    Arquitectura:
    - CNN para features espaciales (por frame)
    - LSTM para modelar secuencia temporal
    - Clasificador final
    """
    
    def __init__(
        self,
        num_classes: int = 7,
        lstm_hidden: int = 256,
        lstm_layers: int = 2,
        dropout: float = 0.3
    ):
        """
        Inicializar modelo.
        
        Args:
            num_classes: Número de clases de comportamiento
            lstm_hidden: Tamaño oculto del LSTM
            lstm_layers: Número de capas LSTM
            dropout: Tasa de dropout
        """
        super().__init__()
        
        # CNN feature extractor (MobileNetV2 como backbone)
        mobilenet = torch.hub.load(
            'pytorch/vision:v0.10.0',
            'mobilenet_v2',
            pretrained=True
        )
        
        # Usar solo features (quitar clasificador)
        self.cnn = nn.Sequential(*list(mobilenet.children())[:-1])
        cnn_output_size = 1280  # MobileNetV2 output
        
        # Congelar capas CNN inicialmente (fine-tuning posterior)
        for param in self.cnn.parameters():
            param.requires_grad = False
        
        # LSTM para secuencia temporal
        self.lstm = nn.LSTM(
            input_size=cnn_output_size,
            hidden_size=lstm_hidden,
            num_layers=lstm_layers,
            batch_first=True,
            dropout=dropout if lstm_layers > 1 else 0
        )
        
        # Clasificador
        self.classifier = nn.Sequential(
            nn.Linear(lstm_hidden, 128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, num_classes)
        )
    
    def forward(self, x):
        """
        Forward pass.
        
        Args:
            x: Tensor de entrada [batch, sequence_length, channels, height, width]
            
        Returns:
            Logits de clasificación [batch, num_classes]
        """
        batch_size, seq_len, c, h, w = x.shape
        
        # Procesar cada frame con CNN
        x = x.view(batch_size * seq_len, c, h, w)
        features = self.cnn(x)
        features = features.view(batch_size, seq_len, -1)
        
        # LSTM
        lstm_out, _ = self.lstm(features)
        
        # Usar output del último timestep
        last_output = lstm_out[:, -1, :]
        
        # Clasificador
        logits = self.classifier(last_output)
        
        return logits


class BehaviorClassifier:
    """
    Clasificador de comportamientos de hurones.
    
    Analiza secuencias de frames para determinar el comportamiento actual
    (comer, dormir, jugar, etc.).
    
    Ejemplo:
        >>> classifier = BehaviorClassifier(model_path="behavior_model.pth")
        >>> prediction = classifier.classify(tracked_object, frame_sequence)
        >>> print(f"Comportamiento: {prediction.behavior}")
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        sequence_length: int = 30,
        input_size: Tuple[int, int] = (224, 224),
        confidence_threshold: float = 0.6,
        device: Optional[str] = None,
        behavior_classes: Optional[List[str]] = None
    ):
        """
        Inicializar clasificador.
        
        Args:
            model_path: Path al modelo entrenado (.pth)
            sequence_length: Número de frames para análisis
            input_size: Tamaño de entrada (width, height)
            confidence_threshold: Umbral de confianza mínimo
            device: Dispositivo ('cuda', 'cpu', 'mps')
            behavior_classes: Lista de nombres de comportamientos
        """
        self.sequence_length = sequence_length
        self.input_size = input_size
        self.confidence_threshold = confidence_threshold
        
        # Clases de comportamiento por defecto
        self.behavior_classes = behavior_classes or [
            "eating", "sleeping", "playing", "walking",
            "interacting", "exploring", "idle"
        ]
        self.num_classes = len(self.behavior_classes)
        
        # Determinar dispositivo
        if device is None:
            device = self._get_device()
        self.device = device
        
        # Crear modelo
        self.model = CNN_LSTM_Classifier(
            num_classes=self.num_classes,
            lstm_hidden=256,
            lstm_layers=2
        )
        
        # Cargar pesos si se proporciona path
        if model_path and Path(model_path).exists():
            logger.info(f"Cargando modelo desde {model_path}")
            self.model.load_state_dict(
                torch.load(model_path, map_location=device)
            )
        else:
            logger.warning(
                "No se proporcionó modelo entrenado o no existe. "
                "Usando modelo sin entrenar (predicciones aleatorias)."
            )
        
        self.model.to(device)
        self.model.eval()
        
        # Buffers de secuencias por objeto
        self.frame_buffers: Dict[str, deque] = {}
        
        # Estadísticas
        self.stats = {
            "total_predictions": 0,
            "behavior_counts": {b: 0 for b in self.behavior_classes},
        }
        
        logger.info(
            f"BehaviorClassifier inicializado: "
            f"classes={self.num_classes}, seq_len={sequence_length}, "
            f"device={device}"
        )
    
    def _get_device(self) -> str:
        """Determinar mejor dispositivo disponible."""
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    def _preprocess_frame(self, frame: np.ndarray) -> torch.Tensor:
        """
        Preprocesar frame para el modelo.
        
        Args:
            frame: Frame RGB [H, W, C]
            
        Returns:
            Tensor normalizado [C, H, W]
        """
        # Resize
        frame = cv2.resize(frame, self.input_size)
        
        # Convertir a RGB si es BGR
        if frame.shape[2] == 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Normalizar (ImageNet stats)
        frame = frame.astype(np.float32) / 255.0
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        frame = (frame - mean) / std
        
        # Convertir a tensor [C, H, W]
        frame = torch.from_numpy(frame.transpose(2, 0, 1)).float()
        
        return frame
    
    def add_frame(self, object_id: str, frame_patch: np.ndarray):
        """
        Agregar frame al buffer de un objeto.
        
        Args:
            object_id: ID único del objeto
            frame_patch: Patch del frame correspondiente al objeto
        """
        if object_id not in self.frame_buffers:
            self.frame_buffers[object_id] = deque(maxlen=self.sequence_length)
        
        # Preprocesar y agregar
        processed = self._preprocess_frame(frame_patch)
        self.frame_buffers[object_id].append(processed)
    
    def classify(
        self,
        object_id: str,
        frame_patch: Optional[np.ndarray] = None,
        timestamp: Optional[float] = None
    ) -> Optional[BehaviorPrediction]:
        """
        Clasificar comportamiento de un objeto.
        
        Args:
            object_id: ID único del objeto
            frame_patch: Frame patch actual (opcional si ya se agregó)
            timestamp: Timestamp de la predicción
            
        Returns:
            BehaviorPrediction o None si no hay suficientes frames
        """
        import time
        
        if timestamp is None:
            timestamp = time.time()
        
        # Agregar frame si se proporciona
        if frame_patch is not None:
            self.add_frame(object_id, frame_patch)
        
        # Verificar que hay suficientes frames
        if object_id not in self.frame_buffers:
            return None
        
        buffer = self.frame_buffers[object_id]
        if len(buffer) < self.sequence_length:
            return None
        
        # Preparar secuencia
        sequence = torch.stack(list(buffer))  # [seq_len, C, H, W]
        sequence = sequence.unsqueeze(0)  # [1, seq_len, C, H, W]
        sequence = sequence.to(self.device)
        
        # Inferencia
        with torch.no_grad():
            logits = self.model(sequence)
            probabilities = torch.softmax(logits, dim=1)
            confidence, predicted_class = torch.max(probabilities, dim=1)
        
        # Convertir a numpy
        probabilities = probabilities.cpu().numpy()[0]
        confidence = float(confidence.cpu().numpy())
        predicted_class = int(predicted_class.cpu().numpy())
        
        # Crear diccionario de probabilidades
        prob_dict = {
            self.behavior_classes[i]: float(probabilities[i])
            for i in range(self.num_classes)
        }
        
        behavior = self.behavior_classes[predicted_class]
        
        # Actualizar estadísticas
        self.stats["total_predictions"] += 1
        self.stats["behavior_counts"][behavior] += 1
        
        prediction = BehaviorPrediction(
            behavior=behavior,
            confidence=confidence,
            probabilities=prob_dict,
            timestamp=timestamp
        )
        
        return prediction
    
    def classify_batch(
        self,
        object_ids: List[str],
        frame_patches: List[np.ndarray]
    ) -> List[Optional[BehaviorPrediction]]:
        """
        Clasificar múltiples objetos en batch.
        
        Args:
            object_ids: Lista de IDs de objetos
            frame_patches: Lista de patches
            
        Returns:
            Lista de predicciones
        """
        predictions = []
        
        for obj_id, patch in zip(object_ids, frame_patches):
            pred = self.classify(obj_id, patch)
            predictions.append(pred)
        
        return predictions
    
    def detect_interaction(
        self,
        object_ids: List[str],
        positions: List[np.ndarray],
        distance_threshold: float = 100.0
    ) -> List[Tuple[str, str]]:
        """
        Detectar interacciones entre objetos (hurones cercanos).
        
        Args:
            object_ids: Lista de IDs
            positions: Lista de posiciones (centros)
            distance_threshold: Distancia máxima para interacción (píxeles)
            
        Returns:
            Lista de pares de IDs que están interactuando
        """
        interactions = []
        
        for i in range(len(object_ids)):
            for j in range(i + 1, len(object_ids)):
                # Calcular distancia
                dist = np.linalg.norm(positions[i] - positions[j])
                
                if dist < distance_threshold:
                    interactions.append((object_ids[i], object_ids[j]))
        
        return interactions
    
    def get_stats(self) -> Dict:
        """Obtener estadísticas del clasificador."""
        stats = self.stats.copy()
        stats["active_buffers"] = len(self.frame_buffers)
        return stats
    
    def clear_buffer(self, object_id: str):
        """Limpiar buffer de un objeto."""
        if object_id in self.frame_buffers:
            del self.frame_buffers[object_id]
    
    def clear_all_buffers(self):
        """Limpiar todos los buffers."""
        self.frame_buffers.clear()


# ==================== EJEMPLO DE USO ====================
if __name__ == "__main__":
    """Ejemplo de uso del BehaviorClassifier."""
    
    # Configurar logging
    logger.add("behavior_test.log", rotation="10 MB")
    
    # Crear clasificador
    classifier = BehaviorClassifier(
        model_path=None,  # Sin modelo entrenado para testing
        sequence_length=30,
        device="cpu"
    )
    
    logger.info("Simulando clasificación de comportamiento...")
    
    # Simular 40 frames para un objeto
    object_id = "F0"
    
    for i in range(40):
        # Frame sintético
        frame_patch = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # Clasificar
        prediction = classifier.classify(object_id, frame_patch)
        
        if prediction:
            logger.info(
                f"Frame {i}: {prediction.behavior} "
                f"(conf={prediction.confidence:.2f})"
            )
        else:
            logger.info(f"Frame {i}: Acumulando frames...")
    
    # Estadísticas
    stats = classifier.get_stats()
    logger.info(f"\nEstadísticas:")
    logger.info(f"  Total predicciones: {stats['total_predictions']}")
    logger.info(f"  Conteo de comportamientos:")
    for behavior, count in stats['behavior_counts'].items():
        if count > 0:
            logger.info(f"    {behavior}: {count}")
    
    logger.info("\nTest finalizado")





