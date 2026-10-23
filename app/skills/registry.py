# -*- coding: utf-8 -*-
"""
Danh mục tác vụ của Skill Engine.

Mỗi tác vụ khai báo: mục skill cần nạp, ô nhập, trường hồ sơ bắt buộc, JSON Schema đầu ra,
loại nội dung cho cổng tuân thủ, và bước hậu xử lý bằng code (tính toán, kiểm tra, sửa số).
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple

from app import metrics

# ---------------------------------------------------------------------------
# Tiện ích dựng schema
# ---------------------------------------------------------------------------

S: Dict[str, Any] = {"type": "string"}
I: Dict[str, Any] = {"type": "integer"}
N: Dict[str, Any] = {"type": "number"}
B: Dict[str, Any] = {"type": "boolean"}


def A(item: Dict[str, Any], min_items: Optional[int] = None, max_items: Optional[int] = None) -> Dict[str, Any]:
    out: Dict[str, Any] = {"type": "array", "items": item}
    if min_items is not None:
        out["minItems"] = min_items
    if max_items is not None:
        out["maxItems"] = max_items
    return out


def O(props: Dict[str, Any], required: Optional[List[str]] = None) -> Dict[str, Any]:
    return {"type": "object", "properties": props, "required": required if required is not None else list(props)}


def E(*values: str) -> Dict[str, Any]:
    return {"type": "string", "enum": list(values)}


def with_common(schema: Dict[str, Any]) -> Dict[str, Any]:
    props = dict(schema["properties"])
    props["missing_info"] = A(S)
    props["lesson"] = A(S, 1, 4)
    req = list(schema.get("required", [])) + ["missing_info", "lesson"]
    return {"type": "object", "properties": props, "required": req}


POINT = O({"text": S, "source_ids": A(I), "tag": E("Có nguồn", "[Unverified]", "[Inference]")})
KPI = O({"name": S, "target": S, "deadline": S, "formula": S})

# ---------------------------------------------------------------------------
# Định nghĩa
# ---------------------------------------------------------------------------

PostFn = Callable[[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]], Tuple[Dict[str, Any], List[Dict[str, str]]]]


@dataclass
class Task:
    id: str
    group: str
    title: str
    description: str
    sections: List[str]
    inputs: List[Dict[str, Any]]
    schema: Dict[str, Any]
    instructions: str
    kind: Any = "internal"  # str hoặc hàm(inputs) -> str
    required_context: List[str] = field(default_factory=list)
    temperature: float = 0.5
    grounded: bool = False
    extras: Optional[str] = None  # tên bộ nạp dữ liệu (app.services.extras)
    post: Optional[PostFn] = None
    module: str = ""

    def guard_kind(self, inputs: Dict[str, Any]) -> str:
        return self.kind(inputs) if callable(self.kind) else self.kind

    def public(self) -> Dict[str, Any]:
        return {"id": self.id, "group": self.group, "module": self.module, "title": self.title,
                "description": self.description, "inputs": self.inputs, "required_context": self.required_context,
                "grounded": self.grounded, "sections": self.sections}


def inp(name: str, label: str, type_: str = "text", required: bool = False, **kw: Any) -> Dict[str, Any]:
    d = {"name": name, "label": label, "type": type_, "required": required}
    d.update(kw)
    return d


CHANNEL_KIND = {
    "Bài Facebook": "post", "Kịch bản TikTok/Reels": "video_script", "Tin Zalo OA": "post", "Email": "email",
    "Landing page": "landing", "Quảng cáo Google Search": "ad", "Quảng cáo Facebook": "ad", "Bài blog/website": "post",
    "SMS": "sms",
}

# ---------------------------------------------------------------------------
# Hậu xử lý
# ---------------------------------------------------------------------------

def _post_offer(data, inputs, ctx, extras):
    issues = []
    levers = [l for l in data.get("levers", []) if isinstance(l.get("score"), (int, float))]
    for l in levers:
        l["score"] = max(1, min(10, int(round(l["score"]))))
    if levers:
        weakest = min(levers, key=lambda l: l["score"])
        if data.get("weakest_lever") != weakest["name"]:
            data["weakest_lever"] = weakest["name"]
            issues.append({"code": "CALC", "message": f"Đòn bẩy yếu nhất được tính lại theo điểm: {weakest['name']}."})
    lift = data.get("expected_lift") or {}
    lift["label"] = "[Unverified]"
    data["expected_lift"] = lift
    return data, issues


def _post_copy(data, inputs, ctx, extras):
    variants = data.get("variants") or []
    rec = data.get("recommended")
    if not isinstance(rec, int) or not (0 <= rec < len(variants)):
        data["recommended"] = 0
    return data, []


def _post_pillars(data, inputs, ctx, extras):
    pillars = data.get("pillars") or []
    total = sum(float(p.get("share_pct") or 0) for p in pillars)
    if total > 0 and abs(total - 100) > 0.5:
        for p in pillars:
            p["share_pct"] = round(float(p.get("share_pct") or 0) * 100 / total)
        return data, [{"code": "CALC", "message": f"Tỉ lệ trụ cột được chuẩn hóa về 100% (AI trả tổng {total:g}%)."}]
    return data, []


def _post_calendar(data, inputs, ctx, extras):
    plan = extras.get("plan_dates") or []
    allowed_dates = {d["date"] for d in plan}
    allowed_channels = [c.lower() for c in (extras.get("channels") or [])]
    holidays = {h["date"]: h["name"] for h in extras.get("holidays_in_range", [])}
    issues: List[Dict[str, str]] = []
    rows = []
    for row in data.get("rows") or []:
        if row.get("date") not in allowed_dates:
            continue
        if allowed_channels and str(row.get("channel", "")).lower() not in allowed_channels:
            issues.append({"code": "CAL", "message": f"Bỏ dòng ngày {row.get('date')}: kênh \"{row.get('channel')}\" không có trong hồ sơ."})
            continue
        row["holiday"] = holidays.get(row["date"], "")
        rows.append(row)
    rows.sort(key=lambda r: (r["date"], r.get("channel", "")))
    covered = {r["date"] for r in rows}
    missing = sorted(allowed_dates - covered)
    if missing:
        issues.append({"code": "CAL", "message": f"{len(missing)} ngày chưa có bài: {', '.join(missing[:6])}{'…' if len(missing) > 6 else ''}."})
    if rows:
        counts = {k: sum(1 for r in rows if r.get("intent") == k) for k in ("findable", "shareable", "experiment")}
        pct = {k: round(v * 100 / len(rows)) for k, v in counts.items()}
        target = {"findable": 60, "shareable": 30, "experiment": 10}
        data["mix"] = pct
        off = [k for k in target if abs(pct[k] - target[k]) > 10]
        if off:
            issues.append({"code": "MIX", "message": f"Tỉ lệ tìm được/chia sẻ được/thử nghiệm là {pct['findable']}/{pct['shareable']}/"
                                                     f"{pct['experiment']} — lệch quá 10 điểm so với 60/30/10."})
    data["rows"] = rows
    return data, issues


def _post_ads(data, inputs, ctx, extras):
    platform = inputs.get("platform", "META")
    objective = inputs.get("objective", "")
    offer = inputs.get("offer", "") or "NoOffer"
    period = inputs.get("period_tag") or _quarter_tag(date.today())
    daily = float(inputs.get("daily_budget_vnd") or 0)
    days = int(inputs.get("days") or 14)
    total = daily * days
    camp = data.get("campaign") or {}
    camp["name"] = metrics.ad_name(platform=platform, objective=objective,
                                   audience=camp.get("audience_label") or "Broad", offer=offer, period=period)
    data["campaign"] = camp
    adsets = data.get("adsets") or []
    proven = [a for a in adsets if "70" in str(a.get("role", ""))]
    tests = [a for a in adsets if "30" in str(a.get("role", ""))]
    for group, share in ((proven, 0.7), (tests, 0.3)):
        for a in group:
            a["daily_budget_vnd"] = round(daily * share / len(group)) if group else 0
            a["name"] = metrics.ad_name(platform=platform, objective=objective, audience=a.get("name_audience") or a.get("audience", ""),
                                        offer=offer, period=period)
    if adsets and (not proven or not tests):
        for a in adsets:
            a["daily_budget_vnd"] = round(daily / len(adsets))
            a.setdefault("name", metrics.ad_name(platform=platform, objective=objective,
                                                 audience=a.get("name_audience") or "", offer=offer, period=period))
    est = inputs.get("cost_per_result_estimate_vnd")
    kpi: Dict[str, Any] = {"total_budget_vnd": round(total), "days": days}
    if est:
        try:
            est_f = float(est)
            if est_f > 0:
                kpi["expected_results"] = math.floor(total / est_f)
                kpi["basis"] = f"[Inference] {round(total):,} đ ÷ {est_f:,.0f} đ/kết quả (chi phí bạn nhập)".replace(",", ".")
        except (TypeError, ValueError):
            pass
    if "expected_results" not in kpi:
        kpi["basis"] = "[THIẾU DỮ LIỆU] Nhập chi phí dự kiến cho mỗi kết quả (lấy từ lịch sử tài khoản) để suy ra KPI."
    data["kpi"] = kpi
    data["operating_rules"] = [
        "Giai đoạn test 2–4 tuần: 70% ngân sách cho nhóm đã chứng minh, 30% cho tệp/creative mới.",
        "Khi scale: mỗi lần tăng ~20% ngân sách, chờ 3–5 ngày rồi mới tăng tiếp.",
        "Mỗi tuần làm mới creative; tắt mẫu kém nhất sau khi đủ dữ liệu, không tắt sớm.",
        "Loại trừ khách vừa mua khỏi tệp remarketing.",
    ]
    issues = []
    n_variants = sum(len(a.get("variants") or []) for a in data.get("angles") or [])
    if len(data.get("angles") or []) < 3:
        issues.append({"code": "ADS", "message": "Nên có ít nhất 3 góc tiếp cận."})
    if n_variants < 9:
        issues.append({"code": "ADS", "message": f"Mới có {n_variants} biến thể; chuẩn là 3–5 góc × 3 biến thể."})
    return data, issues


def _quarter_tag(d: date) -> str:
    return f"{d.year}Q{(d.month - 1) // 3 + 1}"


def _post_plan(data, inputs, ctx, extras):
    from app.guardrails import check_kpis
    return data, check_kpis(data.get("kpis") or [])


def _post_budget(data, inputs, ctx, extras):
    from app.guardrails import check_budget_lines
    total_cap = float(inputs.get("total_budget_vnd") or 0)
    lines = data.get("lines") or []
    for line in lines:
        try:
            line["projected_total"] = round(float(line.get("unit_price") or 0) * float(line.get("quantity") or 0))
        except (TypeError, ValueError):
            line["projected_total"] = 0
    total = sum(l["projected_total"] for l in lines)
    data["total_projected"] = total
    issues = check_budget_lines(lines)
    if total_cap and total > total_cap * 1.001:
        issues.append({"code": "G08", "message": f"Tổng dự kiến {total:,.0f} đ vượt ngân sách {total_cap:,.0f} đ.".replace(",", ".")})
    return data, issues


def _post_voc(data, inputs, ctx, extras):
    lines = extras.get("lines") or []
    sources = extras.get("line_sources") or []
    n = len(lines)
    issues: List[Dict[str, str]] = []
    raw_low = "\n".join(lines).lower()

    def conf(evidence: List[int]) -> str:
        valid = [i for i in evidence if isinstance(i, int) and 1 <= i <= n]
        distinct = {sources[i - 1] or f"dòng {i}" for i in valid}
        return "Cao" if len(distinct) >= 3 else "Trung bình" if len(distinct) == 2 else "Thấp" if distinct else "Không có bằng chứng"

    for key in ("jtbd", "pains", "triggers", "desired_outcomes", "alternatives"):
        kept = []
        for item in data.get(key) or []:
            ev = [i for i in (item.get("evidence_lines") or []) if isinstance(i, int) and 1 <= i <= n]
            if not ev:
                continue
            item["evidence_lines"] = ev
            item["confidence"] = conf(ev)
            kept.append(item)
        data[key] = kept
    quotes = []
    for q in data.get("verbatim_quotes") or []:
        text = str(q.get("quote", "")).strip().strip('"“”')
        if text and text.lower() in raw_low:
            quotes.append({"quote": text, "line": q.get("line")})
    dropped = len(data.get("verbatim_quotes") or []) - len(quotes)
    if dropped:
        issues.append({"code": "VOC", "message": f"Bỏ {dropped} câu \"nguyên văn\" không tìm thấy trong dữ liệu bạn dán."})
    data["verbatim_quotes"] = quotes
    persona = data.get("persona") or {}
    if n < 5:
        persona = {"allowed": False, "summary": f"Mới có {n} điểm dữ liệu. Skill yêu cầu tối thiểu 5 điểm dữ liệu cho một phân khúc trước khi lập persona."}
    data["persona"] = persona
    data["data_points"] = n
    return data, issues


DONT_SAY = ["tôi xin lỗi.", "chắc là có sự hiểu lầm", "lỗi sai của anh", "lỗi sai của chị", "thật không may",
            "cứ để tôi xem", "giữ máy nhé", "không có thông tin đơn", "việc đó tôi không làm được"]


def _post_complaint(data, inputs, ctx, extras):
    reply = str(data.get("reply", "")).lower()
    hits = [p for p in DONT_SAY if p in reply]
    data["avoid_phrases_found"] = hits
    issues = [{"code": "CSKH", "message": f"Câu trả lời còn cụm \"{h}\" thuộc danh sách \"đừng nói\"."} for h in hits]
    return data, issues


def _post_lifecycle(data, inputs, ctx, extras):
    issues = []
    msgs = sorted(data.get("messages") or [], key=lambda m: int(m.get("day") or 0))
    data["messages"] = msgs
    channel = inputs.get("channel", "Email")
    for m in msgs:
        subject = str(m.get("subject", ""))
        if channel == "Email" and subject and not (30 <= len(subject) <= 70):
            issues.append({"code": "MAIL", "message": f"Tiêu đề ngày {m.get('day')} dài {len(subject)} ký tự (nên ~40–60)."})
        if channel == "SMS":
            body = str(m.get("body", ""))
            segments = math.ceil(len(body) / 67) if any(ord(c) > 127 for c in body) else math.ceil(len(body) / 153)
            m["sms_segments"] = segments
            if segments > 2:
                issues.append({"code": "SMS", "message": f"Tin ngày {m.get('day')} tốn {segments} tin SMS (tiếng Việt có dấu ~70 ký tự/tin)."})
    data["consent_rule"] = "Chỉ gửi cho khách đã đồng ý nhận tin tiếp thị; mọi tin có cách từ chối (Luật 91/2025/QH15)."
    return data, issues


DISCLOSURE_CLAUSE = ("Ghi rõ \"Quảng cáo\" hoặc \"Được tài trợ bởi [thương hiệu]\" ở đầu nội dung và trong suốt video/bài đăng, "
                     "bật nhãn nội dung có trả phí của nền tảng (Luật 75/2025/QH15).")


def _post_kol(data, inputs, ctx, extras):
    brief = data.get("brief") or {}
    req = str(brief.get("disclosure_requirement", ""))
    if "quảng cáo" not in req.lower() and "tài trợ" not in req.lower():
        brief["disclosure_requirement"] = DISCLOSURE_CLAUSE + (" " + req if req else "")
    data["brief"] = brief
    checklist = list(data.get("checklist") or [])
    must = ["KOL đã dùng thật hoặc hiểu rõ sản phẩm trước khi nhận quảng cáo",
            "KOL đã kiểm tra tư cách pháp lý và giấy tờ sản phẩm của nhà quảng cáo",
            "Hợp đồng có điều khoản công khai quảng cáo và trách nhiệm khi thông tin sai"]
    for m in must:
        if m not in checklist:
            checklist.append(m)
    data["checklist"] = checklist
    issues = []
    if not inputs.get("product_used"):
        issues.append({"code": "KOL", "message": "Chưa xác nhận KOL đã dùng sản phẩm — Luật 75/2025/QH15 yêu cầu KOL dùng hoặc hiểu rõ sản phẩm."})
    from app.guardrails import check_kpis
    return data, issues + check_kpis(data.get("kpis") or [])


def _post_grounded_points(data, inputs, ctx, extras):
    """Gắn lại nhãn cho từng ý: 'Có nguồn' mà không có source_id hợp lệ → [Unverified]."""
    n_sources = len(extras.get("sources") or [])
    fixed = 0

    def fix(point: Dict[str, Any]) -> None:
        nonlocal fixed
        ids = [i for i in (point.get("source_ids") or []) if isinstance(i, int) and 1 <= i <= n_sources]
        point["source_ids"] = ids
        if point.get("tag") == "Có nguồn" and not ids:
            point["tag"] = "[Unverified]"
            fixed += 1

    def walk(v: Any) -> None:
        if isinstance(v, dict):
            if "tag" in v and "source_ids" in v:
                fix(v)
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)

    walk(data)
    issues = [{"code": "SRC", "message": f"{fixed} ý ghi \"Có nguồn\" nhưng không trỏ tới nguồn nào — đã đổi thành [Unverified]."}] if fixed else []
    return data, issues


def _post_discovery(data, inputs, ctx, extras):
    sources = extras.get("sources") or []
    n_sources = len(sources)
    known = [k.lower() for k in extras.get("known_competitors") or []]
    kept, dropped = [], 0
    for c in data.get("competitors") or []:
        name = str(c.get("name") or "").strip()
        if not name or len(name) < 2:
            dropped += 1
            continue
        ids = [i for i in (c.get("source_ids") or []) if isinstance(i, int) and 1 <= i <= n_sources]

        # 1. Nếu chưa có source_ids hợp lệ, đối chiếu tên quán/thương hiệu hoặc website với nguồn tìm kiếm
        if not ids and n_sources > 0:
            name_low = name.lower()
            web_low = str(c.get("website") or "").lower().replace("https://", "").replace("http://", "").replace("www.", "").strip("/")
            for i, s in enumerate(sources, 1):
                s_text = (str(s.get("title") or "") + " " + str(s.get("url") or "")).lower()
                if (name_low in s_text) or (web_low and len(web_low) > 4 and web_low in s_text):
                    ids.append(i)

        is_known = name.lower() in known
        has_web = bool(str(c.get("website") or "").strip())
        has_details = bool(str(c.get("what_they_sell") or "").strip()) or bool(str(c.get("price_info") or "").strip())

        if not n_sources:
            # Không có nguồn ngoài -> giữ nguyên
            c["source_ids"] = ids
            kept.append(c)
        elif ids or is_known:
            c["source_ids"] = ids
            kept.append(c)
        elif has_web:
            # Có website chứng minh sự tồn tại -> gán nguồn tìm kiếm [1] nếu có sources
            ids = [1] if n_sources > 0 else []
            c["source_ids"] = ids
            kept.append(c)
        elif has_details and n_sources > 0:
            # Có sản phẩm/giá cụ thể từ kết quả tìm kiếm Google Grounding / DDG nhưng AI quên gắn source_ids
            ids = [1]
            c["source_ids"] = ids
            kept.append(c)
        else:
            dropped += 1
    data["competitors"] = kept
    issues = [{"code": "SRC", "message": f"Bỏ {dropped} đối thủ không có nguồn chứng minh."}] if dropped else []
    return data, issues


def _post_weekly(data, inputs, ctx, extras):
    diag = (extras.get("funnel") or {}).get("bottleneck")
    issues = []
    if diag:
        stage = f"{diag['from']} → {diag['to']}"
        if data.get("bottleneck_stage") != stage:
            data["bottleneck_stage"] = stage
            issues.append({"code": "CALC", "message": f"Nút thắt lấy theo số liệu thật: {stage} ({diag['rate_pct']}%)."})
    return data, issues


def _post_event(data, inputs, ctx, extras):
    data["metric_formula"] = "Chi phí mỗi cuộc gặp chất lượng = tổng chi phí sự kiện ÷ số cuộc gặp chất lượng (không dùng số người đăng ký)."
    return data, []


# ---------------------------------------------------------------------------
# Danh mục
# ---------------------------------------------------------------------------

GROUPS = ["Chiến lược", "Ưu đãi & Nội dung", "Quảng cáo", "Khách hàng & Bán hàng", "Giữ chân", "SEO & Local", "PR & KOL", "Đo lường"]

TASKS: Dict[str, Task] = {}


def _add(task: Task) -> None:
    task.schema = with_common(task.schema)
    TASKS[task.id] = task


_add(Task(
    id="marketing_plan", group="Chiến lược", module="M2", title="Kế hoạch marketing 90 ngày",
    description="Kế hoạch theo AARRR, lộ trình 90 ngày 4 chặng, phân bổ 70/20/10, kiểm ORB và KPI suy từ phễu.",
    sections=["1", "3", "4", "13", "17"],
    inputs=[inp("plan_type", "Loại kế hoạch", "select", True, options=["Bản gọn (shop/SME)", "Bản đầy đủ 13 phần"]),
            inp("start_date", "Ngày bắt đầu", "date", True),
            inp("notes", "Bối cảnh thêm", "textarea", placeholder="Vấn đề đang gặp, nguồn lực, điều đã thử…")],
    required_context=["product.one_liner", "customers.buyer", "goals.business_goal", "channels_active"],
    schema=O({
        "executive_summary": O({"big_bets": A(S, 1, 3), "priorities_90d": A(S), "outcome_12m": S}),
        "market_quality": O({"magnitude": E("lớn", "vừa", "nhỏ"), "frequency": E("thường xuyên", "thỉnh thoảng", "hiếm"), "verdict": S}),
        "key_message": S,
        "aarrr": A(O({"stage": E("Acquisition", "Activation", "Retention", "Referral", "Revenue"), "running": A(S), "will_run": A(S),
                      "skip": A(O({"channel": S, "reason": S}))})),
        "roadmap": A(O({"phase": E("Tuần 1–2: gỡ nút thắt", "Tuần 3–4: nền móng", "Tuần 5–8: tăng tốc", "Tuần 9–12: cộng dồn"),
                        "actions": A(O({"action": S, "aarrr_stage": S, "owner": S, "due": S, "kpi": S, "mechanism": S}))})),
        "allocation": O({"proven_70": A(S), "next_20": A(S), "experiments_10": A(S)}),
        "orb_check": A(O({"flow": S, "leads_to_owned": B, "fix": S})),
        "kpis": A(KPI),
        "measurement": O({"north_star": S, "leading": A(O({"stage": S, "metric": S}))}),
        "open_decisions": A(S),
    }),
    instructions=("Lập kế hoạch marketing cho 90 ngày kể từ ngày bắt đầu. Dựa vào số liệu phễu và kết quả thật trong DỮ LIỆU THÊM. "
                  "Chấm cổng chất lượng thị trường thẳng thắn. KPI phải SMART và có công thức suy từ phễu; hạn là ngày cụ thể. "
                  "Mỗi hành động có người phụ trách (dùng vai trò nếu chưa biết tên, ví dụ \"Chủ quán\"). Không đề xuất kênh ngoài hồ sơ trừ khi giải thích lý do."),
    extras="plan", post=_post_plan, temperature=0.4,
))

_add(Task(
    id="marketing_ideas", group="Chiến lược", module="M2", title="Ý tưởng marketing theo giai đoạn & ngân sách",
    description="10 ý tưởng hợp giai đoạn và mức ngân sách, mỗi ý có cơ chế, chỉ số dẫn dắt và điều kiện dừng.",
    sections=["3", "4", "9"],
    inputs=[inp("stage", "Giai đoạn", "select", True, options=["Trước ra mắt", "Giai đoạn đầu", "Tăng trưởng"]),
            inp("budget_level", "Mức ngân sách", "select", True, options=["0 đồng", "Ít tiền", "Vừa"]),
            inp("focus", "Muốn cải thiện điều gì", "text", placeholder="Ví dụ: khách quay lại")],
    required_context=["product.one_liner", "customers.buyer"],
    schema=O({"ideas": A(O({"idea": S, "aarrr_stage": S, "mechanism": S, "leading_metric": S, "stop_condition": S,
                             "cost_level": S, "time_to_impact": E("nhanh", "trung hạn", "dài hạn"), "first_step": S}), 5, 12)}),
    instructions="Đề xuất ý tưởng phù hợp giai đoạn và ngân sách. Ưu tiên ý tưởng tạo tài sản cộng dồn và dẫn về kênh sở hữu.",
    temperature=0.8,
))

_add(Task(
    id="launch_plan", group="Chiến lược", module="M2", title="Kế hoạch ra mắt (ORB + SLC)",
    description="Ra mắt sản phẩm/món mới: kiểm SLC, kênh Owned–Rented–Borrowed, lịch 4 tuần, KPI.",
    sections=["3", "9", "12", "14"],
    inputs=[inp("product_name", "Sản phẩm ra mắt", "text", True), inp("launch_date", "Ngày ra mắt", "date", True),
            inp("what_is_new", "Điểm mới", "textarea", True), inp("budget_vnd", "Ngân sách (VND)", "number")],
    required_context=["customers.buyer", "channels_active"],
    schema=O({"slc_check": O({"simple": S, "lovable": S, "complete": S, "ready": B}),
              "owned": A(S), "rented": A(S), "borrowed": A(S),
              "timeline": A(O({"week": S, "actions": A(S)})), "kpis": A(KPI), "risks": A(S)}),
    instructions="Mọi luồng phải dẫn về kênh sở hữu (Owned). Nếu chưa đạt SLC thì nói rõ cần làm gì trước.",
    extras=None, post=_post_plan,
))

_add(Task(
    id="offer_lab", group="Ưu đãi & Nội dung", module="M4", title="Offer Lab — chẩn đoán ưu đãi",
    description="Phương trình giá trị Hormozi: chấm 4 đòn bẩy, kiểm 6 thành phần, chỉ sửa đòn bẩy yếu nhất.",
    sections=["1", "5.3", "6", "14"],
    inputs=[inp("offer_current", "Ưu đãi hiện tại", "textarea", True, placeholder="Viết như đang nói với khách: mua gì, được gì, giá bao nhiêu, điều kiện"),
            inp("product_focus", "Sản phẩm áp dụng", "text"),
            inp("scarcity_evidence", "Giới hạn có thật (nếu có)", "textarea", help="Ví dụ: chỉ có 50 hộp vì lô hàng giới hạn. Để trống nếu không có.")],
    required_context=["product.one_liner", "customers.buyer", "problem.core"],
    schema=O({
        "plain_rewrite": S,
        "levers": A(O({"name": E("Kết quả mơ ước", "Khả năng đạt được cảm nhận", "Thời gian chờ", "Công sức/hy sinh"),
                       "score": I, "reason": S}), 4, 4),
        "components": A(O({"name": E("Sản phẩm lõi", "Quà/bonus", "Cam kết/bảo hành", "Lý do mua ngay", "Tên gọi", "Giá và cách trả"),
                           "present": B, "comment": S}), 6, 6),
        "weakest_lever": S,
        "fix": O({"change": S, "why": S, "new_offer_copy": S, "how_to_test": S}),
        "expected_lift": O({"range": S, "label": S}),
        "risks": A(S),
    }),
    instructions=("Chẩn đoán ưu đãi theo vòng chẩn đoán của mục 6. Điểm 10 là tốt nhất (với Thời gian chờ và Công sức, 10 nghĩa là rất nhanh, rất dễ). "
                  "Chỉ đề xuất sửa MỘT đòn bẩy yếu nhất. Ưu đãi mới không được có khan hiếm nếu không có giới hạn thật, không bonus thổi phồng."),
    kind="offer_copy", post=_post_offer, temperature=0.5,
))

_add(Task(
    id="copy_studio", group="Ưu đãi & Nội dung", module="M5", title="Copy Studio — viết bài, kịch bản, landing",
    description="2–3 phương án tiêu đề, hook, thân bài, CTA kèm lý do; chọn công thức PAS/BAB/kể chuyện 7 bước.",
    sections=["1", "5.3", "7", "8.4", "14"],
    inputs=[inp("channel", "Kênh", "select", True, options=list(CHANNEL_KIND)),
            inp("topic", "Chủ đề / thông điệp", "textarea", True),
            inp("formula", "Công thức", "select", options=["Tự chọn phù hợp", "PAS", "BAB", "Kể chuyện 7 bước", "Landing page"]),
            inp("goal", "Mục tiêu", "select", options=["Nhận biết", "Tương tác", "Tin nhắn/lead", "Đơn hàng", "Quay lại mua"]),
            inp("emotion", "Tử huyệt cảm xúc", "select", options=["Tự chọn", "Yêu thương", "Tiền bạc", "Danh vọng", "Bản thân"]),
            inp("offer", "Ưu đãi kèm theo (nếu có)", "text"),
            inp("scarcity_evidence", "Giới hạn có thật (nếu có)", "text"),
            inp("length", "Độ dài", "select", options=["Ngắn", "Vừa", "Dài"])],
    required_context=["product.one_liner", "customers.buyer"],
    schema=O({
        "formula_used": S, "emotion_used": S,
        "variants": A(O({"headline": S, "hook": S, "hook_type": E("Tò mò", "Câu chuyện", "Giá trị", "Ngược dòng"),
                         "body": S, "cta": S, "rationale": S}), 2, 3),
        "recommended": I, "visual_brief": S, "hashtags": A(S), "claims_to_verify": A(S),
    }),
    instructions=("Viết 2–3 phương án khác nhau thật sự (khác góc, khác hook). Dùng ngôn ngữ khách trong hồ sơ. "
                  "CTA = động từ + thứ khách nhận. Chỉ dùng bằng chứng có \"ĐƯỢC phép dùng công khai\". "
                  "Với kịch bản video: 3 giây đầu có móc hình + móc lời + chữ trên màn hình; ghi rõ phân cảnh. "
                  "Ghi vào claims_to_verify mọi khẳng định cần chủ doanh nghiệp xác nhận."),
    kind=lambda i: CHANNEL_KIND.get(i.get("channel", ""), "post"), post=_post_copy, temperature=0.85,
))

_add(Task(
    id="copy_edit", group="Ưu đãi & Nội dung", module="M5", title="Biên tập 7 lượt",
    description="Rõ ràng → giọng điệu → \"thì sao?\" → chứng minh → cụ thể → cảm xúc → không rủi ro.",
    sections=["5.3", "7", "14"],
    inputs=[inp("text", "Bài cần biên tập", "textarea", True), inp("channel", "Kênh", "select", options=list(CHANNEL_KIND))],
    schema=O({"passes": A(O({"name": S, "issues": A(S), "changes": A(S)}), 7, 7), "final_text": S, "cta_check": S}),
    instructions="Biên tập đúng 7 lượt theo thứ tự mục 7.5. Giữ ý chính của tác giả; không thêm số liệu hay cam kết mới.",
    kind=lambda i: CHANNEL_KIND.get(i.get("channel", ""), "post"), temperature=0.4,
))

_add(Task(
    id="content_pillars", group="Ưu đãi & Nội dung", module="M6", title="Trụ cột nội dung",
    description="3–5 trụ cột có tỉ lệ, gắn giai đoạn mua và từ khóa; chuẩn hóa tổng 100%.",
    sections=["1", "8"],
    inputs=[inp("notes", "Ghi chú", "textarea", placeholder="Nội dung đang làm tốt/kém, đối thủ hay đăng gì…")],
    required_context=["product.one_liner", "customers.buyer", "channels_active"],
    schema=O({"pillars": A(O({"name": S, "share_pct": N, "purpose": S, "findable_or_shareable": E("tìm được", "chia sẻ được", "cả hai"),
                               "funnel_stage": S, "example_topics": A(S), "search_keywords": A(S)}), 3, 5), "mix_note": S}),
    instructions="Trụ cột phải gắn với sản phẩm, khách và nhu cầu tìm kiếm. Từ khóa là gợi ý [Inference], không kèm lượng tìm kiếm.",
    post=_post_pillars, temperature=0.6,
))

_add(Task(
    id="content_atomize", group="Ưu đãi & Nội dung", module="M6", title="Chia nhỏ bài trụ cột",
    description="Một bài trụ cột thành 5–10 mẩu nội dung cho từng kênh.",
    sections=["7", "8"],
    inputs=[inp("source_text", "Bài trụ cột", "textarea", True), inp("channels", "Kênh", "multiselect", True, options="channels")],
    schema=O({"atoms": A(O({"channel": S, "format": S, "angle": S, "text": S}), 5, 10)}),
    instructions="Mỗi mẩu đứng được một mình, dẫn về kênh sở hữu. Không thêm thông tin không có trong bài gốc.",
    kind="post", temperature=0.7,
))

_add(Task(
    id="ads_plan", group="Quảng cáo", module="M7", title="Ads Studio — bộ quảng cáo",
    description="Cấu trúc chiến dịch, tên theo quy ước, 3–5 góc × 3 biến thể, remarketing theo tầng, KPI suy từ ngân sách.",
    sections=["1", "5.3", "7.2", "10", "13", "14"],
    inputs=[inp("platform", "Nền tảng", "select", True, options=["META", "GOOGLE", "TIKTOK", "ZALO"]),
            inp("objective", "Mục tiêu", "select", True, options=["Tin nhắn", "Lead", "Đơn hàng", "Lượt truy cập", "Nhận biết"]),
            inp("daily_budget_vnd", "Ngân sách/ngày (VND)", "number", True), inp("days", "Số ngày chạy", "number", default=14),
            inp("audience_note", "Tệp khách", "textarea", placeholder="Khu vực, độ tuổi, sở thích (dùng công cụ nhắm mục tiêu chính thức)"),
            inp("offer", "Ưu đãi", "text"),
            inp("cost_per_result_estimate_vnd", "Chi phí dự kiến/kết quả (VND)", "number", help="Lấy từ lịch sử tài khoản. Để trống nếu chưa biết."),
            inp("scarcity_evidence", "Giới hạn có thật (nếu có)", "text"),
            inp("period_tag", "Nhãn thời gian", "text", placeholder="Ví dụ 2026Q4")],
    required_context=["product.one_liner", "customers.buyer"],
    schema=O({
        "campaign": O({"objective": S, "audience_label": S, "offer_label": S}),
        "adsets": A(O({"name_audience": S, "audience": S, "role": E("đã chứng minh (70%)", "thử nghiệm (30%)"), "exclusions": A(S)}), 2, 4),
        "angles": A(O({"angle": E("nỗi đau", "kết quả", "bằng chứng xã hội", "tò mò", "so sánh", "khẩn cấp có thật", "danh tính", "ngược dòng"),
                       "why": S, "variants": A(O({"headline": S, "primary_text": S, "visual_brief": S, "cta": S}), 3, 3)}), 3, 5),
        "remarketing": A(O({"stage": S, "audience": S, "message": S, "offer": S, "exclusions": A(S)})),
        "test_plan": S,
    }),
    instructions=("Lập bộ quảng cáo đúng mục 10. Chèn từ khóa danh tính vào tiêu đề. Quảng cáo không trông giống quảng cáo. "
                  "Góc \"khẩn cấp có thật\" chỉ dùng khi có giới hạn thật. Không nhắm mục tiêu bằng dữ liệu cào. "
                  "Nhóm \"đã chứng minh\" là tệp/creative đã có kết quả; nếu chưa có lịch sử, ghi rõ đó là giả định."),
    kind="ad", post=_post_ads, temperature=0.8,
))

_add(Task(
    id="budget_plan", group="Đo lường", module="M11", title="Lập ngân sách tháng",
    description="Chia ngân sách theo 7 chương trình, tự nhân lại đơn giá × số lượng, KPI suy từ phễu.",
    sections=["3.3", "13"],
    inputs=[inp("month", "Tháng (YYYY-MM)", "text", True), inp("total_budget_vnd", "Tổng ngân sách (VND)", "number", True),
            inp("priorities", "Ưu tiên", "textarea")],
    required_context=["channels_active"],
    schema=O({"lines": A(O({"program": E("Quảng cáo trả phí", "Content", "Sự kiện", "PR", "Branding & Creative", "Product Marketing", "Khác"),
                             "item": S, "unit_price": N, "unit": S, "quantity": N, "kpi_formula": S}), 1, 20),
              "allocation_note": S}),
    instructions="Đơn vị phải đúng (VND/ngày × số ngày, VND/tháng × 1). Tổng không vượt ngân sách. KPI có công thức từ chi phí dự kiến; chi phí chưa biết thì ghi [THIẾU DỮ LIỆU].",
    post=_post_budget, temperature=0.3,
))

_add(Task(
    id="voc_extract", group="Khách hàng & Bán hàng", module="M8", title="Tiếng nói khách hàng (VoC) → insight",
    description="Rút JTBD, nỗi đau, sự kiện kích hoạt, câu nguyên văn từ review/inbox thật; persona chỉ khi đủ 5 điểm dữ liệu.",
    sections=["1", "5.1"],
    inputs=[inp("raw_feedback", "Dữ liệu khách", "textarea", True,
                placeholder="Mỗi dòng một ý. Có thể ghi nguồn ở đầu dòng, ví dụ:\nGoogle Maps: Cà phê muối béo vừa, chờ hơi lâu\nInbox: Có giao tới văn phòng không em?"),
            inp("segment", "Phân khúc (nếu muốn tách)", "text")],
    schema=O({
        "jtbd": A(O({"text": S, "type": E("chức năng", "cảm xúc", "xã hội"), "evidence_lines": A(I)})),
        "pains": A(O({"text": S, "evidence_lines": A(I)})),
        "triggers": A(O({"text": S, "evidence_lines": A(I)})),
        "desired_outcomes": A(O({"text": S, "evidence_lines": A(I)})),
        "alternatives": A(O({"text": S, "evidence_lines": A(I)})),
        "verbatim_quotes": A(O({"quote": S, "line": I})),
        "persona": O({"allowed": B, "summary": S}),
    }),
    instructions=("Mỗi nhận định phải trỏ tới số dòng bằng chứng (evidence_lines, đánh số từ 1). Câu nguyên văn phải chép đúng từng chữ. "
                  "Không suy ra điều dữ liệu không nói. Persona chỉ khi có từ 5 điểm dữ liệu trở lên."),
    extras="voc", post=_post_voc, temperature=0.2,
))

_add(Task(
    id="sales_script", group="Khách hàng & Bán hàng", module="M9", title="Kịch bản tư vấn 7 bước",
    description="Kịch bản theo 7 bước, điều chỉnh theo DISC/VAK, ngân hàng phản đối từ hồ sơ và lead đã mất.",
    sections=["1", "5"],
    inputs=[inp("channel", "Kênh tư vấn", "select", True, options=["Gọi điện", "Chat/Inbox", "Tại cửa hàng"]),
            inp("customer_type", "Kiểu khách (DISC)", "select", options=["Chưa rõ", "D – Quyền lực", "I – Ảnh hưởng", "S – Trầm tĩnh", "C – Tuân thủ"]),
            inp("vak", "Kiểu tiếp nhận (VAK)", "select", options=["Chưa rõ", "V – Hình ảnh", "A – Âm thanh", "K – Vận động"]),
            inp("product_focus", "Sản phẩm tư vấn", "text"), inp("situation", "Tình huống", "textarea")],
    required_context=["product.one_liner", "customers.buyer"],
    schema=O({"steps": A(O({"step": S, "goal": S, "lines": A(S)}), 7, 7), "questions_to_ask": A(S),
              "objections": A(O({"objection": S, "response": S, "source": E("hồ sơ", "lead đã mất", "phổ biến [Inference]")})),
              "upsell": S, "downsell": S, "follow_up": S, "adapt_for_type": S}),
    instructions="Bước 2 lấy thông tin phải xin đồng ý rõ ràng. Không ép, không dọa. Testimonial chỉ dùng bằng chứng được phép.",
    extras="sales", temperature=0.6,
))

_add(Task(
    id="complaint_reply", group="Khách hàng & Bán hàng", module="M9", title="Trả lời phàn nàn",
    description="Soạn câu trả lời theo bảng \"đừng nói / hãy nói\" và 5 bước xử lý, kèm việc nội bộ.",
    sections=["5.5"],
    inputs=[inp("complaint", "Lời phàn nàn của khách", "textarea", True), inp("channel", "Kênh", "select", options=["Bình luận công khai", "Tin nhắn riêng", "Đánh giá Google Maps", "Gọi điện"]),
            inp("facts", "Sự thật và cách bạn có thể bù đắp", "textarea", True, help="Ghi đúng chuyện đã xảy ra và điều bạn sẵn sàng làm.")],
    schema=O({"reply": S, "tone_notes": A(S), "internal_actions": A(O({"step": S, "owner": S, "due": S})), "follow_up_at": S, "avoid_phrases_found": A(S)}),
    instructions="Xin lỗi cụ thể, nhận phần lỗi có thật, đưa giải pháp và mốc thời gian. Không hứa điều ngoài phần \"Sự thật và cách bù đắp\".",
    kind="review_reply", post=_post_complaint, temperature=0.4,
))

_add(Task(
    id="lifecycle_flow", group="Giữ chân", module="M10", title="Chuỗi chăm sóc Email / Zalo / SMS",
    description="Chuỗi chào mừng, nuôi lead, kích hoạt lại, sau mua, giới thiệu; chỉ gửi cho người đã đồng ý.",
    sections=["4.1", "12", "14"],
    inputs=[inp("flow", "Loại chuỗi", "select", True, options=["Chào mừng", "Nuôi lead", "Kích hoạt lại", "Sau mua (mua lần 2)", "Giới thiệu bạn bè"]),
            inp("channel", "Kênh", "select", True, options=["Email", "Zalo OA", "SMS"]),
            inp("lead_magnet", "Mồi/quà ban đầu", "text"), inp("offer", "Ưu đãi (nếu có)", "text")],
    required_context=["product.one_liner", "customers.buyer"],
    schema=O({"flow_name": S, "audience_rule": S,
              "messages": A(O({"day": I, "subject": S, "preview": S, "body": S, "cta": S, "goal": S}), 3, 8),
              "exit_conditions": A(S),
              "referral_program": O({"trigger": S, "mechanism": S, "reward_referrer": S, "reward_friend": S, "reward_timing": S})}),
    instructions=("Số lượng và nhịp theo mục 12.3. Mỗi tin một việc, một CTA, có cách từ chối nhận tin. "
                  "Chương trình giới thiệu: thưởng khi khách mới mua, thưởng bằng số tiền cho sản phẩm giá thấp. Không phải chuỗi giới thiệu thì để referral_program rỗng."),
    kind=lambda i: "sms" if i.get("channel") == "SMS" else "email", post=_post_lifecycle, temperature=0.7,
))

_add(Task(
    id="review_reply", group="SEO & Local", module="M12", title="Trả lời đánh giá Google Maps",
    description="Trả lời đánh giá thật, đúng giọng thương hiệu, có từ khóa địa phương tự nhiên.",
    sections=["5.5", "11.3"],
    inputs=[inp("review", "Nội dung đánh giá", "textarea", True), inp("stars", "Số sao", "select", True, options=["5", "4", "3", "2", "1"]),
            inp("facts", "Thông tin bạn muốn nói thêm", "textarea")],
    schema=O({"reply": S, "internal_note": S}),
    instructions="Ngắn gọn, cảm ơn cụ thể, xử lý điểm chê bằng hành động có thật. Không mời khách xóa/sửa đánh giá, không đổi quà lấy đánh giá.",
    kind="review_reply", temperature=0.5,
))

_add(Task(
    id="answer_first", group="SEO & Local", module="M12", title="Khối trả lời cho AI search",
    description="Câu trả lời trực tiếp 40–60 từ cho một câu hỏi khách hay hỏi, chỉ từ thông tin đã xác nhận.",
    sections=["11.4"],
    inputs=[inp("question", "Câu hỏi", "text", True)],
    required_context=["brand.name", "product.one_liner"],
    schema=O({"answer_40_60": S, "supporting_points": A(S), "facts_needed": A(S)}),
    instructions="Chỉ dùng sự thật trong hồ sơ (kể cả mục FAQ). Thiếu thì ghi [THIẾU DỮ LIỆU] và liệt kê ở facts_needed. Không nhồi từ khóa.",
    kind="faq", temperature=0.3,
))

_add(Task(
    id="keyword_plan", group="SEO & Local", module="M12", title="Cụm từ khóa theo giai đoạn mua",
    description="Từ khóa theo Nhận biết → Cân nhắc → Quyết định → Sử dụng, kèm ý tưởng trang.",
    sections=["8.2", "11"],
    inputs=[inp("seeds", "Chủ đề gốc", "textarea", True)],
    required_context=["product.one_liner", "market.location"],
    schema=O({"clusters": A(O({"stage": E("Nhận biết", "Cân nhắc", "Quyết định", "Sử dụng"), "keywords": A(S), "content_idea": S, "page_type": S}), 4, 8),
              "local_keywords": A(S), "next_step": S}),
    instructions="Từ khóa là gợi ý [Inference]; không đưa ra lượng tìm kiếm. Hướng dẫn kiểm bằng Google Keyword Planner/Search Console.",
    temperature=0.5,
))

_add(Task(
    id="kol_brief", group="PR & KOL", module="M13", title="Brief KOL/KOC đúng luật",
    description="Brief có điều khoản công khai quảng cáo, checklist Luật 75/2025/QH15, KPI SMART.",
    sections=["9.4", "13.4", "14"],
    inputs=[inp("kol_name", "KOL/KOC", "text", True), inp("kol_type", "Loại", "select", options=["KOL", "KOC", "Micro-influencer"]),
            inp("audience_fit", "Tệp người theo dõi của họ", "textarea", True), inp("deliverables", "Sản phẩm bàn giao", "text"),
            inp("budget_vnd", "Ngân sách (VND)", "number"), inp("campaign_goal", "Mục tiêu", "text", True),
            inp("product_used", "KOL đã dùng thật sản phẩm", "checkbox")],
    required_context=["product.one_liner", "customers.buyer"],
    schema=O({"brief": O({"objective": S, "key_message": S, "must_say": A(S), "must_not_say": A(S), "disclosure_requirement": S,
                          "deliverables": A(S), "timeline": S}),
              "fit_assessment": S, "kpis": A(KPI), "contract_clauses": A(S), "checklist": A(S)}),
    instructions="Chọn KOL theo độ khớp tệp khách, không theo số follower. KPI đo tin nhắn/đơn/mã giảm giá riêng, không đo lượt xem làm thành tích.",
    kind="kol_brief", post=_post_kol, temperature=0.5,
))

_add(Task(
    id="event_plan", group="PR & KOL", module="M13", title="Kế hoạch sự kiện (20/80)",
    description="Việc trước – trong – sau sự kiện, follow-up 24–48 giờ, đo chi phí mỗi cuộc gặp chất lượng.",
    sections=["9.4", "13.1"],
    inputs=[inp("event", "Sự kiện", "text", True), inp("date", "Ngày", "date", True), inp("goal", "Mục tiêu", "text", True),
            inp("budget_vnd", "Ngân sách (VND)", "number")],
    schema=O({"before": A(O({"task": S, "due": S, "owner": S})), "during": A(O({"task": S, "owner": S})),
              "after": A(O({"task": S, "due": S, "owner": S})), "follow_up_template": S, "quality_meeting_definition": S, "kpis": A(KPI)}),
    instructions="80% công sức là trước và sau. Follow-up trong 24–48 giờ.",
    post=_post_event, temperature=0.5,
))

_add(Task(
    id="pr_pitch", group="PR & KOL", module="M13", title="Góc PR & thư mời báo chí",
    description="Chọn góc kể chuyện, tiêu đề, thư pitch, khung thông cáo và media kit.",
    sections=["9.4", "14"],
    inputs=[inp("news_hook", "Câu chuyện/tin", "textarea", True),
            inp("angle", "Góc kể", "select", options=["Tự chọn", "Câu chuyện khởi nghiệp", "David và Goliath", "Có kẻ thù chung", "Dữ liệu/xu hướng"]),
            inp("target_media", "Báo/kênh nhắm tới", "text")],
    required_context=["brand.name", "product.one_liner"],
    schema=O({"angle_rationale": S, "headline_options": A(S, 2, 4), "pitch_email": O({"subject": S, "body": S}),
              "press_release_outline": A(S), "media_kit_checklist": A(S), "proof_needed": A(S)}),
    instructions="Câu chuyện là xu hướng, dữ liệu, xung đột hoặc con người; sản phẩm là bằng chứng. Không phóng đại.",
    kind="pr", temperature=0.7,
))

_add(Task(
    id="weekly_loop", group="Đo lường", module="M15", title="Vòng lặp tuần: nút thắt → 1 thử nghiệm",
    description="Đọc số thật, chỉ ra tầng nghẽn nhất, đề xuất đúng một thử nghiệm có điều kiện dừng; góc nhìn hội đồng.",
    sections=["4.3", "10.5", "13.4"],
    inputs=[inp("notes", "Điều xảy ra tuần qua", "textarea")],
    schema=O({"bottleneck_stage": S, "evidence": S,
              "experiment": O({"title": S, "hypothesis": S, "change": S, "primary_metric": S, "guardrail_metric": S,
                               "sample_or_duration": S, "stop_condition": S}),
              "quick_actions": A(S, 1, 3),
              "council": A(O({"lens": E("Ogilvy – thông điệp", "Hormozi – ưu đãi", "Dunford – định vị", "Godin – khác biệt"), "comment": S}), 2, 4)}),
    instructions=("Dựa vào số liệu phễu trong DỮ LIỆU THÊM. Một giả thuyết, một biến số. Nếu chưa đủ dữ liệu thì thử nghiệm đầu tiên là thu thập dữ liệu. "
                  "Phần council là góc nhìn tham khảo theo phong cách từng người, không phải lời trích dẫn."),
    extras="weekly", post=_post_weekly, temperature=0.5,
))

_add(Task(
    id="market_research", group="Chiến lược", module="Research", title="Nghiên cứu thị trường có nguồn",
    description="Tìm kiếm Google thời gian thực; mọi con số có nguồn hoặc nhãn [Unverified]; quy mô thị trường tính bottom-up.",
    sections=["1", "3.1", "15"],
    inputs=[inp("location", "Khu vực", "text", True), inp("objective", "Câu hỏi nghiên cứu", "textarea", True,
                                                         placeholder="Ví dụ: có nên mở thêm điểm bán ở Sơn Trà không?")],
    required_context=["brand.industry", "product.one_liner"],
    schema=O({
        "summary": S,
        "market_size": O({"method": S, "bottom_up_formula": S, "inputs_needed": A(S), "figures": A(O({"label": S, "value": S, "source_ids": A(I),
                                                                                                       "tag": E("Có nguồn", "[Unverified]", "[Inference]")}))}),
        "sections": A(O({"title": E("Chính trị – pháp lý", "Kinh tế", "Xã hội", "Công nghệ", "Cạnh tranh", "Khách hàng", "Xu hướng"),
                         "points": A(POINT)})),
        "swot": O({"strengths": A(POINT), "weaknesses": A(POINT), "opportunities": A(POINT), "threats": A(POINT)}),
        "gtm_4_weeks": A(O({"week": I, "actions": A(S), "kpi": S}), 4, 4),
    }),
    instructions=(
        "Phân tích thị trường chuyên sâu và thực tế cho ngành và khu vực được yêu cầu. "
        "Nếu có BÁO CÁO TÌM KIẾM, ưu tiên trích dẫn dữ liệu và gán source_ids theo DANH SÁCH NGUỒN (gắn nhãn 'Có nguồn'). "
        "Về quy mô thị trường: Đưa ra công thức Bottom-Up cụ thể và ước tính số liệu thực tế dựa trên dung lượng thị trường địa phương (gắn nhãn [Inference]). "
        "Phân tích chi tiết toàn diện cả 7 khía cạnh (Chính trị – pháp lý, Kinh tế, Xã hội, Công nghệ, Cạnh tranh, Khách hàng, Xu hướng) với hiểu biết thị trường Việt Nam thực tế, không để trống hoặc chỉ trả về [THIẾU DỮ LIỆU]. "
        "Điểm mạnh/yếu của doanh nghiệp gắn với hồ sơ bối cảnh."
    ),
    grounded=True, post=_post_grounded_points, temperature=0.3,
))

_add(Task(
    id="competitor_discovery", group="Chiến lược", module="Research", title="Rà soát đối thủ có nguồn",
    description="Tìm đối thủ thật trong khu vực; mỗi đối thủ phải có nguồn chứng minh, không độn danh sách.",
    sections=["1"],
    inputs=[inp("location", "Khu vực", "text", True), inp("criteria", "Tiêu chí", "text", placeholder="Cùng phân khúc giá, cùng khu vực…")],
    required_context=["brand.industry", "product.one_liner"],
    schema=O({"competitors": A(O({"name": S, "type": E("Trực tiếp", "Thứ cấp", "Gián tiếp"), "website": S, "what_they_sell": S,
                                   "price_info": S, "source_ids": A(I)}))}),
    instructions=(
        "Tìm kiếm và liệt kê toàn bộ các đối thủ cạnh tranh có thật trên thị trường tại khu vực được yêu cầu (có bao nhiêu liệt kê bấy nhiêu, không tự giới hạn 3 hay 4 bên; tối thiểu 4–10 đối thủ thuộc các nhóm: Trực tiếp, Thứ cấp, Gián tiếp). "
        "Tận dụng tối đa các đối thủ tìm được từ BÁO CÁO TÌM KIẾM, các đối thủ đã biết trong hồ sơ, và các doanh nghiệp/thương hiệu cơ khí/máy móc/thiết bị có thật trên thị trường Việt Nam mà AI biết. "
        "Với mỗi đối thủ, gán source_ids theo DANH SÁCH NGUỒN nếu có nguồn web; nếu là đối thủ từ tri thức ngành thì ghi rõ địa chỉ/website/sản phẩm thực tế. Tuyệt đối không để danh sách rỗng."
    ),
    grounded=True, extras="discovery", post=_post_discovery, temperature=0.2,
))

_add(Task(
    id="competitor_dossier", group="Chiến lược", module="Research", title="Hồ sơ đối thủ & battlecard trung thực",
    description="Điểm mạnh/yếu có nguồn, nơi mình thắng dựa trên khác biệt thật, kịch bản trả lời khi khách so sánh.",
    sections=["1", "5.4", "14"],
    inputs=[
        inp("competitor_name", "Tên đối thủ", "text", True),
        inp("website", "Website", "text"),
        inp("social", "Mạng xã hội (fanpage/TikTok)", "text"),
        inp("phone", "Số điện thoại", "text"),
        inp("notes", "Bạn biết gì về họ", "textarea"),
    ],
    required_context=["product.one_liner", "differentiation.only_we_have"],
    schema=O({"positioning": S, "products": A(S), "price_info": POINT, "channels": A(S),
              "strengths": A(POINT), "weaknesses": A(POINT), "customer_complaints": A(POINT),
              "where_we_win": A(S), "objection_scripts": A(O({"objection": S, "response": S})), "watch_items": A(S)}),
    instructions=("Điểm yếu và lời phàn nàn chỉ ghi khi có nguồn; không có thì để trống. where_we_win chỉ dựa vào khác biệt thật trong hồ sơ. "
                  "Kịch bản trả lời không được nói xấu đối thủ; tập trung vào giá trị của mình."),
    grounded=True, extras="dossier", post=_post_grounded_points, temperature=0.3,
))

_add(Task(
    id="content_package", group="Ưu đãi & Nội dung", module="M5", title="Gói nội dung: bài + kịch bản video + prompt ảnh",
    description="Một chủ đề thành bài đăng, kịch bản video dọc theo phân cảnh và prompt tạo ảnh.",
    sections=["5.3", "7", "8.4", "14"],
    inputs=[inp("topic", "Chủ đề", "textarea", True), inp("channel", "Kênh chính", "select", True, options=["Facebook", "TikTok", "Zalo OA", "Instagram", "YouTube Shorts"]),
            inp("goal", "Mục tiêu", "select", options=["Nhận biết", "Tương tác", "Tin nhắn/lead", "Đơn hàng"]),
            inp("scarcity_evidence", "Giới hạn có thật (nếu có)", "text")],
    required_context=["product.one_liner", "customers.buyer"],
    schema=O({"headline": S, "body": S, "cta": S, "hashtags": A(S),
              "video_script": A(O({"time": S, "visual": S, "audio": S, "on_screen_text": S}), 3, 8),
              "image_prompt": S, "claims_to_verify": A(S)}),
    instructions="Kịch bản dọc 9:16, 3 giây đầu có móc hình + lời + chữ. Prompt ảnh viết bằng tiếng Anh, mô tả cảnh thật, không chèn chữ, logo hay người nổi tiếng.",
    kind="post", post=_post_copy, temperature=0.8,
))

_add(Task(
    id="content_calendar", group="Ưu đãi & Nội dung", module="M6", title="Lịch nội dung theo ngày thật",
    description="Ngày thật, ngày lễ Việt Nam (âm + dương lịch), đủ 8 cột, tỉ lệ 60/30/10, chỉ kênh trong hồ sơ.",
    sections=["8", "17"],
    inputs=[inp("start_date", "Từ ngày", "date", True), inp("days", "Số ngày (7–31)", "number", True, default=14),
            inp("channels", "Kênh", "multiselect", True, options="channels"), inp("posts_per_day", "Bài/ngày", "number", default=1),
            inp("focus", "Trọng tâm giai đoạn này", "text")],
    required_context=["product.one_liner", "customers.buyer", "channels_active"],
    schema=O({"rows": A(O({"date": S, "channel": S, "pillar": S, "topic": S, "format": S, "hook": S, "cta": S, "metric": S,
                           "intent": E("findable", "shareable", "experiment"),
                           "funnel_stage": E("Nhận biết", "Cân nhắc", "Quyết định", "Sử dụng/Quay lại")}))}),
    instructions=("Điền đúng các ngày trong DANH SÁCH NGÀY, mỗi ngày đúng số bài yêu cầu, chỉ dùng kênh được liệt kê. "
                  "intent: findable (bắt nhu cầu tìm kiếm), shareable (đáng chia sẻ), experiment (thử nghiệm) theo tỉ lệ 60/30/10. "
                  "Ngày lễ chỉ khai thác khi hợp với thương hiệu; chuẩn bị trước đúng số ngày gợi ý. Mục tiêu đo là chỉ số thật (tin nhắn, đơn, lưu, chia sẻ)."),
    extras="calendar", post=_post_calendar, temperature=0.6,
))


def get_task(task_id: str) -> Optional[Task]:
    return TASKS.get(task_id)


def catalog() -> List[Dict[str, Any]]:
    return [t.public() for t in TASKS.values()]
