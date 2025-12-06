from fastapi import APIRouter
import sqlite3
from pathlib import Path

router = APIRouter(prefix="/memory", tags=["memory"])
DB_PATH = Path("data/memory.db")


@router.get("/summary")
async def memory_summary(limit: int = 20):
    """Return a condensed snapshot of recent interactions for faster recall."""
    if not DB_PATH.exists():
        return {"items": []}
    conn = sqlite3.connect(DB_PATH.as_posix())
    try:
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
        cur.execute("SELECT prompt, response, time FROM interactions ORDER BY id DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        items = []
        for r in rows:
            prompt = (r[0] or "").strip()
            response = (r[1] or "").strip()
            # Simple short summary: truncate and pair
            items.append({
                "prompt": prompt[:200],
                "response": response[:400],
                "time": r[2],
            })
        return {"items": items}
    finally:
        conn.close()