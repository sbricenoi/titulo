#!/usr/bin/env python3
"""
Servicio de grabación de video usando FFmpeg.
Graba múltiples cámaras simultáneamente con segmentación automática.
"""

import subprocess
import time
import signal
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from loguru import logger

from recorder_config import config

# Configurar logger
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    level=config.LOG_LEVEL
)
logger.add(
    config.RECORDER_LOG,
    rotation="100 MB",
    retention="30 days",
    level=config.LOG_LEVEL
)


class FFmpegRecorder:
    """Gestor de grabación con FFmpeg."""
    
    def __init__(self, camera_config: Dict):
        """
        Inicializar grabador para una cámara.
        
        Args:
            camera_config: Diccionario con id, name, url
        """
        self.camera_id = camera_config["id"]
        self.camera_name = camera_config["name"]
        self.rtsp_url = camera_config["url"]
        self.process = None
        self.running = False
        
    def start(self):
        """Iniciar grabación continua."""
        if self.running:
            logger.warning(f"[Camera {self.camera_id}] Ya está grabando")
            return
        
        # Crear comando FFmpeg
        output_pattern = str(
            config.RECORDINGS_DIR / f"camera_{self.camera_id}_%Y-%m-%d_%H-%M-%S.{config.VIDEO_FORMAT}"
        )
        
        ffmpeg_cmd = [
            "ffmpeg",
            "-rtsp_transport", "tcp",        # Usar TCP (más estable)
            "-i", self.rtsp_url,              # Input RTSP
            "-c:v", config.VIDEO_CODEC,       # Codec (copy = no recodificar)
            "-c:a", "aac",                    # Codec de audio
            "-f", "segment",                  # Formato segmentado
            "-segment_time", str(config.SEGMENT_DURATION),  # 10 min
            "-segment_format", config.VIDEO_FORMAT,
            "-segment_atclocktime", "1",      # Alinear con reloj del sistema
            "-strftime", "1",                 # Usar strftime en nombres
            "-reset_timestamps", "1",         # Reset timestamps cada segmento
            "-y",                              # Sobrescribir si existe
            output_pattern
        ]
        
        try:
            logger.info(f"[Camera {self.camera_id}] Iniciando grabación: {self.camera_name}")
            logger.debug(f"[Camera {self.camera_id}] Comando: {' '.join(ffmpeg_cmd)}")
            
            # Iniciar proceso FFmpeg
            self.process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            self.running = True
            logger.success(f"[Camera {self.camera_id}] ✓ Grabación iniciada (PID: {self.process.pid})")
            
        except Exception as e:
            logger.error(f"[Camera {self.camera_id}] ✗ Error iniciando grabación: {e}")
            self.running = False
    
    def stop(self):
        """Detener grabación."""
        if not self.running or not self.process:
            return
        
        logger.info(f"[Camera {self.camera_id}] Deteniendo grabación...")
        
        try:
            # Enviar SIGTERM para terminar elegantemente
            self.process.terminate()
            
            # Esperar hasta 10 segundos
            self.process.wait(timeout=10)
            
        except subprocess.TimeoutExpired:
            logger.warning(f"[Camera {self.camera_id}] Timeout, forzando detención...")
            self.process.kill()
            
        finally:
            self.running = False
            logger.info(f"[Camera {self.camera_id}] ✓ Grabación detenida")
    
    def is_alive(self) -> bool:
        """Verificar si el proceso está corriendo."""
        if not self.process:
            return False
        
        return self.process.poll() is None
    
    def restart(self):
        """Reiniciar grabación."""
        logger.warning(f"[Camera {self.camera_id}] Reiniciando...")
        self.stop()
        time.sleep(2)
        self.start()


class RecorderService:
    """Servicio principal de grabación."""
    
    def __init__(self):
        """Inicializar servicio."""
        self.recorders: List[FFmpegRecorder] = []
        self.running = False
        
        # Crear directorios si no existen
        config.RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
        config.COMPLETED_DIR.mkdir(parents=True, exist_ok=True)
        config.UPLOADED_DIR.mkdir(parents=True, exist_ok=True)
        config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Handlers de señales
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handler para señales de terminación."""
        logger.info(f"Señal recibida ({signum}), deteniendo servicio...")
        self.stop()
        sys.exit(0)
    
    def start(self):
        """Iniciar servicio de grabación."""
        logger.info("=" * 60)
        logger.info("🎥 SERVICIO DE GRABACIÓN DE VIDEO")
        logger.info("=" * 60)
        
        # Validar configuración
        if not config.CAMERAS:
            logger.error("✗ No hay cámaras configuradas")
            return
        
        if not config.S3_BUCKET_NAME:
            logger.warning("⚠️  Bucket S3 no configurado (solo grabación local)")
        
        logger.info(f"📹 Cámaras detectadas: {len(config.CAMERAS)}")
        if config.S3_BUCKET_NAME:
            logger.info(f"📦 Bucket S3: {config.S3_BUCKET_NAME}")
        logger.info(f"⏱️  Duración de segmento: {config.SEGMENT_DURATION // 60} minutos")
        logger.info(f"💾 Directorio local: {config.RECORDINGS_DIR}")
        logger.info("")
        
        # Crear recorders
        for camera in config.CAMERAS:
            recorder = FFmpegRecorder(camera)
            self.recorders.append(recorder)
        
        # Iniciar todos los recorders
        for recorder in self.recorders:
            recorder.start()
            time.sleep(1)  # Delay entre cámaras
        
        self.running = True
        logger.success("✓ Todos los recorders iniciados")
        logger.info("")
        
        # Loop de monitoreo
        self._monitor_loop()
    
    def _monitor_loop(self):
        """Loop principal de monitoreo."""
        check_interval = 30  # Verificar cada 30 segundos
        
        while self.running:
            try:
                time.sleep(check_interval)
                
                # Verificar estado de cada recorder
                for recorder in self.recorders:
                    if recorder.running and not recorder.is_alive():
                        logger.error(
                            f"[Camera {recorder.camera_id}] ✗ Proceso murió, reiniciando..."
                        )
                        recorder.restart()
                
                # Log de estado cada 5 minutos
                if int(time.time()) % 300 < 30:  # Ventana de 30 segundos
                    alive_count = sum(1 for r in self.recorders if r.is_alive())
                    logger.info(f"📊 Estado: {alive_count}/{len(self.recorders)} cámaras grabando")
                    
            except KeyboardInterrupt:
                logger.info("Interrupción de usuario detectada")
                break
            except Exception as e:
                logger.error(f"Error en loop de monitoreo: {e}")
    
    def stop(self):
        """Detener servicio."""
        logger.info("Deteniendo servicio de grabación...")
        self.running = False
        
        for recorder in self.recorders:
            recorder.stop()
        
        logger.info("✓ Servicio detenido")


def main():
    """Punto de entrada principal."""
    service = RecorderService()
    service.start()


if __name__ == "__main__":
    main()
