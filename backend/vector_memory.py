import os
import time
from typing import List, Dict, Any

try:
    import chromadb
    from chromadb.utils import embedding_functions
except Exception:  # pragma: no cover
    chromadb = None
    embedding_functions = None


_client = None
_collection = None
_last_update_ts = 0.0


def _get_client():
    global _client
    if _client is None:
        if chromadb is None:
            raise RuntimeError("chromadb is not installed. Please add 'chromadb' to requirements.")
        persist_dir = os.path.join("data", "vector_memory")
        os.makedirs(persist_dir, exist_ok=True)
        _client = chromadb.PersistentClient(path=persist_dir)
    return _client


def _get_collection():
    global _collection
    if _collection is None:
        client = _get_client()
        # Use SentenceTransformers by default
        if embedding_functions is None:
            raise RuntimeError("sentence-transformers embedding_functions not available.")
        model_name = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_name)
        try:
            _collection = client.get_or_create_collection(name="jessica_memory", embedding_function=ef)
        except Exception:
            # Fallback: create without embedding function then set
            _collection = client.get_or_create_collection(name="jessica_memory")
    return _collection


def store_interaction(prompt: str, response: str, tags: List[str] | None = None) -> Dict[str, Any]:
    """Store prompt/response as two documents with shared interaction_id metadata."""
    coll = _get_collection()
    interaction_id = str(int(time.time() * 1000))
    metadata_base = {"interaction_id": interaction_id, "ts": time.time()}
    if tags:
        metadata_base["tags"] = tags
    docs = [
        {"id": interaction_id + ":prompt", "doc": prompt or "", "meta": {**metadata_base, "type": "prompt"}},
        {"id": interaction_id + ":response", "doc": response or "", "meta": {**metadata_base, "type": "response"}},
    ]
    coll.add(ids=[d["id"] for d in docs], documents=[d["doc"] for d in docs], metadatas=[d["meta"] for d in docs])
    global _last_update_ts
    _last_update_ts = time.time()
    return {"stored": True, "interaction_id": interaction_id}


def search(q: str, k: int = 5) -> List[Dict[str, Any]]:
    coll = _get_collection()
    res = coll.query(query_texts=[q], n_results=k)
    items: List[Dict[str, Any]] = []
    ids = (res.get("ids") or [[]])[0]
    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]
    for i in range(len(ids)):
        items.append({
            "id": ids[i],
            "content": docs[i],
            "metadata": metas[i],
            "score": dists[i],
        })
    return items


def count() -> int:
    try:
        coll = _get_collection()
        return coll.count()
    except Exception:
        return 0


def last_update_time() -> float:
    return _last_update_ts