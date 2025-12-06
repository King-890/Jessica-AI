from typing import Optional

try:
    import vosk  # type: ignore
except Exception:
    vosk = None


class STT:
    def __init__(self, model_path: Optional[str] = None):
        self._model = None
        self._rec = None
        if vosk is not None and model_path:
            try:
                self._model = vosk.Model(model_path)
                self._rec = vosk.KaldiRecognizer(self._model, 16000)
            except Exception:
                self._model = None
                self._rec = None

    def is_ready(self) -> bool:
        return self._rec is not None

    def transcribe_pcm16(self, audio_bytes: bytes) -> str:
        """
        Accepts raw PCM16 mono 16kHz bytes; returns recognized text.
        If no STT engine configured, returns an informative message.
        """
        if not self._rec:
            return "[stt-not-configured]"
        try:
            self._rec.AcceptWaveform(audio_bytes)
            import json
            res = json.loads(self._rec.Result())
            return res.get("text", "")
        except Exception:
            return ""

    # Streaming helpers for partial transcripts
    def accept_chunk(self, audio_bytes: bytes) -> str | None:
        """Accept a PCM16 chunk and return a partial transcript when available."""
        if not self._rec:
            return None
        try:
            self._rec.AcceptWaveform(audio_bytes)
            import json
            pres = json.loads(self._rec.PartialResult())
            partial = pres.get("partial", "")
            return partial or None
        except Exception:
            return None

    def finalize_chunked(self, _audio_bytes: bytes) -> str:
        """Finalize current recognition and return final text; reset recognizer state."""
        if not self._rec:
            return "[stt-not-configured]"
        try:
            import json
            res = json.loads(self._rec.Result())
            text = res.get("text", "")
            # Reset recognizer for next session
            if self._model is not None and vosk is not None:
                try:
                    self._rec = vosk.KaldiRecognizer(self._model, 16000)
                except Exception:
                    pass
            return text
        except Exception:
            return ""