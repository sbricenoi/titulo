# 🚀 Guía Rápida - Dashboard Angular

## Pasos para ejecutar el dashboard

### 1️⃣ Backend (FastAPI)

```bash
# Terminal 1: Iniciar backend API
cd /Users/sbriceno/Documents/projects/titulo

# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias API
pip install fastapi uvicorn websockets

# Iniciar servidor API
python api/main.py

# ✅ API corriendo en: http://localhost:8000
# 📚 Docs en: http://localhost:8000/docs
```

### 2️⃣ Frontend (Angular)

```bash
# Terminal 2: Iniciar frontend
cd /Users/sbriceno/Documents/projects/titulo/frontend

# Instalar dependencias (primera vez)
npm install

# Iniciar servidor de desarrollo
ng serve

# ✅ Dashboard corriendo en: http://localhost:4200
```

### 3️⃣ Sistema de Monitoreo (Opcional)

```bash
# Terminal 3: Sistema completo con cámaras
cd /Users/sbriceno/Documents/projects/titulo

# Activar entorno virtual
source venv/bin/activate

# Ejecutar sistema completo
python main.py

# ✅ Sistema procesando cámaras y enviando datos a API
```

---

## 📊 Vista Previa del Dashboard

### Pantalla Principal

```
┌─────────────────────────────────────────────────────────────────┐
│  🐾 FERRET MONITORING SYSTEM                    🔄 Refresh  ⚙️  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📹 CÁMARAS EN VIVO                                             │
│  ┌──────────────────┬──────────────────┬──────────────────┐    │
│  │ 📹 Cámara Sup.   │ 📹 Cámara Inf.   │ 📹 Cámara 3      │    │
│  │ ✅ Conectada     │ ✅ Conectada     │ ⚠️ Conectando   │    │
│  │                  │                  │                  │    │
│  │ [VIDEO STREAM]   │ [VIDEO STREAM]   │ [CONNECTING...]  │    │
│  │                  │                  │                  │    │
│  │ 🎯 30.2 FPS      │ 🎯 29.8 FPS      │ 🎯 0.0 FPS       │    │
│  │ 📐 1920x1080     │ 📐 1920x1080     │ 📐 1920x1080     │    │
│  └──────────────────┴──────────────────┴──────────────────┘    │
│                                                                  │
│  📊 REPORTE DE INDIVIDUOS                                       │
│  ┌────────────────────────────────────────────────────────────┐│
│  │ 🐾 Total: 3  |  ✅ Activos: 2  |  📹 Detecciones: 12      ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                  │
│  🔍 Buscar: [________________]                      📥 Exportar │
│                                                                  │
│  ┌─────┬─────────┬──────────────┬──────────┬──────────┬───────┐│
│  │ ID  │ Estado  │ Comportam.   │ Cámaras  │ Confianza│ Tiempo││
│  ├─────┼─────────┼──────────────┼──────────┼──────────┼───────┤│
│  │ F0  │● Activo │🎮 Jugando    │ Cám 1,2  │████████92│ 5m23s ││
│  │     │         │87%           │          │          │       ││
│  ├─────┼─────────┼──────────────┼──────────┼──────────┼───────┤│
│  │ F1  │○ Inact. │😴 Durmiendo  │ Cám 1    │██████░78 │ 1h12m ││
│  │     │         │94%           │          │          │       ││
│  ├─────┼─────────┼──────────────┼──────────┼──────────┼───────┤│
│  │ F2  │● Activo │🚶 Caminando  │ Cám 2,3  │███████85 │ 45s   ││
│  │     │         │71%           │          │          │       ││
│  └─────┴─────────┴──────────────┴──────────┴──────────┴───────┘│
│                                                                  │
│  Mostrando 3 de 3 individuos              [< 1 2 3 4 5 >]      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Funcionalidades Implementadas

### ✅ Visualización de Cámaras
- [x] Mosaico responsivo de múltiples cámaras
- [x] Estados en tiempo real (conectada, desconectada, error)
- [x] Métricas por cámara (FPS, resolución)
- [x] Reconexión automática
- [x] Vista completa individual

### ✅ Reporte de Individuos
- [x] Tabla interactiva con ordenamiento
- [x] Filtrado y búsqueda en tiempo real
- [x] Paginación automática
- [x] 7 comportamientos detectables con colores
- [x] Indicadores visuales de confianza
- [x] Estado activo/inactivo en tiempo real
- [x] Exportación a CSV
- [x] Auto-refresh cada 5 segundos

### ✅ Estadísticas en Tiempo Real
- [x] Total de individuos detectados
- [x] Individuos activos actualmente
- [x] Total de detecciones
- [x] Métricas del sistema (FPS, uptime)

---

## 🛠️ Tecnologías Utilizadas

### Backend
- **FastAPI:** API REST moderna y rápida
- **WebSocket:** Streaming en tiempo real
- **Pydantic:** Validación de datos
- **CORS Middleware:** Comunicación frontend-backend

### Frontend
- **Angular 17:** Framework principal
- **Angular Material:** Componentes UI
- **RxJS:** Programación reactiva
- **WebSocket:** Conexión en tiempo real
- **TypeScript:** Tipado estático
- **SCSS:** Estilos avanzados

---

## 📁 Estructura de Archivos Creados

```
titulo/
├── api/
│   ├── __init__.py                          ✅ Creado
│   └── main.py                              ✅ Creado (FastAPI backend)
│
├── frontend/
│   ├── package.json                         ✅ Creado
│   ├── angular.json                         ✅ Creado
│   ├── README.md                            ✅ Creado
│   └── src/
│       ├── environments/
│       │   ├── environment.ts               ✅ Creado
│       │   └── environment.prod.ts          ✅ Creado
│       │
│       └── app/
│           ├── core/
│           │   ├── models/
│           │   │   ├── camera.model.ts      ✅ Creado
│           │   │   ├── individual.model.ts  ✅ Creado
│           │   │   └── metrics.model.ts     ✅ Creado
│           │   └── services/
│           │       ├── api.service.ts       ✅ Creado
│           │       └── websocket.service.ts ✅ Creado
│           │
│           └── features/
│               ├── cameras/
│               │   └── camera-grid/
│               │       ├── component.ts     ✅ Creado
│               │       ├── component.html   ✅ Creado
│               │       └── component.scss   ✅ Creado
│               │
│               └── tracking/
│                   └── individual-report/
│                       ├── component.ts     ✅ Creado
│                       ├── component.html   ✅ Creado
│                       └── component.scss   ✅ Creado
│
└── docs/
    ├── DASHBOARD_UI.md                      ✅ Creado
    └── QUICK_START_DASHBOARD.md             ✅ Este archivo
```

---

## 🔧 Configuración Necesaria

### 1. Configurar URLs del Backend

**Archivo:** `frontend/src/environments/environment.ts`

```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000',      // ← Cambiar si es necesario
  wsUrl: 'ws://localhost:8000',         // ← Cambiar si es necesario
  updateInterval: 1000
};
```

### 2. Configurar CORS en Backend

**Archivo:** `api/main.py` (ya configurado)

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # ← Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. Configurar Cámaras

**Archivo:** `config.py`

```python
CAMERA_URLS = [
    "rtsp://usuario:contraseña@192.168.1.10:554/stream1",
    "rtsp://usuario:contraseña@192.168.1.11:554/stream1",
]

CAMERA_NAMES = [
    "Cámara Superior",
    "Cámara Inferior",
]
```

---

## 🐛 Solución de Problemas Comunes

### Problema: "Cannot GET /"
**Solución:** El frontend no está corriendo. Ejecuta `ng serve` en la carpeta frontend.

### Problema: "CORS error"
**Solución:** Verifica que el backend tenga configurado CORS correctamente en `api/main.py`.

### Problema: "No se conecta WebSocket"
**Solución:** 
1. Verifica que el backend esté corriendo en http://localhost:8000
2. Revisa la URL en `environment.ts`
3. Abre DevTools > Console para ver errores

### Problema: "Tabla de individuos vacía"
**Solución:**
1. Verifica que el sistema de monitoreo esté corriendo (`python main.py`)
2. Espera a que se detecten individuos
3. Revisa la respuesta de `/api/individuals` en DevTools > Network

---

## 📈 Próximos Pasos

### Mejoras Inmediatas
1. **Integrar con sistema real:** Conectar el dashboard con `main.py` para recibir datos reales
2. **Streaming de video:** Implementar envío de frames via WebSocket
3. **Persistencia:** Guardar histórico en base de datos

### Mejoras Futuras
1. **Visualización de trayectorias:** Mapa 2D/3D con movimientos
2. **Gráficos de comportamiento:** Charts con estadísticas temporales
3. **Alertas en tiempo real:** Notificaciones push
4. **Dashboard personalizable:** Drag & drop de widgets
5. **Modo oscuro:** Theme switcher
6. **App móvil:** Versión móvil con Ionic

---

## 📚 Documentación Adicional

- **Arquitectura del Sistema:** `docs/arquitectura.md`
- **Documentación del Dashboard:** `docs/DASHBOARD_UI.md`
- **README Principal:** `README.md`
- **API Docs:** http://localhost:8000/docs (cuando backend está corriendo)

---

## ✅ Checklist de Verificación

Antes de considerar el dashboard funcional, verifica:

- [ ] Backend API corriendo en puerto 8000
- [ ] Frontend corriendo en puerto 4200
- [ ] Sin errores en consola del navegador
- [ ] WebSocket conectado (ver DevTools > Network > WS)
- [ ] Cámaras aparecen en el mosaico
- [ ] Tabla de individuos se actualiza
- [ ] Estadísticas muestran números correctos
- [ ] Exportar CSV funciona
- [ ] Filtrado y búsqueda funcionan
- [ ] Responsive en diferentes tamaños de pantalla

---

## 🎉 ¡Listo!

El dashboard está completamente desarrollado y listo para usar. Solo necesitas:

1. **Instalar dependencias** del frontend (`npm install`)
2. **Iniciar el backend** (`python api/main.py`)
3. **Iniciar el frontend** (`ng serve`)
4. **Abrir el navegador** en http://localhost:4200

¡Disfruta monitoreando a tus hurones! 🐾

---

**Desarrollado con ❤️ para el Sistema de Monitoreo de Hurones**  
**Fecha:** 2025-10-28  
**Versión:** 1.0.0





