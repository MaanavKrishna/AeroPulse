from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from ..config import get_settings
from .models import Base


@lru_cache
def engine_for(url: str) -> Engine:
    kwargs = {"future": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    engine = create_engine(url, **kwargs)
    if url.startswith("sqlite"):
        # A read-only snapshot (mode=ro) cannot switch journal mode; it needs no WAL anyway.
        read_only = "mode=ro" in url

        @event.listens_for(engine, "connect")
        def _pragmas(conn, _):                       # noqa: ANN001
            cur = conn.cursor()
            cur.execute("PRAGMA foreign_keys=ON")
            if not read_only:
                cur.execute("PRAGMA journal_mode=WAL")
            cur.close()
    return engine


def get_engine() -> Engine:
    return engine_for(get_settings().database_url)


def init_db(engine: Engine | None = None) -> None:
    """Create tables directly. Used by tests and the demo; production uses Alembic."""
    Base.metadata.create_all(engine or get_engine())


@contextmanager
def session_scope(engine: Engine | None = None) -> Iterator[Session]:
    factory = sessionmaker(bind=engine or get_engine(), expire_on_commit=False)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
