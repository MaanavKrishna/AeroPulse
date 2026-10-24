"""Number and date formatting shared by templates, charts and generated text."""
from __future__ import annotations

import datetime as dt
import html

MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def esc(s: object) -> str:
    return html.escape(str(s), quote=True)


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
