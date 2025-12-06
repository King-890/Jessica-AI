import webbrowser
import subprocess


def handle(intent: str, args: dict | None = None):
    text = (intent or "").lower()
    if "open browser" in text or "launch browser" in text:
        try:
            webbrowser.open("https://www.google.com")
            return "Opening browser"
        except Exception as e:
            return f"Failed to open browser: {e}"
    if "open vscode" in text or "open code" in text:
        try:
            subprocess.Popen(["code"], shell=True)
            return "Opening VS Code"
        except Exception as e:
            return f"Failed to open VS Code: {e}"
    return None