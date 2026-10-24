"""The route constellation: every tracked route as an arc between airports at their real
positions, coloured by how today's fares compare with usual, with planes flying them.

There is deliberately no country outline. Airports alone read clearly as India, and an
outline would mean choosing a depiction of disputed borders, which is not ours to make.

Everything is server-rendered SVG, so the map works without JavaScript. The plane motion
is SMIL (`animateMotion`), which app.js pauses when the reader prefers reduced motion.
"""
from __future__ import annotations

import hashlib
import math
from collections.abc import Iterable

from ...reference import airports, route_name, route_slug, split_route
from .svg import esc

#: Label offsets (dx, dy, text-anchor) so codes do not collide with arcs or each other.
LABELS = {
    "SXR": (9, 4, "start"), "DEL": (10, -6, "start"), "LKO": (9, -6, "start"),
    "PAT": (9, -6, "start"), "CCU": (10, 4, "start"), "AMD": (-10, 4, "end"),
    "BOM": (-10, 4, "end"), "PNQ": (10, 12, "start"), "HYD": (10, 4, "start"),
    "GOI": (-10, 4, "end"), "BLR": (-10, 10, "end"), "MAA": (10, 6, "start"),
    "COK": (-10, 6, "end"),
}
LEVEL_CLASS = {"above": "lv-4", "below": "lv-0", "typical": "lv-2", "unknown": "lv-u"}
PAD = 34
SCALE = 30.0          # viewBox units per degree of latitude


def _project(codes: Iterable[str]) -> tuple[dict[str, tuple[float, float]], float, float]:
    ap = airports()
    codes = list(codes)
    lats = [ap[c].lat for c in codes]
    lons = [ap[c].lon for c in codes]
    k = math.cos(math.radians((min(lats) + max(lats)) / 2))
    min_x, max_y = min(lons) * k, max(lats)
    pos = {c: (PAD + (ap[c].lon * k - min_x) * SCALE, PAD + (max_y - ap[c].lat) * SCALE)
           for c in codes}
    width = PAD * 2 + (max(lons) - min(lons)) * k * SCALE
    height = PAD * 2 + (max(lats) - min(lats)) * SCALE
    return pos, width, height


def arc_path(p0: tuple[float, float], p1: tuple[float, float], bow: float) -> tuple[str, float]:
    """Quadratic arc from p0 to p1 bowing sideways by `bow` × length. Returns (d, length)."""
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy) or 1.0
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    cx, cy = mx - dy / length * length * bow, my + dx / length * length * bow
    # quadratic curve length, approximated well enough for animation timing
    approx = (length + math.hypot(cx - x0, cy - y0) + math.hypot(x1 - cx, y1 - cy)) / 2
    return f"M{x0:.1f},{y0:.1f} Q{cx:.1f},{cy:.1f} {x1:.1f},{y1:.1f}", approx


def _phase(route_id: str) -> float:
    return int(hashlib.sha1(route_id.encode()).hexdigest()[:4], 16) / 0xFFFF


def network_map(rows: list[dict], *, selected: str | None = None, uid: str = "net",
                label: str = "") -> str:
    """`rows` are route rows from queries.route_rows (route_id, name, verdict)."""
    if not rows:
        return '<div class="sky-map sky-map-empty"></div>'
    codes = {c for r in rows for c in split_route(r["route_id"])}
    pos, width, height = _project(codes)
    ap = airports()

    arcs, hits, planes = [], [], []
    for i, r in enumerate(sorted(rows, key=lambda r: r["route_id"] == selected)):
        route_id = r["route_id"]
        o, d = split_route(route_id)
        # Opposite directions bow to opposite sides, so a pair reads as two lanes.
        bow = 0.13 if o < d else -0.13
        path, length = arc_path(pos[o], pos[d], bow)
        level = r["verdict"].level
        cls = LEVEL_CLASS.get(level, "lv-u")
        sel = " is-selected" if route_id == selected else ""
        aid = f"{uid}-{route_id}"
        title = f"{r['name']}: {_short(r['verdict'])}"
        arcs.append(f'<path id="{aid}" class="arc {cls}{sel}" d="{path}" pathLength="1" '
                    f'style="--i:{i % 20}" data-route="{route_id}"/>')
        hits.append(f'<a href="/routes/{route_slug(route_id)}" class="arc-hit" '
                    f'data-route="{route_id}" data-name="{esc(r["name"])}" '
                    f'data-state="{esc(_short(r["verdict"]))}" data-level="{cls}">'
                    f'<title>{esc(title)}</title><path d="{path}"/></a>')
        dur = max(length / 34.0, 3.2)
        # A negative start spreads the planes along their routes from the first frame.
        begin = -_phase(route_id) * dur
        planes.append(f'<g class="plane {cls}{sel}" data-route="{route_id}">'
                      f'<path d="M3.2,0 L-2.4,-2.3 L-1.2,0 L-2.4,2.3 Z"/>'
                      f'<animateMotion dur="{dur:.1f}s" begin="{begin:.2f}s" '
                      f'repeatCount="indefinite" rotate="auto"><mpath href="#{aid}"/>'
                      f'</animateMotion></g>')

    dots = []
    for j, code in enumerate(sorted(codes, key=lambda c: pos[c][1])):
        x, y = pos[code]
        dx, dy, anchor = LABELS.get(code, (9, 4, "start"))
        dots.append(f'<g class="airport" style="--j:{j}" data-code="{code}">'
                    f'<circle class="halo" cx="{x:.1f}" cy="{y:.1f}" r="7"/>'
                    f'<circle class="dot" cx="{x:.1f}" cy="{y:.1f}" r="2.6"/>'
                    f'<text x="{x + dx:.1f}" y="{y + dy:.1f}" text-anchor="{anchor}">{code}'
                    f'<tspan class="city" x="{x + dx:.1f}" dy="10">{esc(ap[code].city)}</tspan>'
                    f'</text></g>')

    label = label or "Tracked routes, coloured by how fares compare with usual"
    return (f'<div class="sky-map" data-map>'
            f'<svg viewBox="0 0 {width:.0f} {height:.0f}" role="group" '
            f'aria-label="{esc(label)}">'
            f'<g class="arcs">{"".join(arcs)}</g>'
            f'<g class="planes" aria-hidden="true">{"".join(planes)}</g>'
            f'<g class="airports" aria-hidden="true">{"".join(dots)}</g>'
            f'<g class="hits">{"".join(hits)}</g>'
            f'</svg><div class="map-tip" role="status" hidden></div></div>')


def route_flight(origin: str, dest: str, level: str, *, uid: str = "flight") -> str:
    """One route drawn as a single long arc, for the route page header."""
    path = "M14,150 Q500,-40 986,150"
    cls = LEVEL_CLASS.get(level, "lv-u")
    return (f'<div class="flight" aria-hidden="true"><svg viewBox="0 0 1000 160">'
            f'<path class="flight-trail" d="{path}"/>'
            f'<path id="{uid}" class="flight-path {cls}" d="{path}" pathLength="1"/>'
            f'<circle class="flight-end" cx="14" cy="150" r="6"/>'
            f'<circle class="flight-end" cx="986" cy="150" r="6"/>'
            f'<g class="plane plane-lg {cls}"><path d="M9,0 L-7,-6.5 L-3.5,0 L-7,6.5 Z"/>'
            f'<animateMotion dur="7s" begin="0.9s" repeatCount="indefinite" rotate="auto" '
            f'keyPoints="0;1" keyTimes="0;1" calcMode="spline" keySplines="0.45 0 0.55 1">'
            f'<mpath href="#{uid}"/></animateMotion></g></svg></div>')


def _short(v) -> str:
    if v.level == "unknown":
        return "too new to judge"
    if v.level == "typical":
        return "usual"
    word = "above" if v.level == "above" else "below"
    return f"{abs(v.pct_vs_median or 0):.0f}% {word} usual"


__all__ = ["network_map", "route_flight", "route_name"]
