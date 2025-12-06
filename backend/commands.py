import os
import subprocess
import webbrowser


def execute_command(text: str):
    """Map simple natural language commands to local actions.

    Returns a user-facing status string when a command is handled,
    otherwise returns None to allow upstream handling.
    """
    if not text:
        return None
    t = text.lower()

    if "open unity" in t:
        path = r"C:\\Program Files\\Unity Hub\\Unity Hub.exe"
        try:
            subprocess.Popen([path])
            return "Opening Unity Hub..."
        except Exception:
            return "Failed to open Unity Hub (not installed or path incorrect)."

    if "open vscode" in t or "open vs code" in t:
        try:
            subprocess.Popen(["code"])  # relies on VSCode in PATH
            return "Opening VS Code..."
        except Exception:
            return "Failed to open VS Code (ensure 'code' is in PATH)."

    if "open youtube" in t or "open youtube.com" in t:
        try:
            webbrowser.open("https://youtube.com")
            return "Opening YouTube..."
        except Exception:
            return "Failed to open YouTube in browser."

    return None