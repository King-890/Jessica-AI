import sys
import os

# Force UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.rag.vector_store import VectorStore
from src.rag.document_processor import Document
import datetime

def test_insert():
    print("Testing One-Off Cloud Insert...")
    
    try:
        store = VectorStore(model_name="all-MiniLM-L6-v2")
        
        # Check backend
        if not store.use_supabase:
            print("❌ Store initialized in LOCAL mode. Credentials still failing?")
            return

        print("✅ Store initialized in CLOUD mode.")
        
        doc = Document(
            content=f"Test Memory {datetime.datetime.now()}",
            metadata={
                "source": "manual_test",
                "topic": "system_diagnostic",
                "timestamp": datetime.datetime.now().isoformat()
            }
        )
        
        print("Attempting Insert...")
        store.add_documents([doc])
        print("✅ INSERT SUCCESSFUL! (If triggers work, check learning_logs)")

    except Exception as e:
        print(f"❌ INSERT FAILED: {e}")

if __name__ == "__main__":
    test_insert()
