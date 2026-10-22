# -*- coding: utf-8 -*-
"""Hồ sơ bối cảnh, cài đặt AI, trạng thái hệ thống, sao lưu/làm mới workspace."""
from __future__ import annotations

import json
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query
from fastapi.responses import Response

from app import config, context as ctx_mod, llm
from app.database import get_automation_logs, log_automation, one
from app.deps import CurrentUser, require_user
from app.services import content as content_service
from app.services import runner, workspace
from app.security import get_user, rotate_ingest_secret

router = APIRouter(prefix="/api", tags=["core"])


@router.get("/system/status")
def system_status(user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    ai = runner.ai_settings(user.email)
    server_key = bool(config.settings.server_gemini_key) and (user.is_admin or config.settings.share_server_key)
    return {"version": "4.0.0", "ephemeral_storage": config.settings.ephemeral_storage_risk,
            "ai": {**ai, "server_key_available": server_key}, "web_fetch": config.settings.allow_web_fetch,
            "google_login": bool(config.settings.google_client_id)}


# --------------------------- Cài đặt AI ------------------------------------

@router.get("/settings/ai")
def get_ai(user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    return runner.ai_settings(user.email)


@router.post("/settings/ai")
def set_ai(user: CurrentUser = Depends(require_user), body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    try:
        return runner.save_ai_settings(user.email, api_key=body.get("api_key"), clear_key=bool(body.get("clear_key")),
                                       model=body.get("model"))
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@router.post("/settings/ai/check")
def check_ai(user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    key, source = runner.resolve_key(user.email, user.is_admin)
    if not key:
        return {"ok": False, "error": "Chưa có Gemini API key."}
    result = llm.check_key(key)
    result["key_source"] = source
    return result


@router.get("/settings/webhook")
def get_webhook(user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    return {"content_webhook_url": content_service.webhook_url(user.email)}


@router.post("/settings/webhook")
def set_webhook(user: CurrentUser = Depends(require_user), body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    try:
        return {"content_webhook_url": content_service.set_webhook_url(user.email, str(body.get("content_webhook_url") or ""))}
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@router.get("/settings/ingest")
def ingest_info(user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    u = get_user(user.email) or {}
    secret = u.get("ingest_secret") or rotate_ingest_secret(user.email)
    return {"path": f"/api/leads/ingest/{secret}", "secret_hint": secret[:4] + "…"}


@router.post("/settings/ingest/rotate")
def ingest_rotate(user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    secret = rotate_ingest_secret(user.email)
    return {"path": f"/api/leads/ingest/{secret}"}


# --------------------------- Hồ sơ bối cảnh --------------------------------

@router.get("/context")
def get_context(user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    data = ctx_mod.load_context(user.email)
    return {"context": data, "completeness": ctx_mod.completeness(data), "fields": ctx_mod.field_catalog()}


@router.patch("/context")
def patch_context(user: CurrentUser = Depends(require_user), body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    patch = body.get("patch")
    if not isinstance(patch, dict) or not patch:
        raise HTTPException(400, "Thiếu dữ liệu cập nhật.")
    try:
        data = ctx_mod.save_context(user.email, patch, str(body.get("note") or ""))
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return {"context": data, "completeness": ctx_mod.completeness(data)}


@router.get("/context/questions")
def context_questions(user: CurrentUser = Depends(require_user), focus: str = Query(""), limit: int = Query(5)) -> Dict[str, Any]:
    data = ctx_mod.load_context(user.email)
    focus_list = [f for f in focus.split(",") if f]
    return {"questions": ctx_mod.next_questions(data, focus_list, limit)}


@router.get("/context/versions")
def context_versions(user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    return {"versions": ctx_mod.list_versions(user.email)}


@router.get("/context/export")
def context_export(user: CurrentUser = Depends(require_user)) -> Response:
    data = ctx_mod.load_context(user.email)
    return Response(json.dumps(data, ensure_ascii=False, indent=2), media_type="application/json",
                    headers={"Content-Disposition": "attachment; filename=ho-so-boi-canh.json"})


# --------------------------- Workspace -------------------------------------

@router.get("/workspace/export")
def export_ws(user: CurrentUser = Depends(require_user)) -> Response:
    data = workspace.export_workspace(user.email)
    return Response(json.dumps(data, ensure_ascii=False, indent=1, default=str), media_type="application/json",
                    headers={"Content-Disposition": "attachment; filename=marketing-os-sao-luu.json"})


@router.post("/workspace/reset")
def reset_ws(user: CurrentUser = Depends(require_user), body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    if body.get("confirm") != "XOA":
        raise HTTPException(400, "Gõ XOA để xác nhận làm mới toàn bộ dữ liệu workspace.")
    counts = workspace.reset_workspace(user.email)
    return {"ok": True, "deleted": counts}


@router.delete("/account")
def delete_account(user: CurrentUser = Depends(require_user), body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    if body.get("confirm") != user.email:
        raise HTTPException(400, "Nhập đúng email của bạn để xác nhận xóa tài khoản.")
    workspace.delete_account(user.email)
    return {"ok": True}


# --------------------------- Nhật ký & khởi động nhanh ----------------------

@router.get("/autopilot/status")
def autopilot_status(user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    data = ctx_mod.load_context(user.email)
    counts = {}
    for key, sql in (("content", "SELECT COUNT(*) AS n FROM content_items WHERE user_email = ?"),
                     ("calendar", "SELECT COUNT(*) AS n FROM calendar_schedules WHERE user_email = ? AND plan_date >= date('now','localtime')"),
                     ("competitors", "SELECT COUNT(*) AS n FROM discovered_competitors WHERE user_email = ?"),
                     ("leads", "SELECT COUNT(*) AS n FROM lead_records WHERE user_email = ?"),
                     ("runs", "SELECT COUNT(*) AS n FROM skill_runs WHERE user_email = ?")):
        r = one(sql, (user.email,))
        counts[key] = int(r["n"]) if r else 0
    return {"completeness": ctx_mod.completeness(data), "counts": counts, "logs": get_automation_logs(user.email, 30)}


def _quickstart(email: str, is_admin: bool, start_date: str) -> None:
    from app.services import content as content_service_local
    steps = [("content_pillars", {}, "Trụ cột nội dung"),
             ("content_calendar", None, "Lịch nội dung 14 ngày"),
             ("marketing_ideas", {"stage": "Giai đoạn đầu", "budget_level": "Ít tiền"}, "Ý tưởng marketing")]
    data = ctx_mod.load_context(email)
    channels = [str(c) for c in (data.get("channels_active") or [])][:4]
    log_automation(email, "QUICKSTART", "Khởi động nhanh", "RUNNING", "Bắt đầu chạy 3 tác vụ nền tảng")
    for task_id, inputs, label in steps:
        if inputs is None:
            inputs = {"start_date": start_date, "days": 14, "channels": channels, "posts_per_day": 1}
        res = runner.run_task(email, is_admin, task_id, inputs)
        status = res.get("status")
        if status == "ok":
            if task_id == "content_calendar":
                content_service_local.save_calendar(email, res["output"].get("rows", []), res["provenance"])
            log_automation(email, task_id.upper(), label, "SUCCESS", f"Xong (lần chạy #{res.get('run_id')})")
        elif status == "needs_context":
            log_automation(email, task_id.upper(), label, "SKIPPED", "Thiếu hồ sơ: " + ", ".join(m["label"] for m in res["missing"]))
        elif status == "invalid_input":
            log_automation(email, task_id.upper(), label, "SKIPPED", "; ".join(res["errors"]))
        else:
            err = (res.get("provenance") or {}).get("error") or res.get("message") or "Lỗi không rõ"
            log_automation(email, task_id.upper(), label, "FAILED", err)
            if (res.get("provenance") or {}).get("error_code") in ("no_key", "invalid_key", "forbidden"):
                break
    log_automation(email, "QUICKSTART", "Khởi động nhanh", "DONE", "Kết thúc. Xem từng bước ở trên.")


@router.post("/autopilot/run")
def autopilot_run(background: BackgroundTasks, user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    from datetime import date
    background.add_task(_quickstart, user.email, user.is_admin, date.today().isoformat())
    return {"ok": True, "message": "Đã bắt đầu Khởi động nhanh. Theo dõi tiến độ ở Nhật ký."}
