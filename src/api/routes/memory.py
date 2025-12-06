from fastapi import APIRouter
from memory.store import MemoryStore


router = APIRouter()
memory = MemoryStore()


@router.get("/commands")
def recent_commands(limit: int = 10):
    return {"commands": memory.recent_commands(limit)}


@router.get("/history")
def recent_history(limit: int = 20):
    return {"history": memory.recent_history(limit)}


@router.get("/patterns")
def top_patterns(limit: int = 10):
    return {"patterns": memory.top_patterns(limit)}