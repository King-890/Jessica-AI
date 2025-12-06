import asyncio
import psutil
from fastapi import APIRouter, Request
from data.db import log_watchdog_event
from .vector_memory import count as vector_count, last_update_time


class SystemWatcher:
    def __init__(self, interval: float = 5.0):
        self.interval = interval
        self.latest = {
            "cpu_percent": 0.0,
            "memory_percent": 0.0,
            "processes": [],
        }
        self._running = False
        self._publisher = None
        self._last_anomaly_ts = 0.0

    async def run(self):
        self._running = True
        while self._running:
            try:
                self.latest["cpu_percent"] = float(psutil.cpu_percent(interval=None))
                self.latest["memory_percent"] = float(psutil.virtual_memory().percent)
                procs = []
                for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
                    info = p.info
                    procs.append({
                        "pid": info.get("pid"),
                        "name": info.get("name"),
                        "cpu": info.get("cpu_percent"),
                        "mem": info.get("memory_percent"),
                    })
                # Top 8 by CPU
                procs.sort(key=lambda x: (x.get("cpu") or 0), reverse=True)
                self.latest["processes"] = procs[:8]
                # Publish event to log stream if available
                if callable(self._publisher):
                    try:
                        self._publisher({"type": "system_status", "data": self.latest})
                    except Exception:
                        pass
                # Detect anomalies
                try:
                    if (self.latest["cpu_percent"] or 0) >= 90.0:
                        now = asyncio.get_event_loop().time()
                        # throttle anomaly logs to once per 60s
                        if now - self._last_anomaly_ts > 60.0:
                            self._last_anomaly_ts = now
                            log_watchdog_event(
                                source="system",
                                level="warning",
                                message="High CPU usage",
                                metadata_json=f"{{\"cpu_percent\": {self.latest['cpu_percent']}}}",
                            )
                except Exception:
                    pass
            except Exception:
                pass
            await asyncio.sleep(self.interval)

    def stop(self):
        self._running = False


router = APIRouter(prefix="/system", tags=["system"])
_watcher = SystemWatcher()


@router.get("/status")
async def status(request: Request):
    base = dict(_watcher.latest)
    try:
        base["vector_memory_count"] = int(vector_count())
        ts = float(last_update_time() or 0)
        base["knowledge_last_update"] = ts
    except Exception:
        base["vector_memory_count"] = 0
        base["knowledge_last_update"] = 0
    # Scheduler status
    try:
        app = request.app
        sched = {
            "auto_update": bool(getattr(app.state, "update_task", None)),
            "cron_update": bool(getattr(app.state, "update_cron_task", None)),
            "knowledge_updater": bool(getattr(app.state, "knowledge_task", None)),
        }
        base["scheduler_status"] = sched
    except Exception:
        base["scheduler_status"] = {}
    return base


def start(app):
    app.state.watcher_task = asyncio.create_task(_watcher.run())


def stop(app):
    try:
        _watcher.stop()
        task = getattr(app.state, "watcher_task", None)
        if task:
            task.cancel()
    except Exception:
        pass


def set_publisher(fn):
    """Attach a publisher callable used to push system events to clients."""
    try:
        _watcher._publisher = fn
    except Exception:
        pass