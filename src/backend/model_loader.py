
import os
from pathlib import Path
from src.backend.cloud.supabase_client import download_file

def ensure_model(model_name: str, bucket: str = "models", force_download: bool = False) -> str:
    """
    Ensure a model file exists locally. If not, download from Supabase.
    Returns the absolute path to the model.
    """
    # Define local models directory
    # Assuming run from root or src
    root = Path(os.getcwd())
    if (root / "src").exists():
        # We are in root
        model_dir = root / "models"
    else:
        # We might be deeper, try to find root
        model_dir = Path("../models").resolve()
        
    model_dir.mkdir(parents=True, exist_ok=True)
    local_path = model_dir / model_name
    
    if local_path.exists() and not force_download:
        print(f"Model {model_name} found locally.")
        return str(local_path)
        
    print(f"Model {model_name} not found. Downloading from Supabase [{bucket}]...")
    
    # Try different paths in bucket (root or inside models folder)
    # The migration script puts root/models/foo.pt -> bucket/models/foo.pt
    # But files in root/foo.pt -> bucket/foo.pt 
    # We'll try strict text match first
    
    remote_path = model_name
    
    if download_file(bucket, remote_path, str(local_path)):
        print(f"Downloaded {model_name} successfully.")
        return str(local_path)
        
    # Try with 'models/' prefix if it failed
    remote_path_prefix = f"models/{model_name}"
    if download_file(bucket, remote_path_prefix, str(local_path)):
        print(f"Downloaded {model_name} successfully (with prefix).")
        return str(local_path)
        
    print(f"Failed to download {model_name}.")
    raise FileNotFoundError(f"Could not fetch model {model_name} from Supabase.")
