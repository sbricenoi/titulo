#!/usr/bin/env python3
"""
Servicio de subida automática de videos a S3.
Detecta nuevos archivos completados y los sube a AWS S3.
"""

import time
import signal
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger
import boto3
from botocore.exceptions import ClientError
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from recorder_config import config

# Configurar logger
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    level=config.LOG_LEVEL
)
logger.add(
    config.UPLOADER_LOG,
    rotation="100 MB",
    retention="30 days",
    level=config.LOG_LEVEL
)


class S3Uploader:
    """Clase para subir archivos a S3."""
    
    def __init__(self):
        """Inicializar cliente S3."""
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
            region_name=config.AWS_REGION
        )
        self.bucket_name = config.S3_BUCKET_NAME
        
    def upload_file(self, local_path: Path) -> bool:
        """
        Subir archivo a S3.
        
        Args:
            local_path: Path del archivo local
            
        Returns:
            True si se subió correctamente
        """
        try:
            # Extraer información del nombre del archivo
            # Formato: camera_1_2026-01-24_14-30-00.mp4
            filename = local_path.name
            parts = filename.split('_')
            
            if len(parts) < 4:
                logger.error(f"Nombre de archivo inválido: {filename}")
                return False
            
            camera_id = parts[1]
            date_str = parts[2]  # 2026-01-24
            
            # Construir path S3: year/month/day/camera_X/filename
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            s3_key = f"{date_obj.year}/{date_obj.month:02d}/{date_obj.day:02d}/camera_{camera_id}/{filename}"
            
            # Calcular tamaño
            file_size = local_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            
            logger.info(f"📤 Subiendo: {filename} ({file_size_mb:.1f} MB)")
            logger.debug(f"   Local: {local_path}")
            logger.debug(f"   S3: s3://{self.bucket_name}/{s3_key}")
            
            # Subir archivo
            start_time = time.time()
            
            self.s3_client.upload_file(
                str(local_path),
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'StorageClass': 'STANDARD',
                    'ServerSideEncryption': 'AES256'
                }
            )
            
            elapsed = time.time() - start_time
            speed_mbps = (file_size_mb * 8) / elapsed if elapsed > 0 else 0
            
            logger.success(
                f"✓ Subido: {filename} en {elapsed:.1f}s ({speed_mbps:.1f} Mbps)"
            )
            
            return True
            
        except ClientError as e:
            logger.error(f"✗ Error AWS subiendo {local_path.name}: {e}")
            return False
        except Exception as e:
            logger.error(f"✗ Error subiendo {local_path.name}: {e}")
            return False


class VideoFileHandler(FileSystemEventHandler):
    """Handler para detectar archivos de video nuevos."""
    
    def __init__(self, uploader: S3Uploader):
        """Inicializar handler."""
        self.uploader = uploader
        self.processing = set()  # Archivos en proceso
        
    def on_modified(self, event):
        """Callback cuando se modifica un archivo."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Solo procesar archivos .mp4
        if file_path.suffix != f".{config.VIDEO_FORMAT}":
            return
        
        # Evitar procesar el mismo archivo múltiples veces
        if file_path in self.processing:
            return
        
        # Verificar que el archivo no esté siendo escrito
        if not self._is_file_complete(file_path):
            return
        
        # Procesar archivo
        self.processing.add(file_path)
        self._process_file(file_path)
        self.processing.discard(file_path)
    
    def _is_file_complete(self, file_path: Path, stability_time: int = 5) -> bool:
        """
        Verificar que el archivo está completo (no está siendo escrito).
        
        Args:
            file_path: Path del archivo
            stability_time: Segundos sin cambios para considerar completo
            
        Returns:
            True si el archivo está completo
        """
        try:
            initial_size = file_path.stat().st_size
            time.sleep(stability_time)
            final_size = file_path.stat().st_size
            
            return initial_size == final_size and final_size > 0
            
        except Exception:
            return False
    
    def _process_file(self, file_path: Path):
        """
        Procesar archivo: subir a S3 y mover a carpeta uploaded.
        
        Args:
            file_path: Path del archivo a procesar
        """
        logger.info(f"🔄 Procesando: {file_path.name}")
        
        # Subir a S3
        if self.uploader.upload_file(file_path):
            # Mover a carpeta uploaded
            uploaded_path = config.UPLOADED_DIR / file_path.name
            
            try:
                file_path.rename(uploaded_path)
                logger.debug(f"   Movido a: {uploaded_path}")
            except Exception as e:
                logger.error(f"✗ Error moviendo archivo: {e}")
        else:
            logger.error(f"✗ No se pudo subir {file_path.name}")


class UploaderService:
    """Servicio principal de subida."""
    
    def __init__(self):
        """Inicializar servicio."""
        self.uploader = S3Uploader()
        self.observer = None
        self.running = False
        
        # Handlers de señales
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handler para señales de terminación."""
        logger.info(f"Señal recibida ({signum}), deteniendo servicio...")
        self.stop()
        sys.exit(0)
    
    def start(self):
        """Iniciar servicio."""
        logger.info("=" * 60)
        logger.info("☁️  SERVICIO DE SUBIDA A S3")
        logger.info("=" * 60)
        logger.info(f"📦 Bucket: {config.S3_BUCKET_NAME}")
        logger.info(f"📂 Monitoreando: {config.RECORDINGS_DIR}")
        logger.info("")
        
        # Procesar archivos existentes
        self._process_existing_files()
        
        # Iniciar watchdog observer
        event_handler = VideoFileHandler(self.uploader)
        self.observer = Observer()
        self.observer.schedule(
            event_handler,
            str(config.RECORDINGS_DIR),
            recursive=False
        )
        self.observer.start()
        
        self.running = True
        logger.success("✓ Servicio iniciado")
        logger.info("")
        
        # Loop principal
        try:
            while self.running:
                time.sleep(60)
                
                # Limpiar archivos antiguos cada hora
                if int(time.time()) % 3600 < 60:  # Ventana de 60 segundos
                    self._cleanup_old_files()
                    
        except KeyboardInterrupt:
            logger.info("Interrupción de usuario detectada")
        finally:
            self.stop()
    
    def _process_existing_files(self):
        """Procesar archivos existentes en la carpeta de grabaciones."""
        logger.info("🔍 Buscando archivos existentes...")
        
        files = list(config.RECORDINGS_DIR.glob(f"*.{config.VIDEO_FORMAT}"))
        
        if not files:
            logger.info("   No hay archivos para procesar")
            return
        
        logger.info(f"   Encontrados {len(files)} archivos")
        
        handler = VideoFileHandler(self.uploader)
        
        for file_path in files:
            # Solo procesar archivos estables (no en escritura)
            if handler._is_file_complete(file_path, stability_time=2):
                handler._process_file(file_path)
    
    def _cleanup_old_files(self):
        """Eliminar archivos locales antiguos (ya subidos)."""
        logger.info("🧹 Limpiando archivos antiguos...")
        
        cutoff_time = datetime.now() - timedelta(hours=config.LOCAL_RETENTION_HOURS)
        deleted_count = 0
        freed_space_mb = 0
        
        for file_path in config.UPLOADED_DIR.glob(f"*.{config.VIDEO_FORMAT}"):
            try:
                # Verificar antigüedad
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                if file_time < cutoff_time:
                    file_size_mb = file_path.stat().st_size / (1024 * 1024)
                    file_path.unlink()
                    deleted_count += 1
                    freed_space_mb += file_size_mb
                    logger.debug(f"   Eliminado: {file_path.name}")
                    
            except Exception as e:
                logger.error(f"Error eliminando {file_path.name}: {e}")
        
        if deleted_count > 0:
            logger.info(
                f"✓ Eliminados {deleted_count} archivos "
                f"({freed_space_mb:.1f} MB liberados)"
            )
        else:
            logger.info("   No hay archivos para eliminar")
    
    def stop(self):
        """Detener servicio."""
        logger.info("Deteniendo servicio de subida...")
        self.running = False
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        logger.info("✓ Servicio detenido")


def main():
    """Punto de entrada principal."""
    service = UploaderService()
    service.start()


if __name__ == "__main__":
    main()
