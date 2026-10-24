"""Reference data: airports, the basket, festivals. Loaded from files, never from the DB,
so the definition of what is measured lives in version control."""
from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from .config import PACKAGE_DIR, get_settings


@dataclass(frozen=True)
class Airport:
    iata: str
    city: str
    city_hi: str
    airport: str
    state: str
    aliases: tuple[str, ...]


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
    rows = json.loads((PACKAGE_DIR / "data" / "airports.json").read_text("utf-8"))
    return {r["iata"]: Airport(r["iata"], r["city"], r["city_hi"], r["airport"], r["state"],
                               tuple(r.get("aliases", []))) for r in rows}


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
