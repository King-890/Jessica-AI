
import os
import sys
from dotenv import load_dotenv

# Load env from d:\Jessica AI\.env if not loaded
load_dotenv(r"d:\Jessica AI\.env")

print("Testing Supabase Connection...")
print(f"URL: {os.getenv('SUPABASE_URL')}")
key = os.getenv('SUPABASE_ANON_KEY')
print(f"Key: {key[:10]}..." if key else "Key: None")

try:
    from src.rag.vector_store import VectorStore
    from src.backend.cloud.supabase_client import get_client
    
    # 1. Test Client
    cli = get_client()
    if cli:
        print("[OK] Supabase Client initialized.")
    else:
        print("[FAIL] Supabase Client failed.")
        
    # 2. Test Vector Store Init
    print("\nInitializing VectorStore...")
    vs = VectorStore()
    if vs.use_supabase:
        print("[OK] VectorStore is using Supabase backend.")
    else:
        print(f"[WARN] VectorStore is using Backend: {vs.get_stats().get('backend', 'unknown')}")
        print("Note: This is expected if Supabase is not reachable or dependencies missing.")

except Exception as e:
    print(f"[ERROR] Verification failed: {e}")
    import traceback
    traceback.print_exc()
