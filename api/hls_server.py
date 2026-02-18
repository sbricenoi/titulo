"""
Servidor HLS independiente para streaming de video al frontend.
Usa FFmpeg para convertir RTSP a HLS sin afectar el análisis AI.

Autor: Sistema de Monitoreo de Hurones
Fecha: 2025-11-10
"""

import subprocess
import os
import signal
import time
from pathlib import Path
from typing import Dict, Optional
from loguru import logger
import threading


class HLSStreamServer:
    """
    Servidor HLS que convierte streams RTSP a HLS para reproducción en navegadores.
    Completamente independiente del análisis AI.
    """
    
    def __init__(self, camera_urls: Dict[int, str], hls_output_dir: str = "/tmp/hls_streams"):
        """
        Inicializar servidor HLS.
        
        Args:
            camera_urls: Diccionario {camera_id: rtsp_url} de cámaras
            hls_output_dir: Directorio donde se guardarán los archivos HLS
        """
        self.camera_urls = camera_urls
        self.hls_output_dir = Path(hls_output_dir)
        self.processes: Dict[int, subprocess.Popen] = {}
        self.running = False
        
        # Crear directorio de salida
        self.hls_output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Directorio HLS: {self.hls_output_dir}")
    
    def start_camera_stream(self, camera_id: int) -> bool:
        """
        Iniciar conversión RTSP → HLS para una cámara.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            True si se inició correctamente
        """
        if camera_id in self.processes:
            logger.warning(f"⚠️  Stream HLS ya existe para cámara {camera_id}")
            return True
        
        if camera_id not in self.camera_urls:
            logger.error(f"❌ Cámara {camera_id} no existe en configuración")
            return False
        
        camera_url = self.camera_urls[camera_id]
        output_path = self.hls_output_dir / f"camera_{camera_id}"
        output_path.mkdir(exist_ok=True)
        
        playlist_file = output_path / "stream.m3u8"
        
        # ESTRATEGIA SIMPLE Y ESTABLE: Re-codificar TODAS las cámaras con configuración compatible
        # Esto asegura que todos los streams sean compatibles y estables
        logger.info(f"🔄 Cámara {camera_id}: Re-codificando con perfil compatible")
        cmd = [
            'ffmpeg',
            '-rtsp_transport', 'tcp',
            '-i', camera_url,
            '-c:v', 'libx264',  # Re-codificar siempre
            '-preset', 'ultrafast',  # Máxima velocidad (bajo CPU)
            '-tune', 'zerolatency',  # Baja latencia
            '-profile:v', 'baseline',  # Perfil Baseline (máxima compatibilidad)
            '-level', '3.0',  # Nivel 3.0 (compatible con todos los navegadores)
            '-b:v', '1200k',  # 1.2 Mbps
            '-maxrate', '1500k',
            '-bufsize', '2400k',
            '-g', '50',  # Keyframe cada 50 frames (~2.5 seg)
            '-sc_threshold', '0',
            '-pix_fmt', 'yuv420p',  # Pixel format compatible
            '-an',  # Sin audio
            '-f', 'hls',
            '-hls_time', '3',  # Segmentos de 3 segundos (balance estabilidad/latencia)
            '-hls_list_size', '3',  # 3 segmentos (9 segundos buffer)
            '-hls_flags', 'delete_segments+append_list+omit_endlist',
            '-hls_segment_type', 'mpegts',
            '-hls_segment_filename', str(output_path / 'segment_%03d.ts'),
            '-start_number', '0',
            str(playlist_file),
            '-loglevel', 'error',  # Solo errores críticos
            '-nostats'
        ]
        
        try:
            logger.info(f"🎬 Iniciando stream HLS para cámara {camera_id}")
            logger.debug(f"   RTSP: {camera_url}")
            logger.debug(f"   HLS: {playlist_file}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            self.processes[camera_id] = process
            
            # Esperar a que se genere el playlist
            for i in range(30):  # 15 segundos máximo
                if playlist_file.exists():
                    logger.info(f"✅ Stream HLS listo para cámara {camera_id}")
                    return True
                time.sleep(0.5)
            
            logger.warning(f"⚠️  Playlist no generado para cámara {camera_id}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error iniciando stream HLS cámara {camera_id}: {e}")
            return False
    
    def stop_camera_stream(self, camera_id: int):
        """
        Detener stream HLS de una cámara.
        
        Args:
            camera_id: ID de la cámara
        """
        if camera_id not in self.processes:
            return
        
        process = self.processes[camera_id]
        
        try:
            logger.info(f"🛑 Deteniendo stream HLS cámara {camera_id}")
            
            # Enviar SIGTERM
            if os.name != 'nt':
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            else:
                process.terminate()
            
            # Esperar a que termine
            process.wait(timeout=5)
            
        except subprocess.TimeoutExpired:
            # Si no termina, forzar
            logger.warning(f"⚠️  Forzando cierre de stream HLS cámara {camera_id}")
            if os.name != 'nt':
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            else:
                process.kill()
        
        except Exception as e:
            logger.error(f"❌ Error deteniendo stream HLS cámara {camera_id}: {e}")
        
        finally:
            del self.processes[camera_id]
            logger.info(f"✓ Stream HLS detenido: cámara {camera_id}")
    
    def start_all(self):
        """Iniciar streams HLS para todas las cámaras."""
        self.running = True
        logger.info(f"🚀 Iniciando servidor HLS para {len(self.camera_urls)} cámaras")
        
        threads = []
        for camera_id in self.camera_urls.keys():
            # Iniciar cada stream en un thread separado para no bloquear
            thread = threading.Thread(
                target=self.start_camera_stream,
                args=(camera_id,),
                daemon=True
            )
            thread.start()
            threads.append(thread)
        
        # Esperar a que todos los streams inicien
        for thread in threads:
            thread.join(timeout=20)
        
        logger.info(f"✅ Servidor HLS iniciado: {len(self.processes)}/{len(self.camera_urls)} cámaras activas")
    
    def stop_all(self):
        """Detener todos los streams HLS."""
        self.running = False
        logger.info("🛑 Deteniendo servidor HLS...")
        
        for camera_id in list(self.processes.keys()):
            self.stop_camera_stream(camera_id)
        
        logger.info("✓ Servidor HLS detenido")
    
    def get_playlist_url(self, camera_id: int, base_url: str = "http://localhost:8000") -> Optional[str]:
        """
        Obtener URL del playlist HLS para una cámara.
        
        Args:
            camera_id: ID de la cámara
            base_url: URL base del servidor
            
        Returns:
            URL del playlist M3U8
        """
        if camera_id not in self.processes:
            return None
        
        return f"{base_url}/hls/camera_{camera_id}/stream.m3u8"
    
    def is_stream_active(self, camera_id: int) -> bool:
        """
        Verificar si un stream HLS está activo.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            True si el stream está activo
        """
        if camera_id not in self.processes:
            return False
        
        process = self.processes[camera_id]
        return process.poll() is None  # None = proceso sigue corriendo
    
    def monitor_streams(self):
        """
        Monitorear y reiniciar streams si se caen.
        Ejecutar en un thread separado.
        """
        logger.info("👁️  Monitor de streams HLS iniciado")
        
        while self.running:
            for camera_id in self.camera_urls.keys():
                if not self.is_stream_active(camera_id):
                    logger.warning(f"⚠️  Stream HLS caído para cámara {camera_id}, reiniciando...")
                    self.stop_camera_stream(camera_id)
                    time.sleep(1)
                    self.start_camera_stream(camera_id)
            
            time.sleep(10)  # Revisar cada 10 segundos
        
        logger.info("✓ Monitor de streams HLS detenido")
    
    async def start_camera_stream_async(self, camera_id: int, camera_url: str) -> bool:
        """
        Versión asíncrona de start_camera_stream para agregar cámaras dinámicamente.
        
        Args:
            camera_id: ID de la cámara
            camera_url: URL RTSP de la cámara
            
        Returns:
            True si se inició correctamente
        """
        # Agregar URL al diccionario
        self.camera_urls[camera_id] = camera_url
        
        # Iniciar stream en thread para no bloquear
        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self.start_camera_stream,
            camera_id
        )
        
        return result
    
    async def stop_camera_stream_async(self, camera_id: int):
        """
        Versión asíncrona de stop_camera_stream.
        
        Args:
            camera_id: ID de la cámara
        """
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self.stop_camera_stream,
            camera_id
        )
    
    def get_active_streams(self) -> list:
        """
        Obtener lista de IDs de cámaras con streams activos.
        
        Returns:
            Lista de IDs de cámaras
        """
        active = []
        for camera_id, process in self.processes.items():
            if process.poll() is None:
                active.append(camera_id)
        return active
    
    def get_stream_count(self) -> int:
        """
        Obtener número de streams activos.
        
        Returns:
            Número de streams
        """
        return len([p for p in self.processes.values() if p.poll() is None])
    
    def is_stream_running(self, camera_id: int) -> bool:
        """Alias para is_stream_active (compatibilidad)."""
        return self.is_stream_active(camera_id)


# Instancia global (se inicializa en main.py al arrancar la API)
hls_server: Optional[HLSStreamServer] = None


def initialize_hls_server(camera_urls: Dict[int, str]):
    """
    Inicializar y arrancar el servidor HLS.
    
    Args:
        camera_urls: Diccionario {camera_id: rtsp_url} de cámaras
    """
    global hls_server
    
    hls_server = HLSStreamServer(camera_urls)
    hls_server.start_all()
    
    # Iniciar monitor en thread separado
    monitor_thread = threading.Thread(
        target=hls_server.monitor_streams,
        daemon=True
    )
    monitor_thread.start()
    
    return hls_server


def shutdown_hls_server():
    """Detener el servidor HLS."""
    global hls_server
    
    if hls_server:
        hls_server.stop_all()
        hls_server = None

