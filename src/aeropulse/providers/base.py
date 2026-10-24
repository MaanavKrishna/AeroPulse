"""What every fare provider must do: given a route and a range of departure dates, return
the cheapest economy one-way fare for each date, plus exactly what it received."""
from __future__ import annotations

import datetime as dt
import hashlib
from dataclasses import dataclass, field
from typing import Protocol


class ProviderError(Exception):
    """The provider could not answer. The run records it and moves to the next route."""


class SchemaChangeError(ProviderError):
    """The provider answered, but not in the shape we expect. Usually means their API
    changed. Nothing from the response is used until the parser is updated."""


@dataclass(frozen=True)
class DateFare:
    departure_date: dt.date
    fare: float
    currency: str
    carrier: str | None = None
    price_status: str | None = None


@dataclass
class ProviderResponse:
    provider: str
    request: dict
    http_status: int | None
    payload: str | None
    observed_at: dt.datetime | None
    fares: list[DateFare] = field(default_factory=list)
    error: str | None = None
    #: Billable requests this answer cost. Some providers need several per route.
    calls: int = 1

    @property
    def payload_sha256(self) -> str | None:
        return hashlib.sha256(self.payload.encode()).hexdigest() if self.payload else None


class Provider(Protocol):
    name: str
    is_demo: bool

    def cheapest_dates(self, origin: str, destination: str, start: dt.date,
                       end: dt.date) -> ProviderResponse: ...

    def close(self) -> None: ...
