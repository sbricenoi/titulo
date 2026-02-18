"""
Incremental Trainer - Reentrenamiento incremental de modelos.

Este módulo implementa entrenamiento continuo que permite actualizar
modelos con nuevos datos sin olvidar conocimiento previo.

Autor: Sistema de Monitoreo de Hurones
Fecha: 2025-10-28
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, random_split
import numpy as np
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from loguru import logger
import json


@dataclass
class TrainingConfig:
    """Configuración de entrenamiento."""
    batch_size: int = 16
    learning_rate: float = 0.001
    epochs: int = 50
    validation_split: float = 0.2
    early_stopping_patience: int = 10
    checkpoint_dir: str = "data/models/checkpoints"
    replay_buffer_size: int = 1000
    new_data_threshold: int = 100


class BehaviorDataset(Dataset):
    """
    Dataset para secuencias de comportamiento.
    
    Cada muestra es una secuencia de frames y su label de comportamiento.
    """
    
    def __init__(
        self,
        sequences: List[torch.Tensor],
        labels: List[int],
        transform=None
    ):
        """
        Inicializar dataset.
        
        Args:
            sequences: Lista de secuencias [seq_len, C, H, W]
            labels: Lista de labels (índices de clase)
            transform: Transformaciones opcionales
        """
        assert len(sequences) == len(labels), "Mismatch entre sequences y labels"
        
        self.sequences = sequences
        self.labels = labels
        self.transform = transform
    
    def __len__(self) -> int:
        return len(self.sequences)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        sequence = self.sequences[idx]
        label = self.labels[idx]
        
        if self.transform:
            sequence = self.transform(sequence)
        
        return sequence, label


class IncrementalTrainer:
    """
    Entrenador incremental para modelos de comportamiento.
    
    Características:
    - Continual learning sin olvido catastrófico
    - Replay buffer con muestras antiguas
    - Early stopping
    - Checkpointing automático
    - Métricas de evaluación
    
    Ejemplo:
        >>> trainer = IncrementalTrainer(model, data_path="data/training")
        >>> trainer.add_training_data(new_clips, new_labels)
        >>> metrics = trainer.train_epoch()
        >>> trainer.save_checkpoint("checkpoint.pth")
    """
    
    def __init__(
        self,
        model: nn.Module,
        data_path: str,
        config: Optional[TrainingConfig] = None,
        device: Optional[str] = None
    ):
        """
        Inicializar trainer.
        
        Args:
            model: Modelo a entrenar
            data_path: Path a datos de entrenamiento
            config: Configuración de entrenamiento
            device: Dispositivo ('cuda', 'cpu', 'mps')
        """
        self.model = model
        self.data_path = Path(data_path)
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        self.config = config or TrainingConfig()
        
        # Determinar dispositivo
        if device is None:
            device = self._get_device()
        self.device = device
        
        self.model.to(device)
        
        # Optimizador y loss
        self.optimizer = optim.Adam(
            self.model.parameters(),
            lr=self.config.learning_rate
        )
        self.criterion = nn.CrossEntropyLoss()
        
        # Scheduler para learning rate
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer,
            mode='min',
            factor=0.5,
            patience=5,
            verbose=True
        )
        
        # Replay buffer (para evitar olvido catastrófico)
        self.replay_buffer = {
            'sequences': [],
            'labels': []
        }
        
        # Nuevos datos pendientes
        self.new_data = {
            'sequences': [],
            'labels': []
        }
        
        # Historia de entrenamiento
        self.history = {
            'train_loss': [],
            'val_loss': [],
            'train_acc': [],
            'val_acc': [],
            'epochs': 0
        }
        
        # Early stopping
        self.best_val_loss = float('inf')
        self.patience_counter = 0
        
        logger.info(
            f"IncrementalTrainer inicializado: "
            f"device={device}, lr={self.config.learning_rate}"
        )
    
    def _get_device(self) -> str:
        """Determinar mejor dispositivo disponible."""
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    def add_training_data(
        self,
        sequences: List[torch.Tensor],
        labels: List[int]
    ):
        """
        Agregar nuevos datos de entrenamiento.
        
        Args:
            sequences: Lista de secuencias de frames
            labels: Lista de labels (índices de clase)
        """
        self.new_data['sequences'].extend(sequences)
        self.new_data['labels'].extend(labels)
        
        logger.info(
            f"Agregados {len(sequences)} ejemplos. "
            f"Total nuevos: {len(self.new_data['sequences'])}"
        )
        
        # Si alcanzó el umbral, agregar al replay buffer
        if len(self.new_data['sequences']) >= self.config.new_data_threshold:
            self._update_replay_buffer()
    
    def _update_replay_buffer(self):
        """Actualizar replay buffer con nuevos datos."""
        # Agregar nuevos datos al buffer
        self.replay_buffer['sequences'].extend(self.new_data['sequences'])
        self.replay_buffer['labels'].extend(self.new_data['labels'])
        
        # Mantener tamaño máximo del buffer (FIFO)
        if len(self.replay_buffer['sequences']) > self.config.replay_buffer_size:
            excess = len(self.replay_buffer['sequences']) - self.config.replay_buffer_size
            self.replay_buffer['sequences'] = self.replay_buffer['sequences'][excess:]
            self.replay_buffer['labels'] = self.replay_buffer['labels'][excess:]
        
        logger.info(
            f"Replay buffer actualizado. "
            f"Tamaño: {len(self.replay_buffer['sequences'])}"
        )
        
        # Limpiar nuevos datos
        self.new_data = {'sequences': [], 'labels': []}
    
    def _create_dataloader(
        self,
        sequences: List[torch.Tensor],
        labels: List[int],
        shuffle: bool = True
    ) -> DataLoader:
        """Crear DataLoader."""
        dataset = BehaviorDataset(sequences, labels)
        
        dataloader = DataLoader(
            dataset,
            batch_size=self.config.batch_size,
            shuffle=shuffle,
            num_workers=0  # 0 para evitar problemas con pickling
        )
        
        return dataloader
    
    def train_epoch(self) -> Dict[str, float]:
        """
        Entrenar una época.
        
        Returns:
            Diccionario con métricas (loss, accuracy)
        """
        # Combinar replay buffer con nuevos datos
        all_sequences = (
            self.replay_buffer['sequences'] +
            self.new_data['sequences']
        )
        all_labels = (
            self.replay_buffer['labels'] +
            self.new_data['labels']
        )
        
        if len(all_sequences) == 0:
            logger.warning("No hay datos para entrenar")
            return {"train_loss": 0, "train_acc": 0, "val_loss": 0, "val_acc": 0}
        
        # Split train/validation
        dataset = BehaviorDataset(all_sequences, all_labels)
        val_size = int(len(dataset) * self.config.validation_split)
        train_size = len(dataset) - val_size
        
        train_dataset, val_dataset = random_split(
            dataset,
            [train_size, val_size]
        )
        
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.config.batch_size,
            shuffle=True
        )
        val_loader = DataLoader(
            val_dataset,
            batch_size=self.config.batch_size,
            shuffle=False
        )
        
        # Entrenar
        self.model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0
        
        for sequences, labels in train_loader:
            sequences = sequences.to(self.device)
            labels = labels.to(self.device)
            
            # Forward
            self.optimizer.zero_grad()
            outputs = self.model(sequences)
            loss = self.criterion(outputs, labels)
            
            # Backward
            loss.backward()
            self.optimizer.step()
            
            # Métricas
            train_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            train_total += labels.size(0)
            train_correct += (predicted == labels).sum().item()
        
        train_loss /= len(train_loader)
        train_acc = train_correct / train_total if train_total > 0 else 0
        
        # Validar
        val_loss, val_acc = self.evaluate(val_loader)
        
        # Scheduler
        self.scheduler.step(val_loss)
        
        # Early stopping
        if val_loss < self.best_val_loss:
            self.best_val_loss = val_loss
            self.patience_counter = 0
        else:
            self.patience_counter += 1
        
        # Actualizar historia
        self.history['train_loss'].append(train_loss)
        self.history['val_loss'].append(val_loss)
        self.history['train_acc'].append(train_acc)
        self.history['val_acc'].append(val_acc)
        self.history['epochs'] += 1
        
        metrics = {
            "train_loss": train_loss,
            "train_acc": train_acc,
            "val_loss": val_loss,
            "val_acc": val_acc,
            "patience": self.patience_counter
        }
        
        logger.info(
            f"Epoch {self.history['epochs']}: "
            f"train_loss={train_loss:.4f}, train_acc={train_acc:.4f}, "
            f"val_loss={val_loss:.4f}, val_acc={val_acc:.4f}"
        )
        
        return metrics
    
    def evaluate(self, dataloader: DataLoader) -> Tuple[float, float]:
        """
        Evaluar modelo.
        
        Args:
            dataloader: DataLoader de evaluación
            
        Returns:
            (loss, accuracy)
        """
        self.model.eval()
        
        total_loss = 0.0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for sequences, labels in dataloader:
                sequences = sequences.to(self.device)
                labels = labels.to(self.device)
                
                outputs = self.model(sequences)
                loss = self.criterion(outputs, labels)
                
                total_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
        
        avg_loss = total_loss / len(dataloader) if len(dataloader) > 0 else 0
        accuracy = correct / total if total > 0 else 0
        
        return avg_loss, accuracy
    
    def train(self, epochs: Optional[int] = None) -> Dict:
        """
        Entrenar múltiples épocas.
        
        Args:
            epochs: Número de épocas (None = usar config)
            
        Returns:
            Historia de entrenamiento
        """
        if epochs is None:
            epochs = self.config.epochs
        
        logger.info(f"Iniciando entrenamiento por {epochs} épocas...")
        
        for epoch in range(epochs):
            metrics = self.train_epoch()
            
            # Early stopping
            if self.patience_counter >= self.config.early_stopping_patience:
                logger.info(
                    f"Early stopping en época {epoch+1} "
                    f"(paciencia={self.config.early_stopping_patience})"
                )
                break
            
            # Checkpoint cada 10 épocas
            if (epoch + 1) % 10 == 0:
                checkpoint_path = (
                    Path(self.config.checkpoint_dir) /
                    f"checkpoint_epoch_{self.history['epochs']}.pth"
                )
                self.save_checkpoint(str(checkpoint_path))
        
        logger.info("Entrenamiento completado")
        return self.history
    
    def save_checkpoint(self, path: str):
        """
        Guardar checkpoint del modelo.
        
        Args:
            path: Path donde guardar el checkpoint
        """
        checkpoint = {
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
            'history': self.history,
            'config': vars(self.config),
            'best_val_loss': self.best_val_loss,
        }
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        torch.save(checkpoint, path)
        
        logger.info(f"Checkpoint guardado en {path}")
    
    def load_checkpoint(self, path: str):
        """
        Cargar checkpoint.
        
        Args:
            path: Path del checkpoint
        """
        checkpoint = torch.load(path, map_location=self.device)
        
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        self.history = checkpoint['history']
        self.best_val_loss = checkpoint['best_val_loss']
        
        logger.info(f"Checkpoint cargado desde {path}")
    
    def should_retrain(self) -> bool:
        """
        Determinar si se debe reentrenar.
        
        Returns:
            True si hay suficientes datos nuevos
        """
        return len(self.new_data['sequences']) >= self.config.new_data_threshold


# ==================== EJEMPLO DE USO ====================
if __name__ == "__main__":
    """Ejemplo de uso del IncrementalTrainer."""
    
    from ai.behavior_model import CNN_LSTM_Classifier
    
    # Configurar logging
    logger.add("trainer_test.log", rotation="10 MB")
    
    # Crear modelo
    model = CNN_LSTM_Classifier(num_classes=7)
    
    # Crear trainer
    trainer = IncrementalTrainer(
        model=model,
        data_path="data/training",
        device="cpu"
    )
    
    logger.info("Simulando datos de entrenamiento...")
    
    # Generar datos sintéticos
    num_samples = 50
    sequences = []
    labels = []
    
    for i in range(num_samples):
        # Secuencia de 30 frames de 224x224
        seq = torch.randn(30, 3, 224, 224)
        label = i % 7  # 7 clases
        
        sequences.append(seq)
        labels.append(label)
    
    # Agregar datos
    trainer.add_training_data(sequences, labels)
    
    # Entrenar
    logger.info("Entrenando modelo...")
    history = trainer.train(epochs=5)
    
    logger.info(f"\nResultados finales:")
    logger.info(f"  Épocas entrenadas: {history['epochs']}")
    logger.info(f"  Mejor val_loss: {trainer.best_val_loss:.4f}")
    
    # Guardar checkpoint
    trainer.save_checkpoint("test_checkpoint.pth")
    
    logger.info("\nTest finalizado")





