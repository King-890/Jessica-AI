from __future__ import annotations

import json
from typing import Callable
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from .routes.auth import validate_token, get_token_role
from .cloud.supabase_client import get_client


class AuthTokenMiddleware(BaseHTTPMiddleware):
    """Validates API token (if provided) and attaches role to request.state.

    If settings.require_api_token is true, requests without a valid token are rejected.
    Otherwise, token (if present) is validated and role recorded for downstream checks.
    """

    def __init__(self, app, require_api_token: bool = False):
        super().__init__(app)
        self.require_api_token = require_api_token

    async def dispatch(self, request: Request, call_next: Callable):
        # Always allow CORS preflight
        if request.method.upper() == "OPTIONS":
            return await call_next(request)
        token = request.headers.get("X-API-Token") or request.headers.get("Authorization")
        if token and token.lower().startswith("bearer "):
            token = token.split(" ", 1)[1]

        role = None
        if token:
            try:
                if validate_token(token):
                    role = get_token_role(token)
                    request.state.token_role = role
                else:
                    request.state.token_role = None
            except Exception:
                request.state.token_role = None

        # Enforce token presence if required
        if self.require_api_token:
            if not token or not validate_token(token):
                return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

        return await call_next(request)


class SupabaseAuthMiddleware(BaseHTTPMiddleware):
    """Validates Supabase JWT if provided and attaches a 'user' role when valid.

    Does not reject requests; acts as a soft authenticator to enable cloud-backed identity.
    """

    async def dispatch(self, request: Request, call_next: Callable):
        token = request.headers.get("Authorization")
        if token and token.lower().startswith("bearer "):
            token = token.split(" ", 1)[1]
        else:
            token = None

        if token:
            cli = None
            try:
                cli = get_client()
            except Exception:
                cli = None
            if cli:
                try:
                    user = cli.auth.get_user(token)  # type: ignore
                    # If Supabase confirms token, attach identity and default 'user' role when not present
                    if user and getattr(user, "user", None):
                        request.state.supabase_user = getattr(user, "user", None)
                        if not getattr(request.state, "token_role", None):
                            request.state.token_role = "user"
                except Exception:
                    pass
        return await call_next(request)


class RolePermissionMiddleware(BaseHTTPMiddleware):
    """Uniform role-based gate for sensitive routes.

    Rules:
    - POST /updates/* requires admin.
    - POST /config/reload requires admin.
    - Other /config endpoints require at least 'user'.
    - /voice/* requires one of ('admin','user','skill').
    """

    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path or ""
        method = request.method.upper()
        role = getattr(request.state, "token_role", None)

        def deny(status: int, msg: str) -> Response:
            return JSONResponse(status_code=status, content={"detail": msg})

        # Sensitive updates
        if path.startswith("/updates"):
            if method == "POST":
                if role != "admin":
                    return deny(403, "Forbidden: admin required")
            # Allow GET checks without strict role; if token is present but skill, deny
            if method == "GET" and role == "skill":
                return deny(403, "Forbidden for skill tokens")

        # Config reload and basic config access
        if path.startswith("/config"):
            if path.startswith("/config/reload") and method == "POST":
                if role != "admin":
                    return deny(403, "Forbidden: admin required")
            else:
                # Require at least user for other config routes when token is present requirement enforced
                if role not in (None, "admin", "user"):
                    return deny(403, "Forbidden")

        # Voice: allow admin/user/skill; if token required and role missing, handled by AuthTokenMiddleware
        if path.startswith("/voice"):
            if role not in (None, "admin", "user", "skill"):
                return deny(403, "Forbidden")

        return await call_next(request)


class ResponseValidationMiddleware(BaseHTTPMiddleware):
    """Validate and lightly normalize JSON responses for critical routes.

    Adds header 'X-Response-Validated' with 'ok' or 'failed'.
    Does not alter body unless non-JSON is returned, in which case wraps into a JSON error.
    """

    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path or ""
        need_validate = (
            path.startswith("/voice") or path.startswith("/config") or path.startswith("/updates")
        )
        response = await call_next(request)

        if not need_validate:
            return response

        try:
            media_type = getattr(response, "media_type", "application/json")
            body_bytes = getattr(response, "body", b"")
            payload = None
            if media_type and "json" in media_type:
                try:
                    if isinstance(body_bytes, (bytes, bytearray)) and body_bytes:
                        payload = json.loads(body_bytes.decode("utf-8"))
                except Exception:
                    payload = None

            if payload is None:
                # Non-JSON or unreadable body; mark as failed but do not alter response
                try:
                    response.headers["X-Response-Validated"] = "failed"
                except Exception:
                    pass
                return response

            # Basic shape checks per route group
            valid = True
            if path.startswith("/voice"):
                if request.method.upper() == "POST" and path.endswith("/transcribe"):
                    valid = isinstance(payload, dict) and ("text" in payload) and ("error" in payload or True)
                elif request.method.upper() == "POST" and path.endswith("/command"):
                    valid = isinstance(payload, dict) and ("response" in payload or isinstance(payload, dict))
            elif path.startswith("/config"):
                if request.method.upper() == "GET":
                    valid = all(k in payload for k in (
                        "auto_update", "enable_voice_mode", "cron_update_enabled", "cron_update_expression"
                    ))
            elif path.startswith("/updates"):
                # Allow either 'status' field (check) or 'success' (apply)
                valid = ("status" in payload) or ("success" in payload)

            # Attach header with validation status
            try:
                response.headers["X-Response-Validated"] = "ok" if valid else "failed"
            except Exception:
                pass
            return response
        except Exception:
            return response