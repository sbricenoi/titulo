#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio de grabación de video usando FFmpeg.

Este servicio graba múltiples cámaras simultáneamente con segmentación
automática cada X minutos. Incluye:
- Grabación continua 24/7
- Segmentación automática
- Monitoreo de procesos
- Reinicio automático ante fallos
- Logs detallados

Uso:
    python video_recorder.py

Autor: Sistema de Monitoreo de Hurones
Fecha: 2026-01-24
Versión: 1.0.0
"""

import subprocess
import time
import signal
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from loguru import logger

from recorder_config import config

# ==================== CONFIGURACIÓN DE LOGGER ====================
logger.remove()

# Logger para consola
logger.add(
    sys.stdout,
    format=config.LOG_FORMAT,
    level=config.LOG_LEVEL,
    colorize=True
)

# Logger para archivo
logger.add(
    config.RECORDER_LOG,
    format=config.LOG_FORMAT,
    level=config.LOG_LEVEL,
    rotation=config.LOG_ROTATION,
    retention=config.LOG_RETENTION,
    compression="zip"
)


class FFmpegRecorder:
    """
    Grabador de video usando FFmpeg para una cámara individual.
    
    Maneja la grabación continua con segmentación automática,
    reinicio ante fallos y monitoreo del proceso.
    """
    
    def __init__(self, camera_config: Dict[str, any]):
        """
        Inicializar grabador para una cámara.
        
        Args:
            camera_config: Diccionario con id, name, url de la cámara
        """
        self.camera_id = camera_config["id"]
        self.camera_name = camera_config["name"]
        self.rtsp_url = camera_config["url"]
        
        self.process: Optional[subprocess.Popen] = None
        self.running = False
        
        # Estadísticas
        self.start_time: Optional[float] = None
        self.restart_count = 0
        self.last_restart_time: Optional[float] = None
        
        logger.debug(f"[Camera {self.camera_id}] FFmpegRecorder inicializado para {self.camera_name}")
    
    def _build_ffmpeg_command(self) -> List[str]:
        """
        Construir comando FFmpeg para grabación.
        
        Returns:
            Lista con el comando FFmpeg y sus argumentos
        """
        # Patrón de salida con timestamp
        output_pattern = str(
            config.RECORDINGS_DIR / f"camera_{self.camera_id}_%Y-%m-%d_%H-%M-%S.{config.VIDEO_FORMAT}"
        )
        
        # Comando base
        cmd = [
            "ffmpeg",
            # Opciones de entrada
            "-rtsp_transport", "tcp",        # Usar TCP (más estable que UDP)
            "-i", self.rtsp_url,              # URL RTSP de entrada
            
            # Opciones de video
            "-c:v", config.VIDEO_CODEC,       # Codec de video (copy = no recodificar)
            
            # Opciones de audio
            "-c:a", "aac",                    # Codec de audio
            "-b:a", "128k",                   # Bitrate de audio
            
            # Opciones de segmentación
            "-f", "segment",                  # Formato segmentado
            "-segment_time", str(config.SEGMENT_DURATION),  # Duración de cada segmento
            "-segment_format", config.VIDEO_FORMAT,         # Formato de los segmentos
            "-strftime", "1",                 # Usar strftime en nombres de archivo
            "-reset_timestamps", "1",         # Resetear timestamps en cada segmento
            
            # Opciones generales
            "-y",                              # Sobrescribir archivos sin preguntar
            
            # Archivo de salida
            output_pattern
        ]
        
        # Agregar bitrate máximo si está configurado
        if config.MAX_BITRATE:
            cmd.extend(["-maxrate", f"{config.MAX_BITRATE}M"])
            cmd.extend(["-bufsize", f"{int(config.MAX_BITRATE) * 2}M"])
        
        return cmd
    
    def start(self) -> bool:
        """
        Iniciar grabación.
        
        Returns:
            True si se inició correctamente, False en caso contrario
        """
        if self.running:
            logger.warning(f"[Camera {self.camera_id}] Ya está grabando")
            return False
        
        try:
            # Construir comando
            ffmpeg_cmd = self._build_ffmpeg_command()
            
            logger.info(f"[Camera {self.camera_id}] 🎬 Iniciando grabación: {self.camera_name}")
            logger.debug(f"[Camera {self.camera_id}] Comando: {' '.join(ffmpeg_cmd)}")
            
            # Iniciar proceso FFmpeg
            self.process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            self.running = True
            self.start_time = time.time()
            
            # Esperar un momento para verificar que no falle inmediatamente
            time.sleep(2)
            
            if self.is_alive():
                logger.success(
                    f"[Camera {self.camera_id}] ✓ Grabación iniciada correctamente "
                    f"(PID: {self.process.pid})"
                )
                return True
            else:
                # El proceso murió inmediatamente
                stderr = self.process.stderr.read() if self.process.stderr else "N/A"
                logger.error(
                    f"[Camera {self.camera_id}] ✗ Proceso FFmpeg murió inmediatamente. "
                    f"Error: {stderr[:200]}"
                )
                self.running = False
                return False
            
        except FileNotFoundError:
            logger.error(
                f"[Camera {self.camera_id}] ✗ FFmpeg no está instalado. "
                f"Instalar con: sudo apt install ffmpeg (Linux) o brew install ffmpeg (Mac)"
            )
            self.running = False
            return False
            
        except Exception as e:
            logger.error(f"[Camera {self.camera_id}] ✗ Error iniciando grabación: {e}")
            logger.exception(e)
            self.running = False
            return False
    
    def stop(self) -> bool:
        """
        Detener grabación de forma elegante.
        
        Returns:
            True si se detuvo correctamente, False en caso contrario
        """
        if not self.running or not self.process:
            logger.debug(f"[Camera {self.camera_id}] No hay grabación activa para detener")
            return True
        
        logger.info(f"[Camera {self.camera_id}] ⏸️  Deteniendo grabación...")
        
        try:
            # Enviar SIGTERM para terminar elegantemente
            self.process.terminate()
            
            # Esperar hasta 10 segundos
            try:
                self.process.wait(timeout=10)
                logger.success(f"[Camera {self.camera_id}] ✓ Grabación detenida correctamente")
            except subprocess.TimeoutExpired:
                # Si no responde, forzar terminación
                logger.warning(f"[Camera {self.camera_id}] Timeout, forzando terminación...")
                self.process.kill()
                self.process.wait()
                logger.info(f"[Camera {self.camera_id}] ✓ Proceso terminado forzadamente")
            
            self.running = False
            return True
            
        except Exception as e:
            logger.error(f"[Camera {self.camera_id}] ✗ Error deteniendo grabación: {e}")
            self.running = False
            return False
    
    def is_alive(self) -> bool:
        """
        Verificar si el proceso FFmpeg está corriendo.
        
        Returns:
            True si está corriendo, False en caso contrario
        """
        if not self.process:
            return False
        
        # poll() retorna None si el proceso está corriendo
        return self.process.poll() is None
    
    def is_actually_recording(self) -> bool:
        """
        Verificar si FFmpeg está realmente grabando (no zombie).
        
        Returns:
            True si está grabando activamente, False si es zombie
        """
        if not self.is_alive():
            return False
        
        try:
            import glob
            from pathlib import Path
            
            # Calcular threshold dinámicamente basado en SEGMENT_DURATION
            # Debe ser mayor que el tiempo de segmento + margen de seguridad
            # Fórmula: SEGMENT_DURATION + 120 segundos de margen
            zombie_threshold = config.SEGMENT_DURATION + 120
            
            # Verificar si hay archivos recientes de esta cámara
            pattern = str(config.RECORDINGS_DIR / f"camera_{self.camera_id}_*.mp4")
            recent_files = glob.glob(pattern)
            
            if not recent_files:
                logger.debug(f"[Camera {self.camera_id}] No hay archivos en recordings/")
                return False
            
            newest_file = max(recent_files, key=lambda x: Path(x).stat().st_mtime)
            file_age = time.time() - Path(newest_file).stat().st_mtime
            
            # Si el archivo más reciente es más nuevo que el threshold, está grabando
            is_recording = file_age < zombie_threshold
            
            if not is_recording:
                logger.warning(
                    f"[Camera {self.camera_id}] ⚠️  Proceso zombie detectado: "
                    f"último archivo hace {file_age:.0f}s (threshold: {zombie_threshold}s)"
                )
            else:
                logger.debug(
                    f"[Camera {self.camera_id}] ✓ Grabando correctamente "
                    f"(último archivo hace {file_age:.0f}s)"
                )
            
            return is_recording
            
        except Exception as e:
            logger.debug(f"[Camera {self.camera_id}] Error verificando grabación: {e}")
            # En caso de error, asumir que está grabando para evitar reinicios innecesarios
            return True
    
    def restart(self) -> bool:
        """
        Reiniciar grabación.
        
        Returns:
            True si se reinició correctamente, False en caso contrario
        """
        logger.warning(f"[Camera {self.camera_id}] 🔄 Reiniciando grabación...")
        
        self.restart_count += 1
        self.last_restart_time = time.time()
        
        # Detener si está corriendo
        self.stop()
        
        # Esperar un momento
        time.sleep(2)
        
        # Iniciar nuevamente
        success = self.start()
        
        if success:
            logger.success(f"[Camera {self.camera_id}] ✓ Grabación reiniciada (reinicio #{self.restart_count})")
        else:
            logger.error(f"[Camera {self.camera_id}] ✗ Fallo al reiniciar")
        
        return success
    
    def get_stats(self) -> Dict[str, any]:
        """
        Obtener estadísticas del recorder.
        
        Returns:
            Diccionario con estadísticas
        """
        uptime = time.time() - self.start_time if self.start_time else 0
        
        return {
            "camera_id": self.camera_id,
            "camera_name": self.camera_name,
            "running": self.running,
            "alive": self.is_alive(),
            "pid": self.process.pid if self.process else None,
            "uptime_seconds": uptime,
            "uptime_hours": uptime / 3600,
            "restart_count": self.restart_count,
            "last_restart": self.last_restart_time
        }
    
    def __repr__(self) -> str:
        """Representación en string del recorder."""
        status = "🟢 Grabando" if self.is_alive() else "🔴 Detenido"
        return f"<FFmpegRecorder cam={self.camera_id} name={self.camera_name} {status}>"


class RecorderService:
    """
    Servicio principal de grabación.
    
    Maneja múltiples FFmpegRecorder, monitorea su estado,
    y reinicia automáticamente ante fallos.
    """
    
    def __init__(self):
        """Inicializar servicio de grabación."""
        self.recorders: List[FFmpegRecorder] = []
        self.running = False
        self.start_time: Optional[float] = None
        
        # Configurar handlers de señales
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        logger.debug("RecorderService inicializado")
    
    def _signal_handler(self, signum, frame):
        """
        Handler para señales de terminación (SIGTERM, SIGINT).
        
        Args:
            signum: Número de señal
            frame: Frame actual
        """
        signal_name = "SIGTERM" if signum == signal.SIGTERM else "SIGINT"
        logger.info(f"📡 Señal {signal_name} recibida, deteniendo servicio...")
        self.stop()
        sys.exit(0)
    
    def _validate_config(self) -> bool:
        """
        Validar configuración antes de iniciar.
        
        Returns:
            True si la configuración es válida, False en caso contrario
        """
        is_valid, error_message = config.validate()
        
        if not is_valid:
            logger.error(f"❌ Configuración inválida: {error_message}")
            return False
        
        logger.success("✓ Configuración válida")
        return True
    
    def _create_recorders(self):
        """Crear recorders para todas las cámaras configuradas."""
        logger.info(f"📹 Creando recorders para {config.get_camera_count()} cámaras...")
        
        for camera in config.CAMERAS:
            recorder = FFmpegRecorder(camera)
            self.recorders.append(recorder)
            logger.debug(f"   ✓ Recorder creado para {camera['name']}")
        
        logger.success(f"✓ {len(self.recorders)} recorders creados")
    
    def _start_all_recorders(self):
        """Iniciar todos los recorders."""
        logger.info("🚀 Iniciando grabación en todas las cámaras...")
        
        success_count = 0
        
        for recorder in self.recorders:
            if recorder.start():
                success_count += 1
            
            # Delay entre cámaras para no saturar
            time.sleep(1)
        
        logger.info(f"✓ {success_count}/{len(self.recorders)} cámaras iniciadas correctamente")
        
        if success_count == 0:
            logger.error("❌ No se pudo iniciar ninguna cámara")
            return False
        
        return True
    
    def _monitor_loop(self):
        """
        Loop principal de monitoreo.
        
        Verifica continuamente el estado de los recorders y los
        reinicia automáticamente si fallan.
        """
        logger.info("👁️  Iniciando monitoreo de cámaras...")
        logger.info(f"   Intervalo de verificación: {config.MONITOR_INTERVAL}s")
        
        check_count = 0
        
        while self.running:
            try:
                time.sleep(config.MONITOR_INTERVAL)
                check_count += 1
                
                # Verificar estado de cada recorder
                dead_recorders = []
                alive_count = 0
                zombie_recorders = []
                
                for recorder in self.recorders:
                    if recorder.running and not recorder.is_alive():
                        # Proceso muerto
                        dead_recorders.append(recorder)
                    elif recorder.is_alive():
                        # Proceso vivo, pero verificar si es zombie
                        if not recorder.is_actually_recording():
                            zombie_recorders.append(recorder)
                        else:
                            alive_count += 1
                
                # Reiniciar recorders muertos
                if dead_recorders:
                    logger.warning(
                        f"⚠️  Detectados {len(dead_recorders)} recorders muertos, reiniciando..."
                    )
                    
                    for recorder in dead_recorders:
                        recorder.restart()
                
                # Reiniciar recorders zombie
                if zombie_recorders:
                    logger.warning(
                        f"⚠️  Detectados {len(zombie_recorders)} recorders ZOMBIE, reiniciando..."
                    )
                    
                    for recorder in zombie_recorders:
                        recorder.restart()
                
                # Log de estado cada 10 verificaciones (~5 minutos con intervalo de 30s)
                if check_count % 10 == 0:
                    uptime = time.time() - self.start_time
                    uptime_hours = uptime / 3600
                    
                    logger.info(
                        f"📊 Estado: {alive_count}/{len(self.recorders)} cámaras activas | "
                        f"Uptime: {uptime_hours:.1f}h | "
                        f"Verificaciones: {check_count}"
                    )
                
            except KeyboardInterrupt:
                logger.info("⌨️  Interrupción de teclado detectada")
                break
                
            except Exception as e:
                logger.error(f"❌ Error en loop de monitoreo: {e}")
                logger.exception(e)
                time.sleep(5)  # Esperar antes de continuar
    
    def start(self):
        """Iniciar servicio de grabación."""
        logger.info("=" * 70)
        logger.info("🎥 SERVICIO DE GRABACIÓN DE VIDEO")
        logger.info("=" * 70)
        logger.info(f"📅 Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("")
        
        # Validar configuración
        if not self._validate_config():
            logger.error("❌ No se puede iniciar el servicio debido a errores de configuración")
            sys.exit(1)
        
        # Mostrar resumen de configuración
        logger.info(f"📦 Bucket S3: {config.S3_BUCKET_NAME}")
        logger.info(f"📹 Cámaras: {config.get_camera_count()}")
        logger.info(f"⏱️  Segmentos: {config.SEGMENT_DURATION // 60} minutos")
        logger.info(f"🎞️  Codec: {config.VIDEO_CODEC}")
        logger.info(f"💾 Directorio: {config.RECORDINGS_DIR}")
        logger.info("")
        
        # Crear recorders
        self._create_recorders()
        logger.info("")
        
        # Iniciar recorders
        if not self._start_all_recorders():
            logger.error("❌ No se pudo iniciar ninguna cámara, abortando")
            sys.exit(1)
        
        logger.info("")
        self.running = True
        self.start_time = time.time()
        
        logger.success("✅ Servicio de grabación iniciado correctamente")
        logger.info("=" * 70)
        logger.info("")
        
        # Iniciar loop de monitoreo
        try:
            self._monitor_loop()
        except Exception as e:
            logger.error(f"❌ Error fatal en servicio: {e}")
            logger.exception(e)
        finally:
            self.stop()
    
    def stop(self):
        """Detener servicio de grabación."""
        if not self.running:
            return
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("⏹️  DETENIENDO SERVICIO DE GRABACIÓN")
        logger.info("=" * 70)
        
        self.running = False
        
        # Detener todos los recorders
        for recorder in self.recorders:
            recorder.stop()
        
        # Calcular uptime
        if self.start_time:
            uptime = time.time() - self.start_time
            uptime_hours = uptime / 3600
            logger.info(f"⏱️  Uptime total: {uptime_hours:.2f} horas")
        
        # Mostrar estadísticas
        logger.info("")
        logger.info("📊 Estadísticas finales:")
        for recorder in self.recorders:
            stats = recorder.get_stats()
            logger.info(
                f"   Camera {stats['camera_id']}: "
                f"{stats['uptime_hours']:.1f}h uptime, "
                f"{stats['restart_count']} reinicios"
            )
        
        logger.info("")
        logger.success("✅ Servicio detenido correctamente")
        logger.info("=" * 70)
    
    def get_status(self) -> Dict[str, any]:
        """
        Obtener estado actual del servicio.
        
        Returns:
            Diccionario con estado del servicio
        """
        alive_count = sum(1 for r in self.recorders if r.is_alive())
        uptime = time.time() - self.start_time if self.start_time else 0
        
        return {
            "running": self.running,
            "uptime_seconds": uptime,
            "uptime_hours": uptime / 3600,
            "total_cameras": len(self.recorders),
            "active_cameras": alive_count,
            "recorders": [r.get_stats() for r in self.recorders]
        }


def main():
    """Punto de entrada principal del servicio."""
    service = RecorderService()
    
    try:
        service.start()
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        logger.exception(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
