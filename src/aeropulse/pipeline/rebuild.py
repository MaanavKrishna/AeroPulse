"""Recompute the published index from the open dataset alone: no database, no provider.

Anyone can run `aeropulse rebuild <export dir>` and check that the numbers we publish
follow from the numbers we publish. Point values are reproduced exactly. Standard errors
need departure-date fares, which are not in the export, so they are not rebuilt here.
"""
from __future__ import annotations

import csv
import datetime as dt
from collections import defaultdict
from pathlib import Path

from ..core.index import Product, Segment, chain_link, compute_index, product_key


def _read(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def rebuild_from_export(directory: str | Path) -> dict[str, float]:
    d = Path(directory)
    prices = {}
    for r in _read(d / "product_prices.csv"):
        prices[(dt.date.fromisoformat(r["date"]), product_key(r["route"], r["window"]))] = {
            "price": float(r["median_cheapest_fare_inr"]),
            "n": int(r["departure_dates_priced"]), "route_id": r["route"], "window": r["window"]}

    versions: dict[str, dict] = defaultdict(lambda: {"products": {}})
    for b in _read(d / "basket_products.csv"):
        v = versions[b["basket_version"]]
        v["start"] = dt.date.fromisoformat(b["valid_from"])
        v["end"] = dt.date.fromisoformat(b["valid_to"]) if b["valid_to"] else None
        key = product_key(b["route"], b["window"])
        v["products"][key] = Product(key, b["route"], b["window"], float(b["weight"]),
                                     float(b["base_price_inr"]))

    segments = []
    for name, v in sorted(versions.items(), key=lambda kv: kv[1]["start"]):
        window = {k: p for k, p in prices.items()
                  if k[0] >= v["start"] and (v["end"] is None or k[0] <= v["end"])}
        points = compute_index(window, v["products"], "daily")
        if points:
            segments.append(Segment(name, points))
    linked, _ = chain_link(segments)
    return {p.period: p.value for p in linked}


def compare(directory: str | Path, tolerance: float = 1e-6) -> tuple[int, list[str]]:
    """(points checked, mismatches) against the published national chained series."""
    rebuilt = rebuild_from_export(directory)
    published = {r["date"]: float(r["value"]) for r in _read(Path(directory) / "index_values.csv")
                 if r["scope"] == "national" and r["kind"] == "CHAINED"}
    bad = [f"{p}: published {published[p]:.6f}, rebuilt {rebuilt.get(p)}"
           for p in published if p not in rebuilt or abs(published[p] - rebuilt[p]) > tolerance]
    return len(published), bad
