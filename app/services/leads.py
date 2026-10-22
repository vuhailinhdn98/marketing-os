# -*- coding: utf-8 -*-
"""Mini CRM theo phễu khách hàng 6 tầng (skill §4.1) + đồng ý tiếp thị (Luật 91/2025/QH15)."""
from __future__ import annotations

import csv
import io
from typing import Any, Dict, List, Optional, Tuple

from app.database import execute, normalize_email, one, rows
from app.metrics import funnel_diagnosis

STAGES: List[Tuple[str, str]] = [
    ("new", "Mới / Nhận biết"),
    ("consulting", "Đang tư vấn"),
    ("won", "Đã mua lần đầu"),
    ("repeat", "Mua lần 2+"),
    ("referral", "Đã giới thiệu"),
    ("loyal", "Thân quen"),
]
STAGE_KEYS = [k for k, _ in STAGES]
ALL_STATUSES = STAGE_KEYS + ["lost"]
STAGE_LABEL = dict(STAGES + [("lost", "Mất / chăm sóc lại")])

FIELDS = ["full_name", "phone", "email", "source", "channel", "product_interest", "deal_value", "notes",
          "utm_source", "utm_medium", "utm_campaign", "referred_by"]


class LeadError(ValueError):
    pass


def _clean(data: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for f in FIELDS:
        if f in data and data[f] is not None:
            if f == "deal_value":
                try:
                    out[f] = max(0.0, float(data[f] or 0))
                except (TypeError, ValueError):
                    raise LeadError("Giá trị đơn phải là số.")
            else:
                out[f] = str(data[f]).strip()[:2000 if f == "notes" else 300]
    return out


def create_lead(owner: str, data: Dict[str, Any], *, consent_source: str = "") -> Dict[str, Any]:
    owner = normalize_email(owner)
    clean = _clean(data)
    if not clean.get("full_name"):
        raise LeadError("Thiếu họ tên khách.")
    if not clean.get("phone") and not clean.get("email"):
        raise LeadError("Cần ít nhất số điện thoại hoặc email.")
    status = data.get("status") or "new"
    if status not in ALL_STATUSES:
        raise LeadError("Trạng thái không hợp lệ.")
    consent = 1 if data.get("consent_marketing") is True else 0
    consent_text = str(data.get("consent_text") or "").strip()[:500]
    if consent and not consent_text:
        raise LeadError("Đồng ý tiếp thị phải kèm nội dung khách đã đồng ý (để kiểm chứng được).")
    cols = ["user_email", "status", "consent_marketing", "consent_text", "consent_source"] + list(clean)
    vals = [owner, status, consent, consent_text if consent else "", consent_source[:100] if consent else ""] + list(clean.values())
    sql = (f"INSERT INTO lead_records ({', '.join(cols)}, stage_changed_at, consent_at) "
           f"VALUES ({', '.join(['?'] * len(vals))}, CURRENT_TIMESTAMP, {'CURRENT_TIMESTAMP' if consent else 'NULL'})")
    lead_id = execute(sql, vals)
    return get_lead(owner, lead_id)  # type: ignore[return-value]


def get_lead(owner: str, lead_id: int) -> Optional[Dict[str, Any]]:
    return one("SELECT * FROM lead_records WHERE id = ? AND user_email = ?", (lead_id, normalize_email(owner)))


def list_leads(owner: str, status: Optional[str] = None, search: str = "") -> List[Dict[str, Any]]:
    sql = "SELECT * FROM lead_records WHERE user_email = ?"
    params: List[Any] = [normalize_email(owner)]
    if status:
        sql += " AND status = ?"
        params.append(status)
    if search:
        sql += " AND (full_name LIKE ? OR phone LIKE ? OR email LIKE ? OR product_interest LIKE ? OR notes LIKE ?)"
        params += [f"%{search}%"] * 5
    sql += " ORDER BY updated_at DESC, id DESC"
    return rows(sql, params)


def update_lead(owner: str, lead_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    lead = get_lead(owner, lead_id)
    if not lead:
        raise LeadError("Không tìm thấy khách.")
    clean = _clean(data)
    sets = [f"{k} = ?" for k in clean]
    vals: List[Any] = list(clean.values())
    if "consent_marketing" in data:
        if data["consent_marketing"] is True and not lead.get("consent_marketing"):
            text = str(data.get("consent_text") or "").strip()
            if not text:
                raise LeadError("Ghi lại khách đã đồng ý điều gì, qua kênh nào.")
            sets += ["consent_marketing = 1", "consent_at = CURRENT_TIMESTAMP", "consent_text = ?", "consent_source = ?"]
            vals += [text[:500], str(data.get("consent_source") or "Nhập tay")[:100]]
        elif data["consent_marketing"] is False and lead.get("consent_marketing"):
            sets += ["consent_marketing = 0", "consent_source = ?"]
            vals += ["Khách rút lại đồng ý"]
    if "status" in data and data["status"] != lead["status"]:
        return _apply_status(owner, lead, data["status"], sets, vals, data.get("lost_reason", ""))
    if not sets:
        return lead
    execute(f"UPDATE lead_records SET {', '.join(sets)}, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_email = ?",
            vals + [lead_id, normalize_email(owner)])
    return get_lead(owner, lead_id)  # type: ignore[return-value]


def _apply_status(owner: str, lead: Dict[str, Any], status: str, sets: List[str], vals: List[Any], lost_reason: str = "") -> Dict[str, Any]:
    if status not in ALL_STATUSES:
        raise LeadError("Trạng thái không hợp lệ.")
    sets = list(sets) + ["status = ?", "stage_changed_at = CURRENT_TIMESTAMP"]
    vals = list(vals) + [status]
    if status == "lost" and lead["status"] != "lost":
        sets += ["lost_from_stage = ?", "lost_reason = ?"]
        vals += [lead["status"], str(lost_reason or "")[:300]]
    if status in ("won",):
        sets.append("purchase_count = MAX(COALESCE(purchase_count, 0), 1)")
    if status in ("repeat", "referral", "loyal"):
        sets.append("purchase_count = MAX(COALESCE(purchase_count, 0), 2)")
    execute(f"UPDATE lead_records SET {', '.join(sets)}, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_email = ?",
            vals + [lead["id"], normalize_email(owner)])
    return get_lead(owner, lead["id"])  # type: ignore[return-value]


def set_status(owner: str, lead_id: int, status: str, lost_reason: str = "") -> Dict[str, Any]:
    lead = get_lead(owner, lead_id)
    if not lead:
        raise LeadError("Không tìm thấy khách.")
    if status == lead["status"]:
        return lead
    return _apply_status(owner, lead, status, [], [], lost_reason)


def delete_lead(owner: str, lead_id: int) -> bool:
    return execute("DELETE FROM lead_records WHERE id = ? AND user_email = ?", (lead_id, normalize_email(owner))) > 0


def stats(owner: str) -> Dict[str, Any]:
    owner = normalize_email(owner)
    data = rows("SELECT status, lost_from_stage, deal_value, consent_marketing FROM lead_records WHERE user_email = ?", (owner,))
    counts = {k: 0 for k in ALL_STATUSES}
    reached = {k: 0 for k in STAGE_KEYS}
    won_value = 0.0
    consented = 0
    for r in data:
        st = r["status"] if r["status"] in ALL_STATUSES else "new"
        counts[st] += 1
        consented += 1 if r.get("consent_marketing") else 0
        idx = STAGE_KEYS.index(st) if st in STAGE_KEYS else (STAGE_KEYS.index(r["lost_from_stage"]) if r.get("lost_from_stage") in STAGE_KEYS else 0)
        for k in STAGE_KEYS[: idx + 1]:
            reached[k] += 1
        if st in ("won", "repeat", "referral", "loyal"):
            won_value += float(r.get("deal_value") or 0)
    funnel = funnel_diagnosis([(STAGE_LABEL[k], reached[k]) for k in STAGE_KEYS])
    return {"total": len(data), "by_status": counts, "reached": reached, "won_value": won_value,
            "consented": consented, "funnel": funnel,
            "stages": [{"key": k, "label": STAGE_LABEL[k]} for k in ALL_STATUSES]}


def lost_reasons(owner: str, limit: int = 20) -> List[str]:
    data = rows("SELECT lost_reason FROM lead_records WHERE user_email = ? AND status = 'lost' AND lost_reason != '' "
                "ORDER BY updated_at DESC LIMIT ?", (normalize_email(owner), limit))
    return [r["lost_reason"] for r in data]


def marketing_audience(owner: str) -> List[Dict[str, Any]]:
    """Chỉ khách đã đồng ý nhận tiếp thị (G07)."""
    return rows("SELECT * FROM lead_records WHERE user_email = ? AND consent_marketing = 1 AND status != 'lost'",
                (normalize_email(owner),))


def export_csv(owner: str, consented_only: bool = False) -> str:
    data = marketing_audience(owner) if consented_only else list_leads(owner)
    out = io.StringIO()
    out.write("﻿")
    w = csv.writer(out)
    w.writerow(["ID", "Họ tên", "SĐT", "Email", "Nguồn", "Kênh", "Quan tâm", "Tầng phễu", "Giá trị đơn (VND)",
                "Đồng ý tiếp thị", "Nội dung đồng ý", "Thời điểm đồng ý", "UTM source", "UTM campaign", "Ghi chú", "Ngày tạo"])
    for l in data:
        w.writerow([l["id"], l["full_name"], l["phone"], l["email"], l["source"], l["channel"], l["product_interest"],
                    STAGE_LABEL.get(l["status"], l["status"]), l.get("deal_value") or 0,
                    "Có" if l.get("consent_marketing") else "Không", l.get("consent_text") or "", l.get("consent_at") or "",
                    l.get("utm_source") or "", l.get("utm_campaign") or "", l.get("notes") or "", l.get("created_at")])
    return out.getvalue()
