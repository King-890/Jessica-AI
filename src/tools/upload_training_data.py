import os
import glob
from pathlib import Path
from src.backend.cloud.supabase_client import upload_file, get_client

def upload_training_sessions():
    print("🚀 Starting Training Data Upload to Supabase...")
    
    # 0. Check Client
    client = get_client()
    if not client:
        print("❌ Supabase client not configured. Check env vars.")
        return

    # 1. Find Files
    root_dir = Path("d:/Jessica AI/training_data")
    if not root_dir.exists():
        print(f"❌ Training directory not found: {root_dir}")
        return

    files = list(root_dir.glob("*.jsonl"))
    print(f"📂 Found {len(files)} session files.")

    # 2. Upload
    success_count = 0
    for file_path in files:
        filename = file_path.name
        print(f"   ⬆️ Uploading {filename}...")
        
        # Determine bucket path (e.g. sessions/filename)
        bucket_path = f"sessions/{filename}"
        
        if upload_file("training-data", bucket_path, str(file_path)):
            print(f"      ✅ Success")
            success_count += 1
        else:
            print(f"      ❌ Failed (Bucket 'training-data' might not exist or perm issue)")

    print(f"\n🎉 Upload Complete. {success_count}/{len(files)} files uploaded.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    upload_training_sessions()
