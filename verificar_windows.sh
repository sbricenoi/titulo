#!/bin/bash

# ====================================
# Verificar Estado del Sistema Windows
# IP: 192.168.0.15
# ====================================

WINDOWS_IP="192.168.0.15"
WINDOWS_USER="Administrator"
PROJECT_PATH="C:\\Users\\${WINDOWS_USER}\\titulo"

echo "======================================"
echo "🔍 VERIFICACIÓN SISTEMA WINDOWS"
echo "======================================"
echo "IP: $WINDOWS_IP"
echo ""

# Verificar conectividad
echo "📡 1. VERIFICANDO CONECTIVIDAD..."
if ping -c 2 -W 2 $WINDOWS_IP > /dev/null 2>&1; then
    echo "   ✅ Windows está en línea"
else
    echo "   ❌ No se puede alcanzar el Windows"
    exit 1
fi
echo ""

# Verificar SSH
echo "🔐 2. VERIFICANDO SERVICIO SSH..."
if nc -z -w2 $WINDOWS_IP 22 > /dev/null 2>&1; then
    echo "   ✅ SSH está disponible (puerto 22)"
else
    echo "   ❌ SSH no está disponible"
    exit 1
fi
echo ""

# Estado de procesos Python
echo "📊 3. PROCESOS PYTHON (GRABACIÓN):"
ssh ${WINDOWS_USER}@${WINDOWS_IP} "tasklist | findstr python" 2>/dev/null || echo "   ⚠️  No hay procesos Python corriendo"
echo ""

# Espacio en disco
echo "💾 4. ESPACIO EN DISCO:"
ssh ${WINDOWS_USER}@${WINDOWS_IP} "wmic logicaldisk where drivetype=3 get caption,freespace,size /format:list" 2>/dev/null | grep -E "(Caption|FreeSpace|Size)" | while read line; do
    if [[ $line == Caption=* ]]; then
        echo -n "   Disco ${line#*=}: "
    elif [[ $line == Size=* ]]; then
        size=$((${line#*=} / 1073741824))
        echo -n "${size}GB total, "
    elif [[ $line == FreeSpace=* ]]; then
        free=$((${line#*=} / 1073741824))
        echo "${free}GB libre"
    fi
done
echo ""

# Verificar carpeta del proyecto
echo "📁 5. PROYECTO INSTALADO:"
if ssh ${WINDOWS_USER}@${WINDOWS_IP} "if exist ${PROJECT_PATH} (exit 0) else (exit 1)" 2>/dev/null; then
    echo "   ✅ Proyecto encontrado en ${PROJECT_PATH}"
    
    # Contar videos en recordings
    video_count=$(ssh ${WINDOWS_USER}@${WINDOWS_IP} "dir ${PROJECT_PATH}\\video-recording-system\\data\\videos\\recordings\\*.mp4 2>nul | find /C \"mp4\"" 2>/dev/null || echo "0")
    echo "   📹 Videos pendientes de subir: $video_count"
else
    echo "   ⚠️  Proyecto no encontrado - aún no instalado"
fi
echo ""

# Conexión a internet
echo "🌐 6. CONEXIÓN A INTERNET (desde Windows):"
if ssh ${WINDOWS_USER}@${WINDOWS_IP} "ping -n 1 8.8.8.8 > nul 2>&1" 2>/dev/null; then
    echo "   ✅ Tiene acceso a internet"
else
    echo "   ❌ Sin acceso a internet"
fi
echo ""

# Conexión a cámaras (si ya están configuradas)
echo "📷 7. CONECTIVIDAD CÁMARAS:"
for ip in 192.168.0.7 192.168.0.8 192.168.0.9; do
    if ssh ${WINDOWS_USER}@${WINDOWS_IP} "ping -n 1 -w 1000 $ip > nul 2>&1" 2>/dev/null; then
        echo "   ✅ Cámara $ip: accesible"
    else
        echo "   ❌ Cámara $ip: no accesible"
    fi
done
echo ""

echo "======================================"
echo "✅ Verificación completada"
echo "======================================"
echo ""
echo "💡 Para conectarte: ./conectar_windows.sh"
echo "💡 O directamente: ssh ${WINDOWS_USER}@${WINDOWS_IP}"
