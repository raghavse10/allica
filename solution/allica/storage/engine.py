"""Sync engine, session factory, FastAPI session dependency (no async ORM)."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .config import db_settings


log = logging.getLogger(__name__)

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _build_engine() -> Engine:
    settings = db_settings()
    connect_args: dict = {}
    if settings.is_sqlite:
        # `check_same_thread=False` lets the request thread pool share the
        # connection. We still serialise writes via SQLAlchemy's session.
        connect_args["check_same_thread"] = False

    engine = create_engine(
        settings.url,
        echo=settings.echo_sql,
        future=True,
        pool_pre_ping=True,
        connect_args=connect_args,
    )

    if settings.is_sqlite:
        # Foreign keys are off by default in SQLite — we want them ON so
        # cascade deletes and FK constraints actually behave as declared.
        @event.listens_for(engine, "connect")
        def _enable_sqlite_fks(dbapi_conn, _conn_record):  # type: ignore[no-untyped-def]
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def get_engine() -> Engine:
    global _engine, _SessionLocal
    if _engine is None:
        _engine = _build_engine()
        _SessionLocal = sessionmaker(
            bind=_engine, autoflush=False, autocommit=False, future=True
        )
    return _engine


def init_db() -> None:
    """Initialise the DB.

    For SQLite (or whenever ALLICA_DB_AUTO_MIGRATE=true): creates tables
    via SQLAlchemy metadata. For Postgres in prod, run Alembic instead and
    leave ALLICA_DB_AUTO_MIGRATE=false — this function will then just verify
    connectivity.
    """
    from . import models  # noqa: F401 — register models on Base

    engine = get_engine()
    settings = db_settings()
    if settings.auto_migrate:
        from .models import Base

        Base.metadata.create_all(engine)
        log.info("storage_initialised mode=auto_migrate url=%s", _redact_url(settings.url))
    else:
        with engine.connect() as conn:
            conn.execute(_select_one(settings.url))
        log.info("storage_initialised mode=connectivity_check url=%s", _redact_url(settings.url))


def _select_one(url: str):
    from sqlalchemy import text
    return text("SELECT 1")


def _redact_url(url: str) -> str:
    """Strip password from a SQLAlchemy URL for logging."""
    if "@" not in url:
        return url
    scheme_creds, _, host = url.partition("@")
    scheme, _, _creds = scheme_creds.rpartition("//")
    return f"{scheme}//***@{host}"


@contextmanager
def session_scope() -> Iterator[Session]:
    """Transactional unit of work.

    Commits on success, rolls back on any exception, and always closes the
    session. Use this from CLI / scripts / services. For FastAPI handlers,
    prefer `get_session` so the session participates in dependency injection.
    """
    if _SessionLocal is None:
        get_engine()
    assert _SessionLocal is not None
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session() -> Iterator[Session]:
    """FastAPI dependency that yields a transactional session."""
    if _SessionLocal is None:
        get_engine()
    assert _SessionLocal is not None
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
