"""
Tests for Conversations Database
"""
import pytest
from pathlib import Path
import sys
import tempfile
import json

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from conversations_db import ConversationsDB, ConversationRecord, MessageRecord


@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db = ConversationsDB(Path(tmpdir) / "conversations.db")
        yield db


def test_db_init(temp_db):
    """Test database initialization"""
    assert temp_db.db_path.exists()
    stats = temp_db.get_stats()
    assert stats['total_conversations'] == 0
    assert stats['total_messages'] == 0
    
    print(f"✓ Conversations database initialized")


def test_add_conversation(temp_db):
    """Test adding a conversation"""
    session_id = "test-session-123"
    conv_id = temp_db.add_conversation(session_id, "Test context")
    
    assert conv_id > 0
    
    conv = temp_db.get_conversation(session_id)
    assert conv.session_id == session_id
    assert conv.context == "Test context"
    
    print(f"✓ Conversation added: {session_id}")


def test_add_message(temp_db):
    """Test adding messages"""
    session_id = "test-session"
    temp_db.add_conversation(session_id)
    
    msg = MessageRecord(
        id=None,
        session_id=session_id,
        timestamp=None,
        role="user",
        content="Test question",
        context_books=json.dumps([1, 2, 3])
    )
    
    msg_id = temp_db.add_message(msg)
    assert msg_id > 0
    
    messages = temp_db.get_messages(session_id)
    assert len(messages) == 1
    assert messages[0].content == "Test question"
    
    print(f"✓ Message added")


def test_conversation_workflow(temp_db):
    """Test complete conversation workflow"""
    session_id = "workflow-test"
    
    # Create conversation
    temp_db.add_conversation(session_id, "Books about AI")
    
    # Add user message
    user_msg = MessageRecord(
        id=None, session_id=session_id, timestamp=None,
        role="user", content="What is AI?", context_books=None
    )
    temp_db.add_message(user_msg)
    
    # Add assistant response
    assistant_msg = MessageRecord(
        id=None, session_id=session_id, timestamp=None,
        role="assistant", content="AI is...", context_books=None
    )
    temp_db.add_message(assistant_msg)
    
    # Get messages
    messages = temp_db.get_messages(session_id)
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[1].role == "assistant"
    
    print(f"✓ Conversation workflow complete")


def test_export_conversation(temp_db):
    """Test exporting conversation"""
    session_id = "export-test"
    temp_db.add_conversation(session_id)
    
    msg = MessageRecord(
        id=None, session_id=session_id, timestamp=None,
        role="user", content="Test", context_books=None
    )
    temp_db.add_message(msg)
    
    export = temp_db.export_conversation(session_id)
    
    assert export is not None
    assert export['session_id'] == session_id
    assert len(export['messages']) == 1
    
    print(f"✓ Conversation exported")


def test_delete_conversation(temp_db):
    """Test deleting conversation"""
    session_id = "delete-test"
    temp_db.add_conversation(session_id)
    
    msg = MessageRecord(
        id=None, session_id=session_id, timestamp=None,
        role="user", content="Test", context_books=None
    )
    temp_db.add_message(msg)
    
    # Delete
    assert temp_db.delete_conversation(session_id)
    
    # Verify deleted
    assert temp_db.get_conversation(session_id) is None
    assert len(temp_db.get_messages(session_id)) == 0
    
    print(f"✓ Conversation deleted (cascade)")


def test_clear_messages(temp_db):
    """Test clearing messages"""
    session_id = "clear-test"
    temp_db.add_conversation(session_id)
    
    # Add messages
    for i in range(3):
        msg = MessageRecord(
            id=None, session_id=session_id, timestamp=None,
            role="user", content=f"Message {i}", context_books=None
        )
        temp_db.add_message(msg)
    
    # Clear
    count = temp_db.clear_conversation_messages(session_id)
    assert count == 3
    
    # Verify cleared
    assert len(temp_db.get_messages(session_id)) == 0
    # But conversation still exists
    assert temp_db.get_conversation(session_id) is not None
    
    print(f"✓ Messages cleared (conversation kept)")


def test_search_conversations(temp_db):
    """Test searching conversations"""
    # Add conversations with messages
    for i in range(3):
        session_id = f"search-test-{i}"
        temp_db.add_conversation(session_id)
        
        msg = MessageRecord(
            id=None, session_id=session_id, timestamp=None,
            role="user", content=f"Question about machine learning {i}", context_books=None
        )
        temp_db.add_message(msg)
    
    # Search
    results = temp_db.search_conversations("machine learning")
    
    assert len(results) == 3
    
    print(f"✓ Search found {len(results)} conversations")


def test_get_stats(temp_db):
    """Test getting statistics"""
    # Add data
    temp_db.add_conversation("stats-test-1")
    temp_db.add_conversation("stats-test-2")
    
    msg = MessageRecord(
        id=None, session_id="stats-test-1", timestamp=None,
        role="user", content="Test", context_books=None
    )
    temp_db.add_message(msg)
    
    stats = temp_db.get_stats()
    
    assert stats['total_conversations'] == 2
    assert stats['total_messages'] == 1
    
    print(f"✓ Stats: {stats}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
