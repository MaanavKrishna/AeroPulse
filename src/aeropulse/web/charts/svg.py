"""Server-rendered charts. Pages, embeds and downloadable images all use these, so a chart
looks the same everywhere and works with JavaScript switched off.

Page charts are HTML fragments: the shapes are an SVG that stretches to any width
(`preserveAspectRatio="none"`, strokes that do not scale), and every label or marker is
positioned HTML on top, so text never distorts. Downloadable charts (`*_standalone`) are
self-contained SVG files at a fixed size with concrete colours.

Colours are CSS custom properties from static/css/tokens.css, so charts follow the theme.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import math
from collections.abc import Sequence

LEVEL_VARS = ("--r-cool-2", "--r-cool-1", "--r-even", "--r-warm-1", "--r-warm-2")
LEVEL_NAMES = ("much lower than usual", "lower than usual", "usual", "higher than usual",
               "much higher than usual")
CSS = {"ink": "var(--ink)", "muted": "var(--ink-muted)", "band": "var(--band)",
       "grid": "var(--rule)", "accent": "var(--accent)", "sky": "var(--sky)",
       "levels": tuple(f"var({v})" for v in LEVEL_VARS)}
STANDALONE = {"ink": "#16202C", "muted": "#5A6676", "band": "#D7DDE5", "grid": "#DCE2E9",
              "accent": "#3036A0", "sky": "#F2F5F8",
              "levels": ("#1D6FA5", "#6FA3C7", "#B4BDC9", "#DD8A70", "#C4492C")}
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
VB_W, VB_H = 1000, 100        # stretchable viewBox for page charts


def esc(s: object) -> str:
    return html.escape(str(s), quote=True)


def _f(x: float) -> str:
    return f"{x:.2f}".rstrip("0").rstrip(".")


def level_index(value: float, low: float | None, high: float | None) -> int:
    """0..4 on the diverging scale, relative to a typical band. 2 = inside the band."""
    if low is None or high is None:
        return 2
    spread = max(high - low, 1e-9)
    if value > high:
        return 4 if value > high + spread else 3
    if value < low:
        return 0 if value < low - spread else 1
    return 2


class Scale:
    def __init__(self, d0: float, d1: float, r0: float, r1: float) -> None:
        self.d0, self.d1, self.r0, self.r1 = d0, d1, r0, r1

    def __call__(self, v: float) -> float:
        if self.d1 == self.d0:
            return (self.r0 + self.r1) / 2
        return self.r0 + (v - self.d0) / (self.d1 - self.d0) * (self.r1 - self.r0)


def _bounds(values: list[float], pad: float = 0.12) -> tuple[float, float]:
    lo, hi = min(values), max(values)
    span = max(hi - lo, abs(hi) * 0.01, 1e-6)
    return lo - span * pad, hi + span * pad


# ----------------------------------------------------------------------------- ribbon

def _ribbon_geometry(pts, typical, w: float, h: float, top: float = 0.0):
    lows = [p.low if p.low is not None else p.value for p in pts]
    highs = [p.high if p.high is not None else p.value for p in pts]
    t_low, t_high = getattr(typical, "low", None), getattr(typical, "high", None)
    lo, hi = _bounds(lows + highs + [v for v in (t_low, t_high) if v is not None])
    xs = Scale(0, len(pts) - 1, 0, w)
    ys = Scale(lo, hi, top + h, top)
    min_half = h * 0.018
    upper, lower = [], []
    for i, p in enumerate(pts):
        yv = ys(p.value)
        upper.append((xs(i), min(ys(highs[i]), yv - min_half)))
        lower.append((xs(i), max(ys(lows[i]), yv + min_half)))
    area = ("M" + " L".join(f"{_f(a)},{_f(b)}" for a, b in upper) + " L"
            + " L".join(f"{_f(a)},{_f(b)}" for a, b in reversed(lower)) + " Z")
    line = "M" + " L".join(f"{_f(xs(i))},{_f(ys(p.value))}" for i, p in enumerate(pts))
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
        svg.append(f'<rect class="typical-band" x="0" y="{_f(band[0])}" width="{VB_W}" '
                   f'height="{_f(max(band[1] - band[0], 0.5))}"/>')
    svg.append(f'<path class="ribbon-area" d="{area}" fill="url(#{uid}-g)"/>')
    svg.append(f'<path class="ribbon-line" d="{line}" vector-effect="non-scaling-stroke"/>')
    svg.append("</svg>")

    last = pts[-1]
    lv = level_index(last.value, getattr(typical, "low", None), getattr(typical, "high", None))
    overlay = [f'<span class="today lv-{lv}" style="left:100%;top:{_f(ys(last.value))}%">'
               f'</span>']
    if axis:
        seen = set()
        for i, p in enumerate(pts):
            if p.date.day == 1 and p.date.month not in seen:
                seen.add(p.date.month)
                pct = xs(i) / VB_W * 100
                if 4 < pct < 96:
                    overlay.append(f'<span class="tick" style="left:{_f(pct)}%">'
                                   f'{MONTHS[p.date.month - 1]}</span>')
    attrs = f' data-points="{ribbon_data(pts)}" data-lo="{_f(ys.d0)}" data-hi="{_f(ys.d1)}"' \
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
        g.append(f'<rect x="0" y="{_f(band[0])}" width="{plot_w}" '
                 f'height="{_f(max(band[1] - band[0], 1))}" fill="{pal["band"]}" '
                 f'opacity="0.6"/>')
    g.append(f'<path d="{area}" fill="url(#sg)"/>')
    g.append(f'<path d="{line}" fill="none" stroke="{pal["ink"]}" stroke-width="2.5"/>')
    g.append(f'<circle cx="{_f(xs(len(pts) - 1))}" cy="{_f(ys(pts[-1].value))}" r="9" '
             f'fill="{pal["sky"]}" stroke="{pal["ink"]}" stroke-width="4"/>')
    g.append("</g>")
    foot = (f'<text x="64" y="{height - 48}" font-size="24" fill="{pal["muted"]}">'
            f'{esc(footer)}</text>')
    return head + "".join(g) + foot + "</svg>"


# ----------------------------------------------------------------------------- curves

def booking_curve(curve: Sequence[dict], *, cheap: tuple[int, int] | None = None,
                  label: str = "") -> str:
    """Median cheapest fare by days before departure. Far ahead on the left, departure
    day on the right, the way time moves for a traveller."""
    if len(curve) < 2:
        return ('<div class="plot plot-md plot-empty" role="img" aria-label="Not enough data">'
                '<p>Not enough data to draw this yet.</p></div>')
    pts = sorted(curve, key=lambda c: -c["days_ahead"])
    max_d = pts[0]["days_ahead"]
    lo, hi = _bounds([c["median"] for c in pts], 0.15)
    xs = Scale(max_d, 1, 0, VB_W)
    ys = Scale(lo, hi, VB_H, 0)
    line = "M" + " L".join(f"{_f(xs(c['days_ahead']))},{_f(ys(c['median']))}" for c in pts)
    area = line + f" L{_f(xs(pts[-1]['days_ahead']))},{VB_H} L{_f(xs(max_d))},{VB_H} Z"
    svg = [f'<svg viewBox="0 0 {VB_W} {VB_H}" preserveAspectRatio="none" aria-hidden="true" '
           f'focusable="false">']
    if cheap:
        x0, x1 = xs(cheap[1]), xs(cheap[0])
        svg.append(f'<rect class="cheap-zone" x="{_f(x0)}" y="0" width="{_f(x1 - x0)}" '
                   f'height="{VB_H}"/>')
    ticks = _nice_ticks(lo, hi, 3)
    for t in ticks:
        svg.append(f'<line class="grid" x1="0" x2="{VB_W}" y1="{_f(ys(t))}" '
                   f'y2="{_f(ys(t))}" vector-effect="non-scaling-stroke"/>')
    svg.append(f'<path class="curve-area" d="{area}"/>')
    svg.append(f'<path class="curve-line" d="{line}" vector-effect="non-scaling-stroke"/>')
    svg.append("</svg>")
    overlay = [f'<span class="ylabel" style="top:{_f(ys(t))}%">₹{inr(t)}</span>'
               for t in ticks]
    for d, text in ((60, "2 months before"), (30, "1 month"), (14, "2 weeks"),
                    (7, "1 week"), (1, "1 day")):
        if d <= max_d:
            pos = xs(d) / VB_W * 100
            edge = " edge-start" if pos < 8 else " edge-end" if pos > 92 else ""
            overlay.append(f'<span class="tick{edge}" style="left:{_f(pos)}%">{text}</span>')
    if cheap:
        mid = (xs(cheap[0]) + xs(cheap[1])) / 2 / VB_W * 100
        overlay.append(f'<span class="zone-label" style="left:{_f(mid)}%">usually cheapest'
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
    line = "M" + " L".join(f"{_f(xs(p['days_ahead']))},{_f(ys(p['pct']))}" for p in pts)
    zero = ys(0)
    area = (line + f" L{_f(xs(pts[-1]['days_ahead']))},{_f(zero)} "
            f"L{_f(xs(pts[0]['days_ahead']))},{_f(zero)} Z")
    step = 50 if hi - lo > 80 else 25
    grid = [v for v in range(step, int(hi) + 1, step)]
    gridlines = "".join(f'<line class="grid" x1="0" x2="{VB_W}" y1="{_f(ys(v))}" '
                        f'y2="{_f(ys(v))}" vector-effect="non-scaling-stroke"/>' for v in grid)
    svg = (f'<svg viewBox="0 0 {VB_W} {VB_H}" preserveAspectRatio="none" aria-hidden="true" '
           f'focusable="false">{gridlines}<line class="zero" x1="0" x2="{VB_W}" y1="{_f(zero)}" '
           f'y2="{_f(zero)}" vector-effect="non-scaling-stroke"/>'
           f'<path class="track-area" d="{area}"/>'
           f'<path class="track-line" d="{line}" vector-effect="non-scaling-stroke"/></svg>')
    last = pts[-1]
    overlay = [f'<span class="ylabel" style="top:{_f(ys(v))}%">+{v}%</span>' for v in grid]
    overlay += [f'<span class="ylabel" style="top:{_f(zero)}%">usual</span>',
               f'<span class="today lv-4" style="left:{_f(xs(last["days_ahead"]) / VB_W * 100)}%;'
               f'top:{_f(ys(last["pct"]))}%"></span>']
    for d, text in ((60, "60 days before"), (30, "30"), (14, "14"), (7, "7"), (1, "1 day")):
        if d <= max_d:
            pos = xs(d) / VB_W * 100
            edge = " edge-start" if pos < 8 else " edge-end" if pos > 92 else ""
            overlay.append(f'<span class="tick{edge}" style="left:{_f(pos)}%">{text}</span>')
    return (f'<div class="plot plot-sm has-axis has-y" role="img" aria-label="{esc(label)}">'
            f'{svg}<div class="overlay">{"".join(overlay)}</div></div>')


def _nice_ticks(lo: float, hi: float, n: int) -> list[float]:
    raw = (hi - lo) / max(n, 1)
    if raw <= 0:
        return [lo]
    mag = 10 ** math.floor(math.log10(raw))
    step = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw)
    v = math.ceil(lo / step) * step
    out = []
    while v <= hi:
        out.append(v)
        v += step
    return out


# ----------------------------------------------------------------------------- formatting

def inr(value: float) -> str:
    """Indian digit grouping: 124500 -> 1,24,500."""
    n = int(round(value))
    sign = "-" if n < 0 else ""
    s = str(abs(n))
    if len(s) <= 3:
        return sign + s
    head, tail = s[:-3], s[-3:]
    groups = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    if head:
        groups.insert(0, head)
    return sign + ",".join(groups) + "," + tail


def day_month(d: dt.date) -> str:
    return f"{d.day} {MONTHS[d.month - 1]}"
