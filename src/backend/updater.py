import asyncio
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def update_jessica() -> tuple[bool, str]:
    """Run `git pull` in the project root. Returns (success, output)."""
    try:
        result = subprocess.run(
            ["git", "pull"],
            cwd=PROJECT_ROOT.as_posix(),
            capture_output=True,
            text=True,
            check=False,
        )
        output = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
        success = result.returncode == 0
        if not success:
            print(f"[AutoUpdate] git pull failed (code {result.returncode}):\n{output}")
        else:
            print(f"[AutoUpdate] git pull succeeded:\n{output}")
        return success, output.strip()
    except Exception as e:
        msg = f"[AutoUpdate] git pull error: {e}"
        print(msg)
        return False, msg


async def run_periodic_updates(interval_hours: int = 24) -> None:
    """Periodically run update_jessica every interval_hours."""
    seconds = max(1, int(interval_hours * 3600))
    while True:
        update_jessica()
        await asyncio.sleep(seconds)