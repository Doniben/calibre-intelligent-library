"""
Tests for FastAPI endpoints
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


def test_root_endpoint():
    """Test root endpoint"""
    response = requests.get(f"{BASE_URL}/")
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["version"] == "1.0.0"
    
    print(f"✓ Root endpoint: {data['message']}")


def test_health_check():
    """Test health check endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "calibre_library" in data
    assert "indexed_books" in data
    assert "total_chunks" in data
    
    print(f"✓ Health check: {data['status']}")
    print(f"  Calibre library: {data['calibre_library']}")
    print(f"  Indexed books: {data['indexed_books']}")


def test_stats_endpoint():
    """Test stats endpoint"""
    response = requests.get(f"{BASE_URL}/stats")
    
    assert response.status_code == 200
    data = response.json()
    assert "calibre" in data
    assert "indexed" in data
    assert "vector_index" in data
    
    assert data["calibre"]["total_books"] > 0
    
    print(f"✓ Stats:")
    print(f"  Calibre books: {data['calibre']['total_books']:,}")
    print(f"  Indexed books: {data['indexed']['total_books']}")


def test_get_book():
    """Test get book endpoint"""
    # Test with book ID 1
    response = requests.get(f"{BASE_URL}/book/1")
    
    assert response.status_code == 200
    data = response.json()
    assert "title" in data
    assert "author" in data
    assert data["calibre_id"] == 1
    
    print(f"✓ Get book:")
    print(f"  Title: {data['title']}")
    print(f"  Author: {data['author']}")


def test_get_nonexistent_book():
    """Test get book with invalid ID"""
    response = requests.get(f"{BASE_URL}/book/999999")
    
    assert response.status_code == 404
    
    print(f"✓ Nonexistent book returns 404")


def test_search_without_index():
    """Test search when index is empty"""
    response = requests.post(
        f"{BASE_URL}/search",
        json={"query": "test query", "limit": 10}
    )
    
    # Should return 503 if no index
    if response.status_code == 503:
        print(f"✓ Search returns 503 when index not ready (expected)")
    else:
        # Or return empty results if index exists but is empty
        assert response.status_code == 200
        print(f"✓ Search endpoint accessible")


def test_api_documentation():
    """Test that API documentation is accessible"""
    response = requests.get(f"{BASE_URL}/docs")
    
    assert response.status_code == 200
    assert "swagger" in response.text.lower() or "openapi" in response.text.lower()
    
    print(f"✓ API documentation accessible at /docs")


if __name__ == "__main__":
    if is_server_running():
        print("✓ Server is running, executing tests...")
        pytest.main([__file__, "-v", "-s"])
    else:
        print("✗ Server is not running!")
        print("Start server with: python backend/server.py")
        print("Then run tests with: pytest tests/test_api.py")
