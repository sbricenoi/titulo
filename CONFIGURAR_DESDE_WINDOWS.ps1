# =============================================
# Configurar SSH y Clonar Proyecto
# Ejecutar en Windows como Administrador
# =============================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CONFIGURACIÓN AUTOMÁTICA SSH + PROYECTO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Variables
$MAC_IP = "192.168.0.3"  # Ajustar si es necesario
$GITHUB_REPO = "https://github.com/sbricenoi/titulo.git"
$PROJECT_PATH = "C:\titulo"

# 1. Verificar si es administrador
Write-Host "1️⃣  Verificando permisos..." -ForegroundColor Yellow
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "   ❌ Este script debe ejecutarse como Administrador" -ForegroundColor Red
    Write-Host ""
    Write-Host "   Pasos:" -ForegroundColor Yellow
    Write-Host "   1. Click derecho en este archivo" -ForegroundColor Yellow
    Write-Host "   2. Seleccionar 'Ejecutar como administrador'" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host "   ✅ Ejecutando como Administrador" -ForegroundColor Green
Write-Host ""

# 2. Instalar/Verificar OpenSSH Server
Write-Host "2️⃣  Configurando OpenSSH Server..." -ForegroundColor Yellow

$sshInstalled = Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH.Server*' | Select-Object -ExpandProperty State

if ($sshInstalled -ne "Installed") {
    Write-Host "   Instalando OpenSSH Server..." -ForegroundColor Yellow
    Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
    Write-Host "   ✅ OpenSSH Server instalado" -ForegroundColor Green
} else {
    Write-Host "   ✅ OpenSSH Server ya instalado" -ForegroundColor Green
}

# Iniciar y configurar servicio
Write-Host "   Iniciando servicio SSH..." -ForegroundColor Yellow
Start-Service sshd -ErrorAction SilentlyContinue
Set-Service -Name sshd -StartupType 'Automatic'
Write-Host "   ✅ Servicio SSH configurado" -ForegroundColor Green

# Configurar firewall
Write-Host "   Configurando firewall..." -ForegroundColor Yellow
$firewallRule = Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -ErrorAction SilentlyContinue
if (-not $firewallRule) {
    New-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -DisplayName 'OpenSSH Server (sshd)' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22
    Write-Host "   ✅ Regla de firewall creada" -ForegroundColor Green
} else {
    Write-Host "   ✅ Regla de firewall ya existe" -ForegroundColor Green
}

Write-Host ""

# 3. Mostrar información de conexión
Write-Host "3️⃣  Información de conexión:" -ForegroundColor Yellow
$username = $env:USERNAME
$computername = $env:COMPUTERNAME
$ipAddress = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.*"}).IPAddress

Write-Host "   Usuario: $username" -ForegroundColor Cyan
Write-Host "   Computadora: $computername" -ForegroundColor Cyan
Write-Host "   IP: $ipAddress" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Desde el Mac, conecta con:" -ForegroundColor Green
Write-Host "   ssh $username@$ipAddress" -ForegroundColor White
Write-Host ""

# 4. Verificar/Instalar Git
Write-Host "4️⃣  Verificando Git..." -ForegroundColor Yellow
$gitInstalled = Get-Command git -ErrorAction SilentlyContinue

if (-not $gitInstalled) {
    Write-Host "   ❌ Git no está instalado" -ForegroundColor Red
    Write-Host ""
    Write-Host "   Opciones:" -ForegroundColor Yellow
    Write-Host "   A) Instalar con winget (automático)" -ForegroundColor Yellow
    Write-Host "   B) Saltar por ahora (instalar manualmente después)" -ForegroundColor Yellow
    Write-Host ""
    $choice = Read-Host "   Selecciona [A/B]"
    
    if ($choice -eq "A" -or $choice -eq "a") {
        Write-Host "   Instalando Git con winget..." -ForegroundColor Yellow
        winget install --id Git.Git -e --source winget --silent
        
        # Recargar PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        Write-Host "   ✅ Git instalado" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Saltando instalación de Git" -ForegroundColor Yellow
        Write-Host "   Instala Git manualmente desde: https://git-scm.com/download/win" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ✅ Git ya instalado: $(git --version)" -ForegroundColor Green
}

Write-Host ""

# 5. Clonar repositorio (si Git está instalado)
$gitNowInstalled = Get-Command git -ErrorAction SilentlyContinue

if ($gitNowInstalled) {
    Write-Host "5️⃣  Clonando repositorio..." -ForegroundColor Yellow
    
    if (Test-Path $PROJECT_PATH) {
        Write-Host "   ⚠️  El proyecto ya existe en $PROJECT_PATH" -ForegroundColor Yellow
        $overwrite = Read-Host "   ¿Quieres eliminarlo y clonar de nuevo? [S/N]"
        
        if ($overwrite -eq "S" -or $overwrite -eq "s") {
            Write-Host "   Eliminando proyecto existente..." -ForegroundColor Yellow
            Remove-Item -Path $PROJECT_PATH -Recurse -Force
        } else {
            Write-Host "   ⚠️  Manteniendo proyecto existente" -ForegroundColor Yellow
            $PROJECT_PATH = $null
        }
    }
    
    if ($PROJECT_PATH) {
        Write-Host "   Clonando desde GitHub..." -ForegroundColor Yellow
        git clone $GITHUB_REPO $PROJECT_PATH
        
        if (Test-Path $PROJECT_PATH) {
            Write-Host "   ✅ Proyecto clonado exitosamente" -ForegroundColor Green
            Write-Host "   Ubicación: $PROJECT_PATH" -ForegroundColor Cyan
        } else {
            Write-Host "   ❌ Error al clonar repositorio" -ForegroundColor Red
        }
    }
} else {
    Write-Host "5️⃣  ⚠️  Saltando clonado (Git no disponible)" -ForegroundColor Yellow
}

Write-Host ""

# 6. Crear carpeta .ssh y preparar para clave pública
Write-Host "6️⃣  Preparando carpeta SSH..." -ForegroundColor Yellow
$sshPath = "$env:USERPROFILE\.ssh"

if (-not (Test-Path $sshPath)) {
    New-Item -Path $sshPath -ItemType Directory | Out-Null
    Write-Host "   ✅ Carpeta .ssh creada" -ForegroundColor Green
} else {
    Write-Host "   ✅ Carpeta .ssh ya existe" -ForegroundColor Green
}

# Crear archivo authorized_keys vacío si no existe
$authorizedKeysPath = "$sshPath\authorized_keys"
if (-not (Test-Path $authorizedKeysPath)) {
    New-Item -Path $authorizedKeysPath -ItemType File | Out-Null
    Write-Host "   ✅ Archivo authorized_keys creado" -ForegroundColor Green
} else {
    Write-Host "   ✅ Archivo authorized_keys ya existe" -ForegroundColor Green
}

Write-Host ""

# 7. Resumen final
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ✅ CONFIGURACIÓN COMPLETADA" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📋 PRÓXIMOS PASOS:" -ForegroundColor Yellow
Write-Host ""

Write-Host "1️⃣  DESDE TU MAC, configura SSH:" -ForegroundColor Cyan
Write-Host "   cd ~/Documents/projects/titulo" -ForegroundColor White
Write-Host "   ./configurar_ssh_windows.sh" -ForegroundColor White
Write-Host ""
Write-Host "   Cuando te pida el usuario, ingresa: $username" -ForegroundColor Yellow
Write-Host "   PIN/Contraseña: 341341" -ForegroundColor Yellow
Write-Host ""

Write-Host "2️⃣  VERIFICAR conexión desde Mac:" -ForegroundColor Cyan
Write-Host "   ./verificar_windows.sh" -ForegroundColor White
Write-Host ""

if (Test-Path $PROJECT_PATH) {
    Write-Host "3️⃣  INSTALAR el sistema de grabación:" -ForegroundColor Cyan
    Write-Host "   Opción A - Desde Windows:" -ForegroundColor White
    Write-Host "   cd $PROJECT_PATH" -ForegroundColor White
    Write-Host "   .\INSTALAR_SIMPLE.bat" -ForegroundColor White
    Write-Host ""
    Write-Host "   Opción B - Desde Mac (remoto):" -ForegroundColor White
    Write-Host "   ssh windows-grabacion `"cd C:\titulo && INSTALAR_SIMPLE.bat`"" -ForegroundColor White
} else {
    Write-Host "3️⃣  CLONAR el proyecto:" -ForegroundColor Cyan
    Write-Host "   cd C:\" -ForegroundColor White
    Write-Host "   git clone $GITHUB_REPO" -ForegroundColor White
    Write-Host "   cd titulo" -ForegroundColor White
    Write-Host "   .\INSTALAR_SIMPLE.bat" -ForegroundColor White
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "💡 TIP: Deja este PowerShell abierto para copiar el usuario si lo necesitas" -ForegroundColor Yellow
Write-Host ""

Read-Host "Presiona Enter para salir"
