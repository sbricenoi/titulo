# Cómo Usar las Imágenes de Cámaras

## Paso 1: Agregar tus imágenes

Coloca tus imágenes en esta carpeta con los siguientes nombres:

```
camera-1.jpg   → Cámara Principal - Sala
camera-2.jpg   → Cámara Túnel - Izquierda
camera-3.jpg   → Cámara Nido - Superior
camera-4.jpg   → Cámara Comedero
camera-5.jpg   → Cámara Juguetero
default.jpg    → Imagen por defecto (opcional)
```

## Paso 2: Activar uso de imágenes locales

Abre el archivo: `src/app/core/services/mock-data.service.ts`

Busca el método `getCameraPlaceholderUrl` y cambia:

**De esto:**
```typescript
getCameraPlaceholderUrl(cameraId: number): string {
  const localImagePath = `assets/images/cameras/camera-${cameraId}.jpg`;
  
  // Por ahora, usa placeholders externos
  const imageIndex = (cameraId % 5) + 1;
  return `https://picsum.photos/seed/${cameraId}/640/360?random=${imageIndex}`;
}
```

**A esto:**
```typescript
getCameraPlaceholderUrl(cameraId: number): string {
  // Usar imágenes locales
  return `assets/images/cameras/camera-${cameraId}.jpg`;
}
```

## Paso 3: Verificar en el navegador

1. Guarda los cambios
2. Angular recargará automáticamente
3. Las imágenes locales se mostrarán en el dashboard

## Alternativa: Imagen por Defecto

Si prefieres usar una sola imagen para todas las cámaras mientras las configuras:

```typescript
getCameraPlaceholderUrl(cameraId: number): string {
  return `assets/images/cameras/default.jpg`;
}
```

## Notas Importantes

- **Formato**: Asegúrate de usar el formato correcto (jpg, png, webp)
- **Nombres**: Los nombres deben coincidir exactamente (camera-1.jpg, camera-2.jpg, etc.)
- **Tamaño**: Optimiza las imágenes para web (< 500KB recomendado)
- **Aspect Ratio**: 3:2 o 16:9 funcionan mejor con el diseño actual

## Si no aparecen las imágenes

Verifica:
1. ✅ Las imágenes están en `frontend/src/assets/images/cameras/`
2. ✅ Los nombres de archivo son correctos (sin espacios, con extensión)
3. ✅ Angular se ha recargado completamente (Ctrl+C y volver a ejecutar `ng serve`)
4. ✅ La consola del navegador no muestra errores 404





