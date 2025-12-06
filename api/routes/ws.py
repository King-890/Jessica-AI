from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from core.llm_engine import LLMEngine
from memory.store import MemoryStore
import json
import time


router = APIRouter()
engine = LLMEngine()
memory = MemoryStore()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    # Initial status message
    await ws.send_json({"type": "status", "message": "connected"})
    try:
        last_ping = time.time()
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            mtype = msg.get("type")
            payload = msg.get("payload")

            if mtype == "heartbeat":
                last_ping = time.time()
                await ws.send_json({"type": "heartbeat", "message": "pong"})
                continue

            if mtype == "chat":
                text = str(payload or "")
                memory.log_command(text)
                memory.add_message("user", text)
                history = memory.recent_history(limit=20)
                output = engine.generate_with_context(text, history)
                memory.add_message("assistant", output)
                await ws.send_json({"type": "chat", "input": text, "output": output})
                continue

            if mtype == "command":
                # Placeholder routing for system commands; implemented via HTTP API in Phase 2
                await ws.send_json({"type": "command", "status": "unsupported_in_ws"})
                continue

            await ws.send_json({"type": "error", "message": "Unknown message type"})
    except WebSocketDisconnect:
        # Best-effort closing
        try:
            await ws.close()
        except Exception:
            pass