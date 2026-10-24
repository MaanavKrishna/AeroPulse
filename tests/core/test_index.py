"""Properties the index formula and the chain must have."""
import datetime as dt
import math

import pytest

from aeropulse.core.index import (
    Point,
    Product,
    Segment,
    chain_link,
    compute_index,
    decompose,
    logarithmic_mean,
    product_key,
    product_prices,
)

DAY = dt.date(2026, 11, 1)
A = product_key("DEL-BOM", "8-14")
B = product_key("DEL-BLR", "8-14")


def products(base_a=5000.0, base_b=4000.0, wa=0.5, wb=0.5):
    return {A: Product(A, "DEL-BOM", "8-14", wa, base_a),
            B: Product(B, "DEL-BLR", "8-14", wb, base_b)}


def prices(rows):
    return {(d, k): {"price": p, "n": 7, "route_id": k.split("/")[0], "window": "8-14"}
            for d, k, p in rows}


def test_geometric_not_arithmetic():
    """Relatives of 2.0 and 0.5 with equal weights: geometric mean 1.0, so 100. The
    arithmetic mean would say 125 for two prices that moved in offsetting proportions."""
    point = compute_index(prices([(DAY, A, 10000.0), (DAY, B, 2000.0)]), products())[0]
    assert point.value == pytest.approx(100.0)


def test_time_reversal():
    d0, d1 = DAY, DAY + dt.timedelta(days=1)
    fwd = compute_index(prices([(d0, A, 5000.0), (d0, B, 4000.0),
                                (d1, A, 7000.0), (d1, B, 3000.0)]), products())
    back = compute_index(prices([(d0, A, 5000.0), (d0, B, 4000.0)]),
                         products(7000.0, 3000.0))[0].value
    assert (fwd[1].value / fwd[0].value) * (back / 100) == pytest.approx(1.0, abs=1e-12)


def test_daily_chaining_equals_direct_measure():
    days = [DAY + dt.timedelta(days=i) for i in range(6)]
    a = [5000, 5400, 5100, 5900, 5300, 5600]
    b = [4000, 3800, 4300, 3900, 4400, 4100]
    pts = compute_index(prices([(d, k, float(v)) for d, va, vb in zip(days, a, b, strict=True)
                                for k, v in ((A, va), (B, vb))]), products())
    chained = math.prod(y.value / x.value for x, y in zip(pts, pts[1:], strict=False))
    assert chained == pytest.approx(pts[-1].value / pts[0].value, rel=1e-12)


def test_non_positive_price_is_skipped_and_coverage_falls():
    point = compute_index(prices([(DAY, A, 5500.0), (DAY, B, 0.0)]), products())[0]
    assert point.product_count == 1
    assert point.coverage == pytest.approx(50.0)
    assert point.status == "insufficient_data"


def test_logarithmic_mean():
    assert logarithmic_mean(5.0, 5.0) == pytest.approx(5.0)
    assert logarithmic_mean(100.0, 110.0) == pytest.approx(10 / math.log(1.1))


def test_decomposition_sums_exactly_to_the_change():
    d0, d1 = DAY, DAY + dt.timedelta(days=1)
    pts = compute_index(prices([(d0, A, 5000.0), (d0, B, 4000.0),
                                (d1, A, 6100.0), (d1, B, 3700.0)]), products())
    result = decompose(pts, lag=1)
    change = pts[1].value - pts[0].value
    assert sum(r["points"] for r in result["routes"]) == pytest.approx(change, abs=1e-9)
    assert sum(w["points"] for w in result["windows"]) == pytest.approx(change, abs=1e-9)


def test_product_price_is_median_of_departure_dates_and_needs_enough_dates():
    obs = [{"route_id": "DEL-BOM", "window": "8-14", "collection_date": DAY, "fare": f,
            "eligible": True} for f in (5000, 9000, 5200, 5100)]
    obs.append({"route_id": "DEL-BLR", "window": "8-14", "collection_date": DAY,
                "fare": 4000, "eligible": True})
    out = product_prices(obs)
    assert out[(DAY, A)]["price"] == pytest.approx(5150.0)
    assert (DAY, B) not in out                       # one date is not enough


def test_ineligible_fares_are_ignored():
    obs = [{"route_id": "DEL-BOM", "window": "8-14", "collection_date": DAY, "fare": f,
            "eligible": e} for f, e in ((5000, True), (5100, True), (5200, True), (90000, False))]
    assert product_prices(obs)[(DAY, A)]["price"] == pytest.approx(5100.0)


# ---------------------------------------------------------------------- chaining

DAYS = [DAY + dt.timedelta(days=i) for i in range(6)]


def series(values, start=0):
    return [Point(DAYS[i + start].isoformat(), DAYS[i + start], DAYS[i + start], v, 100.0,
                  10, 2, "valid") for i, v in enumerate(values)]


def test_single_basket_passes_through():
    linked, links = chain_link([Segment("b1", series([100.0, 101.0, 102.0]))])
    assert [p.value for p in linked] == [100.0, 101.0, 102.0] and links == []


def test_splice_removes_level_jump_and_keeps_growth():
    linked, links = chain_link([Segment("b1", series([100.0, 101.0, 102.0])),
                                Segment("b2", series([200.0, 206.0, 212.18], start=2))])
    assert links[0].factor == pytest.approx(102.0 / 200.0)
    v = [p.value for p in linked]
    assert v[:3] == [100.0, 101.0, 102.0]
    assert v[3] / v[2] == pytest.approx(206.0 / 200.0)
    assert v[4] / v[3] == pytest.approx(212.18 / 206.0)
    assert [p.version for p in linked] == ["b1", "b1", "b1", "b2", "b2"]
    assert [p.is_link_period for p in linked] == [False, False, True, False, False]


def test_link_without_overlap_is_refused():
    with pytest.raises(ValueError, match="share no period"):
        chain_link([Segment("b1", series([100.0, 101.0])),
                    Segment("b2", series([200.0, 206.0], start=3))])


def test_route_sub_index_is_invariant_to_route_weights():
    rows = [(d, k, base * (1 + rate * i)) for i, d in enumerate(DAYS[:3])
            for k, base, rate in ((A, 5000.0, 0.05), (B, 4000.0, -0.01))]
    p = prices(rows)
    for route in ("DEL-BOM", "DEL-BLR"):
        heavy = compute_index(p, products(wa=0.8, wb=0.2), route=route)
        light = compute_index(p, products(wa=0.2, wb=0.8), route=route)
        assert [x.value for x in heavy] == pytest.approx([x.value for x in light])
    nat_h = compute_index(p, products(wa=0.8, wb=0.2))
    nat_l = compute_index(p, products(wa=0.2, wb=0.8))
    assert [x.value for x in nat_h] != pytest.approx([x.value for x in nat_l])
