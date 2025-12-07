"""
Vector Store using FAISS for semantic search
"""

import os
import pickle
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np

# Optional Imports for CI/Lightweight mode
try:
    import faiss
    from sentence_transformers import SentenceTransformer
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("Warning: RAG dependencies (faiss, sentence-transformers) not found. RAG features disabled.")

from .document_processor import Document
from .document_processor import Document

class VectorStore:
    """FAISS-based vector store for semantic search"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", index_path: Optional[Path] = None):
        """
        Initialize vector store
        
        Args:
            model_name: Sentence transformer model to use
            index_path: Path to save/load index
        """
        self.model_name = model_name
        self.index_path = index_path
        self.documents: List[Document] = []
        
        if ML_AVAILABLE:
            self.model = SentenceTransformer(model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            # Initialize FAISS index
            self.index = faiss.IndexFlatL2(self.dimension)
            print(f"Vector store initialized with model: {model_name}")
            print(f"Embedding dimension: {self.dimension}")
        else:
            self.model = None
            self.index = None
            self.dimension = 0
            print("Vector store initialized in dummy mode (no ML libs).")
    
    def add_documents(self, documents: List[Document]):
        """Add documents to the vector store"""
        if not ML_AVAILABLE:
            return
        if not documents:
            return
        
        print(f"Generating embeddings for {len(documents)} documents...")
        
        # Extract text content
        texts = [doc.content for doc in documents]
        
        # Generate embeddings in batches
        batch_size = 32
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self.model.encode(batch, show_progress_bar=False)
            embeddings.extend(batch_embeddings)
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings).astype('float32')
        
        # Add to FAISS index
        self.index.add(embeddings_array)
        self.documents.extend(documents)
        
        print(f"Added {len(documents)} documents to index")
        print(f"Total documents in index: {len(self.documents)}")
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[Document, float]]:
        """
        Search for similar documents
        
        Args:
            query: Search query
            top_k: Number of results to return
        
        Returns:
            List of (document, similarity_score) tuples
        """
        if not ML_AVAILABLE:
            return []
            
        if len(self.documents) == 0:
            return []
        
        # Generate query embedding
        query_embedding = self.model.encode([query])[0].astype('float32')
        query_embedding = np.array([query_embedding])
        
        # Search in FAISS
        distances, indices = self.index.search(query_embedding, min(top_k, len(self.documents)))
        
        # Prepare results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.documents):
                # Convert L2 distance to similarity score (lower distance = higher similarity)
                similarity = 1.0 / (1.0 + dist)
                results.append((self.documents[idx], similarity))
        
        return results
    
    def save(self, path: Optional[Path] = None):
        """Save index and documents to disk"""
        save_path = path or self.index_path
        if save_path is None:
            raise ValueError("No save path specified")
        
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        index_file = save_path / "faiss.index"
        if ML_AVAILABLE:
            faiss.write_index(self.index, str(index_file))
        
        # Save documents
        docs_file = save_path / "documents.pkl"
        with open(docs_file, 'wb') as f:
            pickle.dump(self.documents, f)
        
        # Save metadata
        metadata_file = save_path / "metadata.pkl"
        metadata = {
            'model_name': self.model_name,
            'dimension': self.dimension,
            'num_documents': len(self.documents)
        }
        with open(metadata_file, 'wb') as f:
            pickle.dump(metadata, f)
        
        print(f"Index saved to {save_path}")
    
    def load(self, path: Optional[Path] = None):
        """Load index and documents from disk"""
        load_path = path or self.index_path
        if load_path is None:
            raise ValueError("No load path specified")
        
        load_path = Path(load_path)
        
        # Load FAISS index
        index_file = load_path / "faiss.index"
        
        if ML_AVAILABLE:
            if not index_file.exists():
                raise FileNotFoundError(f"Index file not found: {index_file}")
            self.index = faiss.read_index(str(index_file))
        
        # Load documents
        docs_file = load_path / "documents.pkl"
        with open(docs_file, 'rb') as f:
            self.documents = pickle.load(f)
        
        # Load metadata
        metadata_file = load_path / "metadata.pkl"
        with open(metadata_file, 'rb') as f:
            metadata = pickle.load(f)
        
        print(f"Index loaded from {load_path}")
        print(f"Loaded {len(self.documents)} documents")
        
        return metadata
    
    def clear(self):
        """Clear all documents and reset index"""
        self.documents = []
        if ML_AVAILABLE:
            self.index = faiss.IndexFlatL2(self.dimension)
        print("Index cleared")
    
    def get_stats(self) -> dict:
        """Get statistics about the vector store"""
        return {
            'total_documents': len(self.documents),
            'model': self.model_name,
            'dimension': self.dimension,
            'index_size': self.index.ntotal
        }
