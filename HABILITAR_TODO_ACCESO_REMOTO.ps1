# =============================================
# HABILITAR TODO ACCESO REMOTO EN WINDOWS
# Ejecutar como Administrador
# =============================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  HABILITAR TODO ACCESO REMOTO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar permisos
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "❌ Este script debe ejecutarse como Administrador" -ForegroundColor Red
    Write-Host ""
    Write-Host "Click derecho > Ejecutar como administrador" -ForegroundColor Yellow
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host "✅ Ejecutando como Administrador" -ForegroundColor Green
Write-Host ""

# ==================================================
# 1. HABILITAR SSH
# ==================================================
Write-Host "1️⃣  CONFIGURANDO SSH..." -ForegroundColor Yellow

# Instalar OpenSSH Server
$sshInstalled = Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH.Server*' | Select-Object -ExpandProperty State

if ($sshInstalled -ne "Installed") {
    Write-Host "   Instalando OpenSSH Server..." -ForegroundColor Yellow
    Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0 | Out-Null
}

# Iniciar servicio
Start-Service sshd -ErrorAction SilentlyContinue
Set-Service -Name sshd -StartupType 'Automatic'

# Configurar firewall
$sshFirewall = Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -ErrorAction SilentlyContinue
if (-not $sshFirewall) {
    New-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -DisplayName 'OpenSSH Server (sshd)' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22 | Out-Null
}

# Configurar SSH para permitir contraseñas
$sshdConfig = "C:\ProgramData\ssh\sshd_config"
if (Test-Path $sshdConfig) {
    $config = Get-Content $sshdConfig
    $newConfig = @()
    $passwordAuthFound = $false
    
    foreach ($line in $config) {
        if ($line -match "^\s*#?\s*PasswordAuthentication") {
            $newConfig += "PasswordAuthentication yes"
            $passwordAuthFound = $true
        }
        elseif ($line -match "^\s*Match Group administrators") {
            $newConfig += "# $line"
        }
        elseif ($line -match "^\s*AuthorizedKeysFile.*__PROGRAMDATA__") {
            $newConfig += "# $line"
        }
        else {
            $newConfig += $line
        }
    }
    
    if (-not $passwordAuthFound) {
        $newConfig += "PasswordAuthentication yes"
    }
    
    $newConfig | Set-Content $sshdConfig
    Restart-Service sshd
}

Write-Host "   ✅ SSH configurado (puerto 22)" -ForegroundColor Green

# ==================================================
# 2. HABILITAR RDP (ESCRITORIO REMOTO)
# ==================================================
Write-Host ""
Write-Host "2️⃣  CONFIGURANDO RDP (ESCRITORIO REMOTO)..." -ForegroundColor Yellow

# Habilitar RDP
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name "fDenyTSConnections" -Value 0

# Habilitar en firewall
Enable-NetFirewallRule -DisplayGroup "Remote Desktop" -ErrorAction SilentlyContinue

# Permitir NLA (Network Level Authentication) - opcional
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp' -Name "UserAuthentication" -Value 0

Write-Host "   ✅ RDP habilitado (puerto 3389)" -ForegroundColor Green

# ==================================================
# 3. HABILITAR WinRM (POWERSHELL REMOTO)
# ==================================================
Write-Host ""
Write-Host "3️⃣  CONFIGURANDO WinRM (PowerShell Remoto)..." -ForegroundColor Yellow

# Habilitar WinRM
Enable-PSRemoting -Force -SkipNetworkProfileCheck | Out-Null

# Configurar para permitir conexiones desde red privada
Set-Item WSMan:\localhost\Client\TrustedHosts -Value "*" -Force

# Configurar firewall
Enable-NetFirewallRule -Name "WINRM-HTTP-In-TCP" -ErrorAction SilentlyContinue

Write-Host "   ✅ WinRM habilitado (puerto 5985)" -ForegroundColor Green

# ==================================================
# 4. HABILITAR COMPARTIR ARCHIVOS (SMB)
# ==================================================
Write-Host ""
Write-Host "4️⃣  CONFIGURANDO COMPARTIR ARCHIVOS..." -ForegroundColor Yellow

# Habilitar File and Printer Sharing
Enable-NetFirewallRule -DisplayGroup "File and Printer Sharing" -ErrorAction SilentlyContinue

# Habilitar descubrimiento de red
Get-NetFirewallRule -DisplayGroup "Network Discovery" | Enable-NetFirewallRule -ErrorAction SilentlyContinue

Write-Host "   ✅ Compartir archivos habilitado (puerto 445)" -ForegroundColor Green

# ==================================================
# 5. DESHABILITAR FIREWALL (TEMPORAL - SOLO PARA PRUEBAS)
# ==================================================
Write-Host ""
Write-Host "5️⃣  FIREWALL..." -ForegroundColor Yellow
Write-Host ""
Write-Host "   ¿Quieres DESHABILITAR el firewall temporalmente para pruebas?" -ForegroundColor Yellow
Write-Host "   (Útil si aún tienes problemas de conexión)" -ForegroundColor Yellow
Write-Host ""
$disableFirewall = Read-Host "   Deshabilitar firewall? [S/N]"

if ($disableFirewall -eq "S" -or $disableFirewall -eq "s") {
    Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False
    Write-Host "   ⚠️  Firewall DESHABILITADO (recuerda habilitarlo después)" -ForegroundColor Yellow
} else {
    Write-Host "   ✅ Firewall mantenido activo (con reglas necesarias)" -ForegroundColor Green
}

# ==================================================
# RESUMEN FINAL
# ==================================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ✅ CONFIGURACIÓN COMPLETADA" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Obtener información del sistema
$username = $env:USERNAME
$computername = $env:COMPUTERNAME
$ipAddress = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.*"}).IPAddress

Write-Host "📊 INFORMACIÓN DE CONEXIÓN:" -ForegroundColor Yellow
Write-Host ""
Write-Host "   Usuario: $username" -ForegroundColor Cyan
Write-Host "   Computadora: $computername" -ForegroundColor Cyan
Write-Host "   IP: $ipAddress" -ForegroundColor Cyan
Write-Host ""

Write-Host "🎯 SERVICIOS HABILITADOS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "   ✅ SSH (puerto 22)" -ForegroundColor Green
Write-Host "      Comando desde Mac:" -ForegroundColor White
Write-Host "      ssh $username@$ipAddress" -ForegroundColor Gray
Write-Host ""

Write-Host "   ✅ RDP - Escritorio Remoto (puerto 3389)" -ForegroundColor Green
Write-Host "      Desde Mac: usar 'Microsoft Remote Desktop'" -ForegroundColor White
Write-Host "      Conectar a: $ipAddress" -ForegroundColor Gray
Write-Host ""

Write-Host "   ✅ WinRM - PowerShell Remoto (puerto 5985)" -ForegroundColor Green
Write-Host "      Para ejecutar comandos remotos" -ForegroundColor White
Write-Host ""

Write-Host "   ✅ SMB - Compartir Archivos (puerto 445)" -ForegroundColor Green
Write-Host "      Desde Mac: Finder > Go > Connect to Server" -ForegroundColor White
Write-Host "      smb://$ipAddress" -ForegroundColor Gray
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📝 PRÓXIMOS PASOS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. DESDE TU MAC, probar SSH:" -ForegroundColor Cyan
Write-Host "   ssh $username@$ipAddress" -ForegroundColor White
Write-Host "   Contraseña/PIN: 341341" -ForegroundColor Gray
Write-Host ""

Write-Host "2. O ejecutar el script de configuración:" -ForegroundColor Cyan
Write-Host "   cd ~/Documents/projects/titulo" -ForegroundColor White
Write-Host "   ./configurar_ssh_windows.sh" -ForegroundColor White
Write-Host ""

Write-Host "3. Verificar estado:" -ForegroundColor Cyan
Write-Host "   ./verificar_windows.sh" -ForegroundColor White
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "💡 TIP: Ahora puedes administrar este Windows 100% desde tu Mac" -ForegroundColor Green
Write-Host ""

Read-Host "Presiona Enter para salir"
