#!/bin/bash
# ===============================================
# Script de Configuración para Lightsail
# ===============================================
# Este script configura el servidor Lightsail para
# procesar videos desde S3 sin acceso directo a cámaras
#
# Uso: ./lightsail-setup.sh
#

set -e  # Salir si hay error

echo "🚀 Configurando Servidor Lightsail para Análisis de Videos"
echo "=========================================================="
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar que estamos en Lightsail
if [ ! -f /etc/os-release ]; then
    echo -e "${RED}❌ Este script debe ejecutarse en el servidor Lightsail${NC}"
    exit 1
fi

echo "✅ Verificando sistema..."
cat /etc/os-release | grep "Ubuntu"

echo ""
echo "📦 Actualizando sistema..."
sudo apt update
sudo apt upgrade -y

echo ""
echo "🔧 Instalando dependencias del sistema..."
sudo apt install -y \
    python3-pip \
    python3-venv \
    git \
    ffmpeg \
    htop \
    curl \
    unzip

echo ""
echo "🐍 Creando entorno virtual de Python..."
cd ~
python3 -m venv venv

echo ""
echo "📥 Activando entorno virtual..."
source ~/venv/bin/activate

echo ""
echo "📦 Instalando dependencias de Python..."
pip install --upgrade pip

# Si el repositorio ya está clonado
if [ -d ~/titulo ]; then
    cd ~/titulo
    pip install -r requirements.txt
    pip install -r requirements-recorder.txt
    echo -e "${GREEN}✅ Dependencias instaladas${NC}"
else
    echo -e "${YELLOW}⚠️  Repositorio no encontrado. Clónalo primero:${NC}"
    echo "   git clone <URL_DEL_REPO> ~/titulo"
fi

echo ""
echo "📁 Creando estructura de directorios..."
mkdir -p ~/titulo/data/videos/from_s3
mkdir -p ~/titulo/data/analysis_results
mkdir -p ~/titulo/data/smart_analysis_results
mkdir -p ~/titulo/data/frames_for_classification
mkdir -p ~/titulo/logs

echo ""
echo "🔐 Configurando permisos..."
chmod +x ~/titulo/*.sh

echo ""
echo "📝 Verificando configuración de .env..."
if [ ! -f ~/titulo/.env ]; then
    echo -e "${YELLOW}⚠️  Archivo .env no encontrado${NC}"
    echo "   Cópialo desde env.example:"
    echo "   cp ~/titulo/env.example ~/titulo/.env"
    echo "   nano ~/titulo/.env"
    echo ""
    echo "   Configuración requerida:"
    echo "   - AWS_ACCESS_KEY_ID"
    echo "   - AWS_SECRET_ACCESS_KEY"
    echo "   - S3_BUCKET_NAME"
    echo "   - AWS_REGION"
    echo ""
    echo "   NO configurar CAMERA_X_URL (las cámaras están en red local)"
else
    echo -e "${GREEN}✅ Archivo .env encontrado${NC}"
fi

echo ""
echo "🧪 Verificando instalación..."
echo "Python: $(python --version)"
echo "FFmpeg: $(ffmpeg -version | head -1)"
echo "Git: $(git --version)"

echo ""
echo "📊 Recursos del servidor:"
free -h
df -h /

echo ""
echo "=========================================================="
echo -e "${GREEN}✅ Configuración básica completada${NC}"
echo "=========================================================="
echo ""
echo "📋 Próximos pasos:"
echo ""
echo "1. Configurar .env:"
echo "   nano ~/titulo/.env"
echo ""
echo "2. Probar descarga desde S3:"
echo "   cd ~/titulo"
echo "   source ~/venv/bin/activate"
echo "   python process_s3_videos.py"
echo ""
echo "3. Probar análisis:"
echo "   python auto_analyze_videos.py"
echo ""
echo "4. Iniciar API:"
echo "   cd ~/titulo"
echo "   ./start_api_classification.sh"
echo ""
echo "5. Monitorear recursos:"
echo "   htop"
echo ""
echo -e "${YELLOW}⚠️  Recuerda: Este servidor NO graba de cámaras directamente.${NC}"
echo -e "${YELLOW}   Procesa videos que llegan desde S3.${NC}"
echo ""
