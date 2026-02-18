#!/bin/bash
# Script de monitoreo del sistema de grabación de video
#
# Muestra el estado actual del sistema, procesos, archivos y uso de recursos
#
# Uso: ./monitor.sh
#
# Autor: Sistema de Monitoreo de Hurones
# Fecha: 2026-01-24

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Directorio del proyecto (ajustar si es necesario)
PROJECT_DIR="${PROJECT_DIR:-/home/ubuntu/video-recording-system}"

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}           📊 MONITOREO DEL SISTEMA DE GRABACIÓN               ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}📅 Fecha: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo ""

# ==================== SERVICIOS ====================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔧 SERVICIOS SYSTEMD${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Video Recorder
if systemctl is-active --quiet video-recorder; then
    echo -e "  ${GREEN}✓ video-recorder: ACTIVO${NC}"
    RECORDER_PID=$(systemctl show -p MainPID video-recorder | cut -d= -f2)
    if [ "$RECORDER_PID" != "0" ]; then
        echo -e "    PID: $RECORDER_PID"
    fi
else
    echo -e "  ${RED}✗ video-recorder: INACTIVO${NC}"
fi

# S3 Uploader
if systemctl is-active --quiet s3-uploader; then
    echo -e "  ${GREEN}✓ s3-uploader: ACTIVO${NC}"
    UPLOADER_PID=$(systemctl show -p MainPID s3-uploader | cut -d= -f2)
    if [ "$UPLOADER_PID" != "0" ]; then
        echo -e "    PID: $UPLOADER_PID"
    fi
else
    echo -e "  ${RED}✗ s3-uploader: INACTIVO${NC}"
fi

echo ""

# ==================== PROCESOS FFMPEG ====================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🎥 PROCESOS FFMPEG${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

FFMPEG_COUNT=$(pgrep -c ffmpeg 2>/dev/null || echo "0")
echo -e "  Procesos corriendo: ${GREEN}$FFMPEG_COUNT${NC}"

if [ "$FFMPEG_COUNT" -gt 0 ]; then
    echo ""
    echo "  Detalles:"
    ps aux | grep "[f]fmpeg" | awk '{printf "    PID: %-6s CPU: %-5s MEM: %-5s\n", $2, $3"%", $4"%"}'
fi

echo ""

# ==================== ESPACIO EN DISCO ====================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}💾 ESPACIO EN DISCO${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ -d "$PROJECT_DIR/data/videos" ]; then
    df -h "$PROJECT_DIR/data/videos" | tail -n 1 | awk '{
        printf "  Tamaño: %s | Usado: %s | Disponible: %s | Uso: %s\n", $2, $3, $4, $5
    }'
    
    # Advertencia si el uso es > 80%
    DISK_USAGE=$(df "$PROJECT_DIR/data/videos" | tail -n 1 | awk '{print $5}' | sed 's/%//')
    if [ "$DISK_USAGE" -gt 80 ]; then
        echo -e "  ${RED}⚠️  ADVERTENCIA: Uso de disco mayor al 80%${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠️  Directorio no encontrado: $PROJECT_DIR/data/videos${NC}"
fi

echo ""

# ==================== ARCHIVOS LOCALES ====================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📁 ARCHIVOS LOCALES${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ -d "$PROJECT_DIR/data/videos/recordings" ]; then
    RECORDINGS_COUNT=$(find "$PROJECT_DIR/data/videos/recordings" -name "*.mp4" 2>/dev/null | wc -l)
    RECORDINGS_SIZE=$(du -sh "$PROJECT_DIR/data/videos/recordings" 2>/dev/null | awk '{print $1}')
    echo -e "  📹 Recordings:  ${GREEN}$RECORDINGS_COUNT${NC} archivos (${RECORDINGS_SIZE})"
else
    echo -e "  ${YELLOW}⚠️  Directorio recordings/ no encontrado${NC}"
fi

if [ -d "$PROJECT_DIR/data/videos/uploaded" ]; then
    UPLOADED_COUNT=$(find "$PROJECT_DIR/data/videos/uploaded" -name "*.mp4" 2>/dev/null | wc -l)
    UPLOADED_SIZE=$(du -sh "$PROJECT_DIR/data/videos/uploaded" 2>/dev/null | awk '{print $1}')
    echo -e "  ☁️  Uploaded:    ${CYAN}$UPLOADED_COUNT${NC} archivos (${UPLOADED_SIZE})"
else
    echo -e "  ${YELLOW}⚠️  Directorio uploaded/ no encontrado${NC}"
fi

echo ""

# ==================== ÚLTIMOS ARCHIVOS ====================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📄 ÚLTIMOS ARCHIVOS (5 más recientes)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ -d "$PROJECT_DIR/data/videos/recordings" ]; then
    RECENT_FILES=$(find "$PROJECT_DIR/data/videos/recordings" -name "*.mp4" -type f -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -5)
    
    if [ -n "$RECENT_FILES" ]; then
        echo "$RECENT_FILES" | while read -r timestamp filepath; do
            filename=$(basename "$filepath")
            filesize=$(du -h "$filepath" 2>/dev/null | awk '{print $1}')
            filedate=$(date -d @"${timestamp%.*}" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || date -r "${timestamp%.*}" '+%Y-%m-%d %H:%M:%S' 2>/dev/null)
            echo -e "  ${filedate} | ${filesize} | ${filename}"
        done
    else
        echo "  No hay archivos"
    fi
else
    echo -e "  ${YELLOW}⚠️  Directorio no encontrado${NC}"
fi

echo ""

# ==================== LOGS RECIENTES ====================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📝 LOGS RECIENTES (últimas 5 líneas)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo ""
echo -e "${CYAN}Video Recorder:${NC}"
if [ -f "$PROJECT_DIR/data/logs/recorder.log" ]; then
    tail -n 3 "$PROJECT_DIR/data/logs/recorder.log" 2>/dev/null | sed 's/^/  /'
else
    echo "  (log no encontrado)"
fi

echo ""
echo -e "${CYAN}S3 Uploader:${NC}"
if [ -f "$PROJECT_DIR/data/logs/uploader.log" ]; then
    tail -n 3 "$PROJECT_DIR/data/logs/uploader.log" 2>/dev/null | sed 's/^/  /'
else
    echo "  (log no encontrado)"
fi

echo ""

# ==================== USO DE RECURSOS ====================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}⚡ USO DE RECURSOS${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# CPU
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//' 2>/dev/null || echo "N/A")
echo -e "  CPU: ${GREEN}${CPU_USAGE}%${NC}"

# RAM
MEM_USAGE=$(free -h | grep Mem | awk '{printf "%s / %s (%.1f%%)", $3, $2, $3/$2*100}' 2>/dev/null || echo "N/A")
echo -e "  RAM: ${GREEN}${MEM_USAGE}${NC}"

# Load Average
LOAD_AVG=$(uptime | awk -F'load average:' '{print $2}' | xargs 2>/dev/null || echo "N/A")
echo -e "  Load Avg: ${GREEN}${LOAD_AVG}${NC}"

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
