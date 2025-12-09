from fastapi import APIRouter, Request, Depends
from .routes.auth import require_role


router = APIRouter(prefix="/config", tags=["config"])


@router.get("/")
async def get_config(request: Request):
    app = request.app
    app = request.app
    # Try fetch from Supabase first
    from ..cloud.supabase_client import get_client
    cli = get_client()
    
    # Defaults
    auto_update = False
    voice_mode = False
    cron_enabled = False
    cron_expr = ""

    if cli:
        try:
            resp = cli.table("settings").select("*").execute()
            data = {row['key']: row['value'] for row in resp.data} if resp.data else {}
            
            auto_update = bool(data.get("auto_update", False))
            voice_mode = bool(data.get("enable_voice_mode", False))
            cron_enabled = bool(data.get("cron_update_enabled", False))
            cron_expr = str(data.get("cron_update_expression", ""))
            
            # Update app state to match cloud
            app.state.auto_update_enabled = auto_update
            app.state.voice_mode_enabled = voice_mode
            app.state.cron_update_enabled = cron_enabled
            app.state.cron_update_expression = cron_expr
        except Exception:
            pass

    # Fallback to current memory state if cloud failed or empty (or mixed)
    return {
        "auto_update": bool(getattr(app.state, "auto_update_enabled", auto_update)),
        "enable_voice_mode": bool(getattr(app.state, "voice_mode_enabled", voice_mode)),
        "cron_update_enabled": bool(getattr(app.state, "cron_update_enabled", cron_enabled)),
        "cron_update_expression": getattr(app.state, "cron_update_expression", cron_expr),
    }


@router.post("/")
async def set_config(request: Request, payload: dict):
    app = request.app
    # Sync with Supabase 'settings' table
    # Schema: key (text, pk), value (jsonb)
    from ..cloud.supabase_client import get_client
    cli = get_client()
    
    # 1. Update In-Memory State & Prepare Upsert
    updates = {}
    if "auto_update" in payload:
        val = bool(payload.get("auto_update"))
        app.state.auto_update_enabled = val
        updates["auto_update"] = val
        # manage updater task if exists
        try:
            if not val and getattr(app.state, "updater_task", None):
                app.state.updater_task.cancel()
                app.state.updater_task = None
        except Exception:
            pass
            
    if "enable_voice_mode" in payload:
        val = bool(payload.get("enable_voice_mode"))
        app.state.voice_mode_enabled = val
        updates["enable_voice_mode"] = val

    if "cron_update_enabled" in payload:
        val = bool(payload.get("cron_update_enabled"))
        app.state.cron_update_enabled = val
        updates["cron_update_enabled"] = val

    if "cron_update_expression" in payload:
        val = str(payload.get("cron_update_expression"))
        app.state.cron_update_expression = val
        updates["cron_update_expression"] = val

    # 2. Push to Supabase
    if cli and updates:
        try:
            # Upsert each key-value pair
            # Assuming table 'settings' has columns: key, value
            for k, v in updates.items():
                cli.table("settings").upsert({"key": k, "value": v}).execute()
        except Exception as e:
            print(f"Config Sync Error: {e}")

    return await get_config(request)


@router.post("/reload")
async def reload_config(request: Request, _ok: bool = Depends(require_role("admin"))):
    """Reload configuration and return current values. Admin-only."""
    # In this phase, reloading is lightweight: we simply re-evaluate runtime flags
    # and return the current snapshot. More advanced reload hooks can be added later.
    return await get_config(request)