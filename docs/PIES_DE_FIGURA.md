# Pies de Figura para Tesis
## Texto para acompañar las capturas de pantalla

---

## Figura 1: Panel de Visualización Multi-Cámara en Tiempo Real

**Interfaz de monitoreo multi-cámara del sistema de seguimiento de hurones.** La vista presenta tres cámaras posicionadas estratégicamente (Superior, Inferior, Lateral) que permiten cobertura espacial completa del recinto. Cada panel de cámara muestra: (a) estado de conexión en tiempo real, (b) identificación automática de elementos del entorno (hamaca, arena, agua, alimento) mediante etiquetado visual, (c) métricas técnicas de rendimiento (FPS y resolución), y (d) controles de acceso para visualización expandida y configuración de parámetros. El diseño multi-punto-de-vista elimina zonas ocultas y facilita la triangulación espacial para reconstrucción tridimensional de trayectorias. La cámara lateral muestra estado de desconexión, evidenciando la capacidad del sistema para monitorear el estado operativo de cada componente de hardware.

---

## Figura 2: Panel de Análisis y Seguimiento Individual

**Interfaz de registro individualizado de hurones monitoreados mediante sistema de re-identificación visual.** El panel superior presenta métricas agregadas del sistema: total de individuos identificados (n=5), individuos activos en período actual (n=4), y total de detecciones exitosas acumuladas (n=7). La tabla de seguimiento individual registra para cada hurón: identificador único persistente (F0-F3), estado de actividad actual, comportamiento clasificado automáticamente con nivel de confianza asociado (71%-91%), localización espacial por cámara, representación visual del nivel de confianza de identificación, tiempo acumulado de actividad en sesión actual, y timestamp de última detección. El sistema permite búsqueda por identificador, exportación de datos para análisis estadístico, y configuración de alertas individualizadas. La actualización de información ocurre en tiempo real mediante conexión persistente al servidor de procesamiento.

---

## Descripción Técnica Complementaria (opcional para metodología)

**Sistema implementado:** Arquitectura cliente-servidor con procesamiento en tiempo real de streams de video mediante algoritmos de visión por computador. El sistema emplea YOLOv8 para detección de objetos, DeepSORT para seguimiento multi-objeto, y OSNet para re-identificación persistente de individuos. La clasificación comportamental se realiza mediante redes neuronales convolucionales entrenadas en secuencias temporales de poses. La interfaz de usuario está desarrollada como aplicación web progresiva (PWA) que permite acceso desde dispositivos múltiples sin necesidad de instalación de software especializado.

**Hardware requerido:** Cámaras IP con capacidad de transmisión RTSP, resolución mínima HD (1280×720), visión nocturna infrarroja para monitoreo 24/7, servidor con GPU para procesamiento en tiempo real (mínimo NVIDIA GTX 1060 o equivalente).

---

## Versión Corta - Pies de Figura Concisos

### Figura 1:
**Panel de visualización multi-cámara** mostrando tres puntos de vista simultáneos del recinto con identificación automática de zonas de interés y estado operativo de cada cámara en tiempo real.

### Figura 2:
**Panel de análisis individual** presentando seguimiento de cinco hurones (F0-F3) con métricas de actividad, comportamiento clasificado automáticamente, y nivel de confianza de identificación del sistema.

---

## Versión Media - Pies de Figura Descriptivos

### Figura 1: Vista de Monitoreo Multi-Cámara

**Sistema de visualización en tiempo real de múltiples cámaras IP** instaladas en el recinto de hurones. El diseño multi-punto-de-vista permite cobertura espacial completa, identificación automática de elementos del entorno (hamaca, agua, alimento, sustrato), y monitoreo del estado operativo de cada cámara. Las métricas técnicas (FPS, resolución) aseguran calidad adecuada para análisis automático de comportamiento.

### Figura 2: Vista de Reporte Individual

**Panel de seguimiento individualizado de hurones** mediante sistema de re-identificación visual. Para cada individuo se registra: identificador único (F0-F3), comportamiento actual clasificado automáticamente (explorando, caminando, jugando, comiendo, durmiendo) con nivel de confianza asociado, localización espacial, tiempo activo acumulado, y última detección. El sistema permite identificación rápida de individuos con patrones comportamentales anómalos para priorización de atención veterinaria.

---

## Recomendaciones de Uso

**Para sección de Resultados/Metodología:**
- Usar la versión media o larga dependiendo del espacio disponible
- Incluir la descripción técnica complementaria si el trabajo tiene un componente significativo de desarrollo tecnológico

**Para presentaciones:**
- Usar la versión corta en diapositivas
- Expandir verbalmente durante la presentación

**Para artículos:**
- Versión media es apropiada para journals veterinarios
- Versión larga para journals de tecnología aplicada o informática biomédica

**Numeración sugerida:**
- Si son las primeras figuras técnicas: Figura 1 y Figura 2
- Si ya hay figuras previas: Usar numeración correlativa (ej. Figura 5a y 5b si son sub-figuras de una misma figura)





