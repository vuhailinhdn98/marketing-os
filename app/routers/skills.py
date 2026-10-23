# -*- coding: utf-8 -*-
"""Skill Studio: danh mục tác vụ, chạy tác vụ, lịch sử và các thao tác lưu kết quả vào đúng nơi."""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import Response

from app import context as ctx_mod
from app.deps import CurrentUser, require_user
from app.skills.registry import GROUPS, catalog
from app.services import analytics, competitors, content, runner

router = APIRouter(prefix="/api/skills", tags=["skills"])


@router.get("")
def list_tasks(user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    return {"groups": GROUPS, "tasks": catalog()}


@router.post("/{task_id}/run")
def run(task_id: str, user: CurrentUser = Depends(require_user), body: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    result = runner.run_task(user.email, user.is_admin, task_id, body.get("inputs") or {})
    if result.get("status") == "error":
        raise HTTPException(404, result.get("message", "Không tìm thấy tác vụ."))
    return result


@router.get("/runs")
def runs(user: CurrentUser = Depends(require_user), task: Optional[str] = Query(None)) -> Dict[str, Any]:
    return {"runs": runner.list_runs(user.email, task)}


def _run_or_404(email: str, run_id: int) -> Dict[str, Any]:
    r = runner.get_run(email, run_id)
    if not r:
        raise HTTPException(404, "Không tìm thấy kết quả.")
    return r


@router.get("/runs/{run_id}")
def get_run(run_id: int, user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    return _run_or_404(user.email, run_id)


@router.delete("/runs/{run_id}")
def delete_run(run_id: int, user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    if not runner.delete_run(user.email, run_id):
        raise HTTPException(404, "Không tìm thấy kết quả.")
    return {"ok": True}


@router.get("/runs/{run_id}/markdown")
def download_markdown(run_id: int, user: CurrentUser = Depends(require_user)) -> Response:
    r = _run_or_404(user.email, run_id)
    return Response(r["markdown"], media_type="text/markdown; charset=utf-8",
                    headers={"Content-Disposition": f"attachment; filename=marketing-os-{r['task']}-{run_id}.md"})


# --------------------------- Lưu kết quả vào nơi dùng ----------------------

@router.post("/runs/{run_id}/to-content")
def to_content(run_id: int, user: CurrentUser = Depends(require_user), body: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    r = _run_or_404(user.email, run_id)
    out, inputs = r["output"], r["inputs"]
    if r["task"] == "copy_studio":
        variants = out.get("variants") or []
        idx = int(body.get("variant", out.get("recommended", 0)) or 0)
        if not (0 <= idx < len(variants)):
            raise HTTPException(400, "Phương án không tồn tại.")
        v = variants[idx]
        data = {"channel": inputs.get("channel"), "topic": v.get("headline") or inputs.get("topic"), "hook": v.get("hook"),
                "body": v.get("body"), "cta": v.get("cta"), "image_prompt": out.get("visual_brief"), "variants": variants,
                "scarcity_evidence": inputs.get("scarcity_evidence", "")}
    elif r["task"] == "content_package":
        script = "\n".join(f"[{s.get('time', '')}] Hình: {s.get('visual', '')} | Lời: {s.get('audio', '')} | Chữ: {s.get('on_screen_text', '')}"
                           for s in out.get("video_script") or [])
        data = {"channel": inputs.get("channel"), "topic": out.get("headline") or inputs.get("topic"), "hook": out.get("headline"),
                "body": (out.get("body") or "") + ("\n\n" + " ".join(out.get("hashtags") or []) if out.get("hashtags") else ""),
                "cta": out.get("cta"), "video_script": script, "image_prompt": out.get("image_prompt"),
                "scarcity_evidence": inputs.get("scarcity_evidence", "")}
    elif r["task"] == "copy_edit":
        data = {"channel": inputs.get("channel") or "Facebook", "topic": (out.get("final_text") or "")[:80], "body": out.get("final_text")}
    else:
        raise HTTPException(400, "Kết quả này không phải nội dung để đưa vào kho.")
    item = content.create_item(user.email, data, r["provenance"])
    return {"item": item}


@router.post("/runs/{run_id}/to-calendar")
def to_calendar(run_id: int, user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    r = _run_or_404(user.email, run_id)
    if r["task"] != "content_calendar":
        raise HTTPException(400, "Kết quả này không phải lịch nội dung.")
    n = content.save_calendar(user.email, r["output"].get("rows") or [], r["provenance"])
    return {"saved": n}


@router.post("/runs/{run_id}/to-budget")
def to_budget(run_id: int, user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    r = _run_or_404(user.email, run_id)
    if r["task"] != "budget_plan":
        raise HTTPException(400, "Kết quả này không phải ngân sách.")
    month = r["inputs"].get("month")
    saved = 0
    for line in r["output"].get("lines") or []:
        analytics.add_budget_line(user.email, {"month": month, "program": line.get("program"), "item": line.get("item"),
                                               "unit_price": line.get("unit_price"), "unit": line.get("unit"),
                                               "quantity": line.get("quantity"), "notes": line.get("kpi_formula", "")})
        saved += 1
    return {"saved": saved, "month": month}


@router.post("/runs/{run_id}/to-experiment")
def to_experiment(run_id: int, user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    r = _run_or_404(user.email, run_id)
    if r["task"] != "weekly_loop":
        raise HTTPException(400, "Kết quả này không có thử nghiệm.")
    e = r["output"].get("experiment") or {}
    exp_id = analytics.save_experiment(user.email, {
        "title": e.get("title") or "Thử nghiệm tuần", "funnel_stage": r["output"].get("bottleneck_stage", ""),
        "hypothesis": e.get("hypothesis", ""), "change_desc": e.get("change", ""), "primary_metric": e.get("primary_metric", ""),
        "guardrail_metric": e.get("guardrail_metric", ""), "stop_condition": e.get("stop_condition", ""), "status": "planned"})
    return {"experiment_id": exp_id}


@router.post("/runs/{run_id}/to-competitors")
def to_competitors(run_id: int, user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    r = _run_or_404(user.email, run_id)
    if r["task"] == "competitor_discovery":
        n = competitors.save_from_discovery(user.email, r["output"].get("competitors") or [], r["provenance"].get("sources") or [],
                                            r["inputs"].get("location", ""))
        return {"saved": n}
    if r["task"] == "competitor_dossier":
        comp = competitors.save_dossier(user.email, r["inputs"].get("competitor_name", ""), r["markdown"], r["provenance"],
                                        website=r["inputs"].get("website", ""), phone=r["inputs"].get("phone", ""),
                                        social=r["inputs"].get("social", ""))
        return {"competitor": comp}
    raise HTTPException(400, "Kết quả này không phải dữ liệu đối thủ.")


@router.post("/runs/{run_id}/to-context")
def to_context(run_id: int, user: CurrentUser = Depends(require_user), body: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    """Đưa câu nguyên văn (VoC) đã chọn vào hồ sơ bối cảnh mục 9."""
    r = _run_or_404(user.email, run_id)
    if r["task"] != "voc_extract":
        raise HTTPException(400, "Chỉ kết quả VoC mới đưa được vào hồ sơ.")
    quotes = r["output"].get("verbatim_quotes") or []
    chosen = body.get("indexes")
    if isinstance(chosen, list):
        quotes = [q for i, q in enumerate(quotes) if i in chosen]
    if not quotes:
        raise HTTPException(400, "Không có câu nguyên văn nào để thêm.")
    data = ctx_mod.load_context(user.email)
    existing = list((data.get("customer_language") or {}).get("verbatim") or [])
    known = {str(x.get("quote", "")).strip().lower() for x in existing}
    added = 0
    for q in quotes:
        if q["quote"].strip().lower() not in known:
            existing.append({"quote": q["quote"], "source": "VoC", "date": r["created_at"][:10]})
            added += 1
    ctx_mod.save_context(user.email, {"customer_language.verbatim": existing}, "Thêm câu nguyên văn từ phân tích VoC")
    return {"added": added}
