# Imágenes de Cámaras

Esta carpeta contiene las imágenes placeholder que se mostrarán en el dashboard cuando las cámaras están conectadas.

## Estructura

```
cameras/
├── camera-1.jpg    # Imagen para Cámara Principal - Sala
├── camera-2.jpg    # Imagen para Cámara Túnel - Izquierda
├── camera-3.jpg    # Imagen para Cámara Nido - Superior
├── camera-4.jpg    # Imagen para Cámara Comedero
├── camera-5.jpg    # Imagen para Cámara Juguetero
└── default.jpg     # Imagen por defecto para cámaras sin imagen específica
```

## Especificaciones Recomendadas

- **Formato**: JPG, PNG o WebP
- **Resolución recomendada**: 1280x720 (HD) o 1920x1080 (Full HD)
- **Aspect Ratio**: 3:2 (para mejor visualización en el grid)
- **Tamaño de archivo**: Optimizado, menor a 500KB por imagen

## Imágenes de Ejemplo

Mientras no tengas imágenes reales de las cámaras, puedes usar:

1. **Capturas de las cámaras reales** en modo test
2. **Imágenes de los espacios** donde están instaladas las cámaras
3. **Placeholders temporales** hasta tener las imágenes definitivas

## Uso

El servicio `MockDataService` utiliza automáticamente estas imágenes:
- Si existe `camera-{id}.jpg`, se usa esa imagen
- Si no existe, se usa `default.jpg`
- Si no hay ninguna imagen, se usa un placeholder externo temporal





