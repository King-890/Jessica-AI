import sqlite3


def summarize_memory():
    conn = sqlite3.connect("data/memory.db")
    try:
        rows = conn.execute(
            "SELECT prompt, response FROM interactions ORDER BY id DESC LIMIT 100"
        ).fetchall()
        text = " ".join([f"Q:{r[0]} A:{r[1]}" for r in rows])
        summary = text[:2000]
        conn.execute("DELETE FROM interactions")
        conn.execute(
            "INSERT INTO interactions(prompt,response) VALUES (?,?)",
            ("memory_summary", summary),
        )
        conn.commit()
    finally:
        conn.close()