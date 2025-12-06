from typing import Dict, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .ai_core import jessica_core


router = APIRouter(prefix="/ide", tags=["ide"])


# In-memory collaboration rooms (simple broadcast). Not for production use.
_rooms: Dict[str, List[WebSocket]] = {}
_buffers: Dict[str, str] = {}


@router.post("/assist")
async def assist(payload: dict):
    """AI-powered assistance for code generation/optimization.

    Body: { "prompt": str, "language": str|None, "context": str|None }
    Returns: { suggestion: str }
    """
    prompt = str(payload.get("prompt") or "").strip()
    language = str(payload.get("language") or "").strip()
    context = str(payload.get("context") or "").strip()

    enriched = prompt
    if language:
        enriched = f"Language: {language}\n\n{enriched}"
    if context:
        enriched = f"Context:\n{context}\n\n{enriched}"

    try:
        out = jessica_core(enriched)
        return {"suggestion": str(out)}
    except Exception as e:
        return {"suggestion": f"Assistant unavailable: {e}"}


@router.websocket("/ws")
async def collab_ws(ws: WebSocket, room: str = "default"):
    await ws.accept()
    peers = _rooms.setdefault(room, [])
    if ws not in peers:
        peers.append(ws)
    # Send current buffer if any
    buf = _buffers.get(room, "")
    await ws.send_json({"type": "sync", "buffer": buf})
    try:
        while True:
            msg = await ws.receive_json()
            mtype = msg.get("type")
            if mtype == "change":
                text = str(msg.get("buffer") or "")
                _buffers[room] = text
                # Broadcast change
                dead: List[WebSocket] = []
                for p in peers:
                    if p is ws:
                        continue
                    try:
                        await p.send_json({"type": "change", "buffer": text})
                    except Exception:
                        dead.append(p)
                for d in dead:
                    try:
                        peers.remove(d)
                    except Exception:
                        pass
            elif mtype == "cursor":
                # Broadcast cursor position metadata
                pos = msg.get("pos")
                user = msg.get("user")
                for p in peers:
                    if p is ws:
                        continue
                    try:
                        await p.send_json({"type": "cursor", "user": user, "pos": pos})
                    except Exception:
                        pass
            else:
                await ws.send_json({"type": "error", "message": "Unknown message type"})
    except WebSocketDisconnect:
        try:
            peers.remove(ws)
        except Exception:
            pass
    except Exception:
        try:
            peers.remove(ws)
        except Exception:
            pass