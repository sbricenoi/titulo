#!/bin/bash
# Script para abrir el backoffice de clasificación

echo "🚀 Abriendo Backoffice de Clasificación..."
echo ""
echo "📊 Verificando servicios..."
echo ""

# Verificar API
if curl -s http://localhost:8000/api/classification/stats > /dev/null 2>&1; then
    echo "✅ API Backend funcionando (puerto 8000)"
else
    echo "❌ API Backend no responde"
    echo "   Ejecuta: ./start_api_classification.sh"
    exit 1
fi

# Verificar Frontend
if curl -s http://localhost:4200 > /dev/null 2>&1; then
    echo "✅ Frontend Angular funcionando (puerto 4200)"
else
    echo "❌ Frontend no responde"  
    echo "   Ejecuta: cd frontend && npm start"
    exit 1
fi

echo ""
echo "✅ Todos los servicios están activos"
echo ""
echo "🌐 Abriendo navegador en:"
echo "   http://localhost:4200/classifier"
echo ""

# Abrir navegador
open http://localhost:4200/classifier

echo "✅ ¡Listo! El backoffice debería abrirse en tu navegador."
echo ""
echo "📋 Si no se abre automáticamente, copia y pega:"
echo "   http://localhost:4200/classifier"
echo ""
