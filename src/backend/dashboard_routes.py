import asyncio
import psutil
import time
from fastapi import APIRouter
from starlette.responses import StreamingResponse
from .vector_memory import count as vector_count, last_update_time


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/metrics")
async def metrics_stream():
    async def gen():
        try:
            while True:
                cpu = float(psutil.cpu_percent(interval=None))
                mem = float(psutil.virtual_memory().percent)
                net = psutil.net_io_counters()
                vmc = 0
                last = 0.0
                try:
                    vmc = int(vector_count())
                    last = float(last_update_time() or 0)
                except Exception:
                    pass
                payload = {
                    "timestamp": time.time(),
                    "cpu": cpu,
                    "ram": mem,
                    "net": {
                        "sent": int(getattr(net, "bytes_sent", 0)),
                        "recv": int(getattr(net, "bytes_recv", 0)),
                    },
                    "vector_count": vmc,
                    "knowledge_last_update": last,
                }
                import json
                yield f"data: {json.dumps(payload)}\n\n"
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            pass
    return StreamingResponse(gen(), media_type="text/event-stream")