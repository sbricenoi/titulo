#!/bin/bash

# ====================================
# Monitorear Grabación en Tiempo Real
# IP: 192.168.0.15
# ====================================

WINDOWS_IP="192.168.0.15"
WINDOWS_USER="brice"
PROJECT_PATH="C:\\Users\\${WINDOWS_USER}\\titulo\\video-recording-system"

echo "======================================"
echo "📹 MONITOR DE GRABACIÓN EN VIVO"
echo "======================================"
echo "IP: $WINDOWS_IP"
echo "Presiona Ctrl+C para salir"
echo ""

# Función para mostrar estadísticas
show_stats() {
    clear
    echo "======================================"
    echo "📹 MONITOR DE GRABACIÓN - $(date '+%H:%M:%S')"
    echo "======================================"
    echo ""
    
    # Procesos activos
    echo "🔄 PROCESOS ACTIVOS:"
    ssh ${WINDOWS_USER}@${WINDOWS_IP} "tasklist | findstr python" 2>/dev/null || echo "   ⚠️  Sin procesos Python"
    echo ""
    
    # Videos recientes
    echo "📁 ÚLTIMOS 5 VIDEOS:"
    ssh ${WINDOWS_USER}@${WINDOWS_IP} "dir ${PROJECT_PATH}\\data\\videos\\recordings\\*.mp4 /O-D /B 2>nul | findstr /N \"^\" | findstr \"^[1-5]:\"" 2>/dev/null | sed 's/^[0-9]*:/   /' || echo "   Sin videos aún"
    echo ""
    
    # Contador de videos
    video_count=$(ssh ${WINDOWS_USER}@${WINDOWS_IP} "dir ${PROJECT_PATH}\\data\\videos\\recordings\\*.mp4 2>nul | find /C \"mp4\"" 2>/dev/null || echo "0")
    echo "📊 TOTAL VIDEOS PENDIENTES: $video_count"
    echo ""
    
    # Uso de CPU y RAM
    echo "💻 RECURSOS DEL SISTEMA:"
    ssh ${WINDOWS_USER}@${WINDOWS_IP} "wmic cpu get loadpercentage /value 2>nul | findstr LoadPercentage" 2>/dev/null | sed 's/LoadPercentage=/   CPU: /' | sed 's/$/%/'
    
    free_mem=$(ssh ${WINDOWS_USER}@${WINDOWS_IP} "wmic OS get FreePhysicalMemory /value 2>nul | findstr FreePhysicalMemory" 2>/dev/null | sed 's/FreePhysicalMemory=//' | tr -d '\r')
    if [ ! -z "$free_mem" ]; then
        free_gb=$((free_mem / 1024 / 1024))
        echo "   RAM libre: ${free_gb}GB"
    fi
    echo ""
    
    echo "======================================"
    echo "Actualizando cada 5 segundos..."
    echo "Presiona Ctrl+C para salir"
}

# Loop infinito
while true; do
    show_stats
    sleep 5
done
