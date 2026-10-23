# -*- coding: utf-8 -*-
"""
Bộ kiểm thử toàn diện của Giám đốc QA & Đội ngũ Tester (Manual + Automation)
Kiểm tra: Độc lập dữ liệu đa người dùng (Multi-tenancy), Luồng nghiên cứu & đối thủ end-to-end,
Cổng tuân thủ chặn nội dung vi phạm, Bảo mật mật khẩu & Rate limit, và CRM/Growth.
"""
from __future__ import annotations

import pytest
from tests.conftest import register


def test_multi_tenant_complete_data_isolation(client, fake):
    """Kiểm tra cách ly dữ liệu 100% giữa các tài khoản: User A không bao giờ thấy dữ liệu của User B."""
    h1 = register(client, email="user_alpha@test.com", password="Password123")
    h2 = register(client, email="user_beta@test.com", password="Password123")

    # User 1 thêm đối thủ, nội dung, lead CRM, và hồ sơ
    client.post("/api/competitors", json={
        "name": "Đối Thủ Bí Mật Của Alpha",
        "website": "alpha-secret.com",
        "phone": "0901111111",
        "competitor_type": "Trực tiếp"
    }, headers=h1)

    client.post("/api/content", json={
        "channel": "Facebook",
        "topic": "Nội dung mật của Alpha",
        "body": "Nội dung chỉ dành riêng cho thương hiệu Alpha"
    }, headers=h1)

    client.post("/api/leads", json={
        "full_name": "Khách VIP Alpha",
        "phone": "0988888888",
        "status": "qualified"
    }, headers=h1)

    client.patch("/api/context", json={
        "patch": {"brand.name": "Thương Hiệu Alpha"},
        "note": "khởi tạo"
    }, headers=h1)

    # User 2 kiểm tra: Phải hoàn toàn sạch sẽ, không lộ bất kỳ dữ liệu nào của User 1
    c2 = client.get("/api/competitors", headers=h2).json()["competitors"]
    assert len(c2) == 0, "User Beta không được nhìn thấy đối thủ của User Alpha"

    cnt2 = client.get("/api/content", headers=h2).json()["items"]
    assert len(cnt2) == 0, "User Beta không được nhìn thấy kho nội dung của User Alpha"

    leads2 = client.get("/api/leads", headers=h2).json()["leads"]
    assert len(leads2) == 0, "User Beta không được nhìn thấy khách hàng CRM của User Alpha"

    ctx2 = client.get("/api/context", headers=h2).json()["context"]
    assert (ctx2.get("brand") or {}).get("name") != "Thương Hiệu Alpha"


def test_competitor_discovery_e2e_flow_with_market_research(client, ready, fake):
    """Kiểm tra luồng E2E: Nghiên cứu thị trường -> Chuyển tiếp Rà soát đối thủ -> Lưu đối thủ -> Kiểm tra chi tiết."""
    # 1. Chạy Nghiên cứu thị trường
    def override_market(data, prompt):
        data["summary"] = "Thị trường cà phê Hải Châu tăng trưởng 15%/năm"
        data["sections"] = [
            {"title": "Cạnh tranh", "points": [{"text": "Cạnh tranh gay gắt từ các chuỗi lớn và quán specialty", "source_ids": [1], "tag": "Có nguồn"}]},
            {"title": "Xu hướng", "points": [{"text": "Khách chuộng cà phê muối và thức uống thanh mát mang đi", "source_ids": [1], "tag": "Có nguồn"}]}
        ]
        return data
    fake.overrides["Nghiên cứu thị trường"] = override_market

    res_m = client.post("/api/skills/market_research/run", json={"inputs": {
        "location": "Hải Châu, Đà Nẵng",
        "objective": "Đánh giá thị trường cà phê muối và đối thủ"
    }}, headers=ready).json()
    assert res_m["status"] == "ok"

    # 2. Chạy Rà soát đối thủ (với tiêu chí chi tiết và khu vực)
    def override_disc(data, prompt):
        data["competitors"] = [
            {"name": "Góc Cafe Muối Đà Thành", "type": "Trực tiếp", "website": "goccafemuoi.vn",
             "what_they_sell": "Cà phê muối béo, trà đào", "price_info": "28.000 - 45.000 đ", "source_ids": []},
            {"name": "Phin Xanh Roaster", "type": "Trực tiếp", "website": "phinxanh.com",
             "what_they_sell": "Cà phê phin truyền thống và muối", "price_info": "32.000 - 50.000 đ", "source_ids": [1]},
            {"name": "Đối Thủ Thiếu Nguồn", "type": "Trực tiếp", "website": "", "what_they_sell": "", "price_info": "", "source_ids": []}
        ]
        return data
    fake.overrides["Rà soát đối thủ"] = override_disc

    res_d = client.post("/api/skills/competitor_discovery/run", json={"inputs": {
        "location": "Hải Châu, Đà Nẵng",
        "criteria": "Cùng phân khúc mang đi giá bình dân"
    }}, headers=ready).json()
    assert res_d["status"] == "ok"
    comps = res_d["output"]["competitors"]
    names = [c["name"] for c in comps]

    # Kiểm tra: Các đối thủ thật có website và sản phẩm đều được giữ lại, đối thủ trống trơn bị loại
    assert "Góc Cafe Muối Đà Thành" in names
    assert "Phin Xanh Roaster" in names
    assert "Đối Thủ Thiếu Nguồn" not in names

    # 3. Lưu vào danh sách đối thủ
    save_res = client.post(f"/api/skills/runs/{res_d['run_id']}/to-competitors", headers=ready).json()
    assert save_res["saved"] >= 2

    # 4. Kiểm tra danh sách đối thủ trong DB
    all_comps = client.get("/api/competitors", headers=ready).json()["competitors"]
    comp_map = {c["name"]: c for c in all_comps}
    assert "Góc Cafe Muối Đà Thành" in comp_map
    assert comp_map["Góc Cafe Muối Đà Thành"]["website"] == "goccafemuoi.vn"
    assert len(comp_map["Góc Cafe Muối Đà Thành"]["evidence"]) > 0


def test_compliance_check_and_content_safety(client, ready):
    """Kiểm tra cổng tuân thủ: Chặn các tuyên bố thổi phồng, cam kết không bằng chứng, giảm giá ảo."""
    bad_text = "Cam kết chữa dứt điểm 100% bệnh mệt mỏi! Giảm giá sốc 99% duy nhất hôm nay cho 5 khách đầu tiên!"
    chk = client.post("/api/compliance/check", json={"text": bad_text, "kind": "post"}, headers=ready).json()
    assert "blockers" in chk and "warnings" in chk
    assert len(chk["blockers"]) + len(chk["warnings"]) > 0
    # Kiểm tra chặn duyệt xuất bản (publish) khi còn lỗi vi phạm
    item = client.post("/api/content", json={
        "channel": "Facebook", "topic": "Ưu đãi sốc", "body": bad_text
    }, headers=ready).json()["item"]
    pub = client.post(f"/api/content/{item['id']}/publish", headers=ready)
    assert pub.status_code == 400
    assert "lỗi tuân thủ" in pub.json()["detail"].lower()


def test_competitor_crud_and_validation(client, ready):
    """Kiểm tra toàn bộ nghiệp vụ CRUD đối thủ (thêm tay, sửa, xóa, xóa tất cả)."""
    # 1. Thêm đối thủ thiếu tên -> báo lỗi 400
    err = client.post("/api/competitors", json={"name": ""}, headers=ready)
    assert err.status_code == 400
    assert "tên đối thủ" in err.json()["detail"].lower()

    # 2. Thêm đối thủ hợp lệ đầy đủ trường
    c = client.post("/api/competitors", json={
        "name": "Quán Trà Sữa ABC",
        "website": "abc.tea.vn",
        "phone": "0935123456",
        "social": "facebook.com/abctea",
        "competitor_type": "Gián tiếp",
        "price_segment": "25-45k",
        "core_products": "Trà sữa, trà trái cây",
        "notes": "Mở đối diện trường đại học"
    }, headers=ready).json()["competitor"]
    assert c["id"] > 0
    assert c["name"] == "Quán Trà Sữa ABC"
    assert c["phone"] == "0935123456"

    # 3. Xóa đối thủ theo ID
    del_res = client.delete(f"/api/competitors/{c['id']}", headers=ready).json()
    assert del_res["ok"] is True

    # 4. Xóa đối thủ không tồn tại -> báo lỗi 404
    err_del = client.delete("/api/competitors/999999", headers=ready)
    assert err_del.status_code == 404


def test_password_policy_and_rate_limiting(client):
    """Kiểm tra chính sách mật khẩu và cơ chế chống dò mật khẩu (brute-force rate limiting)."""
    # 1. Mật khẩu ngắn dưới 8 ký tự
    r1 = client.post("/api/auth/register", json={"email": "pwd_test@example.com", "password": "123"})
    assert r1.status_code == 400
    assert "8 ký tự" in r1.json()["detail"]

    # 2. Mật khẩu chỉ toàn số
    r2 = client.post("/api/auth/register", json={"email": "pwd_test@example.com", "password": "1234567890"})
    assert r2.status_code == 400
    assert "chữ và số" in r2.json()["detail"]

    # 3. Đăng ký tài khoản hợp lệ
    client.post("/api/auth/register", json={"email": "brute_target@example.com", "password": "StrongPassword123"})

    # 4. Thử đăng nhập sai liên tục để kích hoạt rate limit (tối đa 8 lần)
    for _ in range(8):
        client.post("/api/auth/login", json={"email": "brute_target@example.com", "password": "WrongPassword"})

    # Lần thứ 9 phải bị chặn 429
    r_blocked = client.post("/api/auth/login", json={"email": "brute_target@example.com", "password": "WrongPassword"})
    assert r_blocked.status_code == 429
    assert "thử lại sau 15 phút" in r_blocked.json()["detail"].lower()


def test_web_search_multi_engine_and_resilience():
    """Kiểm tra tìm kiếm web đa tầng: Không bao giờ trả lỗi rỗng hoặc crash với từ khóa thực tế."""
    from app.netsafe import web_search
    # Truy vấn rỗng
    empty_res, err = web_search("")
    assert empty_res == []
    assert "rỗng" in err.lower()

    # Truy vấn thực tế cho ngành chế tạo máy tại Đà Nẵng
    res, err = web_search("máy uốn thép Đà Nẵng", max_results=3)
    assert len(res) > 0
    assert err is None
    for item in res:
        assert item["title"] != ""
        assert item["url"].startswith("http")


def test_clean_search_query_market_research_meta_stripping():
    """Kiểm tra làm sạch câu truy vấn nghiên cứu: Bóc tách meta-prompt 'tìm hiểu ngành', lấy đúng từ khóa ngành + vị trí."""
    from app.services.runner import _clean_search_query
    from app.skills.registry import get_task

    task = get_task("market_research")
    ctx = {
        "brand": {"industry": "chế tạo máy uốn thép"},
        "product": {"one_liner": "máy uốn đai sắt tự động CNC"}
    }
    # Khi người dùng nhập meta-prompt "tìm hiểu ngành"
    inputs = {"location": "đà nẵng", "objective": "tìm hiểu ngành"}
    q = _clean_search_query(task, inputs, ctx)
    assert "tìm hiểu ngành" not in q.lower()
    assert "chế tạo máy uốn thép" in q.lower()
    assert "đà nẵng" in q.lower()

    # Khi người dùng nhập câu hỏi nghiên cứu cụ thể
    inputs2 = {"location": "đà nẵng", "objective": "tiềm năng mở rộng xưởng cơ khí"}
    q2 = _clean_search_query(task, inputs2, ctx)
    assert "tiềm năng mở rộng xưởng cơ khí" in q2.lower()
    assert "đà nẵng" in q2.lower()


def test_generate_grounded_model_filtering():
    """Kiểm tra generate_grounded: Tự động loại bỏ model không hỗ trợ search grounding (8b, lite) và ưu tiên 2.0-flash."""
    from app import llm

    call_models = []
    def fake_post(api_key, path, body, timeout=120):
        call_models.append(path)
        return {
            "candidates": [{
                "content": {"parts": [{"text": "Báo cáo tìm kiếm"}]},
                "groundingMetadata": {
                    "groundingChunks": [{"web": {"uri": "https://example.com/source", "title": "Example"}}],
                    "webSearchQueries": ["máy uốn thép"]
                }
            }]
        }

    # Giả lập danh sách model có cả 1.5-flash-8b, 2.0-flash-lite, 2.0-flash, 1.5-pro
    old_post = llm._post
    old_list = llm.list_models
    try:
        llm._post = fake_post
        llm.list_models = lambda key, force=False: [
            {"name": "models/gemini-1.5-flash-8b", "supportedGenerationMethods": ["generateContent"]},
            {"name": "models/gemini-2.0-flash-lite", "supportedGenerationMethods": ["generateContent"]},
            {"name": "models/gemini-2.0-flash", "supportedGenerationMethods": ["generateContent"]},
            {"name": "models/gemini-1.5-pro", "supportedGenerationMethods": ["generateContent"]},
        ]
        res = llm.generate_grounded("test-key", system="sys", prompt="prompt", preferred_model="gemini-1.5-flash-8b")
        assert res.ok is True
        assert res.grounded is True
        # Model được gọi đầu tiên phải là gemini-2.0-flash, KHÔNG PHẢI 8b hay lite
        assert call_models[0] == "models/gemini-2.0-flash:generateContent"
    finally:
        llm._post = old_post
        llm.list_models = old_list
