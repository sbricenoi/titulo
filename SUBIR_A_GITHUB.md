# 📤 Subir Proyecto a GitHub

## 🎯 Pasos para Crear Repositorio

### 1. Crear Repositorio en GitHub

Te acabo de abrir: https://github.com/new

**Configuración recomendada:**

```
Repository name:        sistema-monitoreo-hurones
Description:           Sistema de grabación y análisis IA para monitoreo de hurones con YOLOv8
Visibility:            🔒 Private (IMPORTANTE: tiene credenciales en historial)
Initialize:            ❌ NO marcar ninguna opción (ya tenemos README, .gitignore)
```

**⚠️ IMPORTANTE:** Debe ser **PRIVADO** porque aunque el código no tiene credenciales, es tu proyecto de tesis.

Click en **"Create repository"**

---

### 2. Conectar Repositorio Local con GitHub

GitHub te mostrará instrucciones. Copia los comandos o usa estos:

```bash
cd /Users/sbriceno/Documents/projects/titulo

# Agregar remote
git remote add origin https://github.com/TU-USUARIO/sistema-monitoreo-hurones.git

# Verificar
git remote -v
```

---

### 3. Subir Código

```bash
# Push a main
git push -u origin main

# Verificar
git log --oneline -3
```

---

## ✅ Después de Subir

### URLs del Proyecto

```
Repositorio:  https://github.com/TU-USUARIO/sistema-monitoreo-hurones
Clone URL:    https://github.com/TU-USUARIO/sistema-monitoreo-hurones.git
```

### Para Clonar en Windows

El instalador automático (`INSTALAR_TODO_WINDOWS.ps1`) te pedirá la URL:

```
URL del repositorio GitHub: https://github.com/TU-USUARIO/sistema-monitoreo-hurones.git
```

### Para Clonar en Lightsail

```bash
ssh ubuntu@3.147.46.191
cd ~
git clone https://github.com/TU-USUARIO/sistema-monitoreo-hurones.git titulo
```

---

## 🔐 Seguridad

### ✅ Archivos Protegidos (NO están en el repo)

El `.gitignore` protege:
- ✅ `.env` (credenciales)
- ✅ `*.pem` (SSH keys)
- ✅ `*.mp4` (videos)
- ✅ `*.jpg` (frames)
- ✅ `*.db` (base de datos)
- ✅ `logs/` (logs)

### ⚠️ Verificación Final

Antes de hacer público (si alguna vez lo haces):

```bash
# Verificar que no hay secretos
git log --all --full-history -- "**/*.env"
git log --all --full-history -- "**/*.pem"

# No debe retornar nada
```

---

## 📊 Estado Actual

```
Commits locales:  18
Remote:          ❌ No configurado
Branch:          main
Estado:          Clean working tree
```

---

## 🚀 Comandos Completos

```bash
cd /Users/sbriceno/Documents/projects/titulo

# 1. Crear repo en GitHub (manual en navegador)
# 2. Agregar remote
git remote add origin https://github.com/TU-USUARIO/sistema-monitoreo-hurones.git

# 3. Push
git push -u origin main

# 4. Verificar
git remote -v
git log --oneline -5
```

---

**¿Ya creaste el repositorio en GitHub?** Avísame el nombre de usuario y nombre del repo para configurar el remote automáticamente.
