import sys
import os
import time

# Force UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.backend.cloud.supabase_client import get_client

def test_trigger():
    print("Testing Direct Cloud Insert (Bypassing ML components)...")
    
    client = get_client()
    if not client:
        print("❌ Supabase Client failed to initialize.")
        return

    print("✅ Supabase Client Connected.")
    
    # Insert a record WITHOUT embedding (to test trigger logic)
    # The 'on_memory_added' trigger works on AFTER INSERT
    
    record = {
        "content": "Diagnostics Test: Light Probe",
        "metadata": {
            "source": "trigger_test_script",
            "topic": "db_diagnostics",
            "timestamp": time.time()
        }
    }
    
    print("Attempting Insert into 'documents'...")
    try:
        resp = client.table("documents").insert(record).execute()
        print(f"✅ INSERT SUCCESS: {resp.data}")
        print("Now sleeping 2s to allow trigger to fire...")
        time.sleep(2)
        
        # Check logs
        lid = resp.data[0]['id']
        print(f"Checking 'learning_logs' for document_id={lid}...")
        
        logs = client.table("learning_logs").select("*").eq("document_id", lid).execute()
        if logs.data:
            print("🎉 TRIGGER VERIFIED! Found log entry:")
            print(logs.data[0])
        else:
            print("⚠️ Insert worked, but NO LOG found. Trigger failed?")
            
    except Exception as e:
        print(f"❌ COMMAND FAILED: {e}")

if __name__ == "__main__":
    test_trigger()
