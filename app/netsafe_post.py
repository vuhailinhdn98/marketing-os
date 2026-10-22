# -*- coding: utf-8 -*-
"""Gửi webhook ra ngoài an toàn: chỉ https công khai, không theo chuyển hướng, báo đúng kết quả."""
from __future__ import annotations

from typing import Any, Dict, Tuple
from urllib.parse import urlparse

import requests

from app.netsafe import USER_AGENT, _host_is_public


def validate_webhook_url(url: str) -> str:
    url = (url or "").strip()
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Webhook phải là địa chỉ https://")
    if not _host_is_public(parsed.hostname):
        raise ValueError("Webhook phải trỏ tới máy chủ công khai.")
    return url


def post_json(url: str, payload: Dict[str, Any], timeout: float = 10.0) -> Tuple[bool, str]:
    """Trả (thành_công, mô_tả). Thành công chỉ khi máy nhận trả mã 2xx."""
    try:
        url = validate_webhook_url(url)
    except ValueError as exc:
        return False, str(exc)
    try:
        resp = requests.post(url, json=payload, timeout=(5, timeout), allow_redirects=False,
                             headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"})
    except requests.RequestException as exc:
        return False, f"Không gửi được: {exc.__class__.__name__}"
    if 200 <= resp.status_code < 300:
        return True, f"Máy nhận trả HTTP {resp.status_code}"
    return False, f"Máy nhận trả HTTP {resp.status_code}"
