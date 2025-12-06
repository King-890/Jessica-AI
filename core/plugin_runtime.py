import threading
from typing import Any


class Sandbox:
    def __init__(self, timeout_seconds: float = 2.0):
        self.timeout_seconds = timeout_seconds

    def call(self, obj: Any, method: str, *args, **kwargs):
        fn = getattr(obj, method, None)
        if not callable(fn):
            return None
        result = [None]
        exc = [None]

        def _run():
            try:
                result[0] = fn(*args, **kwargs)
            except Exception as e:
                exc[0] = e

        t = threading.Thread(target=_run)
        t.start()
        t.join(self.timeout_seconds)
        if t.is_alive():
            return None
        if exc[0] is not None:
            return None
        return result[0]