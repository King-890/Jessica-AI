import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


# Restrict FS operations under this base directory
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _safe_join(*paths: str) -> str:
    target = os.path.abspath(os.path.join(*paths))
    base = os.path.abspath(BASE_DIR)
    if os.path.commonpath([target, base]) != base:
        raise HTTPException(status_code=403, detail="Forbidden path")
    return target


class WriteRequest(BaseModel):
    path: str
    content: str


class PathRequest(BaseModel):
    path: str


router = APIRouter()


@router.get("/list")
def list_dir(path: str = ""):
    target = _safe_join(BASE_DIR, path)
    if not os.path.isdir(target):
        raise HTTPException(status_code=404, detail="Not a directory")
    items = []
    for name in os.listdir(target):
        full = os.path.join(target, name)
        items.append({
            "name": name,
            "is_dir": os.path.isdir(full),
            "size": os.path.getsize(full) if os.path.isfile(full) else None,
        })
    return {"path": os.path.relpath(target, BASE_DIR), "items": items}


@router.get("/read")
def read_file(path: str):
    target = _safe_join(BASE_DIR, path)
    if not os.path.isfile(target):
        raise HTTPException(status_code=404, detail="File not found")
    try:
        with open(target, "r", encoding="utf-8") as f:
            return {"path": path, "content": f.read()}
    except UnicodeDecodeError:
        raise HTTPException(status_code=415, detail="Unsupported file encoding")


@router.post("/write")
def write_file(req: WriteRequest):
    target = _safe_join(BASE_DIR, req.path)
    parent = os.path.dirname(target)
    os.makedirs(parent, exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write(req.content)
    return {"path": req.path, "status": "written"}


@router.post("/create")
def create_file(req: WriteRequest):
    target = _safe_join(BASE_DIR, req.path)
    parent = os.path.dirname(target)
    os.makedirs(parent, exist_ok=True)
    if os.path.exists(target):
        raise HTTPException(status_code=409, detail="File already exists")
    with open(target, "w", encoding="utf-8") as f:
        f.write(req.content)
    return {"path": req.path, "status": "created"}


@router.post("/delete")
def delete_file(req: PathRequest):
    target = _safe_join(BASE_DIR, req.path)
    if not os.path.exists(target):
        raise HTTPException(status_code=404, detail="Path not found")
    if os.path.isdir(target):
        raise HTTPException(status_code=400, detail="Refusing to delete directories via file delete")
    os.remove(target)
    return {"path": req.path, "status": "deleted"}


@router.post("/mkdir")
def make_dir(req: PathRequest):
    target = _safe_join(BASE_DIR, req.path)
    os.makedirs(target, exist_ok=True)
    return {"path": req.path, "status": "mkdir"}