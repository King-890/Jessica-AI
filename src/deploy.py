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
    
    # Load Trained Weights if available
    if Path(MODEL_PATH).exists():
        print(f"📦 Loading trained model from {MODEL_PATH}...")
        try:
            state_dict = torch.load(MODEL_PATH, map_location=brain.device)
            brain.local_model.load_state_dict(state_dict)
            print("✅ Model loaded successfully.")
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
    else:
        print("⚠️  No custom model found. Using initialized random weights.")

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
    uvicorn.run(app, host=HOST, port=PORT)
