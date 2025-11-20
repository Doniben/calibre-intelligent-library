"""
Tests for Embeddings Generator
"""
import pytest
from pathlib import Path
import sys
import numpy as np
import tempfile

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from embeddings import EmbeddingsGenerator, EmbeddingsPipeline


def test_embeddings_generator_init():
    """Test EmbeddingsGenerator initialization"""
    generator = EmbeddingsGenerator()
    
    assert generator.model is not None
    assert generator.embedding_dim == 384  # all-MiniLM-L6-v2 dimension
    assert generator.model_name == "all-MiniLM-L6-v2"
    
    print(f"✓ Generator initialized with dimension: {generator.embedding_dim}")


def test_encode_single_text():
    """Test encoding single text"""
    generator = EmbeddingsGenerator()
    
    text = "This is a test sentence about machine learning."
    embedding = generator.encode_text(text)
    
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (384,)
    assert not np.all(embedding == 0)  # Should not be all zeros
    
    print(f"✓ Single text encoded: shape {embedding.shape}")
    print(f"  Sample values: {embedding[:5]}")


def test_encode_empty_text():
    """Test encoding empty text"""
    generator = EmbeddingsGenerator()
    
    embedding = generator.encode_text("")
    
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (384,)
    assert np.all(embedding == 0)  # Should be zero vector
    
    print(f"✓ Empty text returns zero vector")


def test_encode_batch():
    """Test batch encoding"""
    generator = EmbeddingsGenerator()
    
    texts = [
        "Machine learning is fascinating",
        "Natural language processing",
        "Deep learning and neural networks",
        "Computer vision applications",
        "Artificial intelligence research"
    ]
    
    embeddings = generator.encode_batch(texts, show_progress=False)
    
    assert isinstance(embeddings, np.ndarray)
    assert embeddings.shape == (5, 384)
    assert not np.all(embeddings == 0)
    
    print(f"✓ Batch encoded: {len(texts)} texts")
    print(f"  Shape: {embeddings.shape}")


def test_encode_batch_with_empty():
    """Test batch encoding with some empty texts"""
    generator = EmbeddingsGenerator()
    
    texts = [
        "Valid text",
        "",
        "Another valid text",
        "   ",  # Only whitespace
        "Last valid text"
    ]
    
    embeddings = generator.encode_batch(texts, show_progress=False)
    
    assert embeddings.shape == (5, 384)
    # Empty texts should have zero vectors
    assert np.all(embeddings[1] == 0)
    assert np.all(embeddings[3] == 0)
    # Valid texts should not be zero
    assert not np.all(embeddings[0] == 0)
    assert not np.all(embeddings[2] == 0)
    
    print(f"✓ Batch with empty texts handled correctly")


def test_similarity():
    """Test similarity calculation"""
    generator = EmbeddingsGenerator()
    
    # Similar texts
    text1 = "I love reading books about history"
    text2 = "Historical books are my favorite"
    text3 = "I enjoy playing video games"
    
    emb1 = generator.encode_text(text1)
    emb2 = generator.encode_text(text2)
    emb3 = generator.encode_text(text3)
    
    sim_12 = generator.get_similarity(emb1, emb2)
    sim_13 = generator.get_similarity(emb1, emb3)
    
    # Similar texts should have higher similarity
    assert sim_12 > sim_13
    assert 0 <= sim_12 <= 1
    assert 0 <= sim_13 <= 1
    
    print(f"✓ Similarity calculation:")
    print(f"  Similar texts (history): {sim_12:.3f}")
    print(f"  Different texts (books vs games): {sim_13:.3f}")
    print(f"  Semantic understanding: {sim_12 > sim_13}")


def test_similarity_identical():
    """Test similarity of identical texts"""
    generator = EmbeddingsGenerator()
    
    text = "This is a test sentence"
    emb1 = generator.encode_text(text)
    emb2 = generator.encode_text(text)
    
    sim = generator.get_similarity(emb1, emb2)
    
    # Identical texts should have similarity ~1.0
    assert sim > 0.99
    
    print(f"✓ Identical texts similarity: {sim:.4f}")


def test_save_load_embeddings():
    """Test saving and loading embeddings"""
    generator = EmbeddingsGenerator()
    
    texts = ["Text 1", "Text 2", "Text 3"]
    embeddings = generator.encode_batch(texts, show_progress=False)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "test_embeddings.npy"
        
        # Save
        generator.save_embeddings(embeddings, filepath)
        assert filepath.exists()
        
        # Load
        loaded = generator.load_embeddings(filepath)
        
        assert loaded.shape == embeddings.shape
        assert np.allclose(loaded, embeddings)
    
    print(f"✓ Save/load embeddings working")


def test_embeddings_pipeline():
    """Test EmbeddingsPipeline"""
    generator = EmbeddingsGenerator()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline = EmbeddingsPipeline(generator, Path(tmpdir))
        
        # Check initial state
        stats = pipeline.get_stats()
        assert stats['processed_books'] == 0
        assert stats['total_chunks'] == 0
        
        # Process some texts
        texts = ["Text 1", "Text 2", "Text 3"]
        embeddings = pipeline.process_texts(texts, "Test processing")
        
        assert embeddings.shape == (3, 384)
        
        # Check updated state
        stats = pipeline.get_stats()
        assert stats['total_chunks'] == 3
        
        print(f"✓ Pipeline working:")
        print(f"  Processed chunks: {stats['total_chunks']}")


def test_pipeline_book_tracking():
    """Test pipeline book tracking"""
    generator = EmbeddingsGenerator()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline = EmbeddingsPipeline(generator, Path(tmpdir))
        
        # Mark books as processed
        pipeline.mark_book_processed(1)
        pipeline.mark_book_processed(2)
        
        assert pipeline.is_book_processed(1)
        assert pipeline.is_book_processed(2)
        assert not pipeline.is_book_processed(3)
        
        stats = pipeline.get_stats()
        assert stats['processed_books'] == 2
        assert stats['last_book_id'] == 2
        
        print(f"✓ Book tracking working")


def test_pipeline_resume():
    """Test pipeline state persistence"""
    generator = EmbeddingsGenerator()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create pipeline and process
        pipeline1 = EmbeddingsPipeline(generator, Path(tmpdir))
        pipeline1.mark_book_processed(1)
        pipeline1.mark_book_processed(2)
        
        # Create new pipeline instance (should load state)
        pipeline2 = EmbeddingsPipeline(generator, Path(tmpdir))
        
        assert pipeline2.is_book_processed(1)
        assert pipeline2.is_book_processed(2)
        
        stats = pipeline2.get_stats()
        assert stats['processed_books'] == 2
        
        print(f"✓ Pipeline state persistence working")


def test_semantic_search_simulation():
    """Test semantic search simulation"""
    generator = EmbeddingsGenerator()
    
    # Simulate a small library
    books = [
        "A comprehensive guide to machine learning algorithms",
        "Introduction to deep learning and neural networks",
        "Cooking recipes from around the world",
        "History of ancient civilizations",
        "Modern artificial intelligence techniques"
    ]
    
    # Generate embeddings
    book_embeddings = generator.encode_batch(books, show_progress=False)
    
    # Search query
    query = "artificial intelligence and machine learning"
    query_embedding = generator.encode_text(query)
    
    # Calculate similarities
    similarities = []
    for i, book_emb in enumerate(book_embeddings):
        sim = generator.get_similarity(query_embedding, book_emb)
        similarities.append((i, sim, books[i]))
    
    # Sort by similarity
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    # Top result should be ML/AI related
    top_idx, top_sim, top_book = similarities[0]
    assert top_idx in [0, 1, 4]  # ML, DL, or AI books
    
    print(f"✓ Semantic search simulation:")
    print(f"  Query: '{query}'")
    print(f"  Top 3 results:")
    for idx, sim, book in similarities[:3]:
        print(f"    {sim:.3f} - {book}")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
