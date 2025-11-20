"""
Tests for Chunks Database
"""
import pytest
from pathlib import Path
import sys
import tempfile

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from chunks_db import ChunksDB, BookRecord, ChapterRecord, ChunkRecord


@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db = ChunksDB(Path(tmpdir) / "test.db")
        yield db


def test_db_init(temp_db):
    """Test database initialization"""
    assert temp_db.db_path.exists()
    stats = temp_db.get_stats()
    assert stats['total_books'] == 0
    assert stats['total_chapters'] == 0
    assert stats['total_chunks'] == 0
    
    print(f"✓ Database initialized")


def test_add_book(temp_db):
    """Test adding a book"""
    book = BookRecord(
        id=None,
        calibre_id=1,
        title="Test Book",
        author="Test Author",
        path="test/path",
        summary="A test summary",
        tags="fiction, test",
        pubdate="2025-01-01",
        indexed_at=None
    )
    
    book_id = temp_db.add_book(book)
    assert book_id > 0
    
    # Retrieve book
    retrieved = temp_db.get_book(book_id)
    assert retrieved.title == "Test Book"
    assert retrieved.author == "Test Author"
    
    print(f"✓ Book added with ID: {book_id}")


def test_get_book_by_calibre_id(temp_db):
    """Test getting book by Calibre ID"""
    book = BookRecord(
        id=None, calibre_id=42, title="Book 42", author="Author",
        path="path", summary=None, tags=None, pubdate=None, indexed_at=None
    )
    
    temp_db.add_book(book)
    
    retrieved = temp_db.get_book_by_calibre_id(42)
    assert retrieved is not None
    assert retrieved.calibre_id == 42
    assert retrieved.title == "Book 42"
    
    print(f"✓ Retrieved book by Calibre ID")


def test_book_exists(temp_db):
    """Test checking if book exists"""
    assert not temp_db.book_exists(1)
    
    book = BookRecord(
        id=None, calibre_id=1, title="Book", author="Author",
        path="path", summary=None, tags=None, pubdate=None, indexed_at=None
    )
    temp_db.add_book(book)
    
    assert temp_db.book_exists(1)
    assert not temp_db.book_exists(2)
    
    print(f"✓ Book existence check working")


def test_add_chapter(temp_db):
    """Test adding a chapter"""
    # Add book first
    book = BookRecord(
        id=None, calibre_id=1, title="Book", author="Author",
        path="path", summary=None, tags=None, pubdate=None, indexed_at=None
    )
    book_id = temp_db.add_book(book)
    
    # Add chapter
    chapter = ChapterRecord(
        id=None,
        book_id=book_id,
        chapter_num=1,
        title="Chapter 1",
        file_path="ch1.html",
        word_count=1500
    )
    
    chapter_id = temp_db.add_chapter(chapter)
    assert chapter_id > 0
    
    # Retrieve chapter
    retrieved = temp_db.get_chapter(chapter_id)
    assert retrieved.title == "Chapter 1"
    assert retrieved.word_count == 1500
    
    print(f"✓ Chapter added with ID: {chapter_id}")


def test_get_chapters(temp_db):
    """Test getting all chapters for a book"""
    book = BookRecord(
        id=None, calibre_id=1, title="Book", author="Author",
        path="path", summary=None, tags=None, pubdate=None, indexed_at=None
    )
    book_id = temp_db.add_book(book)
    
    # Add multiple chapters
    for i in range(1, 4):
        chapter = ChapterRecord(
            id=None, book_id=book_id, chapter_num=i,
            title=f"Chapter {i}", file_path=f"ch{i}.html", word_count=1000
        )
        temp_db.add_chapter(chapter)
    
    chapters = temp_db.get_chapters(book_id)
    assert len(chapters) == 3
    assert chapters[0].chapter_num == 1
    assert chapters[2].chapter_num == 3
    
    print(f"✓ Retrieved {len(chapters)} chapters")


def test_add_chunk(temp_db):
    """Test adding a chunk"""
    # Setup book and chapter
    book = BookRecord(
        id=None, calibre_id=1, title="Book", author="Author",
        path="path", summary=None, tags=None, pubdate=None, indexed_at=None
    )
    book_id = temp_db.add_book(book)
    
    chapter = ChapterRecord(
        id=None, book_id=book_id, chapter_num=1,
        title="Chapter 1", file_path="ch1.html", word_count=1000
    )
    chapter_id = temp_db.add_chapter(chapter)
    
    # Add chunk
    chunk = ChunkRecord(
        id=None,
        chapter_id=chapter_id,
        chunk_num=1,
        text="This is a test chunk of text.",
        embedding_id=0,
        start_pos=0,
        end_pos=30
    )
    
    chunk_id = temp_db.add_chunk(chunk)
    assert chunk_id > 0
    
    # Retrieve by embedding ID
    retrieved = temp_db.get_chunk_by_embedding_id(0)
    assert retrieved.text == "This is a test chunk of text."
    
    print(f"✓ Chunk added with ID: {chunk_id}")


def test_add_chunks_batch(temp_db):
    """Test batch adding chunks"""
    # Setup
    book = BookRecord(
        id=None, calibre_id=1, title="Book", author="Author",
        path="path", summary=None, tags=None, pubdate=None, indexed_at=None
    )
    book_id = temp_db.add_book(book)
    
    chapter = ChapterRecord(
        id=None, book_id=book_id, chapter_num=1,
        title="Chapter 1", file_path="ch1.html", word_count=1000
    )
    chapter_id = temp_db.add_chapter(chapter)
    
    # Create multiple chunks
    chunks = []
    for i in range(10):
        chunk = ChunkRecord(
            id=None, chapter_id=chapter_id, chunk_num=i+1,
            text=f"Chunk {i+1} text", embedding_id=i,
            start_pos=i*100, end_pos=(i+1)*100
        )
        chunks.append(chunk)
    
    temp_db.add_chunks_batch(chunks)
    
    # Verify
    retrieved_chunks = temp_db.get_chunks(chapter_id)
    assert len(retrieved_chunks) == 10
    
    print(f"✓ Batch added {len(chunks)} chunks")


def test_get_chunks_by_embedding_ids(temp_db):
    """Test getting multiple chunks by embedding IDs"""
    # Setup
    book = BookRecord(
        id=None, calibre_id=1, title="Book", author="Author",
        path="path", summary=None, tags=None, pubdate=None, indexed_at=None
    )
    book_id = temp_db.add_book(book)
    
    chapter = ChapterRecord(
        id=None, book_id=book_id, chapter_num=1,
        title="Chapter 1", file_path="ch1.html", word_count=1000
    )
    chapter_id = temp_db.add_chapter(chapter)
    
    # Add chunks
    for i in range(5):
        chunk = ChunkRecord(
            id=None, chapter_id=chapter_id, chunk_num=i+1,
            text=f"Chunk {i+1}", embedding_id=i,
            start_pos=0, end_pos=10
        )
        temp_db.add_chunk(chunk)
    
    # Get multiple
    chunks = temp_db.get_chunks_by_embedding_ids([0, 2, 4])
    assert len(chunks) == 3
    assert chunks[0].embedding_id in [0, 2, 4]
    
    print(f"✓ Retrieved {len(chunks)} chunks by embedding IDs")


def test_get_chunk_with_context(temp_db):
    """Test getting chunk with full context"""
    # Setup complete hierarchy
    book = BookRecord(
        id=None, calibre_id=1, title="Test Book", author="Test Author",
        path="path", summary="Summary", tags="test", pubdate="2025-01-01", indexed_at=None
    )
    book_id = temp_db.add_book(book)
    
    chapter = ChapterRecord(
        id=None, book_id=book_id, chapter_num=1,
        title="Introduction", file_path="intro.html", word_count=500
    )
    chapter_id = temp_db.add_chapter(chapter)
    
    chunk = ChunkRecord(
        id=None, chapter_id=chapter_id, chunk_num=1,
        text="First chunk", embedding_id=100,
        start_pos=0, end_pos=11
    )
    temp_db.add_chunk(chunk)
    
    # Get with context
    context = temp_db.get_chunk_with_context(100)
    
    assert context is not None
    assert context['book_title'] == "Test Book"
    assert context['author'] == "Test Author"
    assert context['chapter_title'] == "Introduction"
    assert context['text'] == "First chunk"
    
    print(f"✓ Chunk with context:")
    print(f"  Book: {context['book_title']}")
    print(f"  Chapter: {context['chapter_title']}")
    print(f"  Text: {context['text']}")


def test_get_stats(temp_db):
    """Test getting database statistics"""
    # Add some data
    book = BookRecord(
        id=None, calibre_id=1, title="Book", author="Author",
        path="path", summary=None, tags=None, pubdate=None, indexed_at=None
    )
    book_id = temp_db.add_book(book)
    
    chapter = ChapterRecord(
        id=None, book_id=book_id, chapter_num=1,
        title="Chapter 1", file_path="ch1.html", word_count=1000
    )
    chapter_id = temp_db.add_chapter(chapter)
    
    chunk = ChunkRecord(
        id=None, chapter_id=chapter_id, chunk_num=1,
        text="Chunk", embedding_id=0, start_pos=0, end_pos=5
    )
    temp_db.add_chunk(chunk)
    
    stats = temp_db.get_stats()
    
    assert stats['total_books'] == 1
    assert stats['total_chapters'] == 1
    assert stats['total_chunks'] == 1
    assert stats['total_words'] == 1000
    
    print(f"✓ Stats: {stats}")


def test_clear_all(temp_db):
    """Test clearing database"""
    # Add data
    book = BookRecord(
        id=None, calibre_id=1, title="Book", author="Author",
        path="path", summary=None, tags=None, pubdate=None, indexed_at=None
    )
    temp_db.add_book(book)
    
    # Clear
    temp_db.clear_all()
    
    stats = temp_db.get_stats()
    assert stats['total_books'] == 0
    assert stats['total_chapters'] == 0
    assert stats['total_chunks'] == 0
    
    print(f"✓ Database cleared")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
