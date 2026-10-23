# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, Response

from app.database import log_automation
from app.deps import CurrentUser, require_user
from app.security import user_by_ingest_secret
from app.services import leads

router = APIRouter(prefix="/api/leads", tags=["leads"])

import threading
import time

_ingest_hits: Dict[str, list] = {}
_ingest_lock = threading.Lock()
INGEST_LIMIT, INGEST_WINDOW = 30, 600   # mỗi IP
INGEST_LIMIT_TOTAL = 300                 # mỗi đường dẫn nhận lead, mọi IP cộng lại


def _ingest_allowed(secret: str, ip: str) -> bool:
    now = time.time()
    keys = ((f"{secret[:12]}|{ip}", INGEST_LIMIT), (f"{secret[:12]}|*", INGEST_LIMIT_TOTAL))
    with _ingest_lock:
        recent = {}
        for key, limit in keys:
            hits = [t for t in _ingest_hits.get(key, []) if now - t < INGEST_WINDOW]
            _ingest_hits[key] = hits
            if len(hits) >= limit:
                return False
            recent[key] = hits
        for key, hits in recent.items():
            hits.append(now)
        # Dọn khóa cũ để bộ nhớ không phình khi bị gửi từ rất nhiều IP
        if len(_ingest_hits) > 5000:
            for key in [k for k, v in _ingest_hits.items() if not v or now - v[-1] >= INGEST_WINDOW]:
                _ingest_hits.pop(key, None)
        return True


_CORS = {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "POST, OPTIONS",
         "Access-Control-Allow-Headers": "Content-Type", "Access-Control-Max-Age": "600"}


@router.get("")
def list_leads(user: CurrentUser = Depends(require_user), status: Optional[str] = Query(None), search: str = Query("")) -> Dict[str, Any]:
    if status and status not in leads.ALL_STATUSES:
        raise HTTPException(400, "Trạng thái không hợp lệ.")
    data = leads.list_leads(user.email, status, search.strip()[:100])
    return {"leads": data, "count": len(data)}


@router.post("")
def create_lead(user: CurrentUser = Depends(require_user), body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    lead = leads.create_lead(user.email, body, consent_source=str(body.get("consent_source") or "Nhập tay"))
    return {"lead": lead}


@router.get("/stats")
def stats(user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    return leads.stats(user.email)


@router.get("/export.csv")
def export_csv(user: CurrentUser = Depends(require_user), consented_only: bool = Query(False)) -> Response:
    data = leads.export_csv(user.email, consented_only)
    name = "khach-dong-y-tiep-thi.csv" if consented_only else "khach-hang.csv"
    return Response(data.encode("utf-8"), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": f"attachment; filename={name}"})


@router.patch("/{lead_id}")
def update_lead(lead_id: int, user: CurrentUser = Depends(require_user), body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    return {"lead": leads.update_lead(user.email, lead_id, body)}


@router.patch("/{lead_id}/status")
def update_status(lead_id: int, user: CurrentUser = Depends(require_user), body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    patch = {"status": str(body.get("status", "")), "lost_reason": str(body.get("lost_reason", ""))}
    if "deal_value" in body and body["deal_value"] is not None:
        patch["deal_value"] = body["deal_value"]
    return {"lead": leads.update_lead(user.email, lead_id, patch)}


@router.delete("/{lead_id}")
def delete_lead(lead_id: int, user: CurrentUser = Depends(require_user)) -> Dict[str, Any]:
    if not leads.delete_lead(user.email, lead_id):
        raise HTTPException(404, "Không tìm thấy khách.")
    return {"ok": True}


@router.options("/ingest/{secret}")
def ingest_preflight(secret: str) -> Response:
    return Response(status_code=204, headers=_CORS)


@router.post("/ingest/{secret}")
async def ingest(secret: str, request: Request) -> Response:
    """Nhận lead từ landing page/form bên ngoài. Workspace xác định bằng mã bí mật trong URL, không bằng dữ liệu gửi lên."""
    if not _ingest_allowed(secret, request.client.host if request.client else ""):
        return JSONResponse({"detail": "Gửi quá nhiều, thử lại sau."}, status_code=429, headers=_CORS)
    owner = user_by_ingest_secret(secret)
    if not owner:
        return JSONResponse({"detail": "Đường dẫn nhận lead không hợp lệ."}, status_code=404, headers=_CORS)
    try:
        if "application/json" in request.headers.get("content-type", ""):
            body = await request.json()
        else:
            form = await request.body()
            from urllib.parse import parse_qs
            body = {k: v[0] for k, v in parse_qs(form.decode("utf-8", errors="replace")).items()}
    except Exception:
        return JSONResponse({"detail": "Dữ liệu gửi lên không đọc được."}, status_code=400, headers=_CORS)
    if not isinstance(body, dict):
        return JSONResponse({"detail": "Dữ liệu phải là đối tượng JSON."}, status_code=400, headers=_CORS)
    consent_raw = body.get("consent_marketing")
    consent = consent_raw is True or str(consent_raw).lower() in ("true", "1", "yes", "on")
    data = {k: body.get(k) for k in leads.FIELDS if k in body}
    data.update({"status": "new", "consent_marketing": consent,
                 "consent_text": str(body.get("consent_text") or "") if consent else ""})
    if not data.get("source"):
        data["source"] = "Form / Landing page"
    try:
        lead = leads.create_lead(owner["email"], data, consent_source="Form " + str(request.headers.get("origin") or "")[:80])
    except leads.LeadError as exc:
        return JSONResponse({"detail": str(exc)}, status_code=400, headers=_CORS)
    log_automation(owner["email"], "LEAD_INGEST", "Nhận lead từ form", "SUCCESS", f"Lead #{lead['id']} ({'có' if consent else 'không'} đồng ý tiếp thị)")
    return JSONResponse({"ok": True, "lead_id": lead["id"]}, headers=_CORS)
