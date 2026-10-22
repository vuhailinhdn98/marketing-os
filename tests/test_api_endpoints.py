import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.abspath("."))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api_endpoints():
    print("==================================================")
    print("🌐 KIỂM THỬ FASTAPI ENDPOINTS & MULTI-TENANCY")
    print("==================================================")

    # 1. Root / UI
    res = client.get("/")
    assert res.status_code == 200
    assert "MARKETING OS" in res.text
    print("✅ 1. Giao diện Web (Root /) load thành công 200 OK.")

    # 2. Login User 1 (user1@test.com)
    res_auth1 = client.post("/api/auth/google", json={"email": "user1@test.com", "name": "User 1"})
    assert res_auth1.status_code == 200
    token1 = res_auth1.json()["token"]
    headers1 = {"Authorization": f"Bearer {token1}"}
    print("✅ 2. Đăng nhập User 1 thành công, nhận Bearer token.")

    # 3. Login User 2 (user2@test.com)
    res_auth2 = client.post("/api/auth/google", json={"email": "user2@test.com", "name": "User 2"})
    assert res_auth2.status_code == 200
    token2 = res_auth2.json()["token"]
    headers2 = {"Authorization": f"Bearer {token2}"}
    print("✅ 3. Đăng nhập User 2 thành công, nhận Bearer token.")

    # 4. Save Profile with mocked background task
    with patch("app.main.run_full_autopilot_pipeline") as mock_pipeline:
        prof1_payload = {
            "brand_name": "Nhà Hàng A",
            "industry": "F&B",
            "market_scope": "Đà Nẵng",
            "market_level": "province",
            "market_location": "Đà Nẵng",
            "phone_hotline": "0911222333"
        }
        res_p1 = client.post("/api/profile", json=prof1_payload, headers=headers1)
        assert res_p1.status_code == 200

        prof2_payload = {
            "brand_name": "Phần Mềm B",
            "industry": "Công nghệ",
            "market_scope": "TP. Hồ Chí Minh",
            "market_level": "province",
            "market_location": "Hồ Chí Minh",
            "phone_hotline": "0988777666"
        }
        res_p2 = client.post("/api/profile", json=prof2_payload, headers=headers2)
        assert res_p2.status_code == 200

    # 6. Verify User 1 sees ONLY Nhà Hàng A
    get_p1 = client.get("/api/profile", headers=headers1).json()
    assert get_p1["brand_name"] == "Nhà Hàng A"
    assert get_p1["phone_hotline"] == "0911222333"

    # 7. Verify User 2 sees ONLY Phần Mềm B
    get_p2 = client.get("/api/profile", headers=headers2).json()
    assert get_p2["brand_name"] == "Phần Mềm B"
    assert get_p2["phone_hotline"] == "0988777666"
    print("✅ 4. Cách ly dữ liệu Endpoint /api/profile giữa 2 user qua token 100% chính xác.")

    # 8. Check Google Sheets Admin endpoints
    res_users = client.get("/api/admin/users")
    assert res_users.status_code == 200
    data_users = res_users.json()
    assert data_users["status"] == "success"
    emails = [u["email"] for u in data_users["users"]]
    assert "user1@test.com" in emails and "user2@test.com" in emails
    print("✅ 5. /api/admin/users hiển thị đúng và đủ danh sách các tài khoản.")

    # 9. Check CSV export endpoint
    res_csv = client.get("/api/admin/users/export-sheets")
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers.get("content-type", "")
    assert "user1@test.com" in res_csv.text and "user2@test.com" in res_csv.text
    print("✅ 6. /api/admin/users/export-sheets xuất file CSV chuẩn.")

    # 10. Check Sheets config endpoint
    res_cfg = client.post("/api/admin/sheets/config", json={"webhook_url": "https://script.google.com/test"})
    assert res_cfg.status_code == 200
    res_get_cfg = client.get("/api/admin/sheets/config").json()
    assert res_get_cfg["webhook_url"] == "https://script.google.com/test"
    assert res_get_cfg["is_connected"] is True
    print("✅ 7. /api/admin/sheets/config lưu và phản hồi trạng thái kết nối Webhook chính xác.")

    print("\n==================================================")
    print("🎉 TẤT CẢ ENDPOINT API ĐÃ PASS KIỂM THỬ 100%!")
    print("==================================================")

if __name__ == "__main__":
    test_api_endpoints()
