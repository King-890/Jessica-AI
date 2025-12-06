import subprocess
from pathlib import Path
from fastapi import APIRouter, Depends

from .routes.auth import require_role
from .updater import update_jessica


router = APIRouter(prefix="/updates", tags=["updates"])
ROOT = Path(__file__).resolve().parents[1]


@router.get("/check")
async def check_updates():
    try:
        subprocess.run(["git", "fetch"], cwd=ROOT.as_posix(), capture_output=True, text=True)
        status = subprocess.run(["git", "status", "-uno"], cwd=ROOT.as_posix(), capture_output=True, text=True)
        out = (status.stdout or "") + ("\n" + status.stderr if status.stderr else "")
        behind = "behind" in out.lower()
        ahead = "ahead" in out.lower()
        return {"status": "ok", "raw": out.strip(), "behind": behind, "ahead": ahead}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/apply")
async def apply_updates(_=Depends(require_role("admin"))):
    ok, output = update_jessica()
    return {"success": ok, "output": output}