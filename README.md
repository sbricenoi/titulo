# 🐾 Ferret Multi-Camera Behavioral AI System

Sistema de monitoreo inteligente multi-cámara para análisis de comportamiento de hurones en tiempo real utilizando inteligencia artificial.

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![PyTorch](https://img.shields.io/badge/PyTorch-2.1.0-red.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-green.svg)
![Angular](https://img.shields.io/badge/Angular-17.0-red.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

</div>

## 📋 Tabla de Contenidos

- [Descripción General](#-descripción-general)
- [Componentes del Sistema](#-componentes-del-sistema)
- [Arquitectura](#-arquitectura)
- [Requisitos](#-requisitos)
- [Instalación Rápida](#-instalación-rápida)
- [Uso](#-uso)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Documentación](#-documentación)

## 🎯 Descripción General

Este proyecto integra tres componentes principales que trabajan juntos para proporcionar un sistema completo de monitoreo y análisis de comportamiento de hurones:

1. **Sistema de Grabación Continua** - Captura y almacena videos de múltiples cámaras Reolink
2. **Motor de Análisis IA** - Detecta, rastrea y clasifica comportamientos en tiempo real
3. **Dashboard Web** - Interfaz de administración y visualización de resultados

## 🧩 Componentes del Sistema

### 1️⃣ Sistema de Grabación a S3

**Ubicación:** `video-recording-system/`

- Captura continua desde cámaras Reolink vía RTSP
- Segmentación automática de videos (configurable)
- Upload automático a AWS S3
- Gestión de almacenamiento local con retención configurable
- Monitoreo y reinicio automático de procesos

**Tecnologías:**
- FFmpeg para captura y procesamiento
- Python (watchdog) para monitoreo de archivos
- AWS S3 para almacenamiento en la nube

### 2️⃣ Motor de Análisis IA

**Ubicación:** `main.py`, `ai/`, `core/`, `api/`

- **Detección:** YOLOv8 entrenado para detectar hurones
- **Tracking:** Seguimiento multi-objeto con Re-ID entre cámaras
- **Clasificación:** Identificación de comportamientos (juego, descanso, exploración, etc.)
- **Fusión Multi-Cámara:** Sincronización y fusión de datos de múltiples streams
- **API REST:** FastAPI para integración con frontend

**Tecnologías:**
- PyTorch + YOLOv8
- OpenCV para procesamiento de video
- FastAPI para API REST
- NumPy, SciPy para procesamiento de datos

### 3️⃣ Frontend Dashboard

**Ubicación:** `frontend/`

- Visualización de streams en tiempo real
- Administración de cámaras y configuraciones
- Dashboard de comportamientos detectados
- Interfaz para etiquetar y entrenar IA
- Visualización de métricas y estadísticas

**Tecnologías:**
- Angular 17
- TypeScript
- RxJS para manejo de streams
- Angular Material para UI

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                     Cámaras Reolink                        │
│                  (RTSP Streams 192.168.0.x)                │
└──────────┬──────────────────────────────────────┬───────────┘
           │                                      │
           v                                      v
┌──────────────────────┐            ┌──────────────────────────┐
│  Sistema Grabación   │            │    Motor Análisis IA     │
│  (video-recording)   │            │      (main.py)           │
│                      │            │                          │
│  • FFmpeg Recorder   │            │  • YOLOv8 Detector       │
│  • S3 Uploader       │───────────▶│  • Multi-Tracker         │
│  • Auto-restart      │   S3 URLs  │  • Behavior Classifier   │
└──────────┬───────────┘            │  • FastAPI Server        │
           │                        └────────┬─────────────────┘
           v                                 │
    ┌────────────┐                          │
    │   AWS S3   │                          │ REST API
    │ (Storage)  │                          │
    └────────────┘                          v
                                  ┌─────────────────────┐
                                  │  Frontend Angular   │
                                  │   (Dashboard)       │
                                  │                     │
                                  │  • Live Streams     │
                                  │  • Behavior Logs    │
                                  │  • Training UI      │
                                  └─────────────────────┘
```

## 💻 Requisitos

### Software Base
- **Python:** 3.9 o superior
- **FFmpeg:** 4.0 o superior
- **Node.js:** 18+ (para frontend)
- **Sistema Operativo:** macOS, Linux, o Windows

### Cuentas/Servicios
- **AWS Account:** Para S3 storage (credenciales IAM con acceso a S3)
- **Cámaras Reolink:** Con RTSP habilitado

### Hardware Recomendado
- **RAM:** 8GB mínimo (16GB recomendado)
- **CPU:** 4 cores mínimo (8+ recomendado para análisis IA)
- **GPU:** Opcional pero recomendado para YOLOv8 (CUDA compatible)
- **Almacenamiento:** 50GB+ libre para videos locales

## 🚀 Instalación Rápida

### 1. Clonar Repositorio

```bash
git clone <repository-url>
cd titulo
```

### 2. Sistema de Grabación

```bash
cd video-recording-system
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configurar .env con credenciales AWS y URLs de cámaras
cp .env.example .env
nano .env  # Editar con tus datos
```

### 3. Motor de Análisis IA

```bash
cd ..  # Volver a raíz
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurar config.py con tus parámetros
nano config.py
```

### 4. Frontend (Opcional)

```bash
cd frontend
npm install
```

**Ver más detalles:** Consulta `SETUP.md` para instrucciones completas.

## 🎮 Uso

### Iniciar Sistema de Grabación

```bash
cd video-recording-system
./INICIAR_SISTEMA_FINAL.sh
```

El sistema comenzará a grabar desde las cámaras configuradas y subirá automáticamente a S3.

### Detener Sistema de Grabación

```bash
./stop_recorder_robusto.sh
```

### Reiniciar con Limpieza

```bash
./REINICIAR_SISTEMA_LIMPIO.sh
```

### Iniciar Motor de Análisis IA

```bash
# Desde raíz del proyecto
python main.py
```

### Iniciar Frontend

```bash
cd frontend
npm start
# Abre http://localhost:4200
```

## 📂 Estructura del Proyecto

```
titulo/
├── video-recording-system/     # Sistema de grabación continua
│   ├── services/
│   │   ├── video_recorder.py   # Grabación FFmpeg
│   │   ├── s3_uploader.py      # Upload a S3
│   │   └── recorder_config.py  # Configuración
│   ├── .env                     # Credenciales y config
│   ├── INICIAR_SISTEMA_FINAL.sh
│   ├── stop_recorder_robusto.sh
│   └── REINICIAR_SISTEMA_LIMPIO.sh
│
├── ai/                          # Módulos de IA
│   ├── detector.py              # YOLOv8 detector
│   ├── tracker.py               # Multi-camera tracker
│   ├── behavior_model.py        # Clasificador de comportamientos
│   └── trainer.py               # Entrenamiento de modelos
│
├── core/                        # Motor del sistema
│   ├── camera_manager.py        # Gestión de cámaras
│   ├── fusion_engine.py         # Fusión multi-cámara
│   └── sync_engine.py           # Sincronización temporal
│
├── api/                         # API REST
│   ├── main.py                  # FastAPI server
│   ├── cameras_endpoints.py     # Endpoints de cámaras
│   ├── system_bridge.py         # Bridge sistema-API
│   └── hls_server.py            # Streaming HLS
│
├── frontend/                    # Dashboard Angular
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/
│   │   │   ├── services/
│   │   │   └── models/
│   │   └── assets/
│   └── package.json
│
├── utils/                       # Utilidades compartidas
├── data/                        # Datos (logs, modelos, videos)
│   ├── logs/
│   ├── models/
│   ├── training/
│   └── videos/
│
├── main.py                      # Punto de entrada análisis IA
├── config.py                    # Configuración global
├── requirements.txt             # Dependencias Python
├── .cursorrules                 # Reglas de desarrollo
├── README.md                    # Este archivo
└── SETUP.md                     # Guía de instalación detallada
```

## 📚 Documentación

- **SETUP.md** - Guía completa de instalación y configuración
- **video-recording-system/README.md** - Documentación del sistema de grabación
- **.cursorrules** - Principios y reglas de desarrollo del proyecto
- **PLAN_LIMPIEZA_PROYECTO.md** - Historial de limpieza y organización

### Documentación Código

Cada módulo incluye docstrings detallados. Para generar documentación HTML:

```bash
# TODO: Agregar herramienta de generación de docs
```

## 🤝 Contribución

Este es un proyecto privado de investigación. Para contribuciones:

1. Seguir las reglas definidas en `.cursorrules`
2. Mantener Clean Code principles
3. No alucinar funcionalidad - analizar código existente primero
4. Probar cada cambio inmediatamente

## 📝 Licencia

MIT License - Ver archivo LICENSE para detalles.

## 🙋 Soporte

Para preguntas o problemas:
- Revisar documentación en `SETUP.md`
- Verificar logs en `data/logs/`
- Consultar `.cursorrules` para principios de desarrollo

---

**Desarrollado con ❤️ para el monitoreo inteligente de hurones**
