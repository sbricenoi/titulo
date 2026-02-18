#!/bin/bash
# Script para reiniciar completamente limpio

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         🔄 REINICIO COMPLETO DEL SISTEMA                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# 1. Detener todo
echo "PASO 1/4: Deteniendo procesos..."
cd /Users/sbriceno/Documents/projects/titulo
pkill -9 -f "video_recorder.py" 2>/dev/null || true
pkill -9 -f "s3_uploader.py" 2>/dev/null || true
pkill -9 -f "ffmpeg.*camera" 2>/dev/null || true
sleep 3
echo "   ✓ Procesos detenidos"
echo ""

# 2. Limpiar
echo "PASO 2/4: Limpiando logs y archivos..."
cd video-recording-system
> data/logs/video_recorder.log
> data/logs/s3_uploader.log
> data/logs/recorder.log
> data/logs/uploader.log
rm -f data/videos/recordings/*.mp4 2>/dev/null || true
echo "   ✓ Limpieza completada"
echo ""

# 3. Verificar configuración
echo "PASO 3/4: Verificando configuración..."
cd ..
SEGMENT=$(grep SEGMENT_DURATION .env | cut -d'=' -f2)
echo "   Segmentos configurados: ${SEGMENT} segundos"
if [ "$SEGMENT" != "120" ]; then
    echo "   ⚠️  Ajustando a 2 minutos (120 segundos)..."
    sed -i '' 's/SEGMENT_DURATION=.*/SEGMENT_DURATION=120/' .env
    echo "   ✓ Configuración ajustada"
fi
echo ""

# 4. Verificar cámaras
echo "PASO 4/4: Verificando cámaras..."
CAMERA_2_OK=false
CAMERA_3_OK=false

if nc -z -w 2 192.168.0.5 554 2>/dev/null; then
    echo "   ✓ Cámara 2 (192.168.0.5)"
    CAMERA_2_OK=true
else
    echo "   ✗ Cámara 2 (192.168.0.5) - NO RESPONDE"
fi

if nc -z -w 2 192.168.0.9 554 2>/dev/null; then
    echo "   ✓ Cámara 3 (192.168.0.9)"
    CAMERA_3_OK=true
else
    echo "   ✗ Cámara 3 (192.168.0.9) - NO RESPONDE"
fi

if [ "$CAMERA_2_OK" = false ] && [ "$CAMERA_3_OK" = false ]; then
    echo ""
    echo "❌ ERROR: Ninguna cámara accesible"
    exit 1
fi
echo ""

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║            ✅ LISTO PARA INICIAR                            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Para iniciar el sistema ejecuta:"
echo "   ./INICIAR_SISTEMA_FINAL.sh"
echo ""
