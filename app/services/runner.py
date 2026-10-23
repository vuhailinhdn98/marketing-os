# -*- coding: utf-8 -*-
"""
Bộ chạy tác vụ của Skill Engine:
kiểm ô nhập → kiểm hồ sơ (thiếu thì hỏi) → nạp dữ liệu thật → (tìm kiếm Google nếu cần) → AI trả JSON đúng schema
→ hậu xử lý bằng code → cổng tuân thủ → lưu lịch sử kèm nguồn gốc.
"""
from __future__ import annotations

import time
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from app import config, guardrails, llm
from app.context import load_context, missing_fields, render_for_prompt
from app.database import dumps, execute, loads, normalize_email, one, rows
from app.skills import system_prompt
from app.skills.registry import Task, get_task
from app.services import extras as extras_mod
from app.services.render import to_markdown

TEXT_LIMIT = 500
TEXTAREA_LIMIT = 12000


class TaskInputError(ValueError):
    def __init__(self, errors: List[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


# ---------------------------------------------------------------------------
# Cài đặt AI của người dùng
# ---------------------------------------------------------------------------

def ai_settings(email: str) -> Dict[str, Any]:
    email = normalize_email(email)
    row = one("SELECT gemini_api_key, gemini_model FROM user_profiles WHERE user_email = ?", (email,)) or {}
    key = (row.get("gemini_api_key") or "").strip()
    return {"has_key": bool(key), "key_hint": f"…{key[-4:]}" if len(key) >= 8 else "", "model": row.get("gemini_model") or ""}


def save_ai_settings(email: str, *, api_key: Optional[str] = None, clear_key: bool = False, model: Optional[str] = None) -> Dict[str, Any]:
    email = normalize_email(email)
    execute("INSERT OR IGNORE INTO user_profiles (user_email) VALUES (?)", (email,))
    if clear_key:
        execute("UPDATE user_profiles SET gemini_api_key = '' WHERE user_email = ?", (email,))
    elif api_key is not None and api_key.strip():
        key = api_key.strip()
        if len(key) < 20 or len(key) > 200 or any(c.isspace() for c in key):
            raise ValueError("API key không đúng định dạng.")
        execute("UPDATE user_profiles SET gemini_api_key = ? WHERE user_email = ?", (key, email))
    if model is not None:
        execute("UPDATE user_profiles SET gemini_model = ? WHERE user_email = ?", (model.strip()[:80], email))
    return ai_settings(email)


def resolve_key(email: str, is_admin: bool) -> Tuple[str, str]:
    row = one("SELECT gemini_api_key FROM user_profiles WHERE user_email = ?", (normalize_email(email),)) or {}
    key = (row.get("gemini_api_key") or "").strip()
    if key:
        return key, "user"
    server = config.settings.server_gemini_key
    if server and (is_admin or config.settings.share_server_key):
        return server, "server"
    return "", ""


# ---------------------------------------------------------------------------
# Kiểm ô nhập
# ---------------------------------------------------------------------------

def validate_inputs(task: Task, raw: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    errors: List[str] = []
    channels = [str(c) for c in (ctx.get("channels_active") or [])]
    for spec in task.inputs:
        name, label, typ = spec["name"], spec["label"], spec["type"]
        val = raw.get(name, spec.get("default"))
        if typ == "checkbox":
            out[name] = bool(val) and val not in ("false", "0", 0)
            continue
        empty = val is None or (isinstance(val, str) and not val.strip()) or (isinstance(val, list) and not val)
        if empty:
            if spec.get("required"):
                errors.append(f"Thiếu \"{label}\".")
            continue
        if typ == "number":
            try:
                num = float(val)
            except (TypeError, ValueError):
                errors.append(f"\"{label}\" phải là số.")
                continue
            if num < 0:
                errors.append(f"\"{label}\" không được âm.")
                continue
            out[name] = num
        elif typ == "date":
            try:
                out[name] = date.fromisoformat(str(val)[:10]).isoformat()
            except ValueError:
                errors.append(f"\"{label}\" phải là ngày dạng YYYY-MM-DD.")
        elif typ == "select":
            options = spec.get("options") or []
            if isinstance(options, list) and options and val not in options:
                errors.append(f"\"{label}\" không hợp lệ.")
                continue
            out[name] = val
        elif typ == "multiselect":
            values = val if isinstance(val, list) else [x.strip() for x in str(val).split(",") if x.strip()]
            allowed = channels if spec.get("options") == "channels" else (spec.get("options") or [])
            bad = [v for v in values if allowed and v not in allowed]
            if bad:
                errors.append(f"\"{label}\": {', '.join(bad)} không có trong danh sách (kênh lấy từ hồ sơ bối cảnh).")
                continue
            out[name] = values[:12]
        else:
            text = str(val).strip()
            limit = TEXTAREA_LIMIT if typ == "textarea" else TEXT_LIMIT
            if len(text) > limit:
                errors.append(f"\"{label}\" quá dài (tối đa {limit} ký tự).")
                continue
            out[name] = text
    # Ràng buộc riêng
    if task.id == "content_calendar":
        d = out.get("days")
        if d is not None and not (7 <= d <= 31):
            errors.append("Số ngày phải từ 7 đến 31.")
        p = out.get("posts_per_day", 1)
        if not (1 <= p <= 3):
            errors.append("Mỗi ngày 1–3 bài.")
        out["days"] = int(out.get("days") or 14)
        out["posts_per_day"] = int(p)
    if task.id == "ads_plan":
        if out.get("daily_budget_vnd", 0) <= 0:
            errors.append("Ngân sách/ngày phải lớn hơn 0.")
        if not (1 <= int(out.get("days") or 14) <= 90):
            errors.append("Số ngày chạy phải từ 1 đến 90.")
    if errors:
        raise TaskInputError(errors)
    return out


# ---------------------------------------------------------------------------
# Chạy tác vụ
# ---------------------------------------------------------------------------

def _format_inputs(task: Task, inputs: Dict[str, Any]) -> str:
    lines = []
    for spec in task.inputs:
        if spec["name"] in inputs:
            v = inputs[spec["name"]]
            if isinstance(v, list):
                v = ", ".join(map(str, v))
            elif isinstance(v, bool):
                v = "Có" if v else "Không"
            lines.append(f"- {spec['label']}: {v}")
    return "\n".join(lines) or "- (không có)"


def _sources_block(sources: List[Dict[str, str]]) -> str:
    if not sources:
        return "DANH SÁCH NGUỒN: (không có nguồn nào — mọi con số phải gắn [Unverified] hoặc bỏ)"
    return "DANH SÁCH NGUỒN:\n" + "\n".join(f"[{i}] {s.get('title') or ''} — {s.get('url')}" for i, s in enumerate(sources, 1))



def _clean_search_query(task: Task, inputs: Dict[str, Any], ctx: Dict[str, Any]) -> str:
    brand = ctx.get("brand") or {}
    product = (ctx.get("product") or {}).get("one_liner", "")
    loc = inputs.get("location", "")
    if task.id == "competitor_discovery":
        import re
        ind = brand.get("industry", "")
        prod_words = [w for w in re.sub(r"[^\w\s]", " ", product).split() if len(w) > 1]
        prod_kw = " ".join(prod_words[:5]) if prod_words else ""
        parts = []
        if ind:
            parts.append(ind)
        if prod_kw and prod_kw.lower() not in (ind or "").lower():
            parts.append(prod_kw)
        if loc:
            parts.append(loc)
        q = " ".join(parts).strip()
        return q or f"đối thủ {loc}".strip()
    if task.id == "competitor_dossier":
        comp = inputs.get("competitor_name", "")
        ind = brand.get("industry", "")
        loc_val = (ctx.get("market") or {}).get("location") or ""
        return f"{comp} {ind} {loc_val}".strip()
    if task.id == "market_research":
        obj = inputs.get("objective", "")
        ind = brand.get("industry", "")
        return f"{obj} {ind} {loc}".strip()
    return f"{inputs.get('query') or loc or ''}".strip()

def _research_prompt(task: Task, inputs: Dict[str, Any], ctx: Dict[str, Any]) -> str:
    brand = ctx.get("brand") or {}
    product = (ctx.get("product") or {}).get("one_liner", "")
    if task.id == "market_research":
        return (f"Nghiên cứu bằng Google Search cho câu hỏi: {inputs.get('objective')}\n"
                f"Ngành: {brand.get('industry', '')}. Sản phẩm: {product}. Khu vực: {inputs.get('location')}.\n"
                "Tìm: số liệu thị trường và khách hàng có nguồn (ghi năm), xu hướng gần đây, doanh nghiệp đang hoạt động trong khu vực, "
                "mức giá tham khảo, quy định pháp lý liên quan. Ghi rõ nguồn cho từng con số. Không có số liệu thì nói không tìm thấy.")
    if task.id == "competitor_discovery":
        return (f"Tìm tất cả các doanh nghiệp/quán đang kinh doanh {product or brand.get('industry', '')} tại {inputs.get('location')}. "
                f"Tiêu chí bổ sung: {inputs.get('criteria') or 'cùng phân khúc khách hàng'}. Liệt kê đầy đủ mọi đối thủ cạnh tranh có thật (có bao nhiêu liệt kê bấy nhiêu, không tự giới hạn 3 hay 4 bên): tên, website/fanpage, sản phẩm chính, mức giá nếu thấy. "
                "Chỉ nêu doanh nghiệp có thật xuất hiện trong kết quả tìm kiếm và hoạt động tại khu vực được yêu cầu, tuyệt đối không bịa đặt đối thủ.")
    if task.id == "competitor_dossier":
        extra_info = []
        if inputs.get('website'): extra_info.append(f"website: {inputs['website']}")
        if inputs.get('social'): extra_info.append(f"mạng xã hội: {inputs['social']}")
        if inputs.get('phone'): extra_info.append(f"SĐT: {inputs['phone']}")
        info_str = f" ({', '.join(extra_info)})" if extra_info else ""
        return (f"Tìm thông tin về {inputs.get('competitor_name')}{info_str}, ngành {brand.get('industry', '')}: "
                "định vị, sản phẩm, giá, kênh bán, đánh giá và phàn nàn của khách (ghi rõ nguồn từng ý).")
    return f"Tìm thông tin liên quan: {inputs}"


def run_task(email: str, is_admin: bool, task_id: str, raw_inputs: Dict[str, Any], *, save: bool = True) -> Dict[str, Any]:
    email = normalize_email(email)
    task = get_task(task_id)
    if not task:
        return {"status": "error", "message": "Tác vụ không tồn tại."}
    ctx = load_context(email)
    try:
        inputs = validate_inputs(task, raw_inputs or {}, ctx)
    except TaskInputError as exc:
        return {"status": "invalid_input", "errors": exc.errors}
    missing = missing_fields(ctx, task.required_context)
    if missing:
        return {"status": "needs_context", "missing": missing,
                "message": "Hồ sơ bối cảnh còn thiếu thông tin tác vụ này cần. Trả lời các câu hỏi dưới đây rồi chạy lại."}
    key, key_source = resolve_key(email, is_admin)
    if not key:
        return {"status": "not_generated", "provenance": {"status": "not_generated", "error_code": "no_key",
                                                          "error": "Chưa có Gemini API key. Thêm key trong mục Cài đặt AI để dùng tác vụ này."}}
    model_pref = ai_settings(email)["model"]
    ex: Dict[str, Any] = {}
    if task.extras:
        ex = extras_mod.LOADERS[task.extras](email, inputs, ctx)
    system = system_prompt(task.sections)
    base_prompt = (f"NHIỆM VỤ: {task.title}\n{task.instructions}\n\n{render_for_prompt(ctx)}\n\n"
                   f"DỮ LIỆU ĐẦU VÀO:\n{_format_inputs(task, inputs)}")
    if ex.get("prompt_text"):
        base_prompt += f"\n\nDỮ LIỆU THÊM (số liệu thật từ hệ thống):\n{ex['prompt_text']}"
    base_prompt += f"\n\nHôm nay là {date.today().isoformat()}."

    grounded_result: Optional[llm.LLMResult] = None
    if task.grounded:
        grounded_result = llm.generate_grounded(key, system=system, prompt=_research_prompt(task, inputs, ctx), preferred_model=model_pref)
        if not grounded_result.ok:
            if grounded_result.error_code in ("invalid_key", "forbidden"):
                prov = grounded_result.provenance(task=task_id, key_source=key_source, context_version=ctx.get("version"))
                return {"status": "not_generated", "provenance": prov}
            # Dự phòng tìm kiếm web khi Google Search grounding hết hạn mức/không hỗ trợ trên key này
            sources: List[Dict[str, str]] = []
            queries: List[str] = []
            grounded_text = ""
            query = _clean_search_query(task, inputs, ctx)
            try:
                from app.netsafe import web_search
                web_results, _ = web_search(query, max_results=8)
                if web_results:
                    sources = [{"title": r["title"], "url": r["url"]} for r in web_results]
                    queries = [query]
                    grounded_text = "\n".join(f"- {r['title']}: {r['snippet']}" for r in web_results)
            except Exception:
                pass
            site = ex.get("site")
            if site and site.get("url"):
                sources.append({"title": f"Website đối thủ (tải trực tiếp): {site.get('title') or site['url']}", "url": site["url"]})
            ex["sources"] = sources
            if grounded_text:
                base_prompt += (f"\n\nBÁO CÁO TÌM KIẾM WEB (thô):\n{grounded_text[:12000]}\n\n{_sources_block(sources)}\n"
                                "Gắn source_ids theo số thứ tự trong DANH SÁCH NGUỒN. Ý nào không có nguồn thì tag [Unverified] hoặc [Inference].")
            else:
                base_prompt += f"\n\n{_sources_block(sources)}\n"
        else:
            sources = list(grounded_result.sources)
            site = ex.get("site")
            if site and site.get("url"):
                sources.append({"title": f"Website đối thủ (tải trực tiếp): {site.get('title') or site['url']}", "url": site["url"]})
            ex["sources"] = sources
            base_prompt += (f"\n\nBÁO CÁO TÌM KIẾM GOOGLE (thô):\n{grounded_result.text[:12000]}\n\n{_sources_block(sources)}\n"
                            "Gắn source_ids theo số thứ tự trong DANH SÁCH NGUỒN. Ý nào không có nguồn thì tag [Unverified] hoặc [Inference].")

    if task.id == "competitor_discovery":
        base_prompt += ("\n\nLƯU Ý VỀ DANH SÁCH ĐỐI THỦ:\n"
                        "- Liệt kê toàn bộ các đối thủ cạnh tranh có thật (có bao nhiêu liệt kê bấy nhiêu, không tự giới hạn 3 hay 4 bên).\n"
                        "- Với mỗi đối thủ, bắt buộc gán source_ids là mảng số nguyên trỏ đến các số thứ tự trong DANH SÁCH NGUỒN (ví dụ [1] hoặc [1, 2]). Không để source_ids rỗng nếu thông tin lấy từ báo cáo tìm kiếm hoặc thị trường.")

    result = llm.generate_json(key, system=system, prompt=base_prompt, schema=task.schema,
                               preferred_model=model_pref, temperature=task.temperature)
    if grounded_result is not None and grounded_result.ok:
        result.grounded = grounded_result.grounded
        result.sources = ex.get("sources", [])
        result.search_queries = grounded_result.search_queries
    elif task.grounded and ex.get("sources"):
        result.grounded = True
        result.sources = ex.get("sources", [])
        result.search_queries = [task.title]
    # Nếu key cá nhân hết quota trong ngày (429), thử dùng key máy chủ (nếu có cấu hình)
    if not result.ok and result.error_code in ("quota", "unavailable") and key_source == "user":
        server_key = config.settings.server_gemini_key
        if server_key and server_key != key:
            log.info("User key exhausted quota, falling back to server Gemini key")
            server_res = llm.generate_json(server_key, system=system, prompt=base_prompt, schema=task.schema,
                                           preferred_model=model_pref, temperature=task.temperature)
            if server_res.ok:
                result = server_res
                key_source = "server_fallback"

    prov = result.provenance(task=task_id, key_source=key_source, context_version=ctx.get("version"), sections=task.sections)
    if not result.ok:
        return {"status": "not_generated", "provenance": prov}

    data = result.data if isinstance(result.data, dict) else {"result": result.data}
    notes: List[Dict[str, str]] = []
    if task.post:
        data, notes = task.post(data, inputs, ctx, ex)
    competitor_names = extras_mod.known_competitors(email, ctx)
    if task.id == "competitor_dossier" and inputs.get("competitor_name"):
        competitor_names.append(inputs["competitor_name"])
    guard = guardrails.check(data, kind=task.guard_kind(inputs), context=ctx, competitor_names=competitor_names,
                             scarcity_evidence=str(inputs.get("scarcity_evidence", "")))
    markdown = to_markdown(task.title, data, prov)
    run_id = None
    if save:
        title = _run_title(task, inputs)
        run_id = execute("INSERT INTO skill_runs (user_email, task, title, input_json, output_json, provenance_json, guardrail_json, status) "
                         "VALUES (?, ?, ?, ?, ?, ?, ?, 'ok')",
                         (email, task_id, title, dumps(inputs), dumps(data), dumps(prov), dumps({**guard, "notes": notes})))
    return {"status": "ok", "run_id": run_id, "task": task_id, "output": data, "provenance": prov,
            "guardrails": guard, "notes": notes, "markdown": markdown, "inputs": inputs, "extras": _public_extras(ex)}


def _public_extras(ex: Dict[str, Any]) -> Dict[str, Any]:
    keep = {}
    for k in ("funnel", "holidays_in_range", "site", "site_error", "known_competitors"):
        if k in ex:
            keep[k] = ex[k]
    return keep


def _run_title(task: Task, inputs: Dict[str, Any]) -> str:
    for key in ("topic", "competitor_name", "product_name", "objective", "question", "kol_name", "event", "month", "flow", "offer_current"):
        if inputs.get(key):
            return f"{task.title}: {str(inputs[key])[:80]}"
    return f"{task.title} — {time.strftime('%d/%m/%Y %H:%M')}"


def list_runs(email: str, task_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    sql = "SELECT id, task, title, status, created_at FROM skill_runs WHERE user_email = ?"
    params: List[Any] = [normalize_email(email)]
    if task_id:
        sql += " AND task = ?"
        params.append(task_id)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(int(limit))
    return rows(sql, params)


def get_run(email: str, run_id: int) -> Optional[Dict[str, Any]]:
    r = one("SELECT * FROM skill_runs WHERE id = ? AND user_email = ?", (run_id, normalize_email(email)))
    if not r:
        return None
    task = get_task(r["task"])
    out = {"id": r["id"], "task": r["task"], "title": r["title"], "status": r["status"], "created_at": r["created_at"],
           "inputs": loads(r["input_json"], {}), "output": loads(r["output_json"], {}),
           "provenance": loads(r["provenance_json"], {}), "guardrails": loads(r["guardrail_json"], {})}
    out["markdown"] = to_markdown(task.title if task else r["task"], out["output"], out["provenance"])
    return out


def delete_run(email: str, run_id: int) -> bool:
    return execute("DELETE FROM skill_runs WHERE id = ? AND user_email = ?", (run_id, normalize_email(email))) > 0
