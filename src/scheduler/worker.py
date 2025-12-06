import json
import os
import threading
import time
from datetime import datetime
import subprocess
from typing import Optional

from data import db
from croniter import croniter
import dateutil.parser


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class SchedulerWorker:
    def __init__(self, interval: int = 10):
        self._interval = interval
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _run(self):
        while not self._stop.is_set():
            try:
                tasks = db.get_due_tasks()
                now = datetime.utcnow()
                for t in tasks:
                    if not self._is_due(t, now):
                        continue
                    rc, out, err = self._execute_task(t)
                    db.log_task_result(t["id"], rc, out, err)
                    db.mark_task_run(t["id"])  # sqlite3.Row supports key access
            except Exception:
                # Avoid crashing the loop; in production, log the exception
                pass
            self._stop.wait(self._interval)

    def _is_due(self, task_row, now: datetime) -> bool:
        stype = task_row["schedule_type"] or "interval"
        last_run = task_row.get("last_run") if isinstance(task_row, dict) else task_row["last_run"] if "last_run" in task_row.keys() else None
        if stype == "interval":
            interval = int(task_row.get("interval_seconds") if isinstance(task_row, dict) else task_row["interval_seconds"]) or 0
            if last_run is None:
                return True
            try:
                last = dateutil.parser.parse(last_run)
            except Exception:
                return True
            return (now - last).total_seconds() >= interval
        elif stype == "cron":
            expr = task_row.get("cron_expr") if isinstance(task_row, dict) else task_row["cron_expr"]
            if not expr:
                return False
            base = dateutil.parser.parse(last_run) if last_run else now.replace(year=now.year - 1)
            try:
                itr = croniter(expr, base)
                next_time = itr.get_next(datetime)
                return now >= next_time
            except Exception:
                return False
        elif stype == "iso":
            iso = task_row.get("iso_time") if isinstance(task_row, dict) else task_row["iso_time"]
            if not iso:
                return False
            try:
                tgt = dateutil.parser.parse(iso)
                # Run only once: if never run and now >= tgt
                return last_run is None and now >= tgt
            except Exception:
                return False
        return False

    def _execute_task(self, task_row):
        command = task_row["command"].lower()
        args_json = task_row["args_json"]
        args = []
        if args_json:
            try:
                args = json.loads(args_json)
            except Exception:
                args = []

        # Only support allowlisted commands similar to system endpoint
        if command == "python":
            if not args:
                return None, "", "Missing args"
            script_path = args[0]
            target = os.path.abspath(os.path.join(BASE_DIR, script_path))
            if os.path.commonpath([target, BASE_DIR]) != BASE_DIR:
                return None, "", "Path outside base"
            if not os.path.isfile(target):
                return None, "", "File not found"
            full = ["python", target] + args[1:]
            p = subprocess.run(full, capture_output=True, text=True, timeout=20, shell=False)
            return p.returncode, p.stdout, p.stderr
        elif command in {"echo", "dir"}:
            full = [command] + args
            p = subprocess.run(full, capture_output=True, text=True, timeout=10, shell=True)
            return p.returncode, p.stdout, p.stderr
        else:
            # Unsupported command; ignore
            return None, "", "Unsupported command"


worker_singleton = SchedulerWorker(interval=10)