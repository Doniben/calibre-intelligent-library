# Guía de Instalación

## Requisitos Previos

### Software
- **Calibre** 5.0 o superior
- **Python** 3.9 o superior
- **Git** (opcional, para desarrollo)

### Hardware Recomendado
- **RAM**: Mínimo 8 GB, recomendado 16 GB
- **Disco**: 15-20 GB libres (para embeddings y chunks)
- **CPU**: Multi-core recomendado (acelera indexación)

### Sistema Operativo
- macOS 10.14+
- Linux (Ubuntu 20.04+, Fedora 35+)
- Windows 10/11

---

## Instalación Rápida

### 1. Descargar el Plugin

```bash
# Opción A: Desde releases de GitHub
# Descarga calibre-intelligent-library-v1.0.0.zip

# Opción B: Clonar repositorio (desarrollo)
git clone https://github.com/Doniben/calibre-intelligent-library.git
cd calibre-intelligent-library
```

### 2. Instalar Dependencias del Backend

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
# En macOS/Linux:
source venv/bin/activate
# En Windows:
venv\Scripts\activate

# Instalar dependencias
pip install -r backend/requirements.txt
```

### 3. Instalar Plugin en Calibre

1. Abrir Calibre
2. Ir a **Preferencias** → **Plugins**
3. Click en **Cargar plugin desde archivo**
4. Seleccionar `plugin/calibre-intelligent-library.zip`
5. Click en **Sí** para confirmar
6. Reiniciar Calibre

### 4. Primera Configuración

1. En Calibre, ir a **Plugins** → **Biblioteca Inteligente** → **Configuración**
2. Verificar ruta a Calibre Library (auto-detectada)
3. Click en **Indexar Biblioteca**
4. Esperar 12-14 horas (proceso en background)

---

## Instalación Detallada

### Paso 1: Preparar el Entorno

#### macOS

```bash
# Instalar Homebrew (si no lo tienes)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instalar Python 3.9+
brew install python@3.9

# Verificar instalación
python3 --version  # Debe ser 3.9 o superior
```

#### Linux (Ubuntu/Debian)

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python y dependencias
sudo apt install python3.9 python3.9-venv python3-pip

# Verificar instalación
python3 --version
```

#### Windows

1. Descargar Python desde [python.org](https://www.python.org/downloads/)
2. Instalar marcando "Add Python to PATH"
3. Verificar en CMD: `python --version`

### Paso 2: Instalar Backend

```bash
# Navegar al directorio del proyecto
cd calibre-intelligent-library

# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate  # macOS/Linux
# o
venv\Scripts\activate  # Windows

# Actualizar pip
pip install --upgrade pip

# Instalar dependencias
pip install -r backend/requirements.txt

# Verificar instalación
python backend/server.py --help
```

### Paso 3: Configurar Backend

```bash
# Copiar archivo de configuración de ejemplo
cp backend/config.example.json backend/config.json

# Editar configuración (opcional)
nano backend/config.json
```

**Configuración por defecto:**
```json
{
  "host": "127.0.0.1",
  "port": 8765,
  "calibre_library_path": "auto-detect",
  "embedding_model": "all-MiniLM-L6-v2",
  "chunk_size": 500,
  "chunk_overlap": 50
}
```

### Paso 4: Probar Backend

```bash
# Iniciar servidor manualmente
python backend/server.py

# En otra terminal, probar health check
curl http://127.0.0.1:8765/health

# Debería responder:
# {"status":"healthy","version":"1.0.0"}
```

### Paso 5: Empaquetar Plugin

```bash
# Desde el directorio raíz del proyecto
cd plugin
zip -r calibre-intelligent-library.zip *
```

### Paso 6: Instalar Plugin en Calibre

#### Método 1: Interfaz Gráfica

1. Abrir Calibre
2. **Preferencias** (Ctrl+P / Cmd+,)
3. **Plugins** (en la sección "Avanzado")
4. **Cargar plugin desde archivo**
5. Seleccionar `plugin/calibre-intelligent-library.zip`
6. Click **Sí** para confirmar instalación
7. Click **Aplicar** y reiniciar Calibre

#### Método 2: Línea de Comandos

```bash
# Instalar plugin vía CLI de Calibre
calibre-customize -a plugin/calibre-intelligent-library.zip

# Verificar instalación
calibre-customize -l | grep "Biblioteca Inteligente"
```

### Paso 7: Configuración Inicial del Plugin

1. Reiniciar Calibre
2. Buscar botón **"Búsqueda Inteligente"** en toolbar
3. Click derecho → **Configuración**
4. Verificar configuración:
   - **Ruta Calibre Library**: Auto-detectada
   - **Puerto Backend**: 8765
   - **Modelo**: all-MiniLM-L6-v2

### Paso 8: Primera Indexación

1. Click en **Plugins** → **Biblioteca Inteligente** → **Indexar**
2. Seleccionar opciones:
   - ☑ Indexar resúmenes
   - ☑ Indexar tablas de contenidos
   - ☑ Indexar texto completo (opcional, más lento)
3. Click **Iniciar Indexación**
4. Monitorear progreso en ventana de estado

**Tiempo estimado:**
- Solo resúmenes + TOC: 2-3 horas
- Texto completo: 12-14 horas

**Nota**: Puedes seguir usando Calibre durante la indexación.

---

## Instalación desde Backup

Si ya tienes una instalación previa y quieres migrarla:

### 1. Copiar Datos

```bash
# En computadora vieja, crear backup
cd "Calibre Library"
tar -czf biblioteca-backup.tar.gz .biblioteca_inteligente/

# Copiar a USB o nube
cp biblioteca-backup.tar.gz /Volumes/USB/
```

### 2. Restaurar en Nueva Computadora

```bash
# Copiar Calibre Library completa
cp -r /Volumes/USB/"Calibre Library" ~/

# O solo restaurar datos procesados
cd ~/Calibre\ Library
tar -xzf /Volumes/USB/biblioteca-backup.tar.gz
```

### 3. Instalar Plugin

Seguir pasos 1-6 de instalación normal.

### 4. Verificar Instalación

1. Abrir Calibre
2. Plugin detectará instalación existente
3. Verificará rutas y actualizará config.json
4. Listo para usar (sin reindexar)

---

## Verificación de Instalación

### Checklist

- [ ] Calibre 5.0+ instalado
- [ ] Python 3.9+ instalado
- [ ] Backend dependencies instaladas
- [ ] Backend responde en http://127.0.0.1:8765/health
- [ ] Plugin visible en Calibre
- [ ] Botón "Búsqueda Inteligente" en toolbar
- [ ] Indexación completada (o en progreso)

### Prueba Rápida

1. Click en **Búsqueda Inteligente**
2. Escribir: "libros sobre historia"
3. Debería mostrar resultados relevantes
4. Seleccionar un libro
5. En panel de chat, preguntar: "¿De qué trata este libro?"
6. Kiro debería responder con análisis

---

## Solución de Problemas

### Backend no inicia

**Error**: `Connection refused` al abrir plugin

**Solución**:
```bash
# Verificar que backend esté corriendo
ps aux | grep "server.py"

# Si no está corriendo, iniciar manualmente
cd calibre-intelligent-library
source venv/bin/activate
python backend/server.py
```

### Plugin no aparece en Calibre

**Solución**:
1. Verificar que el .zip esté bien formado
2. Revisar logs de Calibre: **Preferencias** → **Plugins** → **Personalizar plugin** → **Ver logs**
3. Reinstalar plugin

### Indexación muy lenta

**Solución**:
- Cerrar otras aplicaciones pesadas
- Verificar que tienes suficiente RAM libre
- Considerar indexar solo resúmenes + TOC primero
- Indexar texto completo después

### Kiro no responde

**Solución**:
```bash
# Verificar que Kiro CLI esté instalado
which kiro-cli

# Probar Kiro manualmente
kiro-cli chat

# Verificar suscripción Q Developer
kiro-cli auth status
```

### Error de permisos en macOS

**Solución**:
1. **Preferencias del Sistema** → **Seguridad y Privacidad**
2. **Privacidad** → **Acceso total al disco**
3. Agregar Calibre y Terminal

---

## Actualización

### Actualizar Plugin

```bash
# Descargar nueva versión
git pull origin main

# Reempaquetar plugin
cd plugin
zip -r calibre-intelligent-library.zip *

# Reinstalar en Calibre
# Preferencias → Plugins → Cargar plugin desde archivo
```

### Actualizar Backend

```bash
# Activar entorno virtual
source venv/bin/activate

# Actualizar dependencias
pip install -r backend/requirements.txt --upgrade

# Reiniciar servidor
pkill -f "server.py"
python backend/server.py
```

---

## Desinstalación

### Remover Plugin

1. Calibre → **Preferencias** → **Plugins**
2. Buscar "Biblioteca Inteligente"
3. Click derecho → **Eliminar**
4. Reiniciar Calibre

### Limpiar Datos

```bash
# Eliminar datos procesados (mantiene libros)
rm -rf "Calibre Library/.biblioteca_inteligente"

# Eliminar backend
rm -rf calibre-intelligent-library
```

**Nota**: Esto NO elimina tus libros ni metadata de Calibre.

---

## Soporte

### Logs

**Backend logs**:
```bash
tail -f /tmp/kiro-log/backend.log
```

**Plugin logs**:
Calibre → **Preferencias** → **Plugins** → **Biblioteca Inteligente** → **Ver logs**

### Reportar Problemas

1. Recopilar logs
2. Crear issue en GitHub: [github.com/Doniben/calibre-intelligent-library/issues](https://github.com/Doniben/calibre-intelligent-library/issues)
3. Incluir:
   - Sistema operativo
   - Versión de Calibre
   - Versión de Python
   - Logs relevantes
   - Pasos para reproducir

---

## Próximos Pasos

Una vez instalado:
1. Leer [Tutorial de Uso](tutorial.md)
2. Explorar [Ejemplos de Búsqueda](examples.md)
3. Ver [FAQ](faq.md)
