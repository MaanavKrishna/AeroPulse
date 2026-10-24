"""The site and API, end to end on the session's demo database."""
import pytest
from fastapi.testclient import TestClient

PAGES = ["/", "/routes", "/routes?sort=name", "/routes/del-bom", "/routes/del-bom?w=1-7&range=all",
         "/festivals", "/festivals/diwali-2026", "/methodology", "/data", "/api", "/status",
         "/about", "/embed/routes/del-bom", "/fragments/hero?origin=BLR&dest=CCU&w=1-7"]


@pytest.fixture(scope="module")
def client(demo_db):
    from aeropulse.app import create_app
    return TestClient(create_app())


@pytest.mark.parametrize("path", PAGES)
def test_pages_render(client, path):
    r = client.get(path)
    assert r.status_code == 200, r.text[:500]
    assert "text/html" in r.headers["content-type"]


def test_demo_is_labelled_everywhere(client):
    home = client.get("/").text
    assert "Demo data." in home and 'name="robots" content="noindex"' in home
    assert client.get("/v1/meta").json()["data_mode"] == "demo"
    assert "Disallow: /" in client.get("/robots.txt").text
    assert "DEMO DATA" in client.get("/img/routes/del-bom.svg").text
    assert "Demo data, not real fares" in client.get("/embed/routes/del-bom").text


def test_pages_work_without_javascript(client):
    """Charts are server-rendered SVG, so the HTML alone carries them."""
    html = client.get("/routes/del-bom").text
    assert html.count("<svg") >= 3 and "ribbon-area" in html
    assert "Higher than usual" in html or "Lower than usual" in html or "About usual" in html \
        or "Not enough history" in html


def test_no_prediction_language(client):
    for path in ("/", "/routes/del-bom", "/festivals/diwali-2026"):
        text = client.get(path).text.lower()
        for phrase in ("will rise", "will fall", "will go up", "will drop", "predict that",
                       "book now"):
            assert phrase not in text, (path, phrase)


def test_unknown_route_is_404(client):
    assert client.get("/routes/del-xyz").status_code == 404
    assert client.get("/v1/routes/DEL-XYZ").status_code == 404


def test_api_shapes(client):
    routes = client.get("/v1/routes").json()
    assert len(routes["routes"]) == 40
    one = client.get("/v1/routes/del-bom?window=15-30").json()
    assert one["route"] == "DEL-BOM" and len(one["windows"]) == 1
    assert one["windows"][0]["verdict"]["level"] in {"above", "below", "typical", "unknown"}
    nat = client.get("/v1/indices/national?from=2026-10-01").json()
    assert nat["points"][0]["date"] >= "2026-10-01" and nat["kind"] == "chained"
    csv = client.get("/v1/indices/national?format=csv")
    assert csv.text.startswith("date,value,ci95_low")
    assert client.get("/v1/indices/windows/9-99").status_code == 404
    assert client.get("/v1/festivals/diwali-2026").json()["routes"]
    assert "demo" in client.get("/v1/status").json()["providers"]


def test_security_headers(client):
    r = client.get("/")
    assert "frame-ancestors 'self'" in r.headers["content-security-policy"]
    assert "script-src 'self'" in r.headers["content-security-policy"]
    assert r.headers["x-content-type-options"] == "nosniff"
    assert "frame-ancestors *" in client.get("/embed/routes/del-bom").headers[
        "content-security-policy"]
    assert client.get("/v1/meta").headers["access-control-allow-origin"] == "*"


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
    assert c.get("/v1/x").headers["retry-after"]


def test_csv_and_feed(client):
    csv = client.get("/routes/del-bom/data.csv?w=8-14")
    assert csv.text.startswith("date,route,window,median_cheapest_fare_inr")
    feed = client.get("/feeds/routes/del-bom.xml")
    assert feed.headers["content-type"].startswith("application/atom+xml")
    assert "<entry>" in feed.text


def test_static_assets_are_content_hashed(client):
    html = client.get("/").text
    assert "/static/css/app.css?v=" in html
    r = client.get("/static/css/app.css")
    assert "immutable" in r.headers["cache-control"]


def test_home_map_draws_every_route_as_a_link(client):
    html = client.get("/?origin=DEL&dest=PAT").text
    assert html.count('class="arc ') == 40
    assert html.count('class="arc-hit"') == 40
    assert 'class="arc lv-4 is-selected"' in html or 'is-selected" d=' in html
    assert html.count("<animateMotion") == 40
    assert 'href="/routes/del-pat"' in html


def test_hero_fragment_is_only_the_answer(client):
    """The map stays on the page; the fragment swaps the question, picker and answer."""
    html = client.get("/fragments/hero?origin=BLR&dest=CCU&w=1-7").text
    assert 'data-route="BLR-CCU"' in html and "data-hero-form" in html
    assert "sky-map" not in html


def test_route_page_has_flight_header(client):
    html = client.get("/routes/del-pat").text
    assert 'class="flight"' in html and "animateMotion" in html
    assert "view-transition-name: rt-del-pat" in html
