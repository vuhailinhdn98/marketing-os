# -*- coding: utf-8 -*-
"""
Main FastAPI Web Server for Marketing Automation System (Auto-Pilot OS)
- Multi-Tenant User Isolation: Mỗi Gmail là 1 tài khoản, 1 workspace riêng biệt
- Real-time Google Sheets Integration & Webhook Sync
- Auto-Pilot Full Pipeline (Auto-Research, Auto-Scrape, Auto-Personas, Auto-Calendar, Auto-Draft)
- Mobile-First Responsive API & Real-time Logs Feed
"""
import os
import sys
import time
import threading
from pathlib import Path
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

# Internal modules
from app.database import (
    init_app_db, get_connection, get_profile, update_profile,
    save_research_record, get_latest_research,
    log_automation, get_automation_logs,
    save_calendar_items, get_calendar_items,
    save_discovered_competitors, get_discovered_competitors,
    add_or_update_competitor, delete_competitor,
    save_competitor_battlecard, get_competitor_by_id,
    save_content_package, get_content_items,
    create_or_update_user, create_session, verify_session, delete_session,
    get_all_users, export_users_csv, get_app_config, set_app_config,
    get_analytics_summary, record_performance_metric,
    reset_database_clean, normalize_email
)
from app.google_sheets import (
    dispatch_login_to_google_sheet, get_google_apps_script_template
)
from app.ai_engine import (
    generate_market_research, generate_custom_market_research,
    generate_competitor_analysis, generate_single_competitor_battlecard,
    generate_personas, generate_content_item,
    generate_30day_calendar, generate_custom_30day_calendar,
    generate_full_content_package,
    auto_discover_competitors,
    analyze_deep_competitor_dossier,
    build_catalyst_sections,
    run_catalyst_orchestrator
)

app = FastAPI(title="Marketing Automation OS", version="3.1.0")

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Mount static folder
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Helper: Extract current user email from request
def get_current_user_email(request: Request) -> str:
    # 1. Bearer Token in Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        user = verify_session(token)
        if user and user.get("email"):
            return normalize_email(user["email"])
    
    # 2. X-User-Email custom header
    email_hdr = request.headers.get("X-User-Email")
    if email_hdr and "@" in email_hdr:
        return normalize_email(email_hdr)
        
    # 3. Query parameter token
    token_param = request.query_params.get("token")
    if token_param:
        user = verify_session(token_param)
        if user and user.get("email"):
            return normalize_email(user["email"])
            
    # 4. Fallback default
    return "guest@marketing-os.local"

# Pydantic models
class GoogleAuthRequest(BaseModel):
    email: str
    name: Optional[str] = ""
    picture: Optional[str] = ""
    credential: Optional[str] = ""

class LogoutRequest(BaseModel):
    token: str

class SheetConfigUpdate(BaseModel):
    webhook_url: str

class ProfileUpdate(BaseModel):
    brand_name: Optional[str] = ""
    industry: Optional[str] = ""
    business_model: Optional[str] = ""
    products_services: Optional[str] = ""
    price_range: Optional[str] = ""
    target_audience: Optional[str] = ""
    competitors: Optional[str] = ""
    channels: Optional[str] = ""
    monthly_budget: Optional[float] = 0.0
    brand_voice: Optional[str] = ""
    gemini_api_key: Optional[str] = ""
    gemini_model: Optional[str] = "gemini-2.5-flash"
    region: Optional[str] = "Toàn quốc"
    market_scope_type: Optional[str] = "province"
    market_location: Optional[str] = "Toàn quốc"
    content_direction: Optional[str] = "educational"
    phone_hotline: Optional[str] = ""
    website_url: Optional[str] = ""
    website: Optional[str] = ""
    social_channels: Optional[str] = ""
    usp_advantages: Optional[str] = ""
    product_advantages: Optional[str] = ""

class CustomMarketRequest(BaseModel):
    scope_type: Optional[str] = "province"
    location: Optional[str] = "Toàn quốc"
    region: Optional[str] = "Toàn quốc"
    price_tier: Optional[str] = ""
    objective: Optional[str] = "Đánh chiếm thị phần từ đối thủ & Tăng trưởng doanh thu"

class CompetitorDiscoverRequest(BaseModel):
    criteria: Optional[str] = "all"
    market_context: Optional[dict] = None

class ManualCompetitorRequest(BaseModel):
    id: Optional[int] = None
    name: str
    website: Optional[str] = ""
    phone: Optional[str] = ""
    social: Optional[str] = ""
    notes: Optional[str] = ""
    competitor_type: Optional[str] = "Trực tiếp"
    price_segment: Optional[str] = ""
    core_products: Optional[str] = ""
    key_strengths: Optional[str] = ""
    vulnerabilities: Optional[str] = ""
    is_manual: Optional[int] = 1
    scan_deep: Optional[bool] = True

class CompetitorDossierScanRequest(BaseModel):
    competitor_id: int

class SingleBattlecardRequest(BaseModel):
    name: str
    website: Optional[str] = ""

class CustomCalendarRequest(BaseModel):
    direction: Optional[str] = "educational"

class ContentPackageRequest(BaseModel):
    topic: str
    channel: Optional[str] = "Facebook"
    direction: Optional[str] = "educational"

class CatalystRunRequest(BaseModel):
    loop_type: Optional[str] = "weekly_intel"
    custom_brief: Optional[str] = ""

class ContentRequest(BaseModel):
    channel: str
    topic: str
    format_type: Optional[str] = "standard"

class MetricEntry(BaseModel):
    date: str
    ad_spend: float
    revenue: float
    orders_count: Optional[int] = 0
    leads_count: Optional[int] = 0
    impressions: Optional[int] = 0
    clicks: Optional[int] = 0
    notes: Optional[str] = ""

# --- AUTO-PILOT PIPELINE ENGINE ---
def run_full_autopilot_pipeline(profile: dict = None, user_email: str = "default@marketing-os.local"):
    """Thực thi toàn bộ quy trình tự động hóa khép kín cho riêng tài khoản user_email"""
    email_norm = normalize_email(user_email)
    if not profile:
        profile = get_profile(email_norm)

    brand = profile.get("brand_name", "").strip() or "Doanh nghiệp"
    log_automation("AUTOPILOT_START", "Khởi động Auto-Pilot", "RUNNING", f"Bắt đầu vận hành chuỗi tự động cho {brand}", user_email=email_norm)

    try:
        # Giai đoạn 1: Nghiên cứu thị trường
        log_automation("A01_MARKET", "Nghiên cứu thị trường", "RUNNING", "Đang tính toán TAM/SAM/SOM và PESTEL", user_email=email_norm)
        mr_content = generate_market_research(profile)
        save_research_record("market_research", f"Nghiên cứu thị trường: {brand}", mr_content, user_email=email_norm)
        log_automation("A01_MARKET", "Nghiên cứu thị trường", "SUCCESS", f"Đã hoàn thành báo cáo thị trường ({len(mr_content)} ký tự)", user_email=email_norm)

        # Giai đoạn 2: Tình báo đối thủ
        log_automation("A02_COMPETITORS", "Tình báo đối thủ", "RUNNING", "Đang cào website đối thủ và bóc tách điểm yếu", user_email=email_norm)
        comp_content = generate_competitor_analysis(profile)
        save_research_record("battlecards", f"Tình báo đối thủ: {brand}", comp_content, user_email=email_norm)
        log_automation("A02_COMPETITORS", "Tình báo đối thủ", "SUCCESS", f"Đã lập Battlecards & Kịch bản phản đòn ({len(comp_content)} ký tự)", user_email=email_norm)

        # Giai đoạn 3: Chân dung khách hàng
        log_automation("A05_PERSONAS", "Chân dung khách hàng", "RUNNING", "Đang dựng 3 chân dung khách hàng cốt lõi", user_email=email_norm)
        personas_content = generate_personas(profile)
        save_research_record("personas", f"Chân dung khách hàng: {brand}", personas_content, user_email=email_norm)
        log_automation("A05_PERSONAS", "Chân dung khách hàng", "SUCCESS", "Đã phân loại 3 phân khúc khách hàng thực tế", user_email=email_norm)

        # Giai đoạn 4: Lập lịch 30 ngày
        log_automation("A03_CALENDAR", "Lập lịch 30 ngày", "RUNNING", "Đang phân bổ 30 chủ đề theo phễu TOFU-MOFU-BOFU", user_email=email_norm)
        cal_items = generate_30day_calendar(profile)
        save_calendar_items(cal_items, user_email=email_norm)
        log_automation("A03_CALENDAR", "Lập lịch 30 ngày", "SUCCESS", f"Đã lên lịch 30 ngày đa kênh cho {brand}", user_email=email_norm)

        # Giai đoạn 5: Tự động sản xuất sẵn các nội dung trọng điểm
        log_automation("A03_CONTENT", "Sản xuất nội dung", "RUNNING", "Đang tự động viết nháp kịch bản đa kênh", user_email=email_norm)
        p_name = profile.get('products_services', 'giải pháp')
        p_ind = profile.get('industry', 'dịch vụ')
        p_price = profile.get('price_range', '')
        seed_topics = [
            ("tiktok", f"Bài toán kinh tế: Tối ưu chi phí và tăng trưởng cùng {p_name} ({p_price})"),
            ("facebook", f"3 Tiêu chuẩn sống còn khi lựa chọn đối tác {p_ind} mà doanh nghiệp cần biết"),
            ("facebook", f"Quy trình cam kết chất lượng và hỗ trợ 1-1 chuyên nghiệp từ {brand}"),
            ("tiktok", f"Vén màn những sai lầm phổ biến khiến doanh nghiệp thất thoát khách hàng khi chọn đối tác {p_ind}"),
            ("email", f"Báo giá chi tiết và lộ trình triển khai {p_name} trọn gói cho doanh nghiệp")
        ]

        for ch, top in seed_topics:
            c_dict = generate_content_item(profile, ch, top)
            save_content_package(
                channel=c_dict["channel"],
                topic=c_dict["topic"],
                body=c_dict["body"],
                cta=c_dict["cta"],
                user_email=email_norm
            )

        log_automation("A03_CONTENT", "Sản xuất nội dung", "SUCCESS", f"Đã viết sẵn {len(seed_topics)} bài viết và kịch bản video đa kênh", user_email=email_norm)
        log_automation("AUTOPILOT_COMPLETE", "Hoàn tất Auto-Pilot", "SUCCESS", f"Hệ thống Marketing OS đã tự động hóa 100% dữ liệu cho {brand}", user_email=email_norm)

    except Exception as e:
        log_automation("AUTOPILOT_ERROR", "Lỗi Auto-Pilot", "FAILED", str(e), user_email=email_norm)
        print(f"[Auto-Pilot Worker Error for {email_norm}] {e}")

@app.on_event("startup")
def startup_event():
    init_app_db()
    print(">>> Marketing OS 3.1 Server Started with Multi-Tenant Architecture.")

# --- Root HTML Serve ---
@app.get("/", response_class=HTMLResponse)
def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Marketing Automation OS is running. Please load static/index.html</h1>"

# --- API: Google / Gmail Authentication ---
@app.post("/api/auth/google")
def api_auth_google(req: GoogleAuthRequest, request: Request, background_tasks: BackgroundTasks):
    email = req.email.strip().lower()
    if "@" not in email or "." not in email:
        raise HTTPException(status_code=400, detail="Vui lòng nhập địa chỉ Gmail hoặc Google Workspace hợp lệ.")
    
    name = req.name.strip() if req.name else email.split("@")[0]
    picture = req.picture.strip() if req.picture else f"https://ui-avatars.com/api/?name={name}&background=0ea5e9&color=fff&bold=true"
    
    ip = request.client.host if (request and request.client) else ""
    user_agent = request.headers.get("user-agent", "") if request else ""
    
    user = create_or_update_user(email, name, picture, ip=ip, user_agent=user_agent)
    token = create_session(email)
    
    log_automation("AUTH_LOGIN", "Đăng nhập Gmail", "SUCCESS", f"Người dùng {email} đã đăng nhập thành công (Lượt truy cập #{user.get('login_count', 1)})", user_email=email)
    
    # Tự động gửi thông tin đăng nhập lên Google Sheet nếu đã cấu hình Webhook URL
    sheet_webhook = get_app_config("GOOGLE_SHEET_WEBHOOK_URL")
    if sheet_webhook:
        background_tasks.add_task(dispatch_login_to_google_sheet, sheet_webhook, user)
        
    return {
        "status": "success",
        "token": token,
        "user": user,
        "message": f"Đăng nhập thành công với tài khoản Gmail: {email}"
    }

@app.get("/api/auth/me")
def api_auth_me(token: Optional[str] = None, request: Request = None):
    auth_header = request.headers.get("Authorization") if request else None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    
    user = verify_session(token) if token else None
    if user:
        return {"status": "authenticated", "user": user}
    return {"status": "unauthenticated"}

@app.post("/api/auth/logout")
def api_auth_logout(req: LogoutRequest):
    delete_session(req.token)
    return {"status": "success", "message": "Đã đăng xuất phiên làm việc"}

# --- API: Google Sheet Management & Admin Endpoints ---
@app.get("/api/admin/users")
def api_get_admin_users():
    users = get_all_users()
    return {"status": "success", "users": users, "total": len(users)}

@app.get("/api/admin/users/export-sheets")
def api_export_users_sheets():
    csv_content = export_users_csv()
    return Response(
        content=csv_content.encode("utf-8"),
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": "attachment; filename=marketing_os_users_google_sheets.csv"}
    )

@app.get("/api/admin/sheets/config")
def api_get_sheets_config():
    webhook_url = get_app_config("GOOGLE_SHEET_WEBHOOK_URL", "")
    template_code = get_google_apps_script_template()
    return {
        "status": "success",
        "webhook_url": webhook_url,
        "is_connected": bool(webhook_url),
        "apps_script_template": template_code
    }

@app.post("/api/admin/sheets/config")
def api_set_sheets_config(req: SheetConfigUpdate):
    url = req.webhook_url.strip()
    set_app_config("GOOGLE_SHEET_WEBHOOK_URL", url)
    return {"status": "success", "webhook_url": url, "message": "Đã lưu URL kết nối Google Sheet thành công!"}

@app.post("/api/admin/sheets/sync-all")
def api_sync_all_to_sheets(background_tasks: BackgroundTasks):
    webhook_url = get_app_config("GOOGLE_SHEET_WEBHOOK_URL", "")
    if not webhook_url:
        raise HTTPException(status_code=400, detail="Chưa cấu hình Google Sheet Webhook URL. Vui lòng dán Webhook URL trước khi đồng bộ.")
    
    users = get_all_users()
    for u in users:
        background_tasks.add_task(dispatch_login_to_google_sheet, webhook_url, u)
        
    return {
        "status": "success",
        "synced_count": len(users),
        "message": f"Đang đồng bộ {len(users)} tài khoản người dùng lên Google Sheet của bạn trong nền!"
    }

# --- API: Reset To Clean Database (Chỉ xóa riêng workspace của người dùng hiện tại) ---
@app.post("/api/database/reset")
def api_database_reset(request: Request):
    user_email = get_current_user_email(request)
    res = reset_database_clean(user_email=user_email)
    log_automation("SYS_RESET", "Khởi tạo hệ thống mới", "SUCCESS", "Đã xóa sạch dữ liệu cũ và đưa cơ sở dữ liệu về trạng thái sạch ban đầu", user_email=user_email)
    return res

# --- API: Business Profile (Tách biệt theo User Email) ---
@app.get("/api/profile")
def api_get_profile(request: Request):
    user_email = get_current_user_email(request)
    return get_profile(user_email=user_email)

@app.post("/api/profile")
def api_update_profile(profile_data: ProfileUpdate, background_tasks: BackgroundTasks, request: Request):
    user_email = get_current_user_email(request)
    updated = update_profile(profile_data.dict(), user_email=user_email)
    if updated.get("brand_name"):
        background_tasks.add_task(run_full_autopilot_pipeline, updated, user_email)
    return {"status": "success", "profile": updated, "message": "Đã lưu hồ sơ của bạn thành công!"}

# --- API: Auto-Pilot Hub & Status ---
@app.get("/api/autopilot/status")
def api_autopilot_status(request: Request):
    user_email = get_current_user_email(request)
    prof = get_profile(user_email=user_email)
    logs = get_automation_logs(limit=25, user_email=user_email)
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM content_items WHERE LOWER(user_email) = ?", (user_email,))
    content_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM calendar_schedules WHERE LOWER(user_email) = ?", (user_email,))
    calendar_count = cur.fetchone()[0]
    conn.close()

    return {
        "status": "active",
        "user_email": user_email,
        "brand_name": prof.get("brand_name"),
        "industry": prof.get("industry"),
        "total_content": content_count,
        "calendar_days": calendar_count,
        "logs": logs
    }

@app.post("/api/autopilot/run")
def api_trigger_autopilot(background_tasks: BackgroundTasks, request: Request):
    user_email = get_current_user_email(request)
    prof = get_profile(user_email=user_email)
    background_tasks.add_task(run_full_autopilot_pipeline, prof, user_email)
    return {"status": "success", "message": "Đã kích hoạt chạy tự động toàn trình cho tài khoản của bạn!"}

@app.get("/api/autopilot/logs")
def api_get_logs(request: Request):
    user_email = get_current_user_email(request)
    return get_automation_logs(limit=30, user_email=user_email)

# --- API: Latest Auto-Hydrated Research ---
@app.get("/api/research/latest")
def api_get_latest_research(request: Request):
    user_email = get_current_user_email(request)
    return get_latest_research(user_email=user_email)

# --- API: On-demand AI Research ---
@app.post("/api/research/market")
def api_run_market_research(request: Request):
    user_email = get_current_user_email(request)
    profile = get_profile(user_email=user_email)
    result_md = generate_market_research(profile)
    save_research_record("market_research", f"Nghiên cứu thị trường: {profile.get('brand_name')}", result_md, user_email=user_email)
    log_automation("A01_MARKET", "Nghiên cứu thị trường", "SUCCESS", "Đã cập nhật phân tích thị trường mới nhất", user_email=user_email)
    return {"status": "success", "result": result_md}

@app.post("/api/research/market/custom")
def api_run_custom_market_research(req: CustomMarketRequest, request: Request):
    user_email = get_current_user_email(request)
    profile = get_profile(user_email=user_email)
    location = req.location or req.region or "Toàn quốc"
    scope_type = req.scope_type or "province"
    options = {
        "scope_type": scope_type,
        "location": location,
        "region": location,
        "price_tier": req.price_tier,
        "objective": req.objective
    }
    result_md = generate_custom_market_research(profile, options)
    brand_display = profile.get('brand_name') or 'Doanh nghiệp'
    save_research_record("market_research", f"Nghiên cứu thị trường ({location}): {brand_display}", result_md, user_email=user_email)
    log_automation("A01_MARKET", f"Nghiên cứu thị trường: {location}", "SUCCESS", f"Đã phân tích chuyên sâu địa bàn {location} ({len(result_md)} ký tự)", user_email=user_email)
    return {"status": "success", "result": result_md, "location": location, "scope_type": scope_type}

# --- API: Competitor Auto-Discovery & Strategic Battlecards ---
@app.post("/api/competitors/discover")
def api_discover_competitors(req: CompetitorDiscoverRequest = None, request: Request = None):
    user_email = get_current_user_email(request)
    profile = get_profile(user_email=user_email)
    criteria = req.criteria if req else "all"
    market_context = req.market_context if req and req.market_context else {
        "location": profile.get("market_location") or "Toàn quốc",
        "scope_type": profile.get("market_scope_type") or "province",
        "price_tier": profile.get("price_range") or "Tiêu chuẩn"
    }
    discovered = auto_discover_competitors(profile, criteria=criteria, market_context=market_context)
    if discovered:
        m_loc = market_context.get("location", "Toàn quốc")
        save_discovered_competitors(discovered, market_context=m_loc, user_email=user_email)
        log_automation("A02_DISCOVERY", f"Rà quét đối thủ ({m_loc})", "SUCCESS", f"Đã rà quét và đồng bộ {len(discovered)} đối thủ cạnh tranh trên thị trường {m_loc}", user_email=user_email)
    items = get_discovered_competitors(user_email=user_email)
    return {"status": "success", "competitors": items, "profile": get_profile(user_email=user_email)}

@app.get("/api/competitors/discovered")
def api_get_discovered_competitors(request: Request):
    user_email = get_current_user_email(request)
    items = get_discovered_competitors(user_email=user_email)
    return {"status": "success", "competitors": items}

@app.post("/api/competitors/add-manual")
def api_add_manual_competitor(req: ManualCompetitorRequest, request: Request):
    user_email = get_current_user_email(request)
    profile = get_profile(user_email=user_email)
    comp_dict = req.dict()
    comp_id = add_or_update_competitor(comp_dict, user_email=user_email)
    
    if req.scan_deep:
        try:
            dossier_res = analyze_deep_competitor_dossier(profile, comp_dict)
            battlecard_md = dossier_res.get("battlecard_markdown", "")
            if battlecard_md:
                save_competitor_battlecard(comp_id, battlecard_md, user_email=user_email)
            log_automation("A02_INTEL", f"Tình báo chuyên sâu: {req.name}", "SUCCESS", f"Đã quét website/hotline và thiết lập hồ sơ tác chiến 1-1 với {req.name}", user_email=user_email)
        except Exception as e:
            print(f"[ERROR] Dossier scan error: {e}")
            
    comp_data = get_competitor_by_id(comp_id, user_email=user_email)
    items = get_discovered_competitors(user_email=user_email)
    return {"status": "success", "competitor": comp_data, "competitors": items}

@app.post("/api/competitors/dossier/scan")
def api_scan_competitor_dossier(req: CompetitorDossierScanRequest, request: Request):
    user_email = get_current_user_email(request)
    profile = get_profile(user_email=user_email)
    comp = get_competitor_by_id(req.competitor_id, user_email=user_email)
    if not comp:
        raise HTTPException(status_code=404, detail="Không tìm thấy đối thủ trong cơ sở dữ liệu")
    dossier_res = analyze_deep_competitor_dossier(profile, comp)
    battlecard_md = dossier_res.get("battlecard_markdown", "")
    save_competitor_battlecard(req.competitor_id, battlecard_md, user_email=user_email)
    log_automation("A02_INTEL", f"Tình báo đối thủ: {comp['name']}", "SUCCESS", f"Đã hoàn thành hồ sơ tình báo chuyên sâu & Battlecard cho {comp['name']}", user_email=user_email)
    return {"status": "success", "battlecard": battlecard_md, "competitor": get_competitor_by_id(req.competitor_id, user_email=user_email)}

@app.delete("/api/competitors/dossier/{comp_id}")
def api_delete_competitor_endpoint(comp_id: int, request: Request):
    user_email = get_current_user_email(request)
    delete_competitor(comp_id, user_email=user_email)
    log_automation("A02_INTEL", "Xóa đối thủ", "SUCCESS", f"Đã xóa đối thủ ID {comp_id} khỏi hồ sơ", user_email=user_email)
    items = get_discovered_competitors(user_email=user_email)
    return {"status": "success", "competitors": items}

@app.post("/api/competitors/battlecard")
def api_generate_single_battlecard(req: SingleBattlecardRequest, request: Request):
    user_email = get_current_user_email(request)
    profile = get_profile(user_email=user_email)
    result_md = generate_single_competitor_battlecard(profile, req.name, req.website or "")
    save_research_record("battlecards", f"Battlecard: {req.name}", result_md, user_email=user_email)
    log_automation("A02_BATTLECARD", f"Battlecard vs {req.name}", "SUCCESS", f"Đã lập kịch bản đối đầu 1-1 với {req.name}", user_email=user_email)
    return {"status": "success", "result": result_md, "competitor": req.name}

@app.post("/api/research/competitors")
def api_run_competitor_analysis(request: Request):
    user_email = get_current_user_email(request)
    profile = get_profile(user_email=user_email)
    result_md = generate_competitor_analysis(profile)
    updated_profile = get_profile(user_email=user_email)
    save_research_record("battlecards", f"Tình báo đối thủ: {updated_profile.get('brand_name')}", result_md, user_email=user_email)
    log_automation("A02_COMPETITORS", "Tình báo đối thủ", "SUCCESS", "Đã cập nhật tình báo đối thủ & Battlecards", user_email=user_email)
    return {"status": "success", "result": result_md, "competitors": updated_profile.get("competitors")}

@app.post("/api/strategy/personas")
def api_run_personas(request: Request):
    user_email = get_current_user_email(request)
    profile = get_profile(user_email=user_email)
    result_md = generate_personas(profile)
    save_research_record("personas", f"Chân dung khách hàng: {profile.get('brand_name')}", result_md, user_email=user_email)
    log_automation("A05_PERSONAS", "Chân dung khách hàng", "SUCCESS", "Đã cập nhật 3 chân dung khách hàng", user_email=user_email)
    return {"status": "success", "result": result_md}

# --- API: Content Creation Studio & Multimedia Packages ---
@app.post("/api/content/create")
def api_create_content(req: ContentRequest, request: Request):
    user_email = get_current_user_email(request)
    profile = get_profile(user_email=user_email)
    content_dict = generate_content_item(profile, req.channel, req.topic, req.format_type)
    
    item_id = save_content_package(
        channel=content_dict["channel"],
        topic=content_dict["topic"],
        body=content_dict["body"],
        cta=content_dict["cta"],
        status="draft",
        user_email=user_email
    )
    content_dict["id"] = item_id
    log_automation("A03_CONTENT", "Tạo nội dung mới", "SUCCESS", f"Đã viết bài chủ đề: {req.topic}", user_email=user_email)
    return {"status": "success", "content": content_dict}

@app.post("/api/content/generate_package")
def api_generate_content_package(req: ContentPackageRequest, request: Request):
    user_email = get_current_user_email(request)
    profile = get_profile(user_email=user_email)
    pkg = generate_full_content_package(profile, req.topic, req.channel, req.direction)
    item_id = save_content_package(
        channel=pkg["channel"],
        topic=pkg["topic"],
        body=pkg["body"],
        cta=pkg["cta"],
        video_script=pkg.get("video_script", ""),
        image_prompt=pkg.get("image_prompt", ""),
        status="ready",
        user_email=user_email
    )
    pkg["id"] = item_id
    log_automation("A03_CONTENT", "Sản xuất trọn gói nội dung", "SUCCESS", f"Đã tạo Bài viết + Kịch bản Video + Prompt Ảnh cho '{req.topic[:35]}'", user_email=user_email)
    return {"status": "success", "package": pkg}

@app.get("/api/content/history")
def api_get_content_history(request: Request):
    user_email = get_current_user_email(request)
    items = get_content_items(user_email=user_email)
    return {"status": "success", "items": items}

# --- API: Content Calendar ---
@app.get("/api/calendar/list")
def api_get_calendar_list(request: Request):
    user_email = get_current_user_email(request)
    items = get_calendar_items(user_email=user_email)
    if not items:
        prof = get_profile(user_email=user_email)
        if prof.get("brand_name"):
            gen_items = generate_30day_calendar(prof)
            save_calendar_items(gen_items, user_email=user_email)
            items = get_calendar_items(user_email=user_email)
    return {"status": "success", "items": items}

@app.post("/api/calendar/generate_custom")
def api_generate_custom_calendar(req: CustomCalendarRequest, request: Request):
    user_email = get_current_user_email(request)
    profile = get_profile(user_email=user_email)
    direction = req.direction or "educational"
    profile["content_direction"] = direction
    update_profile(profile, user_email=user_email)
    items = generate_custom_30day_calendar(profile, direction=direction)
    save_calendar_items(items, user_email=user_email)
    log_automation("A03_CALENDAR", "Lập lịch 30 ngày tùy biến", "SUCCESS", f"Đã tạo mới 30 ngày nội dung thiên hướng '{direction}'", user_email=user_email)
    return {"status": "success", "items": items, "direction": direction}

@app.post("/api/calendar/generate")
def api_generate_calendar(request: Request):
    user_email = get_current_user_email(request)
    profile = get_profile(user_email=user_email)
    items = generate_30day_calendar(profile)
    save_calendar_items(items, user_email=user_email)
    log_automation("A03_CALENDAR", "Lập lại lịch 30 ngày", "SUCCESS", f"Đã tạo mới 30 ngày nội dung cho {profile.get('brand_name')}", user_email=user_email)
    return {"status": "success", "items": items}

# --- API: CATALYST Multi-Agent Campaign Orchestrator (6 Chuyên Gia AI Độc Lập) ---
@app.post("/api/catalyst/run")
def api_run_catalyst(req: CatalystRunRequest, request: Request):
    user_email = get_current_user_email(request)
    profile = get_profile(user_email=user_email)
    result = run_catalyst_orchestrator(profile, req.loop_type or "weekly_intel", req.custom_brief or "")
    save_research_record("catalyst_loop", f"CATALYST: {result['loop_name']}", result["content"], user_email=user_email)
    log_automation("CATALYST_LOOP", result["loop_name"], "SUCCESS", f"Đã điều phối 6 chuyên viên AI hoàn thành {len(result['deliverables'])} tài nguyên", user_email=user_email)
    return {"status": "success", "data": result}

@app.get("/api/catalyst/latest")
def api_get_latest_catalyst(request: Request):
    user_email = get_current_user_email(request)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM research_records WHERE category = 'catalyst_loop' AND LOWER(user_email) = ? ORDER BY id DESC LIMIT 1", (user_email,))
    row = cur.fetchone()
    conn.close()
    if row:
        row_dict = dict(row)
        profile = get_profile(user_email=user_email)
        sections = build_catalyst_sections(row_dict.get("content", ""), profile, row_dict.get("title", ""))
        return {"status": "success", "item": row_dict, "sections": sections}
    return {"status": "empty"}

# --- API: Analytics & Performance ---
@app.get("/api/analytics/summary")
def api_get_analytics(request: Request):
    user_email = get_current_user_email(request)
    return get_analytics_summary(user_email=user_email)

@app.post("/api/analytics/record")
def api_record_metric(metric: MetricEntry, request: Request):
    user_email = get_current_user_email(request)
    record_performance_metric(metric.dict(), user_email=user_email)
    return {"status": "success", "message": "Record saved successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
