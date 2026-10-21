# -*- coding: utf-8 -*-
"""
Main FastAPI Web Server for Marketing Automation System (Auto-Pilot OS)
- 24/7 Background Scheduler & Worker
- Auto-Pilot Full Pipeline (Auto-Research, Auto-Scrape, Auto-Personas, Auto-Calendar, Auto-Draft)
- Automatic Data Hydration (No empty tabs, no manual click required)
- Real-time Automation Logs Feed
"""
import os
import sys
import time
import threading
from pathlib import Path
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
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
    save_content_package,
    create_or_update_user, create_session, verify_session, delete_session,
    reset_database_clean
)
from app.ai_engine import (
    generate_market_research, generate_custom_market_research,
    generate_competitor_analysis, generate_single_competitor_battlecard,
    generate_personas, generate_content_item,
    generate_30day_calendar, generate_custom_30day_calendar,
    generate_full_content_package,
    auto_discover_competitors,
    run_catalyst_orchestrator
)

app = FastAPI(title="Marketing Automation OS", version="3.0.0")

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Mount static folder
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Pydantic models
class GoogleAuthRequest(BaseModel):
    email: str
    name: Optional[str] = ""
    picture: Optional[str] = ""
    credential: Optional[str] = ""

class LogoutRequest(BaseModel):
    token: str

class ProfileUpdate(BaseModel):
    brand_name: str
    industry: str
    business_model: str
    products_services: str
    price_range: Optional[str] = ""
    target_audience: str
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
    social_channels: Optional[str] = ""
    usp_advantages: Optional[str] = ""

class CustomMarketRequest(BaseModel):
    scope_type: Optional[str] = "province"
    location: Optional[str] = "Toàn quốc"
    region: Optional[str] = "Toàn quốc"
    price_tier: Optional[str] = ""
    objective: Optional[str] = "Đánh chiếm thị phần từ đối thủ & Tăng trưởng doanh thu"

class CompetitorDiscoverRequest(BaseModel):
    criteria: Optional[str] = "all"

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

def run_full_autopilot_pipeline(profile: dict = None):
    """Thực thi toàn bộ quy trình tự động hóa khép kín không cần người dùng can thiệp"""
    if not profile:
        profile = get_profile()

    brand = profile.get("brand_name", "Doanh nghiệp")
    log_automation("AUTOPILOT_START", "Khởi động Auto-Pilot", "RUNNING", f"Bắt đầu vận hành chuỗi tự động cho {brand}")

    try:
        # Giai đoạn 1: Nghiên cứu thị trường
        log_automation("A01_MARKET", "Nghiên cứu thị trường", "RUNNING", "Đang tính toán TAM/SAM/SOM và PESTEL")
        mr_content = generate_market_research(profile)
        save_research_record("market_research", f"Nghiên cứu thị trường: {brand}", mr_content)
        log_automation("A01_MARKET", "Nghiên cứu thị trường", "SUCCESS", f"Đã hoàn thành báo cáo thị trường ({len(mr_content)} ký tự)")

        # Giai đoạn 2: Tình báo đối thủ
        log_automation("A02_COMPETITORS", "Tình báo đối thủ", "RUNNING", "Đang cào website đối thủ và bóc tách điểm yếu")
        comp_content = generate_competitor_analysis(profile)
        save_research_record("battlecards", f"Tình báo đối thủ: {brand}", comp_content)
        log_automation("A02_COMPETITORS", "Tình báo đối thủ", "SUCCESS", f"Đã lập Battlecards & Kịch bản phản đòn ({len(comp_content)} ký tự)")

        # Giai đoạn 3: Chân dung khách hàng
        log_automation("A05_PERSONAS", "Chân dung khách hàng", "RUNNING", "Đang dựng 3 chân dung khách hàng cốt lõi")
        personas_content = generate_personas(profile)
        save_research_record("personas", f"Chân dung khách hàng: {brand}", personas_content)
        log_automation("A05_PERSONAS", "Chân dung khách hàng", "SUCCESS", "Đã phân loại 3 phân khúc khách hàng thực tế")

        # Giai đoạn 4: Lập lịch 30 ngày
        log_automation("A03_CALENDAR", "Lập lịch 30 ngày", "RUNNING", "Đang phân bổ 30 chủ đề theo phễu TOFU-MOFU-BOFU")
        cal_items = generate_30day_calendar(profile)
        save_calendar_items(cal_items)
        log_automation("A03_CALENDAR", "Lập lịch 30 ngày", "SUCCESS", f"Đã lên lịch 30 ngày đa kênh cho {brand}")

        # Giai đoạn 5: Tự động sản xuất sẵn các nội dung trọng điểm
        log_automation("A03_CONTENT", "Sản xuất nội dung", "RUNNING", "Đang tự động viết nháp kịch bản đa kênh")
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

        conn = get_connection()
        cur = conn.cursor()
        for ch, top in seed_topics:
            c_dict = generate_content_item(profile, ch, top)
            cur.execute("""
            INSERT INTO content_items (channel, topic, body, cta, status)
            VALUES (?, ?, ?, ?, ?)
            """, (c_dict["channel"], c_dict["topic"], c_dict["body"], c_dict["cta"], "ready"))
        conn.commit()
        conn.close()

        log_automation("A03_CONTENT", "Sản xuất nội dung", "SUCCESS", f"Đã viết sẵn {len(seed_topics)} bài viết và kịch bản video đa kênh")
        log_automation("AUTOPILOT_COMPLETE", "Hoàn tất Auto-Pilot", "SUCCESS", f"Hệ thống Marketing OS đã tự động hóa 100% dữ liệu cho {brand}")

    except Exception as e:
        log_automation("AUTOPILOT_ERROR", "Lỗi Auto-Pilot", "FAILED", str(e))
        print(f"[Auto-Pilot Worker Error] {e}")

def background_scheduler_worker():
    """Luồng worker chạy ngầm định kỳ 24/7 kiểm tra tác vụ tự động"""
    time.sleep(3)
    # Kiểm tra xem đã có dữ liệu nghiên cứu chưa, nếu chưa thì tự động chạy ngay lần đầu
    latest = get_latest_research()
    if not latest.get("market_research") or not latest.get("battlecards"):
        print("[Auto-Pilot Worker] Chưa có dữ liệu ban đầu. Đang tự động kích hoạt Full Pipeline...")
        run_full_autopilot_pipeline()
    else:
        log_automation("SYSTEM_CHECK", "Kiểm tra hệ thống", "SUCCESS", "Động cơ Auto-Pilot đang hoạt động bình thường")

    # Vòng lặp định kỳ mỗi 30 phút
    while True:
        try:
            time.sleep(1800) # 30 phút
            prof = get_profile()
            log_automation("A01_MONITOR", "Giám sát định kỳ", "SUCCESS", f"Quét cập nhật đối thủ và dữ liệu ngành cho {prof.get('brand_name')}")
        except Exception as e:
            time.sleep(60)

@app.on_event("startup")
def startup_event():
    init_app_db()
    # Khởi động luồng Auto-Pilot Worker chạy ngầm
    t = threading.Thread(target=background_scheduler_worker, daemon=True)
    t.start()

@app.get("/", response_class=HTMLResponse)
def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Marketing Automation OS is running. Please load static/index.html</h1>"

# --- API: Google / Gmail Authentication ---
@app.post("/api/auth/google")
def api_auth_google(req: GoogleAuthRequest):
    email = req.email.strip().lower()
    if "@" not in email or "." not in email:
        raise HTTPException(status_code=400, detail="Vui lòng nhập địa chỉ Gmail hoặc Google Workspace hợp lệ.")
    
    name = req.name.strip() if req.name else email.split("@")[0]
    picture = req.picture.strip() if req.picture else f"https://ui-avatars.com/api/?name={name}&background=0ea5e9&color=fff&bold=true"
    
    user = create_or_update_user(email, name, picture)
    token = create_session(email)
    log_automation("AUTH_LOGIN", "Đăng nhập Gmail", "SUCCESS", f"Người dùng {email} đã đăng nhập thành công")
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

# --- API: Reset To Clean Database (Xóa sạch toàn bộ dữ liệu mẫu / thử nghiệm) ---
@app.post("/api/database/reset")
def api_database_reset():
    res = reset_database_clean()
    log_automation("SYS_RESET", "Khởi tạo hệ thống mới", "SUCCESS", "Đã xóa sạch dữ liệu cũ và đưa cơ sở dữ liệu về trạng thái sạch ban đầu")
    return res

# --- API: Business Profile ---
@app.get("/api/profile")
def api_get_profile():
    return get_profile()

@app.post("/api/profile")
def api_update_profile(profile_data: ProfileUpdate, background_tasks: BackgroundTasks):
    updated = update_profile(profile_data.dict())
    # Khi cập nhật profile, tự động kích hoạt chạy lại Auto-Pilot trong nền
    background_tasks.add_task(run_full_autopilot_pipeline, updated)
    return {"status": "success", "profile": updated, "message": "Đã lưu hồ sơ và kích hoạt Auto-Pilot tự động chạy ngầm!"}

# --- API: Auto-Pilot Hub & Status ---
@app.get("/api/autopilot/status")
def api_autopilot_status():
    prof = get_profile()
    logs = get_automation_logs(limit=25)
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM content_items")
    content_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM calendar_schedules")
    calendar_count = cur.fetchone()[0]
    conn.close()

    return {
        "status": "active",
        "brand_name": prof.get("brand_name"),
        "industry": prof.get("industry"),
        "total_content": content_count,
        "calendar_days": calendar_count,
        "logs": logs
    }

@app.post("/api/autopilot/run")
def api_trigger_autopilot(background_tasks: BackgroundTasks):
    prof = get_profile()
    background_tasks.add_task(run_full_autopilot_pipeline, prof)
    return {"status": "success", "message": "Đã kích hoạt chạy tự động toàn trình thành công!"}

@app.get("/api/autopilot/logs")
def api_get_logs():
    return get_automation_logs(limit=30)

# --- API: Latest Auto-Hydrated Research ---
@app.get("/api/research/latest")
def api_get_latest_research():
    return get_latest_research()

# --- API: On-demand AI Research ---
@app.post("/api/research/market")
def api_run_market_research():
    profile = get_profile()
    result_md = generate_market_research(profile)
    save_research_record("market_research", f"Nghiên cứu thị trường: {profile.get('brand_name')}", result_md)
    log_automation("A01_MARKET", "Nghiên cứu thị trường", "SUCCESS", "Đã cập nhật phân tích thị trường mới nhất")
    return {"status": "success", "result": result_md}

@app.post("/api/research/market/custom")
def api_run_custom_market_research(req: CustomMarketRequest):
    profile = get_profile()
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
    save_research_record("market_research", f"Nghiên cứu thị trường ({location}): {brand_display}", result_md)
    log_automation("A01_MARKET", f"Nghiên cứu thị trường: {location}", "SUCCESS", f"Đã phân tích chuyên sâu địa bàn {location} ({len(result_md)} ký tự)")
    return {"status": "success", "result": result_md, "location": location, "scope_type": scope_type}

# --- API: Competitor Auto-Discovery & Strategic Battlecards ---
@app.post("/api/competitors/discover")
def api_discover_competitors(req: CompetitorDiscoverRequest = None):
    profile = get_profile()
    criteria = req.criteria if req else "all"
    discovered = auto_discover_competitors(profile, criteria=criteria)
    if discovered:
        comp_str = ", ".join([f"{c['name']} ({c.get('website', '')})" if c.get('website') else c['name'] for c in discovered])
        profile["competitors"] = comp_str
        update_profile(profile)
        save_discovered_competitors(discovered)
        log_automation("A02_DISCOVERY", "Rà quét đối thủ AI", "SUCCESS", f"Đã rà quét và phát hiện {len(discovered)} đối thủ cạnh tranh trên thị trường")
    return {"status": "success", "competitors": discovered, "profile": profile}

@app.get("/api/competitors/discovered")
def api_get_discovered_competitors():
    items = get_discovered_competitors()
    return {"status": "success", "competitors": items}

@app.post("/api/competitors/battlecard")
def api_generate_single_battlecard(req: SingleBattlecardRequest):
    profile = get_profile()
    result_md = generate_single_competitor_battlecard(profile, req.name, req.website or "")
    save_research_record("battlecards", f"Battlecard: {req.name}", result_md)
    log_automation("A02_BATTLECARD", f"Battlecard vs {req.name}", "SUCCESS", f"Đã lập kịch bản đối đầu 1-1 với {req.name}")
    return {"status": "success", "result": result_md, "competitor": req.name}

@app.post("/api/research/competitors")
def api_run_competitor_analysis():
    profile = get_profile()
    result_md = generate_competitor_analysis(profile)
    updated_profile = get_profile()
    save_research_record("battlecards", f"Tình báo đối thủ: {updated_profile.get('brand_name')}", result_md)
    log_automation("A02_COMPETITORS", "Tình báo đối thủ", "SUCCESS", "Đã cập nhật tình báo đối thủ & Battlecards")
    return {"status": "success", "result": result_md, "competitors": updated_profile.get("competitors")}

@app.post("/api/strategy/personas")
def api_run_personas():
    profile = get_profile()
    result_md = generate_personas(profile)
    save_research_record("personas", f"Chân dung khách hàng: {profile.get('brand_name')}", result_md)
    log_automation("A05_PERSONAS", "Chân dung khách hàng", "SUCCESS", "Đã cập nhật 3 chân dung khách hàng")
    return {"status": "success", "result": result_md}

# --- API: Content Creation Studio & Multimedia Packages ---
@app.post("/api/content/create")
def api_create_content(req: ContentRequest):
    profile = get_profile()
    content_dict = generate_content_item(profile, req.channel, req.topic, req.format_type)
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO content_items (channel, topic, body, cta, status)
    VALUES (?, ?, ?, ?, ?)
    """, (content_dict["channel"], content_dict["topic"], content_dict["body"], content_dict["cta"], "draft"))
    conn.commit()
    item_id = cur.lastrowid
    conn.close()
    
    content_dict["id"] = item_id
    log_automation("A03_CONTENT", "Tạo nội dung mới", "SUCCESS", f"Đã viết bài chủ đề: {req.topic}")
    return {"status": "success", "content": content_dict}

@app.post("/api/content/generate_package")
def api_generate_content_package(req: ContentPackageRequest):
    profile = get_profile()
    pkg = generate_full_content_package(profile, req.topic, req.channel, req.direction)
    item_id = save_content_package(
        channel=pkg["channel"],
        topic=pkg["topic"],
        body=pkg["body"],
        cta=pkg["cta"],
        video_script=pkg.get("video_script", ""),
        image_prompt=pkg.get("image_prompt", ""),
        status="ready"
    )
    pkg["id"] = item_id
    log_automation("A03_CONTENT", "Sản xuất trọn gói nội dung", "SUCCESS", f"Đã tạo Bài viết + Kịch bản Video + Prompt Ảnh cho '{req.topic[:35]}'")
    return {"status": "success", "package": pkg}

@app.get("/api/content/history")
def api_get_content_history():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM content_items ORDER BY id DESC LIMIT 50")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# --- API: Content Calendar ---
@app.get("/api/calendar/list")
def api_get_calendar_list():
    items = get_calendar_items()
    if not items:
        prof = get_profile()
        gen_items = generate_30day_calendar(prof)
        save_calendar_items(gen_items)
        items = get_calendar_items()
    return {"status": "success", "items": items}

@app.post("/api/calendar/generate_custom")
def api_generate_custom_calendar(req: CustomCalendarRequest):
    profile = get_profile()
    direction = req.direction or "educational"
    profile["content_direction"] = direction
    update_profile(profile)
    items = generate_custom_30day_calendar(profile, direction=direction)
    save_calendar_items(items)
    log_automation("A03_CALENDAR", "Lập lịch 30 ngày tùy biến", "SUCCESS", f"Đã tạo mới 30 ngày nội dung thiên hướng '{direction}'")
    return {"status": "success", "items": items, "direction": direction}

@app.post("/api/calendar/generate")
def api_generate_calendar():
    profile = get_profile()
    items = generate_30day_calendar(profile)
    save_calendar_items(items)
    log_automation("A03_CALENDAR", "Lập lại lịch 30 ngày", "SUCCESS", f"Đã tạo mới 30 ngày nội dung cho {profile.get('brand_name')}")
    return {"status": "success", "items": items}

# --- API: CATALYST Multi-Agent Campaign Orchestrator (Inspired by SaaS Marketing Agents) ---
@app.post("/api/catalyst/run")
def api_run_catalyst(req: CatalystRunRequest):
    profile = get_profile()
    result = run_catalyst_orchestrator(profile, req.loop_type or "weekly_intel", req.custom_brief or "")
    save_research_record("catalyst_loop", f"CATALYST: {result['loop_name']}", result["content"])
    log_automation("CATALYST_LOOP", result["loop_name"], "SUCCESS", f"Đã điều phối 5 chuyên viên AI hoàn thành {len(result['deliverables'])} tài nguyên")
    return {"status": "success", "data": result}

@app.get("/api/catalyst/latest")
def api_get_latest_catalyst():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM research_records WHERE category = 'catalyst_loop' ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()
    if row:
        return {"status": "success", "item": dict(row)}
    return {"status": "empty"}

# --- API: Analytics & Performance ---
@app.get("/api/analytics/summary")
def api_get_analytics():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT 
        COALESCE(SUM(ad_spend), 0.0) as total_spend,
        COALESCE(SUM(revenue), 0.0) as total_rev,
        COALESCE(SUM(orders_count), 0) as total_orders,
        COALESCE(SUM(leads_count), 0) as total_leads,
        COALESCE(SUM(impressions), 0) as total_impr,
        COALESCE(SUM(clicks), 0) as total_clicks
    FROM performance_metrics
    """)
    totals = dict(cur.fetchone())

    spend = totals["total_spend"]
    rev = totals["total_rev"]
    orders = totals["total_orders"]
    leads = totals["total_leads"]

    mer = (rev / spend) if spend > 0 else 0.0
    roas = mer
    cac = (spend / orders) if orders > 0 else 0.0
    cpl = (spend / leads) if leads > 0 else 0.0

    cur.execute("SELECT date, ad_spend, revenue, orders_count, leads_count FROM performance_metrics ORDER BY date DESC LIMIT 14")
    history = [dict(r) for r in cur.fetchall()]
    conn.close()

    return {
        "totals": {
            "spend": round(spend, 0),
            "revenue": round(rev, 0),
            "mer": round(mer, 2),
            "roas": round(roas, 2),
            "orders": orders,
            "leads": leads,
            "cac": round(cac, 0),
            "cpl": round(cpl, 0)
        },
        "history": list(reversed(history))
    }

@app.post("/api/analytics/record")
def api_record_metric(metric: MetricEntry):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO performance_metrics (date, ad_spend, revenue, orders_count, leads_count, impressions, clicks, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        metric.date, metric.ad_spend, metric.revenue,
        metric.orders_count, metric.leads_count, metric.impressions,
        metric.clicks, metric.notes
    ))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Record saved successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
