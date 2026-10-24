"""DGCA domestic passenger traffic, imported from a CSV you prepare from DGCA's published
city-pair tables (https://www.dgca.gov.in, "Traffic data").

DGCA publishes these as PDF/Excel. We do not scrape them: download the release, copy the
city-pair rows into a CSV with the columns below, and import it. Keep the source URL of the
release in each row so every weight can be traced.

    period,origin,destination,passengers,source_url
    2026-08,DEL,BOM,412345,https://www.dgca.gov.in/...

If DGCA reports a city pair for both directions combined, add two rows and split it
evenly, and note that in the commit that adds the file. Never type in numbers that are
not in the release.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import TrafficStat
from ..reference import airports

REQUIRED = ("period", "origin", "destination", "passengers", "source_url")
PERIOD = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$|^\d{4}-Q[1-4]$")


class ImportErrorRow(ValueError):
    pass


def import_csv(session: Session, path: str | Path) -> int:
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in REQUIRED if c not in (reader.fieldnames or [])]
        if missing:
            raise ImportErrorRow(f"missing columns: {', '.join(missing)}")
        rows = list(reader)
    known = airports()
    count = 0
    for i, row in enumerate(rows, start=2):
        period = row["period"].strip()
        o, d = row["origin"].strip().upper(), row["destination"].strip().upper()
        if not PERIOD.match(period):
            raise ImportErrorRow(f"line {i}: period must be YYYY-MM or YYYY-Qn, got {period!r}")
        if o not in known or d not in known:
            raise ImportErrorRow(f"line {i}: unknown airport in {o}-{d}; add it to "
                                 "src/aeropulse/data/airports.json first")
        try:
            pax = int(row["passengers"].replace(",", "").strip())
        except ValueError as exc:
            raise ImportErrorRow(f"line {i}: passengers is not a whole number") from exc
        if pax < 0:
            raise ImportErrorRow(f"line {i}: passengers cannot be negative")
        url = row["source_url"].strip()
        if not url.startswith("https://"):
            raise ImportErrorRow(f"line {i}: source_url must be an https link to the release")
        route_id = f"{o}-{d}"
        existing = session.scalar(select(TrafficStat).where(
            TrafficStat.period == period, TrafficStat.route_id == route_id))
        if existing:
            existing.passengers, existing.source_url = pax, url
        else:
            session.add(TrafficStat(period=period, route_id=route_id, passengers=pax,
                                    source_url=url))
        count += 1
    return count
