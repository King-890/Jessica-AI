import asyncio
import psutil
import time
from fastapi import APIRouter
from starlette.responses import StreamingResponse


router = APIRouter(prefix="/performance", tags=["performance"])


@router.get("/stream")
async def performance_stream():
    async def gen():
        try:
            while True:
                cpu = float(psutil.cpu_percent(interval=None))
                mem = float(psutil.virtual_memory().percent)
                diskio = psutil.disk_io_counters()
                payload = {
                    "timestamp": time.time(),
                    "cpu": cpu,
                    "ram": mem,
                    "disk": {
                        "read_bytes": int(getattr(diskio, "read_bytes", 0)),
                        "write_bytes": int(getattr(diskio, "write_bytes", 0)),
                    },
                }
                import json
                yield f"data: {json.dumps(payload)}\n\n"
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
    return StreamingResponse(gen(), media_type="text/event-stream")