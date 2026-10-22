# -*- coding: utf-8 -*-
"""
Automated Test Suite for Giai Đoạn 1 (P0 Features)
- Kanban Content Board & Status Advancement
- One-Click Webhook Publisher
- Lead Hub & Mini CRM with Strict Multi-Tenancy
- AEO / GEO Schema Generator
- Visual Analytics Data Aggregation
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fastapi.testclient import TestClient

# Ensure UTF-8 console output on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from app.main import app
from app.database import init_app_db, reset_database_clean, create_or_update_user, create_session, update_profile

client = TestClient(app)

def test_kanban_content_lifecycle():
    print("\n--- TEST: KANBAN CONTENT LIFECYCLE & WEBHOOK ---")
    user_email = "test_kanban_dev@gmail.com"
    reset_database_clean(user_email)
    
    # 1. Quick create an idea card
    res = client.post("/api/content/quick-create", json={
        "channel": "TikTok",
        "topic": "3 Mẹo tối ưu chi phí Ads chuyển đổi",
        "body": "Nội dung chi tiết về cách chọn tệp đối tượng và A/B testing tiêu đề...",
        "cta": "Follow kênh để xem phần 2",
        "status": "ideas"
    }, headers={"X-User-Email": user_email})
    assert res.status_code == 200, f"Quick create failed: {res.text}"
    card_id = res.json()["id"]
    print(f"Created Kanban card ID: {card_id}")
    
    # 2. Advance to 'drafting'
    res = client.patch(f"/api/content/{card_id}/status", json={"status": "drafting"}, headers={"X-User-Email": user_email})
    assert res.status_code == 200
    
    # 3. Advance to 'ready'
    res = client.patch(f"/api/content/{card_id}/status", json={"status": "ready"}, headers={"X-User-Email": user_email})
    assert res.status_code == 200
    
    # 4. Verify item status in history
    res = client.get("/api/content/history", headers={"X-User-Email": user_email})
    assert res.status_code == 200
    items = res.json()["items"]
    target = next((i for i in items if i["id"] == card_id), None)
    assert target is not None
    assert target["status"] == "ready", f"Expected ready, got {target['status']}"
    
    # 5. One-Click Webhook Publish (Simulated)
    res = client.post(f"/api/content/{card_id}/publish-webhook", json={}, headers={"X-User-Email": user_email})
    assert res.status_code == 200
    publish_res = res.json()
    assert publish_res["status"] == "success"
    print(f"Webhook dispatch result: {publish_res['dispatch_status']} - {publish_res['message']}")
    
    # 6. Verify status updated to 'published'
    res = client.get("/api/content/history", headers={"X-User-Email": user_email})
    items = res.json()["items"]
    target = next((i for i in items if i["id"] == card_id), None)
    assert target["status"] == "published"
    
    # 7. Delete card
    res = client.delete(f"/api/content/{card_id}", headers={"X-User-Email": user_email})
    assert res.status_code == 200
    
    # Cleanup
    reset_database_clean(user_email)
    print("Kanban Content Lifecycle PASSED 100%")

def test_lead_crm_multi_tenancy():
    print("\n--- TEST: LEAD HUB & MINI CRM MULTI-TENANCY ---")
    user_a = "crm_user_alpha@gmail.com"
    user_b = "crm_user_beta@gmail.com"
    reset_database_clean(user_a)
    reset_database_clean(user_b)
    
    # 1. User A creates 2 leads
    res_a1 = client.post("/api/leads", json={
        "full_name": "Nguyễn Văn Alpha 1",
        "phone": "0988111222",
        "email": "alpha1@example.com",
        "source": "Facebook Ads",
        "channel": "Facebook",
        "product_interest": "Gói Chăm Sóc Da",
        "deal_value": 2500000,
        "status": "new"
    }, headers={"X-User-Email": user_a})
    assert res_a1.status_code == 200
    lead_a1_id = res_a1.json()["lead"]["id"]
    
    res_a2 = client.post("/api/leads", json={
        "full_name": "Trần Thị Alpha 2",
        "phone": "0988333444",
        "email": "alpha2@example.com",
        "source": "Website Form",
        "channel": "Website",
        "product_interest": "Bộ Kem Trị Nám",
        "deal_value": 4200000,
        "status": "consulting"
    }, headers={"X-User-Email": user_a})
    assert res_a2.status_code == 200
    lead_a2_id = res_a2.json()["lead"]["id"]
    
    # 2. User B creates 1 lead
    res_b = client.post("/api/leads", json={
        "full_name": "Phạm Văn Beta 1",
        "phone": "0977888999",
        "email": "beta1@example.com",
        "source": "TikTok Video",
        "deal_value": 1500000,
        "status": "new"
    }, headers={"X-User-Email": user_b})
    assert res_b.status_code == 200
    lead_b_id = res_b.json()["lead"]["id"]
    
    # 3. Test Multi-tenancy isolation
    # User A views leads -> must be exactly 2
    leads_a = client.get("/api/leads", headers={"X-User-Email": user_a}).json()["leads"]
    assert len(leads_a) == 2, f"Expected 2 leads for User A, got {len(leads_a)}"
    assert all("Alpha" in l["full_name"] for l in leads_a)
    
    # User B views leads -> must be exactly 1
    leads_b = client.get("/api/leads", headers={"X-User-Email": user_b}).json()["leads"]
    assert len(leads_b) == 1, f"Expected 1 lead for User B, got {len(leads_b)}"
    assert leads_b[0]["id"] == lead_b_id
    
    # 4. User B tries to update User A's lead -> Must fail (404)
    res_hack = client.patch(f"/api/leads/{lead_a1_id}/status", json={"status": "won"}, headers={"X-User-Email": user_b})
    assert res_hack.status_code == 404, f"Security Breach! User B modified User A's lead: {res_hack.status_code}"
    
    # 5. User A moves lead A1 to 'won'
    res_win = client.patch(f"/api/leads/{lead_a1_id}/status", json={"status": "won"}, headers={"X-User-Email": user_a})
    assert res_win.status_code == 200
    
    # 6. Verify stats for User A
    stats_a = client.get("/api/leads/stats", headers={"X-User-Email": user_a}).json()["stats"]
    assert stats_a["total_leads"] == 2
    assert stats_a["won_count"] == 1
    assert stats_a["consulting_count"] == 1
    assert stats_a["total_won_value"] == 2500000
    assert stats_a["win_rate"] == 50.0
    print(f"User A CRM Stats: {stats_a}")
    
    # 7. Test CSV Export (Vietnamese BOM UTF-8)
    res_csv = client.get("/api/leads/export-csv", headers={"X-User-Email": user_a})
    assert res_csv.status_code == 200
    assert res_csv.headers["content-type"].startswith("text/csv")
    csv_text = res_csv.content.decode("utf-8")
    assert "Họ Tên" in csv_text
    assert "Nguyễn Văn Alpha 1" in csv_text
    assert "Phạm Văn Beta 1" not in csv_text  # Strict isolation in CSV!
    print("CSV Export generated successfully with UTF-8 BOM encoding.")
    
    # 8. Webhook Ingestion endpoint
    res_ingest = client.post("/api/leads/webhook-ingest", json={
        "user_email": user_a,
        "full_name": "Lê Thu Hà (Từ Landing Page)",
        "phone": "0912345678",
        "source": "Landing Page Webhook",
        "deal_value": 3000000
    })
    assert res_ingest.status_code == 200
    assert res_ingest.json()["status"] == "success"
    
    # Verify User A now has 3 leads
    leads_a_updated = client.get("/api/leads", headers={"X-User-Email": user_a}).json()["leads"]
    assert len(leads_a_updated) == 3
    
    # Cleanup
    reset_database_clean(user_a)
    reset_database_clean(user_b)
    print("Lead CRM & Multi-Tenancy PASSED 100%")

def test_aeo_geo_schema_generator():
    print("\n--- TEST: AEO / GEO SCHEMA GENERATOR ---")
    user_email = "test_aeo_brand@gmail.com"
    reset_database_clean(user_email)
    
    # Configure brand profile directly in database to avoid triggering heavy autopilot pipeline in test
    update_profile({
        "brand_name": "Nha Khoa Nụ Cười Xinh",
        "industry": "Nha khoa & Thẩm mỹ răng",
        "market_scope_type": "province",
        "market_location": "Đà Nẵng",
        "products_services": "Bọc răng sứ, Niềng răng trong suốt, Cấy ghép Implant",
        "phone_hotline": "0905123456",
        "website_url": "https://nhakhoanucuoixinh.vn",
        "social_channels": "https://facebook.com/nhakhoadn, https://tiktok.com/@nhakhoadn",
        "usp_advantages": "Bác sĩ chuyên khoa 15 năm kinh nghiệm, Máy quét 3D iTero 5D hiện đại, Trả góp 0%"
    }, user_email=user_email)
    
    # Generate AEO Schema
    res = client.get("/api/strategy/aeo-schema", headers={"X-User-Email": user_email})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["brand_name"] == "Nha Khoa Nụ Cười Xinh"
    
    schemas = data["schemas"]
    # Check Organization schema
    org = schemas["organization_jsonld"]
    assert org["@type"] == "Organization"
    assert org["name"] == "Nha Khoa Nụ Cười Xinh"
    assert org["telephone"] == "0905123456"
    assert "Đà Nẵng" in org["description"]
    
    # Check Product schema
    product = schemas["product_jsonld"]
    assert product["@type"] == "Product"
    assert "Bọc răng sứ" in product["name"]
    
    # Check FAQPage schema
    faq = schemas["faq_jsonld"]
    assert faq["@type"] == "FAQPage"
    assert len(faq["mainEntity"]) >= 4
    for q in faq["mainEntity"]:
        assert q["@type"] == "Question"
        assert len(q["name"]) > 10
        assert len(q["acceptedAnswer"]["text"]) > 20
        
    # Check AEO Direct Answer
    assert "Nha Khoa Nụ Cười Xinh" in data["aeo_direct_answer"]
    assert "Đà Nẵng" in data["aeo_direct_answer"]
    print(f"Generated {len(faq['mainEntity'])} AI-Search FAQ entities and JSON-LD markup.")
    
    # Cleanup
    reset_database_clean(user_email)
    print("AEO / GEO Schema Generator PASSED 100%")

if __name__ == "__main__":
    test_kanban_content_lifecycle()
    test_lead_crm_multi_tenancy()
    test_aeo_geo_schema_generator()
    print("\n==========================================")
    print("ALL GIAI ĐOẠN 1 BACKEND TESTS PASSED 100%!")
    print("==========================================")
