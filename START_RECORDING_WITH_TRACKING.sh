#!/bin/bash
# =====================================================================
# Sistema de Grabación con Tracking Multi-Individuo
# =====================================================================
# Este script inicia el sistema completo:
# 1. Grabación continua de RTSP
# 2. Upload automático a S3
# 3. Análisis en tiempo real con YOLOv8 entrenado
# 4. Tracking de múltiples individuos
# 5. Guardado de estadísticas por individuo
# =====================================================================

set -e

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}🚀 SISTEMA DE GRABACIÓN CON TRACKING${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Directorio base
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$BASE_DIR"

# Activar virtual environment
if [ -d "venv" ]; then
    echo -e "${GREEN}✓${NC} Activando virtual environment..."
    source venv/bin/activate
else
    echo -e "${YELLOW}⚠${NC}  Virtual environment no encontrado"
    exit 1
fi

# Verificar modelo entrenado
MODEL_PATH="models/ferret_detector_v1.pt"

if [ -f "$MODEL_PATH" ]; then
    echo -e "${GREEN}✓${NC} Modelo entrenado encontrado: $MODEL_PATH"
    USE_TRAINED_MODEL=true
else
    echo -e "${YELLOW}⚠${NC}  Modelo entrenado no encontrado, usando base"
    USE_TRAINED_MODEL=false
fi

echo ""
echo -e "${BLUE}📋 COMPONENTES A INICIAR:${NC}"
echo -e "   1. Sistema de grabación RTSP"
echo -e "   2. Uploader a S3"
echo -e "   3. Analizador en tiempo real con tracking"
echo ""

# Preguntar confirmación
read -p "¿Iniciar sistema completo? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelado"
    exit 1
fi

echo ""
echo -e "${BLUE}🎬 Iniciando componentes...${NC}"
echo ""

# 1. Verificar que no haya procesos corriendo
echo -e "${GREEN}1.${NC} Verificando procesos existentes..."

if pgrep -f "video_recorder.py" > /dev/null; then
    echo -e "${YELLOW}   ⚠  video_recorder.py ya está corriendo${NC}"
    read -p "   ¿Detenerlo y reiniciar? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pkill -f "video_recorder.py"
        sleep 2
    else
        echo "   Manteniendo proceso existente"
    fi
fi

if pgrep -f "s3_uploader.py" > /dev/null; then
    echo -e "${YELLOW}   ⚠  s3_uploader.py ya está corriendo${NC}"
    read -p "   ¿Detenerlo y reiniciar? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pkill -f "s3_uploader.py"
        sleep 2
    else
        echo "   Manteniendo proceso existente"
    fi
fi

echo ""

# 2. Iniciar grabación de video
echo -e "${GREEN}2.${NC} Iniciando grabación RTSP..."

cd video-recording-system

if [ ! -f "video_recorder.py" ]; then
    echo -e "${YELLOW}   ✗ video_recorder.py no encontrado${NC}"
    exit 1
fi

nohup python3 video_recorder.py > ../logs/recorder.log 2>&1 &
RECORDER_PID=$!
echo -e "   ✓ Grabación iniciada (PID: $RECORDER_PID)"

sleep 3

# 3. Iniciar uploader S3
echo -e "${GREEN}3.${NC} Iniciando uploader a S3..."

if [ ! -f "services/s3_uploader.py" ]; then
    echo -e "${YELLOW}   ✗ s3_uploader.py no encontrado${NC}"
    exit 1
fi

nohup python3 services/s3_uploader.py > ../logs/uploader.log 2>&1 &
UPLOADER_PID=$!
echo -e "   ✓ Uploader iniciado (PID: $UPLOADER_PID)"

sleep 2

cd ..

# 4. Iniciar analizador en tiempo real (opcional)
echo ""
echo -e "${GREEN}4.${NC} Analizador en tiempo real con tracking..."
echo -e "   ${YELLOW}Nota:${NC} El análisis en tiempo real es intensivo en CPU"

read -p "   ¿Iniciar análisis en tiempo real? (y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    nohup python3 video-recording-system/services/video_analyzer_realtime.py > logs/analyzer.log 2>&1 &
    ANALYZER_PID=$!
    echo -e "   ✓ Analizador iniciado (PID: $ANALYZER_PID)"
else
    echo -e "   ○ Análisis en tiempo real omitido"
    ANALYZER_PID=""
fi

echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}✅ SISTEMA INICIADO CORRECTAMENTE${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo -e "${BLUE}📊 ESTADO:${NC}"
echo -e "   • Grabación:     PID $RECORDER_PID"
echo -e "   • Uploader S3:   PID $UPLOADER_PID"

if [ -n "$ANALYZER_PID" ]; then
    echo -e "   • Analizador:    PID $ANALYZER_PID"
fi

echo ""
echo -e "${BLUE}📁 LOGS:${NC}"
echo -e "   • Grabación:     logs/recorder.log"
echo -e "   • Uploader:      logs/uploader.log"

if [ -n "$ANALYZER_PID" ]; then
    echo -e "   • Analizador:    logs/analyzer.log"
fi

echo ""
echo -e "${BLUE}🎯 DATOS:${NC}"
echo -e "   • Videos:        video-recording-system/data/videos/recordings/"
echo -e "   • Análisis:      data/realtime_analysis/"
echo ""
echo -e "${YELLOW}💡 COMANDOS ÚTILES:${NC}"
echo -e "   • Ver logs grabación:    tail -f logs/recorder.log"
echo -e "   • Ver logs uploader:     tail -f logs/uploader.log"

if [ -n "$ANALYZER_PID" ]; then
    echo -e "   • Ver logs analizador:   tail -f logs/analyzer.log"
fi

echo -e "   • Ver procesos:          ps aux | grep python"
echo -e "   • Detener todo:          pkill -f 'video_recorder|s3_uploader|video_analyzer'"
echo ""
echo -e "${GREEN}Sistema corriendo en background...${NC}"
echo ""
