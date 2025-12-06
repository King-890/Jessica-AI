def handle(intent: str, args: dict | None = None):
    text = (intent or "").lower()
    if "unity" in text:
        return "Preparing Unity build pipeline..."
    return None