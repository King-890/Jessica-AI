import os
import sqlite3
import time
import secrets

# Compute absolute DB path relative to project root
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DB = os.path.join(BASE_DIR, 'data', 'jessica.db')


def _ensure_table():
    conn = sqlite3.connect(DB)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tokens (
                token TEXT PRIMARY KEY,
                created_at INTEGER,
                role TEXT DEFAULT 'user'
            )
            """
        )
        conn.commit()
        # Migration: ensure role column exists
        cur = conn.execute("PRAGMA table_info(tokens)")
        cols = {row[1] for row in cur.fetchall()}
        if "role" not in cols:
            conn.execute("ALTER TABLE tokens ADD COLUMN role TEXT DEFAULT 'user'")
            conn.commit()
    finally:
        conn.close()


def validate_token(token: str) -> bool:
    _ensure_table()
    conn = sqlite3.connect(DB)
    try:
        cur = conn.execute("SELECT 1 FROM tokens WHERE token=?", (token,))
        ok = cur.fetchone() is not None
        return ok
    finally:
        conn.close()


def get_token_role(token: str) -> str | None:
    _ensure_table()
    conn = sqlite3.connect(DB)
    try:
        cur = conn.execute("SELECT role FROM tokens WHERE token=?", (token,))
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def make_token(role: str = "user") -> str:
    _ensure_table()
    t = secrets.token_hex(32)
    conn = sqlite3.connect(DB)
    try:
        conn.execute("INSERT INTO tokens(token, created_at, role) VALUES (?,?,?)", (t, int(time.time()), role))
        conn.commit()
        return t
    finally:
        conn.close()


def require_role(role: str):
    from fastapi import Request, HTTPException

    async def checker(request: Request):
        token = request.headers.get("Authorization") or request.headers.get("X-API-Token")
        if token and token.lower().startswith("bearer "):
            token = token.split(" ", 1)[1]
        if not token:
            raise HTTPException(status_code=401, detail="Unauthorized")
        r = get_token_role(token)
        if r is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        # simple hierarchy: admin > user > skill (skill restricted)
        if role == "admin" and r != "admin":
            raise HTTPException(status_code=403, detail="Forbidden")
        if role == "user" and r not in ("admin", "user"):
            raise HTTPException(status_code=403, detail="Forbidden")
        return True

    return checker