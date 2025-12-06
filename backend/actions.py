import subprocess
import webbrowser
import os


def open_unity_hub():
    try:
        subprocess.Popen(["Unity Hub"], shell=True)
        return {"ok": True, "message": "Opening Unity Hub..."}
    except Exception as e:
        return {"ok": False, "message": f"Failed to open Unity Hub: {e}"}


def open_vscode(path: str = ""):
    try:
        cmd = ["code"] + ([path] if path else [])
        subprocess.Popen(cmd, shell=True)
        return {"ok": True, "message": f"Opening VS Code {path or ''}"}
    except Exception as e:
        return {"ok": False, "message": f"Failed to open VS Code: {e}"}


def open_youtube(query: str = ""):
    try:
        url = "https://www.youtube.com" if not query else f"https://www.youtube.com/results?search_query={query}"
        webbrowser.open(url)
        return {"ok": True, "message": f"Opening YouTube {('search ' + query) if query else ''}"}
    except Exception as e:
        return {"ok": False, "message": f"Failed to open YouTube: {e}"}


def execute(text: str):
    t = text.lower()
    if "open unity" in t or "unity hub" in t:
        return open_unity_hub()
    if "open code" in t or "open vscode" in t or "vs code" in t:
        return open_vscode()
    if "open youtube" in t or "youtube" in t:
        return open_youtube()
    return None