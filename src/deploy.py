import sys
import os
import yaml
import torch
import uvicorn
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.brain import Brain
from src.core.mcp_host import MCPHost

# --- Configuration ---
HOST = "0.0.0.0"
PORT = 8080 # Lightning Studio usually exposes 8080 or random ports via proxy
MODEL_PATH = "jessica_model_cloud.pt"

# --- API Models ---
class ChatRequest(BaseModel):
    message: str
    user_id: str = "default_user"

class ChatResponse(BaseModel):
    response: str
    status: str = "success"

# --- Globals ---
app = FastAPI(title="Jessica AI Cloud API", version="1.0")
brain = None

def load_config():
    config_path = Path("config.yaml")
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {}

@app.on_event("startup")
async def startup_event():
    global brain
    print("🚀 Starting Jessica AI Cloud API...")
    
    config = load_config()
    
    # Initialize Brain (Inference Mode)
    # RAG could be enabled if vector store is populated, but optional for now
    brain = Brain(config, mcp_host=None, rag_manager=None)
    
    # Debug: List context to help user find the file
    print(f"📂 Current Directory: {os.getcwd()}")
    print(f"📂 Files available: {[f for f in os.listdir('.') if f.endswith('.pt')]}")

    # Load Trained Weights if available
    potential_models = [MODEL_PATH, "jessica_model.pt", "checkpoints/last.ckpt"]
    model_loaded = False
    
    for path in potential_models:
        if Path(path).exists():
            print(f"📦 Loading trained model from {path}...")
            try:
                state_dict = torch.load(path, map_location=brain.device)
                # Handle Lightning checkpoint format vs raw state dict
                if 'state_dict' in state_dict:
                    # Strip 'model.' prefix if using Lightning Checkpoints
                    state_dict = {k.replace('model.', ''): v for k, v in state_dict['state_dict'].items()}
                
                brain.local_model.load_state_dict(state_dict)
                print(f"✅ Model loaded successfully from {path}.")
                model_loaded = True
                break
            except Exception as e:
                print(f"❌ Failed to load model {path}: {e}")
    
    if not model_loaded:
        print("⚠️  No custom model found (checked cloud/local/checkpoints). Using initialized random weights.")

@app.get("/health")
async def health_check():
    return {"status": "online", "model_loaded": Path(MODEL_PATH).exists()}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not brain:
        raise HTTPException(status_code=503, detail="Brain not initialized")
    
    print(f"📩 Received: {request.message}")
    
    # Use brain to generate response (Direct generation for now)
    # We bypass the full process_input for raw API speed unless needed
    try:
        # Check for simple heuristic tools first?
        # For Cloud API, we might want to be safer and just do text gen
        # But let's use the standard flow to be consistent
        response_text = await brain.process_input(
            request.message, 
            update_callback=None, 
            confirmation_callback=lambda action, params: False # Auto-deny tools in cloud for safety
        )
        return ChatResponse(response=response_text)
    except Exception as e:
        print(f"❌ Error generating response: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    try:
        uvicorn.run(app, host=HOST, port=PORT)
    except OSError as e:
        if "Address already in use" in str(e) or "[Errno 98]" in str(e):
             print(f"\n❌ ERROR: Port {PORT} is occupied!")
             print(f"👉 Run this command to kill the blocker:  fuser -k {PORT}/tcp")
        raise e
