from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from data import db
from core.plugins import plugin_manager
from core.plugin_loader import sync_plugins_to_db


class PluginCreateRequest(BaseModel):
    id: str
    name: str
    enabled: bool = True
    config_json: str | None = None


class PluginIdRequest(BaseModel):
    id: str
    enabled: bool | None = None
    config_json: str | None = None


router = APIRouter()


@router.post("/add")
def add_plugin(req: PluginCreateRequest):
    try:
        db.add_plugin(req.id, req.name, req.enabled, req.config_json)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    plugin_manager.reload()
    return {"id": req.id}


@router.get("/list")
def list_plugins():
    rows = db.list_plugins()
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "enabled": bool(r["enabled"]),
            "config_json": r["config_json"],
        }
        for r in rows
    ]


@router.post("/enable")
def enable_plugin(req: PluginIdRequest):
    if req.enabled is None:
        raise HTTPException(status_code=400, detail="enabled must be provided")
    db.set_plugin_enabled(req.id, bool(req.enabled))
    plugin_manager.reload()
    return {"id": req.id, "enabled": bool(req.enabled)}


@router.delete("/remove")
def remove_plugin(req: PluginIdRequest):
    db.remove_plugin(req.id)
    plugin_manager.reload()
    return {"id": req.id, "removed": True}


@router.post("/config")
def update_config(req: PluginIdRequest):
    if req.config_json is None:
        raise HTTPException(status_code=400, detail="config_json must be provided")
    db.update_plugin_config(req.id, req.config_json)
    plugin_manager.reload()
    return {"id": req.id, "updated": True}


@router.post("/scan")
def scan_filesystem_plugins():
    found = sync_plugins_to_db()
    plugin_manager.reload()
    return {"status": "ok", "count": len(found)}