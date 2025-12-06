import os
import uuid
import subprocess
from typing import Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class SessionCreateRequest(BaseModel):
    base_path: str = ""


class SessionRunRequest(BaseModel):
    session_id: str
    command: str
    args: list[str] = []


router = APIRouter()
_sessions: Dict[str, str] = {}


def _safe_join(*paths: str) -> str:
    target = os.path.abspath(os.path.join(*paths))
    base = os.path.abspath(BASE_DIR)
    if os.path.commonpath([target, base]) != base:
        raise HTTPException(status_code=403, detail="Forbidden path")
    return target


@router.post("/session/create")
def create_session(req: SessionCreateRequest):
    cwd = _safe_join(BASE_DIR, req.base_path)
    if not os.path.isdir(cwd):
        raise HTTPException(status_code=404, detail="Base path is not a directory")
    sid = uuid.uuid4().hex
    _sessions[sid] = cwd
    return {"session_id": sid, "cwd": os.path.relpath(cwd, BASE_DIR)}


@router.post("/session/run")
def run_in_session(req: SessionRunRequest):
    if req.session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    cwd = _sessions[req.session_id]
    cmd = req.command.lower()
    args = req.args

    try:
        if cmd == "cd":
            if not args:
                raise HTTPException(status_code=400, detail="Missing path for cd")
            new_cwd = _safe_join(cwd, args[0])
            if not os.path.isdir(new_cwd):
                raise HTTPException(status_code=404, detail="Directory not found")
            _sessions[req.session_id] = new_cwd
            return {"session_id": req.session_id, "cwd": os.path.relpath(new_cwd, BASE_DIR)}
        elif cmd == "python":
            if not args:
                raise HTTPException(status_code=400, detail="Missing script path")
            script_path = _safe_join(cwd, args[0])
            if not os.path.isfile(script_path):
                raise HTTPException(status_code=404, detail="Script not found")
            full = ["python", script_path] + args[1:]
            res = subprocess.run(full, capture_output=True, text=True, timeout=20, shell=False, cwd=cwd)
        elif cmd in {"echo", "dir"}:
            full = [cmd] + args
            res = subprocess.run(full, capture_output=True, text=True, timeout=10, shell=True, cwd=cwd)
        else:
            raise HTTPException(status_code=400, detail="Command not allowed")
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Command timed out")

    return {
        "session_id": req.session_id,
        "cwd": os.path.relpath(_sessions[req.session_id], BASE_DIR),
        "returncode": res.returncode,
        "stdout": res.stdout,
        "stderr": res.stderr,
    }


@router.delete("/session/delete")
def delete_session(session_id: str):
    _sessions.pop(session_id, None)
    return {"session_id": session_id, "deleted": True}