from fastapi import APIRouter
from typing import List, Dict, Any
from .cloud.supabase_client import get_client
from .knowledge_fetcher import perform_update

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/learn")
async def learn_now(queries: List[str] | None = None) -> Dict[str, Any]:
    """Trigger a knowledge update and push summaries to Supabase 'knowledge'."""
    try:
        await perform_update(queries)
    except Exception:
        pass
    # Attempt to push a simple marker to Supabase for visibility
    cli = get_client()
    try:
        if cli:
            cli.table("knowledge").insert({
                "topic": "manual_update",
                "summary": "Manual knowledge update triggered",
                "source": "local",
            }).execute()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/list")
async def list_knowledge(limit: int = 20) -> Dict[str, Any]:
    cli = get_client()
    if not cli:
        return {"items": []}
    try:
        resp = cli.table("knowledge").select("*").order("date", desc=True).limit(limit).execute()
        return {"items": list(resp.data or [])}
    except Exception:
        return {"items": []}