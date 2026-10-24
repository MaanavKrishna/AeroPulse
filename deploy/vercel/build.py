"""Vercel build step: create the read-only demo snapshot the hosted preview serves.

Runs after dependencies are installed (see [tool.vercel.scripts] in pyproject.toml). It
generates labelled synthetic history with the demo provider, strips raw provider payloads
to keep the bundle small, compacts the database and writes the open-data export. Nothing
here is real fare data, and every page says so.
"""
from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "deploy" / "vercel" / "snapshot"
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    SNAPSHOT.mkdir(parents=True, exist_ok=True)
    db = SNAPSHOT / "aeropulse.db"
    for leftover in SNAPSHOT.glob("aeropulse.db*"):
        leftover.unlink()
    os.environ.update({"AEROPULSE_ENV": "development", "AEROPULSE_PROVIDERS": "demo",
                       "AEROPULSE_DATABASE_URL": f"sqlite:///{db}",
                       "AEROPULSE_EXPORT_DIR": str(SNAPSHOT / "exports")})
    from aeropulse.cli import main as cli
    days = os.environ.get("AEROPULSE_SNAPSHOT_DAYS", "120")
    if cli(["demo", "--days", days, "--replications", "100"]) != 0:
        return 1
    if cli(["export", "--out", str(SNAPSHOT / "exports")]) != 0:
        return 1
    from aeropulse.db.session import get_engine
    get_engine().dispose()
    con = sqlite3.connect(db)
    con.execute("UPDATE raw_responses SET payload = NULL")
    con.execute("PRAGMA journal_mode=DELETE")
    con.commit()
    con.execute("VACUUM")
    con.close()
    print(f"snapshot ready: {db.stat().st_size / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
