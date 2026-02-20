# =============================================
# Habilitar Autenticación por Contraseña en SSH
# Ejecutar en Windows como Administrador
# =============================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  HABILITAR SSH PASSWORD AUTH" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar permisos de administrador
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

# Ruta del archivo de configuración
$sshdConfigPath = "C:\ProgramData\ssh\sshd_config"

if (-not (Test-Path $sshdConfigPath)) {
    Write-Host "❌ No se encontró el archivo sshd_config" -ForegroundColor Red
    Write-Host "   Ruta esperada: $sshdConfigPath" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   ¿SSH Server está instalado?" -ForegroundColor Yellow
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host "📝 Configurando SSH Server..." -ForegroundColor Yellow
Write-Host ""

# Leer configuración actual
$config = Get-Content $sshdConfigPath

# Hacer backup
$backupPath = "$sshdConfigPath.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
Copy-Item $sshdConfigPath $backupPath
Write-Host "✅ Backup creado: $backupPath" -ForegroundColor Green

# Configurar opciones necesarias
$newConfig = @()
$passwordAuthFound = $false
$pubkeyAuthFound = $false

foreach ($line in $config) {
    # Habilitar PasswordAuthentication
    if ($line -match "^\s*#?\s*PasswordAuthentication") {
        $newConfig += "PasswordAuthentication yes"
        $passwordAuthFound = $true
        Write-Host "✅ PasswordAuthentication habilitado" -ForegroundColor Green
    }
    # Habilitar PubkeyAuthentication
    elseif ($line -match "^\s*#?\s*PubkeyAuthentication") {
        $newConfig += "PubkeyAuthentication yes"
        $pubkeyAuthFound = $true
        Write-Host "✅ PubkeyAuthentication habilitado" -ForegroundColor Green
    }
    # Comentar Match Group administrators (problema común en Windows)
    elseif ($line -match "^\s*Match Group administrators") {
        $newConfig += "# $line  # Comentado automáticamente"
        Write-Host "✅ Match Group administrators comentado" -ForegroundColor Green
    }
    # Comentar AuthorizedKeysFile con __PROGRAMDATA__ (problema común)
    elseif ($line -match "^\s*AuthorizedKeysFile.*__PROGRAMDATA__") {
        $newConfig += "# $line  # Comentado automáticamente"
        Write-Host "✅ AuthorizedKeysFile __PROGRAMDATA__ comentado" -ForegroundColor Green
    }
    else {
        $newConfig += $line
    }
}

# Agregar opciones si no existían
if (-not $passwordAuthFound) {
    $newConfig += "PasswordAuthentication yes"
    Write-Host "✅ PasswordAuthentication agregado" -ForegroundColor Green
}

if (-not $pubkeyAuthFound) {
    $newConfig += "PubkeyAuthentication yes"
    Write-Host "✅ PubkeyAuthentication agregado" -ForegroundColor Green
}

# Asegurar que AuthorizedKeysFile apunta a la ubicación correcta
$authKeysLine = "AuthorizedKeysFile .ssh/authorized_keys"
if ($newConfig -notcontains $authKeysLine) {
    $newConfig += $authKeysLine
    Write-Host "✅ AuthorizedKeysFile configurado" -ForegroundColor Green
}

# Guardar nueva configuración
$newConfig | Set-Content $sshdConfigPath

Write-Host ""
Write-Host "📝 Reiniciando servicio SSH..." -ForegroundColor Yellow
Restart-Service sshd

Start-Sleep -Seconds 2

# Verificar que el servicio está corriendo
$service = Get-Service sshd
if ($service.Status -eq "Running") {
    Write-Host "✅ Servicio SSH reiniciado correctamente" -ForegroundColor Green
} else {
    Write-Host "❌ Problema al reiniciar SSH" -ForegroundColor Red
    Write-Host "   Estado: $($service.Status)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ✅ CONFIGURACIÓN COMPLETADA" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📋 INFORMACIÓN DE CONEXIÓN:" -ForegroundColor Yellow
Write-Host ""
Write-Host "   Usuario: $env:USERNAME" -ForegroundColor Cyan
Write-Host "   Computadora: $env:COMPUTERNAME" -ForegroundColor Cyan

$ipAddress = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.*"}).IPAddress
Write-Host "   IP: $ipAddress" -ForegroundColor Cyan
Write-Host ""

Write-Host "📝 DESDE TU MAC, prueba la conexión:" -ForegroundColor Yellow
Write-Host ""
Write-Host "   ssh $env:USERNAME@$ipAddress" -ForegroundColor White
Write-Host ""
Write-Host "   PIN: 341341" -ForegroundColor Yellow
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Read-Host "Presiona Enter para salir"
