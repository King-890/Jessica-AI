import os
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

router = APIRouter()


@router.websocket("/ws/terminal")
async def ws_terminal(websocket: WebSocket):
    await websocket.accept()
    proc = None
    try:
        start_msg = await websocket.receive_text()
        try:
            data = json.loads(start_msg)
        except Exception:
            await websocket.send_json({"type": "error", "message": "Invalid JSON"})
            await websocket.close()
            return
        if data.get("type") != "start":
            await websocket.send_json({"type": "error", "message": "First message must be 'start'"})
            await websocket.close()
            return
        command = (data.get("command") or "").lower()
        args = data.get("args") or []

        if command == "python":
            if not args:
                await websocket.send_json({"type": "error", "message": "Missing script path"})
                await websocket.close()
                return
            target = os.path.abspath(os.path.join(BASE_DIR, args[0]))
            if os.path.commonpath([target, BASE_DIR]) != BASE_DIR:
                await websocket.send_json({"type": "error", "message": "Forbidden path"})
                await websocket.close()
                return
            if not os.path.isfile(target):
                await websocket.send_json({"type": "error", "message": "Script not found"})
                await websocket.close()
                return
            proc = await asyncio.create_subprocess_exec(
                "python", target, *args[1:],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        elif command in {"echo", "dir"}:
            cmdline = " ".join([command] + args)
            proc = await asyncio.create_subprocess_shell(
                cmdline,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        else:
            await websocket.send_json({"type": "error", "message": "Unsupported command"})
            await websocket.close()
            return

        async def reader(stream, tag):
            while True:
                chunk = await stream.read(1024)
                if not chunk:
                    break
                try:
                    await websocket.send_json({"type": tag, "data": chunk.decode(errors="ignore")})
                except Exception:
                    break

        await asyncio.gather(reader(proc.stdout, "stdout"), reader(proc.stderr, "stderr"))
        rc = await proc.wait()
        await websocket.send_json({"type": "exit", "code": rc})
    except WebSocketDisconnect:
        if proc and proc.returncode is None:
            try:
                proc.kill()
            except Exception:
                pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
        try:
            await websocket.close()
        except Exception:
            pass