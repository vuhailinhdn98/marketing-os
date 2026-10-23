# -*- coding: utf-8 -*-
"""
Cổng tuân thủ G01–G11 (skill §5.3, §14, §17) — chạy bằng code sau mỗi lần AI sinh nội dung.

Kết quả gồm `warnings` (cần xem lại) và `blockers` (không cho duyệt/xuất bản tới khi sửa).
AI có lỡ bịa thì vẫn không lọt ra ngoài.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, Iterable, List, Optional

# Loại đầu ra: nội dung công khai bị kiểm chặt hơn nội dung nội bộ
PUBLIC_KINDS = {"post", "ad", "landing", "email", "sms", "video_script", "kol_brief", "pr", "review_reply", "faq", "offer_copy"}

BANNED_OFFER_WORDS = ["đột phá", "thần kỳ", "bí mật", "duy nhất", "cam kết 100%", "100% hiệu quả", "tốt nhất thị trường",
                      "số 1 việt nam", "rẻ nhất", "giới hạn"]
SCARCITY = ["chỉ còn", "số lượng có hạn", "suất cuối", r"còn \d+ suất", r"\d+ suất", "sắp hết", "hết hạn trong",
            "đếm ngược", "cơ hội cuối", "duy nhất hôm nay", "chỉ hôm nay", "nhanh tay kẻo lỡ", "kẻo hết"]
FEAR = ["cảnh báo", "mất tiền oan", "tiền mất tật mang", "sai lầm chí mạng", "đừng mắc bẫy", "hối hận",
        "đừng dại", "cẩn thận kẻo", "nguy hiểm khôn lường"]
HEALTH_CLAIMS = ["chữa khỏi", "điều trị", "khỏi bệnh", "trị dứt điểm", "an toàn tuyệt đối", "không tác dụng phụ",
                 "đặc trị", "thay thế thuốc", "chữa bệnh"]
SENSITIVE_INDUSTRY = ["mỹ phẩm", "thực phẩm chức năng", "tpcn", "thuốc", "y tế", "thẩm mỹ", "nha khoa", "spa",
                      "dược", "sữa cho trẻ", "phòng khám"]
FORBIDDEN_TACTICS = ["quét uid", "scan uid", "đổi uid", "uid thành số", "mua data", "data khách hàng giá rẻ",
                     "tool quét", "cào số điện thoại", "mua danh sách số", "spam tin nhắn"]
NEGATIVE_WORDS = ["kém", "tệ", "lừa", "chậm", "đắt", "tồi", "lỗi", "phàn nàn", "yếu", "dở", "gian", "không uy tín",
                  "vấn đề", "tử huyệt", "điểm yếu"]
DISCLOSURE = ["quảng cáo", "được tài trợ", "#quangcao", "#tàitrợ", "#taitro", "hợp tác quảng cáo", "nội dung tài trợ",
              "#ad", "sponsored"]
VANITY = ["like", "lượt thích", "follower", "người theo dõi", "lượt xem", "view", "lên top", "top google", "viral"]

LABEL_RE = re.compile(r"\[(unverified|inference|speculation|thiếu dữ liệu|nguồn[^\]]*)\]", re.I)
STAT_RE = re.compile(
    r"(\d+(?:[.,]\d+)?\s*%(?!\s*(?:off|giảm))|gấp\s+\d+(?:[.,]\d+)?\s*lần|hàng\s+(?:nghìn|ngàn|trăm|triệu)"
    r"|top\s*\d+|số\s*1\b|#1\b|\d+\+?\s*(?:khách hàng|khách|người dùng|đơn vị|doanh nghiệp))", re.I)
DISCOUNT_RE = re.compile(r"(giảm|off|ưu đãi|sale|chiết khấu|khuyến mãi|tặng|hoàn)(?:\s+[^\s\d]+){0,3}\s*\d+\s*%", re.I)


def _norm(text: str) -> str:
    return unicodedata.normalize("NFC", text or "").lower()


def collect_text(value: Any) -> str:
    """Gom mọi chuỗi trong JSON đầu ra thành một văn bản để kiểm."""
    parts: List[str] = []

    def walk(v: Any) -> None:
        if isinstance(v, str):
            parts.append(v)
        elif isinstance(v, dict):
            for k, x in v.items():
                if k in ("lesson", "lessons", "sources", "claims_to_verify", "compliance_notes"):
                    continue
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)

    walk(value)
    return "\n".join(parts)


def _sentences(text: str) -> List[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?…])\s+|\n+", text) if s.strip()]


def _excerpt(sentence: str) -> str:
    return sentence if len(sentence) <= 160 else sentence[:157] + "…"


def _contains(text: str, phrases: Iterable[str]) -> List[str]:
    hits = []
    for p in phrases:
        if "\\d" in p:
            if re.search(p, text):
                hits.append(p.replace("\\d+", "N"))
        elif re.search(r"(?<!\w)" + re.escape(p) + r"(?!\w)", text):
            hits.append(p)
    return hits


def check(output: Any, *, kind: str = "internal", context: Optional[Dict[str, Any]] = None,
          competitor_names: Optional[List[str]] = None, scarcity_evidence: str = "",
          extra_text: str = "") -> Dict[str, List[Dict[str, str]]]:
    context = context or {}
    text = collect_text(output) + ("\n" + extra_text if extra_text else "")
    low = _norm(text)
    public = kind in PUBLIC_KINDS
    warnings: List[Dict[str, str]] = []
    blockers: List[Dict[str, str]] = []

    def add(target: List[Dict[str, str]], code: str, message: str, excerpt: str = "") -> None:
        item = {"code": code, "message": message}
        if excerpt:
            item["excerpt"] = _excerpt(excerpt)
        if item not in target:
            target.append(item)

    proof_text = _norm(" ".join(str(p.get("text", "")) for p in (context.get("proof") or []) if p.get("permission")))
    numbers_text = _norm(str((context.get("goals") or {}).get("current_numbers", "")))

    # G01 — con số/thống kê không có nguồn
    for sentence in _sentences(text):
        s_low = _norm(sentence)
        if DISCOUNT_RE.search(s_low):
            s_low = DISCOUNT_RE.sub("", s_low)
        MATERIAL_RE = re.compile(r"(100\s*%\s*(cotton|tự nhiên|thủ công|nguyên chất|chính hãng|lụa|len|gỗ|da thật|bạc|sợi tre)|(cotton|tự nhiên|thủ công|nguyên chất|chính hãng)\s+100\s*%)", re.I)
        if MATERIAL_RE.search(s_low):
            s_low = MATERIAL_RE.sub("", s_low)
        m = STAT_RE.search(s_low)
        if not m:
            continue
        if LABEL_RE.search(sentence) or "http" in s_low:
            continue
        token = m.group(0).strip()
        if token and (token in proof_text or token in numbers_text):
            continue
        add(blockers if public else warnings, "G01",
            "Con số/thống kê không có nguồn trong hồ sơ. Thêm nguồn, gắn [Unverified] hoặc bỏ.", sentence)

    # G02 — từ cấm trong copy (từ skill + từ cấm riêng của thương hiệu)
    banned = BANNED_OFFER_WORDS + [w.lower() for w in ((context.get("customer_language") or {}).get("banned_words") or [])]
    for word in _contains(low, banned):
        add(warnings, "G02", f"Từ cần tránh: \"{word}\" (chỉ dùng khi chứng minh được).")

    # G03 — khan hiếm / đếm ngược
    scarcity_hits = _contains(low, SCARCITY)
    if scarcity_hits and not scarcity_evidence.strip():
        add(blockers if public else warnings, "G03",
            "Có lời khan hiếm/đếm ngược (" + ", ".join(scarcity_hits[:3]) + ") nhưng chưa nhập bằng chứng giới hạn có thật.")

    # G04 — hù dọa
    for word in _contains(low, FEAR):
        add(warnings, "G04", f"Giọng hù dọa: \"{word}\". Skill cấm dọa khách; chuyển sang nói lợi ích hoặc rủi ro có thật.")

    # G05 — nêu tên đối thủ kèm nhận xét tiêu cực mà không có nguồn
    for name in competitor_names or []:
        n = _norm(name).strip()
        if len(n) < 3:
            continue
        for sentence in _sentences(text):
            s_low = _norm(sentence)
            if n in s_low and any(w in s_low for w in NEGATIVE_WORDS) and "http" not in s_low and not LABEL_RE.search(sentence):
                add(blockers if public else warnings, "G05",
                    f"Nhận xét tiêu cực về \"{name}\" không có nguồn. Quảng cáo so sánh phải có căn cứ (Luật 75/2025/QH15).",
                    sentence)

    # G06 — thiếu nhãn quảng cáo cho nội dung KOL/tài trợ
    if kind == "kol_brief" and not any(d in low for d in DISCLOSURE):
        add(blockers, "G06", "Brief KOL/KOC phải yêu cầu ghi rõ \"Quảng cáo\"/\"Được tài trợ\" trước và trong nội dung.")

    # G08 được kiểm riêng bằng check_budget_lines; G09 bằng check_kpis

    # G10 — ngành nhạy cảm và tuyên bố sức khỏe
    industry = _norm(" ".join([str((context.get("brand") or {}).get("industry", "")), str((context.get("product") or {}).get("one_liner", ""))]))
    for claim in _contains(low, HEALTH_CLAIMS):
        add(blockers if public else warnings, "G10", f"Tuyên bố sức khỏe/y tế: \"{claim}\" — không được dùng trong quảng cáo nếu chưa được cấp phép.")
    if public and any(w in industry for w in SENSITIVE_INDUSTRY):
        add(warnings, "G10", "Ngành cần xác nhận nội dung quảng cáo trước khi đăng (mỹ phẩm, thực phẩm chức năng, y tế…).")

    # G11 — chiến thuật dữ liệu bị cấm
    for tactic in _contains(low, FORBIDDEN_TACTICS):
        add(blockers, "G11", f"Chiến thuật bị cấm theo Luật 91/2025/QH15: \"{tactic}\".")

    return {"warnings": warnings, "blockers": blockers}


def check_budget_lines(lines: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """G08: thành tiền = đơn giá × số lượng; đơn vị theo ngày mà số lượng không khớp số ngày thì cảnh báo."""
    issues = []
    for i, line in enumerate(lines, 1):
        try:
            price = float(line.get("unit_price") or 0)
            qty = float(line.get("quantity") or 0)
            total = float(line.get("projected_total") or 0)
        except (TypeError, ValueError):
            issues.append({"code": "G08", "message": f"Dòng {i}: đơn giá, số lượng hoặc thành tiền không phải số."})
            continue
        expected = round(price * qty)
        if total and abs(total - expected) > max(1.0, 0.005 * expected):
            issues.append({"code": "G08", "message": f"Dòng {i} ({line.get('item', '')}): {price:,.0f} × {qty:g} = {expected:,.0f}, "
                                                     f"không phải {total:,.0f}.".replace(",", ".")})
        unit = _norm(str(line.get("unit", "")))
        if "tháng" in unit and qty > 12:
            issues.append({"code": "G08", "message": f"Dòng {i}: đơn vị 'tháng' mà số lượng {qty:g} — có nhầm VND/ngày không?"})
    return issues


def check_kpis(kpis: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """G09: KPI phải có số mục tiêu và hạn; chỉ số phù phiếm bị đánh dấu."""
    issues = []
    for k in kpis:
        name = str(k.get("name") or k.get("metric") or "")
        target = str(k.get("target", ""))
        deadline = str(k.get("deadline") or k.get("by") or "")
        if not re.search(r"\d", target):
            issues.append({"code": "G09", "message": f"KPI \"{name}\" chưa có con số mục tiêu."})
        if not deadline.strip():
            issues.append({"code": "G09", "message": f"KPI \"{name}\" chưa có hạn."})
        if any(v in _norm(name) for v in VANITY):
            issues.append({"code": "G09", "message": f"KPI \"{name}\" là chỉ số phù phiếm; nên đo tin nhắn, đơn, chi phí mỗi đơn."})
    return issues


def merge(*results: Dict[str, List[Dict[str, str]]]) -> Dict[str, List[Dict[str, str]]]:
    out: Dict[str, List[Dict[str, str]]] = {"warnings": [], "blockers": []}
    for r in results:
        for key in ("warnings", "blockers"):
            for item in r.get(key, []):
                if item not in out[key]:
                    out[key].append(item)
    return out
