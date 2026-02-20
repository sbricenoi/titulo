#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio de subida automática de videos a AWS S3.

Este servicio:
- Detecta automáticamente nuevos archivos de video completados
- Los sube a AWS S3 con estructura organizada (year/month/day/camera/)
- Verifica la integridad de la subida
- Mueve archivos locales después de subir exitosamente
- Limpia archivos antiguos basándose en la retención configurada

Uso:
    python s3_uploader.py

Autor: Sistema de Monitoreo de Hurones
Fecha: 2026-01-24
Versión: 1.0.0
"""

import time
import signal
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List
from loguru import logger
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

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
    config.UPLOADER_LOG,
    format=config.LOG_FORMAT,
    level=config.LOG_LEVEL,
    rotation=config.LOG_ROTATION,
    retention=config.LOG_RETENTION,
    compression="zip"
)


class S3Uploader:
    """
    Clase para manejar subidas a AWS S3.
    
    Maneja la conexión con S3, subida de archivos, verificación
    de integridad y gestión de errores.
    """
    
    def __init__(self):
        """Inicializar cliente S3."""
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                region_name=config.AWS_REGION
            )
            
            self.bucket_name = config.S3_BUCKET_NAME
            
            # Verificar que el bucket existe
            self._verify_bucket()
            
            logger.success(f"✓ Cliente S3 inicializado correctamente")
            logger.debug(f"   Bucket: {self.bucket_name}")
            logger.debug(f"   Region: {config.AWS_REGION}")
            
        except NoCredentialsError:
            logger.error("❌ Credenciales AWS no encontradas")
            raise
        except Exception as e:
            logger.error(f"❌ Error inicializando cliente S3: {e}")
            raise
    
    def _verify_bucket(self):
        """Verificar que el bucket S3 existe y es accesible."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.debug(f"✓ Bucket '{self.bucket_name}' verificado")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"❌ Bucket '{self.bucket_name}' no existe")
            elif error_code == '403':
                logger.error(f"❌ Sin permisos para acceder al bucket '{self.bucket_name}'")
            else:
                logger.error(f"❌ Error verificando bucket: {e}")
            raise
    
    def _parse_filename(self, filename: str) -> Optional[dict]:
        """
        Extraer información del nombre del archivo.
        
        Formato esperado: camera_X_YYYY-MM-DD_HH-MM-SS.mp4
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            Diccionario con información parseada o None si el formato es inválido
        """
        try:
            # Remover extensión
            name_without_ext = filename.rsplit('.', 1)[0]
            
            # Split por underscore
            parts = name_without_ext.split('_')
            
            if len(parts) < 4 or parts[0] != 'camera':
                logger.warning(f"Formato de nombre inválido: {filename}")
                return None
            
            camera_id = parts[1]
            date_str = parts[2]  # YYYY-MM-DD
            time_str = parts[3]  # HH-MM-SS
            
            # Parsear fecha
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            
            return {
                "camera_id": camera_id,
                "date": date_obj,
                "year": date_obj.year,
                "month": date_obj.month,
                "day": date_obj.day,
                "time": time_str
            }
            
        except Exception as e:
            logger.warning(f"Error parseando nombre de archivo '{filename}': {e}")
            return None
    
    def _build_s3_key(self, filename: str) -> Optional[str]:
        """
        Construir la key S3 para el archivo.
        
        Estructura: year/month/day/camera_X/filename
        Ejemplo: 2026/01/24/camera_1/camera_1_2026-01-24_14-30-00.mp4
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            Key S3 o None si no se pudo construir
        """
        info = self._parse_filename(filename)
        
        if not info:
            return None
        
        s3_key = (
            f"{info['year']}/"
            f"{info['month']:02d}/"
            f"{info['day']:02d}/"
            f"camera_{info['camera_id']}/"
            f"{filename}"
        )
        
        return s3_key
    
    def upload_file(self, local_path: Path) -> bool:
        """
        Subir archivo a S3.
        
        Args:
            local_path: Path del archivo local
            
        Returns:
            True si se subió correctamente, False en caso contrario
        """
        filename = local_path.name
        
        try:
            # Construir key S3
            s3_key = self._build_s3_key(filename)
            
            if not s3_key:
                logger.error(f"No se pudo construir S3 key para: {filename}")
                return False
            
            # Obtener tamaño del archivo
            file_size = local_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            
            logger.info(f"📤 Subiendo: {filename} ({file_size_mb:.1f} MB)")
            logger.debug(f"   Local: {local_path}")
            logger.debug(f"   S3: s3://{self.bucket_name}/{s3_key}")
            
            # Subir archivo con reintentos
            start_time = time.time()
            
            for attempt in range(1, config.S3_UPLOAD_RETRIES + 1):
                try:
                    self.s3_client.upload_file(
                        str(local_path),
                        self.bucket_name,
                        s3_key,
                        ExtraArgs={
                            'StorageClass': 'STANDARD',
                            'ServerSideEncryption': 'AES256',
                            'ContentType': 'video/mp4',
                            'ContentDisposition': 'inline',
                            'CacheControl': 'max-age=31536000'
                        }
                    )
                    
                    # Subida exitosa
                    elapsed = time.time() - start_time
                    speed_mbps = (file_size_mb * 8) / elapsed if elapsed > 0 else 0
                    
                    logger.success(
                        f"✓ Subido: {filename} en {elapsed:.1f}s ({speed_mbps:.1f} Mbps)"
                    )
                    
                    # Verificar integridad
                    if self.verify_upload(local_path, s3_key):
                        logger.debug(f"   ✓ Integridad verificada")
                        return True
                    else:
                        logger.warning(f"   ⚠️  Integridad no coincide, reintentando...")
                        if attempt < config.S3_UPLOAD_RETRIES:
                            continue
                        else:
                            return False
                    
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    logger.error(
                        f"✗ Error AWS subiendo {filename} (intento {attempt}/{config.S3_UPLOAD_RETRIES}): "
                        f"{error_code}"
                    )
                    
                    if attempt < config.S3_UPLOAD_RETRIES:
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.info(f"   Esperando {wait_time}s antes de reintentar...")
                        time.sleep(wait_time)
                    else:
                        return False
                
            return False
            
        except Exception as e:
            logger.error(f"✗ Error subiendo {filename}: {e}")
            logger.exception(e)
            return False
    
    def verify_upload(self, local_path: Path, s3_key: str) -> bool:
        """
        Verificar que el archivo se subió correctamente.
        
        Compara el tamaño del archivo local con el del objeto en S3.
        
        Args:
            local_path: Path del archivo local
            s3_key: Key del objeto en S3
            
        Returns:
            True si el tamaño coincide, False en caso contrario
        """
        try:
            # Obtener metadata del objeto en S3
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            # Comparar tamaños
            s3_size = response['ContentLength']
            local_size = local_path.stat().st_size
            
            return s3_size == local_size
            
        except ClientError as e:
            logger.error(f"Error verificando upload de {s3_key}: {e}")
            return False


class VideoFileHandler(FileSystemEventHandler):
    """
    Handler para detectar y procesar nuevos archivos de video.
    
    Usa watchdog para detectar cuando se crean nuevos archivos,
    espera a que estén completos, y los procesa (sube a S3).
    """
    
    def __init__(self, uploader: S3Uploader):
        """
        Inicializar handler.
        
        Args:
            uploader: Instancia de S3Uploader
        """
        super().__init__()
        self.uploader = uploader
        self.processing = set()  # Archivos en proceso
        
        logger.debug("VideoFileHandler inicializado")
    
    def on_created(self, event):
        """
        Callback cuando se crea un archivo.
        
        Args:
            event: Evento de creación de archivo
        """
        # Ignorar directorios
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Solo procesar archivos con la extensión correcta
        if file_path.suffix != f".{config.VIDEO_FORMAT}":
            return
        
        # Evitar procesar el mismo archivo múltiples veces
        if file_path in self.processing:
            return
        
        logger.debug(f"🔍 Archivo detectado: {file_path.name}")
        
        # Procesar archivo en un thread aparte (no bloquear el watchdog)
        # Por ahora lo hacemos síncronamente
        self._process_file(file_path)
    
    def _is_file_complete(self, file_path: Path) -> bool:
        """
        Verificar que el archivo está completo (no está siendo escrito).
        
        Estrategia SIMPLE y EFECTIVA:
        - Verificar que el archivo existe y tiene tamaño > 1 MB
        - Verificar que no ha sido modificado en los últimos 60 segundos
        - NO hacer sleep ni bloquear
        
        Args:
            file_path: Path del archivo
            
        Returns:
            True si el archivo está completo, False en caso contrario
        """
        try:
            # Verificar que el archivo existe
            if not file_path.exists():
                return False
            
            # Obtener estadísticas del archivo
            stat_info = file_path.stat()
            file_size = stat_info.st_size
            file_mtime = stat_info.st_mtime
            
            # Verificar que el archivo tiene un tamaño razonable (> 1 MB)
            if file_size < 1_000_000:  # 1 MB
                return False
            
            # Verificar que no ha sido modificado recientemente
            # Si el archivo no se modificó en los últimos 60 segundos, está completo
            current_time = time.time()
            time_since_modification = current_time - file_mtime
            
            STABILITY_THRESHOLD = 60  # 60 segundos sin modificaciones
            
            is_complete = time_since_modification >= STABILITY_THRESHOLD
            
            if is_complete:
                logger.info(
                    f"   ✓ Archivo completo: {file_path.name} "
                    f"({file_size / 1_000_000:.1f} MB, estable por {time_since_modification:.0f}s)"
                )
            
            return is_complete
            
        except Exception as e:
            logger.error(f"Error verificando completitud de {file_path.name}: {e}")
            return False
    
    def _process_file(self, file_path: Path):
        """
        Procesar archivo: esperar completitud, subir a S3, mover a uploaded.
        
        Args:
            file_path: Path del archivo a procesar
        """
        try:
            logger.info(f"🔄 Procesando: {file_path.name}")
            
            # Evitar procesar si ya está en progreso
            if file_path in self.processing:
                logger.debug(f"   Ya en proceso: {file_path.name}")
                return
            
            # Marcar como en proceso
            self.processing.add(file_path)
            
            # Verificar que el archivo está completo
            if not self._is_file_complete(file_path):
                logger.warning(f"   ⚠️  Archivo no está completo, se reintentará después")
                # NO mantener en processing para permitir reintentos
                self.processing.discard(file_path)
                return
            
            logger.debug(f"   ✓ Archivo completo")
            
            # Subir a S3
            success = self.uploader.upload_file(file_path)
            
            if success:
                # Decidir si eliminar inmediatamente o mover a uploaded/
                if config.DELETE_IMMEDIATELY_AFTER_UPLOAD:
                    # ELIMINAR INMEDIATAMENTE después de subir exitosamente
                    try:
                        file_size_mb = file_path.stat().st_size / (1024 * 1024)
                        file_path.unlink()
                        logger.debug(f"   ✓ Eliminado localmente ({file_size_mb:.1f} MB liberados)")
                        logger.success(f"✅ Procesado y eliminado: {file_path.name}")
                        
                    except Exception as e:
                        logger.error(f"✗ Error eliminando archivo: {e}")
                else:
                    # MOVER a uploaded/ para eliminar después según retención
                    uploaded_path = config.UPLOADED_DIR / file_path.name
                    
                    try:
                        file_path.rename(uploaded_path)
                        logger.debug(f"   ✓ Movido a: uploaded/")
                        logger.success(f"✅ Procesado exitosamente: {file_path.name}")
                        
                    except Exception as e:
                        logger.error(f"✗ Error moviendo archivo a uploaded/: {e}")
            else:
                logger.error(f"❌ No se pudo subir: {file_path.name}")
                
        except Exception as e:
            logger.error(f"❌ Error procesando {file_path.name}: {e}")
            logger.exception(e)
            
        finally:
            # Remover de conjunto de procesamiento
            self.processing.discard(file_path)


class UploaderService:
    """
    Servicio principal de subida a S3.
    
    Inicializa el uploader, procesa archivos existentes,
    monitorea nuevos archivos y limpia archivos antiguos.
    """
    
    def __init__(self):
        """Inicializar servicio."""
        self.uploader: Optional[S3Uploader] = None
        self.handler: Optional[VideoFileHandler] = None
        self.observer: Optional[Observer] = None
        self.running = False
        self.start_time: Optional[float] = None
        
        # Estadísticas
        self.uploaded_count = 0
        self.failed_count = 0
        
        # Configurar handlers de señales
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        logger.debug("UploaderService inicializado")
    
    def _signal_handler(self, signum, frame):
        """
        Handler para señales de terminación.
        
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
        Validar configuración.
        
        Returns:
            True si es válida, False en caso contrario
        """
        is_valid, error_message = config.validate()
        
        if not is_valid:
            logger.error(f"❌ Configuración inválida: {error_message}")
            return False
        
        logger.success("✓ Configuración válida")
        return True
    
    def _process_existing_files(self):
        """Procesar archivos existentes en la carpeta de recordings."""
        logger.info("🔍 Buscando archivos existentes...")
        
        # Buscar archivos de video
        pattern = f"*.{config.VIDEO_FORMAT}"
        files = list(config.RECORDINGS_DIR.glob(pattern))
        
        if not files:
            logger.info("   No hay archivos para procesar")
            return
        
        logger.info(f"   Encontrados {len(files)} archivos")
        
        # Crear handler temporal
        handler = VideoFileHandler(self.uploader)
        
        # Procesar cada archivo
        for file_path in files:
            handler._process_file(file_path)
        
        logger.success(f"✓ Archivos existentes procesados")
    
    def _cleanup_old_files(self):
        """Eliminar archivos locales antiguos basándose en la retención."""
        logger.info("🧹 Limpiando archivos antiguos...")
        
        # Calcular fecha de corte
        cutoff_time = datetime.now() - timedelta(hours=config.LOCAL_RETENTION_HOURS)
        
        deleted_count = 0
        freed_space_mb = 0
        
        # Buscar archivos en uploaded/
        pattern = f"*.{config.VIDEO_FORMAT}"
        files = list(config.UPLOADED_DIR.glob(pattern))
        
        for file_path in files:
            try:
                # Obtener fecha de modificación
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                # Verificar si es antiguo
                if file_mtime < cutoff_time:
                    file_size_mb = file_path.stat().st_size / (1024 * 1024)
                    
                    # Eliminar archivo
                    file_path.unlink()
                    
                    deleted_count += 1
                    freed_space_mb += file_size_mb
                    
                    logger.debug(f"   ✓ Eliminado: {file_path.name}")
                    
            except Exception as e:
                logger.error(f"Error eliminando {file_path.name}: {e}")
        
        if deleted_count > 0:
            logger.success(
                f"✓ Eliminados {deleted_count} archivos ({freed_space_mb:.1f} MB liberados)"
            )
        else:
            logger.info("   No hay archivos para eliminar")
    
    def _retry_pending_files(self):
        """Reintentar subir archivos pendientes que no fueron procesados."""
        try:
            # Verificar que el handler existe
            if not self.handler:
                return
            
            # Buscar todos los archivos en recordings/
            pattern = f"*.{config.VIDEO_FORMAT}"
            all_files = list(config.RECORDINGS_DIR.glob(pattern))
            
            if not all_files:
                return
            
            # Filtrar archivos:
            # 1. No en processing
            # 2. Con antigüedad > 60 segundos (para que FFmpeg los haya cerrado)
            # 3. Tamaño > 1 MB
            current_time = time.time()
            pending_files = []
            
            for file_path in all_files:
                try:
                    # Verificar que no esté en procesamiento
                    if file_path in self.handler.processing:
                        continue
                    
                    # Verificar antigüedad y tamaño
                    stat_info = file_path.stat()
                    file_age = current_time - stat_info.st_mtime
                    file_size = stat_info.st_size
                    
                    # Debe tener al menos 60 segundos y más de 1 MB
                    if file_age >= 60 and file_size > 1_000_000:
                        pending_files.append(file_path)
                    
                except Exception as e:
                    logger.error(f"Error verificando {file_path.name}: {e}")
            
            if pending_files:
                logger.info(f"📦 Reintentando {len(pending_files)} archivo(s) pendiente(s)...")
                
                for file_path in pending_files:
                    self.handler._process_file(file_path)
            
        except Exception as e:
            logger.error(f"Error en retry de archivos pendientes: {e}")

    def _monitor_loop(self):
        """Loop de monitoreo y mantenimiento."""
        logger.info("👁️  Iniciando loop de monitoreo...")
        
        cleanup_interval = 3600  # Limpiar cada hora
        last_cleanup = time.time()
        retry_interval = 30  # Reintentar archivos pendientes cada 30 segundos
        last_retry = time.time()
        
        while self.running:
            try:
                # Dormir
                time.sleep(30)  # Verificar cada 30 segundos
                
                # Reintentar archivos pendientes cada 30 segundos
                if time.time() - last_retry >= retry_interval:
                    self._retry_pending_files()
                    last_retry = time.time()
                
                # Limpiar archivos antiguos cada hora
                if time.time() - last_cleanup >= cleanup_interval:
                    self._cleanup_old_files()
                    last_cleanup = time.time()
                
                # Log de estado cada 10 minutos
                uptime = time.time() - self.start_time
                if int(uptime) % 600 == 0:
                    logger.info(
                        f"📊 Estado: {self.uploaded_count} subidos, "
                        f"{self.failed_count} fallidos | "
                        f"Uptime: {uptime / 3600:.1f}h"
                    )
                    
            except KeyboardInterrupt:
                logger.info("⌨️  Interrupción de teclado detectada")
                break
                
            except Exception as e:
                logger.error(f"❌ Error en loop de monitoreo: {e}")
                time.sleep(5)
    
    def start(self):
        """Iniciar servicio."""
        logger.info("=" * 70)
        logger.info("☁️  SERVICIO DE SUBIDA A S3")
        logger.info("=" * 70)
        logger.info(f"📅 Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("")
        
        # Validar configuración
        if not self._validate_config():
            logger.error("❌ No se puede iniciar el servicio")
            sys.exit(1)
        
        # Mostrar configuración
        logger.info(f"📦 Bucket S3: {config.S3_BUCKET_NAME}")
        logger.info(f"📂 Monitoreando: {config.RECORDINGS_DIR}")
        logger.info(f"⏱️  Retención local: {config.LOCAL_RETENTION_HOURS} horas")
        logger.info("")
        
        # Inicializar uploader
        try:
            self.uploader = S3Uploader()
        except Exception as e:
            logger.error(f"❌ No se pudo inicializar S3Uploader: {e}")
            sys.exit(1)
        
        logger.info("")
        
        # Procesar archivos existentes
        self._process_existing_files()
        logger.info("")
        
        # Iniciar watchdog observer
        logger.info("🔭 Iniciando monitoreo de archivos nuevos...")
        self.handler = VideoFileHandler(self.uploader)
        self.observer = Observer()
        self.observer.schedule(
            self.handler,
            str(config.RECORDINGS_DIR),
            recursive=False
        )
        self.observer.start()
        logger.success("✓ Monitoreo iniciado")
        
        self.running = True
        self.start_time = time.time()
        
        logger.info("")
        logger.success("✅ Servicio iniciado correctamente")
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
        """Detener servicio."""
        if not self.running:
            return
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("⏹️  DETENIENDO SERVICIO DE SUBIDA")
        logger.info("=" * 70)
        
        self.running = False
        
        # Detener observer
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5)
            logger.debug("✓ Observer detenido")
        
        # Estadísticas finales
        if self.start_time:
            uptime = time.time() - self.start_time
            logger.info(f"⏱️  Uptime total: {uptime / 3600:.2f} horas")
        
        logger.info(f"📊 Archivos subidos: {self.uploaded_count}")
        logger.info(f"❌ Archivos fallidos: {self.failed_count}")
        
        logger.info("")
        logger.success("✅ Servicio detenido correctamente")
        logger.info("=" * 70)


def main():
    """Punto de entrada principal."""
    service = UploaderService()
    
    try:
        service.start()
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        logger.exception(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
