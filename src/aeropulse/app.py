"""The web application: public site + API v1, one process."""
from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from .config import PACKAGE_DIR, get_settings
from .db.session import init_db


class RateLimit(BaseHTTPMiddleware):
    """Per-IP sliding window on /v1. In memory: fine for one process. Behind a CDN the
    client IP comes from the first X-Forwarded-For hop, which Caddy sets."""

    def __init__(self, app, per_minute: int) -> None:
        super().__init__(app)
        self.per_minute = per_minute
        self.hits: dict[str, deque] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith("/v1/") or request.url.path.startswith("/v1/docs"):
            return await call_next(request)
        ip = (request.headers.get("x-forwarded-for", "").split(",")[0].strip()
              or (request.client.host if request.client else "unknown"))
        now = time.monotonic()
        q = self.hits[ip]
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= self.per_minute:
            retry = int(60 - (now - q[0])) + 1
            return JSONResponse({"error": "rate_limited",
                                 "message": f"Limit is {self.per_minute} requests a minute. "
                                            f"Try again in {retry} seconds, or download the "
                                            "dataset from /data for bulk use."},
                                status_code=429, headers={"Retry-After": str(retry)})
        q.append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.per_minute)
        response.headers["X-RateLimit-Remaining"] = str(self.per_minute - len(q))
        return response


class SecurityHeaders(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        embeddable = path.startswith("/embed/")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; font-src 'self'; connect-src 'self'; base-uri 'self'; "
            "form-action 'self'; frame-ancestors " + ("*" if embeddable else "'self'"))
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy",
                                    "camera=(), microphone=(), geolocation=(), interest-cohort=()")
        if path.startswith("/static/"):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        elif path.startswith("/v1/") or path.startswith("/embed/"):
            response.headers.setdefault("Access-Control-Allow-Origin", "*")
            response.headers.setdefault("Cache-Control", "public, max-age=300")
        return response


def create_app() -> FastAPI:
    settings = get_settings()
    settings.check()
    if not settings.is_production:
        init_db()          # production runs `aeropulse db upgrade` instead

    app = FastAPI(title="AeroPulse API", version="0.1.0",
                  summary="Open, route-level index of Indian domestic airfares.",
                  docs_url="/v1/docs", redoc_url=None, openapi_url="/v1/openapi.json")
    app.add_middleware(RateLimit, per_minute=settings.rate_limit)
    app.add_middleware(SecurityHeaders)
    app.mount("/static", StaticFiles(directory=PACKAGE_DIR / "web" / "static"), name="static")

    from .api.v1 import router as api_router
    from .web.views import router as web_router
    app.include_router(api_router)
    app.include_router(web_router)

    @app.get("/healthz", include_in_schema=False)
    def healthz() -> PlainTextResponse:
        return PlainTextResponse("ok")

    return app


app = create_app()
