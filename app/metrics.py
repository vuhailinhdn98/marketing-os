# -*- coding: utf-8 -*-
"""
Công thức đo lường marketing (skill §4.3, §10.5, §13) — hàm thuần, không gọi AI, có test.

Quy ước:
- Lợi nhuận luôn tính trên biên lợi nhuận gộp, không trên doanh thu.
- MER (hiệu quả marketing tổng) ≠ ROAS (doanh thu do quảng cáo ÷ chi quảng cáo).
- CAC tổng hợp = toàn bộ chi marketing (quảng cáo + chi phí cố định) ÷ số khách MỚI.
- Thiếu dữ liệu thì trả None, không đoán.
"""
from __future__ import annotations

import math
import re
import unicodedata
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


def _div(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b in (None, 0):
        return None
    return a / b


def _r(x: Optional[float], nd: int = 2) -> Optional[float]:
    return None if x is None else round(x, nd)


def unit_economics(*, revenue: float, ad_spend: float, other_cost: float = 0.0, gross_margin_pct: Optional[float] = None,
                   orders: int = 0, new_customers: Optional[int] = None, leads: int = 0,
                   ad_attributed_revenue: Optional[float] = None, messages: int = 0) -> Dict[str, Any]:
    total_cost = (ad_spend or 0) + (other_cost or 0)
    gm = gross_margin_pct / 100 if gross_margin_pct else None
    gross_profit = revenue * gm if gm is not None else None
    out = {
        "revenue": revenue,
        "orders": orders,
        "new_customers": new_customers,
        "leads": leads,
        "ad_spend": ad_spend,
        "other_cost": other_cost,
        "total_marketing_cost": total_cost,
        "gross_margin_pct": gross_margin_pct,
        "gross_profit": _r(gross_profit, 0),
        "contribution_after_marketing": _r(gross_profit - total_cost, 0) if gross_profit is not None else None,
        "mer": _r(_div(revenue, total_cost)),
        "roas": _r(_div(ad_attributed_revenue, ad_spend)) if ad_attributed_revenue is not None else None,
        "breakeven_roas": _r(1 / gm) if gm else None,
        "cost_per_order": _r(_div(total_cost, orders), 0),
        "cac": _r(_div(total_cost, new_customers), 0) if new_customers else None,
        "cpl": _r(_div(total_cost, leads), 0),
        "cost_per_message": _r(_div(ad_spend, messages), 0),
        "aov": _r(_div(revenue, orders), 0),
    }
    notes = []
    if gm is None:
        notes.append("Chưa có biên lợi nhuận gộp trong hồ sơ: chưa tính được lãi gộp và ROAS hòa vốn.")
    if ad_attributed_revenue is None:
        notes.append("Chưa nhập doanh thu do quảng cáo mang lại: ROAS để trống, chỉ có MER.")
    if not new_customers:
        notes.append("Chưa nhập số khách mới: CAC để trống (chi phí mỗi đơn không phải CAC).")
    if out["roas"] is not None and out["breakeven_roas"] is not None:
        out["ads_profitable"] = out["roas"] >= out["breakeven_roas"]
    out["notes"] = notes
    return out


def ltv(*, aov: float, gross_margin_pct: float, purchases_per_customer: float) -> Optional[float]:
    if not aov or not gross_margin_pct or not purchases_per_customer:
        return None
    return round(aov * gross_margin_pct / 100 * purchases_per_customer, 0)


def payback_months(*, cac: float, aov: float, gross_margin_pct: float, purchases_per_month: float) -> Optional[float]:
    monthly_gp = aov * gross_margin_pct / 100 * purchases_per_month if aov and gross_margin_pct and purchases_per_month else 0
    if not cac or not monthly_gp:
        return None
    return round(cac / monthly_gp, 1)


def budget_reverse(*, target_revenue: float, aov: float, purchases_per_customer: float = 1.0,
                   cac: Optional[float] = None, test_reserve_pct: float = 15.0) -> Dict[str, Any]:
    """Skill §13.2: Số khách mới cần = doanh thu mục tiêu ÷ giá trị mỗi khách; ngân sách = số khách × CAC (+ dự phòng thử nghiệm)."""
    value_per_customer = aov * max(purchases_per_customer, 1e-9)
    customers = math.ceil(target_revenue / value_per_customer) if value_per_customer else None
    out: Dict[str, Any] = {"value_per_customer": round(value_per_customer, 0), "customers_needed": customers}
    if cac and customers:
        base = customers * cac
        out.update({"base_budget": round(base, 0), "test_reserve": round(base * test_reserve_pct / 100, 0),
                    "total_budget": round(base * (1 + test_reserve_pct / 100), 0)})
    else:
        out["note"] = "Cần CAC (hoặc chi phí mỗi khách mới) để tính ngân sách. Nếu chưa biết, đây là quyết định mở quan trọng nhất."
    return out


def paid_funnel(*, budget: float, cpm: Optional[float] = None, cpc: Optional[float] = None, ctr_pct: Optional[float] = None,
                cvr_pct: Optional[float] = None, cost_per_result: Optional[float] = None) -> Dict[str, Any]:
    """KPI suy ra từ phễu (skill §3.3): ngân sách ÷ chi phí → tiếp cận/click → chuyển đổi."""
    out: Dict[str, Any] = {"budget": budget}
    if cost_per_result:
        out["results"] = math.floor(budget / cost_per_result)
        return out
    impressions = clicks = None
    if cpm:
        impressions = budget / cpm * 1000
        out["impressions"] = math.floor(impressions)
        if ctr_pct:
            clicks = impressions * ctr_pct / 100
    if cpc:
        clicks = budget / cpc
    if clicks is not None:
        out["clicks"] = math.floor(clicks)
        if cvr_pct:
            out["conversions"] = math.floor(clicks * cvr_pct / 100)
    return out


def ab_test(*, visitors_a: int, conv_a: int, visitors_b: int, conv_b: int) -> Dict[str, Any]:
    """Kiểm định z hai tỉ lệ (hai phía)."""
    if min(visitors_a, visitors_b) <= 0 or conv_a < 0 or conv_b < 0 or conv_a > visitors_a or conv_b > visitors_b:
        raise ValueError("Số liệu thử nghiệm không hợp lệ.")
    pa, pb = conv_a / visitors_a, conv_b / visitors_b
    pooled = (conv_a + conv_b) / (visitors_a + visitors_b)
    se = math.sqrt(pooled * (1 - pooled) * (1 / visitors_a + 1 / visitors_b))
    z = (pb - pa) / se if se > 0 else 0.0
    p_value = math.erfc(abs(z) / math.sqrt(2))
    return {"rate_a": round(pa * 100, 2), "rate_b": round(pb * 100, 2),
            "lift_pct": round((pb - pa) / pa * 100, 1) if pa > 0 else None,
            "z": round(z, 3), "p_value": round(p_value, 4), "significant_95": p_value < 0.05,
            "verdict": ("B tốt hơn A có ý nghĩa thống kê (95%)" if p_value < 0.05 and pb > pa else
                        "A tốt hơn B có ý nghĩa thống kê (95%)" if p_value < 0.05 else
                        "Chưa đủ bằng chứng để kết luận — chạy tiếp, đừng dừng sớm")}


def sample_size_per_variant(*, baseline_pct: float, min_detectable_lift_pct: float) -> Optional[int]:
    """Cỡ mẫu mỗi nhánh cho alpha 5% (hai phía), power 80%."""
    p1 = baseline_pct / 100
    p2 = p1 * (1 + min_detectable_lift_pct / 100)
    if not (0 < p1 < 1 and 0 < p2 < 1) or p1 == p2:
        return None
    z_a, z_b = 1.959964, 0.841621
    pbar = (p1 + p2) / 2
    n = ((z_a * math.sqrt(2 * pbar * (1 - pbar)) + z_b * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2) / (p2 - p1) ** 2
    return math.ceil(n)


def _slug(value: str) -> str:
    value = unicodedata.normalize("NFD", value or "")
    value = "".join(c for c in value if unicodedata.category(c) != "Mn").replace("đ", "d").replace("Đ", "D")
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return value[:80]


def utm_build(*, base_url: str, source: str, medium: str, campaign: str, content: str = "", term: str = "") -> str:
    parsed = urlparse((base_url or "").strip())
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("Link gốc phải bắt đầu bằng http:// hoặc https://")
    if not (source and medium and campaign):
        raise ValueError("utm_source, utm_medium, utm_campaign là bắt buộc.")
    params = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if not k.lower().startswith("utm_")]
    for key, val in (("utm_source", source), ("utm_medium", medium), ("utm_campaign", campaign),
                     ("utm_content", content), ("utm_term", term)):
        if val:
            params.append((key, _slug(val)))
    return urlunparse(parsed._replace(query=urlencode(params)))


def ad_name(*, platform: str, objective: str, audience: str, offer: str, period: str) -> str:
    """Quy ước skill §10.2: [Nền tảng]_[Mục tiêu]_[Tệp]_[Ưu đãi]_[Thời gian]."""
    def part(x: str) -> str:
        words = [w for w in _slug(x).split("-") if w]
        return "-".join(w.capitalize() for w in words)[:40] or "NA"
    return "_".join([_slug(platform).upper() or "NA", part(objective), part(audience), part(offer), part(period)])


def scale_warnings(budget_history: Sequence[Tuple[str, float]]) -> List[str]:
    """Skill §10.2: mỗi lần tăng ~20%, chờ 3–5 ngày. history = [(YYYY-MM-DD, ngân sách/ngày)] theo thời gian."""
    warnings = []
    hist = sorted(budget_history)
    for i in range(1, len(hist)):
        prev_date, prev_budget = hist[i - 1]
        cur_date, cur_budget = hist[i]
        if prev_budget <= 0:
            continue
        change = (cur_budget - prev_budget) / prev_budget * 100
        gap = (date.fromisoformat(cur_date) - date.fromisoformat(prev_date)).days
        if change > 25:
            warnings.append(f"{cur_date}: tăng {change:.0f}% một lần (khuyến nghị ~20%).")
        if change > 0 and gap < 3:
            warnings.append(f"{cur_date}: tăng ngân sách chỉ sau {gap} ngày (khuyến nghị chờ 3–5 ngày).")
    return warnings


def funnel_diagnosis(stages: Sequence[Tuple[str, int]], min_base: int = 5) -> Dict[str, Any]:
    """Theory of Constraints: tầng có tỉ lệ chuyển thấp nhất (đủ mẫu) là nút thắt."""
    steps = []
    for (name_a, a), (name_b, b) in zip(stages, stages[1:]):
        rate = (b / a * 100) if a else None
        steps.append({"from": name_a, "to": name_b, "from_count": a, "to_count": b,
                      "rate_pct": round(rate, 1) if rate is not None else None, "enough_data": a >= min_base})
    valid = [s for s in steps if s["rate_pct"] is not None and s["enough_data"]]
    bottleneck = min(valid, key=lambda s: s["rate_pct"]) if valid else None
    return {"steps": steps, "bottleneck": bottleneck,
            "note": None if bottleneck else f"Chưa đủ dữ liệu (mỗi tầng cần ít nhất {min_base} khách) để xác định nút thắt."}


def anomalies(series: Sequence[Tuple[str, float]], threshold_pct: float = 30.0, window: int = 7) -> List[Dict[str, Any]]:
    """So mỗi ngày với trung bình `window` ngày trước đó; lệch quá ±threshold là bất thường."""
    out = []
    values = list(series)
    for i in range(window, len(values)):
        base = [v for _, v in values[i - window:i]]
        avg = sum(base) / len(base)
        day, val = values[i]
        if avg == 0:
            continue
        change = (val - avg) / avg * 100
        if abs(change) >= threshold_pct:
            out.append({"date": day, "value": val, "baseline": round(avg, 2), "change_pct": round(change, 1)})
    return out


def linear_forecast(series: Sequence[Tuple[str, float]], days_ahead: int = 30) -> Optional[Dict[str, Any]]:
    """Hồi quy tuyến tính đơn giản. Chỉ để tham khảo [Speculation]."""
    pts = [(i, v) for i, (_, v) in enumerate(series)]
    n = len(pts)
    if n < 14:
        return None
    mx = sum(x for x, _ in pts) / n
    my = sum(y for _, y in pts) / n
    sxx = sum((x - mx) ** 2 for x, _ in pts)
    if sxx == 0:
        return None
    slope = sum((x - mx) * (y - my) for x, y in pts) / sxx
    intercept = my - slope * mx
    ss_tot = sum((y - my) ** 2 for _, y in pts)
    ss_res = sum((y - (intercept + slope * x)) ** 2 for x, y in pts)
    r2 = 1 - ss_res / ss_tot if ss_tot else 0.0
    last_day = date.fromisoformat(series[-1][0])
    forecast = []
    for k in range(1, days_ahead + 1):
        x = n - 1 + k
        forecast.append({"date": (last_day + timedelta(days=k)).isoformat(), "value": round(max(0.0, intercept + slope * x), 2)})
    return {"slope_per_day": round(slope, 2), "r2": round(r2, 3), "total_next": round(sum(f["value"] for f in forecast), 0),
            "points": forecast, "label": "[Speculation] Dự báo tuyến tính, chỉ tham khảo; độ tin cậy thấp khi R² < 0,5."}


def pacing(*, planned_month_budget: float, spent_to_date: float, day_of_month: int, days_in_month: int) -> Dict[str, Any]:
    expected = planned_month_budget * day_of_month / days_in_month if days_in_month else 0
    ratio = spent_to_date / expected * 100 if expected else None
    status = None
    if ratio is not None:
        status = "Chi nhanh hơn kế hoạch" if ratio > 110 else "Chi chậm hơn kế hoạch" if ratio < 90 else "Đúng nhịp"
    return {"expected_to_date": round(expected, 0), "spent_to_date": spent_to_date,
            "pacing_pct": round(ratio, 1) if ratio is not None else None, "status": status,
            "projected_month_end": round(spent_to_date / day_of_month * days_in_month, 0) if day_of_month else None}
