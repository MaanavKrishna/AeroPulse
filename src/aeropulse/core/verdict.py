"""The answer to "is this fare high right now?", in a form that can be tested.

Typical is the middle half of the recent past: the 25th to 75th percentile of the
previous TYPICAL_LOOKBACK days, today excluded. Above that band is "higher than usual",
below it "lower than usual". With less than MIN_HISTORY_FOR_VERDICT days of history there
is no verdict at all, because a band built on a fortnight of data would be noise.

This describes the past. It never predicts.
"""
from __future__ import annotations

import datetime as dt
import statistics
from collections.abc import Sequence
from dataclasses import dataclass

from .methodology import (
    MIN_HISTORY_FOR_VERDICT,
    TYPICAL_HIGH_PCT,
    TYPICAL_LOOKBACK,
    TYPICAL_LOW_PCT,
)


@dataclass(frozen=True)
class Verdict:
    level: str                  # "above" | "typical" | "below" | "unknown"
    value: float | None
    median: float | None
    low: float | None
    high: float | None
    pct_vs_median: float | None
    history_days: int
    as_of: dt.date | None

    @property
    def headline(self) -> str:
        return {"above": "Higher than usual", "below": "Lower than usual",
                "typical": "About usual", "unknown": "Not enough history yet"}[self.level]


def percentile(sorted_values: Sequence[float], pct: float) -> float:
    """Linear interpolation between closest ranks (the same as numpy's default)."""
    if not sorted_values:
        raise ValueError("no values")
    k = (len(sorted_values) - 1) * pct / 100.0
    lo = int(k)
    hi = min(lo + 1, len(sorted_values) - 1)
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (k - lo)


def verdict(series: Sequence[tuple[dt.date, float]], *,
            lookback: int = TYPICAL_LOOKBACK,
            min_history: int = MIN_HISTORY_FOR_VERDICT) -> Verdict:
    """Verdict for the last point of `series` against the days before it."""
    if not series:
        return Verdict("unknown", None, None, None, None, None, 0, None)
    ordered = sorted(series)
    as_of, value = ordered[-1]
    start = as_of - dt.timedelta(days=lookback)
    history = sorted(v for d, v in ordered[:-1] if start <= d < as_of)
    if len(history) < min_history:
        return Verdict("unknown", value, None, None, None, None, len(history), as_of)
    low = percentile(history, TYPICAL_LOW_PCT)
    high = percentile(history, TYPICAL_HIGH_PCT)
    med = statistics.median(history)
    level = "above" if value > high else "below" if value < low else "typical"
    return Verdict(level, value, med, low, high, (value / med - 1) * 100 if med else None,
                   len(history), as_of)
