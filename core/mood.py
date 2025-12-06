class MoodEngine:
    def __init__(self, profile: str | None = None):
        # Profiles define base multipliers for contexts
        self._profiles = {
            "neutral": {"rate_mul": 1.0, "volume_mul": 1.0, "gender": None},
            "confident": {"rate_mul": 1.1, "volume_mul": 1.1, "gender": "male"},
            "empathetic": {"rate_mul": 0.95, "volume_mul": 0.95, "gender": "female"},
            "assistive": {"rate_mul": 1.0, "volume_mul": 1.0, "gender": None},
        }
        self._profile = profile or "neutral"

        # Base mappings per context
        self._base = {
            "error": {"rate": 150, "volume": 0.8},
            "warning": {"rate": 160, "volume": 0.9},
            "success": {"rate": 180, "volume": 1.0},
            "info": {"rate": 170, "volume": 1.0},
            "calm": {"rate": 150, "volume": 0.95},
            "neutral": {"rate": None, "volume": None},
        }

    def set_profile(self, profile: str):
        self._profile = profile if profile in self._profiles else "neutral"

    def get_profile(self) -> str:
        return self._profile

    def available_profiles(self) -> list[str]:
        return list(self._profiles.keys())

    def tts_params_for(self, context: str | None):
        key = str(context or "neutral").lower()
        base = self._base.get(key, self._base["neutral"]) or {}
        prof = self._profiles.get(self._profile, self._profiles["neutral"]) or {}
        rate = base.get("rate")
        vol = base.get("volume")
        # Apply multipliers if base values exist
        if rate is not None:
            rate = int(rate * float(prof.get("rate_mul", 1.0)))
        if vol is not None:
            vol = float(vol) * float(prof.get("volume_mul", 1.0))
        gender = prof.get("gender")
        return {"rate": rate, "volume": vol, "gender": gender}