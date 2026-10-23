# -*- coding: utf-8 -*-
"""Danh sách đối thủ: chỉ lưu đối thủ người dùng nhập hoặc có nguồn chứng minh."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.database import dumps, execute, loads, normalize_email, one, rows

TYPES = ["Trực tiếp", "Thứ cấp", "Gián tiếp"]


class CompetitorError(ValueError):
    pass


def _decorate(r: Dict[str, Any]) -> Dict[str, Any]:
    r["evidence"] = loads(r.pop("evidence_json", None), [])
    r["provenance"] = loads(r.pop("provenance_json", None), {})
    return r


def list_competitors(owner: str) -> List[Dict[str, Any]]:
    return [_decorate(r) for r in rows("SELECT * FROM discovered_competitors WHERE user_email = ? ORDER BY is_manual DESC, name",
                                       (normalize_email(owner),))]


def get_competitor(owner: str, comp_id: int) -> Optional[Dict[str, Any]]:
    r = one("SELECT * FROM discovered_competitors WHERE id = ? AND user_email = ?", (comp_id, normalize_email(owner)))
    return _decorate(r) if r else None


def add_manual(owner: str, data: Dict[str, Any]) -> Dict[str, Any]:
    name = str(data.get("name") or "").strip()
    if not name:
        raise CompetitorError("Thiếu tên đối thủ.")
    ctype = data.get("competitor_type") or "Trực tiếp"
    if ctype not in TYPES:
        raise CompetitorError("Loại đối thủ không hợp lệ.")
    owner = normalize_email(owner)
    existing = one("SELECT id FROM discovered_competitors WHERE user_email = ? AND LOWER(name) = LOWER(?)", (owner, name))
    vals = (str(data.get("website") or "")[:300], str(data.get("phone") or "")[:50], str(data.get("social") or "")[:300],
            str(data.get("notes") or "")[:2000], ctype, str(data.get("price_segment") or "")[:100], str(data.get("core_products") or "")[:500])
    if existing:
        execute("UPDATE discovered_competitors SET website = ?, phone = ?, social = ?, notes = ?, competitor_type = ?, price_segment = ?, "
                "core_products = ? WHERE id = ?", vals + (existing["id"],))
        return get_competitor(owner, existing["id"])  # type: ignore[return-value]
    comp_id = execute("INSERT INTO discovered_competitors (user_email, name, website, phone, social, notes, competitor_type, price_segment, "
                      "core_products, is_manual) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)", (owner, name[:200]) + vals)
    return get_competitor(owner, comp_id)  # type: ignore[return-value]


def save_from_discovery(owner: str, competitors: List[Dict[str, Any]], sources: List[Dict[str, str]], location: str) -> int:
    owner = normalize_email(owner)
    saved = 0
    for c in competitors:
        name = str(c.get("name") or "").strip()
        if not name:
            continue
        evidence = [sources[i - 1] for i in c.get("source_ids") or [] if 1 <= i <= len(sources)]
        existing = one("SELECT id FROM discovered_competitors WHERE user_email = ? AND LOWER(name) = LOWER(?)", (owner, name))
        fields = (str(c.get("website") or "")[:300], c.get("type") if c.get("type") in TYPES else "Trực tiếp",
                  str(c.get("price_info") or "")[:200], str(c.get("what_they_sell") or "")[:500], dumps(evidence), location[:100])
        if existing:
            execute("UPDATE discovered_competitors SET website = COALESCE(NULLIF(?, ''), website), competitor_type = ?, price_segment = ?, "
                    "core_products = ?, evidence_json = ?, market_context = ?, scanned_at = CURRENT_TIMESTAMP WHERE id = ?",
                    fields + (existing["id"],))
        else:
            execute("INSERT INTO discovered_competitors (user_email, name, website, competitor_type, price_segment, core_products, "
                    "evidence_json, market_context, is_manual, scanned_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP)",
                    (owner, name[:200]) + fields)
        saved += 1
    return saved


def save_dossier(owner: str, name: str, markdown: str, provenance: Dict[str, Any], website: str = "", phone: str = "", social: str = "") -> Dict[str, Any]:
    owner = normalize_email(owner)
    existing = one("SELECT id FROM discovered_competitors WHERE user_email = ? AND LOWER(name) = LOWER(?)", (owner, name))
    if existing:
        comp_id = existing["id"]
        execute("UPDATE discovered_competitors SET battlecard_content = ?, provenance_json = ?, "
                "website = COALESCE(NULLIF(?, ''), website), phone = COALESCE(NULLIF(?, ''), phone), "
                "social = COALESCE(NULLIF(?, ''), social), scanned_at = CURRENT_TIMESTAMP WHERE id = ?",
                (markdown, dumps(provenance), website[:300], phone[:50], social[:300], comp_id))
    else:
        comp_id = execute("INSERT INTO discovered_competitors (user_email, name, website, phone, social, battlecard_content, provenance_json, is_manual, scanned_at) "
                          "VALUES (?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)",
                          (owner, name[:200], website[:300], phone[:50], social[:300], markdown, dumps(provenance)))
    return get_competitor(owner, comp_id)  # type: ignore[return-value]


def delete_competitor(owner: str, comp_id: int) -> bool:
    return execute("DELETE FROM discovered_competitors WHERE id = ? AND user_email = ?", (comp_id, normalize_email(owner))) > 0


def clear_all(owner: str) -> int:
    return execute("DELETE FROM discovered_competitors WHERE user_email = ?", (normalize_email(owner),))
