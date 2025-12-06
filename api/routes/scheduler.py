import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from data import db


class TaskCreateRequest(BaseModel):
    name: str
    command: str
    args: list[str] = []
    interval_seconds: int
    enabled: bool = True


class TaskCreateAdvanced(BaseModel):
    name: str
    command: str
    args: list[str] = []
    schedule_type: str = "interval"  # interval | cron | iso
    interval_seconds: int | None = None
    cron_expr: str | None = None
    iso_time: str | None = None
    enabled: bool = True


class TaskIdRequest(BaseModel):
    id: int
    enabled: bool | None = None


router = APIRouter()


@router.post("/add")
def add_task(req: TaskCreateRequest):
    if req.interval_seconds <= 0:
        raise HTTPException(status_code=400, detail="interval_seconds must be > 0")
    args_json = json.dumps(req.args)
    task_id = db.add_task(req.name, req.command, args_json, req.interval_seconds, req.enabled)
    return {"id": task_id}


@router.get("/list")
def list_tasks():
    rows = db.list_tasks()
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "command": r["command"],
            "args": json.loads(r["args_json"]) if r["args_json"] else [],
            "interval_seconds": r["interval_seconds"],
            "enabled": bool(r["enabled"]),
            "last_run": r["last_run"],
            "schedule_type": r["schedule_type"],
            "cron_expr": r["cron_expr"],
            "iso_time": r["iso_time"],
        }
        for r in rows
    ]


@router.post("/enable")
def enable_task(req: TaskIdRequest):
    if req.enabled is None:
        raise HTTPException(status_code=400, detail="enabled must be provided")
    db.set_task_enabled(req.id, bool(req.enabled))
    return {"id": req.id, "enabled": bool(req.enabled)}


@router.delete("/delete")
def delete_task(req: TaskIdRequest):
    db.delete_task(req.id)
    return {"id": req.id, "deleted": True}


@router.post("/run_now")
def run_now(req: TaskIdRequest):
    # Directly execute the task once without changing schedule
    rows = [r for r in db.list_tasks() if r["id"] == req.id]
    if not rows:
        raise HTTPException(status_code=404, detail="Task not found")
    r = rows[0]
    try:
        import os, subprocess, json as _json
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        command = r["command"].lower()
        args = _json.loads(r["args_json"]) if r["args_json"] else []
        if command == "python":
            if not args:
                raise HTTPException(status_code=400, detail="No script path")
            target = os.path.abspath(os.path.join(base_dir, args[0]))
            if os.path.commonpath([target, base_dir]) != base_dir:
                raise HTTPException(status_code=403, detail="Forbidden script path")
            if not os.path.isfile(target):
                raise HTTPException(status_code=404, detail="Script not found")
            full = ["python", target] + args[1:]
            res = subprocess.run(full, capture_output=True, text=True, timeout=20, shell=False)
        elif command in {"echo", "dir"}:
            full = [command] + args
            res = subprocess.run(full, capture_output=True, text=True, timeout=10, shell=True)
        else:
            raise HTTPException(status_code=400, detail="Unsupported command")
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Command timed out")
    return {"returncode": res.returncode, "stdout": res.stdout, "stderr": res.stderr}


@router.post("/add_advanced")
def add_task_advanced(req: TaskCreateAdvanced):
    # Validate schedule
    st = req.schedule_type
    if st == "interval":
        if not req.interval_seconds or req.interval_seconds <= 0:
            raise HTTPException(status_code=400, detail="interval_seconds must be > 0")
    elif st == "cron":
        if not req.cron_expr:
            raise HTTPException(status_code=400, detail="cron_expr required")
    elif st == "iso":
        if not req.iso_time:
            raise HTTPException(status_code=400, detail="iso_time required")
    else:
        raise HTTPException(status_code=400, detail="Invalid schedule_type")

    args_json = json.dumps(req.args)
    task_id = db.add_task_advanced(
        req.name,
        req.command,
        args_json,
        req.schedule_type,
        req.interval_seconds,
        req.cron_expr,
        req.iso_time,
        req.enabled,
    )
    return {"id": task_id}


@router.get("/results")
def results(id: int, limit: int = 20):
    rows = db.get_task_results(id, limit)
    return [
        {
            "id": r["id"],
            "returncode": r["returncode"],
            "stdout": r["stdout"],
            "stderr": r["stderr"],
            "ts": r["ts"],
        }
        for r in rows
    ]