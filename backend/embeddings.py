"""
Embeddings Generator Module
Generates vector embeddings from text using Sentence Transformers
"""
from pathlib import Path
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import pickle


class EmbeddingsGenerator:
    """Generate and manage text embeddings"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embeddings generator
        
        Args:
            model_name: Name of the sentence-transformers model
        """
        self.model_name = model_name
        print(f"Loading model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        print(f"✓ Model loaded. Embedding dimension: {self.embedding_dim}")
    
    def encode_text(self, text: str) -> np.ndarray:
        """
        Encode single text to embedding vector
        
        Args:
            text: Text to encode
            
        Returns:
            Embedding vector (numpy array)
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return np.zeros(self.embedding_dim)
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding
    
    def encode_batch(self, texts: List[str], batch_size: int = 32, 
                     show_progress: bool = True) -> np.ndarray:
        """
        Encode multiple texts in batches
        
        Args:
            texts: List of texts to encode
            batch_size: Number of texts to process at once
            show_progress: Show progress bar
            
        Returns:
            Array of embeddings (shape: [num_texts, embedding_dim])
        """
        if not texts:
            return np.array([])
        
        # Filter out empty texts but keep track of indices
        valid_indices = [i for i, text in enumerate(texts) if text and text.strip()]
        valid_texts = [texts[i] for i in valid_indices]
        
        if not valid_texts:
            # All texts are empty
            return np.zeros((len(texts), self.embedding_dim))
        
        # Encode valid texts
        embeddings = self.model.encode(
            valid_texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )
        
        # Create result array with zeros for empty texts
        result = np.zeros((len(texts), self.embedding_dim))
        for i, valid_idx in enumerate(valid_indices):
            result[valid_idx] = embeddings[i]
        
        return result
    
    def save_embeddings(self, embeddings: np.ndarray, filepath: Path):
        """Save embeddings to disk"""
        np.save(filepath, embeddings)
        print(f"✓ Saved {len(embeddings)} embeddings to {filepath}")
    
    def load_embeddings(self, filepath: Path) -> np.ndarray:
        """Load embeddings from disk"""
        embeddings = np.load(filepath)
        print(f"✓ Loaded {len(embeddings)} embeddings from {filepath}")
        return embeddings
    
    def get_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score (0-1, higher is more similar)
        """
        # Normalize vectors
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Cosine similarity
        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
        return float(similarity)


class EmbeddingsPipeline:
    """Pipeline for processing books and generating embeddings"""
    
    def __init__(self, generator: EmbeddingsGenerator, output_dir: Path):
        self.generator = generator
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # State file for resumable processing
        self.state_file = self.output_dir / "pipeline_state.pkl"
        self.state = self._load_state()
    
    def _load_state(self) -> dict:
        """Load pipeline state for resuming"""
        if self.state_file.exists():
            with open(self.state_file, 'rb') as f:
                return pickle.load(f)
        return {
            'processed_books': set(),
            'total_chunks': 0,
            'last_book_id': 0
        }
    
    def _save_state(self):
        """Save pipeline state"""
        with open(self.state_file, 'wb') as f:
            pickle.dump(self.state, f)
    
    def is_book_processed(self, book_id: int) -> bool:
        """Check if book has been processed"""
        return book_id in self.state['processed_books']
    
    def mark_book_processed(self, book_id: int):
        """Mark book as processed"""
        self.state['processed_books'].add(book_id)
        self.state['last_book_id'] = book_id
        self._save_state()
    
    def process_texts(self, texts: List[str], description: str = "Processing") -> np.ndarray:
        """
        Process list of texts and generate embeddings
        
        Args:
            texts: List of texts to process
            description: Description for progress bar
            
        Returns:
            Array of embeddings
        """
        print(f"\n{description}: {len(texts)} texts")
        embeddings = self.generator.encode_batch(texts, show_progress=True)
        
        self.state['total_chunks'] += len(texts)
        self._save_state()
        
        return embeddings
    
    def get_stats(self) -> dict:
        """Get pipeline statistics"""
        return {
            'processed_books': len(self.state['processed_books']),
            'total_chunks': self.state['total_chunks'],
            'last_book_id': self.state['last_book_id']
        }
    
    def reset(self):
        """Reset pipeline state"""
        self.state = {
            'processed_books': set(),
            'total_chunks': 0,
            'last_book_id': 0
        }
        self._save_state()
        print("✓ Pipeline state reset")


def test_embeddings_model():
    """Quick test of embeddings model"""
    print("Testing embeddings model...")
    
    generator = EmbeddingsGenerator()
    
    # Test single encoding
    text = "This is a test sentence about artificial intelligence."
    embedding = generator.encode_text(text)
    
    print(f"✓ Single text encoded: shape {embedding.shape}")
    
    # Test batch encoding
    texts = [
        "Machine learning is fascinating",
        "Natural language processing",
        "Deep learning and neural networks",
        "Computer vision applications"
    ]
    
    embeddings = generator.encode_batch(texts, show_progress=False)
    print(f"✓ Batch encoded: shape {embeddings.shape}")
    
    # Test similarity
    sim = generator.get_similarity(embeddings[0], embeddings[1])
    print(f"✓ Similarity between text 1 and 2: {sim:.3f}")
    
    # Test with similar texts
    text1 = "I love reading books about history"
    text2 = "Historical books are my favorite"
    text3 = "I enjoy playing video games"
    
    emb1 = generator.encode_text(text1)
    emb2 = generator.encode_text(text2)
    emb3 = generator.encode_text(text3)
    
    sim_12 = generator.get_similarity(emb1, emb2)
    sim_13 = generator.get_similarity(emb1, emb3)
    
    print(f"✓ Similarity (history books): {sim_12:.3f}")
    print(f"✓ Similarity (books vs games): {sim_13:.3f}")
    print(f"✓ Semantic similarity working: {sim_12 > sim_13}")
    
    return generator


if __name__ == "__main__":
    test_embeddings_model()
