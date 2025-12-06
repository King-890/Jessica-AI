import requests


def handle(intent: str, args: dict | None = None):
    text = (intent or "").lower()
    if "news" in text:
        return "You asked for news. (Stubbed)"
    if "weather" in text:
        city = (args or {}).get("city", "New York")
        return f"Weather for {city} is fair. (Stubbed)"
    return None