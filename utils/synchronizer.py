"""
Synchronizer - Herramientas de sincronización y medición temporal.

Este módulo proporciona utilidades para sincronización temporal,
medición de FPS, y coordinación de componentes.

Autor: Sistema de Monitoreo de Hurones
Fecha: 2025-10-28
"""

import time
import numpy as np
from typing import Optional, Dict
from collections import deque
from dataclasses import dataclass, field


@dataclass
class TimeSync:
    """
    Sincronizador temporal simple.
    
    Permite mantener un FPS constante introduciendo delays apropiados.
    
    Ejemplo:
        >>> sync = TimeSync(target_fps=30)
        >>> while True:
        ...     # Hacer procesamiento
        ...     sync.wait()  # Espera para mantener 30 FPS
    """
    target_fps: float = 30.0
    last_time: float = field(default_factory=time.time)
    
    @property
    def target_interval(self) -> float:
        """Intervalo objetivo en segundos."""
        return 1.0 / self.target_fps if self.target_fps > 0 else 0
    
    def wait(self) -> float:
        """
        Esperar el tiempo necesario para mantener FPS objetivo.
        
        Returns:
            Tiempo real transcurrido desde último wait
        """
        current_time = time.time()
        elapsed = current_time - self.last_time
        
        # Calcular tiempo de espera
        sleep_time = self.target_interval - elapsed
        
        if sleep_time > 0:
            time.sleep(sleep_time)
            current_time = time.time()
            elapsed = current_time - self.last_time
        
        self.last_time = current_time
        return elapsed
    
    def reset(self):
        """Resetear el tiempo base."""
        self.last_time = time.time()


class FPSCounter:
    """
    Contador de FPS con promedio móvil.
    
    Calcula FPS en tiempo real usando una ventana deslizante.
    
    Ejemplo:
        >>> fps_counter = FPSCounter(window_size=30)
        >>> fps_counter.update()
        >>> print(f"FPS: {fps_counter.fps:.1f}")
    """
    
    def __init__(self, window_size: int = 30):
        """
        Inicializar contador de FPS.
        
        Args:
            window_size: Tamaño de la ventana para promedio móvil
        """
        self.window_size = window_size
        self.timestamps = deque(maxlen=window_size)
        self.frame_count = 0
        self.start_time = time.time()
        self._fps = 0.0
    
    def update(self) -> float:
        """
        Actualizar contador con nuevo frame.
        
        Returns:
            FPS actual
        """
        current_time = time.time()
        self.timestamps.append(current_time)
        self.frame_count += 1
        
        # Calcular FPS
        if len(self.timestamps) >= 2:
            time_span = self.timestamps[-1] - self.timestamps[0]
            if time_span > 0:
                self._fps = (len(self.timestamps) - 1) / time_span
        
        return self._fps
    
    @property
    def fps(self) -> float:
        """FPS actual."""
        return self._fps
    
    @property
    def avg_fps(self) -> float:
        """FPS promedio desde el inicio."""
        elapsed = time.time() - self.start_time
        if elapsed > 0:
            return self.frame_count / elapsed
        return 0.0
    
    def reset(self):
        """Resetear contador."""
        self.timestamps.clear()
        self.frame_count = 0
        self.start_time = time.time()
        self._fps = 0.0


class LatencyTracker:
    """
    Rastreador de latencias del sistema.
    
    Mide el tiempo de diferentes etapas del pipeline.
    
    Ejemplo:
        >>> tracker = LatencyTracker()
        >>> tracker.start("detection")
        >>> # ... código de detección ...
        >>> tracker.end("detection")
        >>> print(tracker.get_stats("detection"))
    """
    
    def __init__(self, window_size: int = 100):
        """
        Inicializar tracker de latencias.
        
        Args:
            window_size: Tamaño de ventana para estadísticas
        """
        self.window_size = window_size
        self.latencies: Dict[str, deque] = {}
        self.start_times: Dict[str, float] = {}
    
    def start(self, operation: str):
        """
        Iniciar medición de una operación.
        
        Args:
            operation: Nombre de la operación
        """
        self.start_times[operation] = time.time()
    
    def end(self, operation: str) -> Optional[float]:
        """
        Finalizar medición de una operación.
        
        Args:
            operation: Nombre de la operación
            
        Returns:
            Latencia en milisegundos o None si no se inició
        """
        if operation not in self.start_times:
            return None
        
        latency = (time.time() - self.start_times[operation]) * 1000  # ms
        
        # Agregar a historial
        if operation not in self.latencies:
            self.latencies[operation] = deque(maxlen=self.window_size)
        
        self.latencies[operation].append(latency)
        
        # Limpiar start time
        del self.start_times[operation]
        
        return latency
    
    def get_stats(self, operation: str) -> Optional[Dict[str, float]]:
        """
        Obtener estadísticas de una operación.
        
        Args:
            operation: Nombre de la operación
            
        Returns:
            Dict con min, max, mean, std (en ms)
        """
        if operation not in self.latencies or not self.latencies[operation]:
            return None
        
        values = np.array(self.latencies[operation])
        
        return {
            "min_ms": float(values.min()),
            "max_ms": float(values.max()),
            "mean_ms": float(values.mean()),
            "std_ms": float(values.std()),
            "count": len(values)
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """
        Obtener estadísticas de todas las operaciones.
        
        Returns:
            Dict {operation: stats}
        """
        return {
            op: self.get_stats(op)
            for op in self.latencies.keys()
        }
    
    def reset(self, operation: Optional[str] = None):
        """
        Resetear estadísticas.
        
        Args:
            operation: Operación específica (None = todas)
        """
        if operation is None:
            self.latencies.clear()
            self.start_times.clear()
        else:
            if operation in self.latencies:
                self.latencies[operation].clear()
            if operation in self.start_times:
                del self.start_times[operation]


class RateLimiter:
    """
    Limitador de tasa para control de flujo.
    
    Útil para limitar la frecuencia de operaciones costosas.
    
    Ejemplo:
        >>> limiter = RateLimiter(max_rate=10)  # 10 ops/segundo
        >>> if limiter.allow():
        ...     # Ejecutar operación costosa
        ...     pass
    """
    
    def __init__(self, max_rate: float):
        """
        Inicializar rate limiter.
        
        Args:
            max_rate: Tasa máxima (operaciones por segundo)
        """
        self.max_rate = max_rate
        self.min_interval = 1.0 / max_rate if max_rate > 0 else 0
        self.last_time = 0.0
    
    def allow(self) -> bool:
        """
        Verificar si se permite una operación.
        
        Returns:
            True si se permite, False si debe esperar
        """
        current_time = time.time()
        elapsed = current_time - self.last_time
        
        if elapsed >= self.min_interval:
            self.last_time = current_time
            return True
        
        return False
    
    def wait_if_needed(self):
        """Esperar si es necesario para respetar la tasa."""
        current_time = time.time()
        elapsed = current_time - self.last_time
        
        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            time.sleep(sleep_time)
        
        self.last_time = time.time()
    
    def reset(self):
        """Resetear el limitador."""
        self.last_time = 0.0


# ==================== EJEMPLO DE USO ====================
if __name__ == "__main__":
    """Ejemplo de uso de las herramientas de sincronización."""
    
    from loguru import logger
    
    logger.info("Test de herramientas de sincronización")
    
    # Test FPSCounter
    logger.info("\n=== Test FPSCounter ===")
    fps_counter = FPSCounter(window_size=30)
    
    for i in range(100):
        fps_counter.update()
        time.sleep(0.033)  # ~30 FPS
        
        if i % 30 == 0:
            logger.info(f"Frame {i}: FPS={fps_counter.fps:.1f}, Avg={fps_counter.avg_fps:.1f}")
    
    # Test TimeSync
    logger.info("\n=== Test TimeSync ===")
    sync = TimeSync(target_fps=10)
    
    start = time.time()
    for i in range(10):
        # Simular procesamiento
        time.sleep(0.05)
        
        # Sincronizar
        elapsed = sync.wait()
        logger.info(f"Iteration {i}: elapsed={elapsed*1000:.1f}ms")
    
    total_time = time.time() - start
    logger.info(f"Total time: {total_time:.2f}s (esperado: ~1.0s)")
    
    # Test LatencyTracker
    logger.info("\n=== Test LatencyTracker ===")
    tracker = LatencyTracker()
    
    for i in range(50):
        tracker.start("operation_a")
        time.sleep(0.01 + np.random.rand() * 0.02)
        tracker.end("operation_a")
        
        tracker.start("operation_b")
        time.sleep(0.005 + np.random.rand() * 0.01)
        tracker.end("operation_b")
    
    logger.info("Estadísticas de latencias:")
    for op, stats in tracker.get_all_stats().items():
        logger.info(f"  {op}: {stats['mean_ms']:.2f}ms (±{stats['std_ms']:.2f}ms)")
    
    # Test RateLimiter
    logger.info("\n=== Test RateLimiter ===")
    limiter = RateLimiter(max_rate=5)  # 5 ops/segundo
    
    count = 0
    start = time.time()
    
    while time.time() - start < 2.0:
        if limiter.allow():
            count += 1
            logger.info(f"Operation {count} allowed at {time.time()-start:.2f}s")
    
    logger.info(f"Total operations in 2s: {count} (esperado: ~10)")
    
    logger.info("\nTest completado")





