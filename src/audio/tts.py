import threading
from typing import Optional

try:
    import pyttsx3  # type: ignore
except Exception:  # pragma: no cover
    pyttsx3 = None


class TTS:
    def __init__(self):
        self._engine = None
        if pyttsx3 is not None:
            try:
                self._engine = pyttsx3.init()
            except Exception:
                self._engine = None

    def is_ready(self) -> bool:
        return self._engine is not None

    def speak(self, text: str, rate: Optional[int] = None, volume: Optional[float] = None, gender: Optional[str] = None):
        if not self._engine:
            raise RuntimeError("TTS engine not available")

        if rate is not None:
            try:
                self._engine.setProperty("rate", int(rate))
            except Exception:
                pass
        if volume is not None:
            try:
                self._engine.setProperty("volume", float(volume))
            except Exception:
                pass

        if gender:
            try:
                voices = self._engine.getProperty("voices") or []
                target = None
                for v in voices:
                    name = getattr(v, "name", "").lower()
                    id_ = getattr(v, "id", "").lower()
                    if gender.lower() in name or gender.lower() in id_:
                        target = v
                        break
                if target:
                    self._engine.setProperty("voice", target.id)
            except Exception:
                pass

        # run in a thread to avoid blocking
        def _run():
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except Exception:
                pass

        threading.Thread(target=_run, daemon=True).start()