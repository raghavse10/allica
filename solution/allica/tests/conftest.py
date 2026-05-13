"""API test client fixture: temp SQLite DB, reset engine cache, run lifespan."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path):
    db_path = tmp_path / "allica_test.sqlite"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["ALLICA_DB_AUTO_MIGRATE"] = "true"

    # Reset module state between tests so each gets a fresh engine.
    from allica.storage import config, engine

    config.db_settings.cache_clear()
    engine._engine = None  # type: ignore[attr-defined]
    engine._SessionLocal = None  # type: ignore[attr-defined]

    from allica.api.app import app

    with TestClient(app) as test_client:
        yield test_client
