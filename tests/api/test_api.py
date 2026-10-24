"""The public API, end to end on the session's demo database. The website reads only this
API, so every page's data is covered here."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client(demo_db):
    from aeropulse.app import create_app
    return TestClient(create_app())


@pytest.mark.parametrize("path", [
    "/", "/v1/meta", "/v1/insights", "/v1/routes", "/v1/routes/DEL-BOM",
    "/v1/routes/del-bom/fares?window=8-14", "/v1/routes/DEL-BOM/calendar", "/v1/airports",
    "/v1/airports/DEL", "/v1/methodology", "/v1/sources", "/v1/downloads", "/v1/status",
    "/v1/festivals", "/v1/festivals/diwali-2026", "/v1/indices/national",
    "/v1/indices/windows/8-14", "/v1/indices/routes/DEL-BOM", "/healthz", "/robots.txt",
])
def test_endpoints_answer(client, path):
    assert client.get(path).status_code == 200


def test_demo_is_labelled(client):
    for path in ("/v1/meta", "/v1/routes", "/v1/insights", "/v1/routes/DEL-BOM"):
        assert client.get(path).json()["data_mode"] == "demo"
    assert "DEMO DATA" in client.get("/img/routes/del-bom.svg").text
    assert "demo data" in client.get("/feeds/routes/del-bom.xml").text


def test_routes_list_carries_sparklines_and_distance(client):
    routes = client.get("/v1/routes").json()["routes"]
    assert len(routes) == 40
    r = next(x for x in routes if x["route"] == "DEL-BOM")
    assert 1100 < r["distance_km"] < 1170
    assert r["origin_city"] == "Delhi" and r["destination_city"] == "Mumbai"
    assert len(r["series"]) > 30 and len(r["series"][0]) == 4
    assert r["verdict"]["level"] in {"above", "below", "typical", "unknown"}


def test_route_detail(client):
    d = client.get("/v1/routes/DEL-BOM").json()
    assert [w["window"] for w in d["windows"]] == ["1-7", "8-14", "15-30", "31-60"]
    assert d["origin"]["icao"] == "VIDP" and d["reverse"] == "BOM-DEL"
    assert d["booking_curve"] and d["weekdays"]
    days = {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}
    assert {w["weekday"] for w in d["weekdays"]} <= days


def test_route_fares_have_ranges(client):
    f = client.get("/v1/routes/DEL-BOM/fares?window=15-30&days=30").json()
    assert len(f["points"]) == 30
    date, value, low, high = f["points"][-1]
    assert low <= value <= high
    assert f["latest"]["median_inr"] == value
    assert client.get("/v1/routes/DEL-BOM/fares?window=9-99").status_code == 422


def test_insights(client):
    i = client.get("/v1/insights").json()
    assert i["national"]["series"] and len(i["windows"]) == 4
    assert i["movers"]["up"] and i["movers"]["down"]
    curve = {c["days_ahead"]: c["pct_vs_route_median"] for c in i["booking_curve"]}
    assert curve[1] > curve[30]          # last-minute fares are dearer in the demo data
    assert len(i["weekdays"]) == 7


def test_airport_page_data(client):
    a = client.get("/v1/airports/PAT").json()
    assert a["airport"]["city"] == "Patna"
    assert [r["route"] for r in a["departures"]] == ["PAT-DEL"]
    assert [r["route"] for r in a["arrivals"]] == ["DEL-PAT"]
    assert client.get("/v1/airports/XXX").status_code == 404


def test_unknown_route_is_404(client):
    assert client.get("/v1/routes/DEL-XYZ").status_code == 404
    assert client.get("/img/routes/del-xyz.svg").status_code == 404


def test_files(client):
    csv = client.get("/csv/routes/del-bom.csv?w=8-14")
    assert csv.text.startswith("date,route,window,median_cheapest_fare_inr")
    assert client.get("/downloads/../config.py").status_code == 404
    feed = client.get("/feeds/routes/del-bom.xml")
    assert feed.headers["content-type"].startswith("application/atom+xml")


def test_headers(client):
    r = client.get("/v1/meta")
    assert r.headers["access-control-allow-origin"] == "*"
    assert r.headers["content-security-policy"] == "default-src 'none'; frame-ancestors 'none'"
    assert "content-security-policy" not in client.get("/v1/docs").headers


def test_admin_disabled_without_token(client):
    assert client.post("/v1/admin/rebuild").status_code == 404


def test_rate_limit():
    from fastapi import FastAPI

    from aeropulse.app import RateLimit
    app = FastAPI()
    app.add_middleware(RateLimit, per_minute=2)

    @app.get("/v1/x")
    def x():
        return {}
    c = TestClient(app)
    assert [c.get("/v1/x").status_code for _ in range(3)] == [200, 200, 429]


def test_site_key_skips_rate_limit():
    from fastapi import FastAPI

    from aeropulse.app import RateLimit
    app = FastAPI()
    app.add_middleware(RateLimit, per_minute=1, site_key="s3cret")

    @app.get("/v1/x")
    def x():
        return {}
    c = TestClient(app)
    site = {"X-AeroPulse-Site-Key": "s3cret"}
    assert [c.get("/v1/x", headers=site).status_code for _ in range(3)] == [200, 200, 200]
    wrong = {"X-AeroPulse-Site-Key": "nope"}
    assert [c.get("/v1/x", headers=wrong).status_code for _ in range(2)] == [200, 429]


def test_great_circle_distance():
    from aeropulse.reference import great_circle_km
    assert 1100 < great_circle_km("DEL", "BOM") < 1170
    assert great_circle_km("DEL", "BOM") == great_circle_km("BOM", "DEL")
