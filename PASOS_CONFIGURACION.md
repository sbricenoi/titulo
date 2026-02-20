# Pasos para Configurar Acceso SSH

## 🎯 Situación Actual

- ✅ Windows está en red: `192.168.0.15`
- ✅ SSH está habilitado en Windows (puerto 22 abierto)
- ✅ Clave SSH generada en Mac
- ✅ Configuración SSH creada en Mac
- ❌ **FALTA: Nombre exacto del usuario de Windows**

---

## 📋 PASO 1: Obtener Usuario de Windows

Ve al Windows (192.168.0.15) y ejecuta:

### Opción A: CMD
```cmd
whoami
```

**Ejemplo de salida:**
```
DESKTOP-ABC123\usuario
```
o
```
usuario
```

### Opción B: PowerShell
```powershell
$env:USERNAME
```

### Opción C: Configuración de Windows
1. Abrir Configuración (Win + I)
2. Ir a `Cuentas > Tu información`
3. Ver el nombre que aparece

---

## 📋 PASO 2: Ejecutar Script de Configuración

Una vez que tengas el nombre de usuario:

```bash
cd /Users/sbriceno/Documents/projects/titulo
./configurar_ssh_windows.sh
```

El script te pedirá:
1. El usuario de Windows
2. La contraseña (PIN: 341341)

Y automáticamente:
- ✅ Probará la conexión
- ✅ Copiará tu clave SSH al Windows
- ✅ Configurará acceso sin contraseña
- ✅ Actualizará ~/.ssh/config

---

## 📋 PASO 3: Verificar Conexión

```bash
# Probar conexión:
ssh windows-grabacion

# O con el script:
./verificar_windows.sh
```

---

## 🔧 Si el Script No Funciona (Manual)

### 1. Conectar manualmente
```bash
ssh USUARIO@192.168.0.15
# Reemplaza USUARIO con el que obtuviste en PASO 1
```

### 2. Copiar clave SSH manualmente
```bash
cat ~/.ssh/id_ed25519.pub | ssh USUARIO@192.168.0.15 "mkdir -p .ssh && cat >> .ssh/authorized_keys"
```

### 3. Actualizar ~/.ssh/config
```bash
nano ~/.ssh/config

# Cambiar la línea "User Administrator" por:
User TU_USUARIO_REAL
```

---

## ❓ Formatos Comunes de Usuario en Windows

| Tipo de Cuenta | Formato de Usuario |
|----------------|-------------------|
| Cuenta Local | `usuario` |
| Cuenta Local con Dominio | `NOMBRE-PC\usuario` |
| Cuenta Microsoft | `nombre.apellido` o el email |
| Cuenta Microsoft (formato interno) | Puede variar |

**Ejemplos reales:**
- `sbriceno`
- `DESKTOP-ABC123\sbriceno`
- `familia`
- `briceno.galimidi`

---

## 🆘 Troubleshooting

### "Permission denied"
- Verificar que el usuario es correcto
- Verificar la contraseña/PIN
- En Windows, editar `C:\ProgramData\ssh\sshd_config`:
  ```
  PasswordAuthentication yes
  ```
- Reiniciar SSH: `Restart-Service sshd`

### "Too many authentication failures"
- Demasiados intentos fallidos
- Esperar 1 minuto
- Verificar el usuario correcto con `whoami` en Windows

### "Connection refused"
- SSH no está corriendo
- En PowerShell (Admin): `Start-Service sshd`

---

## ✅ Después de Configurar

Podrás usar:

```bash
# Conectar:
ssh windows-grabacion

# Verificar estado:
./verificar_windows.sh

# Monitorear grabación:
./monitorear_grabacion.sh

# Ver logs:
./ver_logs_remoto.sh

# Ejecutar comandos:
ssh windows-grabacion "COMANDO"
```

---

## 🚀 Siguiente Paso: Instalar el Sistema

Una vez configurado SSH, instalar el sistema de grabación:

```bash
# Desde tu Mac, ejecutar en el Windows:
ssh windows-grabacion "cd C:\ && git clone https://github.com/sbricenoi/titulo.git"
ssh windows-grabacion "cd C:\titulo && INSTALAR_SIMPLE.bat"
```

---

**📝 NOTA:** El PIN es `341341` (según información proporcionada)
