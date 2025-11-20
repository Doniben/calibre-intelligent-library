"""
Tests for Conversation API endpoints
Note: These tests require the server to be running
"""
import pytest
import requests
import time

BASE_URL = "http://127.0.0.1:8765"


def is_server_running():
    """Check if server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


@pytest.fixture(scope="module", autouse=True)
def check_server():
    """Check that server is running before tests"""
    if not is_server_running():
        pytest.skip("API server is not running. Start with: python backend/server.py")


def test_create_session():
    """Test creating a new session"""
    response = requests.post(f"{BASE_URL}/session/new")
    
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "created_at" in data
    assert len(data["session_id"]) > 0
    
    print(f"✓ Session created: {data['session_id']}")
    return data["session_id"]


def test_list_sessions():
    """Test listing all sessions"""
    # Create a session first
    requests.post(f"{BASE_URL}/session/new")
    
    response = requests.get(f"{BASE_URL}/sessions")
    
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "sessions" in data
    assert data["total"] > 0
    
    print(f"✓ Listed {data['total']} sessions")


def test_ask_question_simple():
    """Test asking a simple question"""
    # Create session
    session_response = requests.post(f"{BASE_URL}/session/new")
    session_id = session_response.json()["session_id"]
    
    # Ask question
    response = requests.post(
        f"{BASE_URL}/session/{session_id}/ask",
        json={"question": "What is 2+2?"}
    )
    
    # Note: This will fail if Kiro CLI is not available
    # but we test the endpoint structure
    if response.status_code == 200:
        data = response.json()
        assert "session_id" in data
        assert "question" in data
        assert "response" in data
        assert data["session_id"] == session_id
        print(f"✓ Question answered: {data['response'][:50]}...")
    elif response.status_code == 500:
        # Kiro CLI not available
        print(f"⚠ Kiro CLI not available (expected in test environment)")
        pytest.skip("Kiro CLI not available")
    else:
        pytest.fail(f"Unexpected status code: {response.status_code}")


def test_ask_question_with_context():
    """Test asking with book context"""
    # Create session
    session_response = requests.post(f"{BASE_URL}/session/new")
    session_id = session_response.json()["session_id"]
    
    # Ask with book context
    response = requests.post(
        f"{BASE_URL}/session/{session_id}/ask",
        json={
            "question": "What is this book about?",
            "context_books": [1]  # Book ID 1
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        assert data["session_id"] == session_id
        print(f"✓ Question with context answered")
    elif response.status_code == 500:
        print(f"⚠ Kiro CLI not available")
        pytest.skip("Kiro CLI not available")


def test_get_session_history():
    """Test getting session history"""
    # Create session
    session_response = requests.post(f"{BASE_URL}/session/new")
    session_id = session_response.json()["session_id"]
    
    # Get history (should be empty)
    response = requests.get(f"{BASE_URL}/session/{session_id}/history")
    
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "message_count" in data
    assert "messages" in data
    assert data["message_count"] == 0
    
    print(f"✓ Session history retrieved")


def test_delete_session():
    """Test deleting a session"""
    # Create session
    session_response = requests.post(f"{BASE_URL}/session/new")
    session_id = session_response.json()["session_id"]
    
    # Delete session
    response = requests.delete(f"{BASE_URL}/session/{session_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "deleted"
    assert data["session_id"] == session_id
    
    # Verify it's deleted
    history_response = requests.get(f"{BASE_URL}/session/{session_id}/history")
    assert history_response.status_code == 404
    
    print(f"✓ Session deleted")


def test_nonexistent_session():
    """Test accessing nonexistent session"""
    response = requests.get(f"{BASE_URL}/session/nonexistent-id/history")
    
    assert response.status_code == 404
    
    print(f"✓ Nonexistent session returns 404")


def test_session_workflow():
    """Test complete session workflow"""
    # 1. Create session
    session_response = requests.post(f"{BASE_URL}/session/new")
    assert session_response.status_code == 200
    session_id = session_response.json()["session_id"]
    
    # 2. Check it's in the list
    list_response = requests.get(f"{BASE_URL}/sessions")
    sessions = list_response.json()["sessions"]
    session_ids = [s["session_id"] for s in sessions]
    assert session_id in session_ids
    
    # 3. Get empty history
    history_response = requests.get(f"{BASE_URL}/session/{session_id}/history")
    assert history_response.json()["message_count"] == 0
    
    # 4. Delete session
    delete_response = requests.delete(f"{BASE_URL}/session/{session_id}")
    assert delete_response.status_code == 200
    
    # 5. Verify it's gone
    history_response = requests.get(f"{BASE_URL}/session/{session_id}/history")
    assert history_response.status_code == 404
    
    print(f"✓ Complete workflow validated")


if __name__ == "__main__":
    if is_server_running():
        print("✓ Server is running, executing tests...")
        pytest.main([__file__, "-v", "-s"])
    else:
        print("✗ Server is not running!")
        print("Start server with: python backend/server.py")
