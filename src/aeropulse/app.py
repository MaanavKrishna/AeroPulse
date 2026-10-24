"""The AeroPulse API: JSON under /v1, plus dataset files, CSV, chart images and feeds.

The public website is a separate Next.js app (web/) that reads this API."""
from __future__ import annotations

import hmac
import time
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .config import get_settings
from .db.session import init_db


class RateLimit(BaseHTTPMiddleware):
    """Per-IP sliding window on /v1. In memory: fine for one process. Behind a CDN the
    client IP comes from the first X-Forwarded-For hop, which Caddy sets."""

    def __init__(self, app, per_minute: int, site_key: str | None = None) -> None:
        super().__init__(app)
        self.per_minute = per_minute
        self.site_key = site_key.encode() if site_key else None
        self.hits: dict[str, deque] = defaultdict(deque)

    def _is_site(self, request: Request) -> bool:
        sent = request.headers.get("x-aeropulse-site-key")
        return bool(self.site_key and sent and hmac.compare_digest(sent.encode(), self.site_key))

    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith("/v1/") or request.url.path.startswith("/v1/docs"):
            return await call_next(request)
        if self._is_site(request):
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
    """JSON and files need no scripts, styles or frames. The interactive docs page loads
    Swagger UI from a CDN, so it is the one path without a content policy."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        if not path.startswith("/v1/docs"):
            response.headers.setdefault("Content-Security-Policy",
                                        "default-src 'none'; frame-ancestors 'none'")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        if path.startswith(("/v1/", "/downloads/", "/csv/", "/img/", "/feeds/")):
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
    app.add_middleware(RateLimit, per_minute=settings.rate_limit,
                       site_key=settings.site_key.get_secret_value() if settings.site_key else None)
    app.add_middleware(SecurityHeaders)
    from .api.files import router as files_router
    from .api.v1 import router as api_router
    app.include_router(api_router)
    app.include_router(files_router)

    @app.get("/", include_in_schema=False)
    def index() -> JSONResponse:
        return JSONResponse({"name": "AeroPulse API", "version": "0.1.0",
                             "website": settings.site_url, "docs": "/v1/docs",
                             "openapi": "/v1/openapi.json", "health": "/healthz"})

    @app.get("/healthz", include_in_schema=False)
    def healthz() -> PlainTextResponse:
        return PlainTextResponse("ok")

    @app.get("/robots.txt", include_in_schema=False)
    def robots() -> PlainTextResponse:
        # People should land on the website, not on API URLs.
        return PlainTextResponse("User-agent: *\nDisallow: /\n")

    return app


app = create_app()
