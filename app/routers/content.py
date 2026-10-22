# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from app import context as ctx_mod, guardrails
from app.deps import CurrentUser, require_user
from app.services import content, extras

router = APIRouter(prefix="/api", tags=["content"])


@router.get("/content")
def list_content(user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    return {"items": content.list_items(user.email), "statuses": [{"key": k, "label": content.STATUS_LABEL[k]} for k in content.STATUSES]}


@router.post("/content")
def create_content(user: CurrentUser = Depends(require_user), body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    return {"item": content.create_item(user.email, body)}


@router.get("/content/{item_id}")
def get_content(item_id: int, user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    item = content.get_item(user.email, item_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy nội dung.")
    return {"item": item, "promotion_checklist": content.promotion_checklist(item)}


@router.put("/content/{item_id}")
def update_content(item_id: int, user: CurrentUser = Depends(require_user), body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    return {"item": content.update_item(user.email, item_id, body)}


@router.patch("/content/{item_id}/status")
def content_status(item_id: int, user: CurrentUser = Depends(require_user), body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    return {"item": content.set_status(user.email, item_id, str(body.get("status", "")))}


@router.delete("/content/{item_id}")
def delete_content(item_id: int, user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    if not content.delete_item(user.email, item_id):
        raise HTTPException(404, "Không tìm thấy nội dung.")
    return {"ok": True}


@router.post("/content/{item_id}/publish")
def publish_content(item_id: int, user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    return content.publish(user.email, item_id)


@router.get("/calendar")
def calendar(user: CurrentUser = Depends(require_user), start: Optional[str] = Query(None), days: int = Query(31)) -> Dict[str, Any]:
    try:
        items = content.list_calendar(user.email, start, days)
    except ValueError:
        raise HTTPException(400, "Ngày bắt đầu phải theo dạng YYYY-MM-DD.")
    from datetime import date, timedelta
    from app import vn_calendar
    s = date.fromisoformat(start) if start else date.today() - timedelta(days=3)
    return {"items": items, "holidays": vn_calendar.holidays_between(s, s + timedelta(days=max(1, min(days, 120)) - 1)),
            "legacy_rows": content.legacy_calendar_count(user.email)}


@router.delete("/calendar/legacy")
def clear_legacy(user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    return {"deleted": content.clear_legacy_calendar(user.email)}


@router.delete("/calendar/{row_id}")
def delete_calendar_row(row_id: int, user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    if not content.delete_calendar_row(user.email, row_id):
        raise HTTPException(404, "Không tìm thấy dòng lịch.")
    return {"ok": True}


@router.get("/holidays")
def holidays(user: CurrentUser = Depends(require_user), year: int = Query(...)) -> Dict[str, Any]:
    from app import vn_calendar
    if not (1900 <= year <= 2199):
        raise HTTPException(400, "Năm không hợp lệ.")
    return {"holidays": vn_calendar.holidays_for_year(year)}


@router.post("/compliance/check")
def compliance_check(user: CurrentUser = Depends(require_user), body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    text = str(body.get("text") or "")
    if not text.strip():
        raise HTTPException(400, "Dán nội dung cần kiểm.")
    if len(text) > 20000:
        raise HTTPException(400, "Nội dung quá dài (tối đa 20.000 ký tự).")
    kind = str(body.get("kind") or "post")
    if kind not in guardrails.PUBLIC_KINDS and kind != "internal":
        kind = "post"
    ctx = ctx_mod.load_context(user.email)
    result = guardrails.check({"text": text}, kind=kind, context=ctx, competitor_names=extras.known_competitors(user.email, ctx),
                              scarcity_evidence=str(body.get("scarcity_evidence") or ""))
    if kind == "kol_brief" or body.get("is_sponsored"):
        if not any(d in text.lower() for d in guardrails.DISCLOSURE):
            result["blockers"].append({"code": "G06", "message": "Nội dung tài trợ/KOL phải ghi rõ \"Quảng cáo\" hoặc \"Được tài trợ\"."})
    return result
