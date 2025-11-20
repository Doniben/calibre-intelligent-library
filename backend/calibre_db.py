"""
Calibre Database Connection Module
Reads metadata from Calibre's metadata.db
"""
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class Book:
    """Book metadata from Calibre"""
    id: int
    title: str
    author: str
    path: str
    summary: Optional[str] = None
    tags: Optional[str] = None
    pubdate: Optional[str] = None
    has_epub: bool = False


class CalibreDB:
    """Interface to Calibre's metadata.db"""
    
    def __init__(self, library_path: str):
        self.library_path = Path(library_path)
        self.db_path = self.library_path / "metadata.db"
        
        if not self.db_path.exists():
            raise FileNotFoundError(f"Calibre database not found at {self.db_path}")
    
    def _connect(self) -> sqlite3.Connection:
        """Create database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_book_count(self) -> int:
        """Get total number of books"""
        with self._connect() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM books")
            return cursor.fetchone()[0]
    
    def get_book(self, book_id: int) -> Optional[Book]:
        """Get single book by ID"""
        with self._connect() as conn:
            cursor = conn.execute("""
                SELECT 
                    b.id,
                    b.title,
                    b.path,
                    b.pubdate,
                    (SELECT GROUP_CONCAT(a.name, ' & ') 
                     FROM authors a 
                     JOIN books_authors_link bal ON a.id = bal.author 
                     WHERE bal.book = b.id) as author,
                    (SELECT text FROM comments WHERE book = b.id) as summary,
                    (SELECT GROUP_CONCAT(t.name, ', ') 
                     FROM tags t 
                     JOIN books_tags_link btl ON t.id = btl.tag 
                     WHERE btl.book = b.id) as tags
                FROM books b
                WHERE b.id = ?
            """, (book_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # Check if EPUB exists
            book_path = self.library_path / row['path']
            has_epub = any(book_path.glob("*.epub"))
            
            return Book(
                id=row['id'],
                title=row['title'],
                author=row['author'] or "Unknown",
                path=row['path'],
                summary=row['summary'],
                tags=row['tags'],
                pubdate=row['pubdate'],
                has_epub=has_epub
            )
    
    def get_books(self, limit: Optional[int] = None, offset: int = 0) -> List[Book]:
        """Get multiple books with pagination"""
        query = """
            SELECT 
                b.id,
                b.title,
                b.path,
                b.pubdate,
                (SELECT GROUP_CONCAT(a.name, ' & ') 
                 FROM authors a 
                 JOIN books_authors_link bal ON a.id = bal.author 
                 WHERE bal.book = b.id) as author,
                (SELECT text FROM comments WHERE book = b.id) as summary,
                (SELECT GROUP_CONCAT(t.name, ', ') 
                 FROM tags t 
                 JOIN books_tags_link btl ON t.id = btl.tag 
                 WHERE btl.book = b.id) as tags
            FROM books b
            ORDER BY b.id
        """
        
        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"
        
        books = []
        with self._connect() as conn:
            cursor = conn.execute(query)
            for row in cursor:
                book_path = self.library_path / row['path']
                has_epub = any(book_path.glob("*.epub"))
                
                books.append(Book(
                    id=row['id'],
                    title=row['title'],
                    author=row['author'] or "Unknown",
                    path=row['path'],
                    summary=row['summary'],
                    tags=row['tags'],
                    pubdate=row['pubdate'],
                    has_epub=has_epub
                ))
        
        return books
    
    def get_books_with_summaries(self, limit: Optional[int] = None) -> List[Book]:
        """Get only books that have summaries"""
        query = """
            SELECT 
                b.id,
                b.title,
                b.path,
                b.pubdate,
                (SELECT GROUP_CONCAT(a.name, ' & ') 
                 FROM authors a 
                 JOIN books_authors_link bal ON a.id = bal.author 
                 WHERE bal.book = b.id) as author,
                c.text as summary,
                (SELECT GROUP_CONCAT(t.name, ', ') 
                 FROM tags t 
                 JOIN books_tags_link btl ON t.id = btl.tag 
                 WHERE btl.book = b.id) as tags
            FROM books b
            JOIN comments c ON b.id = c.book
            WHERE c.text IS NOT NULL AND c.text != ''
            ORDER BY b.id
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        books = []
        with self._connect() as conn:
            cursor = conn.execute(query)
            for row in cursor:
                book_path = self.library_path / row['path']
                has_epub = any(book_path.glob("*.epub"))
                
                books.append(Book(
                    id=row['id'],
                    title=row['title'],
                    author=row['author'] or "Unknown",
                    path=row['path'],
                    summary=row['summary'],
                    tags=row['tags'],
                    pubdate=row['pubdate'],
                    has_epub=has_epub
                ))
        
        return books
    
    def get_epub_path(self, book_id: int) -> Optional[Path]:
        """Get path to EPUB file for a book"""
        book = self.get_book(book_id)
        if not book or not book.has_epub:
            return None
        
        book_dir = self.library_path / book.path
        epub_files = list(book_dir.glob("*.epub"))
        
        return epub_files[0] if epub_files else None
    
    def get_stats(self) -> Dict:
        """Get library statistics"""
        with self._connect() as conn:
            stats = {}
            
            # Total books
            cursor = conn.execute("SELECT COUNT(*) FROM books")
            stats['total_books'] = cursor.fetchone()[0]
            
            # Books with summaries
            cursor = conn.execute("""
                SELECT COUNT(*) FROM comments 
                WHERE text IS NOT NULL AND text != ''
            """)
            stats['books_with_summaries'] = cursor.fetchone()[0]
            
            # Total tags
            cursor = conn.execute("SELECT COUNT(*) FROM tags")
            stats['total_tags'] = cursor.fetchone()[0]
            
            # Total authors
            cursor = conn.execute("SELECT COUNT(*) FROM authors")
            stats['total_authors'] = cursor.fetchone()[0]
            
            return stats
