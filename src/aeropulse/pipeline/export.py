"""The open dataset: CSV files plus a manifest with row counts and SHA-256 checksums.

Published: index series, product prices (daily median cheapest fare per route and window),
basket weights, chain links, revisions. Not published: individual departure-date fares,
unless the provider's terms allow it (see providers/policy.py).
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..core.methodology import METHODOLOGY_VERSION
from ..db.models import (
    BasketProduct,
    BasketWeight,
    IndexLink,
    IndexRevision,
    IndexValue,
    ProductPrice,
)

MANIFEST = "manifest.json"


def _write(directory: Path, name: str, header: list[str], rows) -> dict:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    n = 0
    for row in rows:
        w.writerow(row)
        n += 1
    data = buf.getvalue().encode("utf-8")
    (directory / name).write_bytes(data)
    return {"name": name, "rows": n, "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def export(session: Session, out: str | Path) -> dict:
    directory = Path(out)
    directory.mkdir(parents=True, exist_ok=True)
    files = []

    values = list(session.scalars(select(IndexValue).order_by(
        IndexValue.scope, IndexValue.route_id, IndexValue.window, IndexValue.kind,
        IndexValue.period_start)))
    is_demo = any(v.is_demo for v in values)
    f = _write(directory, "index_values.csv",
               ["date", "scope", "route", "window", "kind", "value", "ci95_low", "ci95_high",
                "standard_error", "coverage_pct", "status", "fares_used", "products",
                "basket_version", "methodology_version", "revision", "is_demo"],
               ([v.period, v.scope, v.route_id, v.window, v.kind, f"{v.value:.6f}",
                 "" if v.ci95_low is None else f"{v.ci95_low:.6f}",
                 "" if v.ci95_high is None else f"{v.ci95_high:.6f}",
                 "" if v.standard_error is None else f"{v.standard_error:.6f}",
                 f"{v.coverage:.2f}", v.status, v.observation_count, v.product_count,
                 v.basket_version, v.methodology_version, v.revision,
                 str(v.is_demo).lower()] for v in values))
    f["description"] = ("Every published index point: national, per route and per booking "
                        "window, chained (published) and fixed-basket (reference).")
    files.append(f)

    f = _write(directory, "product_prices.csv",
               ["date", "route", "window", "median_cheapest_fare_inr", "lowest_inr",
                "highest_inr", "departure_dates_priced", "provider", "is_demo"],
               ([p.collection_date.isoformat(), p.route_id, p.window, repr(p.price),
                 f"{p.low:.2f}", f"{p.high:.2f}", p.dates, p.provider,
                 str(p.is_demo).lower()]
                for p in session.scalars(select(ProductPrice).order_by(
                    ProductPrice.route_id, ProductPrice.window,
                    ProductPrice.collection_date))))
    f["description"] = ("Daily median of the cheapest fares across departure dates, per route "
                        "and booking window. The input to the index.")
    files.append(f)

    f = _write(directory, "basket_weights.csv",
               ["basket_version", "route", "weight", "source", "base_from", "base_to"],
               ([w.basket_version, w.route_id, f"{w.weight:.8f}", w.source,
                 w.base_from or "", w.base_to or ""]
                for w in session.scalars(select(BasketWeight))))
    f["description"] = "Route weights per basket version and where they came from."
    files.append(f)

    f = _write(directory, "basket_products.csv",
               ["basket_version", "valid_from", "valid_to", "route", "window", "weight",
                "base_price_inr", "base_from", "base_to"],
               ([b.basket_version, b.valid_from, b.valid_to or "", b.route_id, b.window,
                 repr(b.weight), repr(b.base_price), b.base_from, b.base_to]
                for b in session.scalars(select(BasketProduct).order_by(
                    BasketProduct.basket_version, BasketProduct.route_id,
                    BasketProduct.window))))
    f["description"] = ("Every statistical product per basket version: weight, base price "
                        "and base days. With product_prices.csv this rebuilds the index.")
    files.append(f)

    f = _write(directory, "index_links.csv",
               ["series", "from_version", "to_version", "link_date", "old_level",
                "new_level", "factor"],
               ([lk.scope, lk.from_version, lk.to_version, lk.link_period,
                 f"{lk.old_level:.6f}", f"{lk.new_level:.6f}", f"{lk.factor:.8f}"]
                for lk in session.scalars(select(IndexLink))))
    f["description"] = "Chain links applied when the basket changed."
    files.append(f)

    f = _write(directory, "index_revisions.csv",
               ["index_value_id", "revision", "old_value", "new_value", "reason",
                "revised_at"],
               ([r.index_value_id, r.revision, f"{r.old_value:.6f}", f"{r.new_value:.6f}",
                 r.reason, r.revised_at.isoformat()]
                for r in session.scalars(select(IndexRevision))))
    f["description"] = "Every published value that later changed, with the old value."
    files.append(f)

    manifest = {"generated_at": dt.datetime.now(dt.UTC).isoformat(),
                "methodology_version": METHODOLOGY_VERSION, "is_demo": is_demo,
                "licence": "CC BY 4.0", "attribution": "AeroPulse",
                "directory": str(directory), "files": files}
    (directory / MANIFEST).write_text(json.dumps(manifest, indent=2), "utf-8")
    return manifest


def read_manifest() -> dict | None:
    path = Path(get_settings().export_dir) / MANIFEST
    if not path.exists():
        return None
    return json.loads(path.read_text("utf-8"))


def export_path(name: str) -> Path | None:
    """Only files listed in the manifest are served, so no path tricks reach the disk."""
    manifest = read_manifest()
    if not manifest:
        return None
    names = {f["name"] for f in manifest["files"]} | {MANIFEST}
    if name not in names:
        return None
    return Path(get_settings().export_dir) / name
