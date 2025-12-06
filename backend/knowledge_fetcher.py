import asyncio
import time
from typing import List
import requests

from configs.settings import settings
from .vector_memory import store_interaction


def _google_cse(query: str) -> dict | None:
    cx = settings.google_cse_cx
    key = settings.google_cse_api_key
    if not cx or not key:
        return None
    url = f"https://www.googleapis.com/customsearch/v1?q={requests.utils.quote(query)}&cx={cx}&key={key}"
    try:
        return requests.get(url, timeout=10).json()
    except Exception:
        return None


def _summarize_items(items: list[dict]) -> str:
    # Lightweight summarization: join top snippets
    snippets = [it.get("snippet", "") for it in items]
    summary = " ".join([s for s in snippets if s][:5]).strip()
    return summary or "No summary available."


def _domain_tag(url: str | None) -> str:
    if not url:
        return "general"
    u = url.lower()
    if any(k in u for k in ["ai", "ml", "openai", "deepmind"]):
        return "AI"
    if any(k in u for k in ["science", "nature.com", "sciencemag"]):
        return "science"
    if any(k in u for k in ["tech", "theverge", "techcrunch"]):
        return "tech"
    return "general"


async def perform_update(queries: List[str] | None = None):
    """Pull and summarize knowledge via Google CSE and store into vector memory."""
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    queries = queries or [
        "AI research breakthroughs",
        "Latest technology trends",
        "Scientific discoveries today",
    ]
    for q in queries:
        data = _google_cse(q)
        if not data:
            # Store placeholder when CSE not configured
            try:
                store_interaction(prompt=f"[knowledge] {ts} {q}", response="CSE not configured.", tags=["knowledge", "general"])  # type: ignore
            except Exception:
                continue
            continue
        items = data.get("items", [])
        summary = _summarize_items(items)
        # Tag by first item domain
        tag = _domain_tag(items[0].get("link") if items else None)
        try:
            store_interaction(prompt=f"[knowledge] {q}", response=summary, tags=["knowledge", tag])  # type: ignore
        except Exception:
            continue


async def run_knowledge_updates(interval_hours: int = 12):
    while True:
        try:
            await perform_update()
        except Exception:
            pass
        await asyncio.sleep(max(1, int(interval_hours * 3600)))