"""Shared test setup. Every test session builds its own small demo database in a temp
directory; nothing touches the developer's aeropulse.db or the network."""
from __future__ import annotations

import datetime as dt
import os
from pathlib import Path

import pytest

DEMO_END = dt.date(2026, 10, 24)
DEMO_DAYS = 45
FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session", autouse=True)
def _environment(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("aeropulse")
    os.environ.update({
        "AEROPULSE_ENV": "test",
        "AEROPULSE_DATABASE_URL": f"sqlite:///{tmp / 'test.db'}",
        "AEROPULSE_EXPORT_DIR": str(tmp / "exports"),
        "AEROPULSE_PROVIDERS": "demo",
        "AEROPULSE_RATE_LIMIT": "100000",
        "AEROPULSE_SITE_URL": "https://aeropulse.test",
    })
    for key in ("AEROPULSE_ADMIN_TOKEN", "AEROPULSE_IGNAV_API_KEY"):
        os.environ.pop(key, None)
    from aeropulse.config import get_settings
    get_settings.cache_clear()
    yield tmp


@pytest.fixture(scope="session")
def demo_db(_environment):
    """A 45-day demo history, built once per session."""
    from aeropulse.cli import main
    assert main(["demo", "--days", str(DEMO_DAYS), "--end", DEMO_END.isoformat(),
                 "--replications", "30"]) == 0
    return _environment


@pytest.fixture
def fixture_text():
    return lambda name: (FIXTURES / name).read_text("utf-8")
