"""
Configuración centralizada del sistema de monitoreo multi-cámara.

Este módulo contiene todas las configuraciones del sistema, incluyendo:
- URLs de cámaras RTSP
- Parámetros de modelos IA
- Configuración de tracking y sincronización
- Paths de archivos y modelos
- Configuración de logging

Uso:
    from config import Config
    config = Config()
    print(config.CAMERA_URLS)
"""

import os
import sqlite3
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()


@dataclass
class Config:
    """Configuración principal del sistema."""
    
    # ==================== PATHS ====================
    # Directorio raíz del proyecto
    ROOT_DIR: Path = field(default_factory=lambda: Path(__file__).parent)
    DATA_DIR: Path = field(init=False)
    MODELS_DIR: Path = field(init=False)
    LOGS_DIR: Path = field(init=False)
    CALIBRATION_DIR: Path = field(init=False)
    TRAINING_DIR: Path = field(init=False)
    
    def __post_init__(self):
        """Inicializar paths derivados."""
        self.DATA_DIR = self.ROOT_DIR / "data"
        self.MODELS_DIR = self.DATA_DIR / "models"
        self.LOGS_DIR = self.DATA_DIR / "logs"
        self.CALIBRATION_DIR = self.DATA_DIR / "calibration"
        self.TRAINING_DIR = self.DATA_DIR / "training"
        
        # Crear directorios si no existen
        for directory in [self.DATA_DIR, self.MODELS_DIR, self.LOGS_DIR, 
                         self.CALIBRATION_DIR, self.TRAINING_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Cargar cámaras desde la base de datos
        self._load_cameras_from_db()
    
    # ==================== CÁMARAS ====================
    # URLs de las cámaras RTSP (cargadas dinámicamente desde BD)
    # Formato: rtsp://usuario:contraseña@ip:puerto/ruta
    CAMERA_URLS: List[str] = field(default_factory=list)
    
    # Nombres descriptivos para las cámaras (cargados dinámicamente desde BD)
    CAMERA_NAMES: List[str] = field(default_factory=list)
    
    # IDs de las cámaras (para mapeo con BD)
    CAMERA_IDS: List[int] = field(default_factory=list)
    
    # Configuración de captura (Reolink E1 Pro)
    CAMERA_FPS: int = 20                    # FPS real de la cámara: 20 fps
    CAMERA_RESOLUTION: tuple = (2880, 1616) # Resolución real: 2880x1616 (~3K)
    CAMERA_BUFFER_SIZE: int = 30            # Tamaño del buffer de frames
    CAMERA_RECONNECT_DELAY: int = 5         # Segundos antes de reintentar conexión
    CAMERA_TIMEOUT: int = 10                # Timeout de conexión en segundos
    USE_FFMPEG: bool = True                 # Usar FFmpeg en lugar de OpenCV (macOS)
    
    # ==================== SINCRONIZACIÓN ====================
    SYNC_TOLERANCE_MS: int = 100            # Tolerancia de sincronización (ms)
    SYNC_BUFFER_SIZE: int = 15              # Frames en buffer de sincronización
    SYNC_MAX_DELAY_MS: int = 500            # Máximo delay aceptable entre cámaras
    
    # ==================== DETECCIÓN ====================
    # Modelo de detección (YOLOv8)
    DETECTION_MODEL: str = "yolov8n.pt"     # Modelo por defecto (nano)
    # Para producción usar modelo custom: "models/yolov8_ferret.pt"
    
    # Clases a detectar (nombres de COCO dataset)
    # Detectamos gatos (cat) y hurones (cuando tengamos modelo custom, usaremos "ferret")
    DETECTION_CLASSES: List[str] = field(default_factory=lambda: [
        "person",    # Personas (para alertas de intrusos)
        "cat",       # Gatos
        "ferret",    # Hurones (modelo custom)
        "dog"        # Perros (opcional)
    ])
    
    # Mapeo de clases COCO a tipos de entidad
    CLASS_TO_ENTITY_TYPE: Dict[str, str] = field(default_factory=lambda: {
        "person": "person",     # Personas
        "cat": "cat",           # Gatos → mantener como gatos
        "ferret": "ferret",     # Hurones
        "dog": "dog"            # Perros → mantener como perros
    })
    
    DETECTION_CONFIDENCE: float = 0.5       # Umbral de confianza mínimo
    DETECTION_IOU_THRESHOLD: float = 0.45   # IoU para NMS
    DETECTION_MAX_OBJECTS: int = 10         # Máximo número de detecciones por frame
    DETECTION_INPUT_SIZE: int = 640         # Tamaño de entrada del modelo
    DETECTION_DEVICE: str = "cuda"          # "cuda", "cpu", o "mps" (Mac)
    
    # ==================== TRACKING ====================
    # DeepSORT / ByteTrack
    TRACKER_MAX_AGE: int = 30               # Frames sin detección antes de eliminar
    TRACKER_MIN_HITS: int = 3               # Detecciones mínimas para confirmar track
    TRACKER_IOU_THRESHOLD: float = 0.3      # IoU para asociación
    TRACKER_MAX_COSINE_DISTANCE: float = 0.2 # Distancia máxima para ReID features
    
    # Re-identificación
    REID_MODEL: str = "osnet_x1_0"          # Modelo ReID
    REID_MODEL_PATH: str = ""               # Path a modelo custom (opcional)
    REID_FEATURE_DIM: int = 512             # Dimensión de features ReID
    REID_CONFIDENCE_THRESHOLD: float = 0.7  # Umbral para matching entre cámaras
    
    # ==================== FUSIÓN MULTI-CÁMARA ====================
    FUSION_ENABLED: bool = True             # Activar fusión entre cámaras
    FUSION_SPATIAL_THRESHOLD: float = 0.5   # Umbral espacial para matching
    FUSION_FEATURE_WEIGHT: float = 0.7      # Peso de features vs posición
    FUSION_TIME_WINDOW_MS: int = 200        # Ventana temporal para fusión
    
    # Calibración 3D (opcional)
    FUSION_3D_ENABLED: bool = False         # Calcular posiciones 3D
    CALIBRATION_FILE: str = "calibration/intrinsics.json"
    
    # ==================== COMPORTAMIENTO ====================
    BEHAVIOR_MODEL: str = "behavior_classifier.pth"
    BEHAVIOR_SEQUENCE_LENGTH: int = 30      # Frames para análisis de comportamiento
    BEHAVIOR_STRIDE: int = 10               # Salto entre secuencias
    BEHAVIOR_CONFIDENCE_THRESHOLD: float = 0.6
    
    # Clases de comportamiento
    BEHAVIOR_CLASSES: List[str] = field(default_factory=lambda: [
        "eating",       # Comiendo
        "sleeping",     # Durmiendo
        "running",      # Corriendo
        "fighting",     # Peleando
        "defecating",   # Haciendo necesidades
        "walking",      # Caminando
        "idle",         # Inactivo/parado
    ])
    
    # Mapeo a español
    BEHAVIOR_NAMES_ES: Dict[str, str] = field(default_factory=lambda: {
        "eating": "Comiendo",
        "sleeping": "Durmiendo",
        "running": "Corriendo",
        "fighting": "Peleando",
        "defecating": "Haciendo necesidades",
        "walking": "Caminando",
        "idle": "Inactivo",
    })
    
    # ==================== ENTRENAMIENTO ====================
    TRAINING_BATCH_SIZE: int = 16
    TRAINING_LEARNING_RATE: float = 0.001
    TRAINING_EPOCHS: int = 100
    TRAINING_VALIDATION_SPLIT: float = 0.2
    TRAINING_EARLY_STOPPING_PATIENCE: int = 10
    TRAINING_CHECKPOINT_DIR: str = "data/models/checkpoints"
    
    # Reentrenamiento incremental
    INCREMENTAL_TRAINING_ENABLED: bool = True
    REPLAY_BUFFER_SIZE: int = 1000          # Muestras antiguas a mantener
    NEW_DATA_THRESHOLD: int = 100           # Nuevas muestras antes de reentrenar
    
    # ==================== LOGGING ====================
    LOG_LEVEL: str = "INFO"                 # DEBUG, INFO, WARNING, ERROR
    LOG_FILE: str = "data/logs/system.log"
    EVENT_LOG_FILE: str = "data/logs/events.log"
    LOG_ROTATION: str = "100 MB"            # Rotación de logs
    LOG_RETENTION: str = "30 days"          # Retención de logs
    LOG_FORMAT: str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    
    # ==================== VISUALIZACIÓN ====================
    VISUALIZE_ENABLED: bool = False         # Mostrar ventanas de visualización (False para usar solo Angular)
    VISUALIZE_FPS: int = 30                 # FPS de visualización
    VISUALIZE_RESOLUTION: tuple = (1280, 720)
    VISUALIZE_SHOW_IDS: bool = True         # Mostrar IDs en bounding boxes
    VISUALIZE_SHOW_BEHAVIOR: bool = True    # Mostrar comportamiento actual
    VISUALIZE_SHOW_TRAJECTORIES: bool = True # Mostrar trayectorias
    VISUALIZE_TRAJECTORY_LENGTH: int = 50   # Frames de historial de trayectoria
    
    # Colores para visualización (BGR)
    VISUALIZE_COLORS: List[tuple] = field(default_factory=lambda: [
        (255, 0, 0),      # Azul
        (0, 255, 0),      # Verde
        (0, 0, 255),      # Rojo
        (255, 255, 0),    # Cyan
        (255, 0, 255),    # Magenta
        (0, 255, 255),    # Amarillo
        (128, 0, 128),    # Púrpura
        (255, 165, 0),    # Naranja
    ])
    
    # ==================== API Y DASHBOARD ====================
    API_ENABLED: bool = False               # Activar API REST
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = False                # Auto-reload en desarrollo
    API_WORKERS: int = 4
    
    # WebSocket para streaming
    WEBSOCKET_ENABLED: bool = False
    WEBSOCKET_FPS: int = 15                 # FPS de streaming
    WEBSOCKET_COMPRESSION: bool = True
    
    # CORS
    API_CORS_ORIGINS: List[str] = field(default_factory=lambda: [
        "http://localhost:3000",
        "http://localhost:4200",
        "http://localhost:4201",
        "http://localhost:4203",
        "http://localhost:8000",
    ])
    
    # ==================== PERFORMANCE ====================
    # Threading y procesamiento
    USE_MULTIPROCESSING: bool = False       # Usar multiprocessing (vs threading)
    NUM_WORKERS: int = 2                    # Workers para procesamiento paralelo
    BATCH_PROCESSING: bool = False          # Procesar frames en batch
    BATCH_SIZE: int = 4
    
    # GPU
    USE_GPU: bool = True                    # Usar GPU si está disponible
    GPU_MEMORY_FRACTION: float = 0.8        # Fracción de memoria GPU a usar
    
    # ==================== ALERTAS Y NOTIFICACIONES ====================
    ALERTS_ENABLED: bool = False
    ALERT_BEHAVIORS: List[str] = field(default_factory=lambda: [
        "sleeping",  # Alerta si duerme mucho tiempo
    ])
    ALERT_DURATION_THRESHOLD: int = 300     # Segundos para disparar alerta
    
    # Email (opcional)
    ALERT_EMAIL_ENABLED: bool = False
    ALERT_EMAIL_TO: str = os.getenv("ALERT_EMAIL", "")
    ALERT_EMAIL_FROM: str = os.getenv("EMAIL_FROM", "")
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    
    # ==================== DEBUG Y DESARROLLO ====================
    DEBUG_MODE: bool = os.getenv("DEBUG", "False").lower() == "true"
    SAVE_DEBUG_FRAMES: bool = False         # Guardar frames para debugging
    DEBUG_FRAMES_DIR: str = "data/debug"
    PROFILE_PERFORMANCE: bool = False       # Perfilar rendimiento
    
    # ==================== MÉTODOS AUXILIARES ====================
    
    def get_model_path(self, model_name: str) -> Path:
        """Obtener path completo de un modelo."""
        return self.MODELS_DIR / model_name
    
    def get_log_path(self, log_name: str) -> Path:
        """Obtener path completo de un log."""
        return self.LOGS_DIR / log_name
    
    def get_camera_count(self) -> int:
        """Obtener número de cámaras configuradas."""
        return len(self.CAMERA_URLS)
    
    def get_device(self) -> str:
        """
        Determinar dispositivo a usar (cuda, mps, cpu).
        
        Returns:
            str: Nombre del dispositivo ('cuda', 'mps', o 'cpu')
        """
        if not self.USE_GPU:
            return "cpu"
        
        import torch
        
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir configuración a diccionario."""
        return {
            key: value for key, value in self.__dict__.items()
            if not key.startswith('_')
        }
    
    def _load_cameras_from_db(self):
        """Cargar cámaras activas desde la base de datos."""
        db_path = self.DATA_DIR / "cameras.db"
        
        if not db_path.exists():
            # Si no existe la BD, usar configuración por defecto (vacía)
            return
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Obtener cámaras activas ordenadas por ID
            cursor.execute("""
                SELECT id, name, rtsp_url 
                FROM cameras 
                WHERE is_active = 1 
                ORDER BY id
            """)
            
            cameras = cursor.fetchall()
            conn.close()
            
            if cameras:
                self.CAMERA_IDS = [cam[0] for cam in cameras]
                self.CAMERA_NAMES = [cam[1] for cam in cameras]
                self.CAMERA_URLS = [cam[2] for cam in cameras]
                
        except Exception as e:
            # Si hay error, usar configuración por defecto (vacía)
            print(f"⚠️ Error cargando cámaras desde BD: {e}")
            pass
    
    def validate(self) -> bool:
        """
        Validar configuración.
        
        Returns:
            bool: True si la configuración es válida
        
        Raises:
            ValueError: Si hay errores de configuración
        """
        # Validar URLs de cámaras
        if not self.CAMERA_URLS:
            raise ValueError("No hay cámaras configuradas en CAMERA_URLS")
        
        # Validar que hay nombres para todas las cámaras
        if len(self.CAMERA_NAMES) != len(self.CAMERA_URLS):
            raise ValueError(f"Número de nombres de cámaras ({len(self.CAMERA_NAMES)}) "
                           f"no coincide con número de URLs ({len(self.CAMERA_URLS)})")
        
        # Validar umbrales
        if not 0 <= self.DETECTION_CONFIDENCE <= 1:
            raise ValueError("DETECTION_CONFIDENCE debe estar entre 0 y 1")
        
        if not 0 <= self.REID_CONFIDENCE_THRESHOLD <= 1:
            raise ValueError("REID_CONFIDENCE_THRESHOLD debe estar entre 0 y 1")
        
        # Validar paths de modelos existen (si no son modelos por defecto)
        # Esta validación se puede hacer más adelante cuando se carguen los modelos
        
        return True


# ==================== INSTANCIA GLOBAL ====================
# Crear instancia global de configuración
config = Config()

# Validar al importar (comentar si causa problemas en testing)
# config.validate()


# ==================== EJEMPLO DE USO ====================
if __name__ == "__main__":
    """Ejemplo de uso de la configuración."""
    
    print("=" * 60)
    print("CONFIGURACIÓN DEL SISTEMA")
    print("=" * 60)
    
    print(f"\n📹 Cámaras configuradas: {config.get_camera_count()}")
    for i, (url, name) in enumerate(zip(config.CAMERA_URLS, config.CAMERA_NAMES), 1):
        # Ocultar credenciales en el print
        safe_url = url.split('@')[-1] if '@' in url else url
        print(f"  {i}. {name}: rtsp://***@{safe_url}")
    
    print(f"\n🤖 Modelo de detección: {config.DETECTION_MODEL}")
    print(f"🎯 Confianza mínima: {config.DETECTION_CONFIDENCE}")
    print(f"💻 Dispositivo: {config.get_device()}")
    
    print(f"\n📊 Comportamientos detectables: {len(config.BEHAVIOR_CLASSES)}")
    for behavior in config.BEHAVIOR_CLASSES:
        print(f"  - {behavior} ({config.BEHAVIOR_NAMES_ES.get(behavior, behavior)})")
    
    print(f"\n📁 Directorios:")
    print(f"  - Datos: {config.DATA_DIR}")
    print(f"  - Modelos: {config.MODELS_DIR}")
    print(f"  - Logs: {config.LOGS_DIR}")
    
    print(f"\n🔄 Sincronización: ±{config.SYNC_TOLERANCE_MS}ms")
    print(f"🎥 FPS objetivo: {config.CAMERA_FPS}")
    print(f"📐 Resolución: {config.CAMERA_RESOLUTION[0]}x{config.CAMERA_RESOLUTION[1]}")
    
    print(f"\n✅ Configuración válida: {config.validate()}")
    print("=" * 60)



