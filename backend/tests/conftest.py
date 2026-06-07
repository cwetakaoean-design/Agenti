"""Pytest fixtures: hermetic app with stub LLM and a temp SQLite DB."""
from __future__ import annotations

import importlib
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    monkeypatch.setenv("USE_STUB_LLM", "true")
    monkeypatch.setenv("GIGACHAT_AUTH_KEY", "")

    # Reload modules so they pick up the patched env and fresh engine.
    import app.config as config

    config.get_settings.cache_clear()
    import app.db as db

    importlib.reload(db)
    import app.main as main

    importlib.reload(main)

    with TestClient(main.app) as c:
        yield c

    config.get_settings.cache_clear()
