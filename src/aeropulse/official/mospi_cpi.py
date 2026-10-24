"""MoSPI CPI airfare series, imported from CSV, used only as an outside benchmark.

Source: MoSPI CPI (base 2024) item-level indices, from the download tables at
https://www.mospi.gov.in/download-tables-data or the CPI API (registration required; see
https://api.mospi.gov.in). Export the airfare item to a CSV:

    period,series,value,base_year,source_url
    2026-08,all_india_combined,104.2,2024,https://...

CPI measures what households paid; AeroPulse measures the cheapest fare on sale. The site
shows the two side by side and never treats either as the other.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import CpiAirfare

REQUIRED = ("period", "series", "value", "base_year", "source_url")
PERIOD = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def import_csv(session: Session, path: str | Path) -> int:
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in REQUIRED if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"missing columns: {', '.join(missing)}")
        rows = list(reader)
    count = 0
    for i, row in enumerate(rows, start=2):
        period = row["period"].strip()
        if not PERIOD.match(period):
            raise ValueError(f"line {i}: period must be YYYY-MM, got {period!r}")
        value = float(row["value"])
        if value <= 0:
            raise ValueError(f"line {i}: value must be positive")
        url = row["source_url"].strip()
        if not url.startswith("https://"):
            raise ValueError(f"line {i}: source_url must be an https link")
        series = row["series"].strip()
        existing = session.scalar(select(CpiAirfare).where(
            CpiAirfare.period == period, CpiAirfare.series == series))
        if existing:
            existing.value, existing.base_year, existing.source_url = \
                value, row["base_year"].strip(), url
        else:
            session.add(CpiAirfare(period=period, series=series, value=value,
                                   base_year=row["base_year"].strip(), source_url=url))
        count += 1
    return count
