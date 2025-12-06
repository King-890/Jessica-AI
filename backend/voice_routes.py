import time
import base64
from fastapi import APIRouter, Request
import os
import yaml
import json
import concurrent.futures
from memory.store import MemoryStore

try:
    import speech_recognition as sr  # type: ignore
except Exception:
    sr = None


router = APIRouter(prefix="/voice", tags=["voice"])


def _load_voice_cfg():
    try:
        with open(os.path.join("configs", "voice_settings.yaml"), "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


@router.get("/status")
async def voice_status():
    cfg = _load_voice_cfg()
    wake_phrase = cfg.get("wake_phrase", "hey jessica")
    adapter = cfg.get("stt_adapter", "speech_recognition")
    whisper_model = cfg.get("whisper_model", "base")
    mic_active = False
    try:
        mic_active = sr is not None
    except Exception:
        mic_active = False

    # Placeholders for latencies; actual probes can be added later
    stt_latency_ms = None
    tts_latency_ms = None

    return {
        "microphone_active": mic_active,
        "wake_phrase": wake_phrase,
        "stt_adapter": adapter,
        "whisper_model": whisper_model,
        "stt_latency_ms": stt_latency_ms,
        "tts_latency_ms": tts_latency_ms,
        "wake_phrase_accuracy": None,
    }


@router.post("/transcribe")
async def transcribe(payload: dict):
    """Transcribe base64 PCM16 mono 16kHz audio via configured STT engine."""
    from configs.settings import settings
    from audio.stt import STT
    from audio.stt_whisper import WhisperSTT

    audio_b64 = payload.get("audio_base64") or ""
    if not audio_b64:
        return {"text": "", "error": "missing audio_base64"}
    try:
        audio_bytes = base64.b64decode(audio_b64)
    except Exception:
        return {"text": "", "error": "invalid base64"}

    engine_name = (settings.stt_adapter or "vosk").lower()
    if engine_name == "whisper":
        engine = WhisperSTT(model_name=settings.whisper_model_name)
    else:
        engine = STT(model_path=settings.vosk_model_path)

    if not engine.is_ready():
        return {"text": "", "error": "stt-not-configured"}
    # Retry + timeout control
    try:
        max_retries = int(os.getenv("STT_MAX_RETRIES", "2"))
    except Exception:
        max_retries = 2
    try:
        timeout_seconds = float(os.getenv("STT_TIMEOUT_SECONDS", "12"))
    except Exception:
        timeout_seconds = 12.0

    last_text = ""
    last_err = None
    for attempt in range(max_retries + 1):
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                fut = pool.submit(engine.transcribe_pcm16, audio_bytes)
                text = fut.result(timeout=timeout_seconds)
            last_text = text or ""
            return {"text": last_text, "error": None}
        except concurrent.futures.TimeoutError as e:
            last_err = "stt-timeout"
        except Exception as e:
            last_err = "stt-error"
        # brief backoff
        time.sleep(0.2)

    return {"text": last_text, "error": last_err or "stt-failed"}


@router.post("/command")
async def voice_command(payload: dict):
    """Execute a text command via Jessica core and return response."""
    from .ai_core import jessica_core
    memory = MemoryStore()

    text = (payload.get("text") or "").strip()
    if not text:
        return {"response": ""}
    try:
        # Log and capture conversation
        memory.log_command(text)
        memory.add_message("user", text)

        # Build lightweight context from recent history
        history = memory.recent_history(limit=20)
        context_lines = [f"- {c[:300]}" for role, c in history if c]
        context_blob = "\n".join(context_lines)
        enriched = text if not context_blob else f"{text}\n\nRecent context:\n{context_blob}"

        result = jessica_core(enriched)
        if isinstance(result, dict):
            # If core returns structured response, still record
            memory.add_message("assistant", json.dumps(result))
            return result
        out = str(result)
        memory.add_message("assistant", out)
        return {"response": out}
    except Exception:
        return {"response": ""}