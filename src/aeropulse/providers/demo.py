"""Synthetic fares for development and tests. NOT real data.

The generator answers in exactly the shape Ignav does, so the real parser, screening and
index code all run against it. Everything it produces is stored with `is_demo = True`, the
site shows a banner while any demo data is present, and production refuses to start with
this provider configured.

The shape of the numbers is deliberately plausible, so the site can be designed against
something realistic: fares rise sharply inside two weeks, weekends cost more, festival
travel spikes toward home cities and reverses after, and there is day-to-day noise plus the
occasional feed glitch for the screening rules to catch.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import random

from ..reference import load_festivals, split_route
from .base import ProviderResponse
from .ignav import parse_cheapest_dates

#: Rough cheapest one-way fare, in rupees, a month ahead on a quiet week. Invented.
ROUTE_BASE = {
    "DEL-BOM": 4800, "DEL-BLR": 5600, "BOM-BLR": 3600, "DEL-HYD": 5000, "DEL-MAA": 5800,
    "DEL-CCU": 5200, "BLR-HYD": 2900, "BLR-MAA": 2400, "BOM-HYD": 3300, "BOM-MAA": 3900,
    "BLR-CCU": 5600, "BOM-CCU": 5600, "DEL-GOI": 5600, "BOM-GOI": 2900, "DEL-PNQ": 4800,
    "BLR-COK": 2600, "DEL-AMD": 3700, "DEL-SXR": 4600, "DEL-PAT": 4900, "DEL-LKO": 3200,
}
WEEKDAY = {0: 1.00, 1: 0.95, 2: 0.95, 3: 1.00, 4: 1.08, 5: 0.97, 6: 1.10}
EPOCH = dt.date(2026, 1, 1)


def _rng(*parts: object) -> random.Random:
    digest = hashlib.sha256("|".join(map(str, parts)).encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def base_fare(route_id: str) -> float:
    if route_id in ROUTE_BASE:
        return ROUTE_BASE[route_id]
    o, d = split_route(route_id)
    return ROUTE_BASE.get(f"{d}-{o}", 4500) * 1.03


def advance_curve(days_ahead: int) -> float:
    """Expensive at the last minute, cheapest around 3–6 weeks out."""
    return 0.93 + 0.85 * math.exp(-days_ahead / 6.0) + (0.04 if days_ahead > 45 else 0.0)


def festival_factor(route_id: str, departure: dt.date) -> float:
    origin, dest = split_route(route_id)
    factor = 1.0
    for f in load_festivals():
        delta = (f.date - departure).days            # >0: departure before the festival
        going_home = route_id in f.routes
        coming_back = f"{dest}-{origin}" in f.routes
        if going_home and -1 <= delta <= 7:
            factor *= 1.0 + 0.65 * math.exp(-((delta - 2) ** 2) / 8.0)
        if coming_back and -9 <= delta <= -1:
            factor *= 1.0 + 0.45 * math.exp(-((delta + 4) ** 2) / 10.0)
    if (departure.month == 12 and departure.day >= 20) or (departure.month == 1
                                                          and departure.day <= 2):
        if dest in {"GOI", "COK", "SXR"} or origin in {"GOI", "COK", "SXR"}:
            factor *= 1.4
    return factor


def macro_factor(collection_date: dt.date) -> float:
    """Slow market-wide drift, so the national index moves."""
    t = (collection_date - EPOCH).days
    return 1.0 + 0.04 * math.sin(2 * math.pi * t / 120.0) + 0.00015 * t


def demo_fare(route_id: str, collection_date: dt.date, departure: dt.date) -> float | None:
    rng = _rng("fare", route_id, collection_date, departure)
    if rng.random() < 0.04:                     # no fare found for this date
        return None
    days = (departure - collection_date).days
    fare = (base_fare(route_id) * advance_curve(days) * WEEKDAY[departure.weekday()]
            * festival_factor(route_id, departure) * macro_factor(collection_date)
            * math.exp(rng.gauss(0, 0.06)))
    if rng.random() < 0.002:                    # a feed glitch, for screening to catch
        fare *= 6
    return round(fare / 10) * 10 + 9            # fares are usually quoted ending in 9


class DemoProvider:
    name = "demo"
    is_demo = True

    def __init__(self, collection_date: dt.date) -> None:
        self.collection_date = collection_date

    def cheapest_dates(self, origin: str, destination: str, start: dt.date,
                       end: dt.date) -> ProviderResponse:
        route_id = f"{origin}-{destination}"
        body = {"origin": origin, "destination": destination,
                "departure_date_range": {"start": start.isoformat(), "end": end.isoformat()},
                "cabin_class": "economy", "adults": 1, "market": "IN"}
        dates = []
        day = start
        while day <= end:
            fare = demo_fare(route_id, self.collection_date, day)
            dates.append({"departure_date": day.isoformat(), "return_date": None,
                          "price": None if fare is None else
                          {"amount": fare, "currency": "INR", "status": "verified"}})
            day += dt.timedelta(days=1)
        observed = dt.datetime.combine(self.collection_date, dt.time(6, 0), dt.UTC)
        payload = json.dumps({"origin": origin, "destination": destination, "dates": dates,
                              "observed_at": observed.isoformat()})
        fares, observed_at = parse_cheapest_dates(payload)
        return ProviderResponse(self.name, body, 200, payload, observed_at, fares)

    def close(self) -> None:
        pass
