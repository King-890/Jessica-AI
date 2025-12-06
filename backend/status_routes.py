import time
from fastapi import APIRouter, Request
from .cloud.supabase_client import get_client

router = APIRouter(prefix="/status", tags=["status"])


@router.get("/")
async def get_status(request: Request):
    app = request.app
    start = getattr(app.state, "start_time", None)
    uptime = None
    try:
        if start:
            uptime = time.time() - float(start)
    except Exception:
        uptime = None
    # If supabase client can be created, consider db connected
    db_connected = False
    try:
        db_connected = bool(get_client())
    except Exception:
        db_connected = False
    return {
        "api_online": True,
        "db_connected": db_connected,
        "uptime": uptime,
    }