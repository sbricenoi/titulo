# Guía de Textos para Tesis
## Documentos Preparados para Presentación del Sistema

He preparado varios documentos con diferentes niveles de detalle para que puedas elegir el más apropiado según la sección de tu tesis:

---

## 📄 Documentos Disponibles

### 1. **PRESENTACION_TESIS.md** ⭐ RECOMENDADO PARA CAPÍTULO COMPLETO
**Extensión:** ~3,500 palabras  
**Nivel de detalle:** Completo y exhaustivo  
**Mejor uso:** Capítulo de "Herramientas Tecnológicas" o "Metodología de Monitoreo"

**Contenido:**
- Resumen ejecutivo del sistema
- Contexto y justificación veterinaria
- Descripción detallada de ambas interfaces (Cámaras + Individuos)
- Flujo de información y procesamiento
- Beneficios para práctica veterinaria (bienestar animal, eficiencia, calidad de datos)
- Consideraciones técnicas de implementación
- Conclusiones

**Cuándo usar:** Si la tecnología es un componente significativo de tu trabajo o si necesitas justificar detalladamente la metodología de recopilación de datos.

---

### 2. **DESCRIPCION_VISTAS_BREVE.md** ⭐ RECOMENDADO PARA METODOLOGÍA
**Extensión:** ~1,200 palabras  
**Nivel de detalle:** Moderado, enfocado  
**Mejor uso:** Sección de "Metodología" o "Materiales y Métodos"

**Contenido:**
- Descripción concisa de ambas vistas (Cámaras + Individuos)
- Explicación de funcionalidad de cada componente
- Flujo de trabajo e integración clínica
- Ventajas del enfoque multi-cámara
- Menos detalle técnico, más enfoque en aplicación práctica

**Cuándo usar:** Cuando necesitas explicar el sistema brevemente dentro de una sección más amplia de metodología, sin dedicar un capítulo completo.

---

### 3. **PIES_DE_FIGURA.md** ⭐ RECOMENDADO PARA CAPTURAS DE PANTALLA
**Extensión:** Varias opciones (corta/media/larga)  
**Nivel de detalle:** Descriptivo específico de las imágenes  
**Mejor uso:** Como pie de figura directamente bajo las capturas de pantalla

**Contenido:**
Tres versiones para cada figura:
- **Versión Corta** (~30 palabras): Para espacios reducidos
- **Versión Media** (~80 palabras): Estándar para tesis
- **Versión Larga** (~150 palabras): Muy descriptiva

Más:
- Descripción técnica complementaria (opcional)
- Recomendaciones de uso según contexto

**Cuándo usar:** Como texto que acompaña directamente a cada imagen en tu documento.

---

### 4. **TEXTOS_TESIS_README.md** (este archivo)
**Guía de navegación** para elegir qué documento usar.

---

## 🎯 Guía Rápida de Selección

| Necesito... | Usar documento... | Ubicación en tesis |
|-------------|-------------------|-------------------|
| Capítulo completo sobre el sistema | PRESENTACION_TESIS.md | Cap. 3 o 4 |
| Párrafos para metodología | DESCRIPCION_VISTAS_BREVE.md | Cap. 2: Materiales y Métodos |
| Texto bajo las imágenes | PIES_DE_FIGURA.md (versión media) | Donde estén las figuras |
| Presentación oral | DESCRIPCION_VISTAS_BREVE.md + PIES_DE_FIGURA.md corto | Diapositivas |

---

## 📋 Estructura Sugerida para la Tesis

### Opción A: Tecnología como Apoyo (menos énfasis técnico)

```
Capítulo 2: Materiales y Métodos
├── 2.1 Sujetos de Estudio
├── 2.2 Instalaciones y Condiciones de Alojamiento
├── 2.3 Sistema de Monitoreo Automatizado
│   └── [Usar: DESCRIPCION_VISTAS_BREVE.md]
├── 2.4 Variables Evaluadas
└── 2.5 Análisis Estadístico

[En el cuerpo del texto, donde van las imágenes]
Figura X: [Captura de pantalla de cámaras]
[Usar: PIES_DE_FIGURA.md - Versión Media - Figura 1]

Figura Y: [Captura de pantalla de individuos]
[Usar: PIES_DE_FIGURA.md - Versión Media - Figura 2]
```

### Opción B: Tecnología como Componente Principal (más énfasis técnico)

```
Capítulo 3: Herramientas Tecnológicas de Monitoreo
└── [Usar: PRESENTACION_TESIS.md completo]

[Dentro del capítulo, donde van las imágenes]
Figura 3.1: Panel Multi-Cámara
[Usar: PIES_DE_FIGURA.md - Versión Larga - Figura 1]

Figura 3.2: Panel de Análisis Individual
[Usar: PIES_DE_FIGURA.md - Versión Larga - Figura 2]
```

---

## ✏️ Personalización Recomendada

Los textos están escritos en lenguaje formal semi-técnico apropiado para veterinaria. Puedes:

### Adaptar según tu caso específico:
- **Número de animales:** Los ejemplos muestran 5 hurones, ajusta si usaste otro número
- **Duración del estudio:** Añade información sobre el período de monitoreo
- **Variables específicas:** Enfatiza los comportamientos más relevantes para tu hipótesis

### Integrar con tu marco teórico:
- Conecta con literatura sobre bienestar animal
- Referencia estudios previos de etología de hurones
- Vincula con objetivos específicos de tu investigación

### Agregar contexto institucional:
- Menciona dónde se realizó el estudio
- Indica aprobaciones éticas obtenidas
- Referencia protocolos de cuidado animal seguidos

---

## 🔑 Palabras Clave Incluidas

Los textos incluyen términos relevantes para búsqueda académica:
- Monitoreo no invasivo
- Análisis comportamental automatizado
- Bienestar animal
- Visión por computador aplicada
- Re-identificación individual
- Etología aplicada
- Detección temprana de anomalías
- Sistema multi-cámara

---

## 📝 Checklist de Integración

Antes de incluir en tu tesis, verifica:

- [ ] He elegido el documento apropiado para cada sección
- [ ] He adaptado el número de animales y duración del estudio
- [ ] Las figuras están numeradas correlativa mente
- [ ] Los pies de figura coinciden con las capturas de pantalla actuales
- [ ] He conectado el texto con mi marco teórico
- [ ] He mencionado aprobaciones éticas si corresponde
- [ ] El nivel técnico es apropiado para mi audiencia (veterinarios)
- [ ] He citado fuentes técnicas si es necesario (ver referencias en arquitectura.md)

---

## 🎓 Recomendaciones Finales

### Para defensa oral:
- Usa la **versión breve** en diapositivas
- Ten la **versión completa** como referencia para preguntas
- Enfatiza **beneficios clínicos** más que detalles técnicos

### Para publicación posterior:
- La **versión media** funciona bien para journals veterinarios
- La **versión completa** es apropiada para journals de tecnología biomédica

### Para tribunal evaluador:
- Si hay veterinarios: énfasis en aplicación clínica y bienestar animal
- Si hay ingenieros/tecnólogos: puedes usar versión más técnica y referenciar arquitectura.md

---

## 📞 Modificaciones Adicionales

Si necesitas:
- Versión aún más técnica (con algoritmos específicos, métricas de rendimiento)
- Versión más clínica (con ejemplos de casos, correlación con signos clínicos)
- Enfoque en validación del sistema (precisión, sensibilidad, especificidad)
- Comparación con métodos tradicionales de observación

Puedo generar textos adicionales según tus necesidades específicas.

---

**Última actualización:** Octubre 2025  
**Versión de sistema documentada:** v1.0 (Sistema con datos dummy para demostración)





