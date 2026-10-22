# -*- coding: utf-8 -*-
"""
Marketing OS 4 — máy chủ FastAPI.

Kiến trúc: Skill Engine (hồ sơ bối cảnh → gói skill → AI trả JSON → hậu xử lý → cổng tuân thủ)
cùng CRM 6 tầng, Growth Console, lịch nội dung theo lịch âm – dương Việt Nam.
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.database import ensure_db
from app.routers import admin, auth, content, core, growth, leads, skills
from app.security import AuthError, purge_expired_sessions
from app.services.analytics import DataError
from app.services.competitors import CompetitorError
from app.services.content import ContentError
from app.services.leads import LeadError
from app.services.media import MediaError

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s: %(message)s")

APP_VERSION = "4.0.1"
STATIC_DIR = Path(__file__).resolve().parent / "static"

@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_db()
    purge_expired_sessions()
    from app import config
    if config.settings.ephemeral_storage_risk:
        logging.getLogger("marketing_os").warning(
            "Đang chạy trên Render mà chưa đặt DATA_DIR vào ổ đĩa bền: dữ liệu sẽ mất khi dịch vụ khởi động lại.")
    yield


app = FastAPI(title="Marketing OS", version=APP_VERSION, docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)

CSP = ("default-src 'self'; "
       "script-src 'self' https://cdn.tailwindcss.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://accounts.google.com; "
       "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://accounts.google.com https://fonts.googleapis.com; "
       "font-src 'self' data: https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
       "img-src 'self' data: blob: https:; media-src 'self' blob:; "
       "connect-src 'self' https://accounts.google.com https://cdn.jsdelivr.net; "
       "frame-src https://accounts.google.com; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    path = request.url.path
    if not path.startswith("/api/leads/ingest/"):
        response.headers.setdefault("X-Frame-Options", "DENY")
    if path == "/" or path.startswith("/static/"):
        response.headers.setdefault("Content-Security-Policy", CSP)
    if path.startswith("/api/"):
        response.headers.setdefault("Cache-Control", "no-store")
    elif path == "/" or path.startswith("/static/"):
        # Luôn hỏi lại máy chủ (rẻ nhờ ETag) để bản cập nhật giao diện có hiệu lực ngay sau khi triển khai
        response.headers.setdefault("Cache-Control", "no-cache")
    return response


def _error(status: int, message: str) -> JSONResponse:
    return JSONResponse({"detail": message}, status_code=status)


@app.exception_handler(AuthError)
async def auth_error(_: Request, exc: AuthError) -> JSONResponse:
    return _error(exc.status, exc.message)


for _cls in (LeadError, ContentError, DataError, CompetitorError, MediaError):
    @app.exception_handler(_cls)
    async def _domain_error(_: Request, exc: Exception) -> JSONResponse:  # noqa: B023 - mỗi lớp dùng cùng một cách trả lỗi
        return _error(400, str(exc))


@app.exception_handler(HTTPException)
async def http_error(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code, headers=getattr(exc, "headers", None))


@app.exception_handler(Exception)
async def unexpected(_: Request, exc: Exception) -> JSONResponse:
    logging.getLogger("marketing_os").exception("Unhandled error: %s", exc)
    return _error(500, "Có lỗi không mong muốn ở máy chủ. Vui lòng thử lại; nếu lặp lại, xem nhật ký máy chủ.")


for r in (auth.router, core.router, skills.router, content.router, leads.router, growth.router, admin.router):
    app.include_router(r)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "index.html"), media_type="text/html")


@app.api_route("/healthz", methods=["GET", "HEAD"], include_in_schema=False)
def healthz() -> dict:
    return {"ok": True, "version": APP_VERSION}
