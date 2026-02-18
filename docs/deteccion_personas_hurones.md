# Detección de Personas y Hurones - Historial Compartido

## 📋 Resumen de Implementación

Se ha modificado el sistema para detectar y registrar **TANTO hurones COMO personas** en el historial de individuos, sin confundir ambos tipos.

## 🔧 Cambios Implementados

### 1. **Config (`config.py`)**
```python
# Clases a detectar de COCO dataset
DETECTION_CLASSES = ["person", "cat", "dog"]

# Mapeo de clases a tipos de entidad
CLASS_TO_ENTITY_TYPE = {
    "person": "person",     # Personas
    "cat": "ferret",        # Gatos → consideramos como hurones
    "dog": "ferret"         # Perros → consideramos como hurones  
}
```

**Nota**: YOLOv8 pre-entrenado no detecta "ferret" directamente. Usamos "cat" y "dog" como proxy hasta tener un modelo custom entrenado.

### 2. **Detector (`ai/detector.py`)**
- ✅ Agregado campo `entity_type` al dataclass `Detection`
- ✅ Filtro de clases en `detect()`: solo person/cat/dog
- ✅ Asignación automática de entity_type según mapeo

### 3. **Tracker (`ai/tracker.py`)**
- ✅ Agregado campo `entity_type` al dataclass `TrackedObject`
- ⚠️ **PENDIENTE**: Pasar entity_type desde Detection a TrackedObject

### 4. **Base de Datos (`utils/behavior_log.py`)**
- ✅ Agregada columna `entity_type` a tabla `behaviors`
- ✅ Actualizado `BehaviorEntry` dataclass
- ✅ Modificado `add_behavior()` para aceptar `entity_type`
- ✅ Retrocompatibilidad con bases de datos antiguas

### 5. **Main (`main.py`)**
- ⚠️ **PENDIENTE**: Actualizar llamada a `add_behavior()` para incluir `entity_type`

### 6. **Frontend**
- ⚠️ **PENDIENTE**: Actualizar modelos TypeScript
- ⚠️ **PENDIENTE**: Modificar tabla de historial para mostrar tipo
- ⚠️ **PENDIENTE**: Agregar filtro por tipo de entidad

## 📊 Esquema de Base de Datos

```sql
CREATE TABLE behaviors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    individual_id TEXT NOT NULL,
    entity_type TEXT NOT NULL DEFAULT 'ferret',  -- 'ferret' o 'person'
    behavior TEXT NOT NULL,
    confidence REAL NOT NULL,
    timestamp TEXT NOT NULL,
    duration REAL,
    camera_id INTEGER,
    metadata TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
```

## 🎯 Comportamiento Esperado

### Detección
- **Personas**: Detectadas como clase "person" → `entity_type="person"`
- **Hurones**: Detectados como "cat" o "dog" → `entity_type="ferret"`

### Tracking
- Cada individuo (persona o hurón) recibe un ID único: `F0`, `F1`, `P0`, `P1`
  - `F` = Ferret (hurón o animal pequeño)
  - `P` = Person (persona)

### Historial
```json
{
  "individualId": "P0",
  "entityType": "person",
  "behavior": "walking",
  "confidence": 0.92,
  "timestamp": "2025-11-10T03:00:00Z",
  "cameraId": 0
}
```

```json
{
  "individualId": "F0",
  "entityType": "ferret",
  "behavior": "eating",
  "confidence": 0.95,
  "timestamp": "2025-11-10T03:01:00Z",
  "cameraId": 0
}
```

## 🚀 Pasos Finales (TODO)

1. ✅ Modificar tracker para extraer `entity_type` de detecciones
2. ✅ Actualizar `main.py` para pasar `entity_type` a `add_behavior()`
3. ✅ Arrancar sistema principal de análisis
4. ⚠️ Actualizar frontend para mostrar entity_type

## 🎨 Visualización Propuesta (Frontend)

### Tabla de Historial
| ID | Tipo | Comportamiento | Confianza | Tiempo | Cámara |
|----|------|----------------|-----------|--------|--------|
| P0 | 👤 Persona | Caminando | 92% | 03:00:00 | Cámara 1 |
| F0 | 🦦 Hurón | Comiendo | 95% | 03:01:00 | Cámara 1 |
| P1 | 👤 Persona | Parado | 88% | 03:02:00 | Cámara 2 |
| F0 | 🦦 Hurón | Durmiendo | 93% | 03:05:00 | Cámara 1 |

### Filtros
- ☐ Todos
- ☐ Solo Hurones
- ☐ Solo Personas

## 📝 Notas Importantes

1. **Modelo YOLO Actual**: `yolov8n.pt` (COCO dataset)
   - ✅ Detecta personas perfectamente
   - ⚠️ NO detecta "ferret" directamente
   - 🔧 Usamos "cat" y "dog" como proxy temporal
   - 🎯 **Para producción**: Entrenar modelo custom con dataset de hurones

2. **IDs Únicos**:
   - Personas y hurones tienen prefijos diferentes (P vs F)
   - El tracker mantiene IDs globales across cámaras
   - Re-ID diferencia entre individuos del mismo tipo

3. **Comportamientos**:
   - Hurones: eating, sleeping, running, fighting, defecating
   - Personas: walking, standing, sitting (futura expansión)

## 🔗 Archivos Modificados

- `config.py`: Clases a detectar y mapeo
- `ai/detector.py`: Filtro de clases y entity_type
- `ai/tracker.py`: Agregado entity_type a TrackedObject
- `utils/behavior_log.py`: Campo entity_type en BD
- ⏳ `main.py`: Pendiente actualización
- ⏳ Frontend: Pendiente actualización

## ✅ Próximos Pasos Inmediatos

1. Completar modificación del tracker
2. Arrancar sistema para probar detección
3. Verificar que personas aparezcan en el historial
4. Actualizar frontend para visualizar correctamente

