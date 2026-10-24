"""Public read-only API, version 1. Every response carries `data_mode`; if it is "demo",
the numbers are synthetic.

The website (web/, Next.js) reads everything through these endpoints. Anything a page
shows must be available here too.
"""
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
from ...core.quality import REASONS
from ...core.verdict import Verdict
from ...db.models import CollectionRun
from ...db.session import session_scope
from ...providers.policy import NEVER_COLLECTED, POLICIES
from ...reference import airports, great_circle_km, load_festivals, route_name, split_route

router = APIRouter(prefix="/v1", tags=["v1"])
Kind = Literal["chained", "fixed"]
Fmt = Literal["json", "csv"]


def db() -> Iterator[Session]:
    with session_scope() as s:
        yield s


# ----------------------------------------------------------------------------- shapes

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


def _compact(points, digits: int = 2) -> list[list]:
    """[[date, value, low, high], ...] for sparklines and charts; small over the wire."""
    return [[p.date.isoformat(), round(p.value, digits),
             None if p.low is None else round(p.low, digits),
             None if p.high is None else round(p.high, digits)] for p in points]


def _airport(code: str) -> dict:
    a = airports()[code]
    return {"iata": a.iata, "icao": a.icao, "city": a.city, "city_hi": a.city_hi,
            "airport": a.airport, "state": a.state, "lat": a.lat, "lon": a.lon}


def _route_or_404(s: Session, route_id: str) -> str:
    route_id = route_id.upper()
    if route_id not in q.basket_routes(s):
        raise HTTPException(404, f"{route_id} is not a tracked route; see /v1/routes")
    return route_id


def _window_or_422(window: str) -> str:
    if window not in m.WINDOW_BY_KEY:
        raise HTTPException(422, f"window must be one of {', '.join(m.WINDOW_BY_KEY)}")
    return window


def _windows() -> list[dict]:
    return [{"key": w.key, "label": w.label, "short": w.short, "first_day": w.first_day,
             "last_day": w.last_day} for w in m.WINDOWS]


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


def _route_row(r: dict) -> dict:
    o, d = r["origin"], r["destination"]
    return {"route": r["route_id"], "name": r["name"], "origin": o, "destination": d,
            "origin_city": airports()[o].city, "destination_city": airports()[d].city,
            "distance_km": round(great_circle_km(o, d)),
            "verdict": _verdict(r["verdict"]),
            "index": round(r["series"][-1].value, 3) if r["series"] else None,
            "series": _compact(r["series"])}


# ----------------------------------------------------------------------------- site-wide

@router.get("/meta", summary="Method, basket and data mode")
def meta(s: Session = Depends(db)):
    last = s.scalars(select(CollectionRun).order_by(CollectionRun.id.desc()).limit(1)).first()
    head = q.headline(s)
    return {"data_mode": q.data_mode(s), "methodology_version": m.METHODOLOGY_VERSION,
            "routes": q.basket_routes(s), "windows": _windows(),
            "latest_date": head["last"].date.isoformat() if head["last"] else None,
            "first_date": head["first_date"].isoformat() if head["first_date"] else None,
            "history_days": head["history_days"], "early_series": head["early"],
            "last_collection": None if last is None else {
                "provider": last.provider, "date": last.collection_date.isoformat(),
                "status": last.status},
            "licence": "CC BY 4.0", "attribution": "AeroPulse"}


@router.get("/insights", summary="National picture: index, movers, best time to book")
def insights(s: Session = Depends(db)):
    head = q.headline(s)
    windows = []
    for w in m.WINDOWS:
        pts = q.series(s, "window", "", w.key, days=m.TYPICAL_LOOKBACK + 1)
        windows.append({**_windows()[[x.key for x in m.WINDOWS].index(w.key)],
                        "verdict": _verdict(q.series_verdict(pts)), "series": _compact(pts)})
    curve = q.national_booking_curve(s)
    return {"data_mode": q.data_mode(s),
            "national": {"verdict": _verdict(head["verdict"]), "series": _compact(head["series"]),
                         "change_30d_pct": head["change_30d"], "early_series": head["early"],
                         "history_days": head["history_days"]},
            "windows": windows, "movers": q.movers(s),
            "booking_curve": [{"days_ahead": c["days_ahead"],
                               "pct_vs_route_median": round(c["pct_vs_route_median"], 2)}
                              for c in curve],
            "weekdays": [{**w, "pct_vs_typical": round(w["pct_vs_typical"], 2)}
                         for w in q.weekday_effect(s)]}


@router.get("/methodology", summary="Every constant behind the published numbers")
def methodology(s: Session = Depends(db)):
    return {"version": m.METHODOLOGY_VERSION, "windows": _windows(),
            "base_days": m.BASE_DAYS, "min_dates_per_product_day": m.MIN_DATES_PER_PRODUCT_DAY,
            "price_floor_inr": m.PRICE_FLOOR_INR, "price_ceiling_inr": m.PRICE_CEILING_INR,
            "outlier_z": m.OUTLIER_Z, "coverage_publish_pct": m.COVERAGE_PUBLISH,
            "coverage_warn_pct": m.COVERAGE_WARN, "se_replications": m.SE_REPLICATIONS,
            "se_seed": m.SE_SEED, "typical_lookback_days": m.TYPICAL_LOOKBACK,
            "typical_low_pct": m.TYPICAL_LOW_PCT, "typical_high_pct": m.TYPICAL_HIGH_PCT,
            "min_history_for_verdict": m.MIN_HISTORY_FOR_VERDICT,
            "early_series_days": m.EARLY_SERIES_DAYS,
            "exclusion_reasons": REASONS,
            "weights": [{"basket_version": w.basket_version, "route": w.route_id,
                         "weight": w.weight, "source": w.source,
                         "base_from": w.base_from.isoformat() if w.base_from else None,
                         "base_to": w.base_to.isoformat() if w.base_to else None}
                        for w in q.weights(s)],
            "links": [{"series": lk.scope, "from_version": lk.from_version,
                       "to_version": lk.to_version, "link_date": lk.link_period,
                       "factor": lk.factor} for lk in q.links(s)]}


@router.get("/sources", summary="Where fares come from, and what is never collected")
def sources():
    return {"providers": [{"name": p.name, "display_name": p.display_name,
                           "homepage": p.homepage, "kind": p.kind,
                           "terms_reviewed": p.terms_reviewed,
                           "raw_redistribution": p.raw_redistribution,
                           "attribution": p.attribution, "notes": p.notes}
                          for p in POLICIES.values()],
            "never_collected": list(NEVER_COLLECTED)}


# ----------------------------------------------------------------------------- airports

@router.get("/airports", summary="Airports used by tracked routes")
def airport_list(s: Session = Depends(db)):
    return {"airports": q.airport_list(s)}


@router.get("/airports/{iata}", summary="One airport: every tracked route from and to it")
def airport(iata: str, s: Session = Depends(db)):
    iata = iata.upper()
    if iata not in airports():
        raise HTTPException(404, "unknown airport")
    rows = [r for r in q.route_rows(s) if iata in (r["origin"], r["destination"])]
    if not rows:
        raise HTTPException(404, "no tracked routes at this airport")
    return {"data_mode": q.data_mode(s), "airport": _airport(iata),
            "departures": [_route_row(r) for r in rows if r["origin"] == iata],
            "arrivals": [_route_row(r) for r in rows if r["destination"] == iata]}


# ----------------------------------------------------------------------------- routes

@router.get("/routes", summary="Every tracked route with today's verdict and 90-day index")
def routes(s: Session = Depends(db)):
    return {"data_mode": q.data_mode(s), "routes": [_route_row(r) for r in q.route_rows(s)]}


@router.get("/routes/{route_id}", summary="One route: verdict per booking window, curve, weekdays")
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
        out.append({"window": w.key, "label": w.label, "short": w.short, "verdict": _verdict(v),
                    "median_cheapest_fare_inr": latest.price if latest else None,
                    "lowest_inr": latest.low if latest else None,
                    "highest_inr": latest.high if latest else None,
                    "departure_dates_priced": latest.dates if latest else None,
                    "date": latest.collection_date.isoformat() if latest else None})
    curve = q.booking_curve(s, route_id)
    index_pts = q.series(s, "route", route_id, days=m.TYPICAL_LOOKBACK + 1)
    reverse = f"{d}-{o}"
    return {"data_mode": q.data_mode(s), "route": route_id, "name": route_name(route_id),
            "origin": _airport(o), "destination": _airport(d),
            "distance_km": round(great_circle_km(o, d)),
            "reverse": reverse if reverse in q.basket_routes(s) else None,
            "windows": out,
            "index": {"verdict": _verdict(q.series_verdict(index_pts)),
                      "series": _compact(index_pts)},
            "booking_curve": [{"days_ahead": c["days_ahead"], "median_inr": c["median"],
                               "fares": c["n"]} for c in curve],
            "usually_cheapest_days_ahead": q.cheapest_stretch(curve),
            "weekdays": [{**w, "pct_vs_typical": round(w["pct_vs_typical"], 2)}
                         for w in q.weekday_effect(s, route_id)]}


@router.get("/routes/{route_id}/fares", summary="Daily median cheapest fare (₹) with 95% range")
def route_fares(route_id: str, s: Session = Depends(db), window: str = "15-30",
                days: int | None = Query(90, ge=7, le=3650,
                                         description="Trailing days; omit for all")):
    route_id = _route_or_404(s, route_id)
    window = _window_or_422(window)
    pts = q.product_ribbon(s, route_id, window, days=days)
    v, latest = q.product_verdict(s, route_id, window)
    return {"data_mode": q.data_mode(s), "route": route_id, "window": window,
            "verdict": _verdict(v),
            "latest": None if latest is None else {
                "date": latest.collection_date.isoformat(), "median_inr": latest.price,
                "lowest_inr": latest.low, "highest_inr": latest.high,
                "departure_dates_priced": latest.dates},
            "points": _compact(pts, 0)}


@router.get("/routes/{route_id}/calendar", summary="Next departures against usual")
def route_calendar(route_id: str, s: Session = Depends(db)):
    route_id = _route_or_404(s, route_id)
    cal = q.departure_calendar(s, route_id)
    return {"data_mode": q.data_mode(s), "route": route_id,
            "as_of": cal["as_of"].isoformat() if cal["as_of"] else None,
            "show_prices": cal.get("show_prices", False),
            "days": [{"date": d["date"].isoformat(), "level": d["level"], "window": d["window"],
                      "fare_inr": d["fare"]} for d in cal["days"]]}


# ----------------------------------------------------------------------------- indices

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


# ----------------------------------------------------------------------------- festivals

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
    f = view["festival"]
    show = view["show_prices"]
    return {"data_mode": q.data_mode(s), "slug": f.slug, "festival": f.name,
            "date": f.date.isoformat(), "date_confirmed": f.confirmed,
            "peak_departure": view["peak"].isoformat(), "show_prices": show,
            "routes": [{"route": r["route_id"], "name": r["name"],
                        "points": [{"date": p["date"].isoformat(), "days_ahead": p["days_ahead"],
                                    "pct_vs_ordinary": p["pct"],
                                    **({"fare_inr": p["fare"]} if show else {})}
                                   for p in r["points"]]} for r in view["routes"]]}


# ----------------------------------------------------------------------------- operations

@router.get("/status", summary="Collection health")
def status(s: Session = Depends(db)):
    st = q.status(s)
    return {"data_mode": q.data_mode(s), "coverage_pct": st["coverage"],
            "fares_last_30_days": st["fares_total"],
            "exclusions": [{"reason": k, "description": REASONS.get(k, k), "fares": v}
                           for k, v in st["exclusions"].items()],
            "recent_errors": [{"route": e.route_id, "error": e.error,
                               "at": e.fetched_at.isoformat() if e.fetched_at else None}
                              for e in st["recent_errors"]],
            "providers": {name: {
                "display_name": p["policy"].display_name if p["policy"] else name,
                "kind": p["policy"].kind if p["policy"] else None,
                "last_run": None if p["last"] is None else {
                    "date": p["last"].collection_date.isoformat(), "status": p["last"].status,
                    "routes_ok": p["last"].routes_ok,
                    "routes_requested": p["last"].routes_requested, "calls": p["last"].calls,
                    "message": p["last"].message},
                "route_success_pct": p["route_success_pct"],
                "terms_reviewed": bool(p["policy"] and p["policy"].terms_reviewed),
                "days": [{"date": d["date"].isoformat(), "status": d["status"]}
                         for d in p["days"]]} for name, p in st["providers"].items()}}


@router.get("/downloads", summary="The open dataset: files, row counts, checksums")
def downloads():
    from ...pipeline.export import read_manifest
    manifest = read_manifest()
    if manifest is None:
        return {"files": [], "generated_at": None, "is_demo": None}
    return {"generated_at": manifest["generated_at"], "is_demo": manifest["is_demo"],
            "licence": manifest.get("licence"),
            "files": [{**f, "url": f"/downloads/{f['name']}"} for f in manifest["files"]]}


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

