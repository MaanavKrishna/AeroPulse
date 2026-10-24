"""Storage. Three layers:

* bronze — `raw_responses`: exactly what a provider returned, with a hash.
* silver — `fares`: one cheapest fare per route, departure date and collection run,
  screened (eligible or not, with a reason).
* gold   — `product_prices`, `index_values` and friends: what the site and API publish.

Gold can always be rebuilt from silver, and silver from bronze.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


class Base(DeclarativeBase):
    pass


class CollectionRun(Base):
    __tablename__ = "collection_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), index=True)
    collection_date: Mapped[dt.date] = mapped_column(Date, index=True)
    started_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    #: running | ok | partial | failed | budget_exhausted
    status: Mapped[str] = mapped_column(String(20), default="running")
    routes_requested: Mapped[int] = mapped_column(Integer, default=0)
    routes_ok: Mapped[int] = mapped_column(Integer, default=0)
    calls: Mapped[int] = mapped_column(Integer, default=0)
    fares_stored: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str | None] = mapped_column(Text)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)


class RawResponse(Base):
    __tablename__ = "raw_responses"
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("collection_runs.id"), index=True)
    provider: Mapped[str] = mapped_column(String(32))
    route_id: Mapped[str] = mapped_column(String(7), index=True)
    request_json: Mapped[str] = mapped_column(Text)
    http_status: Mapped[int | None] = mapped_column(Integer)
    payload: Mapped[str | None] = mapped_column(Text)
    payload_sha256: Mapped[str | None] = mapped_column(String(64))
    error: Mapped[str | None] = mapped_column(Text)
    fetched_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    observed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))


class Fare(Base):
    __tablename__ = "fares"
    __table_args__ = (UniqueConstraint("run_id", "route_id", "departure_date"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("collection_runs.id"), index=True)
    raw_id: Mapped[int] = mapped_column(ForeignKey("raw_responses.id"))
    provider: Mapped[str] = mapped_column(String(32))
    route_id: Mapped[str] = mapped_column(String(7), index=True)
    collection_date: Mapped[dt.date] = mapped_column(Date, index=True)
    departure_date: Mapped[dt.date] = mapped_column(Date)
    days_ahead: Mapped[int] = mapped_column(Integer)
    window: Mapped[str | None] = mapped_column(String(8))
    fare: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3))
    carrier: Mapped[str | None] = mapped_column(String(8))
    price_status: Mapped[str | None] = mapped_column(String(16))
    observed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    eligible: Mapped[bool] = mapped_column(Boolean, default=True)
    exclusion_reason: Mapped[str | None] = mapped_column(String(32))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)


class ProductPrice(Base):
    """One price per route × window × collection day: the median cheapest fare."""
    __tablename__ = "product_prices"
    __table_args__ = (UniqueConstraint("collection_date", "route_id", "window"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    collection_date: Mapped[dt.date] = mapped_column(Date, index=True)
    route_id: Mapped[str] = mapped_column(String(7), index=True)
    window: Mapped[str] = mapped_column(String(8))
    price: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)        # cheapest departure date in the window
    high: Mapped[float] = mapped_column(Float)       # dearest departure date in the window
    dates: Mapped[int] = mapped_column(Integer)
    provider: Mapped[str] = mapped_column(String(32))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)


class IndexValue(Base):
    """A published point. `scope` is national | route | window. Empty strings, not NULL,
    mark "all routes" / "all windows" so the unique constraint holds on every database."""
    __tablename__ = "index_values"
    __table_args__ = (UniqueConstraint("scope", "route_id", "window", "frequency", "period",
                                       "kind", "methodology_version"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    scope: Mapped[str] = mapped_column(String(12), index=True)
    route_id: Mapped[str] = mapped_column(String(7), default="", index=True)
    window: Mapped[str] = mapped_column(String(8), default="")
    frequency: Mapped[str] = mapped_column(String(8), default="daily")
    period: Mapped[str] = mapped_column(String(10), index=True)
    period_start: Mapped[dt.date] = mapped_column(Date)
    #: CHAINED is published. FIXED is the single-basket reference, kept for audit.
    kind: Mapped[str] = mapped_column(String(8), default="CHAINED")
    value: Mapped[float] = mapped_column(Float)
    coverage: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20))
    observation_count: Mapped[int] = mapped_column(Integer)
    product_count: Mapped[int] = mapped_column(Integer)
    standard_error: Mapped[float | None] = mapped_column(Float)
    ci95_low: Mapped[float | None] = mapped_column(Float)
    ci95_high: Mapped[float | None] = mapped_column(Float)
    basket_version: Mapped[str] = mapped_column(String(16))
    methodology_version: Mapped[str] = mapped_column(String(8))
    revision: Mapped[int] = mapped_column(Integer, default=0)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    computed_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class IndexRevision(Base):
    """Every time a published value changes, the old one is kept here."""
    __tablename__ = "index_revisions"
    id: Mapped[int] = mapped_column(primary_key=True)
    index_value_id: Mapped[int] = mapped_column(ForeignKey("index_values.id"), index=True)
    revision: Mapped[int] = mapped_column(Integer)
    old_value: Mapped[float] = mapped_column(Float)
    new_value: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(String(200))
    revised_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class IndexLink(Base):
    __tablename__ = "index_links"
    id: Mapped[int] = mapped_column(primary_key=True)
    scope: Mapped[str] = mapped_column(String(12))
    from_version: Mapped[str] = mapped_column(String(16))
    to_version: Mapped[str] = mapped_column(String(16))
    link_period: Mapped[str] = mapped_column(String(10))
    old_level: Mapped[float] = mapped_column(Float)
    new_level: Mapped[float] = mapped_column(Float)
    factor: Mapped[float] = mapped_column(Float)
    methodology_version: Mapped[str] = mapped_column(String(8))


class BasketWeight(Base):
    """The route weights used for one basket version, and where they came from."""
    __tablename__ = "basket_weights"
    __table_args__ = (UniqueConstraint("basket_version", "route_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    basket_version: Mapped[str] = mapped_column(String(16))
    route_id: Mapped[str] = mapped_column(String(7))
    weight: Mapped[float] = mapped_column(Float)
    #: "dgca:<period>" or "equal"
    source: Mapped[str] = mapped_column(String(40))
    base_from: Mapped[dt.date | None] = mapped_column(Date)
    base_to: Mapped[dt.date | None] = mapped_column(Date)


class BasketProduct(Base):
    """Each product's weight and base price per basket version: enough to recompute every
    point from the published product prices."""
    __tablename__ = "basket_products"
    __table_args__ = (UniqueConstraint("basket_version", "route_id", "window"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    basket_version: Mapped[str] = mapped_column(String(16))
    valid_from: Mapped[dt.date] = mapped_column(Date)
    valid_to: Mapped[dt.date | None] = mapped_column(Date)
    route_id: Mapped[str] = mapped_column(String(7))
    window: Mapped[str] = mapped_column(String(8))
    weight: Mapped[float] = mapped_column(Float)
    base_price: Mapped[float] = mapped_column(Float)
    base_from: Mapped[dt.date] = mapped_column(Date)
    base_to: Mapped[dt.date] = mapped_column(Date)


class TrafficStat(Base):
    """DGCA domestic passenger traffic for a city pair and period."""
    __tablename__ = "traffic_stats"
    __table_args__ = (UniqueConstraint("period", "route_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    period: Mapped[str] = mapped_column(String(10))
    route_id: Mapped[str] = mapped_column(String(7))
    passengers: Mapped[int] = mapped_column(Integer)
    source_url: Mapped[str] = mapped_column(String(500))
    imported_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CpiAirfare(Base):
    """MoSPI CPI airfare item index, used only as an outside benchmark."""
    __tablename__ = "cpi_airfare"
    __table_args__ = (UniqueConstraint("period", "series"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    period: Mapped[str] = mapped_column(String(7))
    series: Mapped[str] = mapped_column(String(40))
    value: Mapped[float] = mapped_column(Float)
    base_year: Mapped[str] = mapped_column(String(10))
    source_url: Mapped[str] = mapped_column(String(500))
    imported_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
