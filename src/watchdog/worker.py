import threading
import time
from typing import Dict, Any

import psutil  # type: ignore
import os

from data.db import log_watchdog_event
from src.configs.settings import Settings
from src.watchdog.devtools import DevToolsMonitor


class WatchdogWorker:
    def __init__(self):
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._snapshot: Dict[str, Any] = {}
        self._settings = Settings()
        self._devtools = DevToolsMonitor(port=int(os.getenv("BROWSER_DEVTOOLS_PORT", str(getattr(self._settings, "browser_devtools_port", 9222)))))

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        try:
            self._devtools.start()
        except Exception:
            pass

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1)
        try:
            self._devtools.stop()
        except Exception:
            pass

    def snapshot(self) -> Dict[str, Any]:
        return self._snapshot.copy()

    def _run(self):
        unity_detected = False
        chrome_detected = False
        last_unity_log_check = 0.0

        while not self._stop.is_set():
            try:
                procs = {p.pid: p.info for p in psutil.process_iter(attrs=["name", "exe"]) }
                names = [str(info.get("name") or "").lower() for info in procs.values()]

                unity_detected = any("unity" in n for n in names)
                chrome_detected = any("chrome" in n or "msedge" in n for n in names)

                self._snapshot = {
                    "unity_running": unity_detected,
                    "browser_running": chrome_detected,
                    "process_count": len(procs),
                    "idle_mode": psutil.cpu_percent(interval=0.1) < 5.0,
                }

                if unity_detected and time.time() - last_unity_log_check > 5:
                    self._check_unity_logs()
                    last_unity_log_check = time.time()

                # Future: monitor active window, browser console via devtools API, etc.

            except Exception:
                pass

            time.sleep(2)

    def _check_unity_logs(self):
        # Windows typical path; adapt as needed
        import os
        user = os.getenv("USERNAME") or os.getenv("USER") or ""
        candidates = [
            os.path.expanduser(rf"~\AppData\Local\Unity\Editor\Editor.log"),
            rf"C:\\Users\\{user}\\AppData\\Local\\Unity\\Editor\\Editor.log",
        ]
        for path in candidates:
            try:
                if os.path.exists(path):
                    with open(path, "r", errors="ignore") as f:
                        tail = f.readlines()[-50:]
                    for line in tail:
                        l = line.strip()
                        if not l:
                            continue
                        if "error" in l.lower():
                            log_watchdog_event("unity", "error", l, None)
                        elif "warning" in l.lower():
                            log_watchdog_event("unity", "warning", l, None)
                    break
            except Exception:
                continue


watchdog_singleton = WatchdogWorker()