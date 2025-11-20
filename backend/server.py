"""
FastAPI Server for Calibre Intelligent Library
Main API endpoints for search and book management
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from pathlib import Path
import uvicorn
import time

from calibre_db import CalibreDB
from epub_extractor import EPUBExtractor
from embeddings import EmbeddingsGenerator
from vector_search import VectorIndex, SearchEngine
from chunks_db import ChunksDB
from kiro_client import KiroSessionManager, format_books_context
from conversations_db import ConversationsDB

# Configuration
CALIBRE_LIBRARY = Path.home() / "Calibre Library"
DATA_DIR = CALIBRE_LIBRARY / ".biblioteca_inteligente"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Initialize components
app = FastAPI(
    title="Calibre Intelligent Library API",
    description="Semantic search and AI assistant for Calibre libraries",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances (initialized on startup)
calibre_db = None
chunks_db = None
embeddings_gen = None
vector_index = None
search_engine = None
session_manager = None
conversations_db = None


# Pydantic models
class SearchRequest(BaseModel):
    query: str
    limit: int = 20
    min_similarity: float = 0.0


class SearchResult(BaseModel):
    book_id: int
    calibre_id: int
    title: str
    author: str
    similarity: float
    chapter_title: Optional[str] = None
    chapter_num: Optional[int] = None
    snippet: Optional[str] = None


class BookDetail(BaseModel):
    id: int
    calibre_id: int
    title: str
    author: str
    summary: Optional[str]
    tags: Optional[str]
    pubdate: Optional[str]
    has_epub: bool


class ChapterInfo(BaseModel):
    id: int
    chapter_num: int
    title: str
    word_count: int


class HealthResponse(BaseModel):
    status: str
    version: str
    calibre_library: str
    indexed_books: int
    total_chunks: int


class SessionCreateResponse(BaseModel):
    session_id: str
    created_at: float


class AskRequest(BaseModel):
    question: str
    context_books: Optional[List[int]] = None  # List of book IDs for context


class AskResponse(BaseModel):
    session_id: str
    question: str
    response: str
    timestamp: float


class SessionHistoryResponse(BaseModel):
    session_id: str
    message_count: int
    messages: List[Dict]


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global calibre_db, chunks_db, embeddings_gen, vector_index, search_engine, session_manager, conversations_db
    
    print("🚀 Starting Calibre Intelligent Library API...")
    
    # Initialize Calibre DB
    calibre_db = CalibreDB(str(CALIBRE_LIBRARY))
    print(f"✓ Connected to Calibre library: {CALIBRE_LIBRARY}")
    
    # Initialize chunks DB
    chunks_db = ChunksDB(DATA_DIR / "chunks.db")
    print(f"✓ Chunks database ready")
    
    # Initialize conversations DB
    conversations_db = ConversationsDB(DATA_DIR / "conversations.db")
    print(f"✓ Conversations database ready")
    
    # Initialize embeddings generator
    embeddings_gen = EmbeddingsGenerator()
    print(f"✓ Embeddings generator loaded")
    
    # Initialize vector index
    vector_index = VectorIndex(dimension=384)
    
    # Try to load existing index
    index_path = DATA_DIR / "embeddings"
    if (index_path.with_suffix('.faiss')).exists():
        try:
            vector_index.load(index_path)
            print(f"✓ Loaded existing vector index")
        except Exception as e:
            print(f"⚠ Could not load index: {e}")
    else:
        print(f"ℹ No existing index found (will be created during indexing)")
    
    # Initialize search engine
    search_engine = SearchEngine(embeddings_gen, vector_index)
    print(f"✓ Search engine ready")
    
    # Initialize session manager with conversations DB
    session_manager = KiroSessionManager(conversations_db=conversations_db)
    print(f"✓ Session manager ready")
    
    print("✅ API ready!")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Calibre Intelligent Library API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check endpoint"""
    stats = chunks_db.get_stats()
    calibre_stats = calibre_db.get_stats()
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        calibre_library=str(CALIBRE_LIBRARY),
        indexed_books=stats['total_books'],
        total_chunks=stats['total_chunks']
    )


@app.post("/search", response_model=List[SearchResult], tags=["Search"])
async def search(request: SearchRequest):
    """
    Semantic search for books
    
    - **query**: Search query text
    - **limit**: Maximum number of results (default: 20)
    - **min_similarity**: Minimum similarity threshold 0-1 (default: 0.0)
    """
    if vector_index.index.ntotal == 0:
        raise HTTPException(
            status_code=503,
            detail="Index not ready. Please run indexing first."
        )
    
    # Search
    results = search_engine.search(
        request.query,
        k=request.limit,
        min_similarity=request.min_similarity
    )
    
    # Enrich results with context
    search_results = []
    for result in results:
        # Get chunk with context
        context = chunks_db.get_chunk_with_context(result['index'])
        if context:
            search_results.append(SearchResult(
                book_id=context['book_id'],
                calibre_id=context['calibre_id'],
                title=context['book_title'],
                author=context['author'],
                similarity=result['similarity'],
                chapter_title=context['chapter_title'],
                chapter_num=context['chapter_num'],
                snippet=context['text'][:200] + "..." if len(context['text']) > 200 else context['text']
            ))
    
    return search_results


@app.get("/book/{calibre_id}", response_model=BookDetail, tags=["Books"])
async def get_book(calibre_id: int):
    """Get book details by Calibre ID"""
    book = calibre_db.get_book(calibre_id)
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return BookDetail(
        id=calibre_id,
        calibre_id=calibre_id,
        title=book.title,
        author=book.author,
        summary=book.summary,
        tags=book.tags,
        pubdate=book.pubdate,
        has_epub=book.has_epub
    )


@app.get("/book/{calibre_id}/chapters", response_model=List[ChapterInfo], tags=["Books"])
async def get_book_chapters(calibre_id: int):
    """Get table of contents for a book"""
    # Check if book is indexed
    book_record = chunks_db.get_book_by_calibre_id(calibre_id)
    
    if not book_record:
        raise HTTPException(
            status_code=404,
            detail="Book not indexed. Please index this book first."
        )
    
    chapters = chunks_db.get_chapters(book_record.id)
    
    return [
        ChapterInfo(
            id=ch.id,
            chapter_num=ch.chapter_num,
            title=ch.title,
            word_count=ch.word_count
        )
        for ch in chapters
    ]


@app.get("/chapter/{chapter_id}/text", tags=["Books"])
async def get_chapter_text(chapter_id: int):
    """Get full text of a chapter"""
    chapter = chunks_db.get_chapter(chapter_id)
    
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    # Get all chunks for this chapter
    chunks = chunks_db.get_chunks(chapter_id)
    
    # Concatenate chunk texts
    full_text = "\n\n".join(chunk.text for chunk in chunks)
    
    return {
        "chapter_id": chapter_id,
        "title": chapter.title,
        "chapter_num": chapter.chapter_num,
        "word_count": chapter.word_count,
        "text": full_text
    }


@app.get("/stats", tags=["System"])
async def get_stats():
    """Get system statistics"""
    chunks_stats = chunks_db.get_stats()
    calibre_stats = calibre_db.get_stats()
    vector_stats = vector_index.get_stats()
    
    return {
        "calibre": calibre_stats,
        "indexed": chunks_stats,
        "vector_index": vector_stats
    }


@app.get("/books/indexed", tags=["Books"])
async def get_indexed_books(limit: int = 50, offset: int = 0):
    """Get list of indexed books"""
    # This would need a query in chunks_db to get paginated books
    # For now, return basic info
    stats = chunks_db.get_stats()
    
    return {
        "total": stats['total_books'],
        "limit": limit,
        "offset": offset,
        "message": "Full pagination coming soon"
    }


# Conversation endpoints
@app.post("/session/new", response_model=SessionCreateResponse, tags=["Conversation"])
async def create_session():
    """
    Create a new conversation session with Kiro
    
    Returns session_id to use for subsequent questions
    """
    session = session_manager.create_session()
    
    return SessionCreateResponse(
        session_id=session.session_id,
        created_at=session.created_at
    )


@app.post("/session/{session_id}/ask", response_model=AskResponse, tags=["Conversation"])
async def ask_question(session_id: str, request: AskRequest):
    """
    Ask a question in a conversation session
    
    - **session_id**: Session ID from /session/new
    - **question**: Question to ask Kiro
    - **context_books**: Optional list of book IDs to include as context
    """
    session = session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Build context from books if provided
    context = None
    if request.context_books:
        books_data = []
        for book_id in request.context_books:
            book = calibre_db.get_book(book_id)
            if book:
                books_data.append({
                    'title': book.title,
                    'author': book.author,
                    'summary': book.summary,
                    'tags': book.tags,
                    'pubdate': book.pubdate
                })
        
        if books_data:
            context = format_books_context(books_data)
            session.set_context(context)
    
    # Ask Kiro
    try:
        response = session.ask(request.question)
        
        return AskResponse(
            session_id=session_id,
            question=request.question,
            response=response,
            timestamp=time.time()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with Kiro: {str(e)}")


@app.get("/session/{session_id}/history", response_model=SessionHistoryResponse, tags=["Conversation"])
async def get_session_history(session_id: str):
    """Get conversation history for a session"""
    session = session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    history = session.get_history()
    
    return SessionHistoryResponse(
        session_id=session_id,
        message_count=len(history),
        messages=history
    )


@app.delete("/session/{session_id}", tags=["Conversation"])
async def delete_session(session_id: str):
    """Delete a conversation session"""
    if session_manager.delete_session(session_id):
        return {"status": "deleted", "session_id": session_id}
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@app.get("/sessions", tags=["Conversation"])
async def list_sessions():
    """List all active sessions"""
    sessions = session_manager.get_all_sessions()
    return {
        "total": len(sessions),
        "sessions": sessions
    }


@app.get("/conversations", tags=["Conversation"])
async def list_conversations(limit: int = 50, offset: int = 0):
    """List all persisted conversations"""
    conversations = conversations_db.get_all_conversations(limit, offset)
    
    return {
        "total": len(conversations),
        "limit": limit,
        "offset": offset,
        "conversations": [
            {
                "session_id": c.session_id,
                "created_at": c.created_at,
                "last_activity": c.last_activity,
                "has_context": c.context is not None
            }
            for c in conversations
        ]
    }


@app.get("/conversation/{session_id}/export", tags=["Conversation"])
async def export_conversation(session_id: str):
    """Export a conversation with all messages"""
    export = conversations_db.export_conversation(session_id)
    
    if not export:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return export


@app.delete("/conversation/{session_id}", tags=["Conversation"])
async def delete_persisted_conversation(session_id: str):
    """Delete a persisted conversation permanently"""
    if conversations_db.delete_conversation(session_id):
        # Also delete from active sessions if present
        session_manager.delete_session(session_id)
        return {"status": "deleted", "session_id": session_id}
    else:
        raise HTTPException(status_code=404, detail="Conversation not found")


@app.delete("/conversation/{session_id}/messages", tags=["Conversation"])
async def clear_conversation_messages(session_id: str):
    """Clear all messages from a conversation (keep session)"""
    count = conversations_db.clear_conversation_messages(session_id)
    
    # Also clear from active session if present
    session = session_manager.get_session(session_id)
    if session:
        session.clear_history()
    
    return {
        "status": "cleared",
        "session_id": session_id,
        "messages_deleted": count
    }


@app.get("/conversations/search", tags=["Conversation"])
async def search_conversations(query: str, limit: int = 20):
    """Search conversations by content"""
    results = conversations_db.search_conversations(query, limit)
    
    return {
        "query": query,
        "total": len(results),
        "results": results
    }


@app.get("/conversations/stats", tags=["Conversation"])
async def get_conversations_stats():
    """Get conversation statistics"""
    return conversations_db.get_stats()


if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="127.0.0.1",
        port=8765,
        reload=True,
        log_level="info"
    )
