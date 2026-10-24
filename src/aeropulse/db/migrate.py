"""Alembic, driven from Python so `aeropulse db upgrade` needs no alembic.ini."""
from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

from ..config import get_settings

MIGRATIONS = Path(__file__).resolve().parent / "migrations"


def config(url: str | None = None) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS))
    cfg.set_main_option("sqlalchemy.url", (url or get_settings().database_url).replace("%", "%%"))
    return cfg


def upgrade(url: str | None = None, revision: str = "head") -> None:
    command.upgrade(config(url), revision)


def autogenerate(message: str, url: str | None = None) -> None:
    command.revision(config(url), message=message, autogenerate=True)
