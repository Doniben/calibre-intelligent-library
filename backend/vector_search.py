"""
Vector Search Module using FAISS
Fast similarity search for embeddings
"""
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np
import faiss
import pickle


class VectorIndex:
    """FAISS-based vector index for similarity search"""
    
    def __init__(self, dimension: int = 384):
        """
        Initialize vector index
        
        Args:
            dimension: Dimension of embedding vectors
        """
        self.dimension = dimension
        self.index = None
        self.metadata = []  # Store metadata for each vector
        self._create_index()
    
    def _create_index(self):
        """Create FAISS index"""
        # Using IndexFlatIP (Inner Product) for cosine similarity
        # Vectors should be normalized before adding
        self.index = faiss.IndexFlatIP(self.dimension)
        print(f"✓ Created FAISS index (dimension: {self.dimension})")
    
    def normalize_vectors(self, vectors: np.ndarray) -> np.ndarray:
        """
        Normalize vectors for cosine similarity
        
        Args:
            vectors: Array of vectors to normalize
            
        Returns:
            Normalized vectors
        """
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        # Avoid division by zero
        norms = np.where(norms == 0, 1, norms)
        return vectors / norms
    
    def add_vectors(self, vectors: np.ndarray, metadata: List[dict] = None):
        """
        Add vectors to index
        
        Args:
            vectors: Array of vectors to add (shape: [n, dimension])
            metadata: Optional list of metadata dicts for each vector
        """
        if vectors.shape[1] != self.dimension:
            raise ValueError(f"Vector dimension {vectors.shape[1]} doesn't match index dimension {self.dimension}")
        
        # Normalize vectors for cosine similarity
        normalized = self.normalize_vectors(vectors)
        
        # Add to index
        self.index.add(normalized.astype('float32'))
        
        # Store metadata
        if metadata:
            self.metadata.extend(metadata)
        else:
            # Create empty metadata
            self.metadata.extend([{}] * len(vectors))
        
        print(f"✓ Added {len(vectors)} vectors to index (total: {self.index.ntotal})")
    
    def search(self, query_vector: np.ndarray, k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """
        Search for similar vectors
        
        Args:
            query_vector: Query vector (shape: [dimension])
            k: Number of results to return
            
        Returns:
            Tuple of (similarities, indices)
        """
        if self.index.ntotal == 0:
            return np.array([]), np.array([])
        
        # Normalize query vector
        query = query_vector.reshape(1, -1)
        query_normalized = self.normalize_vectors(query).astype('float32')
        
        # Search
        k = min(k, self.index.ntotal)  # Don't search for more than available
        similarities, indices = self.index.search(query_normalized, k)
        
        return similarities[0], indices[0]
    
    def search_with_metadata(self, query_vector: np.ndarray, k: int = 10) -> List[dict]:
        """
        Search and return results with metadata
        
        Args:
            query_vector: Query vector
            k: Number of results
            
        Returns:
            List of dicts with 'similarity', 'index', and metadata
        """
        similarities, indices = self.search(query_vector, k)
        
        results = []
        for sim, idx in zip(similarities, indices):
            result = {
                'similarity': float(sim),
                'index': int(idx),
                **self.metadata[idx]  # Merge metadata
            }
            results.append(result)
        
        return results
    
    def save(self, filepath: Path):
        """
        Save index and metadata to disk
        
        Args:
            filepath: Path to save (without extension)
        """
        filepath = Path(filepath)
        
        # Save FAISS index
        index_path = filepath.with_suffix('.faiss')
        faiss.write_index(self.index, str(index_path))
        
        # Save metadata
        metadata_path = filepath.with_suffix('.meta')
        with open(metadata_path, 'wb') as f:
            pickle.dump({
                'dimension': self.dimension,
                'metadata': self.metadata
            }, f)
        
        print(f"✓ Saved index to {index_path}")
        print(f"✓ Saved metadata to {metadata_path}")
    
    def load(self, filepath: Path):
        """
        Load index and metadata from disk
        
        Args:
            filepath: Path to load (without extension)
        """
        filepath = Path(filepath)
        
        # Load FAISS index
        index_path = filepath.with_suffix('.faiss')
        if not index_path.exists():
            raise FileNotFoundError(f"Index file not found: {index_path}")
        
        self.index = faiss.read_index(str(index_path))
        
        # Load metadata
        metadata_path = filepath.with_suffix('.meta')
        if metadata_path.exists():
            with open(metadata_path, 'rb') as f:
                data = pickle.load(f)
                self.dimension = data['dimension']
                self.metadata = data['metadata']
        
        print(f"✓ Loaded index from {index_path}")
        print(f"  Total vectors: {self.index.ntotal}")
        print(f"  Dimension: {self.dimension}")
    
    def get_stats(self) -> dict:
        """Get index statistics"""
        return {
            'total_vectors': self.index.ntotal if self.index else 0,
            'dimension': self.dimension,
            'has_metadata': len(self.metadata) > 0
        }


class SearchEngine:
    """High-level search engine combining embeddings and vector index"""
    
    def __init__(self, embeddings_generator, vector_index: VectorIndex):
        """
        Initialize search engine
        
        Args:
            embeddings_generator: EmbeddingsGenerator instance
            vector_index: VectorIndex instance
        """
        self.generator = embeddings_generator
        self.index = vector_index
    
    def index_texts(self, texts: List[str], metadata: List[dict] = None):
        """
        Index texts for search
        
        Args:
            texts: List of texts to index
            metadata: Optional metadata for each text
        """
        print(f"Generating embeddings for {len(texts)} texts...")
        embeddings = self.generator.encode_batch(texts, show_progress=True)
        
        print(f"Adding to vector index...")
        self.index.add_vectors(embeddings, metadata)
    
    def search(self, query: str, k: int = 10, min_similarity: float = 0.0) -> List[dict]:
        """
        Search for similar texts
        
        Args:
            query: Search query text
            k: Number of results
            min_similarity: Minimum similarity threshold (0-1)
            
        Returns:
            List of results with similarity and metadata
        """
        # Generate query embedding
        query_embedding = self.generator.encode_text(query)
        
        # Search
        results = self.index.search_with_metadata(query_embedding, k)
        
        # Filter by minimum similarity
        if min_similarity > 0:
            results = [r for r in results if r['similarity'] >= min_similarity]
        
        return results
    
    def save(self, filepath: Path):
        """Save search engine state"""
        self.index.save(filepath)
    
    def load(self, filepath: Path):
        """Load search engine state"""
        self.index.load(filepath)


def test_vector_search():
    """Test vector search functionality"""
    print("Testing FAISS vector search...")
    
    # Create index
    index = VectorIndex(dimension=384)
    
    # Create some test vectors
    np.random.seed(42)
    vectors = np.random.randn(100, 384).astype('float32')
    
    # Add metadata
    metadata = [{'id': i, 'text': f'Document {i}'} for i in range(100)]
    
    # Add to index
    index.add_vectors(vectors, metadata)
    
    # Search
    query = vectors[0]  # Use first vector as query
    results = index.search_with_metadata(query, k=5)
    
    print(f"\n✓ Search results for query (should find itself first):")
    for i, result in enumerate(results):
        print(f"  {i+1}. ID: {result['id']}, Similarity: {result['similarity']:.3f}")
    
    # First result should be the query itself with similarity ~1.0
    assert results[0]['id'] == 0
    assert results[0]['similarity'] > 0.99
    
    # Test save/load
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "test_index"
        index.save(filepath)
        
        # Load in new index
        index2 = VectorIndex(dimension=384)
        index2.load(filepath)
        
        # Search should give same results
        results2 = index2.search_with_metadata(query, k=5)
        assert results2[0]['id'] == 0
        
        print(f"\n✓ Save/load working correctly")
    
    print(f"\n✓ All vector search tests passed!")


if __name__ == "__main__":
    test_vector_search()
