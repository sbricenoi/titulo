#!/bin/bash
# ===============================================
# Script de Verificación del Sistema
# ===============================================
# Verifica que todos los componentes estén funcionando correctamente
#
# Uso: ./VERIFICAR_SISTEMA.sh
#

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     VERIFICACIÓN DEL SISTEMA DE MONITOREO DE HURONES    ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Función para verificar
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
        return 0
    else
        echo -e "${RED}❌ $1${NC}"
        return 1
    fi
}

# ====================================
# 1. VERIFICAR CONFIGURACIÓN
# ====================================
echo -e "${YELLOW}📋 1. VERIFICANDO CONFIGURACIÓN...${NC}"
echo ""

# .env principal
if [ -f .env ]; then
    check_status "Archivo .env encontrado"
    
    if grep -q "AWS_ACCESS_KEY_ID" .env && grep -q "S3_BUCKET_NAME" .env; then
        check_status "Credenciales AWS configuradas"
    else
        check_status "Credenciales AWS NO configuradas" && false
    fi
else
    check_status "Archivo .env NO encontrado" && false
fi

# .env de video-recording-system
if [ -f video-recording-system/.env ]; then
    check_status "video-recording-system/.env encontrado"
    
    if grep -q "CAMERA_1_URL" video-recording-system/.env; then
        check_status "Cámaras configuradas"
    else
        check_status "Cámaras NO configuradas" && false
    fi
else
    check_status "video-recording-system/.env NO encontrado" && false
fi

echo ""

# ====================================
# 2. VERIFICAR CONECTIVIDAD DE CÁMARAS
# ====================================
echo -e "${YELLOW}📹 2. VERIFICANDO CÁMARAS...${NC}"
echo ""

# Extraer IPs de cámaras
CAMERA_IPS=$(grep "CAMERA_._URL" video-recording-system/.env 2>/dev/null | sed 's/.*@\([0-9.]*\):.*/\1/' | sort -u)

if [ -z "$CAMERA_IPS" ]; then
    echo -e "${RED}❌ No se encontraron cámaras configuradas${NC}"
else
    for ip in $CAMERA_IPS; do
        if ping -c 1 -W 1 $ip &> /dev/null; then
            check_status "Cámara $ip accesible"
        else
            check_status "Cámara $ip NO accesible" && false
        fi
    done
fi

echo ""

# ====================================
# 3. VERIFICAR PROCESOS EN EJECUCIÓN
# ====================================
echo -e "${YELLOW}🔄 3. VERIFICANDO PROCESOS...${NC}"
echo ""

# Video Recorder
if pgrep -f "video_recorder.py" > /dev/null; then
    check_status "Video Recorder está corriendo"
else
    check_status "Video Recorder NO está corriendo" && false
fi

# S3 Uploader
if pgrep -f "s3_uploader.py" > /dev/null; then
    check_status "S3 Uploader está corriendo"
else
    check_status "S3 Uploader NO está corriendo" && false
fi

# API Backend
if pgrep -f "uvicorn.*api.main" > /dev/null; then
    check_status "API Backend está corriendo"
else
    check_status "API Backend NO está corriendo" && false
fi

# Frontend
if pgrep -f "ng serve" > /dev/null || lsof -ti:4201 > /dev/null 2>&1; then
    check_status "Frontend Angular está corriendo"
else
    check_status "Frontend Angular NO está corriendo" && false
fi

echo ""

# ====================================
# 4. VERIFICAR GRABACIÓN DE VIDEOS
# ====================================
echo -e "${YELLOW}📼 4. VERIFICANDO GRABACIÓN...${NC}"
echo ""

RECORDINGS_DIR="video-recording-system/data/videos/recordings"
if [ -d "$RECORDINGS_DIR" ]; then
    # Buscar archivos .mp4 de los últimos 30 minutos
    RECENT_VIDEOS=$(find "$RECORDINGS_DIR" -name "*.mp4" -mmin -30 2>/dev/null | wc -l | xargs)
    
    if [ "$RECENT_VIDEOS" -gt 0 ]; then
        check_status "Videos recientes encontrados ($RECENT_VIDEOS archivos)"
    else
        check_status "NO hay videos recientes (últimos 30 min)" && false
    fi
    
    # Mostrar tamaño total
    TOTAL_SIZE=$(du -sh "$RECORDINGS_DIR" 2>/dev/null | cut -f1)
    echo -e "   📊 Tamaño total en disco: ${BLUE}$TOTAL_SIZE${NC}"
else
    check_status "Directorio de grabaciones NO existe" && false
fi

echo ""

# ====================================
# 5. VERIFICAR CONEXIÓN A S3
# ====================================
echo -e "${YELLOW}☁️  5. VERIFICANDO CONEXIÓN A S3...${NC}"
echo ""

if command -v aws &> /dev/null; then
    BUCKET_NAME=$(grep "S3_BUCKET_NAME" .env 2>/dev/null | cut -d'=' -f2)
    
    if [ ! -z "$BUCKET_NAME" ]; then
        if aws s3 ls "s3://$BUCKET_NAME" --max-items 1 &> /dev/null; then
            check_status "Conexión a S3 bucket exitosa"
            
            # Contar archivos en S3
            S3_COUNT=$(aws s3 ls "s3://$BUCKET_NAME" --recursive 2>/dev/null | wc -l | xargs)
            echo -e "   📊 Videos en S3: ${BLUE}$S3_COUNT archivos${NC}"
        else
            check_status "NO se puede conectar a S3 bucket" && false
        fi
    else
        check_status "S3 bucket name no configurado" && false
    fi
else
    echo -e "${YELLOW}⚠️  AWS CLI no instalado, omitiendo verificación de S3${NC}"
fi

echo ""

# ====================================
# 6. VERIFICAR ANÁLISIS Y FRAMES
# ====================================
echo -e "${YELLOW}🤖 6. VERIFICANDO ANÁLISIS...${NC}"
echo ""

FRAMES_DIR="data/frames_for_classification"
if [ -d "$FRAMES_DIR" ]; then
    FRAMES_COUNT=$(find "$FRAMES_DIR" -name "*.jpg" 2>/dev/null | wc -l | xargs)
    
    if [ "$FRAMES_COUNT" -gt 0 ]; then
        check_status "Frames generados ($FRAMES_COUNT imágenes)"
    else
        echo -e "${YELLOW}⚠️  No hay frames generados aún${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Directorio de frames no existe${NC}"
fi

# Verificar análisis recientes
ANALYSIS_DIR="data/smart_analysis_results"
if [ -d "$ANALYSIS_DIR" ]; then
    RECENT_ANALYSIS=$(find "$ANALYSIS_DIR" -name "*_smart_analysis.json" -mmin -60 2>/dev/null | wc -l | xargs)
    
    if [ "$RECENT_ANALYSIS" -gt 0 ]; then
        check_status "Análisis recientes encontrados ($RECENT_ANALYSIS archivos)"
    else
        echo -e "${YELLOW}⚠️  No hay análisis recientes (última hora)${NC}"
    fi
fi

echo ""

# ====================================
# 7. VERIFICAR API Y FRONTEND
# ====================================
echo -e "${YELLOW}🌐 7. VERIFICANDO SERVICIOS WEB...${NC}"
echo ""

# API
if curl -s http://localhost:8000/api/classification/stats > /dev/null 2>&1; then
    check_status "API respondiendo en puerto 8000"
    
    # Obtener estadísticas
    STATS=$(curl -s http://localhost:8000/api/classification/stats 2>/dev/null)
    if [ ! -z "$STATS" ]; then
        echo -e "   📊 Estadísticas de clasificación disponibles"
    fi
else
    check_status "API NO responde en puerto 8000" && false
fi

# Frontend
if curl -s http://localhost:4201 > /dev/null 2>&1; then
    check_status "Frontend accesible en puerto 4201"
else
    check_status "Frontend NO accesible en puerto 4201" && false
fi

echo ""

# ====================================
# 8. VERIFICAR BASE DE DATOS
# ====================================
echo -e "${YELLOW}💾 8. VERIFICANDO BASE DE DATOS...${NC}"
echo ""

DB_FILE="data/classifications.db"
if [ -f "$DB_FILE" ]; then
    check_status "Base de datos SQLite existe"
    
    # Tamaño de DB
    DB_SIZE=$(du -h "$DB_FILE" 2>/dev/null | cut -f1)
    echo -e "   📊 Tamaño: ${BLUE}$DB_SIZE${NC}"
else
    echo -e "${YELLOW}⚠️  Base de datos no existe (se creará al usar)${NC}"
fi

echo ""

# ====================================
# 9. VERIFICAR LOGS
# ====================================
echo -e "${YELLOW}📄 9. VERIFICANDO LOGS...${NC}"
echo ""

LOGS_DIR="logs"
if [ -d "$LOGS_DIR" ]; then
    check_status "Directorio de logs existe"
    
    # Logs principales
    for log_file in recorder.log uploader.log api_backend.log; do
        if [ -f "$LOGS_DIR/$log_file" ]; then
            SIZE=$(du -h "$LOGS_DIR/$log_file" 2>/dev/null | cut -f1)
            echo -e "   📄 $log_file: ${BLUE}$SIZE${NC}"
        fi
    done
else
    echo -e "${YELLOW}⚠️  Directorio de logs no existe${NC}"
fi

echo ""

# ====================================
# 10. RESUMEN FINAL
# ====================================
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                     RESUMEN FINAL                        ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# URLs de acceso
echo -e "${GREEN}🌐 URLs de Acceso:${NC}"
echo -e "   • API:       ${BLUE}http://localhost:8000${NC}"
echo -e "   • Frontend:  ${BLUE}http://localhost:4201${NC}"
echo -e "   • Docs API:  ${BLUE}http://localhost:8000/docs${NC}"
echo ""

# Comandos útiles
echo -e "${GREEN}📋 Comandos Útiles:${NC}"
echo -e "   • Ver logs grabación:  ${BLUE}tail -f logs/recorder.log${NC}"
echo -e "   • Ver logs upload:     ${BLUE}tail -f logs/uploader.log${NC}"
echo -e "   • Ver logs API:        ${BLUE}tail -f logs/api_backend.log${NC}"
echo -e "   • Reiniciar todo:      ${BLUE}./REINICIAR_SISTEMA_LIMPIO.sh${NC}"
echo ""

# Estado general
echo -e "${GREEN}✅ SISTEMA VERIFICADO${NC}"
echo ""

exit 0
