# -*- coding: utf-8 -*-
"""Hạ tầng test: mỗi test có DB riêng trong thư mục tạm, không gọi mạng thật."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DATA_DIR", str(ROOT / "data" / "runtime-test"))

import pytest
from tests.fake_gemini import FakeGemini

FULL_CONTEXT = {
    "brand.name": "Phê Ly", "brand.industry": "Quán cà phê take-away", "product.one_liner": "Cà phê muối mang đi trong 3 phút",
    "product.price_points": [{"name": "Cà phê muối", "price_vnd": 29000}, {"name": "Bạc xỉu", "price_vnd": 25000}],
    "unit_economics.avg_order_value_vnd": 45000, "unit_economics.gross_margin_pct": 60,
    "customers.buyer": "Dân văn phòng quanh Nguyễn Phước Lan", "customers.jtbd": ["Tỉnh táo ca chiều"],
    "problem.core": "Muốn cà phê ngon mà không phải ngồi lâu", "differentiation.only_we_have": "Muối tự làm từ kem phô mai",
    "goals.business_goal": "Tăng từ 80 lên 150 ly/ngày trước 31/03/2027", "goals.primary_conversion": "Đặt món qua Zalo",
    "channels_active": ["Facebook", "TikTok", "Zalo OA"], "market.location": "Hải Châu, Đà Nẵng",
    "competitors.direct": ["Quán ABC"], "brand.address": "12 Nguyễn Phước Lan, Đà Nẵng", "brand.hotline": "0905000000",
}


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


@pytest.fixture
def fake(monkeypatch):
    return FakeGemini().install(monkeypatch)


@pytest.fixture
def ready(client, fake):
    h = register(client)
    assert client.patch("/api/context", json={"patch": FULL_CONTEXT, "note": "test"}, headers=h).status_code == 200
    assert client.post("/api/settings/ai", json={"api_key": "AIzaSy" + "t" * 33}, headers=h).status_code == 200
    return h
