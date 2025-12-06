import speech_recognition as sr
from typing import Optional

try:
    from audio import stt as stt_local
    from audio import stt_whisper as stt_whisper
except Exception:
    stt_local = None
    stt_whisper = None


class STTEngine:
    def __init__(self, adapter: str = "speech_recognition", whisper_model: str = "base"):
        self.adapter = adapter
        self.whisper_model = whisper_model
        self.recognizer = sr.Recognizer()

    def transcribe(self, audio_data: sr.AudioData) -> Optional[str]:
        try:
            if self.adapter == "whisper" and stt_whisper:
                # Fallback to local whisper pipeline if available
                return stt_whisper.transcribe_audio_data(audio_data, model_name=self.whisper_model)
            # Default: use SpeechRecognition's built-in online recognizer (Sphinx/GCloud optional)
            return self.recognizer.recognize_google(audio_data)
        except Exception:
            return None