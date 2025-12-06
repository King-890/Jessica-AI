import pyttsx3


class TTSEngine:
    def __init__(self, rate: int = 180, volume: float = 1.0, voice_id: str | None = None):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', rate)
        self.engine.setProperty('volume', volume)
        if voice_id is not None:
            try:
                self.engine.setProperty('voice', voice_id)
            except Exception:
                pass

    def speak(self, text: str):
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception:
            pass