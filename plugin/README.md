# Biblioteca Inteligente - Plugin de Calibre

Plugin de Calibre para búsqueda semántica y asistente IA.

## Características

- 🔍 **Búsqueda Semántica**: Busca libros por conceptos, no solo palabras clave
- 💬 **Asistente Kiro**: Pregunta sobre los libros y obtén recomendaciones
- 📊 **Resultados Relevantes**: Muestra capítulos específicos relevantes
- ⚡ **Integración Completa**: Funciona directamente en Calibre

## Instalación

### 1. Instalar el Plugin

1. Abre Calibre
2. Ve a **Preferencias** → **Plugins**
3. Click en **Cargar plugin desde archivo**
4. Selecciona `biblioteca-inteligente.zip`
5. Click **Sí** para confirmar
6. Reinicia Calibre

### 2. Configurar Backend

El plugin requiere que el servidor backend esté corriendo:

```bash
cd calibre-intelligent-library
source venv/bin/activate
python backend/server.py
```

El servidor debe estar corriendo en `http://127.0.0.1:8765`

### 3. Verificar Configuración

1. En Calibre, ve a **Preferencias** → **Plugins**
2. Busca "Biblioteca Inteligente"
3. Click en **Personalizar plugin**
4. Click en **Test Connection** para verificar

## Uso

### Búsqueda Semántica

1. Click en el botón **"Búsqueda Inteligente"** en la barra de herramientas
   - O usa el atajo: `Ctrl+Shift+I`

2. Escribe tu búsqueda conceptual:
   - "libros sobre inteligencia artificial"
   - "feminismo interseccional"
   - "historia de Roma"

3. Los resultados muestran:
   - Título y autor
   - Capítulo relevante
   - Porcentaje de similitud

4. Doble-click en un resultado para abrir el libro

### Asistente Kiro

1. Después de buscar, selecciona uno o más libros

2. Click en **"Preguntar a Kiro"**

3. Escribe tu pregunta:
   - "¿Cuál es más académico?"
   - "¿Qué libro debería leer primero?"
   - "Compara estos libros"

4. Kiro responderá con análisis basado en los libros seleccionados

5. Puedes continuar la conversación en el panel de chat

## Configuración

### Backend

- **Host**: Dirección del servidor (default: 127.0.0.1)
- **Port**: Puerto del servidor (default: 8765)

### Búsqueda

- **Results limit**: Número máximo de resultados (5-100)
- **Min similarity**: Similitud mínima para mostrar (0-100%)

## Requisitos

- Calibre 5.0 o superior
- Python 3.9+
- Backend server corriendo
- Biblioteca indexada (ver documentación principal)

## Solución de Problemas

### "No se pudo conectar al backend"

- Verifica que el servidor esté corriendo
- Verifica host y puerto en configuración
- Prueba la conexión con: `curl http://127.0.0.1:8765/health`

### "Index not ready"

- La biblioteca no está indexada
- Ejecuta el proceso de indexación (ver docs)

### El botón no aparece

- Reinicia Calibre después de instalar
- Verifica que el plugin esté habilitado en Preferencias → Plugins

## Desarrollo

### Construir Plugin

```bash
cd plugin
./build.sh
```

### Estructura

```
plugin/
├── __init__.py              # Entry point
├── ui.py                    # Main action
├── config.py                # Configuration widget
├── search_dialog.py         # Search interface
└── build.sh                 # Build script
```

## Licencia

MIT License
