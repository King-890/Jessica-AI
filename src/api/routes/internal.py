from fastapi import APIRouter

from src.api.schemas import ProcessRequest, ProcessResponse
from core.llm_engine import LLMEngine
from memory.store import MemoryStore
from core.plugins import plugin_manager
from src.audio.livekit_client import LiveKitClient


router = APIRouter()
engine = LLMEngine()
memory = MemoryStore()
lk = LiveKitClient()


@router.get("/health")
def health():
    return {"status": "ok", "livekit_configured": lk.is_configured()}


@router.post("/process", response_model=ProcessResponse)
def process(req: ProcessRequest):
    # Log and capture conversation
    memory.log_command(req.text)
    # Apply pre-processors
    processed_text = plugin_manager.apply_pre(req.text)
    memory.add_message("user", processed_text)

    history = memory.recent_history(limit=20)
    output = engine.generate_with_context(processed_text, history)
    # Apply post-processors
    output = plugin_manager.apply_post(output)

    memory.add_message("assistant", output)
    return {"output": output}