import os
import sqlite3
import threading
from typing import List, Tuple


DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jessica.db")
_conn = None
_lock = threading.Lock()


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.execute("PRAGMA journal_mode=WAL;")
        _conn.row_factory = sqlite3.Row
    return _conn


def init_db():
    conn = _get_conn()
    with _lock:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                ts DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                ts DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS patterns (
                pattern TEXT PRIMARY KEY,
                count INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS plugins (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                config_json TEXT
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                command TEXT NOT NULL,
                args_json TEXT,
                interval_seconds INTEGER NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                last_run DATETIME
            );

            CREATE TABLE IF NOT EXISTS task_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                returncode INTEGER,
                stdout TEXT,
                stderr TEXT,
                ts DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS watchdog_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                metadata_json TEXT,
                ts DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.commit()

        # Simple migration: add schedule fields to tasks if missing
        cur = conn.execute("PRAGMA table_info(tasks)")
        cols = {row[1] for row in cur.fetchall()}
        if "schedule_type" not in cols:
            conn.execute("ALTER TABLE tasks ADD COLUMN schedule_type TEXT DEFAULT 'interval'")
        if "cron_expr" not in cols:
            conn.execute("ALTER TABLE tasks ADD COLUMN cron_expr TEXT")
        if "iso_time" not in cols:
            conn.execute("ALTER TABLE tasks ADD COLUMN iso_time TEXT")
        conn.commit()


def log_command(text: str) -> None:
    conn = _get_conn()
    with _lock:
        conn.execute("INSERT INTO commands (text) VALUES (?)", (text,))
        # Keep only last 50
        conn.execute(
            "DELETE FROM commands WHERE id NOT IN (SELECT id FROM commands ORDER BY id DESC LIMIT 50)"
        )
        conn.commit()


def get_recent_commands(limit: int = 10) -> List[str]:
    conn = _get_conn()
    with _lock:
        cur = conn.execute(
            "SELECT text FROM commands ORDER BY id DESC LIMIT ?", (limit,)
        )
        return [row[0] for row in cur.fetchall()]


def append_conversation(role: str, content: str) -> None:
    conn = _get_conn()
    with _lock:
        conn.execute(
            "INSERT INTO conversations (role, content) VALUES (?, ?)", (role, content)
        )
        # Cap history size to last 200 messages
        conn.execute(
            "DELETE FROM conversations WHERE id NOT IN (SELECT id FROM conversations ORDER BY id DESC LIMIT 200)"
        )
        conn.commit()


def get_recent_conversation(limit: int = 20) -> List[Tuple[str, str]]:
    conn = _get_conn()
    with _lock:
        cur = conn.execute(
            "SELECT role, content FROM conversations ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return [(row[0], row[1]) for row in cur.fetchall()]


def bump_pattern(pattern: str) -> None:
    conn = _get_conn()
    with _lock:
        conn.execute(
            "INSERT INTO patterns (pattern, count) VALUES (?, 1) ON CONFLICT(pattern) DO UPDATE SET count = count + 1",
            (pattern,),
        )
        conn.commit()


def get_top_patterns(limit: int = 10) -> List[Tuple[str, int]]:
    conn = _get_conn()
    with _lock:
        cur = conn.execute(
            "SELECT pattern, count FROM patterns ORDER BY count DESC LIMIT ?",
            (limit,),
        )
        return [(row[0], row[1]) for row in cur.fetchall()]


# Plugin registry operations
def add_plugin(plugin_id: str, name: str, enabled: bool = True, config_json: str | None = None) -> None:
    conn = _get_conn()
    with _lock:
        conn.execute(
            "INSERT INTO plugins (id, name, enabled, config_json) VALUES (?, ?, ?, ?)",
            (plugin_id, name, 1 if enabled else 0, config_json),
        )
        conn.commit()


def list_plugins() -> List[sqlite3.Row]:
    conn = _get_conn()
    with _lock:
        cur = conn.execute("SELECT id, name, enabled, config_json FROM plugins ORDER BY name ASC")
        return cur.fetchall()


def set_plugin_enabled(plugin_id: str, enabled: bool) -> None:
    conn = _get_conn()
    with _lock:
        conn.execute("UPDATE plugins SET enabled = ? WHERE id = ?", (1 if enabled else 0, plugin_id))
        conn.commit()


def remove_plugin(plugin_id: str) -> None:
    conn = _get_conn()
    with _lock:
        conn.execute("DELETE FROM plugins WHERE id = ?", (plugin_id,))
        conn.commit()


def update_plugin_config(plugin_id: str, config_json: str) -> None:
    conn = _get_conn()
    with _lock:
        conn.execute("UPDATE plugins SET config_json = ? WHERE id = ?", (config_json, plugin_id))
        conn.commit()


# Scheduler task operations
def add_task(name: str, command: str, args_json: str | None, interval_seconds: int, enabled: bool = True) -> int:
    conn = _get_conn()
    with _lock:
        cur = conn.execute(
            "INSERT INTO tasks (name, command, args_json, interval_seconds, enabled, schedule_type) VALUES (?, ?, ?, ?, ?, 'interval')",
            (name, command, args_json, interval_seconds, 1 if enabled else 0),
        )
        conn.commit()
        return cur.lastrowid


def add_task_advanced(name: str, command: str, args_json: str | None, schedule_type: str, interval_seconds: int | None = None, cron_expr: str | None = None, iso_time: str | None = None, enabled: bool = True) -> int:
    conn = _get_conn()
    with _lock:
        cur = conn.execute(
            "INSERT INTO tasks (name, command, args_json, interval_seconds, enabled, schedule_type, cron_expr, iso_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                name,
                command,
                args_json,
                interval_seconds if interval_seconds is not None else 0,
                1 if enabled else 0,
                schedule_type,
                cron_expr,
                iso_time,
            ),
        )
        conn.commit()
        return cur.lastrowid


def list_tasks() -> List[sqlite3.Row]:
    conn = _get_conn()
    with _lock:
        cur = conn.execute(
            "SELECT id, name, command, args_json, interval_seconds, enabled, last_run, schedule_type, cron_expr, iso_time FROM tasks ORDER BY id ASC"
        )
        return cur.fetchall()


def set_task_enabled(task_id: int, enabled: bool) -> None:
    conn = _get_conn()
    with _lock:
        conn.execute("UPDATE tasks SET enabled = ? WHERE id = ?", (1 if enabled else 0, task_id))
        conn.commit()


def delete_task(task_id: int) -> None:
    conn = _get_conn()
    with _lock:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()


def mark_task_run(task_id: int) -> None:
    conn = _get_conn()
    with _lock:
        conn.execute("UPDATE tasks SET last_run = CURRENT_TIMESTAMP WHERE id = ?", (task_id,))
        conn.commit()


def get_due_tasks() -> List[sqlite3.Row]:
    conn = _get_conn()
    with _lock:
        cur = conn.execute(
            """
            SELECT id, name, command, args_json, interval_seconds, schedule_type, cron_expr, iso_time FROM tasks
            WHERE enabled = 1
            ORDER BY id ASC
            """
        )
        return cur.fetchall()


def log_task_result(task_id: int, returncode: int | None, stdout: str, stderr: str) -> None:
    conn = _get_conn()
    with _lock:
        conn.execute(
            "INSERT INTO task_results (task_id, returncode, stdout, stderr) VALUES (?, ?, ?, ?)",
            (task_id, returncode, stdout, stderr),
        )
        conn.commit()


def get_task_results(task_id: int, limit: int = 20) -> List[sqlite3.Row]:
    conn = _get_conn()
    with _lock:
        cur = conn.execute(
            "SELECT id, returncode, stdout, stderr, ts FROM task_results WHERE task_id = ? ORDER BY id DESC LIMIT ?",
            (task_id, limit),
        )
        return cur.fetchall()


def log_watchdog_event(source: str, level: str, message: str, metadata_json: str | None = None) -> None:
    conn = _get_conn()
    with _lock:
        conn.execute(
            "INSERT INTO watchdog_events (source, level, message, metadata_json) VALUES (?, ?, ?, ?)",
            (source, level, message, metadata_json),
        )
        # Keep last 500 events
        conn.execute(
            "DELETE FROM watchdog_events WHERE id NOT IN (SELECT id FROM watchdog_events ORDER BY id DESC LIMIT 500)"
        )
        conn.commit()


def list_watchdog_events(limit: int = 50) -> List[sqlite3.Row]:
    conn = _get_conn()
    with _lock:
        cur = conn.execute(
            "SELECT id, source, level, message, metadata_json, ts FROM watchdog_events ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return cur.fetchall()


# Initialize on import
init_db()