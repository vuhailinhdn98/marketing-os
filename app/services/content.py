# -*- coding: utf-8 -*-
"""Kho nội dung + quy trình duyệt + lịch nội dung + xuất bản qua webhook."""
from __future__ import annotations

import time
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from app import guardrails
from app.context import load_context
from app.database import dumps, execute, get_app_config, loads, normalize_email, one, rows, set_app_config
from app.netsafe_post import post_json, validate_webhook_url
from app.services import extras as extras_mod

STATUSES = ["ideas", "draft", "review", "approved", "scheduled", "published", "measured"]
STATUS_LABEL = {"ideas": "Ý tưởng", "draft": "Bản nháp", "review": "Chờ duyệt", "approved": "Đã duyệt",
                "scheduled": "Đã lên lịch", "published": "Đã đăng", "measured": "Đã đo"}
GATED = {"approved", "scheduled", "published", "measured"}
CHANNEL_KIND = {"facebook": "post", "tiktok": "video_script", "reels": "video_script", "youtube": "video_script",
                "zalo": "post", "email": "email", "sms": "sms", "landing": "landing", "blog": "post", "website": "post",
                "instagram": "post", "google": "ad", "ads": "ad", "quảng cáo": "ad"}


class ContentError(ValueError):
    pass


def kind_for_channel(channel: str) -> str:
    low = (channel or "").lower()
    for key, kind in CHANNEL_KIND.items():
        if key in low:
            return kind
    return "post"


def _check(owner: str, item: Dict[str, Any], scarcity_evidence: str = "") -> Dict[str, Any]:
    ctx = load_context(owner)
    text = {"topic": item.get("topic"), "hook": item.get("hook"), "body": item.get("body"), "cta": item.get("cta"),
            "video_script": item.get("video_script")}
    return guardrails.check(text, kind=kind_for_channel(item.get("channel", "")), context=ctx,
                            competitor_names=extras_mod.known_competitors(owner, ctx), scarcity_evidence=scarcity_evidence)


def _decorate(item: Dict[str, Any]) -> Dict[str, Any]:
    item["guardrails"] = loads(item.pop("guardrail_json", None), {"warnings": [], "blockers": []})
    item["provenance"] = loads(item.pop("provenance_json", None), {})
    item["variants"] = loads(item.pop("variants_json", None), [])
    item["status_label"] = STATUS_LABEL.get(item.get("status"), item.get("status"))
    return item


def create_item(owner: str, data: Dict[str, Any], provenance: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    owner = normalize_email(owner)
    topic = str(data.get("topic") or "").strip()
    if not topic:
        raise ContentError("Thiếu chủ đề.")
    status = data.get("status") or "draft"
    if status not in ("ideas", "draft", "review"):
        raise ContentError("Nội dung mới chỉ được ở trạng thái Ý tưởng, Bản nháp hoặc Chờ duyệt.")
    item = {
        "channel": str(data.get("channel") or "Facebook")[:60], "topic": topic[:300], "hook": str(data.get("hook") or "")[:500],
        "body": str(data.get("body") or "")[:20000], "cta": str(data.get("cta") or "")[:300],
        "video_script": str(data.get("video_script") or "")[:12000], "image_prompt": str(data.get("image_prompt") or "")[:2000],
        "pillar": str(data.get("pillar") or "")[:120], "funnel_stage": str(data.get("funnel_stage") or "")[:60],
        "format": str(data.get("format") or "")[:60], "publish_date": str(data.get("publish_date") or "")[:10],
    }
    guard = _check(owner, item, str(data.get("scarcity_evidence") or ""))
    cols = ["user_email", "status", "guardrail_json", "provenance_json", "variants_json"] + list(item)
    vals = [owner, status, dumps(guard), dumps(provenance or {"status": "manual"}), dumps(data.get("variants") or [])] + list(item.values())
    item_id = execute(f"INSERT INTO content_items ({', '.join(cols)}, updated_at) VALUES ({', '.join(['?'] * len(vals))}, CURRENT_TIMESTAMP)", vals)
    return get_item(owner, item_id)  # type: ignore[return-value]


def get_item(owner: str, item_id: int) -> Optional[Dict[str, Any]]:
    r = one("SELECT * FROM content_items WHERE id = ? AND user_email = ?", (item_id, normalize_email(owner)))
    return _decorate(r) if r else None


def list_items(owner: str) -> List[Dict[str, Any]]:
    return [_decorate(r) for r in rows("SELECT * FROM content_items WHERE user_email = ? ORDER BY COALESCE(updated_at, created_at) DESC, id DESC",
                                       (normalize_email(owner),))]


EDITABLE = ["channel", "topic", "hook", "body", "cta", "video_script", "image_prompt", "pillar", "funnel_stage", "format", "publish_date"]


def update_item(owner: str, item_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    item = get_item(owner, item_id)
    if not item:
        raise ContentError("Không tìm thấy nội dung.")
    changes = {k: str(data[k])[:20000] for k in EDITABLE if k in data and data[k] is not None}
    merged = {**item, **changes}
    guard = _check(owner, merged, str(data.get("scarcity_evidence") or ""))
    sets = [f"{k} = ?" for k in changes] + ["guardrail_json = ?", "updated_at = CURRENT_TIMESTAMP"]
    vals = list(changes.values()) + [dumps(guard)]
    # Sửa nội dung đã duyệt thì quay về chờ duyệt
    if changes and item["status"] in GATED and item["status"] != "published":
        sets.append("status = 'review'")
    execute(f"UPDATE content_items SET {', '.join(sets)} WHERE id = ? AND user_email = ?", vals + [item_id, normalize_email(owner)])
    return get_item(owner, item_id)  # type: ignore[return-value]


def set_status(owner: str, item_id: int, status: str) -> Dict[str, Any]:
    if status not in STATUSES:
        raise ContentError("Trạng thái không hợp lệ.")
    item = get_item(owner, item_id)
    if not item:
        raise ContentError("Không tìm thấy nội dung.")
    if status in GATED:
        guard = _check(owner, item)
        execute("UPDATE content_items SET guardrail_json = ? WHERE id = ?", (dumps(guard), item_id))
        if guard["blockers"]:
            raise ContentError("Chưa thể chuyển sang \"" + STATUS_LABEL[status] + "\": còn lỗi tuân thủ — "
                               + "; ".join(b["message"] for b in guard["blockers"][:3]))
    execute("UPDATE content_items SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_email = ?",
            (status, item_id, normalize_email(owner)))
    return get_item(owner, item_id)  # type: ignore[return-value]


def delete_item(owner: str, item_id: int) -> bool:
    return execute("DELETE FROM content_items WHERE id = ? AND user_email = ?", (item_id, normalize_email(owner))) > 0


def webhook_url(owner: str) -> str:
    return get_app_config(f"content_webhook_url:{normalize_email(owner)}", "")


def set_webhook_url(owner: str, url: str) -> str:
    url = (url or "").strip()
    if url:
        validate_webhook_url(url)
    set_app_config(f"content_webhook_url:{normalize_email(owner)}", url)
    return url


def publish(owner: str, item_id: int) -> Dict[str, Any]:
    item = get_item(owner, item_id)
    if not item:
        raise ContentError("Không tìm thấy nội dung.")
    guard = _check(owner, item)
    if guard["blockers"]:
        raise ContentError("Còn lỗi tuân thủ, chưa thể xuất bản: " + "; ".join(b["message"] for b in guard["blockers"][:3]))
    if item["status"] not in ("approved", "scheduled", "published"):
        raise ContentError("Chỉ xuất bản nội dung đã được duyệt.")
    url = webhook_url(owner)
    if not url:
        raise ContentError("Chưa cấu hình webhook xuất bản (Zapier, Make, n8n…). Vào mục Cài đặt để thêm.")
    payload = {"event": "content.publish", "id": item["id"], "channel": item["channel"], "topic": item["topic"], "hook": item["hook"],
               "body": item["body"], "cta": item["cta"], "video_script": item["video_script"], "image_prompt": item["image_prompt"],
               "publish_date": item.get("publish_date"), "sent_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    ok, message = post_json(url, payload)
    if ok:
        execute("UPDATE content_items SET status = 'published', published_webhook = 1, webhook_published_at = CURRENT_TIMESTAMP, "
                "updated_at = CURRENT_TIMESTAMP WHERE id = ?", (item_id,))
    return {"delivered": ok, "message": message, "item": get_item(owner, item_id)}


def promotion_checklist(item: Dict[str, Any]) -> List[str]:
    """Skill §8.3 — checklist quảng bá sau khi đăng (không cần AI)."""
    steps = [
        "Gắn link có UTM (dùng mục Đo lường → Tạo UTM) để đo bài này",
        "Gửi bài cho người được nhắc tới trong bài và người bạn muốn họ bình luận",
        "Đưa vào bản tin email / Zalo OA (chỉ gửi người đã đồng ý)",
        "Nhờ đồng nghiệp, đối tác chia sẻ",
        "Đăng lên fanpage và trang cá nhân",
        "Đăng vào group phù hợp, đúng luật group",
        "Cắt thành Reels / TikTok / Shorts",
        "Làm bản carousel hoặc infographic",
        "Lên lịch đăng lại 1–2 biến thể trong tuần",
        "Gắn link bài vào bài cũ liên quan",
        "Trả lời mọi bình luận trong 24 giờ đầu, cảm ơn người chia sẻ",
    ]
    if "linkedin" in (item.get("channel") or "").lower():
        steps.insert(8, "Đăng LinkedIn (B2B)")
    return steps


# ---------------------------------------------------------------------------
# Lịch nội dung
# ---------------------------------------------------------------------------

def save_calendar(owner: str, rows_in: List[Dict[str, Any]], provenance: Dict[str, Any]) -> int:
    owner = normalize_email(owner)
    if not rows_in:
        return 0
    dates = sorted(r["date"] for r in rows_in)
    execute("DELETE FROM calendar_schedules WHERE user_email = ? AND plan_date BETWEEN ? AND ?", (owner, dates[0], dates[-1]))
    from app.database import connect
    with connect() as conn:
        conn.executemany(
            "INSERT INTO calendar_schedules (user_email, day_number, plan_date, channel, pillar, funnel_stage, topic, format, hook, cta, "
            "metric, intent, holiday, status, provenance_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'planned', ?)",
            [(owner, (date.fromisoformat(r["date"]) - date.fromisoformat(dates[0])).days + 1, r["date"], r.get("channel", ""),
              r.get("pillar", ""), r.get("funnel_stage", ""), r.get("topic", ""), r.get("format", ""), r.get("hook", ""),
              r.get("cta", ""), r.get("metric", ""), r.get("intent", ""), r.get("holiday", ""), dumps(provenance)) for r in rows_in])
    return len(rows_in)


def list_calendar(owner: str, start: Optional[str] = None, days: int = 31) -> List[Dict[str, Any]]:
    start_d = date.fromisoformat(start) if start else date.today() - timedelta(days=3)
    end_d = start_d + timedelta(days=max(1, min(days, 120)) - 1)
    data = rows("SELECT * FROM calendar_schedules WHERE user_email = ? AND plan_date BETWEEN ? AND ? ORDER BY plan_date, id",
                (normalize_email(owner), start_d.isoformat(), end_d.isoformat()))
    for r in data:
        r.pop("provenance_json", None)
    return data


def delete_calendar_row(owner: str, row_id: int) -> bool:
    return execute("DELETE FROM calendar_schedules WHERE id = ? AND user_email = ?", (row_id, normalize_email(owner))) > 0


def legacy_calendar_count(owner: str) -> int:
    r = one("SELECT COUNT(*) AS n FROM calendar_schedules WHERE user_email = ? AND (plan_date IS NULL OR plan_date = '')",
            (normalize_email(owner),))
    return int(r["n"]) if r else 0


def clear_legacy_calendar(owner: str) -> int:
    return execute("DELETE FROM calendar_schedules WHERE user_email = ? AND (plan_date IS NULL OR plan_date = '')", (normalize_email(owner),))
