# -*- coding: utf-8 -*-
"""Bộ nạp dữ liệu thật cho từng tác vụ: số liệu phễu, chỉ số, ngày lễ, dữ liệu khách… (không AI)."""
from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any, Callable, Dict, List

from app import vn_calendar
from app.context import get_path
from app.database import loads, normalize_email, one, rows
from app.netsafe import FetchError, extract_site_info, normalize_url, safe_fetch
from app.services import analytics, leads


def _fmt_money(x: Any) -> str:
    try:
        return f"{float(x):,.0f} đ".replace(",", ".")
    except (TypeError, ValueError):
        return "—"


def _funnel_text(st: Dict[str, Any]) -> str:
    lines = [f"- Tổng khách trong CRM: {st['total']} (đồng ý nhận tiếp thị: {st['consented']})"]
    for s in st["funnel"]["steps"]:
        rate = "—" if s["rate_pct"] is None else f"{s['rate_pct']}%"
        lines.append(f"- {s['from']} → {s['to']}: {s['from_count']} → {s['to_count']} ({rate})")
    b = st["funnel"]["bottleneck"]
    lines.append(f"- Nút thắt theo số liệu: {b['from']} → {b['to']} ({b['rate_pct']}%)" if b else f"- {st['funnel']['note']}")
    return "\n".join(lines)


def _ue_text(sm: Dict[str, Any]) -> str:
    ue = sm["unit_economics"]
    if not sm["entries"]:
        return "- Chưa có số liệu kinh doanh nhập tay trong kỳ."
    parts = [f"- Kỳ {sm['period']['start']} → {sm['period']['end']}: doanh thu {_fmt_money(ue['revenue'])}, chi quảng cáo {_fmt_money(ue['ad_spend'])}, "
             f"chi khác {_fmt_money(ue['other_cost'])}, đơn {ue['orders']}, lead {ue['leads']}",
             f"- MER {ue['mer']}, ROAS {ue['roas'] if ue['roas'] is not None else 'chưa có'}, ROAS hòa vốn {ue['breakeven_roas'] or 'chưa có'}, "
             f"chi phí mỗi đơn {_fmt_money(ue['cost_per_order']) if ue['cost_per_order'] else '—'}, CAC {_fmt_money(ue['cac']) if ue['cac'] else 'chưa có'}"]
    if ue.get("contribution_after_marketing") is not None:
        parts.append(f"- Lãi gộp sau marketing: {_fmt_money(ue['contribution_after_marketing'])}")
    return "\n".join(parts)


def load_plan(owner: str, inputs: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    st = leads.stats(owner)
    sm = analytics.summary(owner, 30)
    month = date.today().strftime("%Y-%m")
    bud = analytics.budget_month(owner, month)
    exps = analytics.list_experiments(owner)[:5]
    text = ["PHỄU KHÁCH HÀNG (CRM):", _funnel_text(st), "", "KẾT QUẢ 30 NGÀY:", _ue_text(sm), "",
            f"NGÂN SÁCH THÁNG {month}: dự kiến {_fmt_money(bud['projected_total'])}, thực chi {_fmt_money(bud['actual_total'])}"]
    if exps:
        text.append("THỬ NGHIỆM GẦN ĐÂY: " + "; ".join(f"{e['title']} ({e['status']}) {e.get('result') or ''}" for e in exps))
    return {"prompt_text": "\n".join(text), "funnel": st["funnel"]}


def load_weekly(owner: str, inputs: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    st = leads.stats(owner)
    week = analytics.summary(owner, 7)
    month = analytics.summary(owner, 28)
    exps = [e for e in analytics.list_experiments(owner) if e["status"] in ("running", "planned")][:5]
    text = ["PHỄU KHÁCH HÀNG (CRM):", _funnel_text(st), "", "7 NGÀY GẦN NHẤT:", _ue_text(week), "", "28 NGÀY GẦN NHẤT:", _ue_text(month)]
    if exps:
        text.append("THỬ NGHIỆM ĐANG MỞ: " + "; ".join(f"{e['title']} — {e['status']}" for e in exps))
    return {"prompt_text": "\n".join(text), "funnel": st["funnel"]}


SOURCE_PREFIX = re.compile(r"^\s*([^:：]{2,25})[:：]\s+(.+)$")


def load_voc(owner: str, inputs: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    lines, sources = [], []
    for raw in str(inputs.get("raw_feedback", "")).splitlines():
        raw = raw.strip()
        if len(raw) < 3:
            continue
        m = SOURCE_PREFIX.match(raw)
        if m and not re.search(r"\d", m.group(1)):
            sources.append(m.group(1).strip().lower())
            lines.append(m.group(2).strip())
        else:
            sources.append("")
            lines.append(raw)
    numbered = "\n".join(f"{i}. [{sources[i - 1] or 'không rõ nguồn'}] {t}" for i, t in enumerate(lines, 1))
    return {"prompt_text": f"DỮ LIỆU KHÁCH (đánh số dòng):\n{numbered}", "lines": lines, "line_sources": sources}


def load_sales(owner: str, inputs: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    reasons = leads.lost_reasons(owner)
    text = "LÝ DO MẤT KHÁCH GẦN ĐÂY (từ CRM): " + ("; ".join(reasons) if reasons else "chưa có")
    return {"prompt_text": text}


def load_calendar(owner: str, inputs: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    start = date.fromisoformat(inputs["start_date"])
    days = int(inputs.get("days") or 14)
    per_day = int(inputs.get("posts_per_day") or 1)
    channels = inputs.get("channels") or []
    plan = []
    for k in range(days):
        d = start + timedelta(days=k)
        plan.append({"date": d.isoformat(), "weekday": ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"][d.weekday()]})
    end = start + timedelta(days=days - 1)
    in_range = vn_calendar.holidays_between(start, end)
    prep = vn_calendar.upcoming_for_prep(start, days)
    text = ["DANH SÁCH NGÀY (mỗi ngày đúng " + str(per_day) + " bài):"]
    text += [f"- {p['date']} ({p['weekday']})" for p in plan]
    text.append("KÊNH ĐƯỢC DÙNG: " + ", ".join(channels))
    if prep:
        text.append("NGÀY LỄ / MÙA MUA SẮM LIÊN QUAN (chỉ dùng nếu hợp thương hiệu):")
        text += [f"- {h['date']}: {h['name']} ({h['type']}, nên chuẩn bị trước {h['prep_days']} ngày)" for h in prep]
    if inputs.get("focus"):
        text.append("TRỌNG TÂM: " + str(inputs["focus"]))
    return {"prompt_text": "\n".join(text), "plan_dates": plan, "holidays_in_range": in_range, "channels": channels}


def known_competitors(owner: str, ctx: Dict[str, Any]) -> List[str]:
    names = []
    for path in ("competitors.direct", "competitors.secondary", "competitors.indirect"):
        names += [str(x) for x in (get_path(ctx, path) or [])]
    names += [r["name"] for r in rows("SELECT name FROM discovered_competitors WHERE user_email = ?", (normalize_email(owner),))]
    seen, out = set(), []
    for n in names:
        key = n.strip().lower()
        if key and key not in seen:
            seen.add(key)
            out.append(n.strip())
    return out


def load_discovery(owner: str, inputs: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    known = known_competitors(owner, ctx)
    parts = []

    # 1. Đối thủ do chủ doanh nghiệp đã nhập tay hoặc đã lưu trước đó
    comp_rows = rows("SELECT name, website, phone, social, competitor_type, price_segment, core_products, notes FROM discovered_competitors WHERE user_email = ?", (normalize_email(owner),))
    comp_details = []
    for r in comp_rows:
        details = [f"- **{r['name']}** ({r.get('competitor_type') or 'Trực tiếp'})"]
        if r.get("website"): details.append(f"Web: {r['website']}")
        if r.get("phone"): details.append(f"SĐT: {r['phone']}")
        if r.get("social"): details.append(f"MXH: {r['social']}")
        if r.get("price_segment"): details.append(f"Giá: {r['price_segment']}")
        if r.get("core_products"): details.append(f"Bán: {r['core_products']}")
        if r.get("notes"): details.append(f"Ghi chú: {r['notes']}")
        comp_details.append(" | ".join(details))

    if comp_details:
        parts.append("ĐỐI THỦ CHỦ DOANH NGHIỆP ĐÃ NHẬP / ĐÃ LƯU TRƯỚC ĐÓ:\n" + "\n".join(comp_details) +
                     "\n-> YÊU CẦU: Hãy đưa lại các đối thủ này vào danh sách phân tích (kèm thông tin đã có), đồng thời rà soát TÌM THÊM các đối thủ cạnh tranh mới khác trên địa bàn.")
    elif known:
        parts.append("ĐỐI THỦ ĐÃ BIẾT TRONG HỒ SƠ: " + ", ".join(known) +
                     ".\n-> YÊU CẦU: Hãy đối chiếu các đối thủ này và rà soát tìm thêm mọi đối thủ cạnh tranh khác trên thị trường.")
    else:
        parts.append("ĐỐI THỦ ĐÃ BIẾT: Chủ doanh nghiệp chưa nhập đối thủ nào. Hãy rà soát toàn diện trên thị trường.")

    # 2. Bối cảnh thị trường từ lần nghiên cứu gần nhất (nếu có)
    last_market_run = one("SELECT output_json FROM skill_runs WHERE user_email = ? AND task = 'market_research' AND status = 'ok' ORDER BY id DESC LIMIT 1", (normalize_email(owner),))
    if last_market_run and last_market_run.get("output_json"):
        try:
            m_out = loads(last_market_run["output_json"], {})
            m_summary = m_out.get("summary") or ""
            sections = m_out.get("sections") or []
            comp_sec = next((s for s in sections if isinstance(s, dict) and s.get("title") == "Cạnh tranh"), None)
            trend_sec = next((s for s in sections if isinstance(s, dict) and s.get("title") == "Xu hướng"), None)
            
            context_bits = []
            if m_summary:
                context_bits.append(f"Tóm tắt thị trường: {m_summary[:400]}")
            if comp_sec and comp_sec.get("points"):
                pts = [p.get("text", "") for p in comp_sec["points"] if isinstance(p, dict) and p.get("text")]
                if pts:
                    context_bits.append("Đối thủ / bối cảnh cạnh tranh phát hiện từ nghiên cứu thị trường: " + "; ".join(pts[:5]))
            if trend_sec and trend_sec.get("points"):
                t_pts = [p.get("text", "") for p in trend_sec["points"] if isinstance(p, dict) and p.get("text")]
                if t_pts:
                    context_bits.append("Xu hướng thị trường: " + "; ".join(t_pts[:3]))
            
            if context_bits:
                market_loc = (ctx.get("market") or {}).get("location") or inputs.get("location") or ""
                parts.append(f"BỐI CẢNH THỊ TRƯỜNG ĐÃ PHÂN TÍCH ({market_loc}):\n" + "\n".join(f"- {b}" for b in context_bits) +
                             "\n-> Rà soát các đối thủ cạnh tranh phù hợp với bối cảnh thị trường này.")
        except Exception:
            pass

    return {"prompt_text": "\n".join(parts), "known_competitors": known}


def load_dossier(owner: str, inputs: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    url = normalize_url(str(inputs.get("website") or ""))
    out: Dict[str, Any] = {"prompt_text": "", "site": None}
    if inputs.get("social"):
        out["prompt_text"] += f"MẠNG XÃ HỘI ĐỐI THỦ: {inputs['social']}\n"
    if inputs.get("phone"):
        out["prompt_text"] += f"SỐ ĐIỆN THOẠI ĐỐI THỦ: {inputs['phone']}\n"
    if inputs.get("notes"):
        out["prompt_text"] += f"CHỦ DOANH NGHIỆP GHI CHÚ VỀ ĐỐI THỦ: {inputs['notes']}\n"
    if url:
        try:
            final_url, html = safe_fetch(url)
            info = extract_site_info(html)
            out["site"] = {"url": final_url, **info}
            out["prompt_text"] += (f"TRANG WEB ĐỐI THỦ (tải trực tiếp {final_url}):\n- Tiêu đề: {info['title']}\n- Mô tả: {info['description']}\n"
                                   f"- Tiêu đề mục: {'; '.join(info['headings'])}\n- Trích nội dung: {info['text_excerpt'][:1500]}")
        except FetchError as exc:
            out["prompt_text"] += f"(Không tải được website đối thủ: {exc})"
            out["site_error"] = str(exc)
    return out


LOADERS: Dict[str, Callable[[str, Dict[str, Any], Dict[str, Any]], Dict[str, Any]]] = {
    "plan": load_plan, "weekly": load_weekly, "voc": load_voc, "sales": load_sales,
    "calendar": load_calendar, "discovery": load_discovery, "dossier": load_dossier,
}
