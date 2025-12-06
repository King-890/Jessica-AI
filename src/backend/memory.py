import sqlite3
from pathlib import Path


DB_PATH = Path("data/memory.db")


def save_interaction(prompt: str, response: str) -> None:
    """Persist an interaction to SQLite (data/memory.db)."""
    # Ensure data directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

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
    cur.execute(
        "INSERT INTO interactions(prompt, response) VALUES (?, ?)",
        (prompt or "", response or ""),
    )
    # Keep only last 100 entries to avoid bloat
    cur.execute(
        "DELETE FROM interactions WHERE id NOT IN (SELECT id FROM interactions ORDER BY id DESC LIMIT 100)"
    )
    conn.commit()
    conn.close()