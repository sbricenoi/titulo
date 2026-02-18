#!/bin/bash
# Script de prueba para el procesador de videos S3

echo "🧪 Probando Procesador de Videos S3"
echo "====================================="
echo ""

cd /Users/sbriceno/Documents/projects/titulo
source venv/bin/activate

echo "1️⃣ Verificando dependencias..."
python3 -c "
try:
    import boto3
    import cv2
    import torch
    from ultralytics import YOLO
    from tqdm import tqdm
    print('✓ Todas las dependencias disponibles')
except ImportError as e:
    print(f'✗ Falta dependencia: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Faltan dependencias. Instalando..."
    pip install opencv-python-headless ultralytics torch boto3 tqdm
    echo ""
fi

echo ""
echo "2️⃣ Verificando acceso a S3..."
python3 -c "
import boto3
try:
    s3 = boto3.client('s3')
    response = s3.list_objects_v2(Bucket='ferret-recordings', MaxKeys=1)
    if 'Contents' in response:
        print(f'✓ Acceso a S3 OK - Bucket: ferret-recordings')
    else:
        print('⚠️  Bucket vacío o sin acceso')
except Exception as e:
    print(f'✗ Error accediendo a S3: {e}')
    exit(1)
"

echo ""
echo "3️⃣ Listando videos disponibles (últimos 5)..."
python3 process_s3_videos.py --limit 5 2>&1 | head -30

echo ""
echo "✅ Prueba completada"
echo ""
echo "Para procesar videos, ejecuta:"
echo "  python3 process_s3_videos.py --date 2026-02-07 --limit 3"
echo ""
