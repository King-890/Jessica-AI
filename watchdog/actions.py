import re

COMMON_PATTERNS = [
    (
        re.compile(r"NullReferenceException", re.I),
        {
            "title": "Unity NullReferenceException",
            "docs": "https://docs.unity3d.com/ScriptReference/NullReferenceException.html",
            "suggest": "Check for missing component references; add null checks",
            "command": None,
        },
    ),
    (
        re.compile(r"Shader error", re.I),
        {
            "title": "Unity Shader Compilation Error",
            "docs": "https://docs.unity3d.com/Manual/SL-ShaderCompileErrors.html",
            "suggest": "Open shader inspector; fix syntax; verify include paths",
            "command": None,
        },
    ),
    (
        re.compile(r"404|network error|failed to fetch", re.I),
        {
            "title": "Browser Network Error",
            "docs": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404",
            "suggest": "Verify URL, CORS, and server availability",
            "command": None,
        },
    ),
]


def suggest_actions_for_events(events):
    suggestions = []
    for e in events:
        msg = e.get("message", "")
        for pat, rec in COMMON_PATTERNS:
            if pat.search(msg):
                suggestions.append({"event": e, "recommendation": rec})
                break
    return suggestions