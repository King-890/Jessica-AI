try:
    import pyttsx3
except Exception:  # pragma: no cover
    pyttsx3 = None


def speak(text: str) -> None:
    """Speak text using pyttsx3; fails gracefully if unavailable.

    Rate is set to ~175 wpm for a balanced cadence.
    """
    if not text:
        return
    if pyttsx3 is None:
        print(f"[TTS disabled] {text}")
        return
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 175)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:  # pragma: no cover
        print(f"TTS error: {e}")