"""
EPUB Extractor Module
Extracts table of contents and text content from EPUB files
"""
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import re


@dataclass
class Chapter:
    """Chapter information"""
    num: int
    title: str
    file_path: str
    text: str
    word_count: int


@dataclass
class TOCEntry:
    """Table of Contents entry"""
    title: str
    file_path: str
    level: int = 0


class EPUBExtractor:
    """Extract content from EPUB files"""
    
    def __init__(self, epub_path: Path):
        self.epub_path = Path(epub_path)
        if not self.epub_path.exists():
            raise FileNotFoundError(f"EPUB not found: {epub_path}")
        
        try:
            self.book = epub.read_epub(str(epub_path))
        except Exception as e:
            raise ValueError(f"Failed to read EPUB: {e}")
    
    def get_metadata(self) -> Dict:
        """Extract basic metadata"""
        metadata = {}
        
        # Title
        title = self.book.get_metadata('DC', 'title')
        metadata['title'] = title[0][0] if title else None
        
        # Author
        author = self.book.get_metadata('DC', 'creator')
        metadata['author'] = author[0][0] if author else None
        
        # Language
        language = self.book.get_metadata('DC', 'language')
        metadata['language'] = language[0][0] if language else None
        
        return metadata
    
    def get_toc(self) -> List[TOCEntry]:
        """Extract table of contents"""
        toc_entries = []
        
        try:
            toc = self.book.toc
            if not toc:
                # Fallback: use spine order
                return self._get_toc_from_spine()
            
            toc_entries = self._parse_toc(toc)
        except Exception as e:
            print(f"Warning: Could not extract TOC: {e}")
            toc_entries = self._get_toc_from_spine()
        
        return toc_entries
    
    def _parse_toc(self, toc, level=0) -> List[TOCEntry]:
        """Recursively parse TOC structure"""
        entries = []
        
        for item in toc:
            if isinstance(item, tuple):
                # Nested section
                section, children = item
                if hasattr(section, 'title') and hasattr(section, 'href'):
                    entries.append(TOCEntry(
                        title=section.title,
                        file_path=section.href.split('#')[0],
                        level=level
                    ))
                entries.extend(self._parse_toc(children, level + 1))
            elif hasattr(item, 'title') and hasattr(item, 'href'):
                # Single entry
                entries.append(TOCEntry(
                    title=item.title,
                    file_path=item.href.split('#')[0],
                    level=level
                ))
        
        return entries
    
    def _get_toc_from_spine(self) -> List[TOCEntry]:
        """Fallback: create TOC from spine (reading order)"""
        entries = []
        
        for idx, item in enumerate(self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT)):
            # Try to extract title from content
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            title_tag = soup.find(['h1', 'h2', 'title'])
            title = title_tag.get_text(strip=True) if title_tag else f"Chapter {idx + 1}"
            
            entries.append(TOCEntry(
                title=title,
                file_path=item.get_name(),
                level=0
            ))
        
        return entries
    
    def extract_text_from_html(self, html_content: bytes) -> str:
        """Extract clean text from HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(['script', 'style', 'nav']):
            script.decompose()
        
        # Get text
        text = soup.get_text(separator='\n')
        
        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines()]
        lines = [line for line in lines if line]
        text = '\n'.join(lines)
        
        return text
    
    def get_chapter(self, file_path: str) -> Optional[str]:
        """Get text content of a specific chapter"""
        for item in self.book.get_items():
            if item.get_name() == file_path:
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    return self.extract_text_from_html(item.get_content())
        return None
    
    def get_all_chapters(self) -> List[Chapter]:
        """Extract all chapters with content"""
        toc = self.get_toc()
        chapters = []
        
        for idx, entry in enumerate(toc):
            text = self.get_chapter(entry.file_path)
            if text:
                word_count = len(text.split())
                chapters.append(Chapter(
                    num=idx + 1,
                    title=entry.title,
                    file_path=entry.file_path,
                    text=text,
                    word_count=word_count
                ))
        
        return chapters
    
    def get_full_text(self) -> str:
        """Get all text content concatenated"""
        chapters = self.get_all_chapters()
        return '\n\n'.join(chapter.text for chapter in chapters)
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks by words"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
        
        return chunks
    
    def get_chapters_with_chunks(self, chunk_size: int = 500, overlap: int = 50) -> List[Dict]:
        """Get chapters with text split into chunks"""
        chapters = self.get_all_chapters()
        result = []
        
        for chapter in chapters:
            chunks = self.chunk_text(chapter.text, chunk_size, overlap)
            result.append({
                'chapter': chapter,
                'chunks': chunks
            })
        
        return result


def extract_epub_info(epub_path: Path) -> Dict:
    """Quick function to extract basic info from EPUB"""
    try:
        extractor = EPUBExtractor(epub_path)
        metadata = extractor.get_metadata()
        toc = extractor.get_toc()
        
        return {
            'success': True,
            'metadata': metadata,
            'toc_entries': len(toc),
            'toc': [{'title': e.title, 'level': e.level} for e in toc[:10]]  # First 10
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
