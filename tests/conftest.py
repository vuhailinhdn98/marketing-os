# -*- coding: utf-8 -*-
"""Hạ tầng test: mỗi test có DB riêng trong thư mục tạm, không gọi mạng thật."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DATA_DIR", str(ROOT / "data" / "runtime-test"))


@pytest.fixture(autouse=True)
def fresh_env(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    for key in ("ADMIN_EMAILS", "GEMINI_API_KEY", "SHARE_SERVER_GEMINI_KEY", "GOOGLE_CLIENT_ID", "ALLOW_REGISTRATION", "RENDER"):
        monkeypatch.delenv(key, raising=False)
    from app import config, database, llm, security
    # Không chép DB cũ của repo vào DB test
    monkeypatch.setattr(config.Settings, "legacy_db_path", property(lambda self: tmp_path / "khong-co-db-cu.db"))
    config.reload_settings()
    database.reset_for_tests()
    security.reset_rate_limits()
    llm.clear_model_cache()
    yield
    database.reset_for_tests()


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as c:
        yield c


def register(client, email="owner@example.com", password="Matkhau123", name=""):
    res = client.post("/api/auth/register", json={"email": email, "password": password, "name": name})
    assert res.status_code == 200, res.text
    token = res.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth(client):
    return register(client)
