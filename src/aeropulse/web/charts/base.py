"""Geometry and colour shared by every chart.

Page charts are HTML fragments: shapes in an SVG that stretches to any width
(`preserveAspectRatio="none"`, strokes that do not scale) and every label positioned as
HTML on top, so text never distorts. Colours are CSS custom properties from
static/css/tokens.css, so charts follow the theme; standalone files use STANDALONE.
"""
from __future__ import annotations

import math

LEVEL_VARS = ("--r-cool-2", "--r-cool-1", "--r-even", "--r-warm-1", "--r-warm-2")
LEVEL_NAMES = ("much lower than usual", "lower than usual", "usual", "higher than usual",
               "much higher than usual")
CSS = {"ink": "var(--ink)", "muted": "var(--ink-muted)", "band": "var(--band)",
       "grid": "var(--rule)", "accent": "var(--accent)", "sky": "var(--sky)",
       "levels": tuple(f"var({v})" for v in LEVEL_VARS)}
STANDALONE = {"ink": "#16202C", "muted": "#5A6676", "band": "#D7DDE5", "grid": "#DCE2E9",
              "accent": "#3036A0", "sky": "#F2F5F8",
              "levels": ("#1D6FA5", "#6FA3C7", "#B4BDC9", "#DD8A70", "#C4492C")}
VB_W, VB_H = 1000, 100        # stretchable viewBox for page charts


def fmt(x: float) -> str:
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


def bounds(values: list[float], pad: float = 0.12) -> tuple[float, float]:
    lo, hi = min(values), max(values)
    span = max(hi - lo, abs(hi) * 0.01, 1e-6)
    return lo - span * pad, hi + span * pad


def nice_ticks(lo: float, hi: float, n: int) -> list[float]:
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
