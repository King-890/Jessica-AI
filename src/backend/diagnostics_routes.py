import psutil
import time
from fastapi import APIRouter
from .vector_memory import count as vector_count, last_update_time


router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])


@router.get("/run")
async def run_diagnostics():
    """Return current system diagnostics snapshot."""
    try:
        cpu = float(psutil.cpu_percent(interval=None))
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        disk = psutil.disk_usage("/")
        net = psutil.net_io_counters()
        procs = len(list(psutil.process_iter()))
    except Exception:
        cpu = 0.0
        mem = type("obj", (), {"percent": 0.0, "total": 0, "available": 0})()
        swap = type("obj", (), {"percent": 0.0})()
        disk = type("obj", (), {"percent": 0.0})()
        net = type("obj", (), {"bytes_sent": 0, "bytes_recv": 0})()
        procs = 0

    vm_count = 0
    last_know = 0.0
    try:
        vm_count = int(vector_count())
        last_know = float(last_update_time() or 0)
    except Exception:
        pass

    anomalies = []
    if cpu >= 90.0:
        anomalies.append({"type": "cpu_high", "value": cpu, "threshold": 90.0})
    if float(mem.percent) >= 90.0:
        anomalies.append({"type": "mem_high", "value": float(mem.percent), "threshold": 90.0})

    return {
        "timestamp": time.time(),
        "system": {
            "cpu_percent": cpu,
            "memory_percent": float(mem.percent),
            "swap_percent": float(getattr(swap, "percent", 0.0)),
            "disk_percent": float(getattr(disk, "percent", 0.0)),
            "net_bytes_sent": int(getattr(net, "bytes_sent", 0)),
            "net_bytes_recv": int(getattr(net, "bytes_recv", 0)),
            "process_count": procs,
        },
        "vector_memory_count": vm_count,
        "knowledge_last_update": last_know,
        "anomalies": anomalies,
    }