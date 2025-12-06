import requests
import threading
import time
import json
import websockets

from data.db import log_watchdog_event


class DevToolsMonitor:
    def __init__(self, port: int = 9222):
        self.port = port
        self._thread = None
        self._stop = threading.Event()

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _run(self):
        while not self._stop.is_set():
            try:
                targets = requests.get(f"http://localhost:{self.port}/json", timeout=1).json()
                for t in targets:
                    ws = t.get("webSocketDebuggerUrl")
                    if not ws:
                        continue
                    try:
                        # Connect briefly and subscribe to Runtime console events
                        # To limit scope, we connect and listen for a short window, then move on
                        self._listen_console(ws, duration=2.0)
                    except Exception:
                        continue
            except Exception:
                pass
            time.sleep(5)

    async def _console_client(self, ws_url: str, duration: float):
        async with websockets.connect(ws_url) as ws:
            # Enable Runtime
            await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
            start = time.time()
            while time.time() - start < duration:
                try:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    method = data.get("method")
                    if method == "Runtime.consoleAPICalled":
                        args = data.get("params", {}).get("args", [])
                        texts = []
                        for a in args:
                            val = a.get("value") or a.get("description")
                            if isinstance(val, str):
                                texts.append(val)
                        if texts:
                            log_watchdog_event("browser", "info", " ".join(texts), None)
                except Exception:
                    break

    def _listen_console(self, ws_url: str, duration: float):
        import asyncio
        try:
            asyncio.run(self._console_client(ws_url, duration))
        except Exception:
            pass