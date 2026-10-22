# -*- coding: utf-8 -*-
"""
Cấu hình tập trung cho Marketing OS.

Mọi giá trị đọc từ biến môi trường để chạy được cả trên máy cá nhân lẫn trên cloud.
Không có giá trị bí mật nào được ghi cứng trong mã nguồn.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parent.parent


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name: str) -> List[str]:
    raw = os.environ.get(name, "")
    return [x.strip().lower() for x in raw.split(",") if x.strip()]


@dataclass
class Settings:
    data_dir: Path = field(default_factory=lambda: Path(os.environ.get("DATA_DIR") or (ROOT / "data" / "runtime")))
    google_client_id: str = field(default_factory=lambda: os.environ.get("GOOGLE_CLIENT_ID", "").strip())
    admin_emails: List[str] = field(default_factory=lambda: _env_list("ADMIN_EMAILS"))
    server_gemini_key: str = field(default_factory=lambda: os.environ.get("GEMINI_API_KEY", "").strip())
    share_server_key: bool = field(default_factory=lambda: _env_bool("SHARE_SERVER_GEMINI_KEY", False))
    allow_registration: bool = field(default_factory=lambda: _env_bool("ALLOW_REGISTRATION", True))
    session_days: int = field(default_factory=lambda: int(os.environ.get("SESSION_DAYS", "30") or 30))
    # Cho phép tải trang web của đối thủ (có kiểm tra chống SSRF). Tắt nếu máy chủ không cần.
    allow_web_fetch: bool = field(default_factory=lambda: _env_bool("ALLOW_WEB_FETCH", True))

    @property
    def db_path(self) -> Path:
        return self.data_dir / "marketing_os.db"

    @property
    def legacy_db_path(self) -> Path:
        return ROOT / "data" / "marketing_os_app.db"

    @property
    def media_dir(self) -> Path:
        return self.data_dir / "media"

    @property
    def ephemeral_storage_risk(self) -> bool:
        """Render (gói free) và nhiều PaaS dùng ổ đĩa tạm: dữ liệu mất khi dịch vụ khởi động lại.
        Cảnh báo khi đang chạy trên Render mà chưa trỏ DATA_DIR vào ổ đĩa bền."""
        on_render = bool(os.environ.get("RENDER"))
        return on_render and not os.environ.get("DATA_DIR")


settings = Settings()


def reload_settings() -> Settings:
    """Dùng trong test: đọc lại biến môi trường."""
    global settings
    settings = Settings()
    return settings
