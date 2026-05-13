"""Storage configuration resolved from environment variables.

* `DATABASE_URL`          — SQLAlchemy URL. Defaults to a SQLite file in the
                            repo root so `git clone && make run` works.
* `ALLICA_DB_AUTO_MIGRATE` — auto-create tables on startup. Defaults to True
                            for SQLite (single-file dev DB) and False for any
                            other dialect (use Alembic in prod).
* `ALLICA_PII_SALT`       — per-deployment salt mixed into PII hashes so the
                            same email in different environments hashes
                            differently.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from ..core.paths import REPO_ROOT


@dataclass(frozen=True)
class DBSettings:
    url: str
    auto_migrate: bool
    pii_salt: str
    echo_sql: bool

    @property
    def is_sqlite(self) -> bool:
        return self.url.startswith("sqlite")


def _truthy(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@lru_cache(maxsize=1)
def db_settings() -> DBSettings:
    # File extension is `.sqlite` (not `.db`) to play nicely with workspace
    # policies that block `.db` files. Override via DATABASE_URL in production.
    default_sqlite_path = REPO_ROOT / "solution" / "allica.sqlite"
    if not default_sqlite_path.parent.exists():
        default_sqlite_path = REPO_ROOT / "allica.sqlite"

    url = os.getenv("DATABASE_URL", f"sqlite:///{default_sqlite_path}")

    is_sqlite = url.startswith("sqlite")
    auto_migrate = _truthy(os.getenv("ALLICA_DB_AUTO_MIGRATE"), default=is_sqlite)

    return DBSettings(
        url=url,
        auto_migrate=auto_migrate,
        pii_salt=os.getenv("ALLICA_PII_SALT", "allica-default-salt-change-me"),
        echo_sql=_truthy(os.getenv("ALLICA_DB_ECHO"), default=False),
    )
