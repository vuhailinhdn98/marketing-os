# -*- coding: utf-8 -*-
"""Tạo ảnh (Gemini image / Nano Banana) và video (Veo) từ prompt; lưu file trong DATA_DIR/media."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from app import config, llm
from app.database import execute, normalize_email, one, rows

IMAGE_RATIOS = ["1:1", "4:5", "9:16", "16:9", "3:4", "4:3"]
VIDEO_RATIOS = ["16:9", "9:16"]
_EXT = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp", "video/mp4": "mp4"}

# Không tạo hình người nổi tiếng, nhân vật/thương hiệu có bản quyền
_BLOCKED = re.compile(r"\b(logo của|nhân vật|disney|marvel|pokemon|doraemon|mickey|hello kitty|coca[- ]?cola|starbucks|"
                      r"highlands|ronaldo|messi|sơn tùng|celebrity|người nổi tiếng)\b", re.I)


class MediaError(ValueError):
    pass


def _dir(owner: str) -> Path:
    d = config.settings.media_dir / hashlib.sha256(normalize_email(owner).encode()).hexdigest()[:16]
    d.mkdir(parents=True, exist_ok=True)
    return d


def _check_prompt(prompt: str) -> str:
    prompt = (prompt or "").strip()
    if len(prompt) < 10:
        raise MediaError("Prompt quá ngắn.")
    if len(prompt) > 2000:
        raise MediaError("Prompt quá dài (tối đa 2000 ký tự).")
    if _BLOCKED.search(prompt):
        raise MediaError("Prompt có người nổi tiếng hoặc nhân vật/thương hiệu có bản quyền. Hãy mô tả hình ảnh nguyên bản.")
    return prompt


def create_image(owner: str, key: str, prompt: str, ratio: str = "1:1") -> Dict[str, Any]:
    prompt = _check_prompt(prompt)
    if ratio not in IMAGE_RATIOS:
        raise MediaError("Tỉ lệ ảnh không hợp lệ.")
    job_id = execute("INSERT INTO media_jobs (user_email, kind, prompt, aspect_ratio, status) VALUES (?, 'image', ?, ?, 'running')",
                     (normalize_email(owner), prompt, ratio))
    try:
        data, mime, model = llm.generate_image(key, prompt, ratio)
    except llm.LLMError as exc:
        execute("UPDATE media_jobs SET status = 'failed', error = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (exc.message, job_id))
        return get_job(owner, job_id)  # type: ignore[return-value]
    name = f"{job_id}.{_EXT.get(mime, 'png')}"
    (_dir(owner) / name).write_bytes(data)
    execute("UPDATE media_jobs SET status = 'done', model = ?, file_name = ?, mime_type = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (model, name, mime, job_id))
    return get_job(owner, job_id)  # type: ignore[return-value]


def start_video(owner: str, key: str, prompt: str, ratio: str = "16:9") -> Dict[str, Any]:
    prompt = _check_prompt(prompt)
    if ratio not in VIDEO_RATIOS:
        raise MediaError("Tỉ lệ video chỉ hỗ trợ 16:9 hoặc 9:16.")
    job_id = execute("INSERT INTO media_jobs (user_email, kind, prompt, aspect_ratio, status) VALUES (?, 'video', ?, ?, 'running')",
                     (normalize_email(owner), prompt, ratio))
    try:
        op, model = llm.start_video(key, prompt, ratio)
    except llm.LLMError as exc:
        execute("UPDATE media_jobs SET status = 'failed', error = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (exc.message, job_id))
        return get_job(owner, job_id)  # type: ignore[return-value]
    execute("UPDATE media_jobs SET operation_name = ?, model = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (op, model, job_id))
    return get_job(owner, job_id)  # type: ignore[return-value]


def refresh_video(owner: str, key: str, job_id: int) -> Dict[str, Any]:
    job = get_job(owner, job_id)
    if not job:
        raise MediaError("Không tìm thấy tác vụ.")
    if job["kind"] != "video" or job["status"] != "running" or not job.get("operation_name"):
        return job
    res = llm.poll_video(key, job["operation_name"])
    if not res.get("done"):
        return {**job, "warning": res.get("warning")}
    if res.get("error"):
        execute("UPDATE media_jobs SET status = 'failed', error = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (res["error"], job_id))
    else:
        mime = res.get("mime") or "video/mp4"
        name = f"{job_id}.{_EXT.get(mime.split(';')[0], 'mp4')}"
        (_dir(owner) / name).write_bytes(res["bytes"])
        execute("UPDATE media_jobs SET status = 'done', file_name = ?, mime_type = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (name, mime.split(";")[0], job_id))
    return get_job(owner, job_id)  # type: ignore[return-value]


def get_job(owner: str, job_id: int) -> Optional[Dict[str, Any]]:
    return one("SELECT id, kind, prompt, aspect_ratio, model, status, mime_type, error, created_at, updated_at, file_name, operation_name "
               "FROM media_jobs WHERE id = ? AND user_email = ?", (job_id, normalize_email(owner)))


def list_jobs(owner: str) -> List[Dict[str, Any]]:
    return rows("SELECT id, kind, prompt, aspect_ratio, model, status, mime_type, error, created_at FROM media_jobs "
                "WHERE user_email = ? ORDER BY id DESC LIMIT 60", (normalize_email(owner),))


def file_path(owner: str, job_id: int) -> Optional[Path]:
    job = get_job(owner, job_id)
    if not job or job["status"] != "done" or not job.get("file_name"):
        return None
    path = _dir(owner) / job["file_name"]
    return path if path.exists() else None


def delete_job(owner: str, job_id: int) -> bool:
    path = file_path(owner, job_id)
    if path:
        path.unlink(missing_ok=True)
    return execute("DELETE FROM media_jobs WHERE id = ? AND user_email = ?", (job_id, normalize_email(owner))) > 0
