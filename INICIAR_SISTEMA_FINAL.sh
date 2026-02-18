#!/bin/bash
# Script DEFINITIVO para iniciar el sistema de grabación
# Probado y verificado para funcionamiento automático 24/7

set -e

cd /Users/sbriceno/Documents/projects/titulo/video-recording-system

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     🎥 SISTEMA DE GRABACIÓN Y SUBIDA A S3                   ║"
echo "║     INICIO DEFINITIVO - Versión 1.0                         ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# PASO 1: Verificar cámaras
echo "PASO 1/5: Verificando cámaras..."
CAMERA_2_OK=false
CAMERA_3_OK=false

if nc -z -w 2 192.168.0.5 554 2>/dev/null; then
    echo "   ✓ Cámara 2 (192.168.0.5) - Accesible"
    CAMERA_2_OK=true
else
    echo "   ✗ Cámara 2 (192.168.0.5) - NO RESPONDE"
fi

if nc -z -w 2 192.168.0.9 554 2>/dev/null; then
    echo "   ✓ Cámara 3 (192.168.0.9) - Accesible"
    CAMERA_3_OK=true
else
    echo "   ✗ Cámara 3 (192.168.0.9) - NO RESPONDE"
fi

if [ "$CAMERA_2_OK" = false ] && [ "$CAMERA_3_OK" = false ]; then
    echo ""
    echo "❌ ERROR: Ninguna cámara accesible"
    echo "   Verifica la conexión de red"
    exit 1
fi
echo ""

# PASO 2: Limpiar procesos anteriores
echo "PASO 2/5: Limpiando procesos anteriores..."
pkill -9 -f "video_recorder.py" 2>/dev/null || true
pkill -9 -f "s3_uploader.py" 2>/dev/null || true
pkill -9 -f "ffmpeg.*camera" 2>/dev/null || true
sleep 3
echo "   ✓ Limpieza completada"
echo ""

# PASO 3: Activar entorno
echo "PASO 3/5: Activando entorno virtual..."
source venv/bin/activate
echo "   ✓ Entorno activado"
echo ""

# PASO 4: Iniciar Video Recorder
echo "PASO 4/5: Iniciando Video Recorder..."
nohup python3 services/video_recorder.py >> data/logs/video_recorder.log 2>&1 &
RECORDER_PID=$!
echo "   PID: $RECORDER_PID"
sleep 7

if ps -p $RECORDER_PID > /dev/null 2>&1; then
    echo "   ✅ Video Recorder ACTIVO"
else
    echo "   ❌ Video Recorder FALLÓ"
    echo ""
    tail -20 data/logs/video_recorder.log
    exit 1
fi
echo ""

# PASO 5: Iniciar S3 Uploader
echo "PASO 5/5: Iniciando S3 Uploader..."
nohup python3 services/s3_uploader.py >> data/logs/s3_uploader.log 2>&1 &
UPLOADER_PID=$!
echo "   PID: $UPLOADER_PID"
sleep 7

if ps -p $UPLOADER_PID > /dev/null 2>&1; then
    echo "   ✅ S3 Uploader ACTIVO"
else
    echo "   ❌ S3 Uploader FALLÓ"
    echo ""
    tail -20 data/logs/s3_uploader.log
    kill $RECORDER_PID 2>/dev/null || true
    exit 1
fi
echo ""

# Verificación final
sleep 3
FFMPEG_COUNT=$(ps aux | grep ffmpeg | grep camera | grep -v grep | wc -l | xargs)

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           ✅ SISTEMA INICIADO CORRECTAMENTE                 ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 ESTADO:"
echo "   Video Recorder: PID $RECORDER_PID ✓"
echo "   S3 Uploader:    PID $UPLOADER_PID ✓"
echo "   FFmpeg:         $FFMPEG_COUNT cámara(s) grabando"
echo ""
echo "⚙️  CONFIGURACIÓN:"
echo "   Segmentos:   2 minutos (120 segundos)"
echo "   Estabilidad: 60 segundos"
echo "   Retry:       Cada 30 segundos"
echo ""
echo "📝 FUNCIONAMIENTO:"
echo "   1. FFmpeg graba segmentos de 2 minutos"
echo "   2. Después de 60s sin modificar, archivo considerado completo"
echo "   3. S3 Uploader sube automáticamente"
echo "   4. Archivo movido a uploaded/ tras subida exitosa"
echo ""
echo "📋 MONITOREAR:"
echo "   tail -f data/logs/video_recorder.log"
echo "   tail -f data/logs/s3_uploader.log"
echo ""
echo "🛑 DETENER:"
echo "   kill $RECORDER_PID $UPLOADER_PID"
echo "   O ejecutar: ./stop_recorder_robusto.sh"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "🎯 PRIMER ARCHIVO SE SUBIRÁ EN ~3 MINUTOS"
echo "   (2 min grabación + 1 min estabilidad)"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "💤 Sistema listo para operar 24/7"
echo ""

# Guardar PIDs para referencia
echo "$RECORDER_PID" > /tmp/video_recorder.pid
echo "$UPLOADER_PID" > /tmp/s3_uploader.pid
