import asyncio
import json
from typing import List
from fastapi import APIRouter
from starlette.responses import StreamingResponse


router = APIRouter(prefix="/logs", tags=["logs"])

_subscribers: List[asyncio.Queue] = []
_history: List[str] = []


def publish_log_event(event: dict):
    try:
        payload = json.dumps(event)
        # Keep a simple capped history for /logs retrieval
        try:
            _history.append(payload)
            if len(_history) > 200:
                del _history[: len(_history) - 200]
        except Exception:
            pass
        for q in list(_subscribers):
            try:
                q.put_nowait(payload)
            except Exception:
                continue
    except Exception:
        pass


@router.get("/stream")
async def stream():
    queue: asyncio.Queue = asyncio.Queue()
    _subscribers.append(queue)

    async def eventgen():
        try:
            while True:
                data = await queue.get()
                yield f"data: {data}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            try:
                _subscribers.remove(queue)
            except Exception:
                pass

    return StreamingResponse(eventgen(), media_type="text/event-stream")


@router.get("")
async def recent_logs():
    # Return last 50 log lines (JSON strings)
    try:
        return _history[-50:]
    except Exception:
        return []