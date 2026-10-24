"""Sampling error for each published index point.

Each product-day price is the median of the cheapest fares across a handful of departure
dates. A different handful would give a different median. The standard error quantifies
that: a **nonparametric bootstrap over departure dates within each product-day**. Resample
the dates with replacement, recompute each median, rebuild the base prices from the same
resample, recompute the index (and the chain), repeat. The spread is the standard error.

What it does NOT capture: whether ~20 busy routes represent all Indian domestic flying.
The basket is chosen by traffic, not probability-sampled, so that uncertainty cannot be
estimated from this data. A ±0.4 interval means "given this basket, date sampling moves
the index by about this much", nothing more. Pages say this next to every interval.
"""
from __future__ import annotations

import datetime as dt
import math
import random
import statistics
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from .index import fares_by_product_day, period_key
from .methodology import MIN_DATES_PER_PRODUCT_DAY, SE_REPLICATIONS, SE_SEED


@dataclass(frozen=True)
class BasketSpec:
    """What one replication needs to rebuild one basket's series."""
    weights: dict[str, float]
    base_from: dt.date
    base_to: dt.date


@dataclass
class Uncertainty:
    period: str
    standard_error: float
    ci95_low: float
    ci95_high: float
    replications: int
    fares: int


def _series(prices: dict[tuple[dt.date, str], float], spec: BasketSpec,
            frequency: str) -> dict[str, float]:
    base_values: dict[str, list[float]] = defaultdict(list)
    for (day, key), price in prices.items():
        if spec.base_from <= day <= spec.base_to and key in spec.weights:
            base_values[key].append(price)
    base = {k: statistics.fmean(v) for k, v in base_values.items()}

    periods: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for (day, key), price in prices.items():
        if key in base and price > 0:
            periods[period_key(day, frequency)[0]][key].append(price)

    out = {}
    for period, by_product in periods.items():
        log_sum = observed = 0.0
        for key, values in by_product.items():
            w = spec.weights.get(key, 0.0)
            if w > 0 and base[key] > 0:
                log_sum += w * math.log(statistics.fmean(values) / base[key])
                observed += w
        if observed > 0:
            out[period] = math.exp(log_sum / observed) * 100.0
    return out


def _splice(series: Sequence[dict[str, float]], link_periods: Sequence[str]) -> dict[str, float]:
    out = dict(series[0])
    for nxt, link in zip(series[1:], link_periods, strict=False):
        if link not in out or not nxt.get(link):
            continue
        factor = out[link] / nxt[link]
        out = {p: v for p, v in out.items() if p <= link}
        out.update({p: v * factor for p, v in nxt.items() if p > link})
    return out


def bootstrap(observations: Iterable[dict], baskets: Sequence[BasketSpec], *,
              link_periods: Sequence[str] = (), frequency: str = "daily",
              replications: int = SE_REPLICATIONS, seed: int = SE_SEED,
              min_dates: int = MIN_DATES_PER_PRODUCT_DAY) -> dict[str, Uncertainty]:
    """Standard errors for each period. With several baskets the chain is rebuilt inside
    every replication, because the link factor is itself estimated from the data.

    Deterministic: same data and seed give the same intervals.
    """
    wanted = set().union(*(b.weights for b in baskets)) if baskets else set()
    buckets = {k: v for k, v in fares_by_product_day(observations).items()
               if k[1] in wanted and len(v) >= min_dates}
    if not buckets:
        return {}
    rng = random.Random(seed)
    ordered = sorted(buckets.items())

    draws: dict[str, list[float]] = defaultdict(list)
    for _ in range(replications):
        resampled = {}
        for key, values in ordered:
            n = len(values)
            resampled[key] = statistics.median(rng.choices(values, k=n))
        series = [_series(resampled, spec, frequency) for spec in baskets]
        for period, value in _splice(series, link_periods).items():
            draws[period].append(value)

    counts: dict[str, int] = defaultdict(int)
    for (day, _), values in buckets.items():
        counts[period_key(day, frequency)[0]] += len(values)

    out = {}
    for period, values in draws.items():
        if len(values) < 2:
            continue
        centre = statistics.fmean(values)
        se = statistics.stdev(values)
        out[period] = Uncertainty(period, se, centre - 1.959964 * se, centre + 1.959964 * se,
                                  len(values), counts[period])
    return out


def change_standard_error(a: Uncertainty, b: Uncertainty) -> float:
    """SE of a change between two points. They share no fares, so variances add."""
    return math.sqrt(a.standard_error ** 2 + b.standard_error ** 2)
