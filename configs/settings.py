import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    host: str = os.getenv("API_HOST", "127.0.0.1")
    port: int = int(os.getenv("API_PORT", "5050"))
    enforce_local_only: bool = os.getenv("ENFORCE_LOCAL_ONLY", "true").lower() == "true"
    allowed_origins: list[str] = [
        "http://127.0.0.1",
        "http://localhost",
        "http://localhost:5173",
        "http://localhost:5174",
    ]

    # Google CSE configuration
    google_cse_api_key: str | None = os.getenv("GOOGLE_CSE_API_KEY")
    google_cse_cx: str | None = os.getenv("GOOGLE_CSE_CX")

    # Tauri integration placeholders
    tauri_enabled: bool = os.getenv("TAURI_ENABLED", "false").lower() == "true"
    tauri_auto_start: bool = os.getenv("TAURI_AUTO_START", "false").lower() == "true"

    # LiveKit configuration
    livekit_url: str | None = os.getenv("LIVEKIT_URL")
    livekit_api_key: str | None = os.getenv("LIVEKIT_API_KEY")
    livekit_api_secret: str | None = os.getenv("LIVEKIT_API_SECRET")

    # Security / API token and rate limiting
    require_api_token: bool = os.getenv("REQUIRE_API_TOKEN", "false").lower() == "true"
    api_token: str | None = os.getenv("API_TOKEN")
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))

    # Watchdog toggle
    enable_watchdog: bool = os.getenv("ENABLE_WATCHDOG", "true").lower() == "true"

    # Auto updater settings
    enable_auto_update: bool = os.getenv("ENABLE_AUTO_UPDATE", "false").lower() == "true"
    auto_update_interval_hours: int = int(os.getenv("AUTO_UPDATE_INTERVAL_HOURS", "24"))
    enable_cron_update: bool = os.getenv("ENABLE_CRON_UPDATE", "false").lower() == "true"
    cron_update_expression: str = os.getenv("CRON_UPDATE_EXPRESSION", "0 3 * * *")

    # STT model path (Vosk)
    vosk_model_path: str | None = os.getenv("VOSK_MODEL_PATH")

    # STT adapter selection: 'vosk' or 'whisper'
    stt_adapter: str = os.getenv("STT_ADAPTER", "vosk")
    whisper_model_name: str = os.getenv("WHISPER_MODEL_NAME", "base")

    # Browser DevTools remote port
    browser_devtools_port: int = int(os.getenv("BROWSER_DEVTOOLS_PORT", "9222"))

    # Optional ffmpeg path for audio conversion
    ffmpeg_path: str | None = os.getenv("FFMPEG_PATH")

    # Voice event feedback toggle
    voice_feedback_enabled: bool = os.getenv("VOICE_FEEDBACK_ENABLED", "true").lower() == "true"

    # Voice wake-word listener toggle
    enable_voice_mode: bool = os.getenv("ENABLE_VOICE_MODE", "false").lower() == "true"

    # Mood profile selection (e.g., neutral, confident, empathetic, assistive)
    mood_profile: str = os.getenv("MOOD_PROFILE", "neutral")

    # Knowledge auto-update toggle and interval
    enable_knowledge_auto_update: bool = os.getenv("ENABLE_KNOWLEDGE_AUTO_UPDATE", "false").lower() == "true"
    knowledge_auto_update_interval_hours: int = int(os.getenv("KNOWLEDGE_AUTO_UPDATE_INTERVAL_HOURS", "12"))

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Instantiate settings for modules that import a singleton
settings = Settings()