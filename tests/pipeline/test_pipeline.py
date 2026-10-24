"""Collection, build, revisions, basket changes, export and rebuild, official imports."""
import datetime as dt

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from aeropulse.db.models import (
    Base,
    BasketWeight,
    CollectionRun,
    Fare,
    IndexLink,
    IndexRevision,
    IndexValue,
    RawResponse,
    TrafficStat,
)
from aeropulse.pipeline.build import build
from aeropulse.pipeline.collect import collect, purge_day
from aeropulse.providers.base import ProviderResponse
from aeropulse.providers.demo import DemoProvider
from aeropulse.reference import BasketVersion, routes_to_collect

START = dt.date(2026, 9, 1)
ROUTES = ("DEL-BOM", "BOM-DEL", "DEL-BLR")


@pytest.fixture
def session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'p.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def collect_days(s, versions, days, start=START):
    for i in range(days):
        day = start + dt.timedelta(days=i)
        collect(s, DemoProvider(day), routes_to_collect(day, versions), day,
                max_calls_per_day=1000)
    s.flush()


def test_collect_stores_raw_and_screened_fares(session):
    run = collect(session, DemoProvider(START), list(ROUTES), START, max_calls_per_day=100)
    assert run.status == "ok" and run.routes_ok == 3 and run.calls == 3 and run.is_demo
    raws = session.scalars(select(RawResponse)).all()
    assert len(raws) == 3 and all(r.payload_sha256 and r.error is None for r in raws)
    fares = session.scalars(select(Fare)).all()
    assert len(fares) == run.fares_stored > 150
    assert all(f.days_ahead >= 1 and f.window for f in fares)
    assert all(f.eligible == (f.exclusion_reason is None) for f in fares)


def test_budget_cap_stops_the_run(session):
    run = collect(session, DemoProvider(START), list(ROUTES), START, max_calls_per_day=2)
    assert run.status == "budget_exhausted" and run.calls == 2
    assert "daily call cap" in run.message


class Failing:
    name, is_demo = "ignav", False

    def cheapest_dates(self, o, d, start, end):
        return ProviderResponse("ignav", {"origin": o}, 503, "{}", None, [], "HTTP 503")

    def close(self):
        pass


def test_failed_route_is_recorded_not_raised(session):
    run = collect(session, Failing(), ["DEL-BOM"], START, max_calls_per_day=10)
    assert run.status == "failed" and "HTTP 503" in run.message
    assert session.scalar(select(RawResponse.error)) == "HTTP 503"


def test_purge_makes_a_day_repeatable(session):
    collect(session, DemoProvider(START), ["DEL-BOM"], START, max_calls_per_day=10)
    assert purge_day(session, "demo", START) == 1
    assert session.scalar(select(func.count()).select_from(Fare)) == 0


def test_build_is_idempotent_and_chained(session):
    versions = [BasketVersion("b1", START, ROUTES)]
    collect_days(session, versions, 12)
    first = build(session, versions, "demo", replications=10)
    assert first.points_written > 0 and first.is_demo
    second = build(session, versions, "demo", replications=10)
    assert second.revisions == 0
    nat = session.scalars(select(IndexValue).where(IndexValue.scope == "national",
                                                   IndexValue.kind == "CHAINED")
                          .order_by(IndexValue.period)).all()
    assert len(nat) == 12
    base = [v.value for v in nat[:7]]
    assert sum(base) / 7 == pytest.approx(100.0, abs=3.0)
    assert all(v.ci95_low < v.value < v.ci95_high for v in nat)
    weights = session.scalars(select(BasketWeight)).all()
    assert {w.source for w in weights} == {"equal"}


def test_changed_fare_is_logged_as_revision(session):
    versions = [BasketVersion("b1", START, ROUTES)]
    collect_days(session, versions, 9)
    build(session, versions, "demo", replications=0)
    last_day = START + dt.timedelta(days=8)
    for f in session.scalars(select(Fare).where(Fare.collection_date == last_day)):
        f.fare *= 1.10
    session.flush()
    report = build(session, versions, "demo", replications=0, reason="late correction")
    assert report.revisions > 0
    rev = session.scalars(select(IndexRevision)).first()
    assert rev.reason == "late correction" and rev.new_value > rev.old_value


def test_basket_change_links_without_a_jump(session):
    link_day = START + dt.timedelta(days=10)
    versions = [BasketVersion("b1", START, ("DEL-BOM", "BOM-DEL")),
                BasketVersion("b2", link_day, ("DEL-BOM", "BOM-DEL", "DEL-BLR"))]
    collect_days(session, versions, 20)
    build(session, versions, "demo", replications=10)
    link = session.scalars(select(IndexLink).where(IndexLink.scope == "national")).one()
    assert link.link_period == link_day.isoformat()
    nat = {v.period: v for v in session.scalars(select(IndexValue).where(
        IndexValue.scope == "national", IndexValue.kind == "CHAINED"))}
    assert nat[link_day.isoformat()].basket_version == "b1"
    after = (link_day + dt.timedelta(days=1)).isoformat()
    assert nat[after].basket_version == "b2"
    # DEL-BLR was not priced before the link day, so the old basket never sees it
    routes = {v.route_id for v in session.scalars(select(IndexValue).where(
        IndexValue.scope == "route"))}
    assert routes == {"DEL-BOM", "BOM-DEL", "DEL-BLR"}


def test_dgca_weights_replace_equal_weights(session, tmp_path):
    from aeropulse.official.dgca import ImportErrorRow, import_csv
    csv = tmp_path / "dgca.csv"
    csv.write_text("period,origin,destination,passengers,source_url\n"
                   "2026-08,DEL,BOM,600000,https://www.dgca.gov.in/x\n"
                   "2026-08,BOM,DEL,600000,https://www.dgca.gov.in/x\n"
                   "2026-08,DEL,BLR,300000,https://www.dgca.gov.in/x\n")
    assert import_csv(session, csv) == 3
    versions = [BasketVersion("b1", START, ROUTES)]
    collect_days(session, versions, 8)
    build(session, versions, "demo", replications=0)
    w = {x.route_id: x.weight for x in session.scalars(select(BasketWeight))}
    assert w["DEL-BOM"] == pytest.approx(0.4) and w["DEL-BLR"] == pytest.approx(0.2)
    assert session.scalar(select(BasketWeight.source)).startswith("dgca:")
    bad = tmp_path / "bad.csv"
    bad.write_text("period,origin,destination,passengers,source_url\n"
                   "2026-08,DEL,XXX,1,https://x\n")
    with pytest.raises(ImportErrorRow, match="unknown airport"):
        import_csv(session, bad)
    assert session.scalar(select(func.count()).select_from(TrafficStat)) == 3


def test_export_then_rebuild_reproduces_every_point(session, tmp_path):
    from aeropulse.pipeline.export import export
    from aeropulse.pipeline.rebuild import compare
    link_day = START + dt.timedelta(days=9)
    versions = [BasketVersion("b1", START, ("DEL-BOM", "BOM-DEL")),
                BasketVersion("b2", link_day, ROUTES)]
    collect_days(session, versions, 18)
    build(session, versions, "demo", replications=0)
    session.commit()
    manifest = export(session, tmp_path / "out")
    assert manifest["is_demo"] and all(f["sha256"] for f in manifest["files"])
    checked, bad = compare(tmp_path / "out")
    assert checked == 18 and bad == []


def test_run_status_counts(session):
    collect(session, DemoProvider(START), ["DEL-BOM"], START, max_calls_per_day=10)
    assert session.scalar(select(CollectionRun.status)) == "ok"
