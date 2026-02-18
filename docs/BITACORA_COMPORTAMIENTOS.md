# Sistema de Bitácora de Comportamientos

## 🎯 Descripción General

El sistema de bitácora de comportamientos registra de forma persistente todos los comportamientos detectados de los hurones, asociados a cada individuo con información detallada incluyendo:
- **ID del individuo**
- **Tipo de comportamiento**
- **Confianza de la detección**
- **Timestamp preciso**
- **Cámara donde se detectó**
- **Duración (opcional)**
- **Metadatos adicionales**

## 🗂️ Comportamientos Detectados

El sistema puede identificar y registrar los siguientes comportamientos:

| Comportamiento (Inglés) | Español | Descripción |
|-------------------------|---------|-------------|
| `eating` | Comiendo | El hurón está comiendo |
| `sleeping` | Durmiendo | El hurón está durmiendo o descansando |
| `running` | Corriendo | El hurón está en movimiento rápido |
| `fighting` | Peleando | Interacción agresiva entre hurones |
| `defecating` | Haciendo necesidades | El hurón está defecando u orinando |
| `walking` | Caminando | Movimiento tranquilo exploratorio |
| `idle` | Inactivo | Parado sin actividad específica |

## 📦 Componentes del Sistema

### 1. **BehaviorLog** (`utils/behavior_log.py`)

Módulo principal que gestiona la base de datos SQLite con todos los comportamientos.

```python
from utils import BehaviorLog

# Crear instancia
log = BehaviorLog("data/behavior_log.db")

# Agregar comportamiento
log.add_behavior(
    individual_id="F0",
    behavior="eating",
    confidence=0.95,
    camera_id=0
)

# Consultar historial
entries = log.get_by_individual("F0", limit=10)

# Estadísticas
stats = log.get_statistics("F0")
```

#### Métodos Principales:

- `add_behavior()` - Registrar nuevo comportamiento
- `get_by_individual()` - Obtener historial de un individuo
- `get_by_behavior()` - Filtrar por tipo de comportamiento
- `get_by_time_range()` - Consultar rango temporal
- `get_recent()` - Comportamientos recientes
- `get_statistics()` - Estadísticas agregadas
- `get_all_individuals()` - Lista de todos los individuos
- `export_to_json()` - Exportar bitácora a JSON

### 2. **Integración en Main** (`main.py`)

El sistema principal detecta cambios de comportamiento y registra automáticamente en la bitácora:

```python
# Cuando se detecta un nuevo comportamiento
self.behavior_log.add_behavior(
    individual_id=obj.global_id,
    behavior=new_behavior,
    confidence=prediction.confidence,
    timestamp=prediction.timestamp,
    camera_id=obj.camera_id,
    metadata={"probabilities": prediction.probabilities}
)
```

### 3. **API REST Endpoints** (`api/main.py`)

#### Endpoints Disponibles:

##### 📋 **GET `/api/behaviors/individuals`**
Obtener lista de todos los individuos en la bitácora.

```bash
curl http://localhost:8000/api/behaviors/individuals
```

**Respuesta:**
```json
{
  "traceId": "behavior-individuals",
  "code": 200,
  "message": "Lista de individuos obtenida",
  "data": [
    {
      "individual_id": "F0",
      "total_behaviors": 150,
      "last_behavior": "eating",
      "last_seen": "2025-11-09T14:30:00"
    }
  ]
}
```

---

##### 📖 **GET `/api/behaviors/individual/{individual_id}`**
Obtener historial completo de un individuo.

**Parámetros:**
- `limit` (opcional, default=50): Número de resultados
- `offset` (opcional, default=0): Offset para paginación

```bash
curl "http://localhost:8000/api/behaviors/individual/F0?limit=20"
```

**Respuesta:**
```json
{
  "traceId": "behavior-history-F0",
  "code": 200,
  "message": "Historial de F0 obtenido",
  "data": {
    "individual_id": "F0",
    "total_count": 150,
    "page_size": 20,
    "offset": 0,
    "behaviors": [
      {
        "id": 1,
        "individual_id": "F0",
        "behavior": "eating",
        "behavior_es": "Comiendo",
        "confidence": 0.95,
        "timestamp": "2025-11-09T14:30:00",
        "duration": null,
        "camera_id": 0,
        "metadata": null
      }
    ]
  }
}
```

---

##### 📊 **GET `/api/behaviors/individual/{individual_id}/statistics`**
Obtener estadísticas agregadas de comportamiento.

**Parámetros:**
- `time_range_hours` (opcional): Filtrar últimas N horas

```bash
curl "http://localhost:8000/api/behaviors/individual/F0/statistics?time_range_hours=24"
```

**Respuesta:**
```json
{
  "traceId": "behavior-stats-F0",
  "code": 200,
  "message": "Estadísticas de F0 obtenidas",
  "data": {
    "individual_id": "F0",
    "total_behaviors": 150,
    "time_range_hours": 24,
    "behaviors": {
      "eating": {
        "count": 45,
        "percentage": 30.0,
        "avg_confidence": 0.92,
        "avg_duration": 15.5,
        "name_es": "Comiendo"
      },
      "sleeping": {
        "count": 60,
        "percentage": 40.0,
        "avg_confidence": 0.88,
        "avg_duration": 120.0,
        "name_es": "Durmiendo"
      }
    }
  }
}
```

---

##### 🕒 **GET `/api/behaviors/recent`**
Obtener comportamientos recientes.

**Parámetros:**
- `minutes` (opcional, default=60): Minutos hacia atrás
- `individual_id` (opcional): Filtrar por individuo

```bash
curl "http://localhost:8000/api/behaviors/recent?minutes=30&individual_id=F0"
```

---

##### 🔍 **GET `/api/behaviors/by-type/{behavior}`**
Filtrar por tipo de comportamiento.

**Parámetros:**
- `individual_id` (opcional): Filtrar por individuo
- `limit` (opcional, default=50): Número de resultados

```bash
curl "http://localhost:8000/api/behaviors/by-type/eating?limit=20"
```

---

##### 💾 **GET `/api/behaviors/export/{individual_id}`**
Exportar bitácora completa a JSON.

```bash
curl -O "http://localhost:8000/api/behaviors/export/F0"
# Descarga: bitacora_F0_20251109_143000.json
```

## 🗄️ Estructura de Base de Datos

### Tabla: `behaviors`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | INTEGER | ID único auto-incrementado |
| `individual_id` | TEXT | ID del hurón (ej: F0, F1) |
| `behavior` | TEXT | Nombre del comportamiento |
| `confidence` | REAL | Confianza (0.0 - 1.0) |
| `timestamp` | TEXT | ISO8601 timestamp |
| `duration` | REAL | Duración en segundos (opcional) |
| `camera_id` | INTEGER | ID de la cámara |
| `metadata` | TEXT | JSON con datos adicionales |
| `created_at` | TEXT | Timestamp de creación del registro |

### Índices:
- `idx_individual` - Por individual_id
- `idx_behavior` - Por behavior
- `idx_timestamp` - Por timestamp
- `idx_individual_timestamp` - Compuesto para consultas rápidas

## 📝 Ejemplos de Uso

### Python - Consultar Bitácora

```python
from utils import BehaviorLog

log = BehaviorLog()

# Últimos 10 comportamientos de F0
entries = log.get_by_individual("F0", limit=10)
for entry in entries:
    print(f"{entry.timestamp}: {entry.behavior} (conf={entry.confidence:.2f})")

# Estadísticas de las últimas 24 horas
stats = log.get_statistics("F0", time_range_hours=24)
print(f"Total comportamientos: {stats['total_behaviors']}")
for behavior, data in stats['behaviors'].items():
    print(f"  {behavior}: {data['count']} veces ({data['percentage']:.1f}%)")

# Comportamientos recientes (última hora)
recent = log.get_recent(minutes=60, individual_id="F0")
print(f"Comportamientos en última hora: {len(recent)}")
```

### JavaScript/TypeScript - Frontend

```typescript
// Servicio de API
async getBehaviorHistory(individualId: string, limit = 50) {
  const response = await fetch(
    `${API_URL}/api/behaviors/individual/${individualId}?limit=${limit}`
  );
  return await response.json();
}

async getBehaviorStats(individualId: string, hours?: number) {
  let url = `${API_URL}/api/behaviors/individual/${individualId}/statistics`;
  if (hours) url += `?time_range_hours=${hours}`;
  
  const response = await fetch(url);
  return await response.json();
}

// Uso
const stats = await getBehaviorStats('F0', 24);
console.log(`F0 ha comido ${stats.data.behaviors.eating.count} veces hoy`);
```

### cURL - Consultas desde Terminal

```bash
# Ver individuos registrados
curl http://localhost:8000/api/behaviors/individuals

# Últimos 20 comportamientos de F0
curl "http://localhost:8000/api/behaviors/individual/F0?limit=20"

# Estadísticas de últimas 24 horas
curl "http://localhost:8000/api/behaviors/individual/F0/statistics?time_range_hours=24"

# Comportamientos recientes (última hora)
curl "http://localhost:8000/api/behaviors/recent?minutes=60"

# Solo comportamientos de "comer"
curl "http://localhost:8000/api/behaviors/by-type/eating?individual_id=F0"

# Exportar bitácora completa
curl -O "http://localhost:8000/api/behaviors/export/F0"
```

## 🔧 Configuración

### Ubicación de la Base de Datos
Por defecto: `data/behavior_log.db`

Configurar en `config.py`:
```python
BEHAVIOR_LOG_DB = "data/behavior_log.db"
```

### Comportamientos Personalizados

Modificar en `config.py`:
```python
BEHAVIOR_CLASSES: List[str] = [
    "eating",
    "sleeping",
    "running",
    "fighting",
    "defecating",
    "walking",
    "idle",
    # Agregar más comportamientos aquí
]

BEHAVIOR_NAMES_ES: Dict[str, str] = {
    "eating": "Comiendo",
    # Agregar traducciones aquí
}
```

## 🚀 Inicio Rápido

### 1. Iniciar Sistema Principal
```bash
# El sistema automáticamente registra comportamientos en la bitácora
python main.py
```

### 2. Iniciar API
```bash
# En otra terminal
python api/main.py
# API disponible en http://localhost:8000
```

### 3. Consultar Bitácora
```bash
# Ver documentación interactiva
open http://localhost:8000/docs

# O consultar directamente
curl http://localhost:8000/api/behaviors/individuals
```

## 📈 Análisis y Visualización

### Generar Reporte Diario
```python
from utils import BehaviorLog
from datetime import datetime, timedelta

log = BehaviorLog()

# Obtener estadísticas de hoy
stats = log.get_statistics("F0", time_range_hours=24)

print(f"=== Reporte Diario de F0 ===")
print(f"Fecha: {datetime.now().strftime('%Y-%m-%d')}")
print(f"\nComportamientos registrados: {stats['total_behaviors']}")
print("\nDistribución:")
for behavior, data in stats['behaviors'].items():
    print(f"  • {data['name_es']}: {data['count']} veces ({data['percentage']:.1f}%)")
    print(f"    Duración promedio: {data['avg_duration']:.1f}s")
```

### Detectar Anomalías
```python
# Buscar periodos sin actividad (posible problema)
recent = log.get_recent(minutes=120, individual_id="F0")
if len(recent) == 0:
    print("⚠️ ALERTA: F0 sin actividad en últimas 2 horas")

# Verificar comportamientos inusuales
eating_count = log.get_by_behavior("eating", individual_id="F0", limit=100)
if len(eating_count) < 2:  # Menos de 2 veces al día
    print("⚠️ ALERTA: F0 ha comido poco hoy")
```

## 🛠️ Mantenimiento

### Limpiar Datos Antiguos
```python
from utils import BehaviorLog

log = BehaviorLog()

# Eliminar registros de más de 90 días
deleted = log.delete_old_entries(days=90)
print(f"Eliminados {deleted} registros antiguos")
```

### Backup de Base de Datos
```bash
# Copiar archivo de base de datos
cp data/behavior_log.db backups/behavior_log_$(date +%Y%m%d).db

# O exportar a JSON
curl -O "http://localhost:8000/api/behaviors/export/F0"
```

## 📊 Formato de Respuestas API

Todas las respuestas de la API siguen el formato estándar:

```json
{
  "traceId": "unique-request-id",
  "code": 200,
  "message": "Descripción del resultado",
  "data": {
    // Datos específicos del endpoint
  }
}
```

Códigos de estado:
- `200` - Éxito
- `404` - Recurso no encontrado
- `500` - Error interno del servidor

## 🔍 Troubleshooting

### La bitácora está vacía
- Verificar que el sistema principal esté corriendo (`python main.py`)
- Confirmar que el clasificador de comportamientos esté activo
- Revisar logs en `data/logs/system.log`

### Error al consultar API
- Verificar que la API esté corriendo (`python api/main.py`)
- Confirmar puerto correcto (default: 8000)
- Revisar CORS si consultas desde navegador

### Base de datos corrupta
```bash
# Verificar integridad
sqlite3 data/behavior_log.db "PRAGMA integrity_check;"

# Si hay problemas, restaurar desde backup
cp backups/behavior_log_YYYYMMDD.db data/behavior_log.db
```

## 📚 Referencias

- **Código fuente:** `utils/behavior_log.py`
- **API:** `api/main.py` (sección ENDPOINTS DE BITÁCORA)
- **Integración:** `main.py` (método `process_synced_frames`)
- **Configuración:** `config.py`

---

**Última actualización:** 2025-11-09  
**Versión:** 1.0.0

