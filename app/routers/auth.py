# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Body, Depends, Request

from app import config
from app.database import get_app_config
from app.deps import CurrentUser, client_ip, require_user
from app import security
from app.security import public_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _ua(request: Request) -> str:
    return request.headers.get("user-agent", "")[:300]


def _sync_sheet(background: BackgroundTasks, user: dict) -> None:
    url = get_app_config("GOOGLE_SHEET_WEBHOOK_URL", "")
    if url:
        from app.google_sheets import dispatch_login_to_google_sheet
        background.add_task(dispatch_login_to_google_sheet, url, {
            "email": user["email"], "name": user.get("name", ""), "login_count": user.get("login_count", 1),
            "ip_address": "", "user_agent": "", "last_login": user.get("last_login", "")})


@router.get("/config")
def auth_config() -> Dict[str, Any]:
    return {"google_client_id": config.settings.google_client_id, "allow_registration": config.settings.allow_registration,
            "password_min_length": 8}


@router.post("/register")
def register(request: Request, background: BackgroundTasks, body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    security.check_rate_limit(str(body.get("email", "")), client_ip(request))
    user = security.register(str(body.get("email", "")), str(body.get("password", "")), str(body.get("name", "")))
    user, token = security.login(user["email"], str(body.get("password", "")), client_ip(request), _ua(request))
    _sync_sheet(background, user)
    return {"token": token, "user": public_user(user)}


@router.post("/login")
def login(request: Request, background: BackgroundTasks, body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    user, token = security.login(str(body.get("email", "")), str(body.get("password", "")), client_ip(request), _ua(request))
    _sync_sheet(background, user)
    return {"token": token, "user": public_user(user)}


@router.post("/google")
def login_google(request: Request, background: BackgroundTasks, body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    user, token = security.login_google(str(body.get("credential", "")), client_ip(request), _ua(request))
    _sync_sheet(background, user)
    return {"token": token, "user": public_user(user)}


@router.get("/me")
def me(user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    full = security.get_user(user.email) or {}
    return {"user": public_user(full)}


@router.post("/logout")
def logout(request: Request) -> Dict[str, Any]:
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        security.delete_session(header[7:].strip())
    return {"ok": True}


@router.post("/password")
def change_password(user: CurrentUser = Depends(require_user), body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    security.change_password(user.email, str(body.get("old_password", "")), str(body.get("new_password", "")))
    return {"ok": True, "message": "Đã đổi mật khẩu. Mọi phiên đăng nhập cũ đã bị đăng xuất."}
