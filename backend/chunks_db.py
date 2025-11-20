"""
Chunks Database Module
SQLite database for storing book chunks and metadata
"""
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass
from datetime import datetime


@dataclass
class BookRecord:
    """Book record in chunks database"""
    id: Optional[int]
    calibre_id: int
    title: str
    author: str
    path: str
    summary: Optional[str]
    tags: Optional[str]
    pubdate: Optional[str]
    indexed_at: Optional[str]


@dataclass
class ChapterRecord:
    """Chapter record"""
    id: Optional[int]
    book_id: int
    chapter_num: int
    title: str
    file_path: str
    word_count: int


@dataclass
class ChunkRecord:
    """Chunk record"""
    id: Optional[int]
    chapter_id: int
    chunk_num: int
    text: str
    embedding_id: int
    start_pos: int
    end_pos: int


class ChunksDB:
    """Database for storing book chunks and embeddings metadata"""
    
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _connect(self) -> sqlite3.Connection:
        """Create database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        """Initialize database schema"""
        with self._connect() as conn:
            # Books table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    calibre_id INTEGER NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    author TEXT,
                    path TEXT NOT NULL,
                    summary TEXT,
                    tags TEXT,
                    pubdate TEXT,
                    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Chapters table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chapters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id INTEGER NOT NULL,
                    chapter_num INTEGER NOT NULL,
                    title TEXT,
                    file_path TEXT,
                    word_count INTEGER,
                    FOREIGN KEY (book_id) REFERENCES books(id),
                    UNIQUE(book_id, chapter_num)
                )
            """)
            
            # Chunks table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chapter_id INTEGER NOT NULL,
                    chunk_num INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    embedding_id INTEGER NOT NULL,
                    start_pos INTEGER,
                    end_pos INTEGER,
                    FOREIGN KEY (chapter_id) REFERENCES chapters(id),
                    UNIQUE(chapter_id, chunk_num)
                )
            """)
            
            # Create indices
            conn.execute("CREATE INDEX IF NOT EXISTS idx_books_calibre_id ON books(calibre_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chapters_book_id ON chapters(book_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_chapter_id ON chunks(chapter_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_embedding_id ON chunks(embedding_id)")
            
            conn.commit()
        
        print(f"✓ Database initialized: {self.db_path}")
    
    # Book operations
    def add_book(self, book: BookRecord) -> int:
        """Add book to database, return book_id"""
        with self._connect() as conn:
            cursor = conn.execute("""
                INSERT INTO books (calibre_id, title, author, path, summary, tags, pubdate)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (book.calibre_id, book.title, book.author, book.path, 
                  book.summary, book.tags, book.pubdate))
            conn.commit()
            return cursor.lastrowid
    
    def get_book(self, book_id: int) -> Optional[BookRecord]:
        """Get book by internal ID"""
        with self._connect() as conn:
            cursor = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,))
            row = cursor.fetchone()
            if row:
                return BookRecord(**dict(row))
            return None
    
    def get_book_by_calibre_id(self, calibre_id: int) -> Optional[BookRecord]:
        """Get book by Calibre ID"""
        with self._connect() as conn:
            cursor = conn.execute("SELECT * FROM books WHERE calibre_id = ?", (calibre_id,))
            row = cursor.fetchone()
            if row:
                return BookRecord(**dict(row))
            return None
    
    def book_exists(self, calibre_id: int) -> bool:
        """Check if book is already indexed"""
        return self.get_book_by_calibre_id(calibre_id) is not None
    
    # Chapter operations
    def add_chapter(self, chapter: ChapterRecord) -> int:
        """Add chapter to database, return chapter_id"""
        with self._connect() as conn:
            cursor = conn.execute("""
                INSERT INTO chapters (book_id, chapter_num, title, file_path, word_count)
                VALUES (?, ?, ?, ?, ?)
            """, (chapter.book_id, chapter.chapter_num, chapter.title, 
                  chapter.file_path, chapter.word_count))
            conn.commit()
            return cursor.lastrowid
    
    def get_chapters(self, book_id: int) -> List[ChapterRecord]:
        """Get all chapters for a book"""
        with self._connect() as conn:
            cursor = conn.execute("""
                SELECT * FROM chapters WHERE book_id = ? ORDER BY chapter_num
            """, (book_id,))
            return [ChapterRecord(**dict(row)) for row in cursor.fetchall()]
    
    def get_chapter(self, chapter_id: int) -> Optional[ChapterRecord]:
        """Get chapter by ID"""
        with self._connect() as conn:
            cursor = conn.execute("SELECT * FROM chapters WHERE id = ?", (chapter_id,))
            row = cursor.fetchone()
            if row:
                return ChapterRecord(**dict(row))
            return None
    
    # Chunk operations
    def add_chunk(self, chunk: ChunkRecord) -> int:
        """Add chunk to database, return chunk_id"""
        with self._connect() as conn:
            cursor = conn.execute("""
                INSERT INTO chunks (chapter_id, chunk_num, text, embedding_id, start_pos, end_pos)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (chunk.chapter_id, chunk.chunk_num, chunk.text, 
                  chunk.embedding_id, chunk.start_pos, chunk.end_pos))
            conn.commit()
            return cursor.lastrowid
    
    def add_chunks_batch(self, chunks: List[ChunkRecord]):
        """Add multiple chunks efficiently"""
        with self._connect() as conn:
            conn.executemany("""
                INSERT INTO chunks (chapter_id, chunk_num, text, embedding_id, start_pos, end_pos)
                VALUES (?, ?, ?, ?, ?, ?)
            """, [(c.chapter_id, c.chunk_num, c.text, c.embedding_id, c.start_pos, c.end_pos) 
                  for c in chunks])
            conn.commit()
    
    def get_chunks(self, chapter_id: int) -> List[ChunkRecord]:
        """Get all chunks for a chapter"""
        with self._connect() as conn:
            cursor = conn.execute("""
                SELECT * FROM chunks WHERE chapter_id = ? ORDER BY chunk_num
            """, (chapter_id,))
            return [ChunkRecord(**dict(row)) for row in cursor.fetchall()]
    
    def get_chunk_by_embedding_id(self, embedding_id: int) -> Optional[ChunkRecord]:
        """Get chunk by embedding ID"""
        with self._connect() as conn:
            cursor = conn.execute("""
                SELECT * FROM chunks WHERE embedding_id = ?
            """, (embedding_id,))
            row = cursor.fetchone()
            if row:
                return ChunkRecord(**dict(row))
            return None
    
    def get_chunks_by_embedding_ids(self, embedding_ids: List[int]) -> List[ChunkRecord]:
        """Get multiple chunks by embedding IDs"""
        if not embedding_ids:
            return []
        
        placeholders = ','.join('?' * len(embedding_ids))
        with self._connect() as conn:
            cursor = conn.execute(f"""
                SELECT * FROM chunks WHERE embedding_id IN ({placeholders})
            """, embedding_ids)
            return [ChunkRecord(**dict(row)) for row in cursor.fetchall()]
    
    # Search and retrieval
    def get_chunk_with_context(self, embedding_id: int) -> Dict:
        """Get chunk with book and chapter context"""
        with self._connect() as conn:
            cursor = conn.execute("""
                SELECT 
                    c.id as chunk_id,
                    c.text,
                    c.chunk_num,
                    ch.id as chapter_id,
                    ch.title as chapter_title,
                    ch.chapter_num,
                    b.id as book_id,
                    b.calibre_id,
                    b.title as book_title,
                    b.author
                FROM chunks c
                JOIN chapters ch ON c.chapter_id = ch.id
                JOIN books b ON ch.book_id = b.id
                WHERE c.embedding_id = ?
            """, (embedding_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    # Statistics
    def get_stats(self) -> Dict:
        """Get database statistics"""
        with self._connect() as conn:
            stats = {}
            
            cursor = conn.execute("SELECT COUNT(*) FROM books")
            stats['total_books'] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM chapters")
            stats['total_chapters'] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM chunks")
            stats['total_chunks'] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT SUM(word_count) FROM chapters")
            stats['total_words'] = cursor.fetchone()[0] or 0
            
            return stats
    
    def clear_all(self):
        """Clear all data (for testing)"""
        with self._connect() as conn:
            conn.execute("DELETE FROM chunks")
            conn.execute("DELETE FROM chapters")
            conn.execute("DELETE FROM books")
            conn.commit()
        print("✓ Database cleared")


if __name__ == "__main__":
    # Quick test
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db = ChunksDB(Path(tmpdir) / "test.db")
        
        # Add book
        book = BookRecord(
            id=None,
            calibre_id=1,
            title="Test Book",
            author="Test Author",
            path="test/path",
            summary="A test book",
            tags="test",
            pubdate="2025-01-01",
            indexed_at=None
        )
        book_id = db.add_book(book)
        print(f"✓ Added book with ID: {book_id}")
        
        # Add chapter
        chapter = ChapterRecord(
            id=None,
            book_id=book_id,
            chapter_num=1,
            title="Chapter 1",
            file_path="ch1.html",
            word_count=1000
        )
        chapter_id = db.add_chapter(chapter)
        print(f"✓ Added chapter with ID: {chapter_id}")
        
        # Add chunk
        chunk = ChunkRecord(
            id=None,
            chapter_id=chapter_id,
            chunk_num=1,
            text="This is a test chunk",
            embedding_id=0,
            start_pos=0,
            end_pos=20
        )
        chunk_id = db.add_chunk(chunk)
        print(f"✓ Added chunk with ID: {chunk_id}")
        
        # Get stats
        stats = db.get_stats()
        print(f"✓ Stats: {stats}")
        
        # Get with context
        context = db.get_chunk_with_context(0)
        print(f"✓ Chunk with context: {context['book_title']} - {context['chapter_title']}")
