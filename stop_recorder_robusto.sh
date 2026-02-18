#!/bin/bash
# Script ROBUSTO para detener el sistema de grabación

cd /Users/sbriceno/Documents/projects/titulo/video-recording-system

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🛑 Deteniendo Sistema de Grabación${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Función para detener procesos con reintentos
stop_process() {
    local name=$1
    local pattern=$2
    
    echo -e "${YELLOW}🛑 Deteniendo $name...${NC}"
    
    # Buscar PIDs
    local pids=$(ps aux 2>/dev/null | grep "$pattern" | grep -v grep | awk '{print $2}' | xargs)
    
    if [ -z "$pids" ]; then
        echo -e "   ${GREEN}✓${NC} $name: Ya detenido"
        return 0
    fi
    
    echo -e "   PIDs encontrados: $pids"
    
    # Intento 1: SIGTERM (graceful)
    for pid in $pids; do
        kill $pid 2>/dev/null || true
    done
    
    sleep 2
    
    # Verificar si se detuvo
    local remaining=$(ps aux 2>/dev/null | grep "$pattern" | grep -v grep | awk '{print $2}' | xargs)
    if [ -z "$remaining" ]; then
        echo -e "   ${GREEN}✓${NC} $name detenido correctamente"
        return 0
    fi
    
    # Intento 2: SIGKILL (force)
    echo -e "   ${YELLOW}⚠️${NC}  Procesos no respondieron, forzando..."
    for pid in $remaining; do
        kill -9 $pid 2>/dev/null || true
    done
    
    sleep 1
    
    # Verificación final
    local still_running=$(ps aux 2>/dev/null | grep "$pattern" | grep -v grep | awk '{print $2}' | xargs)
    if [ -z "$still_running" ]; then
        echo -e "   ${GREEN}✓${NC} $name detenido (forzado)"
        return 0
    else
        echo -e "   ${RED}✗${NC} $name: No se pudo detener completamente"
        return 1
    fi
}

# Detener servicios en orden
stop_process "FFmpeg" "ffmpeg.*camera"
echo ""
stop_process "Video Recorder" "video_recorder.py"
echo ""
stop_process "S3 Uploader" "s3_uploader.py"

echo ""
echo -e "${BLUE}========================================${NC}"

# Verificación final
RECORDER_RUNNING=$(ps aux 2>/dev/null | grep "video_recorder.py" | grep -v grep | wc -l | xargs)
UPLOADER_RUNNING=$(ps aux 2>/dev/null | grep "s3_uploader.py" | grep -v grep | wc -l | xargs)
FFMPEG_RUNNING=$(ps aux 2>/dev/null | grep "ffmpeg.*camera" | grep -v grep | wc -l | xargs)

TOTAL_RUNNING=$((RECORDER_RUNNING + UPLOADER_RUNNING + FFMPEG_RUNNING))

if [ $TOTAL_RUNNING -eq 0 ]; then
    echo -e "${GREEN}✅ Todos los servicios detenidos correctamente${NC}"
else
    echo -e "${RED}⚠️  Algunos procesos aún están corriendo:${NC}"
    [ $RECORDER_RUNNING -gt 0 ] && echo -e "   - Video Recorder: $RECORDER_RUNNING proceso(s)"
    [ $UPLOADER_RUNNING -gt 0 ] && echo -e "   - S3 Uploader: $UPLOADER_RUNNING proceso(s)"
    [ $FFMPEG_RUNNING -gt 0 ] && echo -e "   - FFmpeg: $FFMPEG_RUNNING proceso(s)"
fi

echo -e "${BLUE}========================================${NC}"
echo ""

# Limpiar PIDs temporales
rm -f /tmp/recorder.pid /tmp/uploader.pid 2>/dev/null || true

echo -e "${YELLOW}📂 Archivos locales se mantienen en:${NC}"
echo -e "   data/videos/recordings/"
echo -e "   data/videos/uploaded/"
echo ""
echo -e "${YELLOW}📋 Logs disponibles en:${NC}"
echo -e "   data/logs/video_recorder.log"
echo -e "   data/logs/s3_uploader.log"
echo ""
