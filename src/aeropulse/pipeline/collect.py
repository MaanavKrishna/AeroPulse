"""One collection run: ask a provider for every basket route, store what came back.

A run never raises because one route failed. Each route's response (or error) is stored,
the run gets a status, and the next scheduled run tries again.
"""
from __future__ import annotations

import datetime as dt
import json
import logging
from zoneinfo import ZoneInfo

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ..core.methodology import HORIZON_DAYS, window_for
from ..core.quality import screen
from ..db.models import CollectionRun, Fare, RawResponse, utcnow
from ..providers.base import Provider
from ..reference import split_route

log = logging.getLogger(__name__)
IST = ZoneInfo("Asia/Kolkata")


def today_ist() -> dt.date:
    return dt.datetime.now(IST).date()


def calls_today(session: Session, provider: str, collection_date: dt.date) -> int:
    return session.scalar(select(func.coalesce(func.sum(CollectionRun.calls), 0)).where(
        CollectionRun.provider == provider,
        CollectionRun.collection_date == collection_date)) or 0


def purge_day(session: Session, provider: str, collection_date: dt.date) -> int:
    """Remove every run for one provider and day. Used to make demo backfills repeatable;
    never called on real data by the scheduler."""
    run_ids = list(session.scalars(select(CollectionRun.id).where(
        CollectionRun.provider == provider, CollectionRun.collection_date == collection_date)))
    if not run_ids:
        return 0
    session.execute(delete(Fare).where(Fare.run_id.in_(run_ids)))
    session.execute(delete(RawResponse).where(RawResponse.run_id.in_(run_ids)))
    session.execute(delete(CollectionRun).where(CollectionRun.id.in_(run_ids)))
    return len(run_ids)


def collect(session: Session, provider: Provider, routes: list[str],
            collection_date: dt.date, *, max_calls_per_day: int,
            horizon: int = HORIZON_DAYS) -> CollectionRun:
    run = CollectionRun(provider=provider.name, collection_date=collection_date,
                        routes_requested=len(routes), is_demo=provider.is_demo)
    session.add(run)
    session.flush()

    used = calls_today(session, provider.name, collection_date)
    start = collection_date + dt.timedelta(days=1)
    end = collection_date + dt.timedelta(days=horizon)
    pending: list[tuple[RawResponse, dict]] = []
    errors: list[str] = []
    budget_hit = False

    for route_id in routes:
        if used + run.calls >= max_calls_per_day:
            budget_hit = True
            break
        origin, destination = split_route(route_id)
        response = provider.cheapest_dates(origin, destination, start, end)
        run.calls += response.calls
        raw = RawResponse(run_id=run.id, provider=provider.name, route_id=route_id,
                          request_json=json.dumps(response.request, sort_keys=True),
                          http_status=response.http_status, payload=response.payload,
                          payload_sha256=response.payload_sha256, error=response.error,
                          observed_at=response.observed_at)
        session.add(raw)
        session.flush()
        if response.error:
            errors.append(f"{route_id}: {response.error}")
            log.warning("%s %s failed: %s", provider.name, route_id, response.error)
            continue
        run.routes_ok += 1
        for f in response.fares:
            days = (f.departure_date - collection_date).days
            window = window_for(days)
            pending.append((raw, {
                "route_id": route_id, "collection_date": collection_date,
                "departure_date": f.departure_date, "days_ahead": days,
                "window": window.key if window else None, "fare": f.fare,
                "currency": f.currency, "carrier": f.carrier,
                "price_status": f.price_status, "observed_at": response.observed_at}))

    screen([row for _, row in pending])
    for raw, row in pending:
        session.add(Fare(run_id=run.id, raw_id=raw.id, provider=provider.name,
                         is_demo=provider.is_demo, **row))
    run.fares_stored = len(pending)

    if budget_hit:
        run.status = "budget_exhausted"
        errors.insert(0, f"daily call cap of {max_calls_per_day} reached")
    elif run.routes_ok == len(routes):
        run.status = "ok"
    elif run.routes_ok:
        run.status = "partial"
    else:
        run.status = "failed"
    run.message = "\n".join(errors[:50]) or None
    run.finished_at = utcnow()
    session.flush()
    return run
