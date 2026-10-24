"""Every read the API makes. The website reads only through the API, so a page and its
JSON can never disagree."""
from __future__ import annotations

import datetime as dt
import statistics
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .core.methodology import (
    EARLY_SERIES_DAYS,
    METHODOLOGY_VERSION,
    TYPICAL_LOOKBACK,
    WINDOW_BY_KEY,
    WINDOWS,
    window_for,
)
from .core.verdict import Verdict, percentile, verdict
from .db.models import (
    BasketWeight,
    CollectionRun,
    CpiAirfare,
    Fare,
    IndexLink,
    IndexValue,
    ProductPrice,
    RawResponse,
)
from .providers.policy import POLICIES
from .reference import airports, load_festivals, route_name, split_route


@dataclass
class SeriesPoint:
    date: dt.date
    value: float
    low: float | None
    high: float | None
    coverage: float
    status: str
    observations: int


def data_mode(s: Session) -> str:
    """Return demo, live or empty. Decides the banner on every page."""
    any_point = s.scalar(select(IndexValue.id).limit(1))
    if any_point is None:
        return "empty"
    return "demo" if s.scalar(select(IndexValue.id).where(IndexValue.is_demo)
                              .limit(1)) else "live"


def series(s: Session, scope: str, route_id: str = "", window: str = "",
           kind: str = "CHAINED", days: int | None = None) -> list[SeriesPoint]:
    q = (select(IndexValue).where(IndexValue.scope == scope, IndexValue.route_id == route_id,
                                  IndexValue.window == window, IndexValue.kind == kind,
                                  IndexValue.frequency == "daily",
                                  IndexValue.methodology_version == METHODOLOGY_VERSION)
         .order_by(IndexValue.period_start))
    rows = list(s.scalars(q))
    if days and rows:
        cutoff = rows[-1].period_start - dt.timedelta(days=days - 1)
        rows = [r for r in rows if r.period_start >= cutoff]
    return [SeriesPoint(r.period_start, r.value, r.ci95_low, r.ci95_high, r.coverage,
                        r.status, r.observation_count) for r in rows]


def series_verdict(points: list[SeriesPoint]) -> Verdict:
    return verdict([(p.date, p.value) for p in points if p.status != "insufficient_data"])


def product_series(s: Session, route_id: str, window: str) -> list[ProductPrice]:
    return list(s.scalars(select(ProductPrice).where(
        ProductPrice.route_id == route_id, ProductPrice.window == window)
        .order_by(ProductPrice.collection_date)))


def product_verdict(s: Session, route_id: str, window: str) -> tuple[Verdict, ProductPrice | None]:
    rows = product_series(s, route_id, window)
    if not rows:
        return verdict([]), None
    return verdict([(r.collection_date, r.price) for r in rows]), rows[-1]


def product_ribbon(s: Session, route_id: str, window: str, days: int | None = None,
                   replications: int = 200) -> list[SeriesPoint]:
    """Daily median cheapest fare (₹) for one route and window, with a 95% interval from
    resampling departure dates, the same method as the index."""
    import random
    prices = product_series(s, route_id, window)
    if days and prices:
        cutoff = prices[-1].collection_date - dt.timedelta(days=days - 1)
        prices = [p for p in prices if p.collection_date >= cutoff]
    if not prices:
        return []
    latest = (select(Fare.collection_date, func.max(Fare.run_id).label("run"))
              .where(Fare.route_id == route_id, Fare.provider == prices[-1].provider)
              .group_by(Fare.collection_date).subquery())
    rows = s.execute(select(Fare.collection_date, Fare.fare).join(
        latest, (Fare.collection_date == latest.c.collection_date)
        & (Fare.run_id == latest.c.run))
        .where(Fare.route_id == route_id, Fare.window == window, Fare.eligible.is_(True),
               Fare.collection_date >= prices[0].collection_date)).all()
    by_day: dict[dt.date, list[float]] = defaultdict(list)
    for d, f in rows:
        by_day[d].append(f)
    rng = random.Random(f"{route_id}/{window}")
    out = []
    for p in prices:
        fares = by_day.get(p.collection_date, [])
        low = high = None
        if len(fares) >= 3:
            draws = sorted(statistics.median(rng.choices(fares, k=len(fares)))
                           for _ in range(replications))
            low, high = percentile(draws, 2.5), percentile(draws, 97.5)
        out.append(SeriesPoint(p.collection_date, p.price, low, high, 100.0, "valid", p.dates))
    return out


def basket_routes(s: Session) -> list[str]:
    latest = s.scalar(select(func.max(BasketWeight.basket_version)))
    if latest is None:
        return []
    return sorted(s.scalars(select(BasketWeight.route_id)
                            .where(BasketWeight.basket_version == latest)))


def route_rows(s: Session, days: int = TYPICAL_LOOKBACK) -> list[dict]:
    """Every basket route with its recent series and verdict, for list views."""
    out = []
    for route_id in basket_routes(s):
        pts = series(s, "route", route_id, days=days + 1)
        if not pts:
            continue
        v = series_verdict(series(s, "route", route_id, days=TYPICAL_LOOKBACK + 1))
        o, d = split_route(route_id)
        out.append({"route_id": route_id, "name": route_name(route_id),
                    "origin": o, "destination": d, "series": pts, "verdict": v})
    return out


def headline(s: Session) -> dict:
    nat_all = series(s, "national")
    nat = nat_all[-(TYPICAL_LOOKBACK + 1):]
    v = series_verdict(nat)
    first = nat_all[0].date if nat_all else None
    last = nat_all[-1] if nat_all else None
    change_30 = None
    if len(nat_all) > 30:
        change_30 = (nat_all[-1].value / nat_all[-31].value - 1) * 100
    return {"series": nat, "verdict": v, "first_date": first, "last": last,
            "change_30d": change_30,
            "early": bool(first and last and (last.date - first).days < EARLY_SERIES_DAYS),
            "history_days": (last.date - first).days + 1 if first and last else 0}


def booking_curve(s: Session, route_id: str, lookback: int = 30) -> list[dict]:
    """Median cheapest fare by days before departure, over the last `lookback` collection
    days. Aggregated, so it reveals no single fare."""
    last = s.scalar(select(func.max(Fare.collection_date)).where(Fare.route_id == route_id))
    if last is None:
        return []
    start = last - dt.timedelta(days=lookback - 1)
    rows = s.execute(select(Fare.days_ahead, Fare.fare).where(
        Fare.route_id == route_id, Fare.eligible.is_(True),
        Fare.collection_date >= start)).all()
    by_day: dict[int, list[float]] = defaultdict(list)
    for d, f in rows:
        by_day[d].append(f)
    return [{"days_ahead": d, "median": statistics.median(v), "n": len(v),
             "window": (window_for(d).key if window_for(d) else None)}
            for d, v in sorted(by_day.items()) if len(v) >= 5]


def cheapest_stretch(curve: list[dict]) -> tuple[int, int] | None:
    """The run of days-ahead whose median sits in the cheapest fifth of the curve."""
    if len(curve) < 10:
        return None
    values = sorted(c["median"] for c in curve)
    cut = percentile(values, 20)
    cheap = [c["days_ahead"] for c in curve if c["median"] <= cut]
    return (min(cheap), max(cheap)) if cheap else None


def departure_calendar(s: Session, route_id: str) -> dict:
    """Next departures as seen on the latest collection day, each labelled below / typical /
    above against fares for the same booking window over the lookback period."""
    last = s.scalar(select(func.max(Fare.collection_date)).where(Fare.route_id == route_id))
    if last is None:
        return {"as_of": None, "days": []}
    today = list(s.execute(select(Fare.departure_date, Fare.fare, Fare.window, Fare.eligible,
                                  Fare.provider)
                           .where(Fare.route_id == route_id, Fare.collection_date == last)
                           .order_by(Fare.departure_date, Fare.run_id.desc())))
    history = s.execute(select(ProductPrice.window, ProductPrice.price).where(
        ProductPrice.route_id == route_id,
        ProductPrice.collection_date >= last - dt.timedelta(days=TYPICAL_LOOKBACK),
        ProductPrice.collection_date < last)).all()
    by_window: dict[str, list[float]] = defaultdict(list)
    for w, p in history:
        by_window[w].append(p)
    bands = {w: (percentile(sorted(v), 25), percentile(sorted(v), 75))
             for w, v in by_window.items() if len(v) >= 14}
    seen, days = set(), []
    provider = today[0].provider if today else None
    show_prices = bool(provider and POLICIES.get(provider)
                       and POLICIES[provider].raw_redistribution)
    for dep, fare, window, eligible, _ in today:
        if dep in seen:
            continue
        seen.add(dep)
        band = bands.get(window or "")
        level = "unknown"
        if eligible and band:
            level = "above" if fare > band[1] else "below" if fare < band[0] else "typical"
        days.append({"date": dep, "level": level, "window": window,
                     "fare": fare if show_prices and eligible else None})
    return {"as_of": last, "days": days, "show_prices": show_prices}


def status(s: Session, days: int = 30) -> dict:
    since = dt.date.today() - dt.timedelta(days=days)
    runs = list(s.scalars(select(CollectionRun).where(CollectionRun.collection_date >= since)
                          .order_by(CollectionRun.id)))
    providers: dict[str, dict] = {}
    for r in runs:
        p = providers.setdefault(r.provider, {"runs": [], "last": None, "last_ok": None})
        p["runs"].append(r)
        p["last"] = r
        if r.status == "ok":
            p["last_ok"] = r
    for name, p in providers.items():
        by_day: dict[dt.date, str] = {}
        rank = {"ok": 3, "partial": 2, "budget_exhausted": 1, "failed": 0, "running": 0}
        for r in p["runs"]:
            if rank.get(r.status, 0) >= rank.get(by_day.get(r.collection_date, ""), -1):
                by_day[r.collection_date] = r.status
        p["days"] = [{"date": since + dt.timedelta(days=i),
                      "status": by_day.get(since + dt.timedelta(days=i), "none")}
                     for i in range(days + 1)]
        p["policy"] = POLICIES.get(name)
        total = sum(r.routes_requested for r in p["runs"])
        p["route_success_pct"] = (sum(r.routes_ok for r in p["runs"]) / total * 100
                                  if total else None)
    exclusions = dict(s.execute(select(Fare.exclusion_reason, func.count())
                                .where(Fare.eligible.is_(False),
                                       Fare.collection_date >= since)
                                .group_by(Fare.exclusion_reason)).all())
    fares_total = s.scalar(select(func.count()).select_from(Fare)
                           .where(Fare.collection_date >= since)) or 0
    nat = series(s, "national", days=1)
    errors = list(s.scalars(select(RawResponse).where(RawResponse.error.is_not(None))
                            .order_by(RawResponse.id.desc()).limit(10)))
    return {"providers": providers, "exclusions": exclusions, "fares_total": fares_total,
            "coverage": nat[-1].coverage if nat else None, "recent_errors": errors,
            "days": days}


def links(s: Session) -> list[IndexLink]:
    return list(s.scalars(select(IndexLink).where(
        IndexLink.methodology_version == METHODOLOGY_VERSION).order_by(IndexLink.link_period)))


def weights(s: Session) -> list[BasketWeight]:
    return list(s.scalars(select(BasketWeight).order_by(BasketWeight.basket_version,
                                                        BasketWeight.weight.desc())))


def cpi(s: Session) -> list[CpiAirfare]:
    return list(s.scalars(select(CpiAirfare).order_by(CpiAirfare.period)))


def festival_view(s: Session, slug: str) -> dict | None:
    """For each festival route: how the cheapest fare for the peak travel day developed,
    against the same booking distance on ordinary departure dates."""
    fest = next((f for f in load_festivals() if f.slug == slug), None)
    if fest is None:
        return None
    peak = fest.date - dt.timedelta(days=2)
    normal_from, normal_to = fest.date - dt.timedelta(days=42), fest.date - dt.timedelta(days=21)
    routes = []
    for route_id in fest.routes:
        track = s.execute(select(Fare.collection_date, Fare.days_ahead, Fare.fare)
                          .where(Fare.route_id == route_id, Fare.departure_date == peak,
                                 Fare.eligible.is_(True))
                          .order_by(Fare.collection_date, Fare.run_id.desc())).all()
        normal = s.execute(select(Fare.days_ahead, Fare.fare)
                           .where(Fare.route_id == route_id, Fare.eligible.is_(True),
                                  Fare.departure_date.between(normal_from, normal_to))).all()
        if not track:
            continue
        base: dict[int, list[float]] = defaultdict(list)
        for d, f in normal:
            base[d].append(f)
        seen, points = set(), []
        for cd, d, f in track:
            if cd in seen:
                continue
            seen.add(cd)
            ref = statistics.median(base[d]) if len(base.get(d, [])) >= 3 else None
            points.append({"date": cd, "days_ahead": d, "fare": f, "normal": ref,
                           "pct": (f / ref - 1) * 100 if ref else None})
        latest = points[-1]
        routes.append({"route_id": route_id, "name": route_name(route_id),
                       "points": points, "latest": latest})
    routes.sort(key=lambda r: -(r["latest"]["pct"] or -1e9))
    provider = s.scalar(select(Fare.provider).limit(1))
    show = bool(provider and POLICIES.get(provider) and POLICIES[provider].raw_redistribution)
    return {"festival": fest, "peak": peak, "routes": routes, "show_prices": show}


WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def weekday_effect(s: Session, route_id: str | None = None, lookback: int = 30) -> list[dict]:
    """How the cheapest fare differs by departure weekday, as % against that route's median
    for the same booking distance. Departures 8 to 45 days out, last `lookback` collection
    days, so last-minute spikes do not dominate."""
    q = select(Fare.route_id, Fare.days_ahead, Fare.departure_date, Fare.fare).where(
        Fare.eligible.is_(True), Fare.days_ahead.between(8, 45))
    last = s.scalar(select(func.max(Fare.collection_date)))
    if last is None:
        return []
    q = q.where(Fare.collection_date >= last - dt.timedelta(days=lookback - 1))
    if route_id:
        q = q.where(Fare.route_id == route_id)
    rows = s.execute(q).all()
    ref: dict[tuple[str, int], list[float]] = defaultdict(list)
    for r, d, _, f in rows:
        ref[(r, d)].append(f)
    med = {k: statistics.median(v) for k, v in ref.items() if len(v) >= 3}
    by_wd: dict[int, list[float]] = defaultdict(list)
    for r, d, dep, f in rows:
        m = med.get((r, d))
        if m:
            by_wd[dep.weekday()].append(f / m - 1)
    return [{"weekday": WEEKDAYS[i], "pct_vs_typical": statistics.median(by_wd[i]) * 100,
             "fares": len(by_wd[i])} for i in range(7) if len(by_wd.get(i, [])) >= 5]


def movers(s: Session, lag: int = 7, limit: int = 5) -> dict:
    """Routes whose index moved most over the last `lag` days, up and down."""
    out = []
    for route_id in basket_routes(s):
        pts = series(s, "route", route_id, days=lag + 1)
        if len(pts) >= lag + 1 and pts[0].value:
            out.append({"route_id": route_id, "name": route_name(route_id),
                        "change_pct": (pts[-1].value / pts[0].value - 1) * 100,
                        "from": pts[0].date.isoformat(), "to": pts[-1].date.isoformat()})
    out.sort(key=lambda r: r["change_pct"])
    return {"lag_days": lag, "up": list(reversed(out[-limit:])), "down": out[:limit]}


def national_booking_curve(s: Session, lookback: int = 30) -> list[dict]:
    """Across every route: fare at each booking distance as % of that route's own median,
    then the median across routes. Answers "how far ahead is usually cheapest" nationally."""
    last = s.scalar(select(func.max(Fare.collection_date)))
    if last is None:
        return []
    rows = s.execute(select(Fare.route_id, Fare.days_ahead, Fare.fare).where(
        Fare.eligible.is_(True),
        Fare.collection_date >= last - dt.timedelta(days=lookback - 1))).all()
    by_route: dict[str, list[float]] = defaultdict(list)
    for r, _, f in rows:
        by_route[r].append(f)
    route_med = {r: statistics.median(v) for r, v in by_route.items()}
    per_route_day: dict[tuple[str, int], list[float]] = defaultdict(list)
    for r, d, f in rows:
        per_route_day[(r, d)].append(f / route_med[r])
    by_day: dict[int, list[float]] = defaultdict(list)
    for (_, d), v in per_route_day.items():
        if len(v) >= 3:
            by_day[d].append(statistics.median(v))
    return [{"days_ahead": d, "pct_vs_route_median": (statistics.median(v) - 1) * 100,
             "routes": len(v)} for d, v in sorted(by_day.items()) if len(v) >= 5]


def window_label(key: str) -> str:
    return WINDOW_BY_KEY[key].label if key in WINDOW_BY_KEY else key


def airport_list(s: Session | None = None) -> list[dict]:
    routes = basket_routes(s) if s is not None else []
    out = []
    for a in sorted(airports().values(), key=lambda a: a.city):
        out.append({"iata": a.iata, "icao": a.icao, "city": a.city, "city_hi": a.city_hi,
                    "airport": a.airport, "state": a.state, "lat": a.lat, "lon": a.lon,
                    "aliases": list(a.aliases),
                    "routes_from": sorted(r for r in routes if r.startswith(a.iata + "-")),
                    "routes_to": sorted(r for r in routes if r.endswith("-" + a.iata))})
    return out


__all__ = ["WINDOWS", "data_mode", "series", "headline", "route_rows", "booking_curve",
           "departure_calendar", "status", "festival_view", "product_verdict", "movers",
           "weekday_effect", "national_booking_curve"]
