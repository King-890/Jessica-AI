from fastapi import APIRouter, Request, Depends
from .routes.auth import require_role


router = APIRouter(prefix="/config", tags=["config"])


@router.get("/")
async def get_config(request: Request):
    app = request.app
    return {
        "auto_update": bool(getattr(app.state, "auto_update_enabled", False)),
        "enable_voice_mode": bool(getattr(app.state, "voice_mode_enabled", False)),
        "cron_update_enabled": bool(getattr(app.state, "cron_update_enabled", False)),
        "cron_update_expression": getattr(app.state, "cron_update_expression", ""),
    }


@router.post("/")
async def set_config(request: Request, payload: dict):
    app = request.app
    # Auto update
    if "auto_update" in payload:
        val = bool(payload.get("auto_update"))
        app.state.auto_update_enabled = val
        # manage updater task if exists
        try:
            if not val and getattr(app.state, "updater_task", None):
                app.state.updater_task.cancel()
                app.state.updater_task = None
        except Exception:
            pass
    # Voice mode
    if "enable_voice_mode" in payload:
        app.state.voice_mode_enabled = bool(payload.get("enable_voice_mode"))
    # Cron
    if "cron_update_enabled" in payload:
        app.state.cron_update_enabled = bool(payload.get("cron_update_enabled"))
    if "cron_update_expression" in payload:
        app.state.cron_update_expression = str(payload.get("cron_update_expression"))
    return await get_config(request)


@router.post("/reload")
async def reload_config(request: Request, _ok: bool = Depends(require_role("admin"))):
    """Reload configuration and return current values. Admin-only."""
    # In this phase, reloading is lightweight: we simply re-evaluate runtime flags
    # and return the current snapshot. More advanced reload hooks can be added later.
    return await get_config(request)