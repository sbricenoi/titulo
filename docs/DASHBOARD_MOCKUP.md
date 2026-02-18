# 🎨 Dashboard - Mockup Visual

## Vista Completa del Dashboard

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  🐾 FERRET MONITORING SYSTEM                              👤 Admin    🔔 3    ⚙️      │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│  ┌───────────────────────────────────────────────────────────────────────────────────┐│
│  │  📹 CÁMARAS EN VIVO                                             🔄 Actualizar     ││
│  ├───────────────────────────────────────────────────────────────────────────────────┤│
│  │                                                                                    ││
│  │  ┌───────────────────────┬───────────────────────┬───────────────────────┐       ││
│  │  │ 📹 Cámara Superior    │ 📹 Cámara Inferior    │ 📹 Cámara Lateral     │       ││
│  │  │ ✅ Conectada          │ ✅ Conectada          │ ⚠️ Conectando...     │       ││
│  │  │                       │                       │                       │       ││
│  │  │  ┌─────────────────┐  │  ┌─────────────────┐  │  ┌─────────────────┐  │       ││
│  │  │  │                 │  │  │                 │  │  │                 │  │       ││
│  │  │  │  [LIVE STREAM]  │  │  │  [LIVE STREAM]  │  │  │   🔄 Syncing    │  │       ││
│  │  │  │                 │  │  │                 │  │  │                 │  │       ││
│  │  │  │  F0 ▶           │  │  │        ◀ F1     │  │  │                 │  │       ││
│  │  │  │                 │  │  │                 │  │  │                 │  │       ││
│  │  │  └─────────────────┘  │  └─────────────────┘  │  └─────────────────┘  │       ││
│  │  │                       │                       │                       │       ││
│  │  │  🎯 30.2 FPS         │  🎯 29.8 FPS         │  🎯 0.0 FPS          │       ││
│  │  │  📐 1920x1080        │  📐 1920x1080        │  📐 1920x1080        │       ││
│  │  │                       │                       │                       │       ││
│  │  │  [Ver Completo]       │  [Ver Completo]       │  [Ver Completo]       │       ││
│  │  └───────────────────────┴───────────────────────┴───────────────────────┘       ││
│  │                                                                                    ││
│  │  📊 3 cámaras  |  ✅ 2 activas  |  ❌ 1 inactiva                                  ││
│  └───────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                         │
│  ┌───────────────────────────────────────────────────────────────────────────────────┐│
│  │  📊 REPORTE DE INDIVIDUOS                                                         ││
│  ├───────────────────────────────────────────────────────────────────────────────────┤│
│  │                                                                                    ││
│  │  ┌─────────────────┬─────────────────┬─────────────────┐                         ││
│  │  │  🐾 Total       │  ✅ Activos     │  📹 Detecciones │                         ││
│  │  │      5          │      3          │      12         │                         ││
│  │  │  Individuos     │  Ahora          │  Total          │                         ││
│  │  └─────────────────┴─────────────────┴─────────────────┘                         ││
│  │                                                                                    ││
│  │  🔍 Buscar: [_______________]                             📥 Exportar CSV         ││
│  │                                                                                    ││
│  │  ┌────┬────────┬───────────────┬───────────┬───────────┬────────┬───────┬──────┐ ││
│  │  │ ID │ Estado │ Comportamiento│  Cámaras  │ Confianza │ Tiempo │ Visto │ Acc. │ ││
│  │  ├────┼────────┼───────────────┼───────────┼───────────┼────────┼───────┼──────┤ ││
│  │  │ F0 │● Activo│ 🎮 Jugando    │ 🎥 Cám 1  │███████ 92%│ 5m 23s │ 1 seg │ 👁 📍│ ││
│  │  │    │        │    87%        │ 🎥 Cám 2  │           │        │       │      │ ││
│  │  ├────┼────────┼───────────────┼───────────┼───────────┼────────┼───────┼──────┤ ││
│  │  │ F1 │○ Inact.│ 😴 Durmiendo  │ 🎥 Cám 1  │██████░ 78%│ 1h 12m │ 3 min │ 👁 📍│ ││
│  │  │    │        │    94%        │           │           │        │       │      │ ││
│  │  ├────┼────────┼───────────────┼───────────┼───────────┼────────┼───────┼──────┤ ││
│  │  │ F2 │● Activo│ 🚶 Caminando  │ 🎥 Cám 2  │███████ 85%│   45s  │ 1 seg │ 👁 📍│ ││
│  │  │    │        │    71%        │ 🎥 Cám 3  │           │        │       │      │ ││
│  │  ├────┼────────┼───────────────┼───────────┼───────────┼────────┼───────┼──────┤ ││
│  │  │ F3 │● Activo│ 🤝 Interactuand│ 🎥 Cám 1  │████████89%│ 2m 15s │ 2 seg │ 👁 📍│ ││
│  │  │    │        │    82%        │ 🎥 Cám 2  │           │        │       │      │ ││
│  │  ├────┼────────┼───────────────┼───────────┼───────────┼────────┼───────┼──────┤ ││
│  │  │ F4 │○ Inact.│ 🍽️ Comiendo   │ 🎥 Cám 3  │█████░░ 65%│ 8m 30s │ 5 min │ 👁 📍│ ││
│  │  │    │        │    76%        │           │           │        │       │      │ ││
│  │  └────┴────────┴───────────────┴───────────┴───────────┴────────┴───────┴──────┘ ││
│  │                                                                                    ││
│  │  Mostrando 5 de 5 individuos                        ◀ [1] 2 3 4 5 ▶              ││
│  └───────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                         │
│  ┌───────────────────────────────────────────────────────────────────────────────────┐│
│  │  📈 ESTADÍSTICAS DEL SISTEMA                                                      ││
│  ├───────────────────────────────────────────────────────────────────────────────────┤│
│  │                                                                                    ││
│  │  FPS: 28.5  |  Frames: 145,892  |  Uptime: 5h 23m  |  CPU: 45%  |  GPU: 78%     ││
│  │                                                                                    ││
│  └───────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                         │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎨 Detalles Visuales

### 📹 Tarjeta de Cámara (Individual)

```
┌─────────────────────────────────────┐
│ 📹 Cámara Superior                  │
│ ✅ Conectada                         │
│                                      │
│  ┌────────────────────────────────┐ │
│  │                                │ │
│  │                                │ │
│  │        [LIVE STREAM]           │ │
│  │                                │ │
│  │  🟢 F0   ────────▶   🟡 F1    │ │ <- Bounding boxes
│  │                                │ │
│  │                                │ │
│  └────────────────────────────────┘ │
│                                      │
│  🎯 30.2 FPS    📐 1920x1080        │
│                                      │
│  [🖥️ Ver Completo]  [⚙️ Config]    │
└─────────────────────────────────────┘
```

### 📊 Fila de Tabla de Individuos (Detallada)

```
┌──────────────────────────────────────────────────────────────────────┐
│  ID: F0                                                  🔵 EN VIVO  │
├──────────────────────────────────────────────────────────────────────┤
│  Estado:              ● ACTIVO (hace 1 segundo)                      │
│  Comportamiento:      🎮 Jugando (87% confianza)                     │
│  Cámaras:             🎥 Cámara 1  🎥 Cámara 2                       │
│  Confianza Global:    ████████░░ 92%                                 │
│  Tiempo Activo:       ⏱️ 5 minutos 23 segundos                       │
│  Primera Vez Visto:   12:45:32                                       │
│  Última Vez Visto:    hace 1 segundo                                 │
│  Total Detecciones:   342                                            │
│                                                                       │
│  Trayectoria:         Cám 1 → Cám 2 → Cám 1 → Cám 2 (actual)       │
│                                                                       │
│  [👁️ Ver Detalles]  [📍 Ver Trayectoria]  [📊 Estadísticas]        │
└──────────────────────────────────────────────────────────────────────┘
```

### 🎨 Chips de Comportamiento

```
┌────────────────────────────────────────────────────────────┐
│  Comportamientos Detectables:                             │
│                                                             │
│  🍽️  [  Comiendo  ]  Verde #4CAF50                        │
│  😴  [ Durmiendo ]  Azul #2196F3                           │
│  🎮  [  Jugando  ]  Naranja #FF9800                        │
│  🚶  [ Caminando ]  Púrpura #9C27B0                        │
│  🤝  [Interactuando] Rosa #E91E63                          │
│  🔍  [ Explorando ]  Cian #00BCD4                          │
│  🧘  [  Inactivo  ]  Gris #9E9E9E                          │
└────────────────────────────────────────────────────────────┘
```

### 📊 Barra de Confianza

```
Alta (≥ 80%):     ████████░░ 92%  (Verde)
Media (50-79%):   ██████░░░░ 65%  (Naranja)
Baja (< 50%):     ███░░░░░░░ 38%  (Rojo)
```

---

## 📱 Vista Responsiva

### 💻 Desktop (> 1280px)

```
┌───────────────┬───────────────┬───────────────┐
│   Cámara 1    │   Cámara 2    │   Cámara 3    │
│               │               │               │
└───────────────┴───────────────┴───────────────┘

┌────────────────────────────────────────────────┐
│              Tabla de Individuos                │
│  8 columnas visibles, todas las features       │
└────────────────────────────────────────────────┘
```

### 📱 Tablet (960px - 1280px)

```
┌─────────────────┬─────────────────┐
│    Cámara 1     │    Cámara 2     │
│                 │                 │
├─────────────────┴─────────────────┤
│            Cámara 3               │
│                                   │
└───────────────────────────────────┘

┌──────────────────────────────────┐
│       Tabla de Individuos        │
│  6 columnas, scroll horizontal   │
└──────────────────────────────────┘
```

### 📱 Mobile (< 960px)

```
┌─────────────────┐
│    Cámara 1     │
│                 │
├─────────────────┤
│    Cámara 2     │
│                 │
├─────────────────┤
│    Cámara 3     │
│                 │
└─────────────────┘

┌────────────────┐
│ Estadísticas   │
│ (Cards stack)  │
└────────────────┘

┌────────────────┐
│     Tabla      │
│  (Responsive)  │
│  Cards en vez  │
│  de filas      │
└────────────────┘
```

---

## 🎨 Tema de Colores

```
┌──────────────────────────────────────────────────────────┐
│  PALETA PRINCIPAL                                         │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  🟣 Primary     #667eea ████████                          │
│  🟪 Secondary   #764ba2 ████████                          │
│  🔵 Info        #2196F3 ████████                          │
│  🟢 Success     #4CAF50 ████████                          │
│  🟡 Warning     #FF9800 ████████                          │
│  🔴 Error       #F44336 ████████                          │
│  ⚫ Dark        #212121 ████████                          │
│  ⚪ Light       #F5F5F5 ████████                          │
│                                                           │
│  GRADIENTES:                                              │
│  Hero:   #667eea → #764ba2 ████████████████              │
│  Success: #4CAF50 → #45a049 ████████████████             │
│  Info:    #2196F3 → #1976d2 ████████████████             │
└──────────────────────────────────────────────────────────┘
```

---

## 🔄 Estados y Transiciones

### Loading State

```
┌─────────────────────────────┐
│                             │
│        ⏳ Cargando...       │
│                             │
│     ●●●●○○○○○○ 40%          │
│                             │
│  Conectando a cámaras...    │
│                             │
└─────────────────────────────┘
```

### Error State

```
┌─────────────────────────────┐
│                             │
│          ⚠️ Error           │
│                             │
│  No se pudo conectar        │
│  a la cámara                │
│                             │
│     [🔄 Reintentar]         │
│                             │
└─────────────────────────────┘
```

### Success State

```
┌─────────────────────────────┐
│                             │
│          ✅ Éxito           │
│                             │
│  Datos exportados           │
│  correctamente              │
│                             │
│     [✓ Cerrar]              │
│                             │
└─────────────────────────────┘
```

---

## 🎬 Animaciones

### Pulse (Conectando)

```
Frame 1:    ●●●●●
Frame 2:    ●●●○○  (opacity: 0.5)
Frame 3:    ●●●●●
```

### Fade In (Nueva detección)

```
Frame 1:    ░░░░░  (opacity: 0)
Frame 2:    ▒▒▒▒▒  (opacity: 0.5)
Frame 3:    █████  (opacity: 1)
```

### Slide In (Alerta)

```
Frame 1:    ┤
Frame 2:      ┤──
Frame 3:        ┤─────
Frame 4:          ┤──────────
```

---

## 📊 Métricas Visuales

### Dashboard Completo

```
┌────────────────────────────────────────────┐
│  Elementos UI:             52              │
│  Componentes Angular:      2 principales   │
│  Servicios:                2               │
│  Modelos TypeScript:       8               │
│  Endpoints API:            10+             │
│  WebSockets:               2               │
│  Líneas de código:         ~3,500          │
│  Colores usados:           15+             │
│  Iconos Material:          30+             │
│  Animaciones CSS:          5               │
│  Responsive breakpoints:   3               │
└────────────────────────────────────────────┘
```

---

## 🎯 Interacciones

### Click en Cámara
```
Click → Expandir a pantalla completa
      → Mostrar controles adicionales
      → Pausar/Reanudar stream
```

### Hover en Fila de Tabla
```
Hover → Background color change
      → Mostrar acciones adicionales
      → Tooltip con información
```

### Filtrar Tabla
```
Escribir → Filtrado en tiempo real
         → Highlight de matches
         → Actualización de contador
```

---

**🎨 Dashboard completamente visualizado y documentado**  
**Vista previa ASCII para desarrollo y presentación**  
**Versión: 1.0.0**





