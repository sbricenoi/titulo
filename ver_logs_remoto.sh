#!/bin/bash

# ====================================
# Ver Logs del Sistema en Tiempo Real
# IP: 192.168.0.15
# ====================================

WINDOWS_IP="192.168.0.15"
WINDOWS_USER="brice"
PROJECT_PATH="C:\\Users\\${WINDOWS_USER}\\titulo\\video-recording-system"

echo "======================================"
echo "📋 LOGS DEL SISTEMA"
echo "======================================"
echo ""
echo "Selecciona qué log ver:"
echo ""
echo "1) Grabación (video_recorder.py)"
echo "2) Subida a S3 (s3_uploader.py)"
echo "3) Ambos (alternando)"
echo "4) Salir"
echo ""
read -p "Opción [1-4]: " opcion

case $opcion in
    1)
        echo ""
        echo "📹 Mostrando log de grabación (Ctrl+C para salir)..."
        echo ""
        ssh ${WINDOWS_USER}@${WINDOWS_IP} "powershell Get-Content ${PROJECT_PATH}\\logs\\recorder.log -Wait -Tail 50"
        ;;
    2)
        echo ""
        echo "☁️  Mostrando log de S3 uploader (Ctrl+C para salir)..."
        echo ""
        ssh ${WINDOWS_USER}@${WINDOWS_IP} "powershell Get-Content ${PROJECT_PATH}\\logs\\uploader.log -Wait -Tail 50"
        ;;
    3)
        echo ""
        echo "📋 Mostrando ambos logs..."
        echo ""
        echo "=== GRABACIÓN ==="
        ssh ${WINDOWS_USER}@${WINDOWS_IP} "type ${PROJECT_PATH}\\logs\\recorder.log 2>nul | more +$(wc -l < ${PROJECT_PATH}\\logs\\recorder.log)-20" 2>/dev/null || echo "Sin logs aún"
        echo ""
        echo "=== S3 UPLOADER ==="
        ssh ${WINDOWS_USER}@${WINDOWS_IP} "type ${PROJECT_PATH}\\logs\\uploader.log 2>nul | more +$(wc -l < ${PROJECT_PATH}\\logs\\uploader.log)-20" 2>/dev/null || echo "Sin logs aún"
        ;;
    4)
        echo "Saliendo..."
        exit 0
        ;;
    *)
        echo "Opción inválida"
        exit 1
        ;;
esac
