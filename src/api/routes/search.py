from fastapi import APIRouter, Query, HTTPException
import requests
from src.configs.settings import settings
try:
    from duckduckgo_search import DDGS  # type: ignore
    _has_ddg = True
except Exception:
    DDGS = None  # type: ignore
    _has_ddg = False


# Define router without a prefix; internal_api mounts it under /search
router = APIRouter(tags=["search"])


@router.get("/google")
def google_search(q: str = Query(..., min_length=1), num: int = 5):
    if not settings.google_cse_api_key or not settings.google_cse_cx:
        raise HTTPException(status_code=400, detail="Google CSE is not configured")

    params = {
        "key": settings.google_cse_api_key,
        "cx": settings.google_cse_cx,
        "q": q,
        "num": max(1, min(num, 10)),
        "safe": "active",
    }
    try:
        resp = requests.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Search request failed: {e}")

    items = data.get("items", [])
    results = []
    for it in items:
        results.append({
            "title": it.get("title"),
            "link": it.get("link"),
            "snippet": it.get("snippet"),
        })
    return {"query": q, "results": results}


@router.get("/web")
def web_search(q: str = Query(..., min_length=1), num: int = 5, provider: str = "auto"):
    """Provider-agnostic search endpoint.

    - provider="google" forces Google CSE (requires env keys)
    - provider="ddg" forces DuckDuckGo
    - provider="auto" uses Google if configured, otherwise DDG
    """
    provider = (provider or "auto").lower().strip()
    num = max(1, min(int(num or 5), 10))

    # Prefer Google when requested or when auto and configured
    use_google = (
        provider == "google" or (
            provider == "auto" and settings.google_cse_api_key and settings.google_cse_cx
        )
    )

    if use_google:
        params = {
            "key": settings.google_cse_api_key,
            "cx": settings.google_cse_cx,
            "q": q,
            "num": num,
            "safe": "active",
        }
        try:
            resp = requests.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            # If Google fails and auto mode, attempt DDG fallback
            if provider == "auto" and _has_ddg:
                return _ddg_results(q, num)
            raise HTTPException(status_code=502, detail=f"Search request failed: {e}")

        items = data.get("items", [])
        results = []
        for it in items:
            results.append({
                "title": it.get("title"),
                "link": it.get("link"),
                "snippet": it.get("snippet"),
                "provider": "google",
            })
        return {"query": q, "results": results}

    # DDG path
    if provider in ("ddg", "auto"):
        if not _has_ddg:
            raise HTTPException(status_code=400, detail="DuckDuckGo library not available")
        return _ddg_results(q, num)

    raise HTTPException(status_code=400, detail="Unknown provider. Use 'auto', 'google', or 'ddg'.")


def _ddg_results(q: str, num: int):
    try:
        with DDGS() as ddgs:  # type: ignore
            items = list(ddgs.text(q, max_results=num))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"DDG search failed: {e}")
    results = []
    for it in items:
        results.append({
            "title": it.get("title"),
            "link": it.get("href"),
            "snippet": it.get("body"),
            "provider": "ddg",
        })
    return {"query": q, "results": results}