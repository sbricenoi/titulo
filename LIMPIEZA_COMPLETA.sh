#!/bin/bash
# =====================================================================
# Script de Limpieza Completa del Sistema
# =====================================================================
# Este script elimina TODOS los datos y videos, dejando solo el código
# =====================================================================

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║     ⚠️  LIMPIEZA COMPLETA DEL SISTEMA  ⚠️               ║${NC}"
echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Directorio base
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$BASE_DIR"

# =====================================================================
# PASO 1: DETENER PROCESOS
# =====================================================================
echo -e "${BLUE}📍 PASO 1: Deteniendo procesos activos...${NC}"
echo ""

# Procesos a detener
PROCESSES=(
    "video_recorder.py"
    "s3_uploader.py"
    "video_analyzer"
    "ffmpeg.*rtsp"
)

for process in "${PROCESSES[@]}"; do
    if pgrep -f "$process" > /dev/null; then
        echo -e "   ${YELLOW}⚠${NC}  Deteniendo: $process"
        pkill -f "$process" 2>/dev/null || true
        sleep 1
    fi
done

# Verificar que no haya procesos
sleep 2
REMAINING=$(ps aux | grep -E "video_recorder|s3_uploader|video_analyzer|ffmpeg.*rtsp" | grep -v grep | wc -l)

if [ "$REMAINING" -gt 0 ]; then
    echo -e "   ${RED}✗${NC} Algunos procesos aún activos. Forzando..."
    pkill -9 -f "video_recorder" 2>/dev/null || true
    pkill -9 -f "s3_uploader" 2>/dev/null || true
    pkill -9 -f "video_analyzer" 2>/dev/null || true
    pkill -9 -f "ffmpeg.*rtsp" 2>/dev/null || true
    sleep 1
fi

echo -e "   ${GREEN}✓${NC} Todos los procesos detenidos"
echo ""

# =====================================================================
# PASO 2: MOSTRAR QUÉ SE VA A ELIMINAR
# =====================================================================
echo -e "${BLUE}📍 PASO 2: Calculando tamaño de datos a eliminar...${NC}"
echo ""

# Función para calcular tamaño
calculate_size() {
    if [ -d "$1" ] || [ -f "$1" ]; then
        du -sh "$1" 2>/dev/null | awk '{print $1}'
    else
        echo "0B"
    fi
}

# Videos de grabación
VIDEOS_DIR="video-recording-system/data/videos/recordings"
VIDEOS_SIZE=$(calculate_size "$VIDEOS_DIR")

# Frames para clasificación
FRAMES_DIR="data/frames_for_classification"
FRAMES_SIZE=$(calculate_size "$FRAMES_DIR")

# Resultados de análisis
ANALYSIS_DIR="data/smart_analysis_results"
ANALYSIS_SIZE=$(calculate_size "$ANALYSIS_DIR")

# Análisis tiempo real
REALTIME_DIR="data/realtime_analysis"
REALTIME_SIZE=$(calculate_size "$REALTIME_DIR")

# Dataset YOLO (opcional)
DATASET_DIR="data/yolo_dataset"
DATASET_SIZE=$(calculate_size "$DATASET_DIR")

# Runs de entrenamiento (opcional)
RUNS_DIR="runs"
RUNS_SIZE=$(calculate_size "$RUNS_DIR")

# Logs
LOGS_DIR="logs"
LOGS_SIZE=$(calculate_size "$LOGS_DIR")

# Base de datos
DB_FILE="data/classifications.db"
DB_SIZE=$(calculate_size "$DB_FILE")

echo -e "   ${YELLOW}Se eliminarán:${NC}"
echo ""
echo -e "   📹 Videos de grabación:        ${RED}$VIDEOS_SIZE${NC}  ($VIDEOS_DIR)"
echo -e "   🖼️  Frames clasificación:      ${RED}$FRAMES_SIZE${NC}  ($FRAMES_DIR)"
echo -e "   📊 Análisis smart:             ${RED}$ANALYSIS_SIZE${NC}  ($ANALYSIS_DIR)"
echo -e "   📈 Análisis tiempo real:       ${RED}$REALTIME_SIZE${NC}  ($REALTIME_DIR)"
echo -e "   📦 Dataset YOLO:               ${RED}$DATASET_SIZE${NC}  ($DATASET_DIR)"
echo -e "   🏋️  Runs entrenamiento:        ${RED}$RUNS_SIZE${NC}  ($RUNS_DIR)"
echo -e "   📝 Logs:                       ${RED}$LOGS_SIZE${NC}  ($LOGS_DIR)"
echo -e "   🗄️  Base de datos:             ${RED}$DB_SIZE${NC}  ($DB_FILE)"
echo ""
echo -e "   ${YELLOW}Se mantendrán:${NC}"
echo ""
echo -e "   ${GREEN}✓${NC} Código fuente (Python, TypeScript, etc.)"
echo -e "   ${GREEN}✓${NC} Modelo entrenado (models/ferret_detector_v1.pt)"
echo -e "   ${GREEN}✓${NC} Configuraciones del sistema"
echo -e "   ${GREEN}✓${NC} Virtual environment"
echo -e "   ${GREEN}✓${NC} Documentación (.md files)"
echo ""

# =====================================================================
# CONFIRMACIÓN
# =====================================================================
echo -e "${RED}⚠️  ADVERTENCIA: Esta acción NO se puede deshacer${NC}"
echo ""
read -p "¿Estás SEGURO de eliminar todo? Escribe 'SI ELIMINAR' para confirmar: " CONFIRM

if [ "$CONFIRM" != "SI ELIMINAR" ]; then
    echo -e "${YELLOW}Cancelado por el usuario${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}📍 PASO 3: Eliminando datos...${NC}"
echo ""

# =====================================================================
# PASO 3: ELIMINAR DATOS
# =====================================================================

# Videos
if [ -d "$VIDEOS_DIR" ]; then
    echo -e "   🗑️  Eliminando videos..."
    rm -rf "$VIDEOS_DIR"/*
    echo -e "   ${GREEN}✓${NC} Videos eliminados"
fi

# Frames
if [ -d "$FRAMES_DIR" ]; then
    echo -e "   🗑️  Eliminando frames..."
    rm -rf "$FRAMES_DIR"/*
    echo -e "   ${GREEN}✓${NC} Frames eliminados"
fi

# Análisis smart
if [ -d "$ANALYSIS_DIR" ]; then
    echo -e "   🗑️  Eliminando análisis smart..."
    rm -rf "$ANALYSIS_DIR"/*
    echo -e "   ${GREEN}✓${NC} Análisis eliminados"
fi

# Análisis tiempo real
if [ -d "$REALTIME_DIR" ]; then
    echo -e "   🗑️  Eliminando análisis tiempo real..."
    rm -rf "$REALTIME_DIR"/*
    echo -e "   ${GREEN}✓${NC} Análisis tiempo real eliminados"
fi

# Dataset YOLO
if [ -d "$DATASET_DIR" ]; then
    echo -e "   🗑️  Eliminando dataset YOLO..."
    rm -rf "$DATASET_DIR"
    echo -e "   ${GREEN}✓${NC} Dataset eliminado"
fi

# Runs de entrenamiento
if [ -d "$RUNS_DIR" ]; then
    echo -e "   🗑️  Eliminando runs de entrenamiento..."
    rm -rf "$RUNS_DIR"
    echo -e "   ${GREEN}✓${NC} Runs eliminados"
fi

# Logs
if [ -d "$LOGS_DIR" ]; then
    echo -e "   🗑️  Limpiando logs..."
    rm -rf "$LOGS_DIR"/*
    echo -e "   ${GREEN}✓${NC} Logs limpiados"
fi

# Base de datos
if [ -f "$DB_FILE" ]; then
    echo -e "   🗑️  Eliminando base de datos..."
    rm -f "$DB_FILE"
    echo -e "   ${GREEN}✓${NC} Base de datos eliminada"
fi

# Limpiar archivos temporales Python
echo -e "   🗑️  Limpiando archivos temporales..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
echo -e "   ${GREEN}✓${NC} Archivos temporales eliminados"

echo ""

# =====================================================================
# PASO 4: RECREAR ESTRUCTURA
# =====================================================================
echo -e "${BLUE}📍 PASO 4: Recreando estructura de directorios...${NC}"
echo ""

# Recrear directorios necesarios
mkdir -p "$VIDEOS_DIR"
mkdir -p "$FRAMES_DIR"
mkdir -p "$ANALYSIS_DIR"
mkdir -p "$REALTIME_DIR"
mkdir -p "$LOGS_DIR"
mkdir -p "data"
mkdir -p "models"

echo -e "   ${GREEN}✓${NC} Estructura recreada"
echo ""

# =====================================================================
# RESUMEN
# =====================================================================
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║            ✅ LIMPIEZA COMPLETADA                         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📊 ESTADO DEL SISTEMA:${NC}"
echo ""
echo -e "   ${GREEN}✓${NC} Procesos detenidos"
echo -e "   ${GREEN}✓${NC} Videos eliminados"
echo -e "   ${GREEN}✓${NC} Datos de análisis eliminados"
echo -e "   ${GREEN}✓${NC} Logs limpiados"
echo -e "   ${GREEN}✓${NC} Estructura recreada"
echo ""
echo -e "${BLUE}📁 DIRECTORIOS LIMPIOS:${NC}"
echo ""
ls -lh "$VIDEOS_DIR" 2>/dev/null | tail -5
echo ""
echo -e "${BLUE}✨ Sistema listo para empezar de nuevo${NC}"
echo ""
echo -e "${YELLOW}Para iniciar nuevamente:${NC}"
echo -e "   ./START_RECORDING_WITH_TRACKING.sh"
echo ""
