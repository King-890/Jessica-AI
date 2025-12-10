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
    if os.getenv("CI"):
        # Github Actions / CI environment
        # We explicitly disable ML components to prevent timeout/hangs during tests
        # unless explicitly requested via FORCE_ML
        if not os.getenv("FORCE_ML"):
            raise ImportError("CI Mode: Skipping ML dependencies")

    import faiss
    from sentence_transformers import SentenceTransformer
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("Warning: RAG dependencies (faiss, sentence-transformers) not found or CI mode active. RAG features disabled.")


from .document_processor import Document
# Import Supabase store if available
try:
    from .vector_store_supabase import SupabaseVectorStore
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


class VectorStore:
    """Hybrid vector store (FAISS or Supabase)"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", index_path: Optional[Path] = None):
        """
        Initialize vector store.
        Will use Supabase if SUPABASE_URL is set, otherwise FAISS.
        """
        self.model_name = model_name
        self.index_path = index_path
        self.backend = None
        self.use_supabase = False

        # Check for Supabase config
        if SUPABASE_AVAILABLE and os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY"):
            try:
                print("Initializing Supabase Vector Store...")
                self.backend = SupabaseVectorStore(model_name=model_name)
                self.use_supabase = True
                return
            except Exception as e:
                print(f"Failed to init Supabase store: {e}. Falling back to local.")

        # Fallback to Local FAISS
        self.documents: List[Document] = []
        if ML_AVAILABLE:
            try:
                self.model = SentenceTransformer(model_name)
                self.dimension = self.model.get_sentence_embedding_dimension()
                self.index = faiss.IndexFlatL2(self.dimension)
                print(f"Local Vector store initialized with model: {model_name}")
            except Exception as e:
                print(f"Failed to load SentenceTransformer model: {e}. Falling back to dummy mode.")
                self.model = None
                self.index = None
                self.dimension = 0
        else:
            self.model = None
            self.index = None
            self.dimension = 0
            print("Vector store initialized in dummy mode.")

    def add_documents(self, documents: List[Document]):
        if self.use_supabase and self.backend:
            return self.backend.add_documents(documents)

        # Local Logic
        if not ML_AVAILABLE or not documents:
            return

        print(f"Generating embeddings for {len(documents)} documents (Local)...")
        texts = [doc.content for doc in documents]
        embeddings = self.model.encode(texts, show_progress_bar=False)
        embeddings_array = np.array(embeddings).astype('float32')
        self.index.add(embeddings_array)
        self.documents.extend(documents)
        print(f"Added {len(documents)} documents to local index")

    def search(self, query: str, top_k: int = 5) -> List[Tuple[Document, float]]:
        if self.use_supabase and self.backend:
            return self.backend.search(query, top_k)

        # Local Logic
        if not ML_AVAILABLE or not self.documents:
            return []

        query_embedding = self.model.encode([query])[0].astype('float32')
        distances, indices = self.index.search(np.array([query_embedding]), min(top_k, len(self.documents)))

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.documents):
                similarity = 1.0 / (1.0 + dist)
                results.append((self.documents[idx], similarity))
        return results

    def save(self, path: Optional[Path] = None):
        if self.use_supabase:
            print("Supabase store does not need explicit save (interaction persistence is auto).")
            return

        # Local Logic
        save_path = path or self.index_path
        if not save_path:
            return
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        if ML_AVAILABLE:
            faiss.write_index(self.index, str(save_path / "faiss.index"))
        with open(save_path / "documents.pkl", 'wb') as f:
            pickle.dump(self.documents, f)

        print(f"Local index saved to {save_path}")

    def load(self, path: Optional[Path] = None):
        if self.use_supabase:
            print("Supabase store is stateless/remote. Nothing to load locally.")
            return {}

        # Local Logic
        load_path = path or self.index_path
        if not load_path:
            return {}
        load_path = Path(load_path)

        if ML_AVAILABLE:
            self.index = faiss.read_index(str(load_path / "faiss.index"))
        with open(load_path / "documents.pkl", 'rb') as f:
            self.documents = pickle.load(f)

        print(f"Local index loaded from {load_path}")
        return {}

    def clear(self):
        if self.use_supabase and self.backend:
            return self.backend.clear()

        self.documents = []
        if ML_AVAILABLE:
            self.index = faiss.IndexFlatL2(self.dimension)

    def get_stats(self) -> dict:
        if self.use_supabase and self.backend:
            return self.backend.get_stats()

        return {
            'total_documents': len(self.documents),
            'model': self.model_name,
            'backend': 'local_faiss'
        }
