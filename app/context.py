# -*- coding: utf-8 -*-
"""
Hồ sơ bối cảnh v2 (skill §1) — nguồn sự thật duy nhất cho mọi tác vụ AI.

- 12 mục của skill + kinh tế đơn vị (giá vốn, biên gộp, AOV, chu kỳ mua lại) + thông tin NAP cho Local SEO.
- Có phiên bản và changelog; mỗi lần lưu tạo một bản ghi lịch sử.
- Đo độ đầy đủ; mỗi tác vụ khai báo trường bắt buộc — thiếu thì hỏi, không đoán.
- Không bao giờ chèn giá trị mặc định tự chế vào hồ sơ.
"""
from __future__ import annotations

import copy
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.database import dumps, execute, loads, normalize_email, one, rows

# (path, label, question, hint, priority, kind)
FIELDS: List[Tuple[str, str, str, str, int, str]] = [
    ("brand.name", "Tên thương hiệu", "Tên thương hiệu của bạn là gì?", "Ví dụ: Phê Ly", 1, "text"),
    ("brand.industry", "Ngành", "Bạn kinh doanh ngành gì?", "Ví dụ: Quán cà phê take-away", 1, "text"),
    ("product.one_liner", "Sản phẩm (1 câu)", "Sản phẩm/dịch vụ giúp khách làm được gì? Gói trong một câu.",
     "Ví dụ: Cà phê muối mang đi trong 3 phút cho dân văn phòng quanh Nguyễn Phước Lan", 1, "text"),
    ("product.advantages", "Ưu điểm nổi bật của sản phẩm", "Những ưu điểm, tính năng, điểm vượt trội của sản phẩm/dịch vụ của bạn là gì?",
     "Mỗi dòng một ưu điểm. Ví dụ: Nguyên liệu hữu cơ chứng nhận; giao hàng 15 phút", 1, "list"),
    ("product.shelf_keywords", "Từ khóa khách dùng để tìm", "Khách thường gõ/tìm bạn bằng những từ nào?",
     "Mỗi dòng một từ khóa, ví dụ: cà phê muối đà nẵng", 2, "list"),
    ("product.business_model", "Mô hình kinh doanh", "Bạn bán theo mô hình nào?", "B2C, D2C, B2B, bán sỉ…", 2, "text"),
    ("product.price_points", "Các mức giá chính", "Những sản phẩm/gói chính và giá bán là bao nhiêu?",
     "Mỗi dòng: tên | giá (VND), ví dụ: Cà phê muối | 29000", 1, "price_list"),
    ("unit_economics.avg_order_value_vnd", "Giá trị đơn trung bình (VND)", "Trung bình mỗi đơn khách trả bao nhiêu tiền?",
     "Lấy doanh thu ÷ số đơn của 30 ngày gần nhất", 1, "number"),
    ("unit_economics.gross_margin_pct", "Biên lợi nhuận gộp (%)",
     "Biên lợi nhuận gộp của bạn khoảng bao nhiêu %?",
     "(Doanh thu − giá vốn hàng bán) ÷ doanh thu. Ví dụ ly 30.000đ, nguyên liệu + ly 12.000đ → 60%", 1, "number"),
    ("unit_economics.repeat_purchase_days", "Chu kỳ mua lại (ngày)", "Khách quen thường quay lại sau bao nhiêu ngày?",
     "Ví dụ: 7", 2, "number"),
    ("unit_economics.marketing_fixed_cost_month_vnd", "Chi phí marketing cố định/tháng (VND)",
     "Mỗi tháng tốn bao nhiêu cho lương marketing, công cụ, thuê ngoài (không tính tiền quảng cáo)?",
     "Dùng để tính CAC tổng hợp", 3, "number"),
    ("customers.buyer", "Ai mua", "Ai là người trả tiền mua?", "Mô tả cụ thể: tuổi, nghề, nơi ở, thói quen", 1, "text"),
    ("customers.user", "Ai dùng", "Ai là người trực tiếp dùng (nếu khác người mua)?", "", 3, "text"),
    ("customers.decider", "Ai quyết định", "Ai là người quyết định cuối cùng (nếu khác người mua)?", "", 3, "text"),
    ("customers.jtbd", "Việc khách thuê sản phẩm để làm (JTBD)",
     "Khách \"thuê\" sản phẩm của bạn để làm 2–3 việc gì?",
     "Mỗi dòng một việc, ví dụ: Tỉnh táo cho ca chiều mà không phải ngồi quán lâu", 1, "list"),
    ("customers.segment_traits", "Đặc điểm nhận dạng phân khúc", "Khách mục tiêu sống/làm việc ở đâu, hay lui tới đâu?",
     "Nơi ở, thói quen, sở thích, độ tuổi, thu nhập", 3, "text"),
    ("problem.core", "Vấn đề cốt lõi", "Vấn đề lớn nhất của khách mà bạn giải quyết là gì?", "", 1, "text"),
    ("problem.why_current_fails", "Vì sao cách hiện tại chưa ổn", "Khách đang giải quyết vấn đề đó thế nào, và vì sao chưa ổn?", "", 2, "text"),
    ("problem.cost_of_problem", "Cái giá của vấn đề", "Vấn đề đó làm khách mất gì (tiền, thời gian, cảm xúc)?", "", 2, "text"),
    ("competitors.direct", "Đối thủ trực tiếp", "Ai bán cùng loại sản phẩm cho cùng nhóm khách?", "Mỗi dòng một tên", 2, "list"),
    ("competitors.secondary", "Đối thủ thứ cấp", "Ai giải quyết cùng vấn đề bằng cách khác?", "Mỗi dòng một tên", 3, "list"),
    ("competitors.indirect", "Đối thủ gián tiếp", "Khách có thể chọn làm gì khác hẳn (hoặc không làm gì)?", "", 3, "list"),
    ("differentiation.only_we_have", "Điều chỉ mình có", "Điều gì bạn có mà đối thủ không có?",
     "Chỉ ghi điều có thật và chứng minh được", 1, "text"),
    ("differentiation.why_better", "Vì sao tốt hơn với khách", "Vì sao điều đó tốt hơn cho khách?", "", 2, "text"),
    ("objections", "Lời từ chối hay gặp", "3 lời từ chối khách hay nói và bạn trả lời thế nào?",
     "Mỗi dòng: lời từ chối | cách trả lời", 2, "pair_list"),
    ("anti_persona", "Ai KHÔNG nên là khách", "Ai không phải khách của bạn?", "", 3, "text"),
    ("forces.push", "Lực đẩy", "Khách bực điều gì với cách cũ?", "", 2, "text"),
    ("forces.pull", "Lực kéo", "Điều gì ở bạn hút khách?", "", 2, "text"),
    ("forces.habit", "Thói quen giữ chân", "Thói quen nào khiến khách ngại đổi sang bạn?", "", 3, "text"),
    ("forces.anxiety", "Nỗi lo khi đổi", "Khách sợ gì khi thử bạn lần đầu?", "", 2, "text"),
    ("customer_language.verbatim", "Câu nguyên văn của khách", "Dán vài câu khách đã nói/viết về vấn đề hoặc về bạn.",
     "Mỗi dòng: câu nói | nguồn (inbox, review…)", 2, "quote_list"),
    ("customer_language.use_words", "Từ nên dùng", "Những từ khách hay dùng mà bạn muốn dùng theo?", "Mỗi dòng một từ", 3, "list"),
    ("customer_language.banned_words", "Từ cấm", "Những từ bạn không bao giờ muốn dùng?", "Mỗi dòng một từ", 2, "list"),
    ("brand_voice.tone", "Giọng thương hiệu", "Giọng nói thương hiệu của bạn thế nào?", "Ví dụ: thân mật, hóm hỉnh, không sến", 2, "text"),
    ("brand_voice.traits", "Tính cách thương hiệu", "3–5 tính từ mô tả tính cách thương hiệu?", "Mỗi dòng một tính từ", 2, "list"),
    ("proof", "Bằng chứng có thật", "Bạn có số liệu, review, khách tiêu biểu nào có thật và được phép dùng?",
     "Mỗi dòng: loại (review/số liệu/case) | nội dung | nguồn | được phép dùng (có/không)", 2, "proof_list"),
    ("goals.business_goal", "Mục tiêu kinh doanh", "Mục tiêu kinh doanh 3–12 tháng tới là gì (có số)?",
     "Ví dụ: tăng từ 80 lên 150 ly/ngày trước 31/03/2027", 1, "text"),
    ("goals.primary_conversion", "Hành động chuyển đổi chính", "Hành động chính bạn muốn khách làm là gì?",
     "Ví dụ: đặt món qua Zalo, ghé quán, nhắn tin fanpage", 1, "text"),
    ("goals.current_numbers", "Số liệu hiện tại", "Hiện tại bạn đang đạt bao nhiêu (đơn/ngày, doanh thu/tháng, khách quen…)?", "", 2, "text"),
    ("goals.deadline", "Hạn mục tiêu", "Hạn hoàn thành mục tiêu?", "YYYY-MM-DD", 2, "text"),
    ("channels_active", "Kênh đang dùng", "Bạn đang dùng những kênh nào?", "Mỗi dòng một kênh: Facebook, TikTok, Zalo OA…", 1, "list"),
    ("market.location", "Khu vực thị trường", "Bạn bán ở khu vực nào?", "Ví dụ: Quận Hải Châu, Đà Nẵng", 1, "text"),
    ("market.scope", "Phạm vi", "Phạm vi thị trường?", "Tỉnh/thành, vùng, toàn quốc", 3, "text"),
    ("brand.website", "Website", "Địa chỉ website (nếu có)?", "", 2, "text"),
    ("brand.hotline", "Hotline", "Số điện thoại/Zalo liên hệ?", "", 2, "text"),
    ("brand.address", "Địa chỉ", "Địa chỉ cửa hàng (nếu có)?", "Dùng cho Google Maps và NAP", 2, "text"),
    ("brand.opening_hours", "Giờ mở cửa", "Giờ mở cửa?", "Ví dụ: 6:30–22:00 hằng ngày", 3, "text"),
    ("brand.social_links", "Trang mạng xã hội", "Link fanpage, TikTok, Zalo OA…?", "Mỗi dòng một link", 2, "list"),
    ("brand.monthly_budget_vnd", "Ngân sách marketing/tháng (VND)", "Ngân sách marketing mỗi tháng khoảng bao nhiêu?", "", 2, "number"),
    ("faq", "Câu hỏi thường gặp (đã xác nhận)", "Khách hay hỏi gì và câu trả lời chính xác là gì?",
     "Mỗi dòng: câu hỏi | câu trả lời. Chỉ ghi câu trả lời đúng sự thật.", 3, "faq_list"),
]

FIELD_INDEX = {f[0]: f for f in FIELDS}
WEIGHT = {1: 3, 2: 2, 3: 1}

# Giá trị mặc định do phiên bản cũ tự chèn — không coi là thông tin người dùng đã khai
_LEGACY_DEFAULTS = {
    "channels": {"facebook, tiktok, google, youtube, website"},
    "brand_voice": {"chuyên nghiệp, uy tín", "chuyên nghiệp, uy tín, thực chiến"},
    "business_model": {"b2c / b2b", "b2b / b2c"},
    "market_location": {"toàn quốc"},
}


def empty_context() -> Dict[str, Any]:
    return {"version": 1, "changelog": []}


def get_path(data: Dict[str, Any], path: str) -> Any:
    cur: Any = data
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def set_path(data: Dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    cur = data
    for part in parts[:-1]:
        if not isinstance(cur.get(part), dict):
            cur[part] = {}
        cur = cur[part]
    cur[parts[-1]] = value


def is_filled(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return len(value) > 0
    if isinstance(value, (int, float)):
        return value > 0
    return bool(value)


def _split_list(raw: str) -> List[str]:
    return [x.strip() for x in re.split(r"[\n,;]+", raw or "") if x.strip()]


def from_legacy_profile(p: Dict[str, Any]) -> Dict[str, Any]:
    ctx = empty_context()

    def take(key: str) -> str:
        val = str(p.get(key) or "").strip()
        if val.lower() in _LEGACY_DEFAULTS.get(key, set()):
            return ""
        return val

    mapping = [
        ("brand_name", "brand.name", "text"), ("industry", "brand.industry", "text"),
        ("business_model", "product.business_model", "text"), ("products_services", "product.one_liner", "text"),
        ("price_range", "product.price_note", "text"), ("target_audience", "customers.buyer", "text"),
        ("competitors", "competitors.direct", "list"), ("channels", "channels_active", "list"),
        ("brand_voice", "brand_voice.tone", "text"), ("phone_hotline", "brand.hotline", "text"),
        ("website_url", "brand.website", "text"), ("social_channels", "brand.social_links", "list"),
        ("usp_advantages", "differentiation.only_we_have", "text"), ("market_location", "market.location", "text"),
        ("usp_advantages", "product.advantages", "list"),
    ]
    for key, path, kind in mapping:
        val = take(key)
        if val:
            set_path(ctx, path, _split_list(val) if kind == "list" else val)
    budget = p.get("monthly_budget")
    if isinstance(budget, (int, float)) and budget > 0:
        set_path(ctx, "brand.monthly_budget_vnd", float(budget))
    return ctx


def load_context(email: str) -> Dict[str, Any]:
    email = normalize_email(email)
    row = one("SELECT data_json, version FROM context_profiles WHERE user_email = ?", (email,))
    if row:
        data = loads(row["data_json"], empty_context())
        data["version"] = row["version"]
        return data
    legacy = one("SELECT * FROM user_profiles WHERE user_email = ?", (email,))
    ctx = from_legacy_profile(legacy) if legacy else empty_context()
    if legacy and any(is_filled(get_path(ctx, f[0])) for f in FIELDS):
        ctx["changelog"] = [{"date": datetime.now().strftime("%Y-%m-%d"), "version": 1,
                             "change": "Chuyển từ hồ sơ doanh nghiệp bản cũ", "why": "Nâng cấp lên hồ sơ bối cảnh v2"}]
    execute("INSERT OR IGNORE INTO context_profiles (user_email, data_json, version) VALUES (?, ?, 1)", (email, dumps(ctx)))
    return ctx


def _coerce(kind: str, value: Any) -> Any:
    if value is None:
        return None
    if kind == "number":
        if isinstance(value, (int, float)):
            return float(value)
        txt = str(value).strip().lower().replace(" ", "")
        if not txt:
            return None
        txt = txt.replace("%", "").replace("vnd", "").replace("vnđ", "").replace("đ", "")
        multiplier = 1.0
        if "tỷ" in txt or "ti" in txt:
            multiplier = 1_000_000_000.0
            txt = re.sub(r"(tỷ|ti)", "", txt)
        elif "tr" in txt or "triệu" in txt or "trieu" in txt:
            multiplier = 1_000_000.0
            txt = re.sub(r"(tr|triệu|trieu)", "", txt)
        elif "k" in txt or "nghìn" in txt or "ngàn" in txt or "nghin" in txt or "ngan" in txt:
            multiplier = 1_000.0
            txt = re.sub(r"(k|nghìn|ngàn|nghin|ngan)", "", txt)

        # 1.200.000 hoặc 1,200,000 → 1200000 ; 35,5 → 35.5
        if re.fullmatch(r"\d{1,3}([.,]\d{3})+", txt):
            txt = re.sub(r"[.,]", "", txt)
        txt = txt.replace(",", ".")
        try:
            return float(txt) * multiplier
        except ValueError:
            raise ValueError("phải là số")
    if kind == "list":
        if isinstance(value, list):
            return [str(x).strip() for x in value if str(x).strip()]
        return _split_list(str(value))
    if kind in ("price_list", "pair_list", "quote_list", "proof_list", "faq_list"):
        if not isinstance(value, list):
            raise ValueError("phải là danh sách")
        return [x for x in value if isinstance(x, dict)]
    return str(value).strip()


def validate_patch(patch: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    clean: Dict[str, Any] = {}
    errors: List[str] = []
    for path, value in patch.items():
        field = FIELD_INDEX.get(path)
        if not field and path != "product.price_note":
            errors.append(f"Trường không tồn tại: {path}")
            continue
        kind = field[5] if field else "text"
        try:
            coerced = _coerce(kind, value)
        except ValueError as exc:
            errors.append(f"{field[1] if field else path}: {exc}")
            continue
        if path == "unit_economics.gross_margin_pct" and coerced is not None and not (0 < coerced < 100):
            errors.append("Biên lợi nhuận gộp phải nằm trong khoảng 0–100%.")
            continue
        clean[path] = coerced
    return clean, errors


def save_context(email: str, patch: Dict[str, Any], note: str = "") -> Dict[str, Any]:
    """patch là dict {đường_dẫn: giá_trị}. Trả về hồ sơ mới. Ném ValueError nếu dữ liệu sai."""
    email = normalize_email(email)
    clean, errors = validate_patch(patch)
    if errors:
        raise ValueError("; ".join(errors))
    data = load_context(email)
    before = copy.deepcopy(data)
    changed = []
    for path, value in clean.items():
        if get_path(before, path) != value:
            set_path(data, path, value)
            changed.append(FIELD_INDEX[path][1] if path in FIELD_INDEX else path)
    if not changed:
        return data
    version = int(data.get("version", 1)) + 1
    data["version"] = version
    entry = {"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "version": version,
             "change": "Cập nhật: " + ", ".join(changed[:8]) + ("…" if len(changed) > 8 else ""), "why": note.strip()[:300]}
    data["changelog"] = ([entry] + list(data.get("changelog") or []))[:50]
    execute("UPDATE context_profiles SET data_json = ?, version = ?, updated_at = CURRENT_TIMESTAMP WHERE user_email = ?",
            (dumps(data), version, email))
    execute("INSERT INTO context_versions (user_email, version, data_json, change_note) VALUES (?, ?, ?, ?)",
            (email, version, dumps(before), entry["change"]))
    # Giữ 30 phiên bản gần nhất
    execute("DELETE FROM context_versions WHERE user_email = ? AND id NOT IN "
            "(SELECT id FROM context_versions WHERE user_email = ? ORDER BY id DESC LIMIT 30)", (email, email))
    # Đồng bộ vài trường hiển thị cho trang quản trị
    execute("INSERT OR IGNORE INTO user_profiles (user_email) VALUES (?)", (email,))
    execute("UPDATE user_profiles SET brand_name = ?, industry = ?, updated_at = CURRENT_TIMESTAMP WHERE user_email = ?",
            (get_path(data, "brand.name") or "", get_path(data, "brand.industry") or "", email))
    return data


def list_versions(email: str) -> List[Dict[str, Any]]:
    return rows("SELECT id, version, change_note, created_at FROM context_versions WHERE user_email = ? ORDER BY id DESC",
                (normalize_email(email),))


def completeness(data: Dict[str, Any]) -> Dict[str, Any]:
    total = filled = 0
    missing_core = []
    for path, label, *_rest in FIELDS:
        prio = _rest[2]
        total += WEIGHT[prio]
        if is_filled(get_path(data, path)):
            filled += WEIGHT[prio]
        elif prio == 1:
            missing_core.append({"path": path, "label": label})
    return {"score": round(100 * filled / total) if total else 0, "missing_core": missing_core}


def missing_fields(data: Dict[str, Any], required: List[str]) -> List[Dict[str, str]]:
    out = []
    for path in required:
        if not is_filled(get_path(data, path)):
            f = FIELD_INDEX.get(path)
            if f:
                out.append({"path": path, "label": f[1], "question": f[2], "hint": f[3], "kind": f[5]})
    return out


def next_questions(data: Dict[str, Any], focus: Optional[List[str]] = None, limit: int = 5) -> List[Dict[str, str]]:
    focus = focus or []
    candidates = []
    for path, label, question, hint, prio, kind in FIELDS:
        if is_filled(get_path(data, path)):
            continue
        rank = (0 if path in focus else 1, prio)
        candidates.append((rank, {"path": path, "label": label, "question": question, "hint": hint, "kind": kind}))
    candidates.sort(key=lambda x: x[0])
    return [c[1] for c in candidates[:max(1, min(limit, 5))]]


def field_catalog() -> List[Dict[str, Any]]:
    return [{"path": p, "label": l, "question": q, "hint": h, "priority": pr, "kind": k} for p, l, q, h, pr, k in FIELDS]


# ---------------------------------------------------------------------------
# Chuyển hồ sơ thành văn bản cho prompt
# ---------------------------------------------------------------------------

def _fmt(kind: str, value: Any) -> str:
    if kind == "price_list":
        return "; ".join(f"{x.get('name', '')}: {int(float(x.get('price_vnd') or 0)):,} đ".replace(",", ".") for x in value)
    if kind == "pair_list":
        return " | ".join(f"\"{x.get('objection', '')}\" → {x.get('answer', '')}" for x in value)
    if kind == "quote_list":
        return " | ".join(f"\"{x.get('quote', '')}\" ({x.get('source', '')})" for x in value)
    if kind == "proof_list":
        return " | ".join(
            f"[{x.get('type', '')}] {x.get('text', '')} (nguồn: {x.get('source', '') or 'không ghi'}; "
            f"{'ĐƯỢC phép dùng công khai' if x.get('permission') else 'KHÔNG được dùng công khai'})" for x in value)
    if kind == "faq_list":
        return " | ".join(f"H: {x.get('q', '')} Đ: {x.get('a', '')}" for x in value)
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    if isinstance(value, float) and value.is_integer():
        return f"{int(value):,}".replace(",", ".")
    return str(value)


def render_for_prompt(data: Dict[str, Any], paths: Optional[List[str]] = None) -> str:
    lines = [f"HỒ SƠ BỐI CẢNH (phiên bản {data.get('version', 1)}) — chỉ dùng thông tin dưới đây, không thêm thông tin tự chế:"]
    missing = []
    for path, label, _q, _h, prio, kind in FIELDS:
        if paths is not None and path not in paths and prio != 1:
            continue
        value = get_path(data, path)
        if is_filled(value):
            lines.append(f"- {label}: {_fmt(kind, value)}")
        elif prio <= 2:
            missing.append(label)
    note = get_path(data, "product.price_note")
    if note:
        lines.append(f"- Ghi chú giá: {note}")
    if missing:
        lines.append("- [THIẾU DỮ LIỆU] chưa có: " + ", ".join(missing[:20]))
    return "\n".join(lines)


def public_proof(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [p for p in (data.get("proof") or []) if p.get("permission")]
