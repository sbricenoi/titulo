#!/bin/bash
# Script para iniciar el frontend Angular

echo "🎨 Iniciando Frontend Angular..."
echo "================================"
echo ""

cd /Users/sbriceno/Documents/projects/titulo/frontend

# Verificar que el backend esté corriendo
echo "🔍 Verificando backend..."
if curl -s http://localhost:8000 > /dev/null 2>&1; then
    echo "✅ Backend API disponible en http://localhost:8000"
else
    echo "⚠️  Backend API no responde. Asegúrate de ejecutar ./INICIAR_SISTEMA.sh primero"
    echo ""
    read -p "¿Continuar de todos modos? (s/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "🚀 Iniciando servidor de desarrollo Angular..."
echo "   Puerto: 4200"
echo "   URL: http://localhost:4200"
echo ""
echo "💡 La aplicación se abrirá automáticamente en tu navegador"
echo "   Si no se abre, visita: http://localhost:4200"
echo ""
echo "🛑 Para detener: Presiona Ctrl+C"
echo ""

# Iniciar Angular CLI
npx ng serve --open --port 4200



