# Calibre Intelligent Library

Sistema de búsqueda semántica y asistente de IA para bibliotecas de Calibre.

## 🎯 Objetivo

Crear un plugin de Calibre que permita:
- **Búsqueda semántica**: Encontrar libros por temas y conceptos, no solo por título/autor
- **Búsqueda en capítulos**: Localizar contenido específico dentro de los libros
- **Asistente conversacional**: Interactuar con Kiro CLI para obtener recomendaciones y análisis
- **Sistema portable**: Fácil migración entre computadoras

## 🏗️ Arquitectura

El sistema consta de dos componentes principales:

### 1. Plugin de Calibre (Frontend)
- Interfaz gráfica integrada en Calibre
- Botón de búsqueda inteligente en toolbar
- Panel de chat lateral con Kiro
- Ligero y fácil de instalar

### 2. Backend (Servidor Local)
- Servidor FastAPI que corre en background
- Gestión de embeddings y búsqueda vectorial
- Integración con Kiro CLI
- Procesamiento de texto y capítulos

## 📊 Características

- ✅ Búsqueda por similitud semántica usando embeddings
- ✅ Indexación de 80,000+ libros
- ✅ Extracción y búsqueda en tablas de contenidos
- ✅ Búsqueda dentro de capítulos
- ✅ Chat conversacional con Kiro CLI
- ✅ Sistema completamente local (sin APIs externas)
- ✅ Portable y fácil de respaldar

## 🚀 Instalación Rápida

```bash
# 1. Instalar plugin en Calibre
Preferencias → Plugins → Cargar plugin desde archivo

# 2. Primera indexación (12-14 horas)
Plugins → Biblioteca Inteligente → Indexar biblioteca

# 3. ¡Listo para usar!
```

## 📁 Estructura del Proyecto

```
calibre-intelligent-library/
├── README.md              # Este archivo
├── PLAN.md               # Plan de trabajo detallado
├── docs/                 # Documentación
│   ├── architecture.md   # Arquitectura del sistema
│   └── installation.md   # Guía de instalación
├── plugin/               # Plugin de Calibre
│   ├── __init__.py
│   ├── ui.py
│   └── ...
├── backend/              # Servidor backend
│   ├── server.py
│   ├── embeddings.py
│   ├── kiro_client.py
│   └── ...
└── tests/                # Tests unitarios
```

## 🛠️ Tecnologías

- **Plugin**: Python + PyQt5 (Calibre API)
- **Backend**: FastAPI + Uvicorn
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Vector Search**: FAISS
- **Database**: SQLite
- **IA**: Kiro CLI / Amazon Q Developer

## 📖 Documentación

- [Plan de Trabajo](PLAN.md) - Roadmap y tareas
- [Arquitectura](docs/architecture.md) - Diseño técnico detallado
- [Instalación](docs/installation.md) - Guía completa de instalación

## 🤝 Contribuir

Este es un proyecto personal, pero sugerencias y mejoras son bienvenidas.

## 📝 Licencia

MIT License

## 👤 Autor

Doniben
