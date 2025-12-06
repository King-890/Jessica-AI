import time
from typing import Dict

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.configs.settings import Settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings: Settings):
        super().__init__(app)
        self.settings = settings
        self.window_seconds = 60
        self._buckets: Dict[str, Dict[str, float | int]] = {}

    async def dispatch(self, request: Request, call_next):
        # Simple per-client rate limiting based on client host
        client_host = request.client.host if request.client else "unknown"
        now = time.time()
        bucket = self._buckets.get(client_host)
        if not bucket or now - bucket["start"] > self.window_seconds:
            bucket = {"start": now, "count": 0}
            self._buckets[client_host] = bucket
        bucket["count"] = int(bucket["count"]) + 1
        if bucket["count"] > self.settings.rate_limit_per_minute:
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
        return await call_next(request)


class ApiTokenMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings: Settings):
        super().__init__(app)
        self.settings = settings

    async def dispatch(self, request: Request, call_next):
        if self.settings.require_api_token:
            token = request.headers.get("X-API-Token") or request.headers.get("Authorization")
            if token and token.lower().startswith("bearer "):
                token = token.split(" ", 1)[1]
            if not token or token != (self.settings.api_token or ""):
                from fastapi.responses import JSONResponse
                return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        return await call_next(request)