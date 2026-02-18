#!/bin/bash
# Script para instalar servicios systemd del sistema de grabación
#
# Uso: sudo ./install-services.sh
#
# Autor: Sistema de Monitoreo de Hurones
# Fecha: 2026-01-24

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir con colores
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Verificar que se ejecuta como root
if [[ $EUID -ne 0 ]]; then
   print_error "Este script debe ejecutarse como root (usa sudo)"
   exit 1
fi

print_info "🔧 Instalando servicios systemd..."
echo ""

# Detectar directorio del proyecto
PROJECT_DIR="/home/ubuntu/video-recording-system"

if [ ! -d "$PROJECT_DIR" ]; then
    print_warning "Directorio $PROJECT_DIR no encontrado"
    read -p "Ingresa la ruta completa del proyecto: " PROJECT_DIR
    
    if [ ! -d "$PROJECT_DIR" ]; then
        print_error "Directorio no existe: $PROJECT_DIR"
        exit 1
    fi
fi

print_success "Directorio del proyecto: $PROJECT_DIR"
echo ""

# Archivos de servicio
RECORDER_SERVICE="$PROJECT_DIR/services/systemd/video-recorder.service"
UPLOADER_SERVICE="$PROJECT_DIR/services/systemd/s3-uploader.service"

# Verificar que los archivos existen
if [ ! -f "$RECORDER_SERVICE" ]; then
    print_error "Archivo no encontrado: $RECORDER_SERVICE"
    exit 1
fi

if [ ! -f "$UPLOADER_SERVICE" ]; then
    print_error "Archivo no encontrado: $UPLOADER_SERVICE"
    exit 1
fi

# 1. Copiar archivos de servicio
print_info "Copiando archivos de servicio a /etc/systemd/system/..."
cp "$RECORDER_SERVICE" /etc/systemd/system/
cp "$UPLOADER_SERVICE" /etc/systemd/system/
print_success "Archivos copiados"

# 2. Dar permisos correctos
print_info "Configurando permisos..."
chmod 644 /etc/systemd/system/video-recorder.service
chmod 644 /etc/systemd/system/s3-uploader.service
print_success "Permisos configurados"

# 3. Recargar systemd
print_info "Recargando systemd daemon..."
systemctl daemon-reload
print_success "Daemon recargado"

# 4. Habilitar servicios (arranque automático)
print_info "Habilitando servicios para inicio automático..."
systemctl enable video-recorder.service
systemctl enable s3-uploader.service
print_success "Servicios habilitados"

echo ""
print_success "🎉 Instalación completada exitosamente!"
echo ""
print_info "Próximos pasos:"
echo ""
echo "  1. Iniciar servicios:"
echo "     sudo systemctl start video-recorder"
echo "     sudo systemctl start s3-uploader"
echo ""
echo "  2. Ver estado:"
echo "     sudo systemctl status video-recorder"
echo "     sudo systemctl status s3-uploader"
echo ""
echo "  3. Ver logs en tiempo real:"
echo "     sudo journalctl -u video-recorder -f"
echo "     sudo journalctl -u s3-uploader -f"
echo ""
echo "  4. Detener servicios:"
echo "     sudo systemctl stop video-recorder s3-uploader"
echo ""
echo "  5. Reiniciar servicios:"
echo "     sudo systemctl restart video-recorder s3-uploader"
echo ""
echo "  6. Deshabilitar inicio automático:"
echo "     sudo systemctl disable video-recorder s3-uploader"
echo ""
print_info "Los servicios se reiniciarán automáticamente si fallan"
print_info "Los servicios iniciarán automáticamente al arrancar el sistema"
echo ""
