from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .vector_memory import store_interaction, search


router = APIRouter(prefix="/memory", tags=["memory"])


class StoreRequest(BaseModel):
    prompt: str
    response: str
    tags: Optional[List[str]] = None


@router.post("/store")
async def store(req: StoreRequest):
    try:
        return store_interaction(req.prompt, req.response, req.tags)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def memory_search(q: str = Query(min_length=1), k: int = Query(default=5, ge=1, le=20)):
    try:
        items = search(q, k)
        return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))