import threading
import time

try:
    import speech_recognition as sr  # type: ignore
except Exception:
    sr = None

from .ai_core import jessica_core
from .speak import speak


def listen_forever():
    if sr is None:
        print("SpeechRecognition not installed. Install with `pip install SpeechRecognition pyaudio`.")
        return
    r = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        r.adjust_for_ambient_noise(source)
        print("🎧 Jessica listening… say 'Hey Jessica'")
        while True:
            audio = r.listen(source)
            try:
                text = r.recognize_google(audio)
            except Exception:
                continue
            if not text:
                continue
            lt = text.lower().strip()
            if lt.startswith("hey jessica"):
                speak("Yes?")
                cmd = lt.replace("hey jessica", "").strip()
                if cmd:
                    try:
                        response = jessica_core(cmd)
                        speak(response)
                    except Exception:
                        pass


def start_background_listener():
    t = threading.Thread(target=listen_forever, daemon=True)
    t.start()
    return t