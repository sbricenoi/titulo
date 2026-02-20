#!/bin/bash

# ====================================
# Configurar SSH desde Mac a Windows
# ====================================

echo "======================================"
echo "🔧 CONFIGURACIÓN SSH WINDOWS"
echo "======================================"
echo ""

# Verificar conectividad
echo "1️⃣  Verificando conectividad..."
if ping -c 2 -W 2 192.168.0.15 > /dev/null 2>&1; then
    echo "   ✅ Windows responde a ping"
else
    echo "   ⚠️  Windows no responde a ping (puede ser normal si firewall bloquea ICMP)"
fi

# Verificar SSH
echo ""
echo "2️⃣  Verificando servicio SSH..."
if nc -z -w2 192.168.0.15 22 > /dev/null 2>&1; then
    echo "   ✅ SSH está disponible (puerto 22)"
else
    echo "   ❌ SSH no está disponible"
    echo ""
    echo "   Necesitas habilitar OpenSSH en Windows:"
    echo "   1. Abrir PowerShell como Administrador"
    echo "   2. Ejecutar: Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0"
    echo "   3. Ejecutar: Start-Service sshd"
    echo "   4. Ejecutar: Set-Service -Name sshd -StartupType 'Automatic'"
    exit 1
fi

# Solicitar usuario
echo ""
echo "3️⃣  Configurando usuario..."
echo ""
read -p "   Ingresa el usuario de Windows (ejemplo: usuario, DESKTOP\\usuario): " WINDOWS_USER

if [ -z "$WINDOWS_USER" ]; then
    echo "   ❌ Usuario no puede estar vacío"
    exit 1
fi

echo "   Usuario: $WINDOWS_USER"
echo ""

# Probar conexión
echo "4️⃣  Probando conexión SSH..."
echo "   (Te pedirá la contraseña de Windows)"
echo ""

if ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no ${WINDOWS_USER}@192.168.0.15 "echo Conectado exitosamente"; then
    echo ""
    echo "   ✅ Conexión exitosa!"
    echo ""
    
    # Copiar clave pública
    echo "5️⃣  Configurando acceso sin contraseña..."
    echo ""
    
    if [ -f ~/.ssh/id_ed25519.pub ]; then
        echo "   Copiando clave pública al Windows..."
        cat ~/.ssh/id_ed25519.pub | ssh ${WINDOWS_USER}@192.168.0.15 "mkdir -p .ssh && cat >> .ssh/authorized_keys"
        echo "   ✅ Clave copiada"
    else
        echo "   ⚠️  No se encontró clave pública en ~/.ssh/id_ed25519.pub"
    fi
    
    echo ""
    echo "6️⃣  Actualizando configuración SSH..."
    
    # Actualizar ~/.ssh/config con el usuario correcto
    if grep -q "Host windows-grabacion" ~/.ssh/config 2>/dev/null; then
        # Actualizar usuario en configuración existente
        sed -i.backup "s/User .*/User ${WINDOWS_USER}/" ~/.ssh/config
        echo "   ✅ Configuración actualizada en ~/.ssh/config"
    else
        # Agregar nueva configuración
        cat >> ~/.ssh/config << EOF

Host windows-grabacion
    HostName 192.168.0.15
    User ${WINDOWS_USER}
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 60
    ServerAliveCountMax 3
EOF
        echo "   ✅ Configuración agregada a ~/.ssh/config"
    fi
    
    echo ""
    echo "7️⃣  Probando conexión sin contraseña..."
    if ssh -o ConnectTimeout=5 windows-grabacion "echo OK" > /dev/null 2>&1; then
        echo "   ✅ Conexión sin contraseña funciona!"
    else
        echo "   ⚠️  Aún requiere contraseña (puede ser normal en primera configuración)"
    fi
    
    echo ""
    echo "======================================"
    echo "✅ CONFIGURACIÓN COMPLETADA"
    echo "======================================"
    echo ""
    echo "Ahora puedes conectarte con:"
    echo "  ssh windows-grabacion"
    echo ""
    echo "O usar los scripts:"
    echo "  ./conectar_windows.sh"
    echo "  ./verificar_windows.sh"
    echo "  ./monitorear_grabacion.sh"
    echo ""
    
else
    echo ""
    echo "   ❌ No se pudo conectar"
    echo ""
    echo "Posibles causas:"
    echo "  - Usuario incorrecto"
    echo "  - Contraseña incorrecta"
    echo "  - SSH no permite autenticación por contraseña"
    echo ""
    echo "Soluciones:"
    echo "  1. Verificar nombre de usuario con: whoami (en Windows)"
    echo "  2. Verificar que SSH permite passwords en Windows:"
    echo "     Editar: C:\\ProgramData\\ssh\\sshd_config"
    echo "     Verificar: PasswordAuthentication yes"
    echo "     Reiniciar: Restart-Service sshd"
    exit 1
fi
