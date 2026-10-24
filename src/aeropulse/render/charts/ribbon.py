"""The fare ribbon: a route's recent prices as a band whose thickness is the 95% range and
whose colour runs from cooler to warmer than the route's own usual."""
from __future__ import annotations

import json
from collections.abc import Sequence

from ..format import MONTHS, esc
from .base import CSS, STANDALONE, VB_H, VB_W, Scale, bounds, fmt, level_index


def _ribbon_geometry(pts, typical, w: float, h: float, top: float = 0.0):
    lows = [p.low if p.low is not None else p.value for p in pts]
    highs = [p.high if p.high is not None else p.value for p in pts]
    t_low, t_high = getattr(typical, "low", None), getattr(typical, "high", None)
    lo, hi = bounds(lows + highs + [v for v in (t_low, t_high) if v is not None])
    xs = Scale(0, len(pts) - 1, 0, w)
    ys = Scale(lo, hi, top + h, top)
    min_half = h * 0.018
    upper, lower = [], []
    for i, p in enumerate(pts):
        yv = ys(p.value)
        upper.append((xs(i), min(ys(highs[i]), yv - min_half)))
        lower.append((xs(i), max(ys(lows[i]), yv + min_half)))
    area = ("M" + " L".join(f"{fmt(a)},{fmt(b)}" for a, b in upper) + " L"
            + " L".join(f"{fmt(a)},{fmt(b)}" for a, b in reversed(lower)) + " Z")
    line = "M" + " L".join(f"{fmt(xs(i))},{fmt(ys(p.value))}" for i, p in enumerate(pts))
    # Colour follows the level of the surrounding days (centred 5-day median), so one
    # noisy day does not flip the colour. The line itself is never smoothed.
    values = [p.value for p in pts]
    stops = []
    for i in range(len(pts)):
        window = sorted(values[max(0, i - 2): i + 3])
        stops.append(((xs(i) / w) * 100,
                      level_index(window[len(window) // 2], t_low, t_high)))
    band = (ys(t_high), ys(t_low)) if t_low is not None and t_high is not None else None
    return xs, ys, area, line, stops, band


def _gradient(uid: str, stops, levels) -> str:
    # Merge runs of the same level so the gradient stays small on long series.
    out, last = [], None
    for i, (off, lv) in enumerate(stops):
        if lv != last or i == len(stops) - 1:
            out.append(f'<stop offset="{off:.2f}%" style="stop-color:{levels[lv]}"/>')
            last = lv
    return (f'<linearGradient id="{uid}" x1="0" x2="1" y1="0" y2="0">'
            + "".join(out) + "</linearGradient>")


def ribbon(points: Sequence, *, typical=None, label: str = "", uid: str = "r",
           axis: bool = True, size: str = "lg", data: bool = True) -> str:
    """The fare ribbon, as an HTML fragment. `points` have .date .value .low .high;
    `typical` has .low .high (a Verdict works)."""
    pts = [p for p in points if p.value is not None]
    if len(pts) < 2:
        return (f'<div class="plot plot-{size} plot-empty" role="img" '
                f'aria-label="{esc(label or "Not enough data to draw a chart yet")}">'
                f'<p>Not enough data to draw this yet.</p></div>')
    xs, ys, area, line, stops, band = _ribbon_geometry(pts, typical, VB_W, VB_H)
    svg = [f'<svg viewBox="0 0 {VB_W} {VB_H}" preserveAspectRatio="none" aria-hidden="true" '
           f'focusable="false"><defs>{_gradient(uid + "-g", stops, CSS["levels"])}</defs>']
    if band:
        svg.append(f'<rect class="typical-band" x="0" y="{fmt(band[0])}" width="{VB_W}" '
                   f'height="{fmt(max(band[1] - band[0], 0.5))}"/>')
    svg.append(f'<path class="ribbon-area" d="{area}" fill="url(#{uid}-g)"/>')
    svg.append(f'<path class="ribbon-line" d="{line}" vector-effect="non-scaling-stroke"/>')
    svg.append("</svg>")

    last = pts[-1]
    lv = level_index(last.value, getattr(typical, "low", None), getattr(typical, "high", None))
    overlay = [f'<span class="today lv-{lv}" style="left:100%;top:{fmt(ys(last.value))}%">'
               f'</span>']
    if axis:
        seen = set()
        for i, p in enumerate(pts):
            if p.date.day == 1 and p.date.month not in seen:
                seen.add(p.date.month)
                pct = xs(i) / VB_W * 100
                if 4 < pct < 96:
                    overlay.append(f'<span class="tick" style="left:{fmt(pct)}%">'
                                   f'{MONTHS[p.date.month - 1]}</span>')
    attrs = f' data-points="{ribbon_data(pts)}" data-lo="{fmt(ys.d0)}" data-hi="{fmt(ys.d1)}"' \
        if data else ""
    return (f'<div class="plot plot-{size}{" has-axis" if axis else ""}" role="img" '
            f'aria-label="{esc(label)}"{attrs}>{"".join(svg)}'
            f'<div class="overlay">{"".join(overlay)}</div></div>')


def ribbon_data(points: Sequence) -> str:
    return esc(json.dumps([[p.date.isoformat(), round(p.value, 2),
                            None if p.low is None else round(p.low, 2),
                            None if p.high is None else round(p.high, 2),
                            getattr(p, "observations", None)] for p in points],
                          separators=(",", ":")))


def ribbon_standalone(points: Sequence, *, typical=None, title: str = "", subtitle: str = "",
                      footer: str = "", width: int = 1200, height: int = 630) -> str:
    """A self-contained SVG (social image / download)."""
    pal = STANDALONE
    pts = [p for p in points if p.value is not None]
    head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" font-family="Anek Latin, Arial, sans-serif">'
            f'<rect width="100%" height="100%" fill="{pal["sky"]}"/>'
            f'<text x="64" y="104" font-size="56" font-weight="700" fill="{pal["ink"]}">'
            f'{esc(title)}</text>'
            f'<text x="64" y="156" font-size="30" fill="{pal["muted"]}">{esc(subtitle)}</text>')
    if len(pts) < 2:
        return head + "</svg>"
    plot_w, plot_h, left, top = width - 128, 300, 64, 220
    xs, ys, area, line, stops, band = _ribbon_geometry(pts, typical, plot_w, plot_h, 0)
    g = [f'<defs>{_gradient("sg", stops, pal["levels"])}</defs>',
         f'<g transform="translate({left},{top})">']
    if band:
        g.append(f'<rect x="0" y="{fmt(band[0])}" width="{plot_w}" '
                 f'height="{fmt(max(band[1] - band[0], 1))}" fill="{pal["band"]}" '
                 f'opacity="0.6"/>')
    g.append(f'<path d="{area}" fill="url(#sg)"/>')
    g.append(f'<path d="{line}" fill="none" stroke="{pal["ink"]}" stroke-width="2.5"/>')
    g.append(f'<circle cx="{fmt(xs(len(pts) - 1))}" cy="{fmt(ys(pts[-1].value))}" r="9" '
             f'fill="{pal["sky"]}" stroke="{pal["ink"]}" stroke-width="4"/>')
    g.append("</g>")
    foot = (f'<text x="64" y="{height - 48}" font-size="24" fill="{pal["muted"]}">'
            f'{esc(footer)}</text>')
    return head + "".join(g) + foot + "</svg>"
