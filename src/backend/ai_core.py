from datetime import datetime
import re
import requests
try:
    from duckduckgo_search import DDGS  # type: ignore
    _has_ddg = True
except Exception:
    DDGS = None  # type: ignore
    _has_ddg = False

from src.configs.settings import settings
from .actions import execute as execute_action
from .skill_loader import load_skills
import importlib, json, os
import json as _json


def google_search(query: str) -> str:
    """Web search helper with Google CSE and DDG fallback.

    Outputs a concise, structured summary followed by sources.
    """
    cx = settings.google_cse_cx
    key = settings.google_cse_api_key
    items = []
    provider = "google"

    if cx and key:
        url = f"https://www.googleapis.com/customsearch/v1?q={requests.utils.quote(query)}&cx={cx}&key={key}"
        try:
            data = requests.get(url, timeout=10).json()
            items = [
                {
                    "title": it.get("title", ""),
                    "link": it.get("link", ""),
                    "snippet": it.get("snippet", ""),
                }
                for it in (data.get("items", []) or [])
            ]
        except Exception:
            items = []

    # Fallback to DDG when Google unavailable or returned no items
    if not items and _has_ddg:
        provider = "ddg"
        try:
            with DDGS() as ddgs:  # type: ignore
                ddg_items = list(ddgs.text(query, max_results=5))
            items = [
                {
                    "title": it.get("title", ""),
                    "link": it.get("href", ""),
                    "snippet": it.get("body", ""),
                }
                for it in ddg_items
            ]
        except Exception:
            items = []

    if not items:
        msg = "No results found."
        if not (cx and key):
            msg += " Google CSE not configured; set GOOGLE_CSE_API_KEY and GOOGLE_CSE_CX."
        return msg

    # Build concise summary (top 3 bullets) and sources list
    top = items[:3]
    bullets = [f"- {i['snippet'].strip()}" for i in top if i.get('snippet')]
    sources = [f"[{i['title']}]({i['link']})" for i in items[:5] if i.get('link')]

    summary = (
        f"Search provider: {provider}\n"
        + ("\n".join(bullets) if bullets else "- Relevant information found.")
        + ("\n\nSources: " + "; ".join(sources) if sources else "")
    )
    return summary


_skills = load_skills()


def jessica_core(prompt: str) -> str:
    """Simple local reasoning with optional web search support."""
    text = (prompt or "").lower()

    # 0) Action execution layer short-circuit
    try:
        act_resp = execute_action(text)
        if act_resp:
            return act_resp
    except Exception:
        pass

    if "search" in text:
        query = re.sub(r"^\s*search\s*", "", prompt or "", flags=re.I)
        return google_search(query or "")
    if "time" in text:
        return f"The current time is {datetime.now().strftime('%H:%M:%S')}."
    if "build unity map" in text:
        return "Opening Unity Hub and preparing the map generator pipeline..."
    # 3) Skill routing: attempt each loaded skill until one handles
    for name, mod in _skills.items():
        try:
            handle = getattr(mod, "handle", None)
            if callable(handle):
                out = handle(prompt)
                if out:
                    return out
        except Exception:
            continue
    # 4) Voice intents mapping
    try:
        with open(os.path.join("configs", "voice_intents.json"), "r", encoding="utf-8") as f:
            intents = _json.load(f)
        for it in intents.get("intents", []):
            kws = [str(k).lower() for k in it.get("keywords", [])]
            if any(k in text for k in kws):
                route = it.get("route")
                try:
                    mod = importlib.import_module(route)
                    handle = getattr(mod, "handle", None)
                    if callable(handle):
                        out = handle(prompt, {})
                        if out:
                            return out
                except Exception:
                    continue
    except Exception:
        pass
    # Fallback
    return "Jessica is thinking... this is your local core response."