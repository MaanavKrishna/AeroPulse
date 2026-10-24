"""Vercel entrypoint: serves the read-only demo snapshot made by deploy/vercel/build.py.

This is a hosted preview of the site, not the production collector. It opens the snapshot
read-only, collects nothing, and shows the demo banner on every page. For a real deployment
with live collection, use deploy/compose.yaml (see docs/operations/self-hosting.md).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "deploy" / "vercel" / "snapshot"
sys.path.insert(0, str(ROOT / "src"))

os.environ.setdefault("AEROPULSE_ENV", "production")
os.environ.setdefault("AEROPULSE_PROVIDERS", "ignav")       # nothing is collected here
os.environ.setdefault("AEROPULSE_DATABASE_URL",
                      f"sqlite:///file:{SNAPSHOT / 'aeropulse.db'}?mode=ro&immutable=1&uri=true")
os.environ.setdefault("AEROPULSE_EXPORT_DIR", str(SNAPSHOT / "exports"))
if "AEROPULSE_SITE_URL" not in os.environ and os.environ.get("VERCEL_PROJECT_PRODUCTION_URL"):
    os.environ["AEROPULSE_SITE_URL"] = f"https://{os.environ['VERCEL_PROJECT_PRODUCTION_URL']}"

from aeropulse.app import app  # noqa: E402

__all__ = ["app"]
