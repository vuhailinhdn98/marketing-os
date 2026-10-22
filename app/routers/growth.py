# -*- coding: utf-8 -*-
"""Growth Console: số liệu, nhập CSV, ngân sách, UTM, thử nghiệm, máy tính, Local SEO, đối thủ, media."""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from app import context as ctx_mod, metrics
from app.deps import CurrentUser, require_user
from app.services import analytics, competitors, local_seo, media, runner

router = APIRouter(prefix="/api", tags=["growth"])


# --------------------------- Số liệu nhập tay -------------------------------

@router.post("/metrics")
def add_metric(user: CurrentUser = Depends(require_user), body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    return {"id": analytics.record_metric(user.email, body)}


@router.get("/metrics")
def list_metrics(user: CurrentUser = Depends(require_user), days: int = Query(30)) -> Dict[str, Any]:
    start, end = analytics._period(max(1, min(days, 730)))
    return {"items": analytics.list_metrics(user.email, start, end)}


@router.delete("/metrics/{metric_id}")
def delete_metric(metric_id: int, user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    if not analytics.delete_metric(user.email, metric_id):
        raise HTTPException(404, "Không tìm thấy dòng số liệu.")
    return {"ok": True}


@router.get("/growth/summary")
def growth_summary(user: CurrentUser = Depends(require_user), days: int = Query(30), end: Optional[str] = Query(None)) -> Dict[str, Any]:
    try:
        return analytics.summary(user.email, max(1, min(days, 730)), end)
    except ValueError:
        raise HTTPException(400, "Ngày kết thúc phải theo dạng YYYY-MM-DD.")


@router.get("/growth/imported")
def growth_imported(user: CurrentUser = Depends(require_user), days: int = Query(90)) -> Dict[str, Any]:
    return analytics.imported_report(user.email, max(7, min(days, 730)))


@router.get("/imports")
def list_imports(user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    return {"imports": analytics.imports(user.email), "kinds": analytics.import_kinds()}


@router.post("/imports")
def import_csv(user: CurrentUser = Depends(require_user), body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    filename = str(body.get("filename") or "data.csv")
    kind = str(body.get("kind") or "") or analytics.detect_kind(filename) or ""
    if not kind:
        raise HTTPException(400, "Chọn loại dữ liệu hoặc đặt tên file bắt đầu bằng ads_, sales_, web_… để tự nhận diện.")
    text = body.get("content")
    if not isinstance(text, str) or not text.strip():
        raise HTTPException(400, "File rỗng.")
    return analytics.import_csv(user.email, kind, filename, text.encode("utf-8"), bool(body.get("replace_period", True)))


# --------------------------- Máy tính --------------------------------------

def _num(body: Dict[str, Any], key: str, required: bool = True) -> Optional[float]:
    val = body.get(key)
    if val in (None, ""):
        if required:
            raise HTTPException(400, f"Thiếu {key}.")
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        raise HTTPException(400, f"{key} phải là số.")


@router.post("/calc/budget-reverse")
def calc_budget(user: CurrentUser = Depends(require_user), body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    return metrics.budget_reverse(target_revenue=_num(body, "target_revenue"), aov=_num(body, "aov"),
                                  purchases_per_customer=_num(body, "purchases_per_customer", False) or 1.0,
                                  cac=_num(body, "cac", False), test_reserve_pct=_num(body, "test_reserve_pct", False) or 15.0)


@router.post("/calc/ab-test")
def calc_ab(user: CurrentUser = Depends(require_user), body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    try:
        return metrics.ab_test(visitors_a=int(_num(body, "visitors_a")), conv_a=int(_num(body, "conv_a")),
                               visitors_b=int(_num(body, "visitors_b")), conv_b=int(_num(body, "conv_b")))
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@router.post("/calc/sample-size")
def calc_sample(user: CurrentUser = Depends(require_user), body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    n = metrics.sample_size_per_variant(baseline_pct=_num(body, "baseline_pct"), min_detectable_lift_pct=_num(body, "lift_pct"))
    if n is None:
        raise HTTPException(400, "Tỉ lệ nền và mức tăng phải cho ra tỉ lệ trong khoảng 0–100%.")
    return {"per_variant": n, "total": n * 2}


@router.post("/calc/paid-funnel")
def calc_funnel(user: CurrentUser = Depends(require_user), body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    return metrics.paid_funnel(budget=_num(body, "budget"), cpm=_num(body, "cpm", False), cpc=_num(body, "cpc", False),
                               ctr_pct=_num(body, "ctr_pct", False), cvr_pct=_num(body, "cvr_pct", False),
                               cost_per_result=_num(body, "cost_per_result", False))


@router.post("/calc/ltv")
def calc_ltv(user: CurrentUser = Depends(require_user), body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    ctx = ctx_mod.load_context(user.email)
    gm = _num(body, "gross_margin_pct", False) or ctx_mod.get_path(ctx, "unit_economics.gross_margin_pct")
    aov = _num(body, "aov", False) or ctx_mod.get_path(ctx, "unit_economics.avg_order_value_vnd")
    if not gm or not aov:
        raise HTTPException(400, "Cần giá trị đơn trung bình và biên lợi nhuận gộp (nhập ở đây hoặc trong hồ sơ).")
    purchases = _num(body, "purchases_per_customer")
    cac = _num(body, "cac", False)
    value = metrics.ltv(aov=aov, gross_margin_pct=gm, purchases_per_customer=purchases)
    out: Dict[str, Any] = {"ltv_gross_profit": value, "aov": aov, "gross_margin_pct": gm}
    if cac:
        out["ltv_cac"] = round(value / cac, 2) if value else None
        ppm = _num(body, "purchases_per_month", False)
        if ppm:
            out["payback_months"] = metrics.payback_months(cac=cac, aov=aov, gross_margin_pct=gm, purchases_per_month=ppm)
    return out


# --------------------------- Ngân sách -------------------------------------

@router.get("/budget")
def budget(user: CurrentUser = Depends(require_user), month: Optional[str] = Query(None)) -> Dict[str, Any]:
    return analytics.budget_month(user.email, month or date.today().strftime("%Y-%m"))


@router.post("/budget/lines")
def add_line(user: CurrentUser = Depends(require_user), body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    return {"id": analytics.add_budget_line(user.email, body)}


@router.patch("/budget/lines/{line_id}")
def update_line(line_id: int, user: CurrentUser = Depends(require_user), body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    if not analytics.update_budget_actual(user.email, line_id, body.get("actual_total")):
        raise HTTPException(404, "Không tìm thấy hạng mục.")
    return {"ok": True}


@router.delete("/budget/lines/{line_id}")
def delete_line(line_id: int, user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    if not analytics.delete_budget_line(user.email, line_id):
        raise HTTPException(404, "Không tìm thấy hạng mục.")
    return {"ok": True}


# --------------------------- UTM & thử nghiệm ------------------------------

@router.get("/utm")
def utm_list(user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    return {"links": analytics.list_utm(user.email)}


@router.post("/utm")
def utm_create(user: CurrentUser = Depends(require_user), body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    return analytics.create_utm(user.email, body)


@router.delete("/utm/{link_id}")
def utm_delete(link_id: int, user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    if not analytics.delete_utm(user.email, link_id):
        raise HTTPException(404, "Không tìm thấy link.")
    return {"ok": True}


@router.get("/experiments")
def exp_list(user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    return {"experiments": analytics.list_experiments(user.email), "statuses": analytics.EXP_STATUSES}


@router.post("/experiments")
def exp_create(user: CurrentUser = Depends(require_user), body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    return {"id": analytics.save_experiment(user.email, body)}


@router.patch("/experiments/{exp_id}")
def exp_update(exp_id: int, user: CurrentUser = Depends(require_user), body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    return {"id": analytics.save_experiment(user.email, body, exp_id)}


@router.delete("/experiments/{exp_id}")
def exp_delete(exp_id: int, user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    if not analytics.delete_experiment(user.email, exp_id):
        raise HTTPException(404, "Không tìm thấy thử nghiệm.")
    return {"ok": True}


# --------------------------- Local SEO -------------------------------------

@router.get("/local-seo")
def local_seo_toolkit(user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    return local_seo.toolkit(ctx_mod.load_context(user.email))


# --------------------------- Đối thủ ---------------------------------------

@router.get("/competitors")
def comp_list(user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    return {"competitors": competitors.list_competitors(user.email)}


@router.post("/competitors")
def comp_add(user: CurrentUser = Depends(require_user), body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    return {"competitor": competitors.add_manual(user.email, body)}


@router.delete("/competitors/{comp_id}")
def comp_delete(comp_id: int, user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    if not competitors.delete_competitor(user.email, comp_id):
        raise HTTPException(404, "Không tìm thấy đối thủ.")
    return {"ok": True}


@router.delete("/competitors")
def comp_clear(user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    return {"deleted": competitors.clear_all(user.email)}


# --------------------------- Media -----------------------------------------

def _key(user: CurrentUser) -> str:
    key, _ = runner.resolve_key(user.email, user.is_admin)
    if not key:
        raise HTTPException(400, "Chưa có Gemini API key. Thêm key trong Cài đặt AI.")
    return key


@router.get("/media")
def media_list(user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    return {"jobs": media.list_jobs(user.email), "image_ratios": media.IMAGE_RATIOS, "video_ratios": media.VIDEO_RATIOS}


@router.post("/media/image")
def media_image(user: CurrentUser = Depends(require_user), body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    return {"job": media.create_image(user.email, _key(user), str(body.get("prompt") or ""), str(body.get("aspect_ratio") or "1:1"))}


@router.post("/media/video")
def media_video(user: CurrentUser = Depends(require_user), body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    return {"job": media.start_video(user.email, _key(user), str(body.get("prompt") or ""), str(body.get("aspect_ratio") or "16:9"))}


@router.post("/media/{job_id}/refresh")
def media_refresh(job_id: int, user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    return {"job": media.refresh_video(user.email, _key(user), job_id)}


@router.get("/media/{job_id}/file")
def media_file(job_id: int, user: CurrentUser = Depends(require_user)) -> FileResponse:
    path = media.file_path(user.email, job_id)
    if not path:
        raise HTTPException(404, "Chưa có file.")
    job = media.get_job(user.email, job_id) or {}
    return FileResponse(str(path), media_type=job.get("mime_type") or "application/octet-stream", filename=path.name)


@router.delete("/media/{job_id}")
def media_delete(job_id: int, user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    if not media.delete_job(user.email, job_id):
        raise HTTPException(404, "Không tìm thấy.")
    return {"ok": True}
