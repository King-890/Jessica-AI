
import os
import glob
from pathlib import Path
from src.backend.cloud.supabase_client import upload_file, get_client

# Define paths to migrate
PATHS_TO_MIGRATE = [
    # Models
    {"pattern": "models/**/*", "bucket": "models"},
    # Data
    {"pattern": "data/**/*", "bucket": "datasets"},
    # Training Data
    {"pattern": "training_data/**/*", "bucket": "datasets"},
    # Large specific files
    {"pattern": "*.pt", "bucket": "models"},
    {"pattern": "*.jsonl", "bucket": "datasets"},
]

def migrate():
    print("Starting Cloud Migration...")
    cli = get_client()
    if not cli:
        print("[ERROR] Could not connect to Supabase. Check .env")
        return

    total_files = 0
    success_count = 0

    for item in PATHS_TO_MIGRATE:
        pattern = item["pattern"]
        bucket = item["bucket"]
        
        # Ensure bucket exists (this is a best effort, requires permissions)
        try:
            buckets = cli.storage.list_buckets()
            bucket_names = [b.name for b in buckets]
            if bucket not in bucket_names:
                print(f"Creating bucket '{bucket}'...")
                cli.storage.create_bucket(bucket, options={"public": False})
        except Exception as e:
            print(f"Warning checking/creating bucket '{bucket}': {e}")

        # Find files
        # glob needs to handle recursive search properly
        files = glob.glob(pattern, recursive=True)
        for file_path in files:
            if os.path.isdir(file_path):
                continue
                
            # Skip small files if needed, or specific extensions
            # Check file size (e.g. skip empty files)
            if os.path.getsize(file_path) == 0:
                continue

            rel_path = os.path.relpath(file_path, os.getcwd())
            # Normalize path for storage (forward slashes)
            storage_path = rel_path.replace("\\", "/")
            
            print(f"Uploading {storage_path} to [{bucket}]...")
            if upload_file(bucket, storage_path, file_path):
                print(f" [OK] {file_path}")
                success_count += 1
            else:
                print(f" [FAIL] {file_path}")
            
            total_files += 1

    print(f"\nMigration Complete. {success_count}/{total_files} files uploaded.")

if __name__ == "__main__":
    # Load env manually if not set
    from dotenv import load_dotenv
    load_dotenv()
    migrate()
