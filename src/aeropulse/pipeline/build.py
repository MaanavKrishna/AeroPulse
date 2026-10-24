"""Build every published series from stored fares. Safe to run any number of times: the
same fares always give the same numbers, and any number that changes is logged as a
revision.

Steps:
1. Take the latest successful answer per route and collection day from the index
   provider (the first one in AEROPULSE_PROVIDERS).
2. Product prices: median cheapest fare per route × window × day.
3. Base prices: each product's mean price over its first BASE_DAYS priced days.
4. Weights: route weight from DGCA traffic if imported, else equal; windows equal.
5. Series: national and per-window (chain-linked across basket versions), per-route.
6. Standard errors: bootstrap over departure dates, chain rebuilt in every replication.
"""
from __future__ import annotations

import datetime as dt
import logging
import math
import random
import statistics
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ..core.index import (
    Point,
    Product,
    Segment,
    base_prices,
    chain_link,
    compute_index,
    fares_by_product_day,
    product_key,
    product_prices,
)
from ..core.methodology import (
    BASE_DAYS,
    METHODOLOGY_VERSION,
    MIN_DATES_PER_PRODUCT_DAY,
    SE_REPLICATIONS,
    SE_SEED,
    WINDOW_WEIGHT,
    WINDOWS,
)
from ..db.models import (
    BasketProduct,
    BasketWeight,
    CollectionRun,
    Fare,
    IndexLink,
    IndexRevision,
    IndexValue,
    ProductPrice,
    RawResponse,
    TrafficStat,
)
from ..reference import BasketVersion

log = logging.getLogger(__name__)


@dataclass
class BuildReport:
    provider: str
    days: int
    product_days: int
    points_written: int
    revisions: int
    links: int
    is_demo: bool


# ----------------------------------------------------------------------------- inputs

def load_observations(session: Session, provider: str) -> tuple[list[dict], bool]:
    """Fares from the latest successful answer per (route, collection day)."""
    latest = (select(Fare.route_id, Fare.collection_date, func.max(Fare.run_id).label("run"))
              .join(RawResponse, RawResponse.id == Fare.raw_id)
              .where(Fare.provider == provider, RawResponse.error.is_(None))
              .group_by(Fare.route_id, Fare.collection_date).subquery())
    rows = session.execute(
        select(Fare.route_id, Fare.window, Fare.collection_date, Fare.departure_date,
               Fare.fare, Fare.eligible, Fare.is_demo)
        .join(latest, (Fare.route_id == latest.c.route_id)
              & (Fare.collection_date == latest.c.collection_date)
              & (Fare.run_id == latest.c.run))).all()
    obs = [{"route_id": r.route_id, "window": r.window, "collection_date": r.collection_date,
            "departure_date": r.departure_date, "fare": r.fare,
            "eligible": r.eligible and r.window is not None} for r in rows]
    return obs, any(r.is_demo for r in rows)


def route_weights(session: Session, version: BasketVersion) -> tuple[dict[str, float], str]:
    """Share of DGCA passengers over the latest 12 imported periods, else equal."""
    periods = list(session.scalars(select(TrafficStat.period).distinct()
                                   .order_by(TrafficStat.period.desc()).limit(12)))
    if periods:
        rows = session.execute(select(TrafficStat.route_id, func.sum(TrafficStat.passengers))
                               .where(TrafficStat.period.in_(periods),
                                      TrafficStat.route_id.in_(version.routes))
                               .group_by(TrafficStat.route_id)).all()
        found = {r: float(p) for r, p in rows if p}
        if len(found) == len(version.routes):
            total = sum(found.values())
            return ({r: found[r] / total for r in version.routes},
                    f"dgca:{min(periods)}..{max(periods)}")
        log.warning("DGCA traffic covers %d of %d basket routes; using equal weights",
                    len(found), len(version.routes))
    n = len(version.routes)
    return {r: 1.0 / n for r in version.routes}, "equal"


def first_days(prices: dict, key: str, start: dt.date, n: int) -> list[dt.date]:
    days = sorted(d for (d, k) in prices if k == key and d >= start)
    return days[:n]


# ----------------------------------------------------------------------------- products

@dataclass
class VersionPlan:
    version: BasketVersion
    end: dt.date | None              # last day priced under this version (the link day)
    products: dict[str, Product]
    weight_source: str
    base_window: dict[str, tuple[dt.date, dt.date]]


def plan_versions(session: Session, versions: list[BasketVersion], prices: dict
                  ) -> list[VersionPlan]:
    """Products and weights per basket version. A product keeps the base price from the
    first version it appeared in, so route sub-indices stay continuous across versions."""
    base_of: dict[str, float] = {}
    base_window: dict[str, tuple[dt.date, dt.date]] = {}
    plans = []
    for i, version in enumerate(versions):
        end = versions[i + 1].valid_from if i + 1 < len(versions) else None
        weights, source = route_weights(session, version)
        products = {}
        for route in version.routes:
            for w in WINDOWS:
                key = product_key(route, w.key)
                if key not in base_of:
                    days = first_days(prices, key, version.valid_from, BASE_DAYS)
                    if len(days) < BASE_DAYS:
                        continue                 # not enough history to fix a base yet
                    base = base_prices(prices, days[0], days[-1])
                    if key not in base:
                        continue
                    base_of[key] = base[key]
                    base_window[key] = (days[0], days[-1])
                products[key] = Product(key, route, w.key, weights[route] * WINDOW_WEIGHT,
                                        base_of[key])
        plans.append(VersionPlan(version, end, products, source,
                                 {k: base_window[k] for k in products}))
    return plans


def _slice(prices: dict, start: dt.date, end: dt.date | None) -> dict:
    return {k: v for k, v in prices.items() if k[0] >= start and (end is None or k[0] <= end)}


def segments_for(plans: list[VersionPlan], prices: dict, **select_kw) -> list[Segment]:
    segs = []
    for plan in plans:
        if not plan.products:
            continue
        points = compute_index(_slice(prices, plan.version.valid_from, plan.end),
                               plan.products, "daily", **select_kw)
        if points:
            segs.append(Segment(plan.version.version, points))
    return segs


# ----------------------------------------------------------------------------- uncertainty

def bootstrap_all(observations: list[dict], plans: list[VersionPlan], scopes: dict,
                  replications: int = SE_REPLICATIONS, seed: int = SE_SEED) -> dict:
    """Standard errors for many series from one set of resamples.

    `scopes` maps a name to a predicate over products. For each replication the departure
    dates in every product-day are resampled once; every scope's series (and chain) is then
    rebuilt from that same resample, with base prices re-estimated from it too.
    """
    buckets = {k: v for k, v in fares_by_product_day(observations).items()
               if len(v) >= MIN_DATES_PER_PRODUCT_DAY}
    all_keys = {k for p in plans for k in p.products}
    ordered = sorted((k, v) for k, v in buckets.items() if k[1] in all_keys)
    rng = random.Random(seed)
    draws: dict[str, dict[str, list[float]]] = {s: defaultdict(list) for s in scopes}

    for _ in range(replications):
        by_product: dict[str, list[tuple[dt.date, float]]] = defaultdict(list)
        for (day, key), values in ordered:
            n = len(values)
            by_product[key].append(
                (day, statistics.median(rng.choices(values, k=n))))
        for scope, predicate in scopes.items():
            series = None
            for plan in plans:
                seg = _rep_series(by_product, plan, predicate)
                if not seg:
                    continue
                if series is None:
                    series = seg
                    continue
                link = max((p for p in seg if p in series), default=None)
                if link is None or not seg[link]:
                    continue
                factor = series[link] / seg[link]
                series = {p: v for p, v in series.items() if p <= link}
                series.update({p: v * factor for p, v in seg.items() if p > link})
            for period, value in (series or {}).items():
                draws[scope][period].append(value)

    out: dict[str, dict[str, tuple[float, float, float]]] = {}
    for scope, periods in draws.items():
        out[scope] = {}
        for period, values in periods.items():
            if len(values) >= 2:
                c, se = statistics.fmean(values), statistics.stdev(values)
                out[scope][period] = (se, c - 1.959964 * se, c + 1.959964 * se)
    return out


def _rep_series(by_product: dict, plan: VersionPlan, predicate) -> dict[str, float]:
    start, end = plan.version.valid_from, plan.end
    selected = {k: p for k, p in plan.products.items() if predicate(p)}
    if not selected:
        return {}
    per_day: dict[dt.date, list[tuple[float, float]]] = defaultdict(list)
    for key, prod in selected.items():
        rows = by_product.get(key, [])
        b_from, b_to = plan.base_window[key]
        base_vals = [p for d, p in rows if b_from <= d <= b_to]
        if not base_vals:
            continue
        base = statistics.fmean(base_vals)
        for day, price in rows:
            if day >= start and (end is None or day <= end) and price > 0:
                per_day[day].append((prod.weight, math.log(price / base)))
    return {d.isoformat(): math.exp(sum(w * x for w, x in v) / sum(w for w, _ in v)) * 100
            for d, v in per_day.items() if v}


# ----------------------------------------------------------------------------- writing

def _store(session: Session, existing: dict, *, scope: str, route_id: str, window: str,
           point, kind: str, version: str, se, is_demo: bool, reason: str) -> int:
    key = (scope, route_id, window, "daily", point.period, kind)
    row = existing.get(key)
    se_val, lo, hi = se if se else (None, None, None)
    revisions = 0
    if row is None:
        row = IndexValue(scope=scope, route_id=route_id, window=window, frequency="daily",
                         period=point.period, period_start=point.period_start, kind=kind,
                         methodology_version=METHODOLOGY_VERSION, revision=0,
                         value=point.value)
        session.add(row)
        existing[key] = row
    elif abs(row.value - point.value) > 1e-9:
        session.flush()
        session.add(IndexRevision(index_value_id=row.id, revision=row.revision + 1,
                                  old_value=row.value, new_value=point.value, reason=reason))
        row.revision += 1
        revisions = 1
    row.value = point.value
    row.coverage = point.coverage
    row.status = point.status
    row.observation_count = point.observation_count
    row.product_count = getattr(point, "product_count", 0)
    row.standard_error, row.ci95_low, row.ci95_high = se_val, lo, hi
    row.basket_version = version
    row.is_demo = is_demo
    return revisions


def build(session: Session, versions: list[BasketVersion], provider: str, *,
          reason: str = "scheduled rebuild", replications: int = SE_REPLICATIONS
          ) -> BuildReport:
    observations, is_demo = load_observations(session, provider)
    prices = product_prices(observations)

    # product prices (gold, used by the site for rupee levels)
    session.execute(delete(ProductPrice))
    fares_by = fares_by_product_day(observations)
    for (day, key), row in prices.items():
        fares = fares_by[(day, key)]
        session.add(ProductPrice(collection_date=day, route_id=row["route_id"],
                                 window=row["window"], price=row["price"], low=min(fares),
                                 high=max(fares), dates=row["n"], provider=provider,
                                 is_demo=is_demo))

    plans = plan_versions(session, versions, prices)
    session.execute(delete(BasketWeight))
    for plan in plans:
        weights, _ = route_weights(session, plan.version)
        for route in plan.version.routes:
            windows = [plan.base_window[k] for k in plan.products
                       if k.startswith(route + "/")]
            session.add(BasketWeight(
                basket_version=plan.version.version, route_id=route, weight=weights[route],
                source=plan.weight_source,
                base_from=min((w[0] for w in windows), default=None),
                base_to=max((w[1] for w in windows), default=None)))

    session.execute(delete(BasketProduct))
    for plan in plans:
        for key, prod in plan.products.items():
            b_from, b_to = plan.base_window[key]
            session.add(BasketProduct(
                basket_version=plan.version.version, valid_from=plan.version.valid_from,
                valid_to=plan.end, route_id=prod.route_id, window=prod.window,
                weight=prod.weight, base_price=prod.base_price, base_from=b_from,
                base_to=b_to))

    existing = {(r.scope, r.route_id, r.window, r.frequency, r.period, r.kind): r
                for r in session.scalars(select(IndexValue).where(
                    IndexValue.methodology_version == METHODOLOGY_VERSION))}

    routes = sorted({p.route_id for plan in plans for p in plan.products.values()})
    scopes = {"national": lambda p: True}
    scopes.update({f"window:{w.key}": (lambda p, k=w.key: p.window == k) for w in WINDOWS})
    scopes.update({f"route:{r}": (lambda p, r=r: p.route_id == r) for r in routes})
    errors = bootstrap_all(observations, plans, scopes, replications=replications) \
        if replications else {}

    written = revisions = 0
    session.execute(delete(IndexLink).where(
        IndexLink.methodology_version == METHODOLOGY_VERSION))
    link_count = 0

    def publish(scope_name, scope, route_id, window, segs):
        nonlocal written, revisions, link_count
        if not segs:
            return
        linked, links = chain_link(segs)
        for lk in links:
            session.add(IndexLink(scope=scope_name, from_version=lk.from_version,
                                  to_version=lk.to_version, link_period=lk.link_period,
                                  old_level=lk.old_level, new_level=lk.new_level,
                                  factor=lk.factor, methodology_version=METHODOLOGY_VERSION))
            link_count += 1
        product_counts = {p.period: p.product_count for s in segs for p in s.points}
        for lp in linked:
            lp.product_count = product_counts.get(lp.period, 0)
            revisions += _store(session, existing, scope=scope, route_id=route_id,
                                window=window, point=lp, kind="CHAINED", version=lp.version,
                                se=errors.get(scope_name, {}).get(lp.period),
                                is_demo=is_demo, reason=reason)
            written += 1
        first = segs[0]
        for p in first.points:
            revisions += _store(session, existing, scope=scope, route_id=route_id,
                                window=window, point=p, kind="FIXED", version=first.version,
                                se=None, is_demo=is_demo, reason=reason)

    publish("national", "national", "", "", segments_for(plans, prices))
    for w in WINDOWS:
        publish(f"window:{w.key}", "window", "", w.key,
                segments_for(plans, prices, window=w.key))
    for r in routes:
        # A route sub-index is invariant to route weights and keeps its products' bases,
        # so it needs no link: computing it on the latest plan that contains it is exact.
        plan = next(p for p in reversed(plans)
                    if any(x.route_id == r for x in p.products.values()))
        points: list[Point] = compute_index(prices, plan.products, "daily", route=r)
        seg = [Segment(plan.version.version, points)] if points else []
        publish(f"route:{r}", "route", r, "", seg)

    session.flush()
    return BuildReport(provider, len({d for d, _ in prices}), len(prices), written, revisions,
                       link_count, is_demo)


def latest_run(session: Session, provider: str) -> CollectionRun | None:
    return session.scalars(select(CollectionRun).where(CollectionRun.provider == provider)
                           .order_by(CollectionRun.id.desc()).limit(1)).first()
