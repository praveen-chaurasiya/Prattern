"""
API Key authentication middleware.
If PRATTERN_API_KEY is not set, all requests pass through (local dev).
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from prattern.config import Config

PROTECTED_PREFIXES = ("/movers", "/analysis", "/scan", "/jobs")
PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class ApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Auth disabled when no key configured
        if not Config.PRATTERN_API_KEY:
            return await call_next(request)

        # CORS preflight passes through
        if request.method == "OPTIONS":
            return await call_next(request)

        # Only protect API routes — static files and public paths pass through
        path = request.url.path
        if path in PUBLIC_PATHS:
            return await call_next(request)

        is_api_route = any(path.startswith(p) for p in PROTECTED_PREFIXES)
        if not is_api_route:
            return await call_next(request)

        # Validate API key
        api_key = request.headers.get("X-API-Key")
        if api_key != Config.PRATTERN_API_KEY:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key"},
            )

        return await call_next(request)
