"""
Tests for Calibre DB connection
"""
import pytest
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from calibre_db import CalibreDB, Book


# Path to your Calibre Library
CALIBRE_LIBRARY = Path.home() / "Calibre Library"


def test_calibre_library_exists():
    """Test that Calibre Library exists"""
    assert CALIBRE_LIBRARY.exists(), f"Calibre Library not found at {CALIBRE_LIBRARY}"
    assert (CALIBRE_LIBRARY / "metadata.db").exists(), "metadata.db not found"


def test_calibre_db_init():
    """Test CalibreDB initialization"""
    db = CalibreDB(str(CALIBRE_LIBRARY))
    assert db.library_path == CALIBRE_LIBRARY
    assert db.db_path.exists()


def test_calibre_db_invalid_path():
    """Test CalibreDB with invalid path"""
    with pytest.raises(FileNotFoundError):
        CalibreDB("/invalid/path")


def test_get_book_count():
    """Test getting total book count"""
    db = CalibreDB(str(CALIBRE_LIBRARY))
    count = db.get_book_count()
    
    assert count > 0, "No books found in library"
    assert isinstance(count, int)
    print(f"✓ Found {count:,} books in library")


def test_get_single_book():
    """Test getting a single book"""
    db = CalibreDB(str(CALIBRE_LIBRARY))
    
    # Get first book
    book = db.get_book(1)
    
    assert book is not None, "Book ID 1 not found"
    assert isinstance(book, Book)
    assert book.id == 1
    assert book.title
    assert book.author
    assert book.path
    
    print(f"✓ Book 1: '{book.title}' by {book.author}")


def test_get_multiple_books():
    """Test getting multiple books"""
    db = CalibreDB(str(CALIBRE_LIBRARY))
    
    books = db.get_books(limit=10)
    
    assert len(books) == 10, f"Expected 10 books, got {len(books)}"
    assert all(isinstance(b, Book) for b in books)
    
    print(f"✓ Retrieved {len(books)} books")
    for book in books[:3]:
        print(f"  - {book.title} by {book.author}")


def test_get_books_with_summaries():
    """Test getting books with summaries"""
    db = CalibreDB(str(CALIBRE_LIBRARY))
    
    books = db.get_books_with_summaries(limit=5)
    
    assert len(books) > 0, "No books with summaries found"
    assert all(book.summary for book in books), "Some books missing summaries"
    
    print(f"✓ Found {len(books)} books with summaries")
    for book in books[:2]:
        summary_preview = book.summary[:100] if book.summary else "N/A"
        print(f"  - {book.title}: {summary_preview}...")


def test_get_epub_path():
    """Test getting EPUB file path"""
    db = CalibreDB(str(CALIBRE_LIBRARY))
    
    # Find a book with EPUB
    books = db.get_books(limit=50)
    epub_book = next((b for b in books if b.has_epub), None)
    
    if epub_book:
        epub_path = db.get_epub_path(epub_book.id)
        assert epub_path is not None
        assert epub_path.exists()
        assert epub_path.suffix == ".epub"
        print(f"✓ Found EPUB: {epub_path.name}")
    else:
        print("⚠ No EPUB books found in first 50 books")


def test_get_stats():
    """Test getting library statistics"""
    db = CalibreDB(str(CALIBRE_LIBRARY))
    
    stats = db.get_stats()
    
    assert 'total_books' in stats
    assert 'books_with_summaries' in stats
    assert 'total_tags' in stats
    assert 'total_authors' in stats
    
    assert stats['total_books'] > 0
    
    print(f"✓ Library Statistics:")
    print(f"  Total books: {stats['total_books']:,}")
    print(f"  Books with summaries: {stats['books_with_summaries']:,}")
    print(f"  Total tags: {stats['total_tags']:,}")
    print(f"  Total authors: {stats['total_authors']:,}")


def test_book_with_tags():
    """Test that tags are retrieved correctly"""
    db = CalibreDB(str(CALIBRE_LIBRARY))
    
    books = db.get_books(limit=100)
    books_with_tags = [b for b in books if b.tags]
    
    assert len(books_with_tags) > 0, "No books with tags found"
    
    print(f"✓ Found {len(books_with_tags)} books with tags")
    for book in books_with_tags[:3]:
        print(f"  - {book.title}: {book.tags}")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
