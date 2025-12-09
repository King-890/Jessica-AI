
import os
from pathlib import Path
from src.backend.cloud.supabase_client import get_client, download_file

def sync_data():
    """Download all training data from Supabase Dataset bucket."""
    print("Syncing training data from Cloud...")
    cli = get_client()
    if not cli:
        print("Error: No client.")
        return

    try:
        # List files in bucket
        files = cli.storage.from_("datasets").list("training_data")
        # Note: 'list' behavior depends on library version/folder structure 
        # may need recursive handling if deep folders. 
        # For now, assuming flat or 1-level deep in 'training_data'.
        
        target_dir = Path("training_data")
        target_dir.mkdir(exist_ok=True)
        
        for f in files:
            name = f.get("name")
            if not name: continue
            
            # Construct paths
            remote_path = f"training_data/{name}"
            local_path = target_dir / name
            
            print(f"Downloading {name}...")
            download_file("datasets", remote_path, str(local_path))
            
    except Exception as e:
        print(f"Sync Error: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    sync_data()
