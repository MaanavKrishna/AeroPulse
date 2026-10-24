"""Public read-only API, version 1. Every response carries `data_mode`; if it is "demo",
the numbers are synthetic."""
from __future__ import annotations

import datetime as dt
import hmac
from collections.abc import Iterator
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ... import queries as q
from ...config import get_settings
from ...core import methodology as m
from ...core.verdict import Verdict
from ...db.models import CollectionRun
from ...db.session import session_scope
from ...reference import airports, load_festivals, route_name, split_route

router = APIRouter(prefix="/v1", tags=["v1"])


def db() -> Iterator[Session]:
    with session_scope() as s:
        yield s


def _verdict(v: Verdict) -> dict:
    return {"level": v.level, "headline": v.headline, "value": v.value,
            "usual_low": v.low, "usual_high": v.high, "usual_median": v.median,
            "pct_vs_usual": v.pct_vs_median, "history_days": v.history_days,
            "as_of": v.as_of.isoformat() if v.as_of else None}


def _points(points) -> list[dict]:
    return [{"date": p.date.isoformat(), "value": round(p.value, 4),
             "ci95_low": None if p.low is None else round(p.low, 4),
             "ci95_high": None if p.high is None else round(p.high, 4),
             "coverage_pct": round(p.coverage, 2), "status": p.status,
             "fares_used": p.observations} for p in points]


def _route_or_404(s: Session, route_id: str) -> str:
    route_id = route_id.upper()
    if route_id not in q.basket_routes(s):
        raise HTTPException(404, f"{route_id} is not a tracked route; see /v1/routes")
    return route_id


def _series_response(s: Session, scope: str, route_id: str, window: str, kind: str,
                     start: dt.date | None, end: dt.date | None, fmt: str, name: str):
    pts = q.series(s, scope, route_id, window, kind=kind.upper())
    pts = [p for p in pts if (start is None or p.date >= start) and (end is None or p.date <= end)]
    if fmt == "csv":
        lines = ["date,value,ci95_low,ci95_high,coverage_pct,status,fares_used"]
        lines += [f"{p.date},{p.value:.4f},{'' if p.low is None else f'{p.low:.4f}'},"
                  f"{'' if p.high is None else f'{p.high:.4f}'},{p.coverage:.2f},{p.status},"
                  f"{p.observations}" for p in pts]
        return Response("\n".join(lines) + "\n", media_type="text/csv",
                        headers={"Content-Disposition": f'attachment; filename="{name}.csv"'})
    return {"data_mode": q.data_mode(s), "series": name, "kind": kind,
            "methodology_version": m.METHODOLOGY_VERSION,
            "verdict": _verdict(q.series_verdict(pts[-(m.TYPICAL_LOOKBACK + 1):])),
            "points": _points(pts)}


@router.get("/meta", summary="Method, basket and data mode")
def meta(s: Session = Depends(db)):
    last = s.scalars(select(CollectionRun).order_by(CollectionRun.id.desc()).limit(1)).first()
    return {"data_mode": q.data_mode(s), "methodology_version": m.METHODOLOGY_VERSION,
            "routes": q.basket_routes(s),
            "windows": [{"key": w.key, "label": w.label, "first_day": w.first_day,
                         "last_day": w.last_day} for w in m.WINDOWS],
            "last_collection": None if last is None else {
                "provider": last.provider, "date": last.collection_date.isoformat(),
                "status": last.status},
            "licence": "CC BY 4.0", "attribution": "AeroPulse"}


@router.get("/airports", summary="Airports used by tracked routes")
def airport_list():
    return {"airports": q.airport_list()}


@router.get("/routes", summary="Every tracked route with today's verdict")
def routes(s: Session = Depends(db)):
    return {"data_mode": q.data_mode(s),
            "routes": [{"route": r["route_id"], "name": r["name"],
                        "verdict": _verdict(r["verdict"]),
                        "index": round(r["series"][-1].value, 4) if r["series"] else None}
                       for r in q.route_rows(s)]}


@router.get("/routes/{route_id}", summary="One route: verdicts by booking window")
def route(route_id: str, s: Session = Depends(db),
          window: str | None = Query(None, description="Only this booking window, e.g. 8-14")):
    route_id = _route_or_404(s, route_id)
    o, d = split_route(route_id)
    wins = [w for w in m.WINDOWS if window is None or w.key == window]
    if not wins:
        raise HTTPException(422, f"window must be one of {', '.join(m.WINDOW_BY_KEY)}")
    out = []
    for w in wins:
        v, latest = q.product_verdict(s, route_id, w.key)
        out.append({"window": w.key, "label": w.label, "verdict": _verdict(v),
                    "median_cheapest_fare_inr": latest.price if latest else None,
                    "lowest_inr": latest.low if latest else None,
                    "highest_inr": latest.high if latest else None,
                    "departure_dates_priced": latest.dates if latest else None,
                    "date": latest.collection_date.isoformat() if latest else None})
    curve = q.booking_curve(s, route_id)
    return {"data_mode": q.data_mode(s), "route": route_id, "name": route_name(route_id),
            "origin": {"iata": o, "city": airports()[o].city},
            "destination": {"iata": d, "city": airports()[d].city},
            "windows": out,
            "booking_curve": [{"days_ahead": c["days_ahead"], "median_inr": c["median"],
                               "fares": c["n"]} for c in curve],
            "usually_cheapest_days_ahead": q.cheapest_stretch(curve)}


Kind = Literal["chained", "fixed"]
Fmt = Literal["json", "csv"]


@router.get("/indices/national", summary="National index")
def national(s: Session = Depends(db), kind: Kind = "chained", start: dt.date | None = Query(
        None, alias="from"), end: dt.date | None = Query(None, alias="to"), format: Fmt = "json"):
    return _series_response(s, "national", "", "", kind, start, end, format,
                            "aeropulse-national")


@router.get("/indices/routes/{route_id}", summary="Route index")
def route_index(route_id: str, s: Session = Depends(db), kind: Kind = "chained",
                start: dt.date | None = Query(None, alias="from"),
                end: dt.date | None = Query(None, alias="to"), format: Fmt = "json"):
    route_id = _route_or_404(s, route_id)
    return _series_response(s, "route", route_id, "", kind, start, end, format,
                            f"aeropulse-{route_id.lower()}")


@router.get("/indices/windows/{window}", summary="Booking-window index")
def window_index(window: str, s: Session = Depends(db), kind: Kind = "chained",
                 start: dt.date | None = Query(None, alias="from"),
                 end: dt.date | None = Query(None, alias="to"), format: Fmt = "json"):
    if window not in m.WINDOW_BY_KEY:
        raise HTTPException(404, f"window must be one of {', '.join(m.WINDOW_BY_KEY)}")
    return _series_response(s, "window", "", window, kind, start, end, format,
                            f"aeropulse-window-{window}")


@router.get("/festivals", summary="Festival calendar")
def festivals():
    return {"festivals": [{"slug": f.slug, "name": f.name, "date": f.date.isoformat(),
                           "date_confirmed": f.confirmed, "routes": list(f.routes)}
                          for f in load_festivals()]}


@router.get("/festivals/{slug}", summary="Festival fares against ordinary weeks")
def festival(slug: str, s: Session = Depends(db)):
    view = q.festival_view(s, slug)
    if view is None:
        raise HTTPException(404, "unknown festival")
    show = view["show_prices"]
    return {"data_mode": q.data_mode(s), "festival": view["festival"].name,
            "peak_departure": view["peak"].isoformat(),
            "routes": [{"route": r["route_id"], "name": r["name"],
                        "points": [{"date": p["date"].isoformat(), "days_ahead": p["days_ahead"],
                                    "pct_vs_ordinary": p["pct"],
                                    **({"fare_inr": p["fare"]} if show else {})}
                                   for p in r["points"]]} for r in view["routes"]]}


@router.get("/status", summary="Collection health")
def status(s: Session = Depends(db)):
    st = q.status(s)
    return {"data_mode": q.data_mode(s), "coverage_pct": st["coverage"],
            "fares_last_30_days": st["fares_total"], "exclusions": st["exclusions"],
            "providers": {name: {
                "last_run": None if p["last"] is None else {
                    "date": p["last"].collection_date.isoformat(), "status": p["last"].status,
                    "routes_ok": p["last"].routes_ok,
                    "routes_requested": p["last"].routes_requested},
                "route_success_pct": p["route_success_pct"],
                "terms_reviewed": bool(p["policy"] and p["policy"].terms_reviewed),
                "days": [{"date": d["date"].isoformat(), "status": d["status"]}
                         for d in p["days"]]} for name, p in st["providers"].items()}}


def require_admin(authorization: str | None = Header(None)) -> None:
    token = get_settings().admin_token
    if token is None:
        raise HTTPException(404, "not found")
    expected = f"Bearer {token.get_secret_value()}"
    if not authorization or not hmac.compare_digest(authorization, expected):
        raise HTTPException(401, "admin token required", headers={"WWW-Authenticate": "Bearer"})


@router.post("/admin/rebuild", summary="Rebuild all series (admin)", include_in_schema=False,
             dependencies=[Depends(require_admin)])
def admin_rebuild(s: Session = Depends(db), reason: str = "manual rebuild"):
    from ...pipeline.build import build
    from ...reference import load_basket
    r = build(s, load_basket(), get_settings().provider_list[0], reason=reason[:200])
    return {"points_written": r.points_written, "revisions": r.revisions}
