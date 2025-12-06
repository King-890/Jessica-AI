def matches_wake_phrase(text: str, phrase: str = "hey jessica") -> bool:
    try:
        t = (text or "").strip().lower()
        p = (phrase or "hey jessica").strip().lower()
        return p in t
    except Exception:
        return False