"""
Tests for Kiro Client
"""
import pytest
from pathlib import Path
import sys
import time

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from kiro_client import KiroClient, KiroSession, KiroSessionManager, format_books_context


def test_kiro_client_init():
    """Test KiroClient initialization"""
    try:
        client = KiroClient()
        assert client.command == "kiro-cli"
        print(f"✓ KiroClient initialized")
    except RuntimeError as e:
        pytest.skip(f"Kiro CLI not available: {e}")


def test_kiro_is_available():
    """Test checking if Kiro is available"""
    try:
        client = KiroClient()
        available = client.is_available()
        assert isinstance(available, bool)
        print(f"✓ Kiro available: {available}")
    except RuntimeError:
        pytest.skip("Kiro CLI not available")


def test_kiro_ask_simple():
    """Test asking a simple question"""
    try:
        client = KiroClient()
        
        if not client.is_available():
            pytest.skip("Kiro CLI not available")
        
        response = client.ask("What is 2+2? Answer with just the number.")
        
        assert response is not None
        assert len(response) > 0
        
        print(f"✓ Kiro response: {response[:100]}...")
        
    except RuntimeError:
        pytest.skip("Kiro CLI not available")


def test_kiro_ask_with_context():
    """Test asking with context"""
    try:
        client = KiroClient()
        
        if not client.is_available():
            pytest.skip("Kiro CLI not available")
        
        context = "You are helping with a book library. The user is looking for books about AI."
        question = "What topics should they focus on?"
        
        response = client.ask(question, context)
        
        assert response is not None
        assert len(response) > 0
        
        print(f"✓ Kiro response with context: {response[:100]}...")
        
    except RuntimeError:
        pytest.skip("Kiro CLI not available")


def test_kiro_session_init():
    """Test KiroSession initialization"""
    try:
        client = KiroClient()
        session = KiroSession(kiro_client=client)
        
        assert session.session_id is not None
        assert len(session.history) == 0
        assert session.context is None
        
        print(f"✓ Session created: {session.session_id}")
        
    except RuntimeError:
        pytest.skip("Kiro CLI not available")


def test_kiro_session_set_context():
    """Test setting session context"""
    try:
        client = KiroClient()
        session = KiroSession(kiro_client=client)
        
        context = "Books about machine learning"
        session.set_context(context)
        
        assert session.context == context
        
        print(f"✓ Context set")
        
    except RuntimeError:
        pytest.skip("Kiro CLI not available")


def test_kiro_session_ask():
    """Test asking in a session"""
    try:
        client = KiroClient()
        
        if not client.is_available():
            pytest.skip("Kiro CLI not available")
        
        session = KiroSession(kiro_client=client)
        session.set_context("You are helping with book recommendations.")
        
        response = session.ask("What makes a good technical book?")
        
        assert response is not None
        assert len(session.history) == 1
        assert session.history[0]['question'] == "What makes a good technical book?"
        
        print(f"✓ Session question answered")
        print(f"  History length: {len(session.history)}")
        
    except RuntimeError:
        pytest.skip("Kiro CLI not available")


def test_kiro_session_history():
    """Test session history"""
    try:
        client = KiroClient()
        
        if not client.is_available():
            pytest.skip("Kiro CLI not available")
        
        session = KiroSession(kiro_client=client)
        
        # Ask multiple questions
        session.ask("Question 1")
        session.ask("Question 2")
        
        history = session.get_history()
        assert len(history) == 2
        assert history[0]['question'] == "Question 1"
        assert history[1]['question'] == "Question 2"
        
        # Clear history
        session.clear_history()
        assert len(session.get_history()) == 0
        
        print(f"✓ Session history working")
        
    except RuntimeError:
        pytest.skip("Kiro CLI not available")


def test_kiro_session_stats():
    """Test session statistics"""
    try:
        client = KiroClient()
        session = KiroSession(kiro_client=client)
        
        stats = session.get_stats()
        
        assert 'session_id' in stats
        assert 'created_at' in stats
        assert 'message_count' in stats
        assert stats['message_count'] == 0
        
        print(f"✓ Session stats: {stats}")
        
    except RuntimeError:
        pytest.skip("Kiro CLI not available")


def test_session_manager_create():
    """Test SessionManager create session"""
    try:
        client = KiroClient()
        manager = KiroSessionManager(client)
        
        session = manager.create_session()
        
        assert session.session_id in manager.sessions
        
        print(f"✓ Session manager created session")
        
    except RuntimeError:
        pytest.skip("Kiro CLI not available")


def test_session_manager_get():
    """Test SessionManager get session"""
    try:
        client = KiroClient()
        manager = KiroSessionManager(client)
        
        session1 = manager.create_session()
        session2 = manager.get_session(session1.session_id)
        
        assert session1 is session2
        
        print(f"✓ Session manager get working")
        
    except RuntimeError:
        pytest.skip("Kiro CLI not available")


def test_session_manager_delete():
    """Test SessionManager delete session"""
    try:
        client = KiroClient()
        manager = KiroSessionManager(client)
        
        session = manager.create_session()
        session_id = session.session_id
        
        assert manager.delete_session(session_id)
        assert session_id not in manager.sessions
        
        print(f"✓ Session manager delete working")
        
    except RuntimeError:
        pytest.skip("Kiro CLI not available")


def test_format_books_context():
    """Test formatting books as context"""
    books = [
        {
            'title': 'Machine Learning Basics',
            'author': 'John Doe',
            'pubdate': '2023-01-01',
            'tags': 'AI, ML',
            'summary': 'A comprehensive guide to machine learning algorithms and techniques.',
            'similarity': 0.95
        },
        {
            'title': 'Deep Learning',
            'author': 'Jane Smith',
            'summary': 'Understanding neural networks',
            'chapter_title': 'Introduction to CNNs',
            'similarity': 0.87
        }
    ]
    
    context = format_books_context(books)
    
    assert 'Machine Learning Basics' in context
    assert 'John Doe' in context
    assert 'Deep Learning' in context
    assert 'Introduction to CNNs' in context
    assert '95' in context  # Check for percentage
    
    print(f"✓ Books context formatted:")
    print(context[:200] + "...")


def test_format_books_context_empty():
    """Test formatting empty books list"""
    context = format_books_context([])
    
    assert context == "No books found."
    
    print(f"✓ Empty books context handled")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
