# 📊 Datos Dummy - Sistema de Monitoreo

## 🎭 Servicio Mock Implementado

Se ha creado un servicio completo de datos simulados (`MockDataService`) que genera datos realistas en tiempo real para demostrar el funcionamiento del dashboard sin necesidad de tener cámaras reales o el backend corriendo.

---

## 📹 Cámaras Simuladas

### Configuración de Cámaras

**Total:** 3 cámaras IP simuladas

| ID | Nombre | Estado | FPS | Resolución |
|----|--------|--------|-----|------------|
| 0 | Cámara Superior | ✅ Conectada | 29.5-30.5 | 1920x1080 |
| 1 | Cámara Inferior | ✅ Conectada | 29.5-30.5 | 1920x1080 |
| 2 | Cámara Lateral | ⚠️ Intermitente | 0-30 | 1920x1080 |

### Características de las Cámaras:
- **FPS dinámico:** Varía ligeramente para simular condiciones reales
- **Estado variable:** La cámara 3 se desconecta ocasionalmente
- **Placeholders visuales:** Imágenes con colores distintivos
- **Actualización:** Cada 2 segundos

### Imágenes Placeholder:
```
Cámara Superior (0): Fondo púrpura (#667eea)
Cámara Inferior (1): Fondo morado (#764ba2)
Cámara Lateral (2):  Fondo azul (#2196f3)
```

---

## 🐾 Individuos Tracked

### Individuos Simulados

**Total:** 5 hurones con IDs únicos

#### **F0 - "El Juguetón"**
```json
{
  "id": "F0",
  "confidence": 0.92,
  "cameras": [0, 1],
  "currentBehavior": "playing",
  "behaviorConfidence": 0.87,
  "position": { "x": 150, "y": 200, "z": 0 },
  "trajectory": [ /* 20 puntos */ ],
  "firstSeen": "hace 5m 23s",
  "lastSeen": "hace 1s",
  "totalTime": 323,
  "status": "● ACTIVO"
}
```
**Características:**
- Muy activo, visible en múltiples cámaras
- Alta confianza de detección
- Comportamiento: Jugando constantemente
- Trayectoria: Patrón circular

---

#### **F1 - "El Dormilón"**
```json
{
  "id": "F1",
  "confidence": 0.78,
  "cameras": [0],
  "currentBehavior": "sleeping",
  "behaviorConfidence": 0.94,
  "position": { "x": 450, "y": 300, "z": 0 },
  "trajectory": [ /* 15 puntos */ ],
  "firstSeen": "hace 1h 12m",
  "lastSeen": "hace 3min",
  "totalTime": 4320,
  "status": "○ INACTIVO"
}
```
**Características:**
- Durmiendo (alta confianza)
- Visible solo en cámara superior
- Movimiento mínimo
- No visto recientemente (inactivo)

---

#### **F2 - "El Explorador"**
```json
{
  "id": "F2",
  "confidence": 0.85,
  "cameras": [1, 2],
  "currentBehavior": "walking",
  "behaviorConfidence": 0.71,
  "position": { "x": 320, "y": 450, "z": 0 },
  "trajectory": [ /* 30 puntos */ ],
  "firstSeen": "hace 45s",
  "lastSeen": "hace 1s",
  "totalTime": 45,
  "status": "● ACTIVO"
}
```
**Características:**
- Caminando entre cámaras
- Recién detectado
- Trayectoria larga (explorando)
- Alta movilidad

---

#### **F3 - "El Social"**
```json
{
  "id": "F3",
  "confidence": 0.89,
  "cameras": [0, 1],
  "currentBehavior": "interacting",
  "behaviorConfidence": 0.82,
  "position": { "x": 280, "y": 350, "z": 0 },
  "trajectory": [ /* 25 puntos */ ],
  "firstSeen": "hace 2m 15s",
  "lastSeen": "hace 2s",
  "totalTime": 135,
  "status": "● ACTIVO"
}
```
**Características:**
- Interactuando con otro hurón
- Visible en cámaras múltiples
- Comportamiento social
- Posición cercana a F0

---

#### **F4 - "El Hambriento"**
```json
{
  "id": "F4",
  "confidence": 0.65,
  "cameras": [2],
  "currentBehavior": "eating",
  "behaviorConfidence": 0.76,
  "position": { "x": 500, "y": 250, "z": 0 },
  "trajectory": [ /* 10 puntos */ ],
  "firstSeen": "hace 8m 30s",
  "lastSeen": "hace 5min",
  "totalTime": 510,
  "status": "○ INACTIVO"
}
```
**Características:**
- Comiendo (confianza media)
- Solo en cámara lateral
- No visto recientemente
- Movimiento limitado

---

## 🎯 Comportamientos Simulados

### Tipos de Comportamiento

| Comportamiento | Color | Emoji | Frecuencia | Confianza Promedio |
|----------------|-------|-------|------------|-------------------|
| **Comiendo** | 🟢 Verde | 🍽️ | 10% | 70-85% |
| **Durmiendo** | 🔵 Azul | 😴 | 20% | 85-95% |
| **Jugando** | 🟠 Naranja | 🎮 | 25% | 75-90% |
| **Caminando** | 🟣 Púrpura | 🚶 | 20% | 65-80% |
| **Interactuando** | 🔴 Rosa | 🤝 | 15% | 75-85% |
| **Explorando** | 🔷 Cian | 🔍 | 8% | 70-85% |
| **Inactivo** | ⚫ Gris | 🧘 | 2% | 60-75% |

### Cambios de Comportamiento

Los comportamientos cambian automáticamente cada ~20 segundos para simular actividad real:
- **Probabilidad de cambio:** 15% cada ciclo
- **Confianza variable:** Se actualiza con cada cambio
- **Transiciones realistas:** De caminando → jugando, de explorando → caminando, etc.

---

## 📍 Trayectorias y Movimiento

### Generación de Trayectorias

Cada individuo tiene una trayectoria única generada con:
- **Patrón:** Movimiento circular/elíptico
- **Puntos:** 10-30 puntos históricos
- **Actualización:** Cada 3 segundos
- **Límites:** Dentro del área visible (50-600 x, 50-450 y)

### Formato de Trayectoria:
```json
[
  {
    "x": 150.5,
    "y": 200.3,
    "timestamp": "2025-10-28T12:45:30.123Z",
    "cameraId": 0
  },
  // ... más puntos
]
```

### Características del Movimiento:
- **Velocidad variable:** ±20 píxeles por ciclo
- **Cambio de cámara:** 10% de probabilidad por ciclo
- **Persistencia:** Últimos 50 puntos guardados
- **Suavizado:** Movimiento continuo sin saltos bruscos

---

## 📊 Métricas del Sistema (Simuladas)

### Métricas en Tiempo Real

```javascript
{
  fps: 28-32,                    // Varía ligeramente
  totalFrames: incrementa cada ciclo,
  activeCameras: 2-3,            // Depende de estado
  totalCameras: 3,
  activeIndividuals: 2-4,        // Vistos últimos 10s
  totalDetections: 3-10,
  uptime: tiempo desde inicio,
  cpuUsage: 40-60%,             // Simulado
  memoryUsage: 60-75%,          // Simulado
  gpuUsage: 70-85%              // Simulado
}
```

**Actualización:** Cada 1 segundo

---

## 🔄 Simulación en Tiempo Real

### Ciclo de Actualización

El servicio mock ejecuta un ciclo cada **3 segundos** que:

1. ✅ Incrementa contador de frames (+90)
2. ✅ Actualiza timestamps de individuos
3. ✅ Cambia comportamientos aleatoriamente (15%)
4. ✅ Mueve individuos (+/-20px)
5. ✅ Agrega puntos a trayectorias
6. ✅ Cambia cámaras visibles (10%)
7. ✅ Actualiza confianza de detección
8. ✅ Marca individuos como activos/inactivos

### Estado Activo/Inactivo

**Activo (●):** Visto en últimos 10 segundos
**Inactivo (○):** No visto >10 segundos

---

## 🎨 Configuración Visual

### Colores por Comportamiento

```scss
eating:       #4CAF50  // Verde
sleeping:     #2196F3  // Azul
playing:      #FF9800  // Naranja
walking:      #9C27B0  // Púrpura
interacting:  #E91E63  // Rosa
exploring:    #00BCD4  // Cian
idle:         #9E9E9E  // Gris
```

### Placeholders de Cámaras

Cada cámara tiene un placeholder con:
- **Tamaño:** 640x480
- **Color de fondo:** Único por cámara
- **Texto:** Nombre de la cámara
- **Emoji:** 🎥 para identificación visual

---

## 🔧 Activar/Desactivar Datos Mock

### En el código

**Archivo:** `frontend/src/app/core/services/api.service.ts`

```typescript
export class ApiService {
  private readonly useMockData = true; // ← Cambiar aquí
  
  // true  = Usar datos simulados (no requiere backend)
  // false = Usar API real (requiere backend corriendo)
}
```

### Ventajas de los Datos Mock:

✅ **No requiere backend** - Frontend funciona standalone
✅ **Datos realistas** - Simula comportamiento real del sistema
✅ **Actualización en tiempo real** - Los datos cambian dinámicamente
✅ **Fácil de modificar** - Ajusta valores en `mock-data.service.ts`
✅ **Perfect para demos** - Muestra todas las features sin hardware

---

## 📝 Personalizar Datos Dummy

### Agregar más individuos:

Editar `mock-data.service.ts` en el método `initializeMockData()`:

```typescript
{
  id: 'F5',
  confidence: 0.88,
  cameras: [0, 2],
  currentBehavior: 'exploring',
  behaviorConfidence: 0.79,
  // ... más propiedades
}
```

### Cambiar comportamientos:

Editar el array en `startSimulation()`:

```typescript
const behaviors = [
  'eating', 'sleeping', 'playing', 
  'walking', 'interacting', 
  'exploring', 'idle',
  'custom_behavior'  // ← Agregar nuevo
];
```

### Ajustar velocidad de actualización:

```typescript
interval(3000).subscribe(() => {  // ← Cambiar milisegundos
  // Lógica de actualización
});
```

---

## 🎯 Casos de Uso

### 1. Demostración sin Hardware
✅ Mostrar el dashboard funcionando sin cámaras reales
✅ Presentar el proyecto a stakeholders
✅ Documentación y screenshots

### 2. Desarrollo Frontend
✅ Trabajar en UI sin depender del backend
✅ Probar componentes aisladamente
✅ Debugging de visualización

### 3. Testing
✅ Casos de prueba con datos controlados
✅ Verificar comportamiento de la UI
✅ Testing de rendimiento

---

## 📊 Estadísticas de Datos Mock

```
Total Individuos:        5
Comportamientos únicos:  7
Puntos de trayectoria:   ~100 (total)
Cámaras simuladas:       3
Actualización:           Cada 3 segundos
FPS simulado:           ~30
Datos generados/min:    ~20 actualizaciones
```

---

## 🚀 Estado Actual

✅ **Servicio Mock:** Completamente implementado
✅ **Datos de cámaras:** 3 cámaras con placeholders
✅ **Datos de individuos:** 5 hurones con movimiento
✅ **Comportamientos:** 7 tipos diferentes
✅ **Trayectorias:** Generación automática
✅ **Métricas:** Sistema completo simulado
✅ **Actualización:** Tiempo real (cada 3s)
✅ **Integración:** Conectado a todos los componentes

---

**El dashboard ahora funciona completamente con datos dummy realistas! 🎉**

Para ver en acción:
```bash
cd frontend
ng serve
```

Abre http://localhost:4200 y verás:
- 3 cámaras con imágenes placeholder
- 5 individuos moviéndose y cambiando comportamientos
- Datos actualizándose en tiempo real
- Tabla interactiva completamente funcional

**¡Todo sin necesidad de backend o cámaras reales!** 🚀





