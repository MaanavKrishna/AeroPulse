"""Methodology constants.

Every value here changes what a published number means, so each one is versioned with
METHODOLOGY_VERSION and documented in docs/methodology. Changing any of them is a
methodology change, not a config tweak: bump the version and say why in the changelog.
"""
from __future__ import annotations

from dataclasses import dataclass

#: v3.0 — first version built on licensed provider data. The product is now
#: route × booking window, priced by the cheapest economy fare per departure date.
#: Figures from the v2.x SIH prototype were demo data and are not comparable.
METHODOLOGY_VERSION = "v3.0"


@dataclass(frozen=True)
class Window:
    """A booking window: how far ahead of departure a fare was seen."""
    key: str
    first_day: int
    last_day: int
    label: str          # what a traveller reads
    short: str          # compact form for tables and charts


#: Departures on the collection day itself are excluded: same-day inventory is thin and
#: providers often return nothing or stale fares for it.
WINDOWS: tuple[Window, ...] = (
    Window("1-7", 1, 7, "within a week", "1–7 days"),
    Window("8-14", 8, 14, "1–2 weeks out", "8–14 days"),
    Window("15-30", 15, 30, "2–4 weeks out", "15–30 days"),
    Window("31-60", 31, 60, "1–2 months out", "31–60 days"),
)
WINDOW_BY_KEY = {w.key: w for w in WINDOWS}
HORIZON_DAYS = WINDOWS[-1].last_day

#: Each window counts equally inside a route. There is no public data on how far ahead
#: Indian domestic tickets are bought, so any other split would be invented.
WINDOW_WEIGHT = 1.0 / len(WINDOWS)


def window_for(days_ahead: int) -> Window | None:
    for w in WINDOWS:
        if w.first_day <= days_ahead <= w.last_day:
            return w
    return None


#: The index is 100 at the average price of each product over the first BASE_DAYS days on
#: which that basket version was collected.
BASE_DAYS = 7

#: A product-day needs at least this many departure dates priced, or it is not used.
MIN_DATES_PER_PRODUCT_DAY = 3

#: Plausibility bounds for a one-way economy domestic fare, in rupees. Outside them a fare
#: is treated as a feed error, not a price.
PRICE_FLOOR_INR = 800.0
PRICE_CEILING_INR = 150_000.0

#: Robust z (median / MAD) above which a fare is flagged as an outlier within its
#: product-day. High on purpose: airfares are genuinely volatile.
OUTLIER_Z = 6.0

#: Coverage = share of basket weight that was priced. Below COVERAGE_WARN nothing is
#: published for that point.
COVERAGE_PUBLISH = 80.0
COVERAGE_WARN = 60.0

#: Bootstrap replications behind each standard error, and the seed that makes them
#: reproducible.
SE_REPLICATIONS = 200
SE_SEED = 20261024

#: "Typical" = the middle half (25th–75th percentile) of the previous TYPICAL_LOOKBACK
#: days. A verdict needs at least MIN_HISTORY_FOR_VERDICT days of history.
TYPICAL_LOOKBACK = 90
TYPICAL_LOW_PCT = 25
TYPICAL_HIGH_PCT = 75
MIN_HISTORY_FOR_VERDICT = 21

#: A series younger than this is labelled "early series" everywhere it appears.
EARLY_SERIES_DAYS = 90
