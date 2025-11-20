"""
Conversations Database Module
SQLite database for storing conversation history
"""
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class ConversationRecord:
    """Conversation session record"""
    id: Optional[int]
    session_id: str
    created_at: str
    last_activity: str
    context: Optional[str]


@dataclass
class MessageRecord:
    """Message record"""
    id: Optional[int]
    session_id: str
    timestamp: str
    role: str  # 'user' or 'assistant'
    content: str
    context_books: Optional[str]  # JSON array of book IDs


class ConversationsDB:
    """Database for storing conversation history"""
    
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _connect(self) -> sqlite3.Connection:
        """Create database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign keys
        return conn
    
    def _init_db(self):
        """Initialize database schema"""
        with self._connect() as conn:
            # Conversations table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    context TEXT
                )
            """)
            
            # Messages table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    context_books TEXT,
                    FOREIGN KEY (session_id) REFERENCES conversations(session_id) ON DELETE CASCADE
                )
            """)
            
            # Create indices
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id)")
            
            conn.commit()
        
        print(f"✓ Conversations database initialized: {self.db_path}")
    
    # Conversation operations
    def add_conversation(self, session_id: str, context: Optional[str] = None) -> int:
        """Add new conversation session"""
        with self._connect() as conn:
            cursor = conn.execute("""
                INSERT INTO conversations (session_id, context)
                VALUES (?, ?)
            """, (session_id, context))
            conn.commit()
            return cursor.lastrowid
    
    def get_conversation(self, session_id: str) -> Optional[ConversationRecord]:
        """Get conversation by session ID"""
        with self._connect() as conn:
            cursor = conn.execute("""
                SELECT * FROM conversations WHERE session_id = ?
            """, (session_id,))
            row = cursor.fetchone()
            if row:
                return ConversationRecord(**dict(row))
            return None
    
    def update_conversation_activity(self, session_id: str):
        """Update last activity timestamp"""
        with self._connect() as conn:
            conn.execute("""
                UPDATE conversations 
                SET last_activity = CURRENT_TIMESTAMP 
                WHERE session_id = ?
            """, (session_id,))
            conn.commit()
    
    def update_conversation_context(self, session_id: str, context: str):
        """Update conversation context"""
        with self._connect() as conn:
            conn.execute("""
                UPDATE conversations 
                SET context = ?, last_activity = CURRENT_TIMESTAMP 
                WHERE session_id = ?
            """, (context, session_id))
            conn.commit()
    
    def delete_conversation(self, session_id: str) -> bool:
        """Delete conversation and all its messages"""
        with self._connect() as conn:
            cursor = conn.execute("""
                DELETE FROM conversations WHERE session_id = ?
            """, (session_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_all_conversations(self, limit: int = 50, offset: int = 0) -> List[ConversationRecord]:
        """Get all conversations with pagination"""
        with self._connect() as conn:
            cursor = conn.execute("""
                SELECT * FROM conversations 
                ORDER BY last_activity DESC 
                LIMIT ? OFFSET ?
            """, (limit, offset))
            return [ConversationRecord(**dict(row)) for row in cursor.fetchall()]
    
    # Message operations
    def add_message(self, message: MessageRecord) -> int:
        """Add message to conversation"""
        with self._connect() as conn:
            cursor = conn.execute("""
                INSERT INTO messages (session_id, role, content, context_books)
                VALUES (?, ?, ?, ?)
            """, (message.session_id, message.role, message.content, message.context_books))
            conn.commit()
            
            # Update conversation activity
            self.update_conversation_activity(message.session_id)
            
            return cursor.lastrowid
    
    def get_messages(self, session_id: str) -> List[MessageRecord]:
        """Get all messages for a conversation"""
        with self._connect() as conn:
            cursor = conn.execute("""
                SELECT * FROM messages 
                WHERE session_id = ? 
                ORDER BY timestamp ASC
            """, (session_id,))
            return [MessageRecord(**dict(row)) for row in cursor.fetchall()]
    
    def delete_message(self, message_id: int) -> bool:
        """Delete a specific message"""
        with self._connect() as conn:
            cursor = conn.execute("""
                DELETE FROM messages WHERE id = ?
            """, (message_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def clear_conversation_messages(self, session_id: str) -> int:
        """Clear all messages from a conversation"""
        with self._connect() as conn:
            cursor = conn.execute("""
                DELETE FROM messages WHERE session_id = ?
            """, (session_id,))
            conn.commit()
            return cursor.rowcount
    
    # Search and statistics
    def search_conversations(self, query: str, limit: int = 20) -> List[Dict]:
        """Search conversations by content"""
        with self._connect() as conn:
            cursor = conn.execute("""
                SELECT DISTINCT c.*, 
                       (SELECT COUNT(*) FROM messages WHERE session_id = c.session_id) as message_count
                FROM conversations c
                JOIN messages m ON c.session_id = m.session_id
                WHERE m.content LIKE ?
                ORDER BY c.last_activity DESC
                LIMIT ?
            """, (f"%{query}%", limit))
            
            results = []
            for row in cursor.fetchall():
                results.append(dict(row))
            return results
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        with self._connect() as conn:
            stats = {}
            
            cursor = conn.execute("SELECT COUNT(*) FROM conversations")
            stats['total_conversations'] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM messages")
            stats['total_messages'] = cursor.fetchone()[0]
            
            cursor = conn.execute("""
                SELECT COUNT(*) FROM conversations 
                WHERE datetime(last_activity) > datetime('now', '-1 day')
            """)
            stats['active_last_24h'] = cursor.fetchone()[0]
            
            return stats
    
    def export_conversation(self, session_id: str) -> Optional[Dict]:
        """Export conversation with all messages"""
        conversation = self.get_conversation(session_id)
        if not conversation:
            return None
        
        messages = self.get_messages(session_id)
        
        return {
            'session_id': conversation.session_id,
            'created_at': conversation.created_at,
            'last_activity': conversation.last_activity,
            'context': conversation.context,
            'messages': [
                {
                    'timestamp': msg.timestamp,
                    'role': msg.role,
                    'content': msg.content,
                    'context_books': json.loads(msg.context_books) if msg.context_books else None
                }
                for msg in messages
            ]
        }


if __name__ == "__main__":
    # Quick test
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db = ConversationsDB(Path(tmpdir) / "conversations.db")
        
        # Add conversation
        session_id = "test-session-123"
        db.add_conversation(session_id, "Test context")
        print(f"✓ Added conversation: {session_id}")
        
        # Add messages
        msg1 = MessageRecord(
            id=None,
            session_id=session_id,
            timestamp=None,
            role="user",
            content="What is machine learning?",
            context_books=json.dumps([1, 2, 3])
        )
        db.add_message(msg1)
        
        msg2 = MessageRecord(
            id=None,
            session_id=session_id,
            timestamp=None,
            role="assistant",
            content="Machine learning is...",
            context_books=None
        )
        db.add_message(msg2)
        print(f"✓ Added 2 messages")
        
        # Get messages
        messages = db.get_messages(session_id)
        print(f"✓ Retrieved {len(messages)} messages")
        
        # Export
        export = db.export_conversation(session_id)
        print(f"✓ Exported conversation with {len(export['messages'])} messages")
        
        # Stats
        stats = db.get_stats()
        print(f"✓ Stats: {stats}")
        
        # Delete
        db.delete_conversation(session_id)
        print(f"✓ Deleted conversation")
