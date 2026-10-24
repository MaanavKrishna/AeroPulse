"""Line charts: fare by days before departure, and festival fares against ordinary weeks."""
from __future__ import annotations

import json
from collections.abc import Sequence

from ..format import esc, inr
from .base import VB_H, VB_W, Scale, bounds, fmt, nice_ticks


def booking_curve(curve: Sequence[dict], *, cheap: tuple[int, int] | None = None,
                  label: str = "") -> str:
    """Median cheapest fare by days before departure. Far ahead on the left, departure
    day on the right, the way time moves for a traveller."""
    if len(curve) < 2:
        return ('<div class="plot plot-md plot-empty" role="img" aria-label="Not enough data">'
                '<p>Not enough data to draw this yet.</p></div>')
    pts = sorted(curve, key=lambda c: -c["days_ahead"])
    max_d = pts[0]["days_ahead"]
    lo, hi = bounds([c["median"] for c in pts], 0.15)
    xs = Scale(max_d, 1, 0, VB_W)
    ys = Scale(lo, hi, VB_H, 0)
    line = "M" + " L".join(f"{fmt(xs(c['days_ahead']))},{fmt(ys(c['median']))}" for c in pts)
    area = line + f" L{fmt(xs(pts[-1]['days_ahead']))},{VB_H} L{fmt(xs(max_d))},{VB_H} Z"
    svg = [f'<svg viewBox="0 0 {VB_W} {VB_H}" preserveAspectRatio="none" aria-hidden="true" '
           f'focusable="false">']
    if cheap:
        x0, x1 = xs(cheap[1]), xs(cheap[0])
        svg.append(f'<rect class="cheap-zone" x="{fmt(x0)}" y="0" width="{fmt(x1 - x0)}" '
                   f'height="{VB_H}"/>')
    ticks = nice_ticks(lo, hi, 3)
    for t in ticks:
        svg.append(f'<line class="grid" x1="0" x2="{VB_W}" y1="{fmt(ys(t))}" '
                   f'y2="{fmt(ys(t))}" vector-effect="non-scaling-stroke"/>')
    svg.append(f'<path class="curve-area" d="{area}"/>')
    svg.append(f'<path class="curve-line" d="{line}" vector-effect="non-scaling-stroke"/>')
    svg.append("</svg>")
    overlay = [f'<span class="ylabel" style="top:{fmt(ys(t))}%">₹{inr(t)}</span>'
               for t in ticks]
    for d, text in ((60, "2 months before"), (30, "1 month"), (14, "2 weeks"),
                    (7, "1 week"), (1, "1 day")):
        if d <= max_d:
            pos = xs(d) / VB_W * 100
            edge = " edge-start" if pos < 8 else " edge-end" if pos > 92 else ""
            overlay.append(f'<span class="tick{edge}" style="left:{fmt(pos)}%">{text}</span>')
    if cheap:
        mid = (xs(cheap[0]) + xs(cheap[1])) / 2 / VB_W * 100
        overlay.append(f'<span class="zone-label" style="left:{fmt(mid)}%">usually cheapest'
                       f'</span>')
    data = esc(json.dumps([[c["days_ahead"], round(c["median"])] for c in pts],
                          separators=(",", ":")))
    return (f'<div class="plot plot-md has-axis has-y" role="img" aria-label="{esc(label)}" '
            f'data-curve="{data}">{"".join(svg)}<div class="overlay">{"".join(overlay)}'
            f'</div></div>')


def festival_track(points: Sequence[dict], *, label: str = "") -> str:
    """Peak-day fare as % above ordinary dates at the same booking distance."""
    pts = sorted((p for p in points if p.get("pct") is not None),
                 key=lambda p: -p["days_ahead"])
    if len(pts) < 2:
        return ('<div class="plot plot-sm plot-empty" role="img" aria-label="Not enough data">'
                '<p>Not enough data yet.</p></div>')
    max_d = max(pts[0]["days_ahead"], 30)
    lo, hi = min(min(p["pct"] for p in pts), -10), max(max(p["pct"] for p in pts), 10)
    lo, hi = lo - (hi - lo) * 0.08, hi + (hi - lo) * 0.08
    xs = Scale(max_d, 1, 0, VB_W)
    ys = Scale(lo, hi, VB_H, 0)
    line = "M" + " L".join(f"{fmt(xs(p['days_ahead']))},{fmt(ys(p['pct']))}" for p in pts)
    zero = ys(0)
    area = (line + f" L{fmt(xs(pts[-1]['days_ahead']))},{fmt(zero)} "
            f"L{fmt(xs(pts[0]['days_ahead']))},{fmt(zero)} Z")
    step = 50 if hi - lo > 80 else 25
    grid = [v for v in range(step, int(hi) + 1, step)]
    gridlines = "".join(f'<line class="grid" x1="0" x2="{VB_W}" y1="{fmt(ys(v))}" '
                        f'y2="{fmt(ys(v))}" vector-effect="non-scaling-stroke"/>' for v in grid)
    svg = (f'<svg viewBox="0 0 {VB_W} {VB_H}" preserveAspectRatio="none" aria-hidden="true" '
           f'focusable="false">{gridlines}<line class="zero" x1="0" x2="{VB_W}" y1="{fmt(zero)}" '
           f'y2="{fmt(zero)}" vector-effect="non-scaling-stroke"/>'
           f'<path class="track-area" d="{area}"/>'
           f'<path class="track-line" d="{line}" vector-effect="non-scaling-stroke"/></svg>')
    last = pts[-1]
    overlay = [f'<span class="ylabel" style="top:{fmt(ys(v))}%">+{v}%</span>' for v in grid]
    overlay += [f'<span class="ylabel" style="top:{fmt(zero)}%">usual</span>',
               f'<span class="today lv-4" style="left:{fmt(xs(last["days_ahead"]) / VB_W * 100)}%;'
               f'top:{fmt(ys(last["pct"]))}%"></span>']
    for d, text in ((60, "60 days before"), (30, "30"), (14, "14"), (7, "7"), (1, "1 day")):
        if d <= max_d:
            pos = xs(d) / VB_W * 100
            edge = " edge-start" if pos < 8 else " edge-end" if pos > 92 else ""
            overlay.append(f'<span class="tick{edge}" style="left:{fmt(pos)}%">{text}</span>')
    return (f'<div class="plot plot-sm has-axis has-y" role="img" aria-label="{esc(label)}">'
            f'{svg}<div class="overlay">{"".join(overlay)}</div></div>')
