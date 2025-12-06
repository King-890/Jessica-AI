import threading
import speech_recognition as sr
from typing import Optional, Callable
from .stt_engine import STTEngine
from .wakeword import matches_wake_phrase
from ..ai_core import jessica_core
from .tts_engine import TTSEngine


class VoiceListener:
    def __init__(self, wake_phrase: str = "hey jessica", adapter: str = "speech_recognition", whisper_model: str = "base"):
        self.wake_phrase = wake_phrase
        self.stt = STTEngine(adapter=adapter, whisper_model=whisper_model)
        self.tts = TTSEngine()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self._stop = threading.Event()
        self._bg_thread: Optional[threading.Thread] = None

    def _callback(self, recognizer, audio):
        if self._stop.is_set():
            return
        text = self.stt.transcribe(audio) or ""
        if not text:
            return
        if matches_wake_phrase(text, self.wake_phrase):
            # Next phrase after wake: allow natural command
            self.tts.speak("Yes?")
            return
        # Route text to Jessica core for reasoning
        try:
            response = jessica_core(text)
            if isinstance(response, dict):
                spoken = response.get("message") or str(response)
            else:
                spoken = str(response)
            self.tts.speak(spoken)
        except Exception:
            pass

    def start(self):
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            self._bg_thread = self.recognizer.listen_in_background(self.microphone, self._callback, phrase_time_limit=5)
        except Exception:
            self._bg_thread = None

    def stop(self):
        try:
            self._stop.set()
            if self._bg_thread:
                self._bg_thread(wait_for_stop=False)
        except Exception:
            pass

_listener: Optional[VoiceListener] = None


def start(wake_phrase: str = "hey jessica", adapter: str = "speech_recognition", whisper_model: str = "base"):
    global _listener
    if _listener is not None:
        return
    _listener = VoiceListener(wake_phrase=wake_phrase, adapter=adapter, whisper_model=whisper_model)
    _listener.start()


def stop():
    global _listener
    if _listener:
        _listener.stop()
        _listener = None