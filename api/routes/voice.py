from fastapi import APIRouter, Body

from audio.tts import TTS
from core.mood import MoodEngine
from audio.stt import STT
from audio.stt_whisper import WhisperSTT
from configs.settings import Settings
import io
import wave
import subprocess
import os
from fastapi import UploadFile, Body, WebSocket, WebSocketDisconnect
from typing import Dict, Any

try:
    import whisper as whisper_lib  # type: ignore
except Exception:
    whisper_lib = None

router = APIRouter(prefix="/voice", tags=["voice"])

_tts = TTS()
_mood = MoodEngine()
_settings = Settings()
# Initialize mood profile from settings
try:
    _mood.set_profile(getattr(_settings, "mood_profile", "neutral"))
except Exception:
    pass
if (_settings.stt_adapter or "vosk").lower() == "whisper":
    _stt = WhisperSTT(model_name=_settings.whisper_model_name)
else:
    _stt = STT(model_path=_settings.vosk_model_path)


@router.get("/status")
def voice_status():
    def list_whisper_models():
        if whisper_lib is None:
            return []
        try:
            models = whisper_lib.available_models()
            # available_models may be dict; return keys
            if isinstance(models, dict):
                return list(models.keys())
            return list(models)  # type: ignore
        except Exception:
            return ["tiny", "base", "small", "medium", "large"]

    system: Dict[str, Any] = {
        "ffmpeg_configured": bool(_settings.ffmpeg_path),
        "upload_supported": True,
    }

    return {
        "tts_ready": _tts.is_ready(),
        "stt_ready": _stt.is_ready(),
        "stt_adapter": (_settings.stt_adapter or "vosk"),
        "adapter_status": "ready" if _stt.is_ready() else "not_ready",
        "vosk_model_path": _settings.vosk_model_path,
        "whisper_model_name": _settings.whisper_model_name,
        "voice_feedback_enabled": getattr(_settings, "voice_feedback_enabled", True),
        "mood_profile": getattr(_settings, "mood_profile", "neutral"),
        "available_profiles": _mood.available_profiles(),
        "available_models": {
            "whisper": list_whisper_models(),
            "vosk": [],
        },
        "system": system,
    }


@router.post("/config")
def update_voice_config(
    stt_adapter: str | None = Body(None),
    whisper_model_name: str | None = Body(None),
    vosk_model_path: str | None = Body(None),
    voice_feedback_enabled: bool | None = Body(None),
    mood_profile: str | None = Body(None),
):
    # Update in-memory settings and reinitialize STT adapter
    if stt_adapter:
        _settings.stt_adapter = stt_adapter
    if whisper_model_name is not None:
        _settings.whisper_model_name = whisper_model_name
    if vosk_model_path is not None:
        _settings.vosk_model_path = vosk_model_path
    if voice_feedback_enabled is not None:
        _settings.voice_feedback_enabled = bool(voice_feedback_enabled)
    if mood_profile is not None:
        _settings.mood_profile = str(mood_profile)
        try:
            _mood.set_profile(_settings.mood_profile)
        except Exception:
            pass

    global _stt
    if (_settings.stt_adapter or "vosk").lower() == "whisper":
        _stt = WhisperSTT(model_name=_settings.whisper_model_name)
    else:
        _stt = STT(model_path=_settings.vosk_model_path)

    return voice_status()


@router.post("/tts")
def speak(
    text: str = Body(..., embed=True),
    rate: int | None = Body(None),
    volume: float | None = Body(None),
    gender: str | None = Body(None),
    context: str | None = Body(None),
):
    if not _tts.is_ready():
        return {"status": "error", "detail": "TTS engine not available"}
    # Derive defaults from mood engine if not explicitly provided
    if rate is None or volume is None or gender is None:
        params = _mood.tts_params_for(context)
        rate = rate if rate is not None else params.get("rate")
        volume = volume if volume is not None else params.get("volume")
        gender = gender if gender is not None else params.get("gender")
    _tts.speak(text=text, rate=rate, volume=volume, gender=gender)
    return {"status": "ok"}


@router.post("/stt")
def transcribe_pcm16(audio_bytes: bytes = Body(...)):
    text = _stt.transcribe_pcm16(audio_bytes)
    return {"status": "ok", "text": text}


@router.post("/upload_stt")
async def upload_stt(file: UploadFile):
    """Accept WAV/FLAC; convert to PCM16 mono 16kHz; transcribe."""
    data = await file.read()
    ctype = file.content_type or ""
    pcm = None

    def _wav_to_pcm16(bytes_in: bytes) -> bytes:
        try:
            buf = io.BytesIO(bytes_in)
            with wave.open(buf, "rb") as w:
                params = w.getparams()
                if params.sampwidth != 2:
                    return b""
                frames = w.readframes(params.nframes)
                return frames
        except Exception:
            return b""

    if "wav" in ctype:
        pcm = _wav_to_pcm16(data)
    else:
        # Attempt ffmpeg conversion if configured
        if _settings.ffmpeg_path:
            try:
                proc = subprocess.run([
                    _settings.ffmpeg_path,
                    "-hide_banner",
                    "-loglevel", "error",
                    "-i", "-",
                    "-ac", "1",
                    "-ar", "16000",
                    "-f", "s16le",
                    "-",
                ], input=data, capture_output=True)
                if proc.returncode == 0:
                    pcm = proc.stdout
            except Exception:
                pcm = None

    if not pcm:
        return {"status": "error", "detail": "Unsupported format or conversion not configured"}
    text = _stt.transcribe_pcm16(pcm)
    return {"status": "ok", "text": text}


@router.websocket("/stt_ws")
async def stt_stream(ws: WebSocket):
    await ws.accept()
    buf = bytearray()
    try:
        while True:
            msg = await ws.receive()
            mtype = msg.get("type")
            if mtype == "websocket.receive":
                if "bytes" in msg and msg["bytes"] is not None:
                    chunk = msg["bytes"]
                    buf.extend(chunk)
                    # Emit partial transcripts when available
                    try:
                        if hasattr(_stt, "accept_chunk"):
                            partial = _stt.accept_chunk(chunk)  # type: ignore
                            if partial:
                                await ws.send_json({"type": "partial", "text": partial})
                    except Exception:
                        pass
                    await ws.send_json({"type": "progress", "bytes": len(buf)})
                elif "text" in msg and msg["text"] is not None:
                    t = str(msg["text"]).strip().lower()
                    if t == "finish" or t == "stop":
                        try:
                            if hasattr(_stt, "finalize_chunked"):
                                text = _stt.finalize_chunked(bytes(buf))  # type: ignore
                            else:
                                text = _stt.transcribe_pcm16(bytes(buf))
                        except Exception:
                            text = _stt.transcribe_pcm16(bytes(buf))
                        await ws.send_json({"type": "final", "text": text})
                        buf = bytearray()
                    elif t == "reset":
                        buf = bytearray()
                        await ws.send_json({"type": "reset"})
                    else:
                        await ws.send_json({"type": "ack", "text": t})
            elif mtype == "websocket.disconnect":
                break
    except WebSocketDisconnect:
        try:
            await ws.close()
        except Exception:
            pass