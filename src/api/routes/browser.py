import uuid
from typing import Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


class TabCreateRequest(BaseModel):
    query: str | None = None


class TabUpdateRequest(BaseModel):
    tab_id: str
    query: str


router = APIRouter()
_tabs: Dict[str, dict] = {}


@router.post("/tab/create")
def create_tab(req: TabCreateRequest):
    tid = uuid.uuid4().hex
    _tabs[tid] = {"query": req.query or ""}
    return {"tab_id": tid, "query": _tabs[tid]["query"]}


@router.post("/tab/update")
def update_tab(req: TabUpdateRequest):
    if req.tab_id not in _tabs:
        raise HTTPException(status_code=404, detail="Tab not found")
    _tabs[req.tab_id]["query"] = req.query
    return {"tab_id": req.tab_id, "query": req.query}


@router.get("/tab/get")
def get_tab(tab_id: str):
    if tab_id not in _tabs:
        raise HTTPException(status_code=404, detail="Tab not found")
    return {"tab_id": tab_id, "query": _tabs[tab_id]["query"]}


@router.delete("/tab/delete")
def delete_tab(tab_id: str):
    _tabs.pop(tab_id, None)
    return {"tab_id": tab_id, "deleted": True}