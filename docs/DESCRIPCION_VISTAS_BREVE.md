# Descripción de las Vistas del Sistema
## Texto Breve para Tesis - Sección de Metodología Tecnológica

---

## Sistema de Monitoreo Multi-Cámara para Hurones: Interfaz de Visualización

El sistema desarrollado proporciona dos interfaces principales para el monitoreo y análisis del comportamiento de hurones en ambientes controlados:

### Vista de Cámaras en Tiempo Real (Figura X)

La interfaz multi-cámara presenta un mosaico de visualización simultánea que permite la supervisión continua de las distintas zonas del recinto. Cada cámara está estratégicamente posicionada (superior, inferior, lateral) para eliminar puntos ciegos y facilitar la reconstrucción tridimensional de las trayectorias de movimiento de los animales.

El sistema identifica y etiqueta automáticamente elementos relevantes del entorno (zonas de alimentación, descanso, agua, sustrato sanitario), permitiendo vincular comportamientos específicos con localizaciones particulares del espacio. Los indicadores en tiempo real muestran el estado de conexión de cada cámara, así como parámetros técnicos críticos para la calidad del análisis (FPS y resolución activa).

**Función principal**: Esta vista permite la verificación visual directa del estado general de los animales y la validación de comportamientos clasificados automáticamente por el sistema.

### Vista de Reporte Individual (Figura Y)

El panel de análisis individual presenta una tabla consolidada con información de seguimiento de cada hurón identificado. El sistema asigna automáticamente identificadores únicos (F0, F1, F2...) que se mantienen consistentes entre sesiones mediante algoritmos de re-identificación visual.

Para cada individuo, el sistema registra:

- **Estado de actividad**: Clasificación activo/inactivo basada en detección de movimiento reciente
- **Comportamiento actual**: Categorización automática del comportamiento observado (explorando, caminando, jugando, comiendo, durmiendo) con nivel de confianza asociado
- **Localización espacial**: Identificación de la(s) cámara(s) donde se visualiza actualmente al animal
- **Tiempo activo acumulado**: Métrica temporal relevante para evaluar niveles normales de actividad
- **Última detección**: Timestamp de la última visualización exitosa del individuo

Los indicadores de confianza (representados mediante barras de progreso porcentual) permiten al evaluador considerar el nivel de certeza del sistema en sus clasificaciones automáticas, facilitando la decisión de cuándo es necesaria validación manual.

**Función principal**: Esta interfaz permite la identificación rápida de individuos con patrones comportamentales anómalos, facilitando la priorización de atención veterinaria y la generación de registros objetivos de comportamiento útiles para diagnóstico y seguimiento clínico.

---

## Flujo de Trabajo e Integración Clínica

Ambas vistas funcionan de manera complementaria en el flujo de trabajo veterinario:

1. **Monitoreo Pasivo**: El sistema opera continuamente, registrando actividad de todos los individuos
2. **Detección de Anomalías**: Los algoritmos identifican desviaciones respecto a patrones comportamentales normales
3. **Alertas Priorizadas**: El veterinario recibe notificaciones de individuos que requieren atención
4. **Validación Visual**: Uso de la vista de cámaras para confirmar observaciones automáticas
5. **Análisis Detallado**: Consulta del historial individual para evaluar evolución temporal

Este diseño permite que el sistema actúe como herramienta de apoyo, automatizando la recopilación de datos sin reemplazar el criterio clínico profesional. La información cuantitativa generada complementa la evaluación veterinaria tradicional, proporcionando datos objetivos sobre patrones de actividad, uso del espacio y comportamientos específicos que podrían no ser evidentes durante observaciones puntuales.

---

## Ventajas del Enfoque Multi-Cámara

La arquitectura con múltiples puntos de vista simultáneos ofrece ventajas específicas para el monitoreo de animales pequeños:

- **Cobertura espacial completa**: Elimina zonas ocultas donde los animales podrían no ser detectados
- **Triangulación espacial**: Permite determinar posiciones tridimensionales aproximadas
- **Robustez de identificación**: La visualización desde múltiples ángulos mejora la precisión de re-identificación
- **Contexto comportamental**: Diferentes cámaras capturan comportamientos que ocurren en zonas específicas del recinto

Esta metodología tecnológica representa un avance hacia sistemas de monitoreo veterinario basados en datos continuos y objetivos, reduciendo la dependencia de observaciones manuales esporádicas y potencialmente sesgadas, mientras se mantiene un enfoque no invasivo que minimiza el estrés animal.





