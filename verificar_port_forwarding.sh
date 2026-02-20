#!/bin/bash
# ===============================================
# Script de Verificación de Port Forwarding
# ===============================================
# Verifica que el port forwarding esté configurado correctamente
#
# Uso: ./verificar_port_forwarding.sh
#

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       VERIFICACIÓN DE PORT FORWARDING - CÁMARAS         ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# ====================================
# 1. OBTENER IP PÚBLICA
# ====================================
echo -e "${YELLOW}🌐 1. OBTENIENDO IP PÚBLICA...${NC}"
echo ""

PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s https://api.ipify.org 2>/dev/null)

if [ -z "$PUBLIC_IP" ]; then
    echo -e "${RED}❌ No se pudo obtener IP pública${NC}"
    exit 1
fi

echo -e "${GREEN}✅ IP Pública: ${BLUE}$PUBLIC_IP${NC}"
echo ""

# Verificar si es IP privada (CGNAT)
if [[ $PUBLIC_IP =~ ^10\. ]] || [[ $PUBLIC_IP =~ ^192\.168\. ]] || [[ $PUBLIC_IP =~ ^172\.(1[6-9]|2[0-9]|3[0-1])\. ]] || [[ $PUBLIC_IP =~ ^100\.(6[4-9]|[7-9][0-9]|1[0-2][0-7])\. ]]; then
    echo -e "${RED}⚠️  ADVERTENCIA: Tu IP pública es privada (CGNAT)${NC}"
    echo -e "${YELLOW}   Estás detrás de NAT de tu ISP. Port forwarding no funcionará.${NC}"
    echo -e "${YELLOW}   Contacta a tu ISP o usa Tailscale VPN.${NC}"
    echo ""
fi

# ====================================
# 2. VERIFICAR CÁMARAS LOCALES
# ====================================
echo -e "${YELLOW}📹 2. VERIFICANDO CÁMARAS LOCALES...${NC}"
echo ""

CAMERAS=("192.168.0.8" "192.168.0.9" "192.168.0.7")
PORTS=("8554" "8555" "8556")
NAMES=("Principal" "Secundaria" "Camara_3")

for i in "${!CAMERAS[@]}"; do
    IP="${CAMERAS[$i]}"
    NAME="${NAMES[$i]}"
    
    if ping -c 1 -W 1 "$IP" &> /dev/null; then
        echo -e "${GREEN}✅ Cámara $NAME ($IP) accesible${NC}"
    else
        echo -e "${RED}❌ Cámara $NAME ($IP) NO accesible${NC}"
    fi
done

echo ""

# ====================================
# 3. VERIFICAR PUERTOS LOCALMENTE
# ====================================
echo -e "${YELLOW}🔌 3. VERIFICANDO PUERTOS RTSP LOCALES...${NC}"
echo ""

for i in "${!CAMERAS[@]}"; do
    IP="${CAMERAS[$i]}"
    NAME="${NAMES[$i]}"
    
    if nc -z -w 2 "$IP" 554 2>/dev/null; then
        echo -e "${GREEN}✅ Puerto RTSP 554 abierto en $NAME ($IP)${NC}"
    else
        echo -e "${RED}❌ Puerto RTSP 554 NO accesible en $NAME ($IP)${NC}"
    fi
done

echo ""

# ====================================
# 4. VERIFICAR PORT FORWARDING (desde internet)
# ====================================
echo -e "${YELLOW}🌐 4. VERIFICANDO PORT FORWARDING (desde internet)...${NC}"
echo ""

echo -e "${BLUE}ℹ️  Esta prueba necesita hacerse desde FUERA de tu red local${NC}"
echo -e "${BLUE}   (ej: usando datos móviles de celular)${NC}"
echo ""

echo -e "Comandos para probar desde celular/red externa:"
echo ""

for i in "${!CAMERAS[@]}"; do
    PORT="${PORTS[$i]}"
    NAME="${NAMES[$i]}"
    
    echo -e "${BLUE}# Probar $NAME (puerto $PORT)${NC}"
    echo "telnet $PUBLIC_IP $PORT"
    echo ""
done

echo -e "${YELLOW}Si conecta, verás: 'Connected to...'${NC}"
echo -e "${YELLOW}Si NO conecta, verás: 'Connection refused' o timeout${NC}"
echo ""

# ====================================
# 5. PROBAR CONEXIÓN RTSP LOCAL
# ====================================
echo -e "${YELLOW}📡 5. PROBANDO CONEXIÓN RTSP LOCAL...${NC}"
echo ""

if command -v ffmpeg &> /dev/null; then
    echo -e "${GREEN}✅ FFmpeg instalado${NC}"
    echo ""
    
    # Probar primera cámara
    echo -e "${BLUE}Probando cámara ${CAMERAS[0]}...${NC}"
    
    if timeout 10 ffmpeg -rtsp_transport tcp \
                          -i "rtsp://admin:Sb123456@${CAMERAS[0]}:554/h264Preview_01_main" \
                          -frames 1 \
                          -y \
                          /tmp/test_camera.jpg &> /dev/null; then
        echo -e "${GREEN}✅ Conexión RTSP exitosa a cámara ${CAMERAS[0]}${NC}"
        echo -e "   Archivo de prueba: /tmp/test_camera.jpg"
        ls -lh /tmp/test_camera.jpg
    else
        echo -e "${RED}❌ No se pudo conectar vía RTSP a ${CAMERAS[0]}${NC}"
        echo -e "${YELLOW}   Verifica usuario/contraseña y ruta RTSP${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  FFmpeg no instalado, omitiendo prueba RTSP${NC}"
fi

echo ""

# ====================================
# 6. GENERAR CONFIGURACIÓN PARA LIGHTSAIL
# ====================================
echo -e "${YELLOW}📝 6. GENERANDO CONFIGURACIÓN PARA LIGHTSAIL...${NC}"
echo ""

ENV_FILE="deploy/lightsail-cameras.env"
mkdir -p deploy

cat > "$ENV_FILE" <<EOF
# ============================================
# Configuración para Lightsail
# Cámaras expuestas vía Port Forwarding
# ============================================

# IP Pública (actualizada: $(date))
PUBLIC_IP=$PUBLIC_IP

# AWS S3
AWS_ACCESS_KEY_ID=<tu-key>
AWS_SECRET_ACCESS_KEY=<tu-secret>
AWS_REGION=us-east-2
S3_BUCKET_NAME=ferret-recordings-bucket

# CÁMARAS (acceso desde internet)
# IMPORTANTE: Actualiza las contraseñas después de cambiarlas

CAMERA_1_URL=rtsp://admin:Sb123456@$PUBLIC_IP:8554/h264Preview_01_main
CAMERA_1_NAME=Reolink_Huron_Principal

CAMERA_2_URL=rtsp://admin:Sb123456@$PUBLIC_IP:8555/h264Preview_01_main
CAMERA_2_NAME=Reolink_Huron_Secundaria

CAMERA_3_URL=rtsp://admin:Sb123456@$PUBLIC_IP:8556/h264Preview_01_main
CAMERA_3_NAME=Reolink_Huron_3

# Configuración de grabación
SEGMENT_DURATION=600
VIDEO_CODEC=copy
LOCAL_RETENTION_HOURS=24
LOG_LEVEL=INFO

# Paths en Lightsail
BASE_DIR=/home/ubuntu/titulo
RECORDINGS_DIR=/home/ubuntu/titulo/data/videos/recordings
COMPLETED_DIR=/home/ubuntu/titulo/data/videos/completed
UPLOADED_DIR=/home/ubuntu/titulo/data/videos/uploaded
EOF

echo -e "${GREEN}✅ Archivo creado: ${BLUE}$ENV_FILE${NC}"
echo ""

# ====================================
# 7. RESUMEN Y PRÓXIMOS PASOS
# ====================================
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    RESUMEN Y PRÓXIMOS PASOS              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${GREEN}📊 INFORMACIÓN RECOPILADA:${NC}"
echo ""
echo -e "  • IP Pública:     ${BLUE}$PUBLIC_IP${NC}"
echo -e "  • Cámaras:        ${BLUE}3 detectadas${NC}"
echo -e "  • Config generada: ${BLUE}$ENV_FILE${NC}"
echo ""

echo -e "${YELLOW}⚠️  CONFIGURACIÓN REQUERIDA EN ROUTER:${NC}"
echo ""

for i in "${!CAMERAS[@]}"; do
    IP="${CAMERAS[$i]}"
    PORT="${PORTS[$i]}"
    NAME="${NAMES[$i]}"
    
    echo -e "${BLUE}Regla $((i+1)): $NAME${NC}"
    echo "  External Port:  $PORT"
    echo "  Internal Port:  554"
    echo "  Internal IP:    $IP"
    echo "  Protocol:       TCP"
    echo ""
done

echo -e "${GREEN}✅ PRÓXIMOS PASOS:${NC}"
echo ""
echo "1. Abre tu router en: ${BLUE}http://192.168.0.1${NC}"
echo "   (o ejecuta: ${BLUE}open http://192.168.0.1${NC})"
echo ""
echo "2. Configura las 3 reglas de port forwarding mostradas arriba"
echo ""
echo "3. Guarda y aplica cambios en el router"
echo ""
echo "4. Prueba desde red externa (celular con datos):"
echo "   ${BLUE}telnet $PUBLIC_IP 8554${NC}"
echo ""
echo "5. Copia configuración a Lightsail:"
echo "   ${BLUE}scp -i ferret-recorder-key.pem \\${NC}"
echo "   ${BLUE}    $ENV_FILE \\${NC}"
echo "   ${BLUE}    ubuntu@3.147.46.191:~/titulo/video-recording-system/.env${NC}"
echo ""
echo "6. ${RED}CAMBIA LAS CONTRASEÑAS de las cámaras${NC} (CRÍTICO)"
echo "   Accede a cada cámara y cambia en Settings > User Management"
echo ""

echo -e "${YELLOW}📚 Ver guía completa:${NC}"
echo "   cat CONFIGURAR_PORT_FORWARDING.md"
echo ""

exit 0
