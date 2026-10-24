"""Index construction. Pure functions: no database, no network.

    PriceRelative(i, t) = P(i, t) / P(i, base)
    Index(t)            = exp( Σ w_i · ln PriceRelative(i, t) / Σ w_i ) × 100

A weighted geometric mean of price relatives (Jevons). The arithmetic form (Carli) fails
the time-reversal test and is prohibited in the European HICP; on volatile prices like
airfares its upward bias is large. Jevons is transitive for a fixed basket, which is what
makes a daily series chainable.

The statistical product `i` is a route × booking window (for example DEL-BOM, 15–30 days
ahead). Its price on a collection day, P(i, t), is the **median of the cheapest economy
fares across the departure dates in that window**. So on 1 Nov the DEL-BOM 8–14 product
is the median of the cheapest fares for departures on 9–15 Nov.

That makes this a *cheapest-available-fare* index. It tracks what the lowest fare on the
market is doing, not what the average passenger paid. CPI airfare measures something
closer to the second. The two are related but not the same, and every page says so.
"""
from __future__ import annotations

import datetime as dt
import math
import statistics
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field

from .methodology import COVERAGE_PUBLISH, COVERAGE_WARN, MIN_DATES_PER_PRODUCT_DAY


def product_key(route_id: str, window: str) -> str:
    return f"{route_id}/{window}"


@dataclass(frozen=True)
class Product:
    key: str
    route_id: str
    window: str
    weight: float
    base_price: float


@dataclass
class Contribution:
    """One product's share of a published point, in log space (where Jevons is additive)."""
    route_id: str
    window: str
    price_relative: float
    weight: float
    weighted_log: float
    dates: int


@dataclass
class Point:
    period: str
    period_start: dt.date
    period_end: dt.date
    value: float
    coverage: float
    observation_count: int
    product_count: int
    status: str
    contributions: list[Contribution] = field(default_factory=list)


def logarithmic_mean(a: float, b: float) -> float:
    """L(a, b) = (a − b) / (ln a − ln b), with L(a, a) = a.

    Converts a change in log points to index points with no residual, so a decomposition
    built on log contributions sums exactly to the published movement.
    """
    if a <= 0 or b <= 0:
        return 0.0
    if abs(a - b) < 1e-12:
        return a
    return (a - b) / (math.log(a) - math.log(b))


def coverage_status(coverage: float) -> str:
    if coverage >= COVERAGE_PUBLISH:
        return "valid"
    return "provisional" if coverage >= COVERAGE_WARN else "insufficient_data"


def period_key(day: dt.date, frequency: str) -> tuple[str, dt.date, dt.date]:
    if frequency == "daily":
        return day.isoformat(), day, day
    if frequency == "weekly":
        start = day - dt.timedelta(days=day.weekday())
        iso = start.isocalendar()
        return f"{iso.year}-W{iso.week:02d}", start, start + dt.timedelta(days=6)
    if frequency == "monthly":
        start = day.replace(day=1)
        nxt = (start + dt.timedelta(days=32)).replace(day=1)
        return start.strftime("%Y-%m"), start, nxt - dt.timedelta(days=1)
    raise ValueError(f"unknown frequency {frequency!r}")


def fares_by_product_day(observations: Iterable[dict]) -> dict[tuple[dt.date, str], list[float]]:
    """Eligible cheapest fares grouped by the product-day whose price they determine.

    Each observation is one departure date's cheapest fare, seen on one collection day:
    ``{route_id, window, collection_date, fare, eligible}``.
    """
    buckets: dict[tuple[dt.date, str], list[float]] = defaultdict(list)
    for o in observations:
        if o.get("eligible") and o.get("fare") is not None and o["fare"] > 0:
            buckets[(o["collection_date"], product_key(o["route_id"], o["window"]))].append(
                float(o["fare"]))
    return buckets


def product_prices(observations: Iterable[dict],
                   min_dates: int = MIN_DATES_PER_PRODUCT_DAY) -> dict:
    """One price per (collection day, product): the median across departure dates.

    A product-day with fewer than `min_dates` priced departure dates is dropped. Coverage
    falls instead of the index being driven by one or two dates.
    """
    out = {}
    for (day, key), fares in fares_by_product_day(observations).items():
        if len(fares) < min_dates:
            continue
        route_id, window = key.split("/")
        out[(day, key)] = {"price": statistics.median(fares), "n": len(fares),
                           "route_id": route_id, "window": window}
    return out


def _by_period(prices: dict, frequency: str) -> dict:
    """Weekly and monthly prices are the mean of daily product prices, not resampled
    index values, so a product missing for part of a month lowers coverage rather than
    silently changing the basket."""
    periods: dict = {}
    for (day, pkey), row in prices.items():
        pk, start, end = period_key(day, frequency)
        slot = periods.setdefault(pk, {"start": start, "end": end, "p": {}})
        acc = slot["p"].setdefault(pkey, {"prices": [], "n": 0, "meta": row})
        acc["prices"].append(row["price"])
        acc["n"] += row["n"]
    return {pk: (v["start"], v["end"], {
        pkey: {**acc["meta"], "price": statistics.fmean(acc["prices"]), "n": acc["n"]}
        for pkey, acc in v["p"].items()}) for pk, v in periods.items()}


def base_prices(prices: dict, base_from: dt.date, base_to: dt.date) -> dict[str, float]:
    """Mean daily price of each product over the base window."""
    values: dict[str, list[float]] = defaultdict(list)
    for (day, key), row in prices.items():
        if base_from <= day <= base_to:
            values[key].append(row["price"])
    return {k: statistics.fmean(v) for k, v in values.items() if v}


def compute_index(prices: dict, products: dict[str, Product], frequency: str = "daily", *,
                  route: str | None = None, window: str | None = None) -> list[Point]:
    selected = {k: p for k, p in products.items()
                if (route is None or p.route_id == route)
                and (window is None or p.window == window)}
    total_weight = sum(p.weight for p in selected.values())
    if total_weight <= 0:
        return []

    points = []
    for pk, (start, end, period_products) in sorted(_by_period(prices, frequency).items()):
        log_sum = observed = 0.0
        obs, contributions = 0, []
        for pkey, prod in selected.items():
            row = period_products.get(pkey)
            if row is None or prod.base_price <= 0 or row["price"] <= 0:
                continue
            relative = row["price"] / prod.base_price
            weighted_log = prod.weight * math.log(relative)
            log_sum += weighted_log
            observed += prod.weight
            obs += row["n"]
            contributions.append(Contribution(prod.route_id, prod.window, relative * 100.0,
                                              prod.weight, weighted_log, row["n"]))
        if observed <= 0:
            continue
        coverage = observed / total_weight * 100.0
        points.append(Point(pk, start, end, math.exp(log_sum / observed) * 100.0, coverage,
                            obs, len(contributions), coverage_status(coverage),
                            contributions))
    return points


# --------------------------------------------------------------------------- chaining

@dataclass
class Segment:
    """A stretch of the series computed on one basket version."""
    version: str
    points: list[Point]


@dataclass
class Link:
    from_version: str
    to_version: str
    link_period: str
    old_level: float
    new_level: float
    factor: float


@dataclass
class LinkedPoint:
    period: str
    period_start: dt.date
    period_end: dt.date
    value: float
    version: str
    is_link_period: bool
    coverage: float
    observation_count: int
    status: str


def chain_link(segments: Sequence[Segment]) -> tuple[list[LinkedPoint], list[Link]]:
    """Splice consecutive baskets into one continuous series (one-period overlap).

    Both baskets are computed for a period they share. The ratio of their levels there is
    the link factor; the incoming basket is rescaled by it and carries on. Growth inside
    each basket passes through untouched and the link itself adds no movement.
    """
    if not segments:
        return [], []

    linked = [LinkedPoint(p.period, p.period_start, p.period_end, p.value,
                          segments[0].version, False, p.coverage, p.observation_count,
                          p.status) for p in segments[0].points]
    links: list[Link] = []
    previous = segments[0]

    for segment in segments[1:]:
        previous_periods = {p.period for p in previous.points}
        overlap = [p for p in segment.points if p.period in previous_periods]
        if not overlap:
            raise ValueError(
                f"cannot link {previous.version} to {segment.version}: the baskets share "
                f"no period. A splice needs both baskets priced in the same period.")
        link_point = overlap[-1]
        old_level = next(x.value for x in linked if x.period == link_point.period)
        factor = old_level / link_point.value
        links.append(Link(previous.version, segment.version, link_point.period,
                          old_level, link_point.value, factor))

        linked = [x for x in linked if x.period <= link_point.period]
        for x in linked:
            if x.period == link_point.period:
                x.is_link_period = True
        for p in segment.points:
            if p.period > link_point.period:
                linked.append(LinkedPoint(p.period, p.period_start, p.period_end,
                                          p.value * factor, segment.version, False,
                                          p.coverage, p.observation_count, p.status))
        previous = segment

    linked.sort(key=lambda x: x.period)
    return linked, links


# --------------------------------------------------------------------------- attribution

def decompose(points: Sequence[Point], lag: int = 7) -> dict:
    """Attribute the change over `lag` periods to routes and booking windows.

    Exact by construction: the index is additive in log space, and the logarithmic mean
    converts log contributions back to index points with no residual.
    """
    if len(points) < 2:
        return {"routes": [], "windows": [], "total_points": 0.0, "total_pct": 0.0}
    t1, t0 = points[-1], points[max(0, len(points) - 1 - lag)]
    scale = logarithmic_mean(t1.value, t0.value)

    def shares(p: Point, attr: str) -> tuple[dict, dict]:
        total = sum(c.weight for c in p.contributions) or 1.0
        share: dict = defaultdict(float)
        own: dict = defaultdict(float)
        own_weight: dict = defaultdict(float)
        for c in p.contributions:
            k = getattr(c, attr)
            share[k] += c.weighted_log / total
            own[k] += c.weighted_log
            own_weight[k] += c.weight
        return share, {k: own[k] / own_weight[k] for k in own if own_weight[k]}

    (r1, rin1), (r0, rin0) = shares(t1, "route_id"), shares(t0, "route_id")
    (w1, win1), (w0, win0) = shares(t1, "window"), shares(t0, "window")

    routes = sorted(({"route_id": k,
                      "points": scale * (r1[k] - r0.get(k, r1[k])),
                      "change_pct": (math.exp(rin1[k] - rin0.get(k, rin1[k])) - 1) * 100}
                     for k in r1), key=lambda x: -x["points"])
    windows = [{"window": k, "points": scale * (w1[k] - w0.get(k, w1[k])),
                "change_pct": (math.exp(win1[k] - win0.get(k, win1[k])) - 1) * 100}
               for k in sorted(w1, key=lambda x: int(x.split("-")[0]))]
    return {"from_period": t0.period, "to_period": t1.period, "lag": lag,
            "routes": routes, "windows": windows,
            "total_points": t1.value - t0.value,
            "total_pct": (t1.value / t0.value - 1) * 100}
