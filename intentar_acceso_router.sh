#!/bin/bash
# Script para probar acceso al router VTR

echo "🔐 Intentando acceder al router VTR ARRIS..."
echo ""

IPS=("192.168.0.1" "192.168.1.1")
PASSWORDS=("VTR.2019" "admin" "D9C08E32" "password" "1234")

echo "📋 Probando conexión..."
echo ""

for IP in "${IPS[@]}"; do
    echo "🌐 Probando IP: $IP"
    
    if ping -c 1 -W 1 "$IP" &> /dev/null; then
        echo "   ✅ Router accesible en $IP"
        echo "   🌍 Abriendo en navegador..."
        open "http://$IP"
        echo ""
        echo "   Credenciales a probar:"
        echo "   ---------------------"
        for PASS in "${PASSWORDS[@]}"; do
            echo "   Usuario: admin"
            echo "   Contraseña: $PASS"
            echo ""
        done
        break
    else
        echo "   ❌ No accesible en $IP"
        echo ""
    fi
done

echo "📞 Si ninguna funciona:"
echo "   Llama a VTR: 600 800 9000"
echo "   Pide la contraseña del router"
echo ""
echo "🔒 Alternativa: Usa Tailscale VPN"
echo "   No necesita acceso al router"
echo "   Ver: EXPONER_CAMARAS_LIGHTSAIL.md → Opción 2"
