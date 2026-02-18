"""
Configuración centralizada para el sistema de grabación.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class RecorderConfig:
    """Configuración del sistema de grabación."""
    
    # Directorios base (ajustar según entorno)
    BASE_DIR = Path(os.getenv("BASE_DIR", str(Path.cwd())))
    DATA_DIR = BASE_DIR / "data"
    VIDEOS_DIR = DATA_DIR / "videos"
    RECORDINGS_DIR = VIDEOS_DIR / "recordings"
    COMPLETED_DIR = VIDEOS_DIR / "completed"
    UPLOADED_DIR = VIDEOS_DIR / "uploaded"
    LOGS_DIR = DATA_DIR / "logs"
    
    # AWS
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
    
    # Cámaras (cargar dinámicamente)
    CAMERAS = []
    
    @classmethod
    def load_cameras(cls):
        """Cargar configuración de cámaras desde variables de entorno."""
        cameras = []
        i = 1
        while True:
            url = os.getenv(f"CAMERA_{i}_URL")
            name = os.getenv(f"CAMERA_{i}_NAME", f"Camera_{i}")
            
            if not url:
                break
                
            cameras.append({
                "id": i,
                "name": name,
                "url": url
            })
            i += 1
        
        cls.CAMERAS = cameras
        return cameras
    
    # Configuración de grabación
    SEGMENT_DURATION = int(os.getenv("SEGMENT_DURATION", "600"))  # 10 min
    VIDEO_CODEC = os.getenv("VIDEO_CODEC", "copy")
    VIDEO_FORMAT = "mp4"
    
    # Retención
    LOCAL_RETENTION_HOURS = int(os.getenv("LOCAL_RETENTION_HOURS", "24"))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    RECORDER_LOG = LOGS_DIR / "recorder.log"
    UPLOADER_LOG = LOGS_DIR / "uploader.log"

# Inicializar
RecorderConfig.load_cameras()
config = RecorderConfig()
