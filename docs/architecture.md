# Arquitectura del Sistema

## Visión General

Calibre Intelligent Library es un sistema híbrido que combina un plugin ligero de Calibre con un backend robusto para búsqueda semántica y análisis conversacional.

## Componentes Principales

```
┌─────────────────────────────────────────────────────────┐
│                    Usuario                              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Calibre + Plugin (UI)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Búsqueda   │  │  Resultados  │  │  Chat Panel  │ │
│  │  Inteligente │  │    Tabla     │  │    (Kiro)    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP (localhost:8765)
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Backend Server (FastAPI)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Search     │  │    Kiro      │  │   Session    │ │
│  │   Engine     │  │   Client     │  │   Manager    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│    FAISS     │ │ SQLite   │ │  Kiro CLI    │
│  (Vectores)  │ │ (Chunks) │ │ (subprocess) │
└──────────────┘ └──────────┘ └──────────────┘
        │            │
        └────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────┐
│           Calibre Library (Filesystem)                  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  metadata.db (Calibre)                           │  │
│  │  [Autor]/[Libro]/libro.epub                      │  │
│  │  .biblioteca_inteligente/                        │  │
│  │    ├── embeddings.faiss                          │  │
│  │    ├── chunks.db                                 │  │
│  │    ├── conversations.db                          │  │
│  │    └── config.json                               │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Flujo de Datos

### 1. Búsqueda Semántica

```
Usuario escribe: "libros sobre feminismo interseccional"
    ↓
Plugin envía query a Backend: POST /search
    ↓
Backend convierte query a embedding (vector)
    ↓
FAISS busca vectores similares → IDs de chunks
    ↓
SQLite recupera texto + metadata de chunks
    ↓
Backend agrupa por libro y rankea resultados
    ↓
Plugin recibe JSON con libros + capítulos relevantes
    ↓
Plugin muestra resultados en tabla
```

### 2. Conversación con Kiro

```
Usuario selecciona 3 libros y pregunta: "¿Cuál es más académico?"
    ↓
Plugin envía: POST /ask/{session_id}
    body: {
        question: "¿Cuál es más académico?",
        context: [libro1, libro2, libro3]
    }
    ↓
Backend formatea contexto para Kiro:
    "Libros encontrados:
     1. Título: X, Autor: Y, Resumen: Z
     2. ...
     
     Pregunta del usuario: ¿Cuál es más académico?"
    ↓
Backend ejecuta: kiro-cli chat --prompt "..."
    ↓
Kiro analiza y responde
    ↓
Backend captura respuesta y la devuelve
    ↓
Plugin muestra respuesta en chat panel
    ↓
Usuario hace follow-up: "¿Por qué?"
    ↓
Kiro mantiene contexto de la conversación
```

## Estructura de Datos

### Base de Datos: chunks.db

```sql
-- Libros indexados
CREATE TABLE books (
    id INTEGER PRIMARY KEY,
    calibre_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    author TEXT,
    path TEXT NOT NULL,  -- Ruta relativa en Calibre Library
    summary TEXT,
    tags TEXT,  -- JSON array
    pubdate TEXT,
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Capítulos extraídos
CREATE TABLE chapters (
    id INTEGER PRIMARY KEY,
    book_id INTEGER NOT NULL,
    chapter_num INTEGER NOT NULL,
    title TEXT,
    file_path TEXT,  -- Archivo dentro del EPUB
    word_count INTEGER,
    FOREIGN KEY (book_id) REFERENCES books(id)
);

-- Chunks de texto con embeddings
CREATE TABLE chunks (
    id INTEGER PRIMARY KEY,
    chapter_id INTEGER NOT NULL,
    chunk_num INTEGER NOT NULL,
    text TEXT NOT NULL,
    embedding_id INTEGER NOT NULL,  -- Índice en FAISS
    start_pos INTEGER,
    end_pos INTEGER,
    FOREIGN KEY (chapter_id) REFERENCES chapters(id)
);

-- Índices para búsquedas rápidas
CREATE INDEX idx_books_calibre_id ON books(calibre_id);
CREATE INDEX idx_chapters_book_id ON chapters(book_id);
CREATE INDEX idx_chunks_chapter_id ON chunks(chapter_id);
CREATE INDEX idx_chunks_embedding_id ON chunks(embedding_id);
```

### Base de Datos: conversations.db

```sql
-- Sesiones de conversación
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,  -- UUID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    context TEXT  -- JSON con libros en contexto
);

-- Mensajes de la conversación
CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    session_id TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    role TEXT NOT NULL,  -- 'user' o 'assistant'
    content TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE INDEX idx_messages_session_id ON messages(session_id);
```

### Archivo: config.json

```json
{
  "version": "1.0.0",
  "calibre_library_path": "/Users/doniben/Calibre Library",
  "backend": {
    "host": "127.0.0.1",
    "port": 8765
  },
  "indexing": {
    "last_indexed": "2025-11-19T18:00:00",
    "total_books": 80379,
    "total_chapters": 456789,
    "total_chunks": 856432,
    "embedding_model": "all-MiniLM-L6-v2",
    "chunk_size": 500,
    "chunk_overlap": 50
  },
  "search": {
    "results_per_page": 20,
    "min_similarity": 0.5,
    "context_window": 3
  },
  "kiro": {
    "command": "kiro-cli",
    "timeout": 60,
    "max_context_tokens": 4000
  }
}
```

## API del Backend

### Endpoints de Búsqueda

```python
POST /search
Request:
{
    "query": "feminismo interseccional",
    "limit": 20,
    "search_in": ["summaries", "chapters", "full_text"]
}

Response:
{
    "results": [
        {
            "book_id": 123,
            "calibre_id": 456,
            "title": "Feminismo para el 99%",
            "author": "Nancy Fraser",
            "similarity": 0.89,
            "relevant_chapters": [
                {
                    "chapter_id": 789,
                    "title": "Interseccionalidad y clase",
                    "similarity": 0.92,
                    "snippet": "...texto relevante..."
                }
            ]
        }
    ],
    "total": 15,
    "query_time_ms": 234
}
```

```python
GET /book/{book_id}
Response:
{
    "id": 123,
    "calibre_id": 456,
    "title": "...",
    "author": "...",
    "summary": "...",
    "tags": ["Feminismo", "Política"],
    "pubdate": "2019-01-01",
    "chapters": [
        {"id": 789, "title": "Introducción", "word_count": 2500},
        ...
    ]
}
```

```python
GET /chapter/{chapter_id}
Response:
{
    "id": 789,
    "book_id": 123,
    "title": "Interseccionalidad y clase",
    "text": "...contenido completo del capítulo...",
    "word_count": 3500
}
```

### Endpoints de Conversación

```python
POST /session/new
Response:
{
    "session_id": "uuid-here"
}
```

```python
POST /ask/{session_id}
Request:
{
    "question": "¿Cuál libro es más académico?",
    "context": {
        "books": [123, 456, 789],
        "search_query": "feminismo interseccional"
    }
}

Response:
{
    "response": "Basándome en los libros encontrados...",
    "timestamp": "2025-11-19T18:30:00"
}
```

```python
GET /session/{session_id}/history
Response:
{
    "session_id": "uuid-here",
    "messages": [
        {"role": "user", "content": "...", "timestamp": "..."},
        {"role": "assistant", "content": "...", "timestamp": "..."}
    ]
}
```

```python
DELETE /session/{session_id}
Response:
{
    "status": "closed"
}
```

### Endpoints de Sistema

```python
GET /health
Response:
{
    "status": "healthy",
    "version": "1.0.0",
    "indexed_books": 80379,
    "kiro_available": true
}
```

```python
POST /index/start
Request:
{
    "full_reindex": false,  // true para reindexar todo
    "include_full_text": true
}

Response:
{
    "task_id": "uuid-here",
    "status": "started"
}
```

```python
GET /index/status/{task_id}
Response:
{
    "task_id": "uuid-here",
    "status": "running",  // running, completed, failed
    "progress": 0.45,
    "books_processed": 36000,
    "total_books": 80379,
    "estimated_time_remaining": "6h 30m"
}
```

## Proceso de Indexación

### Pipeline de Procesamiento

```
1. Leer metadata.db de Calibre
   ↓
2. Para cada libro:
   a. Extraer metadata (título, autor, resumen, tags)
   b. Localizar archivo EPUB
   c. Extraer TOC (tabla de contenidos)
   d. Extraer texto de cada capítulo
   e. Dividir en chunks de ~500 palabras
   ↓
3. Generar embeddings:
   a. Cargar modelo Sentence Transformers
   b. Para cada chunk: text → embedding (vector 384D)
   c. Guardar en memoria
   ↓
4. Crear índice FAISS:
   a. Agregar todos los vectores
   b. Optimizar índice
   c. Guardar a disco
   ↓
5. Guardar metadata en chunks.db:
   a. Insertar books
   b. Insertar chapters
   c. Insertar chunks con embedding_id
   ↓
6. Actualizar config.json con estadísticas
```

### Optimizaciones

- **Procesamiento por lotes**: 100 libros a la vez
- **Reanudable**: Guarda progreso cada 1000 libros
- **Paralelización**: Usa múltiples cores para extracción
- **Cache**: Evita reprocesar libros ya indexados
- **Incremental**: Solo procesa libros nuevos/modificados

## Seguridad y Privacidad

- ✅ Todo local, sin envío de datos a internet
- ✅ Backend solo escucha en localhost (127.0.0.1)
- ✅ No modifica metadata.db de Calibre
- ✅ Conversaciones guardadas localmente
- ✅ Compatible con suscripción Q Developer Pro (sin costos adicionales)

## Escalabilidad

### Límites Actuales
- **Libros**: Probado con 80,000
- **Chunks**: ~1M vectores en FAISS
- **RAM**: ~2-3 GB con índice cargado
- **Disco**: ~10-15 GB (embeddings + chunks)

### Optimizaciones Futuras
- Índice FAISS en disco (IVF) para >1M vectores
- Compresión de embeddings (PQ)
- Lazy loading de chunks
- Distributed search para bibliotecas masivas

## Portabilidad

### Migración entre Computadoras

**Archivos a copiar:**
```
Calibre Library/
├── metadata.db (Calibre)
├── [todos los libros]
└── .biblioteca_inteligente/
    ├── embeddings.faiss      (~5 GB)
    ├── chunks.db             (~3 GB)
    ├── conversations.db      (~100 MB)
    └── config.json           (~1 KB)
```

**Proceso:**
1. Copiar carpeta completa a nueva computadora
2. Instalar plugin en Calibre
3. Plugin detecta instalación existente
4. Actualiza rutas en config.json
5. Listo para usar

**No requiere:**
- Regenerar embeddings
- Reindexar libros
- Reconfigurar nada

## Tecnologías Utilizadas

### Backend
- **Python 3.9+**
- **FastAPI**: Framework web async
- **Uvicorn**: ASGI server
- **Sentence Transformers**: Generación de embeddings
- **FAISS**: Búsqueda vectorial eficiente
- **SQLite**: Base de datos portable
- **ebooklib**: Lectura de EPUBs
- **BeautifulSoup4**: Parsing HTML/XML

### Plugin
- **Python 3.9+** (mismo que Calibre)
- **PyQt5**: UI framework (API de Calibre)
- **requests**: Cliente HTTP
- **Calibre API**: Acceso a metadata y libros

### Modelos
- **all-MiniLM-L6-v2**: Embeddings (384 dimensiones)
  - Tamaño: 80 MB
  - Velocidad: ~1000 textos/segundo
  - Calidad: Excelente para búsqueda semántica

## Próximos Pasos

Ver [PLAN.md](../PLAN.md) para roadmap detallado.
