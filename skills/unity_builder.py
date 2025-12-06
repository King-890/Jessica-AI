def handle(prompt: str):
    text = (prompt or "").lower()
    if "build unity" in text or "unity builder" in text:
        return "Unity Builder skill engaged: starting build pipeline (stub)."
    return None