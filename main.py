"""
Sistema Multi-Cámara Inteligente para Monitoreo de Hurones

Punto de entrada principal del sistema. Integra todos los componentes:
- CameraManager: Captura de múltiples streams RTSP
- SyncEngine: Sincronización temporal
- BehaviorDetector: Detección con YOLOv8
- MultiCameraTracker: Tracking y ReID
- BehaviorClassifier: Clasificación de comportamientos
- FusionEngine: Fusión multi-cámara

Autor: Sistema de Monitoreo de Hurones
Fecha: 2025-10-28
"""

import cv2
import sys
import time
import signal
from pathlib import Path
from typing import Dict, List

# Imports locales
from config import config
from core import CameraManager, SyncEngine, FusionEngine
from ai import BehaviorDetector, MultiCameraTracker, BehaviorClassifier
from utils import Visualizer, setup_logger, EventLogger, FPSCounter, LatencyTracker, BehaviorLog
from api.system_bridge import bridge
from loguru import logger


class FerretMonitoringSystem:
    """
    Sistema principal de monitoreo multi-cámara.
    
    Integra todos los componentes del sistema y coordina el flujo de datos
    desde las cámaras hasta la visualización final.
    """
    
    def __init__(self):
        """Inicializar sistema de monitoreo."""
        # Configurar logging
        setup_logger(
            log_file=config.LOG_FILE,
            log_level=config.LOG_LEVEL,
            rotation=config.LOG_ROTATION,
            retention=config.LOG_RETENTION
        )
        
        logger.info("=" * 70)
        logger.info("🐾 FERRET MULTI-CAMERA BEHAVIORAL AI SYSTEM 🐾")
        logger.info("=" * 70)
        
        # Validar configuración
        try:
            config.validate()
            logger.info("✓ Configuración validada")
        except ValueError as e:
            logger.error(f"✗ Error en configuración: {e}")
            sys.exit(1)
        
        # Componentes del sistema
        self.camera_manager = None
        self.sync_engine = None
        self.detector = None
        self.tracker = None
        self.behavior_classifier = None
        self.fusion_engine = None
        self.visualizer = None
        self.event_logger = None
        self.behavior_log = None
        
        # Métricas
        self.fps_counter = FPSCounter(window_size=30)
        self.latency_tracker = LatencyTracker(window_size=100)
        
        # Estado
        self.running = False
        self.frame_count = 0
        
        # Comportamientos actuales por objeto
        self.current_behaviors: Dict[str, str] = {}
        
        logger.info("Sistema inicializado")
    
    def initialize_components(self):
        """Inicializar todos los componentes del sistema."""
        logger.info("\n📦 Inicializando componentes...")
        
        try:
            # 1. Camera Manager
            logger.info("  • Inicializando Camera Manager...")
            self.camera_manager = CameraManager(
                camera_urls=config.CAMERA_URLS,
                camera_names=config.CAMERA_NAMES,
                buffer_size=config.CAMERA_BUFFER_SIZE,
                reconnect_delay=config.CAMERA_RECONNECT_DELAY,
                timeout=config.CAMERA_TIMEOUT,
                target_fps=config.CAMERA_FPS
            )
            logger.info("    ✓ Camera Manager listo")
            
            # 2. Sync Engine
            logger.info("  • Inicializando Sync Engine...")
            self.sync_engine = SyncEngine(
                tolerance_ms=config.SYNC_TOLERANCE_MS,
                buffer_size=config.SYNC_BUFFER_SIZE,
                max_delay_ms=config.SYNC_MAX_DELAY_MS
            )
            
            # Registrar cámaras en sync engine
            for camera_id in range(config.get_camera_count()):
                self.sync_engine.register_camera(camera_id)
            
            logger.info("    ✓ Sync Engine listo")
            
            # 3. Behavior Detector (YOLOv8)
            logger.info("  • Inicializando Behavior Detector...")
            detector_model = config.get_model_path(config.DETECTION_MODEL)
            
            self.detector = BehaviorDetector(
                model_path=str(detector_model),
                confidence_threshold=config.DETECTION_CONFIDENCE,
                iou_threshold=config.DETECTION_IOU_THRESHOLD,
                device=config.get_device(),
                input_size=config.DETECTION_INPUT_SIZE,
                class_names=config.DETECTION_CLASSES
            )
            logger.info("    ✓ Behavior Detector listo")
            
            # 4. Multi-Camera Tracker
            logger.info("  • Inicializando Multi-Camera Tracker...")
            self.tracker = MultiCameraTracker(
                max_age=config.TRACKER_MAX_AGE,
                min_hits=config.TRACKER_MIN_HITS,
                reid_threshold=config.REID_CONFIDENCE_THRESHOLD,
                use_deepsort=True  # Intentar usar DeepSORT
            )
            logger.info("    ✓ Multi-Camera Tracker listo")
            
            # 5. Behavior Classifier
            logger.info("  • Inicializando Behavior Classifier...")
            try:
                behavior_model = config.get_model_path(config.BEHAVIOR_MODEL)
                
                self.behavior_classifier = BehaviorClassifier(
                    model_path=str(behavior_model) if behavior_model.exists() else None,
                    sequence_length=config.BEHAVIOR_SEQUENCE_LENGTH,
                    confidence_threshold=config.BEHAVIOR_CONFIDENCE_THRESHOLD,
                    device=config.get_device(),
                    behavior_classes=config.BEHAVIOR_CLASSES
                )
                logger.info("    ✓ Behavior Classifier listo")
            except Exception as e:
                logger.warning(f"    ⚠️ Behavior Classifier no disponible (error SSL): {e}")
                logger.warning("    → Sistema continuará sin clasificación de comportamientos")
                self.behavior_classifier = None
            
            # 6. Fusion Engine
            if config.FUSION_ENABLED:
                logger.info("  • Inicializando Fusion Engine...")
                self.fusion_engine = FusionEngine(
                    spatial_threshold=config.FUSION_SPATIAL_THRESHOLD,
                    feature_weight=config.FUSION_FEATURE_WEIGHT,
                    enable_3d=config.FUSION_3D_ENABLED,
                    calibration_path=str(config.CALIBRATION_DIR / config.CALIBRATION_FILE)
                        if config.FUSION_3D_ENABLED else None
                )
                logger.info("    ✓ Fusion Engine listo")
            
            # 7. Visualizer
            if config.VISUALIZE_ENABLED:
                logger.info("  • Inicializando Visualizer...")
                self.visualizer = Visualizer(
                    show_ids=config.VISUALIZE_SHOW_IDS,
                    show_confidence=True,
                    show_behavior=config.VISUALIZE_SHOW_BEHAVIOR,
                    show_trajectories=config.VISUALIZE_SHOW_TRAJECTORIES,
                    trajectory_length=config.VISUALIZE_TRAJECTORY_LENGTH,
                    colors=config.VISUALIZE_COLORS
                )
                logger.info("    ✓ Visualizer listo")
            
            # 8. Event Logger
            logger.info("  • Inicializando Event Logger...")
            self.event_logger = EventLogger(
                log_file=config.EVENT_LOG_FILE,
                rotation="500 MB",
                retention="90 days"
            )
            # Compartir event_logger con el bridge para que la API pueda accederlo
            bridge.event_logger = self.event_logger
            logger.info("    ✓ Event Logger listo")
            
            # 9. Behavior Log (Bitácora persistente)
            logger.info("  • Inicializando Behavior Log...")
            self.behavior_log = BehaviorLog(
                db_path=str(config.DATA_DIR / "behavior_log.db")
            )
            logger.info("    ✓ Behavior Log listo")
            
            logger.info("\n✅ Todos los componentes inicializados correctamente\n")
            
        except Exception as e:
            logger.error(f"\n✗ Error inicializando componentes: {e}")
            raise
    
    def process_frame(
        self,
        camera_id: int,
        frame,
        timestamp: float
    ):
        """
        Procesar frame de una cámara.
        
        Args:
            camera_id: ID de la cámara
            frame: Frame capturado
            timestamp: Timestamp del frame
        """
        # Agregar al sync engine
        self.sync_engine.add_frame(camera_id, frame, timestamp)
        
        # Actualizar frame en bridge para API
        bridge.update_frame(
            camera_id=camera_id,
            frame=frame,
            timestamp=timestamp,
            frame_number=self.frame_count
        )
        
        # SOLUCIÓN: Guardar frame en archivo para que la API lo sirva
        # (Los procesos separados no comparten memoria del bridge)
        # Usa escritura atómica para evitar race conditions
        # Solo escribe cada 2 frames (~10 FPS) para reducir I/O
        if self.frame_count % 2 == 0:
            try:
                frame_path = config.DATA_DIR / f"temp_frame_camera_{camera_id}.jpg"
                temp_path = config.DATA_DIR / f"temp_frame_camera_{camera_id}.jpg.tmp"
                
                # Escribir a archivo temporal primero
                cv2.imwrite(str(temp_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                
                # Rename atómico (evita lecturas de archivos parcialmente escritos)
                temp_path.replace(frame_path)
            except Exception as e:
                logger.debug(f"Error guardando frame temporal: {e}")
    
    def process_synced_frames(self):
        """Procesar conjunto de frames sincronizados."""
        # Obtener solo cámaras activas
        from core.camera_manager import CameraStatus
        active_camera_ids = [
            cam_id for cam_id, camera in self.camera_manager.cameras.items()
            if camera.status == CameraStatus.CONNECTED
        ]
        
        if len(active_camera_ids) == 0:
            logger.debug("No hay cámaras activas")
            return
        
        logger.debug(f"Cámaras activas para sincronizar: {active_camera_ids}")
        
        # Obtener frames sincronizados solo de cámaras activas
        synced_frames = self.sync_engine.get_synced_frames(camera_ids=active_camera_ids)
        
        logger.debug(f"Frames sincronizados obtenidos: {len(synced_frames)}")
        
        if len(synced_frames) == 0:
            return
        
        self.latency_tracker.start("total_pipeline")
        
        # 1. DETECCIÓN
        self.latency_tracker.start("detection")
        detections_per_camera = {}
        total_detections = 0
        
        for camera_id, synced_frame in synced_frames.items():
            frame = synced_frame.frame
            detections = self.detector.detect(frame, camera_id=camera_id)
            detections_per_camera[camera_id] = detections
            total_detections += len(detections)
            
            # Verificar y registrar detecciones de humanos
            for det in detections:
                if det.entity_type == "person":
                    # Registrar en event logger
                    if self.event_logger:
                        self.event_logger.log_human_detection(
                            camera_id=camera_id,
                            bbox=det.bbox.tolist(),
                            confidence=float(det.confidence),
                            position=(float(det.center[0]), float(det.center[1])),
                            size=(float(det.width), float(det.height))
                        )
                    
                    # Log adicional en el sistema
                    logger.warning(
                        f"🚨 ALERTA: Humano detectado en Cámara {camera_id} - "
                        f"Confianza: {det.confidence:.2%}, "
                        f"Ubicación: ({det.center[0]:.0f}, {det.center[1]:.0f})"
                    )
                    
                    # Agregar alerta al bridge para que aparezca en el frontend
                    bridge.add_alert(
                        alert_type="warning",
                        message=f"Humano detectado en Cámara {camera_id} (confianza: {det.confidence:.1%})",
                        individual_id=None
                    )
                    
                    # También registrar en behavior log
                    if self.behavior_log:
                        self.behavior_log.log_event(
                            timestamp=synced_frame.timestamp,
                            event_type="human_detection",
                            camera_id=camera_id,
                            confidence=float(det.confidence),
                            metadata={
                                "bbox": det.bbox.tolist(),
                                "position": det.center.tolist(),
                                "size": [det.width, det.height]
                            }
                        )
            
            # Actualizar detecciones en bridge
            bridge.update_frame(
                camera_id=camera_id,
                frame=frame,
                timestamp=synced_frame.timestamp,
                detections=[{
                    "bbox": det.bbox.tolist(),
                    "confidence": float(det.confidence),
                    "class": det.class_name
                } for det in detections],
                frame_number=self.frame_count
            )
        
        self.latency_tracker.end("detection")
        
        # 2. TRACKING
        self.latency_tracker.start("tracking")
        # Preparar frames para el tracker (DeepSORT necesita frames para extraer features)
        frames_per_camera = {
            camera_id: synced_frame.frame
            for camera_id, synced_frame in synced_frames.items()
        }
        tracked_objects = self.tracker.update(detections_per_camera, frames_per_camera)
        self.latency_tracker.end("tracking")
        
        # Actualizar individuos en bridge
        for obj in tracked_objects:
            bridge.update_individual(
                individual_id=obj.global_id,
                confidence=float(obj.confidence),
                cameras=[obj.camera_id],
                position={
                    "x": float(obj.bbox[0]),
                    "y": float(obj.bbox[1]),
                    "width": float(obj.bbox[2] - obj.bbox[0]),
                    "height": float(obj.bbox[3] - obj.bbox[1])
                }
            )
        
        # 3. CLASIFICACIÓN DE COMPORTAMIENTO
        self.latency_tracker.start("behavior")
        for obj in tracked_objects:
            # Obtener frame patch del objeto
            camera_id = obj.camera_id
            if camera_id in synced_frames:
                frame = synced_frames[camera_id].frame
                
                # Extraer patch
                try:
                    x1, y1, x2, y2 = obj.bbox.astype(int)
                    h, w = frame.shape[:2]
                    x1, y1 = max(0, x1), max(0, y1)
                    x2, y2 = min(w, x2), min(h, y2)
                    
                    if x2 > x1 and y2 > y1:
                        patch = frame[y1:y2, x1:x2]
                        
                        # Clasificar comportamiento (si está disponible)
                        if self.behavior_classifier is not None:
                            prediction = self.behavior_classifier.classify(
                                obj.global_id,
                                patch,
                                timestamp=synced_frame.timestamp
                            )
                            
                            if prediction and prediction.confidence >= config.BEHAVIOR_CONFIDENCE_THRESHOLD:
                                # Actualizar comportamiento actual
                                old_behavior = self.current_behaviors.get(obj.global_id)
                                new_behavior = prediction.behavior
                                
                                if old_behavior != new_behavior:
                                    # Cambio de comportamiento
                                    self.current_behaviors[obj.global_id] = new_behavior
                                    
                                    # Registrar en Event Logger (JSON log)
                                    self.event_logger.log_behavior(
                                        object_id=obj.global_id,
                                        behavior=new_behavior,
                                        confidence=prediction.confidence
                                    )
                                    
                                    # Registrar en Behavior Log (Base de datos persistente)
                                    self.behavior_log.add_behavior(
                                        individual_id=obj.global_id,
                                        behavior=new_behavior,
                                        confidence=prediction.confidence,
                                        timestamp=prediction.timestamp,
                                        camera_id=obj.camera_id,
                                        entity_type=obj.entity_type,
                                        metadata={
                                            "probabilities": prediction.probabilities
                                        }
                                    )
                                    
                                    # Actualizar en bridge para API
                                    bridge.log_behavior(
                                        individual_id=obj.global_id,
                                        behavior=new_behavior,
                                        confidence=float(prediction.confidence),
                                        timestamp=synced_frame.timestamp
                                    )
                                    
                                    # Log para consola
                                    behavior_es = config.BEHAVIOR_NAMES_ES.get(new_behavior, new_behavior)
                                    logger.info(
                                        f"🎯 {obj.global_id}: {behavior_es} "
                                        f"(confianza={prediction.confidence:.2f})"
                                    )
                except Exception as e:
                    logger.debug(f"Error procesando comportamiento: {e}")
        
        self.latency_tracker.end("behavior")
        
        # 4. VISUALIZACIÓN
        if config.VISUALIZE_ENABLED and self.visualizer:
            self.latency_tracker.start("visualization")
            
            # Crear frames con visualizaciones
            vis_frames = {}
            for camera_id, synced_frame in synced_frames.items():
                frame = synced_frame.frame
                
                # Filtrar objetos de esta cámara
                camera_objects = [obj for obj in tracked_objects if obj.camera_id == camera_id]
                
                # Dibujar detecciones
                vis_frame = self.visualizer.draw_detections(
                    frame,
                    camera_objects,
                    behaviors=self.current_behaviors
                )
                
                # Agregar info overlay
                info = {
                    "Camera": config.CAMERA_NAMES[camera_id],
                    "Objects": len(camera_objects),
                    "FPS": f"{self.fps_counter.fps:.1f}",
                    "Frame": self.frame_count
                }
                vis_frame = self.visualizer.draw_info_overlay(vis_frame, info)
                
                vis_frames[camera_id] = vis_frame
            
            # Crear mosaico
            mosaic = self.visualizer.create_mosaic(
                vis_frames,
                camera_names={
                    i: name for i, name in enumerate(config.CAMERA_NAMES)
                },
                grid_cols=2
            )
            
            # Mostrar
            cv2.imshow("Ferret Monitoring System", mosaic)
            
            self.latency_tracker.end("visualization")
        
        self.latency_tracker.end("total_pipeline")
        
        # Actualizar contador de frames
        self.frame_count += 1
        
        # Actualizar métricas en bridge
        bridge.update_metrics(
            fps=self.fps_counter.fps,
            total_frames=self.frame_count,
            active_cameras=len(synced_frames),
            active_individuals=len(tracked_objects),
            total_detections=total_detections
        )
        
        # Guardar métricas en archivo JSON para compartir entre procesos
        # (Los procesos separados no comparten memoria del bridge)
        import json
        try:
            metrics_path = config.DATA_DIR / "temp_metrics.json"
            temp_path = config.DATA_DIR / "temp_metrics.json.tmp"
            
            metrics_data = {
                "fps": float(self.fps_counter.fps),
                "total_frames": self.frame_count,
                "active_cameras": len(synced_frames),
                "active_individuals": len(tracked_objects),
                "total_detections": total_detections,
                "timestamp": time.time()
            }
            
            # Escribir a archivo temporal primero
            with open(temp_path, 'w') as f:
                json.dump(metrics_data, f)
            
            # Rename atómico
            temp_path.replace(metrics_path)
        except Exception as e:
            logger.debug(f"Error guardando métricas temporales: {e}")
    
    def run(self):
        """Ejecutar el sistema de monitoreo."""
        logger.info("\n🚀 Iniciando sistema de monitoreo...\n")
        
        # Inicializar componentes
        self.initialize_components()
        
        # Iniciar cámaras
        logger.info("📹 Iniciando captura de cámaras...")
        self.camera_manager.start_all()
        
        # Esperar a que las cámaras se estabilicen
        time.sleep(2)
        
        # Verificar que las cámaras están funcionando
        stats = self.camera_manager.get_stats()
        alive_cameras = sum(1 for s in stats.values() if s['alive'])
        
        if alive_cameras == 0:
            logger.warning("⚠️ No hay cámaras conectadas.")
            logger.warning("→ Sistema continuará en modo SOLO-API (sin procesamiento de video)")
            logger.info("💡 Puedes acceder a la API en http://localhost:8000")
            logger.info("Sistema en ejecución. Presiona Ctrl+C para salir.\n")
        else:
            logger.info(f"✓ {alive_cameras}/{len(config.CAMERA_URLS)} cámaras activas\n")
            logger.info("Sistema en ejecución. Presiona 'q' para salir.\n")
        
        # Actualizar estado inicial de cámaras en bridge
        for camera_id, stat in stats.items():
            bridge.update_camera(
                camera_id=camera_id,
                name=stat['name'],
                status=stat['status'],
                fps=stat['fps'],
                resolution=config.CAMERA_RESOLUTION
            )
        
        self.running = True
        last_stats_time = time.time()
        
        try:
            while self.running:
                # Si no hay cámaras, solo mantener vivo el sistema para la API
                if alive_cameras == 0:
                    time.sleep(1.0)  # Esperar sin consumir CPU
                    continue
                
                # Obtener frames de todas las cámaras
                frames = self.camera_manager.get_frames(timeout=0.5)
                
                # Si no hay frames, continuar
                if not frames:
                    time.sleep(0.1)
                    continue
                
                # Procesar cada frame
                for camera_id, (frame, timestamp) in frames.items():
                    self.process_frame(camera_id, frame, timestamp)
                
                # Procesar frames sincronizados
                self.process_synced_frames()
                
                # Actualizar FPS
                self.fps_counter.update()
                
                # Mostrar estadísticas cada 5 segundos
                if time.time() - last_stats_time >= 5.0:
                    self.print_stats()
                    last_stats_time = time.time()
                
                # Tecla para salir
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    logger.info("\n👋 Saliendo...")
                    break
        
        except KeyboardInterrupt:
            logger.info("\n⚠️  Interrupción del usuario")
        
        except Exception as e:
            logger.error(f"\n❌ Error fatal: {e}")
            logger.exception(e)
        
        finally:
            self.shutdown()
    
    def print_stats(self):
        """Imprimir estadísticas del sistema."""
        logger.info("\n" + "=" * 60)
        logger.info("📊 ESTADÍSTICAS DEL SISTEMA")
        logger.info("=" * 60)
        
        # FPS
        logger.info(f"FPS: {self.fps_counter.fps:.1f} (avg: {self.fps_counter.avg_fps:.1f})")
        logger.info(f"Frames procesados: {self.frame_count}")
        
        # Cámaras
        camera_stats = self.camera_manager.get_stats()
        logger.info(f"\n📹 Cámaras:")
        for cam_id, stats in camera_stats.items():
            status_icon = "✓" if stats['alive'] else "✗"
            logger.info(
                f"  {status_icon} {stats['name']}: "
                f"{stats['fps']:.1f} FPS, "
                f"queue={stats['queue_size']}"
            )
        
        # Tracking
        tracker_stats = self.tracker.get_stats()
        logger.info(f"\n🎯 Tracking:")
        logger.info(f"  Objetos activos: {tracker_stats['total_tracks']}")
        logger.info(f"  IDs globales: {tracker_stats['active_global_ids']}")
        logger.info(f"  Matches ReID: {tracker_stats['reid_matches']}")
        
        # Comportamientos
        if self.current_behaviors:
            logger.info(f"\n🧠 Comportamientos actuales:")
            for obj_id, behavior in self.current_behaviors.items():
                behavior_es = config.BEHAVIOR_NAMES_ES.get(behavior, behavior)
                logger.info(f"  {obj_id}: {behavior_es}")
        
        # Latencias
        latency_stats = self.latency_tracker.get_all_stats()
        if latency_stats:
            logger.info(f"\n⏱️  Latencias:")
            for op, stats in latency_stats.items():
                if stats:
                    logger.info(
                        f"  {op}: {stats['mean_ms']:.1f}ms "
                        f"(±{stats['std_ms']:.1f}ms)"
                    )
        
        logger.info("=" * 60 + "\n")
    
    def shutdown(self):
        """Apagar el sistema de forma segura."""
        logger.info("\n🔄 Cerrando sistema...")
        
        self.running = False
        
        # Detener cámaras
        if self.camera_manager:
            self.camera_manager.stop_all()
            logger.info("  ✓ Cámaras detenidas")
        
        # Cerrar ventanas
        cv2.destroyAllWindows()
        logger.info("  ✓ Ventanas cerradas")
        
        # Estadísticas finales
        logger.info("\n📈 Estadísticas finales:")
        logger.info(f"  Total frames: {self.frame_count}")
        logger.info(f"  FPS promedio: {self.fps_counter.avg_fps:.1f}")
        
        logger.info("\n✅ Sistema cerrado correctamente")
        logger.info("=" * 70)


def signal_handler(sig, frame):
    """Manejar señales del sistema (Ctrl+C)."""
    logger.info("\n⚠️  Señal de interrupción recibida")
    sys.exit(0)


def main():
    """Función principal."""
    # Registrar handler para Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Crear y ejecutar sistema
    system = FerretMonitoringSystem()
    system.run()


if __name__ == "__main__":
    main()



