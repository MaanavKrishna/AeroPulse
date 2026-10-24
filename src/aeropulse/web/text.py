"""Every sentence the site generates from data. One place, so wording stays consistent
and never drifts into prediction.

Voice: plain words, sentence case, active voice. Describe the past ("has been", "usually"),
never the future.
"""
from __future__ import annotations

from ..core.methodology import MIN_HISTORY_FOR_VERDICT, WINDOW_BY_KEY
from ..core.verdict import Verdict
from .charts.svg import day_month, inr

MARKS = {"above": "▲", "below": "▼", "typical": "●", "unknown": "○"}


def level_class(level: str) -> str:
    return {"above": "lv-4", "below": "lv-0", "typical": "lv-2"}.get(level, "lv-u")


def pct(value: float | None) -> str:
    if value is None:
        return ""
    return f"{abs(value):.0f}%"


def short_verdict(v: Verdict) -> str:
    """For list rows: '▲ 31% above usual', '● usual', '▼ 9% below usual'."""
    if v.level == "unknown":
        return "Too new to judge"
    if v.level == "typical":
        return "Usual"
    word = "above" if v.level == "above" else "below"
    return f"{pct(v.pct_vs_median)} {word} usual"


def window_phrase(window: str) -> str:
    return WINDOW_BY_KEY[window].label if window in WINDOW_BY_KEY else window


def fare_verdict(v: Verdict, window: str, route_name: str) -> dict:
    """Headline and explanation for one route and booking window, in rupees."""
    when = window_phrase(window)
    if v.level == "unknown":
        need = MIN_HISTORY_FOR_VERDICT - v.history_days
        return {"headline": "Not enough history yet",
                "body": (f"We need {MIN_HISTORY_FOR_VERDICT} days of prices on {route_name} "
                         f"before we can say what is usual. {need} more to go."),
                "level": "unknown"}
    typical = f"₹{inr(v.low)}–₹{inr(v.high)}"
    if v.level == "typical":
        body = (f"The cheapest fares for flights {when} are around ₹{inr(v.value)}, inside "
                f"this route's usual range of {typical}.")
    else:
        word = "above" if v.level == "above" else "below"
        body = (f"The cheapest fares for flights {when} are around ₹{inr(v.value)}, "
                f"{pct(v.pct_vs_median)} {word} the usual {typical}.")
    return {"headline": v.headline, "body": body, "level": v.level}


def index_verdict(v: Verdict, subject: str = "Domestic fares") -> str:
    if v.level == "unknown":
        return f"{subject}: not enough history yet to say what is usual."
    if v.level == "typical":
        return f"{subject} are about where they usually are."
    word = "above" if v.level == "above" else "below"
    return f"{subject} are {pct(v.pct_vs_median)} {word} usual."


def as_of(date) -> str:
    return day_month(date) if date else ""


def cheapest_sentence(stretch: tuple[int, int] | None) -> str:
    if not stretch:
        return "Not enough data yet to say when this route is usually cheapest."
    a, b = stretch
    if a >= 14:
        lo, hi = round(a / 7), round(b / 7)
        span = f"about {lo} weeks" if lo == hi else f"{lo} to {hi} weeks"
    else:
        span = f"about {a} days" if a == b else f"{a} to {b} days"
    return f"Over the last month, fares were usually lowest {span} before departure."
