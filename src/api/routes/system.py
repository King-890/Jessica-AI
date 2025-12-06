import os
import subprocess
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


ALLOWED_COMMANDS = {
    "echo",
    "dir",
    # Add safe commands as needed
    "python",
}


class CommandRequest(BaseModel):
    command: str
    args: list[str] = []


router = APIRouter()


@router.post("/run")
def run_command(req: CommandRequest):
    cmd = req.command.lower()
    if cmd not in ALLOWED_COMMANDS:
        raise HTTPException(status_code=400, detail="Command not allowed")
    # Special handling for python: only run scripts within project base
    if cmd == "python":
        if not req.args:
            raise HTTPException(status_code=400, detail="Missing python script path")
        script_path = req.args[0]
        # Compute BASE_DIR from api/routes directory
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        target = os.path.abspath(os.path.join(base_dir, script_path))
        if os.path.commonpath([target, base_dir]) != base_dir:
            raise HTTPException(status_code=403, detail="Forbidden script path")
        if not os.path.isfile(target):
            raise HTTPException(status_code=404, detail="Script not found")
        full = ["python", target] + req.args[1:]
        shell_flag = False
    else:
        full = [cmd] + req.args
        shell_flag = True
    try:
        result = subprocess.run(full, capture_output=True, text=True, timeout=15, shell=shell_flag)
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Command timed out")
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }