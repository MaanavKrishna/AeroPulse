"""Provider adapters: parse exactly what the published schema says, fail loudly otherwise,
and refuse configurations that would publish something untrue. No network."""
import datetime as dt
import json

import httpx
import pytest

from aeropulse.config import Settings
from aeropulse.providers import ProviderError, make_provider
from aeropulse.providers.demo import DemoProvider, demo_fare
from aeropulse.providers.ignav import IgnavProvider, parse_cheapest_dates
from aeropulse.providers.travelpayouts import (
    TravelpayoutsProvider,
    months_between,
    parse_prices_for_dates,
)

START, END = dt.date(2026, 10, 25), dt.date(2026, 12, 23)


def test_ignav_parser(fixture_text):
    fares, observed = parse_cheapest_dates(fixture_text("ignav_cheapest_dates.json"))
    assert [f.departure_date.day for f in fares] == [25, 26, 28]      # null price skipped
    assert fares[0].fare == 8459.0 and fares[0].currency == "INR"
    assert fares[2].price_status == "unverified"
    assert observed == dt.datetime(2026, 10, 24, 6, 12, 44, tzinfo=dt.UTC)


@pytest.mark.parametrize("payload", ['{"origin": "DEL"}', '{"dates": "nope"}',
                                     '{"dates": [{"departure_date": "x", "price": {}}]}', "<html>"])
def test_ignav_schema_change_is_an_error_not_data(payload):
    from aeropulse.providers.base import SchemaChangeError
    with pytest.raises(SchemaChangeError):
        parse_cheapest_dates(payload)


def test_ignav_request_shape_and_auth(fixture_text):
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["key"] = request.headers.get("X-Api-Key")
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, text=fixture_text("ignav_cheapest_dates.json"))

    client = httpx.Client(base_url="https://ignav.com/api", transport=httpx.MockTransport(handler),
                          headers={"X-Api-Key": "test-key"})
    r = IgnavProvider("test-key", client=client).cheapest_dates("DEL", "BOM", START, END)
    assert seen["url"] == "https://ignav.com/api/fares/cheapest-dates"
    assert seen["key"] == "test-key"
    assert seen["body"]["departure_date_range"] == {"start": "2026-10-25", "end": "2026-12-23"}
    assert seen["body"]["cabin_class"] == "economy" and seen["body"]["market"] == "IN"
    assert r.error is None and len(r.fares) == 3 and r.payload_sha256


def test_ignav_http_error_is_recorded_not_raised():
    def handler(request):
        return httpx.Response(402, json={"error": {"type": "billing", "code": "payment_required",
                                                   "message": "Add a card"}})
    client = httpx.Client(base_url="https://ignav.com/api", transport=httpx.MockTransport(handler))
    r = IgnavProvider("k", client=client).cheapest_dates("DEL", "BOM", START, END)
    assert r.fares == [] and r.http_status == 402
    assert r.error == "HTTP 402 payment_required: Add a card"


def test_ignav_needs_a_key():
    with pytest.raises(ProviderError):
        IgnavProvider("")


def test_travelpayouts_parser_keeps_cheapest_per_date(fixture_text):
    fares = parse_prices_for_dates(fixture_text("travelpayouts_prices_for_dates.json"))
    assert [(f.departure_date.day, f.fare, f.carrier) for f in fares] == \
        [(3, 4890.0, "AI"), (4, 5510.0, "QP")]
    assert fares[0].currency == "INR"


def test_travelpayouts_calls_once_per_month(fixture_text):
    months = []

    def handler(request):
        months.append(request.url.params["departure_at"])
        assert request.headers["X-Access-Token"] == "t"
        return httpx.Response(200, text=fixture_text("travelpayouts_prices_for_dates.json"))

    client = httpx.Client(base_url="https://api.travelpayouts.com",
                          transport=httpx.MockTransport(handler), headers={"X-Access-Token": "t"})
    r = TravelpayoutsProvider("t", client=client).cheapest_dates("DEL", "BOM", START, END)
    assert months == ["2026-10", "2026-11", "2026-12"] and r.calls == 3
    assert months_between(dt.date(2026, 12, 30), dt.date(2027, 1, 2)) == ["2026-12", "2027-01"]


def test_demo_is_deterministic_and_plausible():
    a = DemoProvider(dt.date(2026, 10, 1)).cheapest_dates("DEL", "BOM", START, END)
    b = DemoProvider(dt.date(2026, 10, 1)).cheapest_dates("DEL", "BOM", START, END)
    assert [f.fare for f in a.fares] == [f.fare for f in b.fares]
    assert 50 < len(a.fares) <= 60
    assert all(f.fare > 800 for f in a.fares)
    near = demo_fare("DEL-BOM", dt.date(2026, 10, 1), dt.date(2026, 10, 2))
    far = demo_fare("DEL-BOM", dt.date(2026, 10, 1), dt.date(2026, 11, 5))
    assert near is None or far is None or near > far


# ---------------------------------------------------------------- guards

def test_production_refuses_demo():
    s = Settings(env="production", providers="demo")
    with pytest.raises(RuntimeError, match="demo provider"):
        s.check()
    with pytest.raises(ProviderError):
        make_provider("demo", s, START)


def test_production_refuses_unreviewed_terms_unless_trial():
    s = Settings(env="production", providers="ignav", ignav_api_key="k")
    with pytest.raises(ProviderError, match="terms not yet reviewed"):
        make_provider("ignav", s, START)
    trial = Settings(env="production", providers="ignav", ignav_api_key="k",
                     allow_unreviewed_terms=True)
    assert make_provider("ignav", trial, START).name == "ignav"


def test_unknown_provider():
    with pytest.raises(ProviderError, match="unknown provider"):
        make_provider("scraper", Settings(), START)
