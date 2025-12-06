from fastapi import APIRouter

from watchdog.worker import watchdog_singleton
from data.db import list_watchdog_events
from watchdog.actions import suggest_actions_for_events

router = APIRouter(prefix="/watchdog", tags=["watchdog"])


@router.get("/status")
def status():
    return {"status": "ok", "snapshot": watchdog_singleton.snapshot()}


@router.get("/events")
def events(limit: int = 50):
    rows = list_watchdog_events(limit)
    events = [
        {
            "id": r[0],
            "source": r[1],
            "level": r[2],
            "message": r[3],
            "metadata_json": r[4],
            "ts": r[5],
        }
        for r in rows
    ]
    return {
        "status": "ok",
        "events": events,
    }


@router.get("/suggest")
def suggest(limit: int = 50):
    rows = list_watchdog_events(limit)
    events = [
        {"source": r[1], "level": r[2], "message": r[3]} for r in rows
    ]
    suggestions = suggest_actions_for_events(events)
    return {"status": "ok", "suggestions": suggestions}