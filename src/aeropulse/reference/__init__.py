"""Reference data: airports, the basket, festivals.

The files live next to this module (airports.json, basket.yaml, festivals.yaml), are
shipped inside the package, and are never stored in the database, so the definition of
what is measured lives in version control.
"""
from __future__ import annotations

import datetime as dt
import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from ..config import get_settings

HERE = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Airport:
    iata: str
    city: str
    city_hi: str
    airport: str
    state: str
    aliases: tuple[str, ...]
    lat: float = 0.0
    lon: float = 0.0
    icao: str = ""


@dataclass(frozen=True)
class BasketVersion:
    version: str
    valid_from: dt.date
    routes: tuple[str, ...]


@dataclass(frozen=True)
class Festival:
    slug: str
    name: str
    date: dt.date
    confirmed: bool
    routes: tuple[str, ...]


@lru_cache
def airports() -> dict[str, Airport]:
    rows = json.loads((HERE / "airports.json").read_text("utf-8"))
    return {r["iata"]: Airport(r["iata"], r["city"], r["city_hi"], r["airport"], r["state"],
                               tuple(r.get("aliases", [])), r.get("lat", 0.0),
                               r.get("lon", 0.0), r.get("icao", "")) for r in rows}


def split_route(route_id: str) -> tuple[str, str]:
    origin, destination = route_id.split("-")
    return origin, destination


def route_name(route_id: str, sep: str = " to ") -> str:
    o, d = split_route(route_id)
    a = airports()
    return f"{a[o].city if o in a else o}{sep}{a[d].city if d in a else d}"


def route_slug(route_id: str) -> str:
    return route_id.lower()


def route_from_slug(slug: str) -> str:
    return slug.upper()


def load_basket(path: Path | None = None) -> list[BasketVersion]:
    path = path or get_settings().basket_path
    data = yaml.safe_load(Path(path).read_text("utf-8"))
    versions = []
    for v in data["versions"]:
        routes = tuple(v["routes"])
        unknown = [r for r in routes
                   if any(code not in airports() for code in split_route(r))]
        if unknown:
            raise ValueError(f"basket {v['version']}: unknown airports in {unknown}")
        if len(set(routes)) != len(routes):
            raise ValueError(f"basket {v['version']}: duplicate routes")
        versions.append(BasketVersion(str(v["version"]), v["valid_from"], routes))
    versions.sort(key=lambda b: b.valid_from)
    return versions


def basket_on(day: dt.date, versions: list[BasketVersion] | None = None) -> BasketVersion | None:
    versions = versions if versions is not None else load_basket()
    active = [v for v in versions if v.valid_from <= day]
    return active[-1] if active else None


def routes_to_collect(day: dt.date, versions: list[BasketVersion] | None = None) -> list[str]:
    """Routes priced on `day`. On the first day of a new version the outgoing version is
    still priced too, because chain-linking needs both baskets on one shared day."""
    versions = versions if versions is not None else load_basket()
    current = basket_on(day, versions)
    if current is None:
        return []
    routes = list(current.routes)
    idx = versions.index(current)
    if idx > 0 and current.valid_from == day:
        routes += [r for r in versions[idx - 1].routes if r not in routes]
    return routes


def load_festivals(path: Path | None = None) -> list[Festival]:
    return list(_festivals(str(path or get_settings().festivals_path)))


@lru_cache
def _festivals(path: str) -> tuple[Festival, ...]:
    data = yaml.safe_load(Path(path).read_text("utf-8"))
    return tuple(sorted((Festival(f["slug"], f["name"], f["date"],
                                  f.get("date_status") == "confirmed",
                                  tuple(f.get("routes", [])))
                         for f in data["festivals"]), key=lambda f: f.date))


def great_circle_km(origin: str, destination: str) -> float:
    """Great-circle distance between two airports, in kilometres (haversine, R = 6371 km)."""
    a, b = airports()[origin], airports()[destination]
    p1, p2 = math.radians(a.lat), math.radians(b.lat)
    dp, dl = p2 - p1, math.radians(b.lon - a.lon)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))
