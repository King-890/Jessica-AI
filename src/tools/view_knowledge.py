import sys
import os

# Force UTF-8 for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add project root to path to find src.backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from src.backend.cloud.supabase_client import get_client
except ImportError:
    # Fix import if running script directly
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
    from src.backend.cloud.supabase_client import get_client

def view_cloud_status():
    print("==================================================")
    print("   JESSICA AI - CLOUD DIAGNOSTICS")
    print("==================================================")

    client = get_client()
    if not client:
        print("❌ Error: Could not connect to Supabase (Check src/app_secrets.py)")
        return

    print("✅ Connected to Supabase!")
    
    # 1. Check Memories (Vector Store)
    print("\n[1] Checking 'documents' (Vector Memory)...")
    try:
        resp = client.table("documents").select("*").order("id", desc=True).limit(5).execute()
        rows = resp.data
        if rows:
            print(f"   Found {len(rows)} recent memories:")
            for r in rows:
                tid = r.get('id')
                source = r.get('metadata', {}).get('source', 'unknown')
                topic = r.get('metadata', {}).get('topic', 'unknown')
                ts = r.get('created_at', 'No Timestamp')
                print(f"   - ID: {tid} | {ts} | Source: {source} | Topic: {topic[:50]}...")
        else:
            print("   ⚠️ No memories found. (Autonomous training might still be starting)")
    except Exception as e:
        print(f"   ❌ Error checking documents: {e}")

    # 2. Check Triggers (Learning Logs)
    print("\n[2] Checking 'learning_logs' (Trigger Audit)...")
    try:
        resp = client.table("learning_logs").select("*").order("created_at", desc=True).limit(5).execute()
        rows = resp.data
        if rows:
            print(f"   Found {len(rows)} execution logs (PROVES TRIGGERS WORKING):")
            for r in rows:
                act = r.get('activity_type')
                ts = r.get('created_at')
                details = r.get('details')
                print(f"   - {ts} | Type: {act} | {str(details)[:80]}...")
        else:
            print("   ⚠️ No logs found. (Triggers might not be firing or table empty)")
    except Exception as e:
        print(f"   ❌ Error checking triggers: {e}")

    # 3. Check Storage Buckets (Raw Files)
    print("\n[3] Checking 'datasets' Bucket (Raw Files)...")
    try:
        res = client.storage.from_("datasets").list("auto_learning")
        if res:
            print(f"   Found {len(res)} files in 'auto_learning/':")
            for f in res[:5]:
                print(f"   - {f.get('name')} ({f.get('metadata', {}).get('size', 0)} bytes) | {f.get('created_at')}")
            if len(res) > 5: print("   - ... and more")
        else:
             print("   ⚠️ No files found in 'datasets/auto_learning'.")
    except Exception as e:
        print(f"   ❌ Error checking buckets: {e}")

    print("\n==================================================")
    print("DIAGNOSTIC COMPLETE")

if __name__ == "__main__":
    view_cloud_status()
