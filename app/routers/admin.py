# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import io
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException
from fastapi.responses import Response

from app.database import get_app_config, loads, rows, set_app_config
from app.deps import CurrentUser, require_admin, require_user
from app.google_sheets import dispatch_login_to_google_sheet, get_google_apps_script_template
from app.security import list_users

router = APIRouter(prefix="/api", tags=["admin"])


@router.get("/admin/users")
def admin_users(user: CurrentUser = Depends(require_admin)) -> Dict[str, Any]:
    data = list_users()
    return {"users": data, "total": len(data)}


@router.get("/admin/users.csv")
def admin_users_csv(user: CurrentUser = Depends(require_admin)) -> Response:
    out = io.StringIO()
    out.write("﻿")
    w = csv.writer(out)
    w.writerow(["Email", "Tên", "Quản trị", "Đăng nhập bằng", "Số lần đăng nhập", "Thương hiệu", "Ngành", "Tạo lúc", "Đăng nhập gần nhất"])
    for u in list_users():
        w.writerow([u["email"], u.get("name") or "", "Có" if u.get("is_admin") else "", u.get("auth_provider") or "",
                    u.get("login_count") or 0, u.get("brand_name") or "", u.get("industry") or "", u.get("created_at") or "", u.get("last_login") or ""])
    return Response(out.getvalue().encode("utf-8"), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=nguoi-dung.csv"})


@router.get("/admin/sheets")
def sheets_config(user: CurrentUser = Depends(require_admin)) -> Dict[str, Any]:
    url = get_app_config("GOOGLE_SHEET_WEBHOOK_URL", "")
    return {"webhook_url": url, "connected": bool(url), "apps_script_template": get_google_apps_script_template()}


@router.post("/admin/sheets")
def set_sheets(user: CurrentUser = Depends(require_admin), body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    url = str(body.get("webhook_url") or "").strip()
    if url and not url.startswith("https://script.google.com/"):
        raise HTTPException(400, "URL phải là Web App của Google Apps Script (https://script.google.com/...).")
    set_app_config("GOOGLE_SHEET_WEBHOOK_URL", url)
    return {"webhook_url": url}


@router.post("/admin/sheets/sync")
def sync_sheets(background: BackgroundTasks, user: CurrentUser = Depends(require_admin)) -> Dict[str, Any]:
    url = get_app_config("GOOGLE_SHEET_WEBHOOK_URL", "")
    if not url:
        raise HTTPException(400, "Chưa cấu hình URL Google Sheet.")
    users = list_users()
    for u in users:
        background.add_task(dispatch_login_to_google_sheet, url, {"email": u["email"], "name": u.get("name") or "",
                                                                 "login_count": u.get("login_count") or 0, "ip_address": "",
                                                                 "user_agent": "", "last_login": u.get("last_login") or ""})
    return {"queued": len(users)}


@router.get("/legacy/research")
def legacy_research(user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    """Kết quả do phiên bản cũ tạo (có thể chứa số liệu tự chế) — chỉ xem, có cảnh báo."""
    data = rows("SELECT id, category, title, content, created_at, provenance_json FROM research_records WHERE user_email = ? "
                "ORDER BY id DESC LIMIT 30", (user.email,))
    for r in data:
        r["legacy"] = not loads(r.pop("provenance_json", None), None)
    return {"items": data, "warning": "Các bản này tạo bởi phiên bản cũ, khi AI lỗi hệ thống tự chèn số liệu và nguồn tự chế. "
                                     "Đừng dùng số liệu trong đó khi chưa kiểm chứng."}
