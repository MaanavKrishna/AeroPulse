"""Which fares are allowed into the index, and why the others are not.

Nothing is deleted. A fare that fails a rule keeps its row with `eligible = False` and a
reason, so the status page can count exclusions and anyone can audit them.
"""
from __future__ import annotations

import statistics
from collections import defaultdict
from collections.abc import Iterable

from .index import product_key
from .methodology import OUTLIER_Z, PRICE_CEILING_INR, PRICE_FLOOR_INR

REASONS = {
    "currency": "Price not in rupees",
    "implausible_price": "Price outside the plausible range for a domestic one-way fare",
    "outside_horizon": "Departure date outside the booking windows",
    "outlier": "Far from the other fares in the same route, window and day",
    "demo": "Demo data, never used in production",
}


def robust_z(value: float, values: list[float]) -> float:
    """|x − median| / (1.4826 · MAD). Zero when the spread is zero."""
    med = statistics.median(values)
    mad = statistics.median(abs(v - med) for v in values)
    if mad == 0:
        return 0.0
    return abs(value - med) / (1.4826 * mad)


def screen(fares: Iterable[dict]) -> list[dict]:
    """Set `eligible` and `exclusion_reason` on each fare dict, in place, and return them.

    Rule order matters only for which reason is recorded; any failure excludes the fare.
    """
    rows = list(fares)
    for f in rows:
        reason = None
        if f.get("currency", "INR").upper() != "INR":
            reason = "currency"
        elif f.get("window") is None:
            reason = "outside_horizon"
        elif not (PRICE_FLOOR_INR <= float(f["fare"]) <= PRICE_CEILING_INR):
            reason = "implausible_price"
        f["exclusion_reason"] = reason
        f["eligible"] = reason is None

    groups: dict[tuple, list[dict]] = defaultdict(list)
    for f in rows:
        if f["eligible"]:
            groups[(f["collection_date"], product_key(f["route_id"], f["window"]))].append(f)
    for group in groups.values():
        if len(group) < 5:          # too few to call anything an outlier
            continue
        values = [float(f["fare"]) for f in group]
        for f in group:
            if robust_z(float(f["fare"]), values) > OUTLIER_Z:
                f["eligible"] = False
                f["exclusion_reason"] = "outlier"
    return rows
