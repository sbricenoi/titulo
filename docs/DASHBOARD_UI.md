# 📊 Dashboard UI - Documentación

## 🎨 Maqueta del Frontend Angular

Dashboard web profesional para visualización de cámaras en tiempo real y reportes de movimientos de individuos.

---

## 🚀 Instalación y Configuración

### Requisitos Previos

- Node.js 18+
- Angular CLI 17+
- Backend API corriendo (FastAPI)

### Instalación

```bash
# Navegar al directorio frontend
cd frontend

# Instalar dependencias
npm install

# Configurar variables de entorno
# Editar src/environments/environment.ts

# Iniciar servidor de desarrollo
ng serve

# Abrir en navegador
# http://localhost:4200
```

---

## 📐 Arquitectura del Frontend

```
frontend/
├── src/
│   ├── app/
│   │   ├── core/                    # Servicios core y modelos
│   │   │   ├── models/
│   │   │   │   ├── camera.model.ts
│   │   │   │   ├── individual.model.ts
│   │   │   │   └── metrics.model.ts
│   │   │   └── services/
│   │   │       ├── api.service.ts
│   │   │       └── websocket.service.ts
│   │   │
│   │   └── features/                # Módulos funcionales
│   │       ├── cameras/
│   │       │   └── camera-grid/    # Mosaico de cámaras
│   │       ├── tracking/
│   │       │   └── individual-report/  # Reporte de individuos
│   │       └── dashboard/
│   │           └── main-dashboard/     # Dashboard principal
│   │
│   ├── environments/
│   └── assets/
└── package.json
```

---

## 🖼️ Componentes Principales

### 1. Camera Grid Component
**Ruta:** `app/features/cameras/camera-grid/`

#### Funcionalidad:
- ✅ Visualización de múltiples cámaras en mosaico responsivo
- ✅ Estado de conexión en tiempo real (conectada, desconectada, error)
- ✅ Métricas por cámara (FPS, resolución)
- ✅ Streaming de video via WebSocket
- ✅ Vista completa de cámara individual

#### Características visuales:
- **Grid responsivo:** 1, 2, 3+ columnas según tamaño de pantalla
- **Indicadores de estado:** Colores y iconos según conexión
- **Overlay de información:** FPS y resolución sobre el video
- **Animaciones:** Pulse para estado "conectando"

#### Código de ejemplo:

```typescript
<app-camera-grid></app-camera-grid>
```

**Vista previa:**
```
┌─────────────────────┬─────────────────────┐
│  📹 Cámara Superior │  📹 Cámara Inferior │
│  ✅ Conectada       │  ✅ Conectada       │
│                     │                     │
│  [VIDEO STREAM]     │  [VIDEO STREAM]     │
│                     │                     │
│  🎯 30.5 FPS        │  🎯 29.8 FPS        │
│  📐 1920x1080       │  📐 1920x1080       │
└─────────────────────┴─────────────────────┘
```

---

### 2. Individual Report Component
**Ruta:** `app/features/tracking/individual-report/`

#### Funcionalidad:
- ✅ Tabla completa de individuos tracked
- ✅ Filtrado y búsqueda en tiempo real
- ✅ Ordenamiento por columnas
- ✅ Paginación
- ✅ Estadísticas resumidas (total, activos, detecciones)
- ✅ Exportación a CSV
- ✅ Auto-refresh cada 5 segundos

#### Columnas de la tabla:
1. **ID:** Identificador único (ej. F0, F1)
2. **Estado:** Activo / Inactivo (basado en última detección)
3. **Comportamiento:** Chip con comportamiento actual y confianza
4. **Cámaras:** Lista de cámaras donde se ve
5. **Confianza:** Barra de progreso visual
6. **Tiempo Activo:** Duración total desde primera detección
7. **Última Vez Visto:** Tiempo relativo (ej. "hace 2 segundos")
8. **Acciones:** Ver detalles, ver trayectoria

#### Comportamientos con colores:
- 🍽️ **Comiendo:** Verde (#4CAF50)
- 😴 **Durmiendo:** Azul (#2196F3)
- 🎮 **Jugando:** Naranja (#FF9800)
- 🚶 **Caminando:** Púrpura (#9C27B0)
- 🤝 **Interactuando:** Rosa (#E91E63)
- 🔍 **Explorando:** Cian (#00BCD4)
- 🧘 **Inactivo:** Gris (#9E9E9E)

#### Vista previa de tabla:

```
┌──────┬─────────┬──────────────┬──────────┬──────────┬────────────┬──────────────┬─────────┐
│  ID  │ Estado  │ Comportamiento│ Cámaras │ Confianza│ Tiempo Act.│ Última Vez   │ Acciones│
├──────┼─────────┼──────────────┼──────────┼──────────┼────────────┼──────────────┼─────────┤
│  F0  │ ● Activo│ 🎮 Jugando   │ Cám 1,2  │ ████████ │ ⏱️ 5m 23s  │ hace 1 seg   │ 👁️ 📍  │
│      │         │ 87%          │          │ 92%      │            │              │         │
├──────┼─────────┼──────────────┼──────────┼──────────┼────────────┼──────────────┼─────────┤
│  F1  │ ○ Inact.│ 😴 Durmiendo │ Cám 1    │ ██████░░ │ ⏱️ 1h 12m  │ hace 3 min   │ 👁️ 📍  │
│      │         │ 94%          │          │ 78%      │            │              │         │
└──────┴─────────┴──────────────┴──────────┴──────────┴────────────┴──────────────┴─────────┘
```

---

## 🎨 Diseño y UX

### Paleta de Colores

**Primarios:**
- Principal: `#667eea` → `#764ba2` (Gradiente púrpura)
- Secundario: `#2196F3` (Azul)
- Acento: `#FF9800` (Naranja)

**Estados:**
- Éxito: `#4CAF50` (Verde)
- Error: `#F44336` (Rojo)
- Advertencia: `#FF9800` (Naranja)
- Info: `#2196F3` (Azul)
- Inactivo: `#9E9E9E` (Gris)

### Tipografía
- **Fuente:** Roboto (Angular Material default)
- **Títulos:** 24px, Medium (500)
- **Subtítulos:** 18px, Regular (400)
- **Cuerpo:** 14px, Regular (400)
- **Labels:** 12px, Medium (500)

### Espaciado
- **Padding contenedor:** 16px
- **Gap entre cards:** 16px
- **Gap entre elementos:** 8px

### Responsive Breakpoints
- **Mobile:** < 960px (1 columna)
- **Tablet:** 960px - 1280px (2 columnas)
- **Desktop:** > 1280px (3+ columnas)

---

## 🔌 Integración con Backend

### API REST Endpoints

```typescript
// Servicios disponibles
apiService.getCameras()           // GET /api/cameras
apiService.getIndividuals()        // GET /api/individuals
apiService.getBehaviors()          // GET /api/behaviors
apiService.getMetrics()            // GET /api/metrics
apiService.getAlerts()             // GET /api/alerts
```

### WebSocket Connections

```typescript
// Streaming de video
wsService.connectStream()          // ws://localhost:8000/ws/stream

// Datos en tiempo real
wsService.connectData()            // ws://localhost:8000/ws/data
```

### Formato de Respuesta API

```json
{
  "traceId": "abc-123",
  "code": 200,
  "message": "Operación exitosa",
  "data": {
    // ... datos específicos
  }
}
```

---

## 📊 Estadísticas y Métricas

### Tarjetas de Estadísticas

**1. Total Individuos**
- Icono: 🐾 `pets`
- Descripción: Número total de individuos detectados
- Actualización: En tiempo real

**2. Activos Ahora**
- Icono: 👁️ `visibility`
- Descripción: Individuos vistos en últimos 10 segundos
- Color: Verde (éxito)
- Actualización: Cada segundo

**3. Total Detecciones**
- Icono: 📹 `videocam`
- Descripción: Suma de todas las detecciones en cámaras
- Color: Azul (info)
- Actualización: En tiempo real

---

## 🎬 Animaciones y Transiciones

### Loading States
- **Spinner:** Material spinner centrado
- **Texto:** "Cargando..." con color gris

### Estado Conectando (Cámaras)
```scss
animation: pulse 1.5s ease-in-out infinite;

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
```

### Hover Effects
- **Botones:** Elevación de sombra
- **Cards:** Transformación sutil (scale 1.02)
- **Rows:** Background color change

---

## 🔧 Configuración de Entorno

### development.ts
```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000',
  wsUrl: 'ws://localhost:8000',
  updateInterval: 1000  // ms
};
```

### production.ts
```typescript
export const environment = {
  production: true,
  apiUrl: 'https://api.ferret-monitoring.com',
  wsUrl: 'wss://api.ferret-monitoring.com',
  updateInterval: 2000  // ms
};
```

---

## 🚀 Despliegue

### Build de Producción

```bash
# Build optimizado
ng build --configuration production

# Output en dist/
# Servir con nginx, Apache, o servidor estático
```

### Configuración Nginx (ejemplo)

```nginx
server {
    listen 80;
    server_name dashboard.ferret-monitoring.com;
    root /var/www/ferret-dashboard/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy para API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }
}
```

---

## 📱 Features Adicionales (Futuras)

### Fase 1 (Actual) ✅
- [x] Mosaico de cámaras
- [x] Tabla de individuos
- [x] Estadísticas básicas
- [x] Auto-refresh
- [x] Exportación CSV

### Fase 2 (Próxima)
- [ ] Visualización de trayectorias en mapa
- [ ] Gráficos de comportamiento (Chart.js)
- [ ] Filtros avanzados
- [ ] Modo oscuro
- [ ] Notificaciones push

### Fase 3 (Futuro)
- [ ] Dashboard personalizable (drag & drop)
- [ ] Historial de grabaciones
- [ ] Comparación entre individuos
- [ ] Reportes automáticos (PDF)
- [ ] App móvil (Ionic)

---

## 🐛 Troubleshooting

### Problema: WebSocket no conecta

**Solución:**
```typescript
// Verificar URL en environment.ts
// Asegurar que backend está corriendo
// Revisar CORS en FastAPI
```

### Problema: Tabla vacía

**Solución:**
```typescript
// Verificar que backend tiene datos
// Abrir DevTools > Network > XHR
// Revisar respuesta de /api/individuals
```

### Problema: Imágenes no se cargan

**Solución:**
```typescript
// Verificar formato Base64
// Comprobar WebSocket de streaming
// Revisar logs del navegador
```

---

## 📚 Recursos

- **Angular Material:** https://material.angular.io/
- **RxJS:** https://rxjs.dev/
- **Chart.js:** https://www.chartjs.org/
- **date-fns:** https://date-fns.org/

---

## 👥 Equipo y Contacto

Para preguntas o soporte del dashboard:
- Frontend Issues: [GitHub Issues]
- Email: frontend@ferret-monitoring.com

---

**Última actualización:** 2025-10-28  
**Versión:** 1.0.0  
**Framework:** Angular 17+





