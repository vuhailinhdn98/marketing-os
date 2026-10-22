# -*- coding: utf-8 -*-
"""Công thức đo lường, cổng tuân thủ và lịch âm – dương."""
import math

import pytest

from app import guardrails, metrics, vn_calendar
from app.context import _coerce, from_legacy_profile, render_for_prompt


def test_unit_economics_uses_gross_margin():
    ue = metrics.unit_economics(revenue=3_000_000, ad_spend=1_000_000, gross_margin_pct=30, orders=40, new_customers=25,
                                ad_attributed_revenue=3_000_000)
    assert ue["roas"] == 3.0
    assert ue["breakeven_roas"] == 3.33
    assert ue["contribution_after_marketing"] == -100_000
    assert ue["ads_profitable"] is False
    assert ue["cac"] == 40_000
    assert ue["cost_per_order"] == 25_000


def test_mer_differs_from_roas():
    ue = metrics.unit_economics(revenue=10_000_000, ad_spend=1_000_000, other_cost=1_000_000, gross_margin_pct=60, orders=100,
                                ad_attributed_revenue=4_000_000)
    assert ue["mer"] == 5.0
    assert ue["roas"] == 4.0


def test_missing_data_returns_none():
    ue = metrics.unit_economics(revenue=1_000_000, ad_spend=0, orders=0)
    assert ue["mer"] is None and ue["roas"] is None and ue["cac"] is None and ue["breakeven_roas"] is None
    assert len(ue["notes"]) == 3


def test_budget_reverse():
    r = metrics.budget_reverse(target_revenue=30_000_000, aov=50_000, purchases_per_customer=3, cac=60_000, test_reserve_pct=10)
    assert r["customers_needed"] == 200
    assert r["base_budget"] == 12_000_000
    assert r["total_budget"] == 13_200_000


def test_ab_test_and_sample_size():
    r = metrics.ab_test(visitors_a=1000, conv_a=50, visitors_b=1000, conv_b=80)
    assert r["significant_95"] is True and r["lift_pct"] == 60.0
    r2 = metrics.ab_test(visitors_a=100, conv_a=5, visitors_b=100, conv_b=6)
    assert r2["significant_95"] is False
    n = metrics.sample_size_per_variant(baseline_pct=5, min_detectable_lift_pct=20)
    assert 7000 < n < 9000
    with pytest.raises(ValueError):
        metrics.ab_test(visitors_a=10, conv_a=11, visitors_b=10, conv_b=1)


def test_utm_build():
    url = metrics.utm_build(base_url="https://pheLy.vn/menu?x=1&utm_source=old", source="Facebook", medium="Bài đăng",
                            campaign="Cà phê muối T11")
    assert "utm_source=facebook" in url and "utm_medium=bai-dang" in url and "utm_campaign=ca-phe-muoi-t11" in url
    assert "x=1" in url and "utm_source=old" not in url
    with pytest.raises(ValueError):
        metrics.utm_build(base_url="phely.vn", source="a", medium="b", campaign="c")


def test_ad_name_convention():
    assert metrics.ad_name(platform="meta", objective="Tin nhắn", audience="Broad Đà Nẵng", offer="Combo 2", period="2026Q4") == \
        "META_Tin-Nhan_Broad-Da-Nang_Combo-2_2026q4"


def test_scale_warnings():
    w = metrics.scale_warnings([("2026-10-01", 100_000), ("2026-10-02", 200_000)])
    assert len(w) == 2
    assert metrics.scale_warnings([("2026-10-01", 100_000), ("2026-10-05", 120_000)]) == []


def test_funnel_bottleneck():
    d = metrics.funnel_diagnosis([("Lead", 100), ("Tư vấn", 60), ("Mua", 12), ("Mua lại", 6)])
    assert d["bottleneck"]["to"] == "Mua"
    d2 = metrics.funnel_diagnosis([("Lead", 3), ("Tư vấn", 1)])
    assert d2["bottleneck"] is None and d2["note"]


def test_anomalies_and_forecast():
    series = [(f"2026-10-{d:02d}", 100.0) for d in range(1, 15)] + [("2026-10-15", 200.0)]
    a = metrics.anomalies(series)
    assert a and a[-1]["date"] == "2026-10-15" and a[-1]["change_pct"] == 100.0
    f = metrics.linear_forecast([(f"2026-10-{d:02d}", float(d)) for d in range(1, 21)], 5)
    assert f["slope_per_day"] == 1.0 and f["r2"] == 1.0 and f["points"][0]["value"] == 21.0
    assert metrics.linear_forecast([("2026-10-01", 1.0)] * 5) is None


def test_pacing():
    p = metrics.pacing(planned_month_budget=3_000_000, spent_to_date=2_000_000, day_of_month=10, days_in_month=30)
    assert p["status"] == "Chi nhanh hơn kế hoạch" and p["pacing_pct"] == 200.0


def test_guardrails_detect_fabrication():
    ctx = {"proof": [{"text": "Hơn 500 khách quen mỗi tháng", "permission": True}], "brand": {"industry": "Quán cà phê"}}
    text = {"body": "3 sai lầm khiến 80% khách hàng mất tiền oan. Chỉ còn 5 suất hôm nay! Sản phẩm đột phá. Giảm 10% cho đơn đầu."}
    r = guardrails.check(text, kind="post", context=ctx)
    codes = {x["code"] for x in r["blockers"]}
    assert {"G01", "G03"} <= codes
    warn_codes = {x["code"] for x in r["warnings"]}
    assert {"G02", "G04"} <= warn_codes


def test_guardrails_allow_sourced_and_discounts():
    ctx = {"proof": [], "brand": {"industry": "Quán cà phê"}}
    text = {"body": "Giảm 10% cho đơn đầu tiên. Cà phê muối 29.000đ. Thị trường tăng 12% [Unverified]."}
    r = guardrails.check(text, kind="post", context=ctx)
    assert r["blockers"] == []
    r2 = guardrails.check({"body": "Chỉ còn 20 hộp cuối"}, kind="post", context=ctx, scarcity_evidence="Lô hàng chỉ có 20 hộp")
    assert all(b["code"] != "G03" for b in r2["blockers"])


def test_guardrails_competitor_and_tactics_and_kol():
    r = guardrails.check({"body": "Quán ABC phục vụ chậm và đắt."}, kind="ad", context={}, competitor_names=["Quán ABC"])
    assert any(b["code"] == "G05" for b in r["blockers"])
    r2 = guardrails.check({"x": "Dùng tool quét UID rồi đổi UID thành số để chạy ads"}, kind="internal", context={})
    assert any(b["code"] == "G11" for b in r2["blockers"])
    r3 = guardrails.check({"x": "Brief cho KOL review món mới"}, kind="kol_brief", context={})
    assert any(b["code"] == "G06" for b in r3["blockers"])
    r4 = guardrails.check({"x": "Kem chữa khỏi mụn"}, kind="post", context={"brand": {"industry": "Mỹ phẩm"}})
    assert any(b["code"] == "G10" for b in r4["blockers"])


def test_budget_and_kpi_checks():
    issues = guardrails.check_budget_lines([{"item": "Google Ads", "unit_price": 150000, "unit": "VND/tháng", "quantity": 30,
                                             "projected_total": 150000}])
    assert len(issues) == 2
    kpi = guardrails.check_kpis([{"name": "Tăng like fanpage", "target": "nhiều", "deadline": ""}])
    assert len(kpi) == 3


def test_lunar_holidays():
    assert vn_calendar.lunar_to_solar(1, 1, 2026).isoformat() == "2026-02-17"
    assert vn_calendar.lunar_to_solar(1, 1, 2027).isoformat() == "2027-02-06"
    assert vn_calendar.lunar_to_solar(15, 8, 2026).isoformat() == "2026-09-25"
    assert vn_calendar.lunar_to_solar(10, 3, 2026).isoformat() == "2026-04-26"
    from datetime import date
    names = [h["name"] for h in vn_calendar.holidays_between(date(2026, 2, 1), date(2026, 2, 28))]
    assert "Ông Công Ông Táo" in names and "Tết Nguyên Đán (mùng 1)" in names


def test_context_coercion_and_legacy():
    assert _coerce("number", "1.200.000") == 1_200_000
    assert _coerce("number", "35,5") == 35.5
    assert _coerce("number", "60%") == 60
    ctx = from_legacy_profile({"brand_name": "Phê Ly", "channels": "Facebook, TikTok, Google, YouTube, Website",
                               "brand_voice": "Chuyên nghiệp, Uy tín", "usp_advantages": "", "competitors": "A, B"})
    assert ctx["brand"]["name"] == "Phê Ly"
    assert "channels_active" not in ctx  # giá trị mặc định cũ không bị coi là người dùng khai
    assert ctx["competitors"]["direct"] == ["A", "B"]
    text = render_for_prompt(ctx)
    assert "[THIẾU DỮ LIỆU]" in text and "Chất lượng vượt trội" not in text
