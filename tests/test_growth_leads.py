# -*- coding: utf-8 -*-
"""CRM 6 tầng, Growth Console, nhập CSV, ngân sách, UTM, Local SEO, kiểm duyệt, sao lưu/làm mới."""
from pathlib import Path

from tests.conftest import register

ROOT = Path(__file__).resolve().parent.parent


def test_lead_stages_consent_and_funnel(client, auth):
    a = client.post("/api/leads", json={"full_name": "An", "phone": "0901", "consent_marketing": True,
                                        "consent_text": "Đồng ý nhận ưu đãi qua Zalo"}, headers=auth).json()["lead"]
    b = client.post("/api/leads", json={"full_name": "Bình", "email": "b@x.vn"}, headers=auth).json()["lead"]
    assert a["consent_marketing"] == 1 and a["consent_at"] and b["consent_marketing"] == 0
    assert client.post("/api/leads", json={"full_name": "C"}, headers=auth).status_code == 400
    assert client.post("/api/leads", json={"full_name": "D", "phone": "1", "consent_marketing": True}, headers=auth).status_code == 400
    for st in ("consulting", "won", "repeat"):
        client.patch(f"/api/leads/{a['id']}/status", json={"status": st}, headers=auth)
    lost = client.patch(f"/api/leads/{b['id']}/status", json={"status": "lost", "lost_reason": "Chê giá"}, headers=auth).json()["lead"]
    assert lost["lost_from_stage"] == "new" and lost["lost_reason"] == "Chê giá"
    s = client.get("/api/leads/stats", headers=auth).json()
    assert s["reached"]["new"] == 2 and s["reached"]["won"] == 1 and s["reached"]["repeat"] == 1 and s["consented"] == 1
    csv_all = client.get("/api/leads/export.csv", headers=auth).text
    csv_ok = client.get("/api/leads/export.csv?consented_only=true", headers=auth).text
    assert "Bình" in csv_all and "Bình" not in csv_ok and "An" in csv_ok
    withdrawn = client.patch(f"/api/leads/{a['id']}", json={"consent_marketing": False}, headers=auth).json()["lead"]
    assert withdrawn["consent_marketing"] == 0


def test_metrics_summary_and_validation(client, auth):
    client.patch("/api/context", json={"patch": {"unit_economics.gross_margin_pct": 30}}, headers=auth)
    from datetime import date
    today = date.today().isoformat()
    ok = client.post("/api/metrics", json={"date": today, "channel": "Facebook", "ad_spend": 1_000_000, "revenue": 3_000_000,
                                           "ad_attributed_revenue": 3_000_000, "orders_count": 40, "new_customers": 25, "leads_count": 60},
                     headers=auth)
    assert ok.status_code == 200
    bad = client.post("/api/metrics", json={"date": today, "revenue": 100, "ad_attributed_revenue": 200}, headers=auth)
    assert bad.status_code == 400
    s = client.get("/api/growth/summary?days=30", headers=auth).json()
    ue = s["unit_economics"]
    assert ue["roas"] == 3.0 and ue["breakeven_roas"] == 3.33 and ue["contribution_after_marketing"] == -100_000
    assert s["channels"][0]["channel"] == "Facebook"


def test_csv_import_and_report(client, auth):
    content = (ROOT / "data" / "samples" / "sales_sample.csv").read_text(encoding="utf-8")
    res = client.post("/api/imports", json={"filename": "sales_2026.csv", "content": content}, headers=auth).json()
    assert res["kind"] == "sales" and res["rows"] > 100
    ads = (ROOT / "data" / "samples" / "ads_sample.csv").read_text(encoding="utf-8")
    client.post("/api/imports", json={"filename": "ads_2026.csv", "content": ads}, headers=auth)
    rep = client.get("/api/growth/imported?days=730", headers=auth).json()
    assert rep["sales"]["orders"] > 0 and rep["ads"][0]["spend"] > 0
    again = client.post("/api/imports", json={"filename": "sales_2026.csv", "content": content}, headers=auth).json()
    rep2 = client.get("/api/growth/imported?days=730", headers=auth).json()
    assert rep2["sales"]["orders"] == rep["sales"]["orders"]  # nhập lại cùng kỳ không nhân đôi
    bad = client.post("/api/imports", json={"filename": "web_x.csv", "content": "date,source\n2026-01-01,google"}, headers=auth)
    assert bad.status_code == 400 and "Thiếu cột" in bad.json()["detail"]
    assert again["rows"] == res["rows"]


def test_budget_utm_experiments_calculators(client, auth):
    line = client.post("/api/budget/lines", json={"month": "2026-11", "program": "Quảng cáo trả phí", "item": "FB", "unit_price": 100000,
                                                  "unit": "VND/ngày", "quantity": 30}, headers=auth).json()
    client.patch(f"/api/budget/lines/{line['id']}", json={"actual_total": 3_200_000}, headers=auth)
    b = client.get("/api/budget?month=2026-11", headers=auth).json()
    assert b["projected_total"] == 3_000_000 and b["actual_total"] == 3_200_000 and b["variance"] == 200_000
    assert client.post("/api/budget/lines", json={"month": "11/2026", "program": "x", "item": "y"}, headers=auth).status_code == 400
    u = client.post("/api/utm", json={"base_url": "https://phely.vn", "utm_source": "Facebook", "utm_medium": "social",
                                      "utm_campaign": "Ra mắt T11"}, headers=auth).json()
    assert u["full_url"] == "https://phely.vn?utm_source=facebook&utm_medium=social&utm_campaign=ra-mat-t11"
    assert len(client.get("/api/utm", headers=auth).json()["links"]) == 1
    e = client.post("/api/experiments", json={"title": "Đổi ảnh bìa", "status": "running"}, headers=auth).json()
    assert client.patch(f"/api/experiments/{e['id']}", json={"status": "done", "result": "Tăng 12% tin nhắn"}, headers=auth).status_code == 200
    assert client.patch(f"/api/experiments/{e['id']}", json={"status": "xyz"}, headers=auth).status_code == 400
    r = client.post("/api/calc/budget-reverse", json={"target_revenue": 30_000_000, "aov": 50_000, "purchases_per_customer": 3, "cac": 60_000},
                    headers=auth).json()
    assert r["customers_needed"] == 200
    ab = client.post("/api/calc/ab-test", json={"visitors_a": 1000, "conv_a": 50, "visitors_b": 1000, "conv_b": 80}, headers=auth).json()
    assert ab["significant_95"] is True
    assert client.post("/api/calc/ltv", json={"purchases_per_customer": 5}, headers=auth).status_code == 400
    client.patch("/api/context", json={"patch": {"unit_economics.gross_margin_pct": 60, "unit_economics.avg_order_value_vnd": 40000}},
                 headers=auth)
    ltv = client.post("/api/calc/ltv", json={"purchases_per_customer": 5, "cac": 30000, "purchases_per_month": 2}, headers=auth).json()
    assert ltv["ltv_gross_profit"] == 120_000 and ltv["ltv_cac"] == 4.0 and ltv["payback_months"] == 0.6


def test_local_seo_never_invents(client, auth):
    t = client.get("/api/local-seo", headers=auth).json()
    assert t["ready"] is False and "faq_page" not in t["schema"]
    client.patch("/api/context", json={"patch": {"brand.name": "Phê Ly", "brand.address": "12 Nguyễn Phước Lan",
                                                 "product.price_points": [{"name": "A", "price_vnd": 25000}, {"name": "B", "price_vnd": 35000}],
                                                 "faq": [{"q": "Có giao hàng không?", "a": "Có, bán kính 3 km."}]}}, headers=auth)
    t = client.get("/api/local-seo", headers=auth).json()
    lb = t["schema"]["local_business"]
    assert lb["name"] == "Phê Ly" and lb["priceRange"] == "25.000–35.000 VND" and "offers" not in lb
    assert t["schema"]["faq_page"]["mainEntity"][0]["acceptedAnswer"]["text"] == "Có, bán kính 3 km."


def test_compliance_check_endpoint(client, auth):
    r = client.post("/api/compliance/check", json={"text": "Chỉ còn 3 suất! 90% khách hài lòng.", "kind": "ad"}, headers=auth).json()
    assert {b["code"] for b in r["blockers"]} >= {"G01", "G03"}
    r2 = client.post("/api/compliance/check", json={"text": "Review món mới cùng Phê Ly", "is_sponsored": True}, headers=auth).json()
    assert any(b["code"] == "G06" for b in r2["blockers"])


def test_context_versions_and_validation(client, auth):
    assert client.patch("/api/context", json={"patch": {"unit_economics.gross_margin_pct": 150}}, headers=auth).status_code == 400
    assert client.patch("/api/context", json={"patch": {"khong.ton.tai": 1}}, headers=auth).status_code == 400
    r = client.patch("/api/context", json={"patch": {"brand.name": "Phê Ly"}, "note": "Bắt đầu"}, headers=auth).json()
    assert r["context"]["version"] == 2 and r["context"]["changelog"][0]["why"] == "Bắt đầu"
    same = client.patch("/api/context", json={"patch": {"brand.name": "Phê Ly"}}, headers=auth).json()
    assert same["context"]["version"] == 2
    q = client.get("/api/context/questions?limit=3", headers=auth).json()["questions"]
    assert len(q) == 3 and all(x["path"] != "brand.name" for x in q)
    assert len(client.get("/api/context/versions", headers=auth).json()["versions"]) == 1


def test_export_reset_delete_account(client):
    h = register(client, "x@example.com")
    client.post("/api/leads", json={"full_name": "K", "phone": "1"}, headers=h)
    exp = client.get("/api/workspace/export", headers=h).json()
    assert len(exp["tables"]["lead_records"]) == 1
    assert client.post("/api/workspace/reset", json={"confirm": "no"}, headers=h).status_code == 400
    client.post("/api/workspace/reset", json={"confirm": "XOA"}, headers=h)
    assert client.get("/api/leads", headers=h).json()["count"] == 0
    assert client.request("DELETE", "/api/account", json={"confirm": "x@example.com"}, headers=h).status_code == 200
    assert client.post("/api/auth/login", json={"email": "x@example.com", "password": "Matkhau123"}).status_code == 401


def test_content_crud_and_calendar_legacy(client, auth):
    item = client.post("/api/content", json={"channel": "TikTok", "topic": "Hậu trường pha chế", "body": "Xem cách pha"}, headers=auth).json()["item"]
    assert item["status"] == "draft" and item["status_label"] == "Bản nháp"
    got = client.get(f"/api/content/{item['id']}", headers=auth).json()
    assert len(got["promotion_checklist"]) >= 10
    assert client.patch(f"/api/content/{item['id']}/status", json={"status": "bogus"}, headers=auth).status_code == 400
    assert client.post("/api/content", json={"topic": "x", "status": "published"}, headers=auth).status_code == 400
    assert client.delete(f"/api/content/{item['id']}", headers=auth).status_code == 200
    from app.database import execute
    execute("INSERT INTO calendar_schedules (user_email, day_number, channel, topic) VALUES ('owner@example.com', 1, 'Facebook', 'cũ')")
    cal = client.get("/api/calendar", headers=auth).json()
    assert cal["legacy_rows"] == 1
    assert client.delete("/api/calendar/legacy", headers=auth).json()["deleted"] == 1
