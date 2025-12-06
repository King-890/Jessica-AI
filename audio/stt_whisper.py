from typing import Optional
import tempfile
import os
import wave

try:
    import whisper  # type: ignore
except Exception:
    whisper = None


class WhisperSTT:
    def __init__(self, model_name: Optional[str] = "base"):
        self._model = None
        if whisper is not None:
            try:
                self._model = whisper.load_model(model_name or "base")
            except Exception:
                self._model = None

    def is_ready(self) -> bool:
        return self._model is not None

    def transcribe_pcm16(self, audio_bytes: bytes) -> str:
        """
        Accept raw PCM16 mono 16kHz bytes; write to temp WAV and transcribe.
        Returns recognized text, or placeholder if not configured.
        """
        if not self._model:
            return "[stt-not-configured]"
        tmp_path = None
        try:
            fd, tmp_path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            with wave.open(tmp_path, "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(16000)
                w.writeframes(audio_bytes)
            # fp16 False for CPU
            result = self._model.transcribe(tmp_path, fp16=False)
            return str(result.get("text", "")).strip()
        except Exception:
            return ""
        finally:
            try:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

    # Whisper does not provide straightforward partials; stubs provided for interface parity
    def accept_chunk(self, _audio_bytes: bytes):
        return None

    def finalize_chunked(self, audio_bytes: bytes) -> str:
        return self.transcribe_pcm16(audio_bytes)