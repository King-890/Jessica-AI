import asyncio
from typing import Any

from src.configs.settings import settings


async def connect_livekit() -> Any:
    """Connect to LiveKit using configuration from settings.

    This uses dynamic import to avoid hard dependency when the
    `livekit` package isn't installed. When credentials are missing,
    it logs a helpful message and returns None.
    """
    url = settings.livekit_url
    api_key = settings.livekit_api_key
    api_secret = settings.livekit_api_secret

    if not url or not api_key or not api_secret:
        print("LiveKit configuration missing. Set LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET in .env.")
        return None

    try:
        import livekit  # type: ignore
    except Exception:
        print("LiveKit SDK not installed. Install with `pip install livekit` to enable voice.")
        return None

    try:
        room = await livekit.connect(url, api_key, api_secret, "Jessica-Voice")
        print("✅ Jessica connected to LiveKit room.")
        return room
    except Exception as e:
        print(f"Failed to connect to LiveKit: {e}")
        return None


if __name__ == "__main__":
    asyncio.run(connect_livekit())