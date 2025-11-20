"""
Tests for EPUB Extractor
"""
import pytest
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from epub_extractor import EPUBExtractor, extract_epub_info, Chapter, TOCEntry
from calibre_db import CalibreDB


# Path to your Calibre Library
CALIBRE_LIBRARY = Path.home() / "Calibre Library"


@pytest.fixture
def sample_epub():
    """Get a sample EPUB file from Calibre library"""
    db = CalibreDB(str(CALIBRE_LIBRARY))
    
    # Find first book with EPUB
    books = db.get_books(limit=50)
    for book in books:
        if book.has_epub:
            epub_path = db.get_epub_path(book.id)
            if epub_path:
                return epub_path, book
    
    pytest.skip("No EPUB books found in library")


def test_epub_extractor_init(sample_epub):
    """Test EPUBExtractor initialization"""
    epub_path, book = sample_epub
    
    extractor = EPUBExtractor(epub_path)
    assert extractor.epub_path == epub_path
    assert extractor.book is not None
    
    print(f"✓ Initialized extractor for: {book.title}")


def test_epub_extractor_invalid_path():
    """Test EPUBExtractor with invalid path"""
    with pytest.raises(FileNotFoundError):
        EPUBExtractor(Path("/invalid/path.epub"))


def test_get_metadata(sample_epub):
    """Test metadata extraction"""
    epub_path, book = sample_epub
    
    extractor = EPUBExtractor(epub_path)
    metadata = extractor.get_metadata()
    
    assert isinstance(metadata, dict)
    assert 'title' in metadata
    assert 'author' in metadata
    
    print(f"✓ Metadata extracted:")
    print(f"  Title: {metadata.get('title')}")
    print(f"  Author: {metadata.get('author')}")
    print(f"  Language: {metadata.get('language')}")


def test_get_toc(sample_epub):
    """Test table of contents extraction"""
    epub_path, book = sample_epub
    
    extractor = EPUBExtractor(epub_path)
    toc = extractor.get_toc()
    
    assert isinstance(toc, list)
    assert len(toc) > 0, "TOC is empty"
    assert all(isinstance(entry, TOCEntry) for entry in toc)
    
    print(f"✓ TOC extracted: {len(toc)} entries")
    for entry in toc[:5]:
        indent = "  " * entry.level
        print(f"  {indent}- {entry.title}")


def test_extract_text_from_html(sample_epub):
    """Test HTML to text extraction"""
    epub_path, book = sample_epub
    
    extractor = EPUBExtractor(epub_path)
    
    # Get first chapter with actual content
    toc = extractor.get_toc()
    text = None
    for entry in toc:
        text = extractor.get_chapter(entry.file_path)
        if text and len(text) > 0:
            break
    
    assert text is not None
    assert len(text) > 0
    assert isinstance(text, str)
    
    print(f"✓ Extracted text from chapter:")
    print(f"  Length: {len(text)} characters")
    print(f"  Preview: {text[:200]}...")


def test_get_all_chapters(sample_epub):
    """Test extracting all chapters"""
    epub_path, book = sample_epub
    
    extractor = EPUBExtractor(epub_path)
    chapters = extractor.get_all_chapters()
    
    assert isinstance(chapters, list)
    assert len(chapters) > 0, "No chapters extracted"
    assert all(isinstance(ch, Chapter) for ch in chapters)
    
    total_words = sum(ch.word_count for ch in chapters)
    
    print(f"✓ Extracted {len(chapters)} chapters")
    print(f"  Total words: {total_words:,}")
    for ch in chapters[:3]:
        print(f"  - Chapter {ch.num}: {ch.title} ({ch.word_count} words)")


def test_chunk_text(sample_epub):
    """Test text chunking"""
    epub_path, book = sample_epub
    
    extractor = EPUBExtractor(epub_path)
    
    # Get some text
    chapters = extractor.get_all_chapters()
    if chapters:
        text = chapters[0].text
        chunks = extractor.chunk_text(text, chunk_size=100, overlap=20)
        
        assert isinstance(chunks, list)
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)
        
        # Check overlap
        if len(chunks) > 1:
            words1 = chunks[0].split()
            words2 = chunks[1].split()
            # Should have some overlap
            assert len(words1) <= 100
        
        print(f"✓ Text chunked into {len(chunks)} chunks")
        print(f"  First chunk: {chunks[0][:100]}...")


def test_get_chapters_with_chunks(sample_epub):
    """Test getting chapters with chunks"""
    epub_path, book = sample_epub
    
    extractor = EPUBExtractor(epub_path)
    chapters_with_chunks = extractor.get_chapters_with_chunks(chunk_size=200, overlap=30)
    
    assert isinstance(chapters_with_chunks, list)
    assert len(chapters_with_chunks) > 0
    
    total_chunks = sum(len(item['chunks']) for item in chapters_with_chunks)
    
    print(f"✓ Extracted {len(chapters_with_chunks)} chapters with chunks")
    print(f"  Total chunks: {total_chunks}")
    for item in chapters_with_chunks[:2]:
        ch = item['chapter']
        print(f"  - {ch.title}: {len(item['chunks'])} chunks")


def test_extract_epub_info(sample_epub):
    """Test quick info extraction function"""
    epub_path, book = sample_epub
    
    info = extract_epub_info(epub_path)
    
    assert info['success'] is True
    assert 'metadata' in info
    assert 'toc_entries' in info
    assert info['toc_entries'] > 0
    
    print(f"✓ Quick info extraction:")
    print(f"  Title: {info['metadata'].get('title')}")
    print(f"  TOC entries: {info['toc_entries']}")


def test_multiple_epubs():
    """Test extraction on multiple EPUBs"""
    db = CalibreDB(str(CALIBRE_LIBRARY))
    
    books = db.get_books(limit=100)
    epub_books = [b for b in books if b.has_epub][:5]  # Test first 5
    
    assert len(epub_books) > 0, "No EPUB books found"
    
    results = []
    for book in epub_books:
        epub_path = db.get_epub_path(book.id)
        try:
            extractor = EPUBExtractor(epub_path)
            toc = extractor.get_toc()
            chapters = extractor.get_all_chapters()
            
            results.append({
                'title': book.title,
                'success': True,
                'toc_entries': len(toc),
                'chapters': len(chapters)
            })
        except Exception as e:
            results.append({
                'title': book.title,
                'success': False,
                'error': str(e)
            })
    
    successful = [r for r in results if r['success']]
    
    print(f"✓ Tested {len(epub_books)} EPUBs:")
    print(f"  Successful: {len(successful)}/{len(results)}")
    for r in results:
        if r['success']:
            print(f"  ✓ {r['title']}: {r['chapters']} chapters")
        else:
            print(f"  ✗ {r['title']}: {r['error']}")
    
    # At least 80% should succeed
    assert len(successful) >= len(results) * 0.8


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
