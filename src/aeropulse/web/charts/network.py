"""The route chart: every tracked route drawn the way an aeronautical en-route chart draws
airways, on a latitude/longitude grid, between airports at their real positions.

There is deliberately no coastline or country outline. The graticule and the airports are
enough to read the geography, and an outline would mean choosing a depiction of disputed
borders, which is not ours to make.

Server-rendered SVG, so the chart works without JavaScript. The one moving plane is SMIL
(`animateMotion`), which app.js pauses when the reader prefers reduced motion.
"""
from __future__ import annotations

import math
from collections.abc import Iterable

from ...reference import airports, route_slug, split_route
from ..format import esc, inr

#: Viewbox units per degree of latitude, and the margin outside the chart frame.
SCALE = 26.0
MARGIN = 30.0
GRID_STEP = 5
LANE = 1.9                       # the two directions of a city pair are drawn as two lanes
LEVEL_CLASS = {"above": "lv-4", "below": "lv-0", "typical": "lv-2", "unknown": "lv-u"}

#: Label placement (dx, dy, anchor) so names keep clear of airways and each other.
LABELS = {
    "SXR": (8, 4, "start"), "DEL": (9, -9, "start"), "LKO": (8, -8, "start"),
    "PAT": (8, -8, "start"), "CCU": (-9, -9, "end"), "AMD": (-9, 4, "end"),
    "BOM": (-9, 4, "end"), "PNQ": (9, 13, "start"), "HYD": (9, 4, "start"),
    "GOI": (-9, 4, "end"), "BLR": (-9, 12, "end"), "MAA": (9, 8, "start"),
    "COK": (-9, 6, "end"),
}


class Chart:
    """Equirectangular projection scaled by cos(mid-latitude), framed on whole degrees."""

    def __init__(self, codes: Iterable[str]) -> None:
        ap = airports()
        codes = list(codes)
        lats = [ap[c].lat for c in codes]
        lons = [ap[c].lon for c in codes]
        self.lat0, self.lat1 = math.floor(min(lats)) - 1, math.ceil(max(lats)) + 1
        self.lon0, self.lon1 = math.floor(min(lons)) - 1, math.ceil(max(lons)) + 2
        self.k = math.cos(math.radians((self.lat0 + self.lat1) / 2))
        self.width = (self.lon1 - self.lon0) * self.k * SCALE
        self.height = (self.lat1 - self.lat0) * SCALE

    def xy(self, lat: float, lon: float) -> tuple[float, float]:
        return (MARGIN + (lon - self.lon0) * self.k * SCALE,
                MARGIN + (self.lat1 - lat) * SCALE)

    def airport(self, code: str) -> tuple[float, float]:
        a = airports()[code]
        return self.xy(a.lat, a.lon)

    @property
    def km_per_unit(self) -> float:
        return 111.2 / SCALE


def great_circle_km(o: str, d: str) -> float:
    a, b = airports()[o], airports()[d]
    p1, p2 = math.radians(a.lat), math.radians(b.lat)
    dp, dl = p2 - p1, math.radians(b.lon - a.lon)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def lane(chart: Chart, o: str, d: str) -> tuple[float, float, float, float]:
    """Endpoints of the directed lane o to d, offset to one side of the city-pair line and
    stopped short of each airport symbol."""
    (x0, y0), (x1, y1) = chart.airport(o), chart.airport(d)
    length = math.hypot(x1 - x0, y1 - y0) or 1.0
    ux, uy = (x1 - x0) / length, (y1 - y0) / length
    side = LANE if o < d else -LANE
    cut = 5.5
    return (x0 - uy * side + ux * cut, y0 + ux * side + uy * cut,
            x1 - uy * side - ux * cut, y1 + ux * side - uy * cut)


def _f(v: float) -> str:
    return f"{v:.1f}"


def _line(x1: float, y1: float, x2: float, y2: float, cls: str) -> str:
    return f'<line class="{cls}" x1="{_f(x1)}" y1="{_f(y1)}" x2="{_f(x2)}" y2="{_f(y2)}"/>'


def _graticule(chart: Chart) -> str:
    left, top = MARGIN, MARGIN
    right, bottom = MARGIN + chart.width, MARGIN + chart.height
    out = ['<g class="graticule" aria-hidden="true">']
    for lat in range(chart.lat0, chart.lat1 + 1):
        y = chart.xy(lat, chart.lon0)[1]
        if lat % GRID_STEP == 0:
            out.append(_line(left, y, right, y, "grid-major"))
            out.append(f'<text class="deg" x="{_f(left - 6)}" y="{_f(y + 3.5)}" '
                       f'text-anchor="end">{lat}°N</text>')
        out.append(_line(left, y, left + 4, y, "tick"))
        out.append(_line(right - 4, y, right, y, "tick"))
    for lon in range(chart.lon0, chart.lon1 + 1):
        x = chart.xy(chart.lat0, lon)[0]
        if lon % GRID_STEP == 0:
            out.append(_line(x, top, x, bottom, "grid-major"))
            out.append(f'<text class="deg" x="{_f(x)}" y="{_f(bottom + 16)}" '
                       f'text-anchor="middle">{lon}°E</text>')
        out.append(_line(x, top, x, top + 4, "tick"))
        out.append(_line(x, bottom - 4, x, bottom, "tick"))
    out.append(f'<rect class="neatline" x="{_f(left)}" y="{_f(top)}" '
               f'width="{_f(chart.width)}" height="{_f(chart.height)}"/></g>')
    return "".join(out)


def airport_symbol(x: float, y: float) -> str:
    """The chart symbol for an airport: a ring with four short ticks."""
    r, t = 3.6, 2.6
    ticks = "".join(_line(x + dx * r, y + dy * r, x + dx * (r + t), y + dy * (r + t), "")
                    for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)))
    return f'<circle cx="{_f(x)}" cy="{_f(y)}" r="{r}"/>{ticks}'


def _title_block(chart: Chart, as_of: str) -> str:
    """Chart title and scale bar, set in the empty sea area at the bottom right."""
    x, y = MARGIN + chart.width - 180, MARGIN + chart.height - 74
    bar_km = 500
    bar = bar_km / chart.km_per_unit
    sx = x + 9
    return ('<g class="title-block" aria-hidden="true">'
            f'<rect x="{_f(x)}" y="{_f(y)}" width="170" height="64"/>'
            f'<text class="tb-title" x="{_f(sx)}" y="{_f(y + 17)}">AeroPulse route chart</text>'
            f'<text class="tb-text" x="{_f(sx)}" y="{_f(y + 30)}">'
            'Airways coloured by fares vs usual</text>'
            f'<text class="tb-text" x="{_f(sx)}" y="{_f(y + 42)}">{esc(as_of)}</text>'
            + _line(sx, y + 53, sx + bar, y + 53, "scale")
            + _line(sx, y + 50, sx, y + 56, "scale")
            + _line(sx + bar / 2, y + 51, sx + bar / 2, y + 55, "scale")
            + _line(sx + bar, y + 50, sx + bar, y + 56, "scale")
            + f'<text class="tb-text" x="{_f(sx + bar + 5)}" y="{_f(y + 56)}">{bar_km} km</text>'
            '</g>')


def network_map(rows: list[dict], *, selected: str | None = None, uid: str = "net",
                label: str = "", as_of: str = "") -> str:
    """`rows` are route rows from queries.route_rows (route_id, name, verdict)."""
    if not rows:
        return '<figure class="route-chart route-chart-empty"></figure>'
    codes = {c for r in rows for c in split_route(r["route_id"])}
    chart = Chart(codes)
    ap = airports()
    vw, vh = chart.width + MARGIN * 2, chart.height + MARGIN * 2

    lanes, hits, marks = [], [], []
    for r in sorted(rows, key=lambda r: r["route_id"] == selected):
        route_id = r["route_id"]
        o, d = split_route(route_id)
        x0, y0, x1, y1 = lane(chart, o, d)
        cls = LEVEL_CLASS.get(r["verdict"].level, "lv-u")
        sel = " is-selected" if route_id == selected else ""
        lid = f"{uid}-{route_id}"
        path = f"M{_f(x0)},{_f(y0)} L{_f(x1)},{_f(y1)}"
        state = short_state(r["verdict"])
        lanes.append(f'<path id="{lid}" class="airway {cls}{sel}" d="{path}" pathLength="1" '
                     f'data-route="{route_id}"/>')
        hits.append(f'<a href="/routes/{route_slug(route_id)}" class="lane-hit" '
                    f'data-route="{route_id}" data-name="{esc(r["name"])}" '
                    f'data-state="{esc(state)}"><title>{esc(r["name"])}: {esc(state)}</title>'
                    f'<path d="{path}"/></a>')
        if route_id == selected:
            marks.append(_selected_marks(chart, o, d, cls, lid))

    symbols = []
    for code in sorted(codes):
        x, y = chart.airport(code)
        dx, dy, anchor = LABELS.get(code, (8, 4, "start"))
        a = ap[code]
        symbols.append(f'<g class="airport" data-code="{code}">{airport_symbol(x, y)}'
                       f'<text x="{_f(x + dx)}" y="{_f(y + dy)}" text-anchor="{anchor}">'
                       f'<tspan class="iata">{code}</tspan>'
                       f'<tspan class="city" x="{_f(x + dx)}" dy="10.5">{esc(a.city)} {a.icao}'
                       f'</tspan></text></g>')

    label = label or "Route chart of tracked domestic routes, coloured by fares against usual"
    return (f'<figure class="route-chart" data-map>'
            f'<svg viewBox="0 0 {vw:.0f} {vh:.0f}" role="group" aria-label="{esc(label)}">'
            f'{_graticule(chart)}'
            f'<g class="airways">{"".join(lanes)}</g>'
            f'<g class="airports" aria-hidden="true">{"".join(symbols)}</g>'
            f'{_title_block(chart, as_of)}'
            f'<g class="selected-marks">{"".join(marks)}</g>'
            f'<g class="hits">{"".join(hits)}</g>'
            f'</svg><div class="map-tip" role="status" hidden></div></figure>')


def _selected_marks(chart: Chart, o: str, d: str, cls: str, lid: str) -> str:
    """Distance label along the selected lane, and the one plane flying it."""
    x0, y0, x1, y1 = lane(chart, o, d)
    length = math.hypot(x1 - x0, y1 - y0) or 1.0
    angle = math.degrees(math.atan2(y1 - y0, x1 - x0))
    if angle > 90:
        angle -= 180
    elif angle < -90:
        angle += 180
    side = 1 if o < d else -1
    tx = (x0 + x1) / 2 - (y1 - y0) / length * side * 9
    ty = (y0 + y1) / 2 + (x1 - x0) / length * side * 9 + 3
    dur = max(length / 26.0, 4.0)
    return (f'<text class="distance {cls}" x="{_f(tx)}" y="{_f(ty)}" text-anchor="middle" '
            f'transform="rotate({angle:.1f} {_f(tx)} {_f(ty)})">'
            f'{inr(great_circle_km(o, d))} km</text>'
            f'<g class="plane {cls}"><path d="M4,0 L-3,-3 L-1.6,0 L-3,3 Z"/>'
            f'<animateMotion dur="{dur:.1f}s" repeatCount="indefinite" rotate="auto">'
            f'<mpath href="#{lid}"/></animateMotion></g>')


def route_flight(level: str, *, uid: str = "flight") -> str:
    """One route as a single airway between two airport symbols. The distance label is
    HTML in the template, so it stays legible at any width."""
    cls = LEVEL_CLASS.get(level, "lv-u")
    return (f'<div class="flight" aria-hidden="true"><svg viewBox="0 0 1000 24">'
            f'<path id="{uid}" class="flight-path {cls}" d="M20,12 L980,12" pathLength="1"/>'
            f'<g class="airport">{airport_symbol(10, 12)}</g>'
            f'<g class="airport">{airport_symbol(990, 12)}</g>'
            f'<g class="plane {cls}"><path d="M6,0 L-4.5,-4.5 L-2.3,0 L-4.5,4.5 Z"/>'
            f'<animateMotion dur="9s" repeatCount="indefinite" rotate="auto">'
            f'<mpath href="#{uid}"/></animateMotion></g></svg></div>')


def short_state(v) -> str:
    if v.level == "unknown":
        return "too new to judge"
    if v.level == "typical":
        return "usual"
    word = "above" if v.level == "above" else "below"
    return f"{abs(v.pct_vs_median or 0):.0f}% {word} usual"
