from typing import Optional
from src.configs.settings import settings


class LiveKitClient:
    def __init__(self, url: Optional[str] = None, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.url = url or settings.livekit_url
        self.api_key = api_key or settings.livekit_api_key
        self.api_secret = api_secret or settings.livekit_api_secret

    def is_configured(self) -> bool:
        return bool(self.url and self.api_key and self.api_secret)

    def get_config(self) -> dict:
        return {
            "url": self.url,
            "api_key": self.api_key,
            "api_secret": "***" if self.api_secret else None,
            "configured": self.is_configured(),
        }

    # Placeholder: future methods to join room, publish audio, etc.