import sys
import os
sys.path.append(os.getcwd())

try:
    print("Attempting to import src.backend.app...")
    from src.backend.app import app
    print("Success!")
except Exception as e:
    print(f"Failed: {e}")
    import traceback
    traceback.print_exc()
