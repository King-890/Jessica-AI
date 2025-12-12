
import os
from typing import List, Tuple

try:
    from supabase import create_client, Client
    from sentence_transformers import SentenceTransformer
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    Client = object  # Dummy for typing
    print("Warning: Supabase or ML dependencies not found. Cloud vector store disabled.")

from .document_processor import Document


class SupabaseVectorStore:
    """Supabase-based vector store using pgvector"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", table_name: str = "documents"):
        """
        Initialize Supabase vector store
        """
        self.model_name = model_name
        self.table_name = table_name
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

        if not self.url or not self.key:
            try:
                from src.app_secrets import SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_ANON_KEY
                self.url = self.url or SUPABASE_URL
                self.key = self.key or SUPABASE_SERVICE_KEY or SUPABASE_ANON_KEY
            except ImportError:
                pass

        if not ML_AVAILABLE:
            print("Supabase/ML libs missing.")
            self.model = None
            self.client = None
            return

        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment")

        self.client: Client = create_client(self.url, self.key)

        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        print(f"Supabase Vector Store initialized. Model: {model_name}, Dim: {self.dimension}")

    def add_documents(self, documents: List[Document]):
        """Add documents to Supabase"""
        if not ML_AVAILABLE or not self.model:
            return

        if not documents:
            return

        print(f"Generating embeddings for {len(documents)} documents...")

        texts = [doc.content for doc in documents]
        embeddings = self.model.encode(texts, show_progress_bar=False)

        records = []
        for i, doc in enumerate(documents):
            records.append({
                "content": doc.content.replace('\x00', ''),  # Sanitize Null Bytes for Postgres
                "metadata": doc.metadata,
                "embedding": embeddings[i].tolist()
            })

        # Batch insert
        try:
            self.client.table(self.table_name).insert(records).execute()
            print(f"Successfully added {len(records)} documents to Supabase.")
        except Exception as e:
            print(f"Error adding documents to Supabase: {e}")
            raise e

    def search(self, query: str, top_k: int = 5) -> List[Tuple[Document, float]]:
        """Search for similar documents using valid RPC call"""
        if not ML_AVAILABLE or not self.model:
            return []

        # Generate query embedding
        query_embedding = self.model.encode([query])[0].tolist()

        try:
            # RPC call to match_documents (defined in setup.sql)
            params = {
                "query_embedding": query_embedding,
                "match_threshold": 0.0,  # Return all distinct
                "match_count": top_k
            }
            response = self.client.rpc("match_documents", params).execute()

            results = []
            if response.data:
                for match in response.data:
                    doc = Document(
                        content=match["content"],
                        metadata=match["metadata"]
                    )
                    similarity = match["similarity"]
                    results.append((doc, similarity))

            return results

        except Exception as e:
            print(f"Error searching Supabase: {e}")
            return []

    def clear(self):
        """Clear all documents from the table"""
        try:
            # This requires SERVICE_ROLE key or relaxed RLS.
            # DELETE * (filter by match all)
            self.client.table(self.table_name).delete().neq("id", 0).execute()
            print("Supabase table cleared (attempted).")
        except Exception as e:
            print(f"Error clearing Supabase table: {e}")

    def get_stats(self) -> dict:
        """Get basics stats"""
        try:
            count = self.client.table(self.table_name).select("id", count="exact").execute().count
            return {
                "total_documents": count,
                "model": self.model_name,
                "backend": "supabase"
            }
        except Exception:
            return {"status": "unknown"}
