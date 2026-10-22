# -*- coding: utf-8 -*-
"""
Xác thực và phiên đăng nhập.

- Mật khẩu băm bằng scrypt (thư viện chuẩn), so sánh hằng thời gian.
- Token phiên ngẫu nhiên 256 bit; DB chỉ lưu SHA-256 của token, có hạn dùng.
- Đăng nhập Google chỉ bật khi có GOOGLE_CLIENT_ID và ID token được Google xác minh.
- Chặn dò mật khẩu: tối đa 8 lần sai / 15 phút cho mỗi cặp email + IP.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import re
import secrets
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple

from app import config
from app.database import execute, normalize_email, one, rows

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_SCRYPT_N, _SCRYPT_R, _SCRYPT_P = 2 ** 14, 8, 1


class AuthError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message = message
        self.status = status


def valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email or "")) and len(email) <= 254


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=64)
    return "scrypt${}${}${}${}${}".format(
        _SCRYPT_N, _SCRYPT_R, _SCRYPT_P,
        base64.b64encode(salt).decode(), base64.b64encode(digest).decode(),
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, n, r, p, salt_b64, hash_b64 = stored.split("$")
        if algo != "scrypt":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
        digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=int(n), r=int(r), p=int(p), dklen=len(expected))
        return hmac.compare_digest(digest, expected)
    except (ValueError, TypeError):
        return False


def password_problem(password: str) -> Optional[str]:
    if len(password or "") < 8:
        return "Mật khẩu cần ít nhất 8 ký tự."
    if len(password) > 256:
        return "Mật khẩu quá dài."
    if password.isdigit() or password.isalpha():
        return "Mật khẩu cần có cả chữ và số."
    return None


# ---------------------------------------------------------------------------
# Chống dò mật khẩu
# ---------------------------------------------------------------------------

_attempts: Dict[str, list] = {}
_attempts_lock = threading.Lock()
MAX_FAILS = 8
WINDOW_SECONDS = 15 * 60


def _attempt_key(email: str, ip: str) -> str:
    return f"{normalize_email(email)}|{ip}"


def check_rate_limit(email: str, ip: str) -> None:
    now = time.time()
    key = _attempt_key(email, ip)
    with _attempts_lock:
        recent = [t for t in _attempts.get(key, []) if now - t < WINDOW_SECONDS]
        _attempts[key] = recent
        if len(recent) >= MAX_FAILS:
            raise AuthError("Sai quá nhiều lần. Vui lòng thử lại sau 15 phút.", 429)


def record_failure(email: str, ip: str) -> None:
    with _attempts_lock:
        _attempts.setdefault(_attempt_key(email, ip), []).append(time.time())


def clear_failures(email: str, ip: str) -> None:
    with _attempts_lock:
        _attempts.pop(_attempt_key(email, ip), None)


def reset_rate_limits() -> None:
    with _attempts_lock:
        _attempts.clear()


# ---------------------------------------------------------------------------
# Người dùng
# ---------------------------------------------------------------------------

def get_user(email: str) -> Optional[dict]:
    return one("SELECT * FROM app_users WHERE email = ?", (normalize_email(email),))


def public_user(user: dict) -> dict:
    return {
        "email": user["email"],
        "name": user.get("name") or user["email"].split("@")[0],
        "picture": user.get("picture") or "",
        "is_admin": bool(user.get("is_admin")),
        "auth_provider": user.get("auth_provider") or "password",
    }


def _should_be_admin(email: str) -> bool:
    admins = config.settings.admin_emails
    if admins:
        return email in admins
    # Chưa cấu hình ADMIN_EMAILS: tài khoản có mật khẩu/Google đầu tiên là quản trị viên
    existing = one("SELECT COUNT(*) AS n FROM app_users WHERE is_admin = 1")
    return not existing or existing["n"] == 0


def _touch_login(email: str, ip: str, user_agent: str) -> None:
    execute(
        "UPDATE app_users SET login_count = COALESCE(login_count, 0) + 1, last_login = CURRENT_TIMESTAMP, "
        "ip_address = ?, user_agent = ? WHERE email = ?",
        (ip[:64], user_agent[:300], email),
    )


def register(email: str, password: str, name: str = "") -> dict:
    email = normalize_email(email)
    if not valid_email(email):
        raise AuthError("Email không hợp lệ.")
    problem = password_problem(password)
    if problem:
        raise AuthError(problem)
    existing = get_user(email)
    if existing and existing.get("password_hash"):
        raise AuthError("Email này đã có tài khoản. Hãy đăng nhập.", 409)
    if existing and existing.get("auth_provider") == "google":
        raise AuthError("Email này đăng nhập bằng Google.", 409)
    if not existing and not config.settings.allow_registration:
        raise AuthError("Máy chủ đang tắt đăng ký tài khoản mới.", 403)
    is_admin = 1 if _should_be_admin(email) else 0
    pw = hash_password(password)
    if existing:
        # Tài khoản cũ (bản trước chỉ nhập email, không có mật khẩu) được đặt mật khẩu lần đầu
        execute(
            "UPDATE app_users SET password_hash = ?, auth_provider = 'password', "
            "is_admin = MAX(COALESCE(is_admin, 0), ?), name = COALESCE(NULLIF(?, ''), name) WHERE email = ?",
            (pw, is_admin, name.strip(), email),
        )
    else:
        execute(
            "INSERT INTO app_users (email, name, password_hash, is_admin, auth_provider, login_count, ingest_secret) "
            "VALUES (?, ?, ?, ?, 'password', 0, ?)",
            (email, name.strip() or email.split("@")[0], pw, is_admin, secrets.token_urlsafe(24)),
        )
    return get_user(email)  # type: ignore[return-value]


def login(email: str, password: str, ip: str, user_agent: str) -> Tuple[dict, str]:
    email = normalize_email(email)
    check_rate_limit(email, ip)
    user = get_user(email)
    if not user or not user.get("password_hash") or not verify_password(password, user["password_hash"]):
        record_failure(email, ip)
        raise AuthError("Email hoặc mật khẩu không đúng.", 401)
    clear_failures(email, ip)
    _ensure_ingest_secret(email)
    _touch_login(email, ip, user_agent)
    return get_user(email), create_session(email, user_agent)  # type: ignore[return-value]


def verify_google_credential(credential: str) -> dict:
    client_id = config.settings.google_client_id
    if not client_id:
        raise AuthError("Đăng nhập Google chưa được bật trên máy chủ (thiếu GOOGLE_CLIENT_ID).", 400)
    if not credential:
        raise AuthError("Thiếu Google credential.", 400)
    try:
        from google.auth.transport import requests as g_requests
        from google.oauth2 import id_token
    except ImportError as exc:  # pragma: no cover - phụ thuộc môi trường
        raise AuthError("Máy chủ thiếu thư viện google-auth.", 500) from exc
    try:
        info = id_token.verify_oauth2_token(credential, g_requests.Request(), client_id)
    except Exception as exc:  # thư viện ném nhiều loại lỗi khác nhau
        raise AuthError("Google không xác minh được phiên đăng nhập.", 401) from exc
    if not info.get("email") or not info.get("email_verified"):
        raise AuthError("Email Google chưa được xác minh.", 401)
    return info


def login_google(credential: str, ip: str, user_agent: str) -> Tuple[dict, str]:
    info = verify_google_credential(credential)
    email = normalize_email(info["email"])
    existing = get_user(email)
    if existing and existing.get("password_hash") and existing.get("auth_provider") != "google":
        raise AuthError("Email này đã đăng ký bằng mật khẩu. Hãy đăng nhập bằng mật khẩu.", 409)
    if not existing:
        if not config.settings.allow_registration:
            raise AuthError("Máy chủ đang tắt đăng ký tài khoản mới.", 403)
        execute(
            "INSERT INTO app_users (email, name, picture, is_admin, auth_provider, login_count, ingest_secret) "
            "VALUES (?, ?, ?, ?, 'google', 0, ?)",
            (email, info.get("name", ""), info.get("picture", ""), 1 if _should_be_admin(email) else 0,
             secrets.token_urlsafe(24)),
        )
    else:
        execute(
            "UPDATE app_users SET auth_provider = 'google', name = COALESCE(NULLIF(?, ''), name), "
            "picture = COALESCE(NULLIF(?, ''), picture) WHERE email = ?",
            (info.get("name", ""), info.get("picture", ""), email),
        )
    _ensure_ingest_secret(email)
    _touch_login(email, ip, user_agent)
    return get_user(email), create_session(email, user_agent)  # type: ignore[return-value]


def _ensure_ingest_secret(email: str) -> None:
    user = get_user(email)
    if user and not user.get("ingest_secret"):
        execute("UPDATE app_users SET ingest_secret = ? WHERE email = ?", (secrets.token_urlsafe(24), email))


def rotate_ingest_secret(email: str) -> str:
    secret = secrets.token_urlsafe(24)
    execute("UPDATE app_users SET ingest_secret = ? WHERE email = ?", (secret, normalize_email(email)))
    return secret


def user_by_ingest_secret(secret: str) -> Optional[dict]:
    if not secret or len(secret) < 16:
        return None
    return one("SELECT * FROM app_users WHERE ingest_secret = ?", (secret,))


def change_password(email: str, old_password: str, new_password: str) -> None:
    user = get_user(email)
    if not user or not user.get("password_hash") or not verify_password(old_password, user["password_hash"]):
        raise AuthError("Mật khẩu hiện tại không đúng.", 401)
    problem = password_problem(new_password)
    if problem:
        raise AuthError(problem)
    execute("UPDATE app_users SET password_hash = ? WHERE email = ?", (hash_password(new_password), user["email"]))
    # Đăng xuất mọi phiên khác
    execute("DELETE FROM auth_sessions WHERE email = ?", (user["email"],))


# ---------------------------------------------------------------------------
# Phiên
# ---------------------------------------------------------------------------

def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def create_session(email: str, user_agent: str = "") -> str:
    token = secrets.token_urlsafe(32)
    expires = _now() + timedelta(days=config.settings.session_days)
    execute(
        "INSERT INTO auth_sessions (token_hash, email, expires_at, user_agent) VALUES (?, ?, ?, ?)",
        (_hash_token(token), normalize_email(email), expires.isoformat(), user_agent[:300]),
    )
    return token


def user_from_token(token: str) -> Optional[dict]:
    if not token or len(token) > 200:
        return None
    row = one(
        "SELECT s.expires_at, u.* FROM auth_sessions s JOIN app_users u ON u.email = s.email WHERE s.token_hash = ?",
        (_hash_token(token),),
    )
    if not row:
        return None
    try:
        expires = datetime.fromisoformat(row["expires_at"])
    except (TypeError, ValueError):
        return None
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires <= _now():
        execute("DELETE FROM auth_sessions WHERE token_hash = ?", (_hash_token(token),))
        return None
    return row


def delete_session(token: str) -> None:
    if token:
        execute("DELETE FROM auth_sessions WHERE token_hash = ?", (_hash_token(token),))


def purge_expired_sessions() -> None:
    execute("DELETE FROM auth_sessions WHERE expires_at <= ?", (_now().isoformat(),))


def list_users() -> list:
    return rows(
        "SELECT u.email, u.name, u.is_admin, u.auth_provider, u.login_count, u.created_at, u.last_login, "
        "p.brand_name, p.industry FROM app_users u LEFT JOIN user_profiles p ON p.user_email = u.email "
        "ORDER BY u.last_login DESC"
    )
