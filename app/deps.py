# -*- coding: utf-8 -*-
"""Phụ thuộc FastAPI dùng chung: lấy người dùng hiện tại, kiểm quyền quản trị."""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request

from app.security import user_from_token


@dataclass(frozen=True)
class CurrentUser:
    email: str
    is_admin: bool
    name: str = ""


def _bearer(request: Request) -> str:
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[7:].strip()
    return ""


def require_user(request: Request) -> CurrentUser:
    """Chỉ chấp nhận Bearer token hợp lệ. Không còn tin header X-User-Email hay tài khoản khách."""
    token = _bearer(request)
    user = user_from_token(token) if token else None
    if not user:
        raise HTTPException(status_code=401, detail="Phiên đăng nhập không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại.")
    return CurrentUser(email=user["email"], is_admin=bool(user.get("is_admin")), name=user.get("name") or "")


def require_admin(user: CurrentUser = Depends(require_user)) -> CurrentUser:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Chỉ quản trị viên được dùng chức năng này.")
    return user


def client_ip(request: Request) -> str:
    return request.client.host if request.client else ""
