# Sistema de Monitoreo Inteligente Multi-Cámara para Hurones
## Descripción del Sistema de Visualización y Control

### Resumen Ejecutivo

El presente sistema constituye una herramienta tecnológica de apoyo para el monitoreo continuo y análisis comportamental de hurones en entornos controlados. A través de la integración de múltiples cámaras IP y algoritmos de visión por computador, el sistema permite realizar un seguimiento individualizado no invasivo de cada animal, facilitando la recopilación de datos etológicos de forma automatizada y la detección temprana de patrones comportamentales anómalos.

### Contexto y Justificación

En la práctica veterinaria moderna, el monitoreo continuo de animales pequeños como los hurones presenta desafíos significativos: la supervisión manual es intensiva en tiempo, puede resultar invasiva para los animales, y dificulta la captura de datos comportamentales durante períodos prolongados, especialmente durante las horas nocturnas cuando muchas especies exhiben sus comportamientos naturales más relevantes.

Este sistema surge como respuesta a la necesidad de implementar métodos de observación que minimicen el estrés animal mientras maximizan la calidad y cantidad de información clínica y comportamental recopilada. La tecnología actúa como asistente del profesional veterinario, permitiendo dedicar más tiempo al análisis clínico y menos a la recopilación manual de datos.

---

## Interfaz de Usuario: Componentes Principales

El sistema está diseñado con dos interfaces principales que responden a diferentes necesidades de monitoreo:

### 1. Vista de Monitoreo de Cámaras en Tiempo Real

**Figura 1: Panel de Visualización Multi-Cámara**

Esta vista presenta un mosaico de las cámaras instaladas en el recinto, permitiendo la supervisión simultánea de diferentes áreas. Cada cámara cubre zonas específicas de interés:

#### Características Funcionales:

**Identificación de Zonas:**
- **Cámara Superior / Inferior / Lateral**: Posiciones estratégicas que permiten la triangulación espacial y seguimiento tridimensional de los individuos
- Cada cámara identifica automáticamente áreas funcionales del recinto (hamaca, arena, agua, alimento) mediante etiquetado visual

**Indicadores de Estado en Tiempo Real:**
- **Estado de Conexión**: Indicador visual del estado operativo de cada cámara (Conectada/Desconectada)


**Funcionalidad de Control:**
- **Ver completo**: Permite expandir la vista de una cámara específica para observación detallada
- **Configuración**: Acceso a ajustes de cada cámara (calibración, regiones de interés, umbrales de detección)

#### Aplicación Veterinaria:

Esta vista es particularmente útil para:
- Verificación visual rápida del estado general del grupo
- Supervisión de interacciones sociales entre individuos
- Observación directa en tiempo real cuando se detecta una alerta
- Validación visual de comportamientos clasificados automáticamente por el sistema

El diseño multi-cámara elimina puntos ciegos y permite documentar comportamientos que ocurren en zonas específicas (uso de recursos, preferencias espaciales, patrones de descanso).

---

### 2. Vista de Reporte Individual de Seguimiento

**Figura 2: Panel de Análisis de Individuos Monitoreados**

Esta interfaz proporciona una visión analítica consolidada de todos los individuos bajo monitoreo, presentando información relevante para la evaluación veterinaria y etológica.

#### Métricas de Resumen:

El panel superior muestra indicadores agregados del sistema:
- **Total Individuos**: Número de hurones identificados y registrados en el sistema
- **Activos Ahora**: Cantidad de animales detectados como activos en el período actual (útil para identificar patrones de actividad circadiana)
- **Total Detecciones**: Contador acumulado que refleja la frecuencia de identificación exitosa de cada individuo

#### Tabla de Seguimiento Individual:

Cada fila representa un individuo único identificado por el sistema, con las siguientes columnas de información:

**ID del Individuo**: 
Identificador único asignado automáticamente (F0, F1, F2, F3...). Este código se mantiene consistente a través de las sesiones de monitoreo mediante algoritmos de re-identificación.

**Estado de Actividad**:
- *Activo/Inactivo*: Basado en detección de movimiento y última visualización
- Indicador visual codificado por color para identificación rápida

**Comportamiento Actual**:
Clasificación automática del comportamiento observado:
- *Explorando*: Movimiento activo por el recinto
- *Caminando*: Desplazamiento dirigido
- *Jugando*: Patrones de movimiento característicos de juego
- *Comiendo*: Detección en zona de alimentación con postura característica
- *Durmiendo*: Inactividad prolongada en zona de descanso

Cada comportamiento incluye un porcentaje de confianza del modelo predictivo, permitiendo al evaluador considerar la certeza de la clasificación automática.

**Ubicación (Cámaras)**:
Indica en qué cámara(s) se visualiza actualmente al individuo, facilitando la localización espacial rápida. Puede mostrar múltiples cámaras cuando el animal está en zona de solapamiento.

**Nivel de Confianza**:
Barra de progreso visual que representa la certeza del sistema en la identificación del individuo. Valores altos (>80%) indican identificación robusta; valores menores pueden requerir validación manual.

**Tiempo Activo**:
Duración acumulada de actividad registrada en la sesión actual. Este dato es especialmente relevante para:
- Evaluar niveles normales de actividad
- Detectar hipoactividad que pudiera indicar enfermedad
- Monitorear recuperación post-tratamiento

**Última Vez Visto**:
Timestamp de la última detección exitosa. Útil para:
- Identificar individuos que no han sido visualizados recientemente
- Alertar sobre posibles animales ocultos o en zonas no monitoreadas
- Validar cobertura espacial de las cámaras

**Acciones Disponibles**:
- 📊 **Ver historial detallado**: Acceso a gráficos temporales de actividad y comportamiento
- 🔔 **Configurar alertas**: Definir umbrales personalizados para alertas específicas de ese individuo

#### Funcionalidades Avanzadas:

**Búsqueda y Filtrado**:
Campo de búsqueda que permite localizar individuos específicos por ID, útil en instalaciones con mayor número de animales.

**Exportación de Datos**:
Botón "Exportar" que permite generar reportes en formato de hoja de cálculo (CSV/Excel) con:
- Datos históricos de actividad
- Distribución temporal de comportamientos
- Métricas de bienestar calculadas
- Datos adecuados para análisis estadístico posterior

**Actualización Automática**:
El ícono de recarga indica actualización en tiempo real de los datos mediante conexión WebSocket, eliminando la necesidad de refrescar manualmente la interfaz.

---

## Flujo de Información del Sistema

### Captura y Procesamiento

1. **Adquisición de Video**: Las cámaras IP transmiten video continuamente mediante protocolo RTSP
2. **Detección Automática**: Algoritmos de visión por computador identifican y localizan hurones en cada frame
3. **Seguimiento Multi-Cámara**: El sistema correlaciona detecciones entre cámaras para mantener la identidad de cada individuo
4. **Clasificación Comportamental**: Modelos de aprendizaje profundo analizan patrones de movimiento y postura para clasificar comportamientos
5. **Almacenamiento y Visualización**: Los datos procesados se almacenan en base de datos y se presentan en las interfaces descritas

### Integración en el Flujo de Trabajo Veterinario

El sistema está diseñado para complementar, no reemplazar, la evaluación profesional:

- **Screening Inicial**: El sistema identifica automáticamente individuos con patrones anómalos
- **Priorización**: Las alertas permiten al veterinario enfocar atención en casos que requieren evaluación
- **Documentación Objetiva**: Genera registros cuantitativos de comportamiento útiles para diagnóstico
- **Seguimiento Longitudinal**: Facilita el monitoreo de cambios comportamentales a lo largo del tiempo
- **Investigación**: Proporciona datos estructurados para estudios etológicos y clínicos

---

## Beneficios para la Práctica Veterinaria

### Bienestar Animal
- **Monitoreo No Invasivo**: Observación continua sin necesidad de manipulación frecuente
- **Detección Temprana**: Identificación de cambios comportamentales sutiles que pueden preceder signos clínicos evidentes
- **Evaluación Nocturna**: Captura de patrones de comportamiento durante horas de menor supervisión humana

### Eficiencia Operacional
- **Automatización de Registro**: Reducción del tiempo dedicado a documentación manual
- **Alertas Inteligentes**: Notificación proactiva de situaciones que requieren atención
- **Accesibilidad Remota**: Posibilidad de supervisión desde ubicaciones externas al recinto

### Calidad de Datos
- **Objetividad**: Métricas cuantitativas independientes de interpretación subjetiva
- **Continuidad**: Registro ininterrumpido sin limitaciones de turnos humanos
- **Trazabilidad**: Cada observación vinculada a timestamp y cámara de origen

---

## Consideraciones Técnicas para la Implementación

### Requisitos de Hardware
- Cámaras IP con capacidad de transmisión RTSP
- Resolución mínima recomendada: 1280×720 (HD)
- Cobertura espacial: Mínimo 3 cámaras con ángulos complementarios
- Iluminación: Infrarrojo para monitoreo nocturno sin perturbar ciclo circadiano

### Procesamiento
- Servidor central con capacidad GPU para análisis en tiempo real
- Sistema de almacenamiento para registro de video y datos procesados
- Red local con ancho de banda suficiente para múltiples streams simultáneos

### Software
- Interfaz web accesible desde navegadores estándar
- Backend con APIs REST para integración con sistemas hospitalarios existentes
- Actualización en tiempo real mediante WebSocket

---

## Conclusión

Este sistema representa una herramienta de apoyo tecnológico que permite al profesional veterinario elevar la calidad del monitoreo animal mediante la automatización de tareas repetitivas de observación y registro, liberando tiempo para tareas de mayor valor clínico: diagnóstico, tratamiento y atención directa.

La combinación de visión por computador, aprendizaje automático e interfaces de usuario intuitivas crea un ecosistema que traduce datos de video complejos en información accionable, manteniendo al veterinario en el centro del proceso de toma de decisiones.

La implementación de este tipo de sistemas en contextos veterinarios y de investigación biomédica representa un avance hacia la medicina de precisión aplicada al cuidado animal, donde las decisiones se fundamentan en datos objetivos, continuos y de alta calidad temporal.

---

**Nota**: Las capturas de pantalla presentadas muestran el sistema en funcionamiento con datos simulados para propósitos de demostración. El sistema es configurable según las necesidades específicas de cada instalación y especie animal monitoreada.





