"""Non-JSON things the API serves: the open dataset files, per-route CSV, a chart image for
social cards and news use, and Atom feeds. Links inside them point at the public website
(AEROPULSE_SITE_URL), not at the API."""
from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from .. import queries as q
from ..config import PACKAGE_DIR, get_settings
from ..core import methodology as m
from ..core.verdict import verdict
from ..db.session import session_scope
from ..reference import route_from_slug, route_name
from ..render import text
from ..render.charts import ribbon_standalone

router = APIRouter(include_in_schema=False)
DEFAULT_WINDOW = "15-30"
_feeds = Environment(loader=FileSystemLoader(PACKAGE_DIR / "render" / "templates"),
                     autoescape=select_autoescape(["xml"]))


def db() -> Iterator[Session]:
    with session_scope() as s:
        yield s


def _route(s: Session, slug: str) -> str:
    route_id = route_from_slug(slug)
    if route_id not in q.basket_routes(s):
        raise HTTPException(404, "route not tracked")
    return route_id


def _window(w: str) -> str:
    return w if w in m.WINDOW_BY_KEY else DEFAULT_WINDOW


def _site() -> str:
    return get_settings().site_url.rstrip("/")


@router.get("/downloads/{name}")
def download(name: str):
    from ..pipeline.export import export_path
    path = export_path(name)
    if path is None:
        raise HTTPException(404, "no such file")
    media = "text/csv" if name.endswith(".csv") else "application/json"
    return Response(Path(path).read_bytes(), media_type=media,
                    headers={"Content-Disposition": f'attachment; filename="{name}"',
                             "Cache-Control": "public, max-age=3600"})


@router.get("/csv/routes/{slug}.csv")
def route_csv(slug: str, s: Session = Depends(db), w: str = DEFAULT_WINDOW):
    route_id = _route(s, slug)
    w = _window(w)
    lines = ["date,route,window,median_cheapest_fare_inr,lowest_inr,highest_inr,"
             "departure_dates_priced,is_demo"]
    lines += [f"{r.collection_date},{r.route_id},{r.window},{r.price:.0f},{r.low:.0f},"
              f"{r.high:.0f},{r.dates},{str(r.is_demo).lower()}"
              for r in q.product_series(s, route_id, w)]
    return Response("\n".join(lines) + "\n", media_type="text/csv",
                    headers={"Content-Disposition":
                             f'attachment; filename="aeropulse-{slug}-{w}.csv"'})


@router.get("/img/routes/{slug}.svg")
def route_image(slug: str, s: Session = Depends(db), w: str = DEFAULT_WINDOW):
    route_id = _route(s, slug)
    w = _window(w)
    v, _ = q.product_verdict(s, route_id, w)
    pts = q.product_ribbon(s, route_id, w, days=90, replications=100)
    demo = q.data_mode(s) == "demo"
    body = ribbon_standalone(
        pts, typical=v, title=route_name(route_id),
        subtitle=f"{text.answer(v)} Flights {text.window_phrase(w)}, last 90 days.",
        footer=("DEMO DATA, NOT REAL FARES. " if demo else "")
        + f"AeroPulse, {_site().split('//')[-1]}, CC BY 4.0")
    return Response(body, media_type="image/svg+xml",
                    headers={"Cache-Control": "public, max-age=3600"})


@router.get("/feeds/routes/{slug}.xml")
def route_feed(slug: str, s: Session = Depends(db)):
    route_id = _route(s, slug)
    rows = q.product_series(s, route_id, DEFAULT_WINDOW)
    entries = []
    for i in range(max(0, len(rows) - 14), len(rows)):
        sub = rows[: i + 1]
        v = verdict([(r.collection_date, r.price) for r in sub])
        entries.append({"date": sub[-1].collection_date,
                        "copy": text.fare_verdict(v, DEFAULT_WINDOW, route_name(route_id))})
    body = _feeds.get_template("route-feed.xml").render(
        route_id=route_id, slug=slug, entries=list(reversed(entries)), site=_site(),
        name=route_name(route_id), mode=q.data_mode(s))
    return Response(body, media_type="application/atom+xml")
