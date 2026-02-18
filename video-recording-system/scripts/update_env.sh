#!/bin/bash
# Script para actualizar .env con las cámaras funcionales

ENV_FILE="../.env"

echo "🔧 Actualizando configuración de cámaras en .env..."
echo ""

# Verificar si .env existe
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: No se encuentra el archivo .env"
    echo "   Crea uno primero copiando env.example:"
    echo "   cp env.example .env"
    exit 1
fi

# Backup del .env actual
cp "$ENV_FILE" "${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
echo "✅ Backup creado: ${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
echo ""

# Función para actualizar o agregar variable
update_var() {
    local var_name=$1
    local var_value=$2
    
    if grep -q "^${var_name}=" "$ENV_FILE"; then
        # Variable existe, actualizarla
        sed -i.tmp "s|^${var_name}=.*|${var_name}=${var_value}|" "$ENV_FILE"
        rm -f "${ENV_FILE}.tmp"
        echo "  ✓ Actualizado: $var_name"
    else
        # Variable no existe, agregarla
        echo "${var_name}=${var_value}" >> "$ENV_FILE"
        echo "  ✓ Agregado: $var_name"
    fi
}

echo "📝 Configurando cámaras..."
echo ""

# Cámara 1
update_var "CAMERA_1_URL" "rtsp://admin:Sb123456@192.168.0.5:554/Preview_01_main"
update_var "CAMERA_1_NAME" "Reolink_Huron_Principal"

# Cámara 2
update_var "CAMERA_2_URL" "rtsp://admin:Sb123456@192.168.0.6:554/h264Preview_01_main"
update_var "CAMERA_2_NAME" "Reolink_Huron_Secundaria"

# Cámara 3
update_var "CAMERA_3_URL" "rtsp://admin:Sb123456@192.168.0.7:554/Preview_01_main"
update_var "CAMERA_3_NAME" "Reolink_Huron_Terciaria"

echo ""
echo "✅ Configuración actualizada exitosamente"
echo ""
echo "📋 Cámaras configuradas:"
echo ""
grep "^CAMERA_[0-9]*_" "$ENV_FILE" | sort
echo ""
echo "🔄 Para aplicar los cambios, reinicia el servicio:"
echo "   python3 services/video_recorder.py"
echo ""
echo "   O si está como servicio systemd:"
echo "   sudo systemctl restart video-recorder"
echo ""
