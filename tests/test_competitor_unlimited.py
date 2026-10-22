import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.abspath("."))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from starlette.testclient import TestClient
from app.main import app
from app.database import (
    init_app_db, get_discovered_competitors,
    save_discovered_competitors, clear_all_competitors,
    create_or_update_user, create_session
)
from app.ai_engine import auto_discover_competitors

client = TestClient(app)

def test_unlimited_competitors():
    print("==================================================")
    print("🎯 KIỂM THỬ KHÔNG GIỚI HẠN ĐỐI THỦ CẠNH TRANH")
    print("==================================================")

    init_app_db()
    test_email = "tester@unlimited-comps.vn"
    create_or_update_user(test_email, "Test User")
    token = create_session(test_email)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Test auto_discover_competitors with realistic profile
    sample_profile = {
        "brand_name": "Cơ Khí Nam Phát",
        "industry": "Cơ khí xây dựng",
        "products_services": "Máy bẻ đai sắt tự động, máy uốn sắt xây dựng",
        "price_range": "Tiêu chuẩn",
        "market_location": "Đà Nẵng",
        "market_scope_type": "province",
        "target_audience": "Nhà thầu xây dựng dân dụng & công nghiệp",
        "usp_advantages": "Máy bẻ đai lập trình cảm ứng tiếng Việt, bảo hành tận chân công trình trong 24h",
        "competitors": "Cơ Khí Đại Lộc, Máy Xây Dựng Tiến Phát"
    }

    print("\n🔍 1. Chạy rà soát đối thủ tự động...")
    comps = auto_discover_competitors(sample_profile)
    print(f"📊 Số lượng đối thủ được phát hiện: {len(comps)} bên.")

    # Phải vượt xa giới hạn 4 bên cũ (tối thiểu >= 10 bên)
    assert len(comps) >= 10, f"Số lượng đối thủ chỉ có {len(comps)}, chưa đạt yêu cầu >= 10 bên!"
    print("✅ Đã vượt qua kiểm tra số lượng: Liệt kê đầy đủ", len(comps), "đối thủ (không còn bị giới hạn 4 bên).")

    # Kiểm tra các đối thủ do user cung cấp có nằm trong danh sách không
    comp_names = [c["name"] for c in comps]
    assert any("Đại Lộc" in n for n in comp_names), "Đối thủ do người dùng nhập 'Cơ Khí Đại Lộc' bị thiếu!"
    assert any("Tiến Phát" in n for n in comp_names), "Đối thủ do người dùng nhập 'Máy Xây Dựng Tiến Phát' bị thiếu!"
    print("✅ Đã giữ lại và làm giàu thông tin cho toàn bộ đối thủ do chủ doanh nghiệp cung cấp.")

    # 2. Test lưu trữ toàn bộ đối thủ vào cơ sở dữ liệu
    save_discovered_competitors(comps, market_context="Đà Nẵng", user_email=test_email)
    db_comps = get_discovered_competitors(user_email=test_email)
    assert len(db_comps) == len(comps), f"DB chỉ lưu {len(db_comps)} / {len(comps)} đối thủ!"
    print(f"✅ Đã lưu toàn bộ {len(db_comps)} đối thủ vào cơ sở dữ liệu multi-tenant của {test_email}.")

    # 3. Test API GET /api/competitors/discovered
    res = client.get("/api/competitors/discovered", headers=headers)
    assert res.status_code == 200
    res_data = res.json()
    assert len(res_data["competitors"]) == len(comps)
    print(f"✅ API /api/competitors/discovered trả về đầy đủ {len(res_data['competitors'])} đối thủ.")

    # 4. Test API DELETE /api/competitors/all
    res_del = client.delete("/api/competitors/all", headers=headers)
    assert res_del.status_code == 200
    after_del = get_discovered_competitors(user_email=test_email)
    assert len(after_del) == 0
    print("✅ API DELETE /api/competitors/all xóa sạch danh sách thành công khi cần làm mới.")

    print("\n==================================================")
    print("🎉 TẤT CẢ KIỂM THỬ KHÔNG GIỚI HẠN ĐỐI THỦ ĐÃ PASS 100%!")
    print("==================================================")

if __name__ == "__main__":
    test_unlimited_competitors()
