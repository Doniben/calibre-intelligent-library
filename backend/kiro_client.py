"""
Kiro CLI Client Module
Manages communication with Kiro CLI for conversational AI
"""
import subprocess
import json
import time
from typing import Optional, Dict, List
from pathlib import Path
import tempfile
import uuid


class KiroClient:
    """Client for interacting with Kiro CLI"""
    
    def __init__(self, command: str = "kiro-cli"):
        """
        Initialize Kiro client
        
        Args:
            command: Command to run Kiro CLI (default: kiro-cli)
        """
        self.command = command
        self._verify_kiro_available()
    
    def _verify_kiro_available(self):
        """Verify that Kiro CLI is available"""
        try:
            result = subprocess.run(
                [self.command, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"✓ Kiro CLI available: {self.command}")
            else:
                print(f"⚠ Kiro CLI command failed: {self.command}")
        except FileNotFoundError:
            raise RuntimeError(f"Kiro CLI not found: {self.command}. Make sure it's installed and in PATH.")
        except Exception as e:
            print(f"⚠ Could not verify Kiro CLI: {e}")
    
    def ask(self, question: str, context: Optional[str] = None, timeout: int = 60) -> str:
        """
        Ask Kiro a question
        
        Args:
            question: Question to ask
            context: Optional context to provide
            timeout: Timeout in seconds
            
        Returns:
            Kiro's response
        """
        # Build prompt
        if context:
            prompt = f"{context}\n\n{question}"
        else:
            prompt = question
        
        try:
            # Run Kiro CLI with prompt
            result = subprocess.run(
                [self.command, "chat", "--prompt", prompt],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                # Extract response (remove any CLI formatting)
                response = result.stdout.strip()
                return response
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                raise RuntimeError(f"Kiro CLI error: {error_msg}")
                
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Kiro CLI timed out after {timeout} seconds")
        except Exception as e:
            raise RuntimeError(f"Failed to communicate with Kiro CLI: {e}")
    
    def is_available(self) -> bool:
        """Check if Kiro CLI is available"""
        try:
            result = subprocess.run(
                [self.command, "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False


class KiroSession:
    """Manages a persistent conversation session with Kiro"""
    
    def __init__(self, session_id: Optional[str] = None, kiro_client: Optional[KiroClient] = None):
        """
        Initialize Kiro session
        
        Args:
            session_id: Optional session ID (generates new if not provided)
            kiro_client: Optional KiroClient instance
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.client = kiro_client or KiroClient()
        self.context = None
        self.history = []
        self.created_at = time.time()
        self.last_activity = time.time()
    
    def set_context(self, context: str):
        """Set context for the session"""
        self.context = context
        self.last_activity = time.time()
    
    def ask(self, question: str, additional_context: Optional[str] = None) -> str:
        """
        Ask a question in this session
        
        Args:
            question: Question to ask
            additional_context: Optional additional context for this specific question
            
        Returns:
            Kiro's response
        """
        # Build full context
        full_context = self.context
        if additional_context:
            full_context = f"{self.context}\n\n{additional_context}" if self.context else additional_context
        
        # Ask Kiro
        response = self.client.ask(question, full_context)
        
        # Update history
        self.history.append({
            "timestamp": time.time(),
            "question": question,
            "response": response,
            "context": additional_context
        })
        
        self.last_activity = time.time()
        
        return response
    
    def get_history(self) -> List[Dict]:
        """Get conversation history"""
        return self.history
    
    def clear_history(self):
        """Clear conversation history"""
        self.history = []
    
    def get_stats(self) -> Dict:
        """Get session statistics"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "message_count": len(self.history),
            "has_context": self.context is not None
        }


class KiroSessionManager:
    """Manages multiple Kiro sessions"""
    
    def __init__(self, kiro_client: Optional[KiroClient] = None):
        """
        Initialize session manager
        
        Args:
            kiro_client: Optional shared KiroClient instance
        """
        self.client = kiro_client or KiroClient()
        self.sessions = {}
        self.max_inactive_time = 3600  # 1 hour
    
    def create_session(self, session_id: Optional[str] = None) -> KiroSession:
        """
        Create a new session
        
        Args:
            session_id: Optional session ID
            
        Returns:
            New KiroSession
        """
        session = KiroSession(session_id, self.client)
        self.sessions[session.session_id] = session
        print(f"✓ Created session: {session.session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[KiroSession]:
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            print(f"✓ Deleted session: {session_id}")
            return True
        return False
    
    def cleanup_inactive_sessions(self):
        """Remove inactive sessions"""
        current_time = time.time()
        inactive = []
        
        for session_id, session in self.sessions.items():
            if current_time - session.last_activity > self.max_inactive_time:
                inactive.append(session_id)
        
        for session_id in inactive:
            self.delete_session(session_id)
        
        if inactive:
            print(f"✓ Cleaned up {len(inactive)} inactive sessions")
    
    def get_all_sessions(self) -> List[Dict]:
        """Get stats for all sessions"""
        return [session.get_stats() for session in self.sessions.values()]


def format_books_context(books: List[Dict]) -> str:
    """
    Format book search results as context for Kiro
    
    Args:
        books: List of book dictionaries with metadata
        
    Returns:
        Formatted context string
    """
    if not books:
        return "No books found."
    
    context_parts = ["Books found in the library:\n"]
    
    for i, book in enumerate(books, 1):
        context_parts.append(f"\n{i}. **{book.get('title', 'Unknown')}**")
        
        if book.get('author'):
            context_parts.append(f"   Author: {book['author']}")
        
        if book.get('pubdate'):
            context_parts.append(f"   Published: {book['pubdate']}")
        
        if book.get('tags'):
            context_parts.append(f"   Tags: {book['tags']}")
        
        if book.get('summary'):
            summary = book['summary']
            if len(summary) > 200:
                summary = summary[:200] + "..."
            context_parts.append(f"   Summary: {summary}")
        
        if book.get('chapter_title'):
            context_parts.append(f"   Relevant chapter: {book['chapter_title']}")
        
        if book.get('similarity'):
            context_parts.append(f"   Relevance: {book['similarity']:.2%}")
    
    return "\n".join(context_parts)


if __name__ == "__main__":
    # Quick test
    print("Testing Kiro Client...")
    
    try:
        client = KiroClient()
        
        if client.is_available():
            print("✓ Kiro CLI is available")
            
            # Test simple question
            response = client.ask("What is 2+2?")
            print(f"✓ Response received: {response[:100]}...")
            
            # Test with context
            context = "I'm looking for books about machine learning."
            response = client.ask("What topics should I focus on?", context)
            print(f"✓ Response with context: {response[:100]}...")
            
        else:
            print("✗ Kiro CLI not available")
            
    except Exception as e:
        print(f"✗ Error: {e}")
