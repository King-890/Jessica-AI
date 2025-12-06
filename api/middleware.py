from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.requests import Request


ALLOWED_LOCAL_HOSTS = {"127.0.0.1", "::1", "localhost"}


class LocalhostOnlyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_host = request.client.host if request.client else None
        if client_host not in ALLOWED_LOCAL_HOSTS:
            return JSONResponse({"detail": "Forbidden: local access only"}, status_code=403)
        return await call_next(request)