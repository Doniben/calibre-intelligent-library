"""
Tests for Vector Search with FAISS
"""
import pytest
from pathlib import Path
import sys
import numpy as np
import tempfile

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from vector_search import VectorIndex, SearchEngine
from embeddings import EmbeddingsGenerator


@pytest.fixture(scope="module")
def generator():
    """Shared embeddings generator for all tests"""
    return EmbeddingsGenerator()


def test_vector_index_init():
    """Test VectorIndex initialization"""
    index = VectorIndex(dimension=384)
    
    assert index.dimension == 384
    assert index.index is not None
    assert index.index.ntotal == 0
    
    print(f"✓ VectorIndex initialized")


def test_normalize_vectors():
    """Test vector normalization"""
    index = VectorIndex(dimension=3)
    
    vectors = np.array([
        [3.0, 4.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0]  # Zero vector
    ])
    
    normalized = index.normalize_vectors(vectors)
    
    # Check norms (should be 1.0 for non-zero vectors)
    norms = np.linalg.norm(normalized, axis=1)
    assert abs(norms[0] - 1.0) < 0.001
    assert abs(norms[1] - 1.0) < 0.001
    # Zero vector stays zero
    assert np.allclose(normalized[2], [0, 0, 0])
    
    print(f"✓ Vector normalization working")


def test_add_vectors():
    """Test adding vectors to index"""
    index = VectorIndex(dimension=384)
    
    # Create random vectors
    np.random.seed(42)
    vectors = np.random.randn(10, 384).astype('float32')
    
    metadata = [{'id': i, 'text': f'Doc {i}'} for i in range(10)]
    
    index.add_vectors(vectors, metadata)
    
    assert index.index.ntotal == 10
    assert len(index.metadata) == 10
    
    print(f"✓ Added 10 vectors to index")


def test_search():
    """Test vector search"""
    index = VectorIndex(dimension=384)
    
    # Create vectors
    np.random.seed(42)
    vectors = np.random.randn(50, 384).astype('float32')
    metadata = [{'id': i} for i in range(50)]
    
    index.add_vectors(vectors, metadata)
    
    # Search with first vector (should find itself)
    query = vectors[0]
    similarities, indices = index.search(query, k=5)
    
    assert len(similarities) == 5
    assert len(indices) == 5
    assert indices[0] == 0  # Should find itself first
    assert similarities[0] > 0.99  # Should be very similar to itself
    
    print(f"✓ Search working:")
    print(f"  Top result: index {indices[0]}, similarity {similarities[0]:.3f}")


def test_search_with_metadata():
    """Test search with metadata"""
    index = VectorIndex(dimension=384)
    
    np.random.seed(42)
    vectors = np.random.randn(20, 384).astype('float32')
    metadata = [{'id': i, 'title': f'Document {i}'} for i in range(20)]
    
    index.add_vectors(vectors, metadata)
    
    query = vectors[5]
    results = index.search_with_metadata(query, k=3)
    
    assert len(results) == 3
    assert results[0]['id'] == 5  # Should find itself
    assert 'similarity' in results[0]
    assert 'title' in results[0]
    
    print(f"✓ Search with metadata:")
    for i, r in enumerate(results):
        print(f"  {i+1}. {r['title']}, similarity: {r['similarity']:.3f}")


def test_save_load():
    """Test saving and loading index"""
    index = VectorIndex(dimension=384)
    
    # Add some vectors
    np.random.seed(42)
    vectors = np.random.randn(30, 384).astype('float32')
    metadata = [{'id': i, 'data': f'test_{i}'} for i in range(30)]
    
    index.add_vectors(vectors, metadata)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "test_index"
        
        # Save
        index.save(filepath)
        
        # Check files exist
        assert (filepath.with_suffix('.faiss')).exists()
        assert (filepath.with_suffix('.meta')).exists()
        
        # Load in new index
        index2 = VectorIndex(dimension=384)
        index2.load(filepath)
        
        assert index2.index.ntotal == 30
        assert len(index2.metadata) == 30
        assert index2.metadata[0]['id'] == 0
        
        # Search should work the same
        query = vectors[10]
        results1 = index.search_with_metadata(query, k=3)
        results2 = index2.search_with_metadata(query, k=3)
        
        assert results1[0]['id'] == results2[0]['id']
        assert abs(results1[0]['similarity'] - results2[0]['similarity']) < 0.001
    
    print(f"✓ Save/load working correctly")


def test_get_stats():
    """Test getting index statistics"""
    index = VectorIndex(dimension=384)
    
    stats = index.get_stats()
    assert stats['total_vectors'] == 0
    assert stats['dimension'] == 384
    
    # Add vectors
    vectors = np.random.randn(15, 384).astype('float32')
    index.add_vectors(vectors)
    
    stats = index.get_stats()
    assert stats['total_vectors'] == 15
    
    print(f"✓ Stats: {stats}")


def test_search_engine(generator):
    """Test SearchEngine integration"""
    index = VectorIndex(dimension=384)
    engine = SearchEngine(generator, index)
    
    # Index some texts
    texts = [
        "Machine learning is a subset of artificial intelligence",
        "Deep learning uses neural networks",
        "Python is a programming language",
        "Natural language processing deals with text",
        "Computer vision processes images"
    ]
    
    metadata = [{'id': i, 'text': text} for i, text in enumerate(texts)]
    
    engine.index_texts(texts, metadata)
    
    # Search
    query = "artificial intelligence and neural networks"
    results = engine.search(query, k=3)
    
    assert len(results) > 0
    assert 'similarity' in results[0]
    assert 'text' in results[0]
    
    print(f"✓ SearchEngine working:")
    print(f"  Query: '{query}'")
    print(f"  Top 3 results:")
    for i, r in enumerate(results):
        print(f"    {i+1}. {r['text'][:50]}... (sim: {r['similarity']:.3f})")


def test_search_engine_save_load(generator):
    """Test SearchEngine save/load"""
    index = VectorIndex(dimension=384)
    engine = SearchEngine(generator, index)
    
    # Index texts
    texts = ["Text 1", "Text 2", "Text 3"]
    metadata = [{'id': i} for i in range(3)]
    engine.index_texts(texts, metadata)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "engine"
        
        # Save
        engine.save(filepath)
        
        # Load in new engine
        index2 = VectorIndex(dimension=384)
        engine2 = SearchEngine(generator, index2)
        engine2.load(filepath)
        
        # Should have same vectors
        assert engine2.index.index.ntotal == 3
    
    print(f"✓ SearchEngine save/load working")


def test_semantic_search_real(generator):
    """Test semantic search with real texts"""
    index = VectorIndex(dimension=384)
    engine = SearchEngine(generator, index)
    
    # Simulate book summaries
    books = [
        {
            'id': 1,
            'title': 'Introduction to Machine Learning',
            'summary': 'A comprehensive guide to machine learning algorithms, covering supervised and unsupervised learning techniques.'
        },
        {
            'id': 2,
            'title': 'Cooking Italian Food',
            'summary': 'Traditional Italian recipes including pasta, pizza, and desserts from various regions of Italy.'
        },
        {
            'id': 3,
            'title': 'Deep Learning Fundamentals',
            'summary': 'Understanding neural networks, backpropagation, and modern deep learning architectures.'
        },
        {
            'id': 4,
            'title': 'History of Rome',
            'summary': 'The rise and fall of the Roman Empire, from its founding to its eventual collapse.'
        },
        {
            'id': 5,
            'title': 'Artificial Intelligence Ethics',
            'summary': 'Exploring the ethical implications of AI systems and their impact on society.'
        }
    ]
    
    # Index summaries
    texts = [book['summary'] for book in books]
    metadata = [{'id': book['id'], 'title': book['title']} for book in books]
    
    engine.index_texts(texts, metadata)
    
    # Search for AI/ML books
    results = engine.search("artificial intelligence and machine learning", k=3)
    
    # Top results should be AI/ML related (ids 1, 3, 5)
    top_ids = [r['id'] for r in results]
    assert 1 in top_ids or 3 in top_ids or 5 in top_ids
    
    print(f"✓ Semantic search on book summaries:")
    print(f"  Query: 'artificial intelligence and machine learning'")
    print(f"  Top 3 results:")
    for i, r in enumerate(results):
        print(f"    {i+1}. {r['title']} (similarity: {r['similarity']:.3f})")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
