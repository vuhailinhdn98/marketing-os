# -*- coding: utf-8 -*-
"""Sao lưu (xuất JSON), làm mới hoặc xóa toàn bộ dữ liệu của một workspace."""
from __future__ import annotations

import shutil
import time
from typing import Any, Dict

from app.database import connect, loads, normalize_email, rows
from app.services import media as media_service

TABLES = ["context_profiles", "context_versions", "research_records", "content_items", "performance_metrics", "calendar_schedules",
          "automation_logs", "discovered_competitors", "lead_records", "skill_runs", "budget_lines", "utm_links", "experiments",
          "data_imports", "data_rows", "media_jobs"]
JSON_COLS = {"data_json", "input_json", "output_json", "provenance_json", "guardrail_json", "evidence_json", "payload_json",
             "errors_json", "variants_json", "metadata_json"}


def export_workspace(owner: str) -> Dict[str, Any]:
    owner = normalize_email(owner)
    out: Dict[str, Any] = {"exported_at": time.strftime("%Y-%m-%d %H:%M:%S"), "owner": owner, "format": "marketing-os/4", "tables": {}}
    for table in TABLES:
        data = rows(f"SELECT * FROM {table} WHERE user_email = ?", (owner,))
        for r in data:
            r.pop("user_email", None)
            for col in list(r):
                if col in JSON_COLS and isinstance(r[col], str):
                    r[col] = loads(r[col], r[col])
        out["tables"][table] = data
    prof = rows("SELECT * FROM user_profiles WHERE user_email = ?", (owner,))
    for p in prof:
        p.pop("gemini_api_key", None)
        p.pop("user_email", None)
    out["tables"]["user_profiles"] = prof
    return out


def reset_workspace(owner: str) -> Dict[str, int]:
    owner = normalize_email(owner)
    counts: Dict[str, int] = {}
    media_dir = media_service._dir(owner)
    with connect() as conn:
        for table in TABLES:
            counts[table] = conn.execute(f"DELETE FROM {table} WHERE user_email = ?", (owner,)).rowcount
        conn.execute("UPDATE user_profiles SET brand_name = '', industry = '', products_services = '', price_range = '', "
                     "target_audience = '', competitors = '', channels = '', monthly_budget = 0, brand_voice = '', "
                     "phone_hotline = '', website_url = '', social_channels = '', usp_advantages = '' WHERE user_email = ?", (owner,))
    shutil.rmtree(media_dir, ignore_errors=True)
    return counts


def delete_account(owner: str) -> None:
    owner = normalize_email(owner)
    reset_workspace(owner)
    with connect() as conn:
        conn.execute("DELETE FROM user_profiles WHERE user_email = ?", (owner,))
        conn.execute("DELETE FROM auth_sessions WHERE email = ?", (owner,))
        conn.execute("DELETE FROM app_configs WHERE key = ?", (f"content_webhook_url:{owner}",))
        conn.execute("DELETE FROM app_users WHERE email = ?", (owner,))
