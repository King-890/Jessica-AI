import sqlite3
from pathlib import Path
from fastapi import APIRouter, Query, Depends
from .routes.auth import require_role


router = APIRouter(prefix="/memory", tags=["memory"])
DB_PATH = Path("data/memory.db")


@router.get("/history")
async def history(limit: int = Query(default=100, ge=1, le=500)):
    if not DB_PATH.exists():
        return {"items": []}
    conn = sqlite3.connect(DB_PATH.as_posix())
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt TEXT,
            response TEXT,
            time DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute("SELECT id, prompt, response, time FROM interactions ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    items = [
        {"id": r[0], "prompt": r[1], "response": r[2], "time": r[3]}
        for r in rows
    ]
    return {"items": items}


def _ensure_table(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt TEXT,
            response TEXT,
            time DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()


@router.post("/store")
async def store_memory(payload: dict, _=Depends(require_role("user"))):
    """Persist a prompt-response pair into AI memory."""
    prompt = (payload.get("prompt") or "").strip()
    response = (payload.get("response") or "").strip()
    conn = sqlite3.connect(DB_PATH.as_posix())
    try:
        _ensure_table(conn)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO interactions (prompt, response) VALUES (?, ?)", (prompt, response)
        )
        conn.commit()
        return {"id": cur.lastrowid}
    finally:
        conn.close()


@router.post("/query")
async def query_memory(payload: dict, _=Depends(require_role("user"))):
    """Query stored memory with optional keyword filter."""
    q = (payload.get("q") or "").strip()
    limit = int(payload.get("limit") or 50)
    limit = max(1, min(limit, 500))
    conn = sqlite3.connect(DB_PATH.as_posix())
    try:
        _ensure_table(conn)
        cur = conn.cursor()
        if q:
            like = f"%{q}%"
            cur.execute(
                "SELECT id, prompt, response, time FROM interactions WHERE prompt LIKE ? OR response LIKE ? ORDER BY id DESC LIMIT ?",
                (like, like, limit),
            )
        else:
            cur.execute(
                "SELECT id, prompt, response, time FROM interactions ORDER BY id DESC LIMIT ?",
                (limit,),
            )
        rows = cur.fetchall()
        items = [
            {"id": r[0], "prompt": r[1], "response": r[2], "time": r[3]}
            for r in rows
        ]
        return {"items": items}
    finally:
        conn.close()