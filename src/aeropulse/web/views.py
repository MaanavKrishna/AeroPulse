"""Public website. Server-rendered; JavaScript only enhances."""
from __future__ import annotations

import datetime as dt
import hashlib
from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .. import queries as q
from ..config import PACKAGE_DIR, get_settings
from ..core import methodology as m
from ..core.quality import REASONS
from ..db.session import session_scope
from ..providers.policy import NEVER_COLLECTED, POLICIES
from ..reference import (
    airports,
    load_festivals,
    route_from_slug,
    route_name,
    route_slug,
    split_route,
)
from . import text
from .charts import svg

router = APIRouter(include_in_schema=False)
STATIC = PACKAGE_DIR / "web" / "static"
templates = Jinja2Templates(directory=str(PACKAGE_DIR / "web" / "templates"))
DEFAULT_ROUTE = "DEL-BOM"
DEFAULT_WINDOW = "15-30"


@lru_cache(maxsize=256)
def _asset_hash(path: str, mtime_ns: int) -> str:
    return hashlib.sha256((STATIC / path).read_bytes()).hexdigest()[:10]


def static_url(path: str) -> str:
    """Content-hashed URL, so static files can be cached forever and still update."""
    return f"/static/{path}?v={_asset_hash(path, (STATIC / path).stat().st_mtime_ns)}"


env = templates.env
env.globals.update(static_url=static_url, svg=svg, text=text, m=m, route_name=route_name,
                   route_slug=route_slug, airports=airports, windows=m.WINDOWS,
                   site_url=lambda: get_settings().site_url.rstrip("/"))
env.filters.update(inr=svg.inr, day_month=svg.day_month,
                   pct=lambda v: "" if v is None else f"{v:+.1f}%",
                   num1=lambda v: "" if v is None else f"{v:.1f}")


def db() -> Iterator[Session]:
    with session_scope() as s:
        yield s


def render(request: Request, name: str, s: Session, status_code: int = 200, **ctx):
    ctx.setdefault("mode", q.data_mode(s))
    ctx.setdefault("nav", "")
    ctx["settings"] = get_settings()
    return templates.TemplateResponse(request, name, ctx, status_code=status_code)


# ----------------------------------------------------------------------------- hero

def hero_context(s: Session, origin: str | None, dest: str | None, window: str | None) -> dict:
    routes = q.basket_routes(s)
    origins = sorted({split_route(r)[0] for r in routes}, key=lambda c: airports()[c].city)
    origin = origin if origin in origins else split_route(DEFAULT_ROUTE)[0]
    dests = sorted({split_route(r)[1] for r in routes if r.startswith(origin + "-")},
                   key=lambda c: airports()[c].city)
    if dest not in dests:
        dest = split_route(DEFAULT_ROUTE)[1] if f"{origin}-BOM" in routes and origin != "BOM" \
            else (dests[0] if dests else None)
    window = window if window in m.WINDOW_BY_KEY else DEFAULT_WINDOW
    ctx = {"origins": origins, "dests": dests, "origin": origin, "dest": dest,
           "window": window, "route_id": None}
    if dest:
        route_id = f"{origin}-{dest}"
        v, latest = q.product_verdict(s, route_id, window)
        ctx.update(route_id=route_id, verdict=v, latest=latest,
                   answer=text.fare_verdict(v, window, route_name(route_id)),
                   points=q.product_ribbon(s, route_id, window, days=90))
    return ctx


@router.get("/", response_class=HTMLResponse)
def home(request: Request, s: Session = Depends(db), origin: str | None = None,
         dest: str | None = None, w: str | None = None):
    hero = hero_context(s, (origin or "").upper(), (dest or "").upper(), w)
    rows = q.route_rows(s)
    rows.sort(key=lambda r: -(r["verdict"].pct_vs_median or 0))
    upcoming = [f for f in load_festivals() if f.date >= dt.date.today()][:2]
    return render(request, "home.html", s, hero=hero, head=q.headline(s), rows=rows,
                  upcoming=upcoming, nav="home")


@router.get("/fragments/hero", response_class=HTMLResponse)
def hero_fragment(request: Request, s: Session = Depends(db), origin: str | None = None,
                  dest: str | None = None, w: str | None = None):
    hero = hero_context(s, (origin or "").upper(), (dest or "").upper(), w)
    return render(request, "_hero_section.html", s, hero=hero)


# ----------------------------------------------------------------------------- routes

@router.get("/routes", response_class=HTMLResponse)
def routes_index(request: Request, s: Session = Depends(db), sort: str = "above"):
    rows = q.route_rows(s)
    if sort == "name":
        rows.sort(key=lambda r: r["name"])
    elif sort == "below":
        rows.sort(key=lambda r: (r["verdict"].pct_vs_median or 0))
    else:
        sort = "above"
        rows.sort(key=lambda r: -(r["verdict"].pct_vs_median or 0))
    return render(request, "routes.html", s, rows=rows, sort=sort, nav="routes")


@router.get("/routes/go")
def routes_go(origin: str, dest: str, w: str = DEFAULT_WINDOW):
    return RedirectResponse(f"/routes/{origin.lower()}-{dest.lower()}?w={w}", status_code=303)


def _route_or_404(s: Session, slug: str) -> str:
    route_id = route_from_slug(slug)
    if route_id not in q.basket_routes(s):
        raise HTTPException(404, "route not tracked")
    return route_id


@router.get("/routes/{slug}", response_class=HTMLResponse)
def route_page(request: Request, slug: str, s: Session = Depends(db),
               w: str = DEFAULT_WINDOW, range: str = "90"):
    route_id = _route_or_404(s, slug)
    w = w if w in m.WINDOW_BY_KEY else DEFAULT_WINDOW
    days = {"90": 90, "365": 365, "all": None}.get(range, 90)
    range = range if range in {"90", "365", "all"} else "90"
    v, latest = q.product_verdict(s, route_id, w)
    points = q.product_ribbon(s, route_id, w, days=days)
    index_points = q.series(s, "route", route_id, days=days)
    curve = q.booking_curve(s, route_id)
    stretch = q.cheapest_stretch(curve)
    o, d = split_route(route_id)
    reverse = f"{d}-{o}"
    window_verdicts = {win.key: q.product_verdict(s, route_id, win.key)[0] for win in m.WINDOWS}
    return render(request, "route.html", s, route_id=route_id, origin=o, dest=d,
                  window=w, span=range, verdict=v, latest=latest, points=points,
                  index_points=index_points, curve=curve, stretch=stretch,
                  window_verdicts=window_verdicts,
                  calendar=q.departure_calendar(s, route_id),
                  copy=text.fare_verdict(v, w, route_name(route_id)),
                  reverse=reverse if reverse in q.basket_routes(s) else None,
                  index_verdict=q.series_verdict(q.series(s, "route", route_id, days=91)),
                  nav="routes")


@router.get("/routes/{slug}/data.csv")
def route_csv(slug: str, s: Session = Depends(db), w: str = DEFAULT_WINDOW):
    route_id = _route_or_404(s, slug)
    rows = q.product_series(s, route_id, w if w in m.WINDOW_BY_KEY else DEFAULT_WINDOW)
    lines = ["date,route,window,median_cheapest_fare_inr,lowest_inr,highest_inr,"
             "departure_dates_priced,is_demo"]
    lines += [f"{r.collection_date},{r.route_id},{r.window},{r.price:.0f},{r.low:.0f},"
              f"{r.high:.0f},{r.dates},{str(r.is_demo).lower()}" for r in rows]
    return Response("\n".join(lines) + "\n", media_type="text/csv",
                    headers={"Content-Disposition":
                             f'attachment; filename="aeropulse-{slug}-{w}.csv"'})


@router.get("/img/routes/{slug}.svg")
def route_image(slug: str, s: Session = Depends(db), w: str = DEFAULT_WINDOW):
    route_id = _route_or_404(s, slug)
    w = w if w in m.WINDOW_BY_KEY else DEFAULT_WINDOW
    v, latest = q.product_verdict(s, route_id, w)
    pts = q.product_ribbon(s, route_id, w, days=90, replications=100)
    mode = q.data_mode(s)
    body = svg.ribbon_standalone(
        pts, typical=v, title=route_name(route_id),
        subtitle=f"{v.headline}. Flights {text.window_phrase(w)}, last 90 days.",
        footer=("DEMO DATA, NOT REAL FARES. " if mode == "demo" else "")
        + f"AeroPulse · {get_settings().site_url.split('//')[-1]} · CC BY 4.0")
    return Response(body, media_type="image/svg+xml",
                    headers={"Cache-Control": "public, max-age=3600"})


@router.get("/embed/routes/{slug}", response_class=HTMLResponse)
def route_embed(request: Request, slug: str, s: Session = Depends(db),
                w: str = DEFAULT_WINDOW):
    route_id = _route_or_404(s, slug)
    w = w if w in m.WINDOW_BY_KEY else DEFAULT_WINDOW
    v, latest = q.product_verdict(s, route_id, w)
    return render(request, "embed.html", s, route_id=route_id, window=w, verdict=v,
                  latest=latest, copy=text.fare_verdict(v, w, route_name(route_id)),
                  points=q.product_ribbon(s, route_id, w, days=90, replications=100))


# ----------------------------------------------------------------------------- festivals

@router.get("/festivals", response_class=HTMLResponse)
def festivals_index(request: Request, s: Session = Depends(db)):
    today = dt.date.today()
    fests = load_festivals()
    views = {f.slug: q.festival_view(s, f.slug) for f in fests
             if -14 <= (f.date - today).days <= 60}
    return render(request, "festivals.html", s, festivals=fests, views=views, today=today,
                  nav="festivals")


@router.get("/festivals/{slug}", response_class=HTMLResponse)
def festival_page(request: Request, slug: str, s: Session = Depends(db)):
    view = q.festival_view(s, slug)
    if view is None:
        raise HTTPException(404, "unknown festival")
    return render(request, "festival.html", s, view=view, today=dt.date.today(),
                  nav="festivals")


# ----------------------------------------------------------------------------- info pages

@router.get("/methodology", response_class=HTMLResponse)
def methodology(request: Request, s: Session = Depends(db)):
    return render(request, "methodology.html", s, links=q.links(s), weights=q.weights(s),
                  nav="methodology")


@router.get("/data", response_class=HTMLResponse)
def data_page(request: Request, s: Session = Depends(db)):
    from ..pipeline.export import read_manifest
    return render(request, "data.html", s, manifest=read_manifest(), nav="data")


@router.get("/downloads/{name}")
def download(name: str):
    from ..pipeline.export import export_path
    path = export_path(name)
    if path is None:
        raise HTTPException(404, "no such file")
    media = "text/csv" if name.endswith(".csv") else "application/json"
    return Response(Path(path).read_bytes(), media_type=media,
                    headers={"Content-Disposition": f'attachment; filename="{name}"'})


@router.get("/status", response_class=HTMLResponse)
def status_page(request: Request, s: Session = Depends(db)):
    return render(request, "status.html", s, st=q.status(s), nav="status", reasons=REASONS)


@router.get("/about", response_class=HTMLResponse)
def about(request: Request, s: Session = Depends(db)):
    return render(request, "about.html", s, policies=POLICIES, never=NEVER_COLLECTED,
                  nav="about")


@router.get("/api", response_class=HTMLResponse)
def api_page(request: Request, s: Session = Depends(db)):
    return render(request, "api.html", s, nav="data")


# ----------------------------------------------------------------------------- machine

@router.get("/feeds/routes/{slug}.xml")
def route_feed(request: Request, slug: str, s: Session = Depends(db)):
    route_id = _route_or_404(s, slug)
    entries = []
    rows = q.product_series(s, route_id, DEFAULT_WINDOW)
    for i in range(max(0, len(rows) - 14), len(rows)):
        sub = rows[: i + 1]
        v = q.verdict([(r.collection_date, r.price) for r in sub])
        entries.append({"date": sub[-1].collection_date,
                        "copy": text.fare_verdict(v, DEFAULT_WINDOW, route_name(route_id))})
    body = templates.get_template("feed.xml").render(
        route_id=route_id, slug=slug, entries=list(reversed(entries)),
        site=get_settings().site_url.rstrip("/"), name=route_name(route_id),
        mode=q.data_mode(s))
    return Response(body, media_type="application/atom+xml")


@router.get("/sitemap.xml")
def sitemap(s: Session = Depends(db)):
    site = get_settings().site_url.rstrip("/")
    paths = ["/", "/routes", "/festivals", "/methodology", "/data", "/api", "/status", "/about"]
    paths += [f"/routes/{route_slug(r)}" for r in q.basket_routes(s)]
    paths += [f"/festivals/{f.slug}" for f in load_festivals()]
    urls = "".join(f"<url><loc>{site}{p}</loc></url>" for p in paths)
    return Response(f'<?xml version="1.0" encoding="UTF-8"?><urlset '
                    f'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>',
                    media_type="application/xml")


@router.get("/robots.txt")
def robots(s: Session = Depends(db)):
    site = get_settings().site_url.rstrip("/")
    blocked = "Disallow: /\n" if q.data_mode(s) == "demo" else "Disallow: /fragments/\n"
    return Response(f"User-agent: *\n{blocked}Sitemap: {site}/sitemap.xml\n",
                    media_type="text/plain")
