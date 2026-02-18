#!/bin/bash
# Iniciar API con endpoints de clasificación

cd "$(dirname "$0")"

echo "🚀 Iniciando API FastAPI para clasificación de frames..."
echo ""

# Activar entorno virtual
source venv/bin/activate

# Iniciar API
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

