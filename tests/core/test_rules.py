"""Uncertainty, screening and the "usual" verdict."""
import datetime as dt

import pytest

from aeropulse.core.index import product_key
from aeropulse.core.methodology import window_for
from aeropulse.core.quality import robust_z, screen
from aeropulse.core.variance import BasketSpec, bootstrap
from aeropulse.core.verdict import percentile, verdict

DAY = dt.date(2026, 11, 1)


def fares(route, day, values, window="8-14"):
    return [{"route_id": route, "window": window, "collection_date": day, "fare": v,
             "eligible": True, "currency": "INR"} for v in values]


# ---------------------------------------------------------------- windows

def test_windows_cover_1_to_60_days_without_gaps():
    assert window_for(0) is None
    assert window_for(61) is None
    assert [window_for(d).key for d in (1, 7, 8, 14, 15, 30, 31, 60)] == \
        ["1-7", "1-7", "8-14", "8-14", "15-30", "15-30", "31-60", "31-60"]


# ---------------------------------------------------------------- screening

def test_screening_rules():
    rows = fares("DEL-BOM", DAY, [5000, 5100, 5200, 5300, 5050, 31000])
    rows += [{**fares("DEL-BOM", DAY, [5000])[0], "currency": "USD"},
             {**fares("DEL-BOM", DAY, [500])[0]},
             {**fares("DEL-BOM", DAY, [5000])[0], "window": None}]
    out = screen(rows)
    reasons = [r["exclusion_reason"] for r in out]
    assert reasons[:5] == [None] * 5
    assert reasons[5] == "outlier"
    assert reasons[6:] == ["currency", "implausible_price", "outside_horizon"]
    assert all(r["eligible"] == (r["exclusion_reason"] is None) for r in out)


def test_no_outliers_called_on_tiny_groups():
    out = screen(fares("DEL-BOM", DAY, [5000, 5100, 40000]))
    assert all(r["eligible"] for r in out)


def test_robust_z_zero_spread():
    assert robust_z(5.0, [5.0, 5.0, 5.0]) == 0.0


# ---------------------------------------------------------------- bootstrap

def _obs(days=6):
    out = []
    for i in range(days):
        d = DAY + dt.timedelta(days=i)
        out += fares("DEL-BOM", d, [5000 + 40 * i + j * 90 for j in range(7)])
        out += fares("DEL-BLR", d, [4000 - 10 * i + j * 70 for j in range(7)])
    return out


def _spec():
    return BasketSpec({product_key("DEL-BOM", "8-14"): 0.5,
                       product_key("DEL-BLR", "8-14"): 0.5}, DAY, DAY + dt.timedelta(days=1))


def test_bootstrap_is_deterministic_and_positive():
    a = bootstrap(_obs(), [_spec()], replications=60, seed=7)
    b = bootstrap(_obs(), [_spec()], replications=60, seed=7)
    assert a.keys() == b.keys() and len(a) == 6
    for k in a:
        assert a[k].standard_error == b[k].standard_error > 0
        assert a[k].ci95_low < a[k].ci95_high


def test_bootstrap_chain_rebuilt_in_each_replication():
    spec2 = BasketSpec({product_key("DEL-BOM", "8-14"): 0.8,
                        product_key("DEL-BLR", "8-14"): 0.2}, DAY, DAY + dt.timedelta(days=1))
    link = (DAY + dt.timedelta(days=3)).isoformat()
    chained = bootstrap(_obs(), [_spec(), spec2], link_periods=[link], replications=60)
    assert len(chained) == 6


# ---------------------------------------------------------------- verdict

def _history(n, value=100.0):
    return [(DAY - dt.timedelta(days=n - i), value + (i % 5)) for i in range(n)]


def test_no_verdict_with_short_history():
    v = verdict(_history(10) + [(DAY, 150.0)])
    assert v.level == "unknown" and v.history_days == 10


@pytest.mark.parametrize("today,level", [(150.0, "above"), (90.0, "below"), (102.0, "typical")])
def test_verdict_levels(today, level):
    v = verdict(_history(60) + [(DAY, today)])
    assert v.level == level
    assert v.low <= v.median <= v.high


def test_verdict_ignores_history_outside_lookback():
    old = [(DAY - dt.timedelta(days=200 + i), 1000.0) for i in range(50)]
    v = verdict(old + _history(30) + [(DAY, 103.0)])
    assert v.history_days == 30 and v.level == "typical"


def test_percentile_interpolates():
    assert percentile([1.0, 2.0, 3.0, 4.0], 50) == pytest.approx(2.5)
    assert percentile([1.0, 2.0, 3.0, 4.0], 25) == pytest.approx(1.75)
