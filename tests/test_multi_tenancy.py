import sys
import os
import sqlite3
import json

# Ensure repo root is on sys.path
sys.path.insert(0, os.path.abspath("."))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.database import (
    init_app_db,
    update_profile,
    get_profile,
    add_or_update_competitor,
    get_discovered_competitors,
    save_content_package,
    get_content_items,
    get_all_users,
    export_users_csv,
    set_app_config,
    get_app_config,
    create_or_update_user,
    create_session,
    verify_session
)

def run_tests():
    print("==================================================")
    print("🚀 BẮT ĐẦU KIỂM THỬ TỰ ĐỘNG MARKETING OS")
    print("==================================================")

    # 1. Initialize DB
    init_app_db()
    print("✅ 1. Khởi tạo Database thành công.")

    # 2. Test Multi-tenancy Isolation
    user_a = "ceo@congty-a.vn"
    user_b = "founder@startup-b.com"

    # User A registers & logs in
    info_a = create_or_update_user(user_a, "Nguyễn Văn A", "https://avatar-a.png", "1.1.1.1", "Mozilla iPhone")
    token_a = create_session(user_a)
    sess_a = verify_session(token_a)
    assert sess_a["email"] == user_a

    # User B registers & logs in
    info_b = create_or_update_user(user_b, "Trần Thị B", "https://avatar-b.png", "2.2.2.2", "Mozilla Android")
    token_b = create_session(user_b)
    sess_b = verify_session(token_b)
    assert sess_b["email"] == user_b

    print(f"✅ 2. Đăng ký & lưu trữ User A ({user_a}) và User B ({user_b}) thành công.")

    # Update Profile for User A
    update_profile({
        "brand_name": "Công ty Cà Phê A",
        "industry": "F&B",
        "target_audience": "Giới trẻ văn phòng",
        "market_scope": "Hà Nội",
        "market_level": "province",
        "market_location": "Hà Nội",
        "phone_hotline": "0901234567",
        "website": "https://caphea.vn",
        "product_advantages": "Cà phê mộc 100% Arabica Cầu Đất"
    }, user_email=user_a)

    # Update Profile for User B
    update_profile({
        "brand_name": "Công ty Công Nghệ B",
        "industry": "SaaS / AI",
        "target_audience": "Doanh nghiệp SMB",
        "market_scope": "Toàn quốc",
        "market_level": "country",
        "market_location": "Việt Nam",
        "phone_hotline": "0987654321",
        "website": "https://techb.ai",
        "product_advantages": "Giải pháp AI tự động hóa chăm sóc khách hàng"
    }, user_email=user_b)

    prof_a = get_profile(user_email=user_a)
    prof_b = get_profile(user_email=user_b)

    assert prof_a["brand_name"] == "Công ty Cà Phê A", f"Expected 'Công ty Cà Phê A', got {prof_a['brand_name']}"
    assert prof_b["brand_name"] == "Công ty Công Nghệ B", f"Expected 'Công ty Công Nghệ B', got {prof_b['brand_name']}"
    assert prof_a["phone_hotline"] == "0901234567"
    assert prof_b["phone_hotline"] == "0987654321"
    assert prof_a["market_location"] == "Hà Nội"
    assert prof_b["market_location"] == "Việt Nam"
    print("✅ 3. Hồ sơ doanh nghiệp tách biệt hoàn toàn giữa User A và User B (100% Multi-tenant).")

    # Competitor Isolation
    add_or_update_competitor({
        "name": "Highlands Coffee",
        "website": "highlands.com.vn",
        "status": "active"
    }, user_email=user_a)

    add_or_update_competitor({
        "name": "Base.vn SaaS",
        "website": "base.vn",
        "status": "active"
    }, user_email=user_b)

    comps_a = get_discovered_competitors(user_email=user_a)
    comps_b = get_discovered_competitors(user_email=user_b)

    assert len(comps_a) == 1 and comps_a[0]["name"] == "Highlands Coffee"
    assert len(comps_b) == 1 and comps_b[0]["name"] == "Base.vn SaaS"
    print("✅ 4. Tình báo Đối thủ cô lập riêng biệt theo tài khoản Gmail (Không bị trùng lặp).")

    # Content Package Isolation
    save_content_package(
        channel="Facebook",
        topic="Cà phê mộc tinh tế",
        body="Nội dung cho cà phê A",
        cta="Đặt mua ngay",
        user_email=user_a
    )

    save_content_package(
        channel="LinkedIn",
        topic="Chuyển đổi số doanh nghiệp",
        body="Nội dung cho AI Tech B",
        cta="Dùng thử miễn phí",
        user_email=user_b
    )

    contents_a = get_content_items(user_email=user_a)
    contents_b = get_content_items(user_email=user_b)

    assert len(contents_a) >= 1 and contents_a[0]["topic"] == "Cà phê mộc tinh tế"
    assert len(contents_b) >= 1 and contents_b[0]["topic"] == "Chuyển đổi số doanh nghiệp"
    print("✅ 5. Xưởng nội dung & Lịch trình hoàn toàn độc lập cho từng người dùng.")

    # 6. Test Google Sheets Management & CSV Export
    users = get_all_users()
    assert len(users) >= 2
    emails = [u["email"] for u in users]
    assert user_a in emails and user_b in emails
    print(f"✅ 6. Quản lý danh sách tài khoản: Đã tìm thấy {len(users)} người dùng.")

    csv_data = export_users_csv()
    assert "\ufeff" in csv_data  # Check UTF-8 BOM
    assert user_a in csv_data and user_b in csv_data
    assert "Công ty Cà Phê A" in csv_data
    print("✅ 7. Xuất file CSV cho Google Sheets: Chuẩn UTF-8 BOM tiếng Việt, đầy đủ thông tin.")

    # 7. Test Webhook Configuration
    test_webhook = "https://script.google.com/macros/s/AKfycbx_TEST_KEY/exec"
    set_app_config("google_sheet_webhook_url", test_webhook)
    cfg_val = get_app_config("google_sheet_webhook_url")
    assert cfg_val == test_webhook
    print("✅ 8. Lưu & Đọc cấu hình Webhook Google Sheet thành công.")

    print("\n==================================================")
    print("🎉 TẤT CẢ 8 MỤC KIỂM THỬ ĐÃ PASS 100%!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
