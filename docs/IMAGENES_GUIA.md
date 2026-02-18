# Guía de Imágenes para el Dashboard

Este documento explica cómo gestionar las imágenes del sistema de monitoreo.

## 📁 Estructura de Carpetas

```
frontend/src/assets/images/
├── cameras/              # Imágenes de las vistas de cámaras
│   ├── camera-1.jpg     # Cámara Principal - Sala
│   ├── camera-2.jpg     # Cámara Túnel - Izquierda
│   ├── camera-3.jpg     # Cámara Nido - Superior
│   ├── camera-4.jpg     # Cámara Comedero
│   ├── camera-5.jpg     # Cámara Juguetero
│   ├── default.jpg      # Imagen por defecto (opcional)
│   └── README.md        # Documentación de esta carpeta
│
└── hurones/             # Imágenes/avatares de hurones (opcional)
    ├── ferret-F1.jpg    # Avatar del hurón F1
    ├── ferret-F2.jpg    # Avatar del hurón F2
    └── .gitkeep
```

## 🎥 Imágenes de Cámaras

### Obtener las Imágenes

Tienes varias opciones:

#### Opción 1: Capturas de Cámaras Reales (RECOMENDADO)
1. Accede a cada cámara IP mediante su interfaz web o VLC
2. Captura un frame representativo de cada cámara
3. Guarda con el nombre correspondiente (camera-1.jpg, camera-2.jpg, etc.)

#### Opción 2: Fotografías de los Espacios
1. Toma fotos de los espacios donde están instaladas las cámaras
2. Asegúrate de capturar el ángulo similar al de la cámara
3. Optimiza y guarda con los nombres correctos

#### Opción 3: Usar Placeholders Temporalmente
- El sistema ya usa placeholders externos automáticamente
- Estos se mostrarán hasta que agregues imágenes reales

### Especificaciones Técnicas

| Propiedad | Valor Recomendado | Mínimo | Máximo |
|-----------|-------------------|---------|---------|
| **Resolución** | 1280x720 (HD) | 640x480 | 1920x1080 |
| **Aspect Ratio** | 16:9 o 3:2 | - | - |
| **Formato** | JPG | PNG, WebP | - |
| **Tamaño** | 200-500 KB | 50 KB | 1 MB |
| **Calidad JPG** | 80-85% | 70% | 90% |

### Optimizar Imágenes

Usa herramientas online gratuitas:
- **TinyPNG**: https://tinypng.com/
- **Squoosh**: https://squoosh.app/
- **ImageOptim** (Mac): https://imageoptim.com/

O con comando de terminal:
```bash
# Instalar ImageMagick
brew install imagemagick  # macOS
sudo apt install imagemagick  # Linux

# Optimizar imagen
convert camera-original.jpg -resize 1280x720 -quality 85 camera-1.jpg
```

## 🔧 Activar Imágenes Locales

### Paso 1: Agregar las Imágenes

Coloca tus imágenes optimizadas en:
```
frontend/src/assets/images/cameras/
```

Con los nombres:
- `camera-1.jpg` → Cámara ID 1
- `camera-2.jpg` → Cámara ID 2
- `camera-3.jpg` → Cámara ID 3
- etc.

### Paso 2: Configurar el Servicio

Edita: `frontend/src/app/core/services/mock-data.service.ts`

Busca el método `getCameraPlaceholderUrl` y cambia:

```typescript
const useLocalImages = false; // ← Cambiar a true
```

Por:

```typescript
const useLocalImages = true; // ✅ Ahora usa imágenes locales
```

### Paso 3: Verificar

1. Guarda el archivo
2. Angular recargará automáticamente
3. Abre el dashboard en http://localhost:4200
4. Verifica que las imágenes se muestran correctamente

### Solución de Problemas

| Problema | Solución |
|----------|----------|
| **Imagen no aparece** | Verifica el nombre del archivo (debe ser exacto) |
| **Error 404** | Asegúrate de que la imagen está en `src/assets/images/cameras/` |
| **Imagen distorsionada** | Ajusta el aspect ratio a 16:9 o 3:2 |
| **Carga lenta** | Optimiza el tamaño del archivo (< 500KB) |
| **No se actualiza** | Limpia la caché del navegador (Ctrl+Shift+R) |

## 🦦 Imágenes de Hurones (Opcional)

Si quieres agregar avatares o fotos de los hurones individuales:

1. Coloca las imágenes en: `frontend/src/assets/images/hurones/`
2. Nombra los archivos según el ID: `ferret-F1.jpg`, `ferret-F2.jpg`, etc.
3. Las imágenes deben ser cuadradas (1:1) para mejor visualización
4. Tamaño recomendado: 200x200 px o 300x300 px
5. Peso máximo: 100KB por imagen

## 📝 Ejemplo Completo

```bash
# Desde la raíz del proyecto
cd frontend/src/assets/images/cameras

# Agregar tus imágenes (ejemplo con curl para testing)
curl -o camera-1.jpg "https://your-camera-ip/snapshot.jpg"
curl -o camera-2.jpg "https://your-camera-ip/snapshot.jpg"

# Verificar que existen
ls -lh

# Resultado esperado:
# camera-1.jpg (320 KB)
# camera-2.jpg (285 KB)
# camera-3.jpg (310 KB)
# ...
```

## ✅ Checklist Final

- [ ] Imágenes agregadas en la carpeta correcta
- [ ] Nombres de archivo correctos (camera-1.jpg, camera-2.jpg, etc.)
- [ ] Imágenes optimizadas (< 500KB cada una)
- [ ] Aspect ratio apropiado (16:9 o 3:2)
- [ ] Configuración actualizada en `mock-data.service.ts` (`useLocalImages = true`)
- [ ] Dashboard recargado y verificado en el navegador
- [ ] No hay errores 404 en la consola del navegador

## 🔄 Actualización Futura

Cuando conectes las cámaras reales vía RTSP, estas imágenes estáticas serán reemplazadas por el stream en vivo. Por ahora, sirven como visualización del layout del sistema.

## 📚 Referencias

- [Angular Assets Guide](https://angular.io/guide/workspace-config#assets-configuration)
- [Image Optimization Best Practices](https://web.dev/fast/#optimize-your-images)
- [RTSP Stream Integration](../api/main.py) - Para la integración futura





