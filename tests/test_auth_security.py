# -*- coding: utf-8 -*-
"""Đợt 0: xác thực, phân quyền, cô lập workspace, ẩn API key, nhận lead an toàn."""
from tests.conftest import register


def test_api_requires_token(client):
    assert client.get("/api/context").status_code == 401
    assert client.get("/api/leads").status_code == 401


def test_x_user_email_header_is_ignored(client, auth):
    client.post("/api/settings/ai", json={"api_key": "AIzaSy" + "x" * 33}, headers=auth)
    res = client.get("/api/settings/ai", headers={"X-User-Email": "owner@example.com"})
    assert res.status_code == 401


def test_api_key_never_returned(client, auth):
    key = "AIzaSy" + "k" * 33
    res = client.post("/api/settings/ai", json={"api_key": key}, headers=auth)
    assert res.status_code == 200
    body = client.get("/api/settings/ai", headers=auth).json()
    assert body["has_key"] is True
    assert key not in str(body)
    assert body["key_hint"] == "…kkkk"
    assert key not in client.get("/api/workspace/export", headers=auth).text


def test_password_rules_and_login(client):
    bad = client.post("/api/auth/register", json={"email": "a@b.co", "password": "12345678"})
    assert bad.status_code == 400
    register(client, "a@b.co", "Abcdef123")
    dup = client.post("/api/auth/register", json={"email": "a@b.co", "password": "Abcdef123"})
    assert dup.status_code == 409
    wrong = client.post("/api/auth/login", json={"email": "a@b.co", "password": "sai-mat-khau1"})
    assert wrong.status_code == 401
    ok = client.post("/api/auth/login", json={"email": "A@B.co", "password": "Abcdef123"})
    assert ok.status_code == 200 and ok.json()["user"]["email"] == "a@b.co"


def test_login_rate_limited(client):
    register(client, "rl@example.com", "Abcdef123")
    for _ in range(8):
        client.post("/api/auth/login", json={"email": "rl@example.com", "password": "sai12345"})
    res = client.post("/api/auth/login", json={"email": "rl@example.com", "password": "Abcdef123"})
    assert res.status_code == 429


def test_first_user_admin_others_not(client):
    a = register(client, "first@example.com")
    b = register(client, "second@example.com")
    assert client.get("/api/admin/users", headers=a).status_code == 200
    assert client.get("/api/admin/users", headers=b).status_code == 403


def test_admin_emails_env(client, monkeypatch):
    from app import config
    monkeypatch.setenv("ADMIN_EMAILS", "boss@example.com")
    config.reload_settings()
    a = register(client, "first@example.com")
    boss = register(client, "boss@example.com")
    assert client.get("/api/admin/users", headers=a).status_code == 403
    assert client.get("/api/admin/users", headers=boss).status_code == 200


def test_workspace_isolation(client):
    a = register(client, "a@example.com")
    b = register(client, "b@example.com")
    lead = client.post("/api/leads", json={"full_name": "Khách A", "phone": "0901234567"}, headers=a).json()["lead"]
    assert client.get("/api/leads", headers=b).json()["count"] == 0
    assert client.patch(f"/api/leads/{lead['id']}/status", json={"status": "won"}, headers=b).status_code == 400
    assert client.delete(f"/api/leads/{lead['id']}", headers=b).status_code == 404


def test_ingest_uses_secret_not_body(client):
    a = register(client, "a@example.com")
    b = register(client, "b@example.com")
    path = client.get("/api/settings/ingest", headers=a).json()["path"]
    res = client.post(path, json={"full_name": "Form Lead", "phone": "0900000001", "user_email": "b@example.com"})
    assert res.status_code == 200
    assert client.get("/api/leads", headers=a).json()["count"] == 1
    assert client.get("/api/leads", headers=b).json()["count"] == 0
    assert client.post("/api/leads/ingest/khong-dung-ma-bi-mat-123", json={"full_name": "X", "phone": "1"}).status_code == 404
    assert client.post("/api/leads/webhook-ingest", json={"full_name": "X"}).status_code in (404, 405)


def test_ingest_consent_requires_text(client):
    a = register(client)
    path = client.get("/api/settings/ingest", headers=a).json()["path"]
    res = client.post(path, json={"full_name": "K", "phone": "0901", "consent_marketing": True})
    assert res.status_code == 400
    res = client.post(path, json={"full_name": "K", "phone": "0901", "consent_marketing": True,
                                  "consent_text": "Tôi đồng ý nhận ưu đãi qua Zalo"})
    assert res.status_code == 200
    lead = client.get("/api/leads", headers=a).json()["leads"][0]
    assert lead["consent_marketing"] == 1 and lead["consent_text"]


def test_rotating_ingest_secret_invalidates_old(client):
    a = register(client)
    old = client.get("/api/settings/ingest", headers=a).json()["path"]
    new = client.post("/api/settings/ingest/rotate", headers=a).json()["path"]
    assert old != new
    assert client.post(old, json={"full_name": "X", "phone": "1"}).status_code == 404


def test_logout_and_password_change(client):
    h = register(client, "p@example.com", "Abcdef123")
    wrong = client.post("/api/auth/password", json={"old_password": "sai-roi-123", "new_password": "Moi12345x"}, headers=h)
    assert wrong.status_code == 400  # không trả 401 để giao diện không tự đăng xuất
    assert client.get("/api/auth/me", headers=h).status_code == 200
    res = client.post("/api/auth/password", json={"old_password": "Abcdef123", "new_password": "Moi12345x"}, headers=h)
    assert res.status_code == 200
    assert client.get("/api/auth/me", headers=h).status_code == 401
    ok = client.post("/api/auth/login", json={"email": "p@example.com", "password": "Moi12345x"})
    assert ok.status_code == 200
    h2 = {"Authorization": "Bearer " + ok.json()["token"]}
    client.post("/api/auth/logout", headers=h2)
    assert client.get("/api/auth/me", headers=h2).status_code == 401


def test_google_login_disabled_without_client_id(client):
    res = client.post("/api/auth/google", json={"credential": "abc"})
    assert res.status_code == 400


def test_legacy_db_copied_not_moved(tmp_path, monkeypatch):
    import shutil
    import sqlite3
    from app import config, database
    legacy = tmp_path / "legacy.db"
    conn = sqlite3.connect(legacy)
    conn.execute("CREATE TABLE app_users (email TEXT PRIMARY KEY, name TEXT)")
    conn.execute("INSERT INTO app_users VALUES ('old@example.com', 'Old')")
    conn.commit()
    conn.close()
    monkeypatch.setattr(config.Settings, "legacy_db_path", property(lambda self: legacy))
    database.reset_for_tests()
    database.ensure_db()
    assert legacy.exists()
    assert database.one("SELECT email FROM app_users")["email"] == "old@example.com"
    shutil.rmtree(tmp_path / "data", ignore_errors=True)


def test_security_headers(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "Content-Security-Policy" in res.headers
    assert res.headers["X-Frame-Options"] == "DENY"


def test_static_zip_removed(client):
    assert client.get("/static/marketing_os.zip").status_code == 404


def test_ssrf_blocked():
    import pytest
    from app.netsafe import FetchError, safe_fetch
    for url in ("http://127.0.0.1:8000/", "http://169.254.169.254/latest/meta-data", "http://localhost/", "file:///etc/passwd",
                "http://10.0.0.1/"):
        with pytest.raises(FetchError):
            safe_fetch(url)


def test_webhook_url_must_be_public_https(client, auth):
    assert client.post("/api/settings/webhook", json={"content_webhook_url": "http://example.com/hook"}, headers=auth).status_code == 400
    assert client.post("/api/settings/webhook", json={"content_webhook_url": "https://127.0.0.1/hook"}, headers=auth).status_code == 400


def test_rate_limit_per_email_across_ips():
    from app import security
    security.reset_rate_limits()
    for i in range(security.MAX_FAILS_PER_EMAIL):
        security.record_failure("victim@example.com", f"10.0.0.{i}")
    import pytest
    with pytest.raises(security.AuthError) as exc:
        security.check_rate_limit("victim@example.com", "10.9.9.9")
    assert exc.value.status == 429
    security.check_rate_limit("other@example.com", "10.9.9.9")  # email khác không bị ảnh hưởng
    security.reset_rate_limits()


def test_ingest_total_limit(client, auth):
    from app.routers import leads as leads_router
    path = client.get("/api/settings/ingest", headers=auth).json()["path"]
    secret = path.rsplit("/", 1)[1]
    leads_router._ingest_hits.clear()
    for i in range(leads_router.INGEST_LIMIT_TOTAL):
        assert leads_router._ingest_allowed(secret, f"10.1.{i // 250}.{i % 250}")
    assert leads_router._ingest_allowed(secret, "10.200.0.1") is False
    leads_router._ingest_hits.clear()


def test_head_and_static_cache_headers(client):
    assert client.head("/").status_code == 200
    assert client.head("/healthz").status_code == 200
    r = client.get("/static/js/core.js")
    assert r.status_code == 200 and r.headers["cache-control"] == "no-cache" and "Content-Security-Policy" in r.headers
