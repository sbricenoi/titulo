#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuración centralizada para el sistema de grabación de video.

Este módulo maneja toda la configuración del sistema, incluyendo:
- Variables de entorno
- Paths de directorios
- Configuración de AWS
- Configuración de cámaras
- Parámetros de grabación y retención

Autor: Sistema de Monitoreo de Hurones
Fecha: 2026-01-24
Versión: 1.0.0
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()


class RecorderConfig:
    """
    Configuración centralizada del sistema de grabación.
    
    Lee configuración desde variables de entorno y proporciona
    valores por defecto sensibles.
    """
    
    # ==================== DIRECTORIOS ====================
    # Directorio base del proyecto (detectar automáticamente)
    BASE_DIR = Path(os.getenv("BASE_DIR", Path(__file__).parent.parent.absolute()))
    
    # Directorios de datos
    DATA_DIR = BASE_DIR / "data"
    VIDEOS_DIR = DATA_DIR / "videos"
    RECORDINGS_DIR = Path(os.getenv("RECORDINGS_DIR", VIDEOS_DIR / "recordings"))
    COMPLETED_DIR = Path(os.getenv("COMPLETED_DIR", VIDEOS_DIR / "completed"))
    UPLOADED_DIR = Path(os.getenv("UPLOADED_DIR", VIDEOS_DIR / "uploaded"))
    LOGS_DIR = DATA_DIR / "logs"
    
    # ==================== AWS CONFIGURATION ====================
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
    S3_UPLOAD_RETRIES = int(os.getenv("S3_UPLOAD_RETRIES", "3"))
    
    # ==================== CÁMARAS ====================
    CAMERAS: List[Dict[str, any]] = []
    
    @classmethod
    def load_cameras(cls) -> List[Dict[str, any]]:
        """
        Cargar configuración de cámaras desde variables de entorno.
        
        Lee todas las variables CAMERA_X_URL y CAMERA_X_NAME donde X es un número.
        
        Returns:
            Lista de diccionarios con configuración de cámaras
        """
        cameras = []
        i = 1
        
        while True:
            url = os.getenv(f"CAMERA_{i}_URL")
            
            if not url:
                break
            
            name = os.getenv(f"CAMERA_{i}_NAME", f"Camera_{i}")
            
            cameras.append({
                "id": i,
                "name": name,
                "url": url
            })
            
            i += 1
        
        cls.CAMERAS = cameras
        return cameras
    
    # ==================== GRABACIÓN ====================
    # Duración de cada segmento en segundos (600 = 10 minutos)
    SEGMENT_DURATION = int(os.getenv("SEGMENT_DURATION", "600"))
    
    # Codec de video ("copy" = no recodificar, más eficiente)
    VIDEO_CODEC = os.getenv("VIDEO_CODEC", "copy")
    
    # Formato de video
    VIDEO_FORMAT = os.getenv("VIDEO_FORMAT", "mp4")
    
    # Bitrate máximo (opcional)
    MAX_BITRATE = os.getenv("MAX_BITRATE")
    
    # ==================== RETENCIÓN ====================
    # Horas que se mantienen los archivos locales después de subir
    LOCAL_RETENTION_HOURS = int(os.getenv("LOCAL_RETENTION_HOURS", "24"))
    
    # ==================== LOGGING ====================
    # Nivel de log (DEBUG, INFO, WARNING, ERROR)
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Archivos de log
    RECORDER_LOG = LOGS_DIR / "recorder.log"
    UPLOADER_LOG = LOGS_DIR / "uploader.log"
    
    # Formato de log
    LOG_FORMAT = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Rotación de logs (100 MB)
    LOG_ROTATION = "100 MB"
    
    # Retención de logs (30 días)
    LOG_RETENTION = "30 days"
    
    # ==================== CONFIGURACIÓN AVANZADA ====================
    # Tiempo de espera para considerar un archivo completo (segundos)
    FILE_STABILITY_TIME = int(os.getenv("FILE_STABILITY_TIME", "5"))
    
    # Intervalo de monitoreo de procesos (segundos)
    MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL", "30"))
    
    # Comprimir antes de subir (experimental)
    ENABLE_COMPRESSION = os.getenv("ENABLE_COMPRESSION", "false").lower() == "true"
    
    # ==================== VALIDACIÓN ====================
    @classmethod
    def validate(cls) -> tuple[bool, Optional[str]]:
        """
        Validar configuración del sistema.
        
        Returns:
            Tupla (es_valido, mensaje_error)
        """
        # Validar AWS credentials
        if not cls.AWS_ACCESS_KEY_ID:
            return False, "AWS_ACCESS_KEY_ID no está configurado"
        
        if not cls.AWS_SECRET_ACCESS_KEY:
            return False, "AWS_SECRET_ACCESS_KEY no está configurado"
        
        if not cls.S3_BUCKET_NAME:
            return False, "S3_BUCKET_NAME no está configurado"
        
        # Validar cámaras
        if not cls.CAMERAS:
            cls.load_cameras()
            
        if not cls.CAMERAS:
            return False, "No hay cámaras configuradas (CAMERA_1_URL, etc.)"
        
        # Validar directorios
        try:
            cls.RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
            cls.COMPLETED_DIR.mkdir(parents=True, exist_ok=True)
            cls.UPLOADED_DIR.mkdir(parents=True, exist_ok=True)
            cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return False, f"No se pueden crear directorios: {e}"
        
        # Validar valores numéricos
        if cls.SEGMENT_DURATION <= 0:
            return False, "SEGMENT_DURATION debe ser mayor a 0"
        
        if cls.LOCAL_RETENTION_HOURS < 0:
            return False, "LOCAL_RETENTION_HOURS debe ser mayor o igual a 0"
        
        return True, None
    
    # ==================== UTILIDADES ====================
    @classmethod
    def get_camera_count(cls) -> int:
        """Obtener número de cámaras configuradas."""
        if not cls.CAMERAS:
            cls.load_cameras()
        return len(cls.CAMERAS)
    
    @classmethod
    def get_camera_by_id(cls, camera_id: int) -> Optional[Dict[str, any]]:
        """
        Obtener configuración de una cámara por su ID.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            Diccionario con configuración o None si no existe
        """
        if not cls.CAMERAS:
            cls.load_cameras()
        
        for camera in cls.CAMERAS:
            if camera["id"] == camera_id:
                return camera
        
        return None
    
    @classmethod
    def print_config(cls):
        """Imprimir configuración actual (para debugging)."""
        print("=" * 60)
        print("CONFIGURACIÓN DEL SISTEMA")
        print("=" * 60)
        print(f"\n📁 Directorios:")
        print(f"   Base: {cls.BASE_DIR}")
        print(f"   Recordings: {cls.RECORDINGS_DIR}")
        print(f"   Completed: {cls.COMPLETED_DIR}")
        print(f"   Uploaded: {cls.UPLOADED_DIR}")
        print(f"   Logs: {cls.LOGS_DIR}")
        
        print(f"\n☁️  AWS:")
        print(f"   Region: {cls.AWS_REGION}")
        print(f"   Bucket: {cls.S3_BUCKET_NAME}")
        print(f"   Access Key: {cls.AWS_ACCESS_KEY_ID[:10]}..." if cls.AWS_ACCESS_KEY_ID else "   Access Key: NOT SET")
        
        print(f"\n📹 Cámaras: {cls.get_camera_count()}")
        for camera in cls.CAMERAS:
            # Ocultar credenciales en la URL
            url_safe = camera['url'].split('@')[-1] if '@' in camera['url'] else camera['url']
            print(f"   {camera['id']}. {camera['name']}: rtsp://***@{url_safe}")
        
        print(f"\n🎥 Grabación:")
        print(f"   Duración de segmento: {cls.SEGMENT_DURATION} segundos ({cls.SEGMENT_DURATION // 60} min)")
        print(f"   Codec: {cls.VIDEO_CODEC}")
        print(f"   Formato: {cls.VIDEO_FORMAT}")
        
        print(f"\n💾 Retención:")
        print(f"   Local: {cls.LOCAL_RETENTION_HOURS} horas")
        
        print(f"\n📝 Logging:")
        print(f"   Nivel: {cls.LOG_LEVEL}")
        print(f"   Rotación: {cls.LOG_ROTATION}")
        print(f"   Retención: {cls.LOG_RETENTION}")
        
        print("=" * 60)


# ==================== INICIALIZACIÓN ====================
# Cargar cámaras al importar el módulo
RecorderConfig.load_cameras()

# Crear alias para facilitar importación
config = RecorderConfig


# ==================== TESTING ====================
if __name__ == "__main__":
    """Script de prueba de configuración."""
    
    print("\n🔍 VALIDANDO CONFIGURACIÓN...\n")
    
    # Mostrar configuración
    config.print_config()
    
    # Validar
    print("\n✅ VALIDACIÓN:")
    is_valid, error_message = config.validate()
    
    if is_valid:
        print("   ✓ Configuración válida")
    else:
        print(f"   ✗ Error: {error_message}")
        exit(1)
    
    print("\n✓ Todo correcto\n")
