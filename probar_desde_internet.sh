#!/bin/bash
# Script para verificar puertos desde internet

echo "🌐 Verificando puertos desde internet..."
echo ""
echo "IP Pública IPv4: 200.104.174.206"
echo ""

# Usar servicio online para verificar puertos abiertos
for PORT in 8554 8555 8556; do
    echo "🔍 Probando puerto $PORT..."
    
    # Timeout de 5 segundos
    if timeout 5 bash -c "echo > /dev/tcp/200.104.174.206/$PORT" 2>/dev/null; then
        echo "   ✅ Puerto $PORT ABIERTO desde internet"
    else
        echo "   ❌ Puerto $PORT NO accesible desde internet"
    fi
    echo ""
done

echo "📝 Nota: Esta prueba puede fallar si estás en la misma red."
echo "   Para prueba definitiva, usa celular con datos móviles:"
echo ""
echo "   telnet 200.104.174.206 8554"
