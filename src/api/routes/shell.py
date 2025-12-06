import subprocess
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

class ShellCommandRequest(BaseModel):
    command: str
    cwd: Optional[str] = None

router = APIRouter()

# --- Safety Guardrails ---
FORBIDDEN_COMMANDS = [
    "rm -rf /", "mkfs", "dd", ":(){ :|:& };:", "wget", "curl", "nc -e"
]
FORBIDDEN_DIRS = [
    "C:\\Windows", "/bin", "/usr", "/etc"
]

class SafetyGuard:
    @staticmethod
    def check(command: str, cwd: str = ".") -> None:
        # 1. Check Keywords
        for bad in FORBIDDEN_COMMANDS:
            if bad in command:
                raise HTTPException(status_code=403, detail=f"Safety Guard: Command blocked due to dangerous pattern '{bad}'")
        
        # 2. Check Directories (Simple string match)
        if cwd:
            abs_cwd = os.path.abspath(cwd)
            for bad_dir in FORBIDDEN_DIRS:
                if bad_dir in abs_cwd:
                     raise HTTPException(status_code=403, detail=f"Safety Guard: Recursive operations in '{bad_dir}' are forbidden")

@router.post("/execute")
def execute_shell(req: ShellCommandRequest):
    cwd = req.cwd or os.getcwd()
    
    # 1. Safety Check
    SafetyGuard.check(req.command, cwd)
    
    # 2. Execute
    try:
        # Use subprocess safely (no shell=True for input if possible, but for 'empire via shell' we might need it)
        # We will use shell=True because the user wants "Command Line" power, but relying on Guardrails.
        result = subprocess.run(
            req.command, 
            cwd=cwd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=30 # Prevent hangs
        )
        
        return {
            "command": req.command,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out (30s limit)"}
    except Exception as e:
        return {"error": str(e)}
