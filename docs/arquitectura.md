# Arquitectura del Sistema Multi-Cámara Inteligente para Hurones

## 🎯 Visión General

Este documento describe la arquitectura completa del **Ferret Multi-Camera Behavioral AI System**, un sistema de monitoreo inteligente basado en IA capaz de rastrear y analizar el comportamiento de hurones mediante múltiples cámaras IP en tiempo real.

## 📐 Arquitectura del Sistema

### Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                     CÁMARAS IP (RTSP)                       │
│  Camera 1    Camera 2    Camera 3    ...    Camera N        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   CAMERA MANAGER                            │
│  • Conexión asíncrona a múltiples streams                  │
│  • Reconexión automática                                    │
│  • Buffer de frames por cámara                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   SYNC ENGINE                               │
│  • Sincronización temporal (timestamps)                     │
│  • Alineación de frames entre cámaras                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   AI PIPELINE                               │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  DETECTOR   │→ │   TRACKER    │→ │  BEHAVIOR    │      │
│  │  (YOLOv8)   │  │ (DeepSORT+   │  │  CLASSIFIER  │      │
│  │             │  │   ReID)      │  │ (CNN+LSTM)   │      │
│  └─────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   FUSION ENGINE                             │
│  • Fusión de detecciones multi-cámara                      │
│  • Eliminación de duplicados                               │
│  • Cálculo de posición 3D (opcional)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              OUTPUTS & LOGGING                              │
│  • Event Logger  • Visualizer  • Dashboard API             │
└─────────────────────────────────────────────────────────────┘
```

## 🗂️ Estructura de Carpetas

```
ferret_monitoring/
│
├── main.py                      # Punto de entrada principal
├── config.py                    # Configuración centralizada
├── requirements.txt             # Dependencias Python
├── README.md                    # Documentación de usuario
│
├── docs/
│   ├── arquitectura.md          # Este documento
│   ├── api.md                   # Documentación API
│   └── deployment.md            # Guía de despliegue
│
├── core/                        # Módulos centrales del sistema
│   ├── __init__.py
│   ├── camera_manager.py        # Gestión de streams RTSP
│   ├── sync_engine.py           # Sincronización temporal
│   └── fusion_engine.py         # Fusión multi-cámara
│
├── ai/                          # Módulos de inteligencia artificial
│   ├── __init__.py
│   ├── detector.py              # Detección de individuos (YOLOv8)
│   ├── tracker.py               # Tracking + Re-ID multi-cámara
│   ├── behavior_model.py        # Clasificación de comportamientos
│   └── trainer.py               # Reentrenamiento incremental
│
├── data/                        # Datos del sistema
│   ├── calibration/             # Parámetros de calibración de cámaras
│   │   ├── camera_1.json
│   │   ├── camera_2.json
│   │   └── intrinsics.json
│   ├── logs/                    # Logs de eventos y errores
│   ├── models/                  # Modelos entrenados
│   │   ├── yolov8_ferret.pt
│   │   ├── reid_model.pth
│   │   └── behavior_classifier.pth
│   └── training/                # Datos de entrenamiento
│       ├── clips/
│       └── annotations/
│
└── utils/                       # Utilidades y helpers
    ├── __init__.py
    ├── visualizer.py            # Visualización de resultados
    ├── logger.py                # Sistema de logging
    └── synchronizer.py          # Herramientas de sincronización
```

## 🔧 Componentes Principales

### 1. Camera Manager (`core/camera_manager.py`)

**Responsabilidades:**
- Conexión asíncrona a múltiples streams RTSP
- Gestión de reconexión automática ante fallos
- Buffer de frames por cámara
- Control de FPS y resolución

**Tecnologías:**
- OpenCV para captura de video
- Threading/asyncio para procesamiento paralelo
- Queue para buffering

**API Principal:**
```python
class CameraManager:
    def __init__(self, camera_urls: List[str])
    def start_all(self)
    def stop_all(self)
    def get_frames(self) -> Dict[int, np.ndarray]
    def is_camera_alive(self, camera_id: int) -> bool
```

### 2. Sync Engine (`core/sync_engine.py`)

**Responsabilidades:**
- Sincronización temporal de frames entre cámaras
- Compensación de latencias
- Alineación por timestamps
- Buffer temporal para sincronización

**Algoritmo:**
1. Cada frame recibe timestamp de captura
2. Buffer mantiene ventana temporal (~500ms)
3. Selección de frames más cercanos temporalmente
4. Interpolación si es necesario

**API Principal:**
```python
class SyncEngine:
    def __init__(self, tolerance_ms: int = 100)
    def add_frame(self, camera_id: int, frame: np.ndarray, timestamp: float)
    def get_synced_frames(self) -> Dict[int, Tuple[np.ndarray, float]]
```

### 3. Fusion Engine (`core/fusion_engine.py`)

**Responsabilidades:**
- Fusión de detecciones de múltiples cámaras
- Eliminación de duplicados
- Cálculo de posición 3D (si hay calibración)
- Mantenimiento de identidades consistentes

**Algoritmos:**
- **Matching espacial:** Comparación de features ReID entre cámaras
- **Filtro de Kalman 3D:** Predicción de posiciones
- **Hungarian Algorithm:** Asignación óptima de detecciones

**API Principal:**
```python
class FusionEngine:
    def __init__(self, calibration_path: str = None)
    def merge_detections(self, detections_per_camera: Dict) -> List[FusedObject]
    def eliminate_duplicates(self, objects: List) -> List[FusedObject]
    def calculate_3d_position(self, detections: List) -> np.ndarray
```

### 4. Detector (`ai/detector.py`)

**Responsabilidades:**
- Detección de hurones en frames individuales
- Extracción de bounding boxes y keypoints
- Estimación de pose (opcional)

**Modelo:**
- **YOLOv8** (ultralytics) fine-tuned para hurones
- Entrada: Frame RGB (640x640)
- Salida: Bounding boxes + confidence scores

**API Principal:**
```python
class BehaviorDetector:
    def __init__(self, model_path: str, confidence_threshold: float = 0.5)
    def detect(self, frame: np.ndarray) -> List[Detection]
    def batch_detect(self, frames: List[np.ndarray]) -> List[List[Detection]]
```

### 5. Tracker (`ai/tracker.py`)

**Responsabilidades:**
- Tracking de individuos dentro de una cámara
- Re-identificación entre cámaras (ReID)
- Mantenimiento de IDs únicos globales

**Tecnologías:**
- **DeepSORT** o **ByteTrack** para tracking local
- **OSNet/FastReID** para features de re-identificación
- Kalman Filter para predicción de trayectorias

**API Principal:**
```python
class MultiCameraTracker:
    def __init__(self, reid_model_path: str)
    def update(self, detections_per_camera: Dict) -> List[TrackedObject]
    def get_global_id(self, local_id: int, camera_id: int) -> str
```

### 6. Behavior Model (`ai/behavior_model.py`)

**Responsabilidades:**
- Clasificación de comportamientos
- Análisis de secuencias temporales
- Detección de interacciones entre individuos

**Comportamientos Detectados:**
- Comer
- Dormir
- Jugar
- Desplazarse
- Interacción social
- Comportamiento anómalo

**Arquitectura del Modelo:**
- CNN para features espaciales (ResNet/EfficientNet)
- LSTM o Transformer para secuencias temporales
- Clasificador multi-clase

**API Principal:**
```python
class BehaviorClassifier:
    def __init__(self, model_path: str, sequence_length: int = 30)
    def classify(self, tracked_object: TrackedObject, frame_sequence: List) -> str
    def detect_interaction(self, objects: List[TrackedObject]) -> List[Interaction]
```

### 7. Trainer (`ai/trainer.py`)

**Responsabilidades:**
- Reentrenamiento incremental
- Gestión de nuevos datos anotados
- Evaluación de modelos
- Exportación de checkpoints

**Estrategia:**
- **Continual Learning** para evitar olvido catastrófico
- Replay buffer con muestras antiguas
- Fine-tuning periódico

**API Principal:**
```python
class IncrementalTrainer:
    def __init__(self, model: nn.Module, data_path: str)
    def add_training_data(self, clips: List, labels: List)
    def train_epoch(self) -> Dict[str, float]
    def evaluate(self) -> Dict[str, float]
    def save_checkpoint(self, path: str)
```

## 🔄 Flujo de Datos

### Pipeline Completo

```
1. CAPTURA
   └─ CameraManager captura frames de N cámaras

2. SINCRONIZACIÓN
   └─ SyncEngine alinea frames temporalmente

3. DETECCIÓN
   └─ Detector identifica hurones en cada frame
   └─ Output: [camera_id, bbox, confidence, features]

4. TRACKING
   └─ Tracker asigna IDs locales por cámara
   └─ ReID asigna ID global único

5. FUSIÓN
   └─ FusionEngine combina info de múltiples cámaras
   └─ Elimina duplicados
   └─ Calcula posición 3D (opcional)

6. CLASIFICACIÓN DE COMPORTAMIENTO
   └─ BehaviorClassifier analiza secuencias
   └─ Output: [ferret_id, behavior, confidence, timestamp]

7. OUTPUT
   └─ Logger guarda eventos
   └─ Visualizer muestra resultados
   └─ Dashboard API expone datos en tiempo real
```

## 🎛️ Configuración

### config.py - Parámetros Principales

```python
# Cámaras
CAMERA_URLS = [
    "rtsp://user:pass@192.168.1.10:554/stream1",
    "rtsp://user:pass@192.168.1.11:554/stream1"
]
CAMERA_FPS = 30
CAMERA_RESOLUTION = (1920, 1080)

# Sincronización
SYNC_TOLERANCE_MS = 100
SYNC_BUFFER_SIZE = 15

# Detección
DETECTION_MODEL = "models/yolov8_ferret.pt"
DETECTION_CONFIDENCE = 0.5
DETECTION_IOU = 0.45

# Tracking
REID_MODEL = "models/reid_model.pth"
MAX_AGE = 30  # frames sin detección antes de eliminar track
MIN_HITS = 3  # detecciones mínimas para confirmar track

# Comportamiento
BEHAVIOR_MODEL = "models/behavior_classifier.pth"
BEHAVIOR_SEQUENCE_LENGTH = 30  # frames para análisis

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "data/logs/system.log"
EVENT_LOG = "data/logs/events.log"
```

## 🧪 Fases de Desarrollo

### ✅ Fase 1: Conexión Multi-Cámara (EN PROGRESO)
**Objetivo:** Conectar 2+ cámaras y mostrar streams sincronizados

**Tareas:**
- [x] Implementar CameraManager básico
- [x] Implementar SyncEngine
- [x] Visualizar mosaico de cámaras
- [x] Descubrir URL RTSP correcta de cámara real
- [x] Implementar solución FFmpeg para macOS
- [ ] Integrar FFmpegCamera en CameraManager
- [ ] Probar con stream en vivo

**Entregables:**
- Sistema capaz de mostrar múltiples streams en tiempo real
- Sincronización básica por timestamps
- Solución compatible con macOS usando FFmpeg

**Notas de Implementación (2025-11-08):**
- ✅ URL RTSP verificada: `rtsp://admin:Sb123456@192.168.0.20:554/Preview_01_main`
- ✅ Cámara: Reolink E1 Pro (E Series E330)
- ⚠️  OpenCV tiene problemas con RTSP en macOS → Solución: FFmpeg
- 📁 Ver `README_CAMARA.md` y `SOLUCION_CAMARA.md` para detalles

### 📋 Fase 2: Detección y Tracking Individual
**Objetivo:** Detectar y trackear hurones en cada cámara independientemente

**Tareas:**
- [ ] Integrar YOLOv8 para detección
- [ ] Implementar DeepSORT para tracking local
- [ ] Visualizar bounding boxes con IDs locales

**Entregables:**
- Detección confiable de hurones
- Tracking consistente dentro de cada cámara

### 📋 Fase 3: Re-Identificación Multi-Cámara
**Objetivo:** Mantener ID único cuando hurón cambia de cámara

**Tareas:**
- [ ] Entrenar/adaptar modelo ReID
- [ ] Implementar matching entre cámaras
- [ ] Sistema de IDs globales

**Entregables:**
- IDs únicos mantenidos entre cámaras
- Database de features por individuo

### 📋 Fase 4: Fusión y Eliminación de Duplicados
**Objetivo:** Combinar información de múltiples vistas

**Tareas:**
- [ ] Implementar algoritmo de fusión
- [ ] Eliminación de detecciones duplicadas
- [ ] Calibración de cámaras (opcional)
- [ ] Cálculo de posición 3D (opcional)

**Entregables:**
- Vista unificada sin duplicados
- Posiciones 3D aproximadas

### 📋 Fase 5: Reconocimiento de Comportamientos
**Objetivo:** Clasificar actividades de hurones

**Tareas:**
- [ ] Recolectar dataset de comportamientos
- [ ] Entrenar modelo CNN+LSTM
- [ ] Implementar BehaviorClassifier
- [ ] Sistema de detección de interacciones

**Entregables:**
- Clasificación en tiempo real de 5+ comportamientos
- Detección de interacciones sociales

### 📋 Fase 6: Dashboard en Tiempo Real
**Objetivo:** Interfaz web para monitoreo

**Tareas:**
- [ ] Backend API con FastAPI
- [ ] Frontend con React
- [ ] WebSocket para streaming en vivo
- [ ] Visualización de estadísticas
- [ ] Sistema de alertas

**Entregables:**
- Dashboard web funcional
- API REST documentada
- Sistema de notificaciones

## 📊 Métricas y Evaluación

### Rendimiento del Sistema
- **FPS total:** ≥ 20 fps con 2 cámaras, ≥ 10 fps con 4 cámaras
- **Latencia de detección:** < 100ms por frame
- **Uso de GPU:** < 80% en inferencia continua

### Precisión de Detección
- **mAP (mean Average Precision):** > 0.85
- **Recall:** > 0.90 (para no perder individuos)
- **False Positives:** < 5% de detecciones

### Tracking
- **MOTA (Multiple Object Tracking Accuracy):** > 0.80
- **ID Switches:** < 10 por hora
- **Track Fragmentation:** < 15%

### Comportamiento
- **Accuracy de clasificación:** > 0.85 por clase
- **Confusión entre clases:** < 10%

## 🔐 Consideraciones de Seguridad

- Credenciales RTSP almacenadas en variables de entorno
- Encriptación de comunicación con cámaras (si soportado)
- Logs sin información sensible
- Control de acceso al dashboard

## 🚀 Despliegue

### Requisitos del Sistema
- **OS:** Linux (Ubuntu 20.04+) o macOS
- **Python:** 3.9+
- **GPU:** NVIDIA con CUDA 11.7+ (recomendado)
- **RAM:** 16GB mínimo, 32GB recomendado
- **Storage:** 100GB+ para logs y modelos

### Instalación
```bash
# Clonar repositorio
git clone <repo-url>
cd ferret_monitoring

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar cámaras
cp config.example.py config.py
# Editar config.py con URLs de cámaras

# Ejecutar
python main.py
```

## 📚 Referencias Técnicas

### Papers
- **YOLOv8:** Ultralytics YOLOv8 Documentation
- **DeepSORT:** "Simple Online and Realtime Tracking with a Deep Association Metric"
- **ReID:** "Bag of Tricks and A Strong Baseline for Deep Person Re-identification"
- **Action Recognition:** "Temporal Segment Networks for Action Recognition in Videos"

### Librerías Clave
- `opencv-python`: Procesamiento de video
- `torch`: Deep learning framework
- `ultralytics`: YOLOv8
- `deep-sort-realtime`: Tracking
- `torchreid`: Re-identificación
- `filterpy`: Kalman filters
- `fastapi`: API web
- `numpy`, `scipy`: Operaciones numéricas

## 🔄 Mantenimiento y Actualización

### Reentrenamiento Periódico
- **Frecuencia:** Mensual o cuando accuracy < 0.80
- **Datos nuevos:** Clips capturados con etiquetas validadas
- **Estrategia:** Fine-tuning con learning rate bajo

### Monitoreo
- Logs de errores revisados semanalmente
- Métricas de rendimiento monitoreadas en tiempo real
- Alertas automáticas si FPS < umbral

## 📞 Soporte y Contacto

Para preguntas o reportar issues:
- Documentación adicional: `/docs`
- Issues: GitHub Issues
- Email: [tu-email@ejemplo.com]

---

**Última actualización:** {{ FECHA }}  
**Versión del documento:** 1.0  
**Estado del proyecto:** Fase 1 - Desarrollo Inicial



