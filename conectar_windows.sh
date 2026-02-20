#!/bin/bash

# ====================================
# Conectar al Windows de Grabación
# IP: 192.168.0.15
# ====================================

WINDOWS_IP="192.168.0.15"
WINDOWS_USER="Administrator"

echo "======================================"
echo "🖥️  CONECTANDO A WINDOWS"
echo "======================================"
echo "IP: $WINDOWS_IP"
echo "Usuario: $WINDOWS_USER"
echo ""
echo "Conectando..."
echo ""

ssh ${WINDOWS_USER}@${WINDOWS_IP}
