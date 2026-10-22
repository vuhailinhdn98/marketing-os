# -*- coding: utf-8 -*-
"""
Database layer for Marketing Automation App
SQLite database: marketing_os_app.db
- Multi-Tenant User Isolation: Mỗi Gmail là 1 tài khoản, 1 workspace riêng biệt
- User Management & Google Sheets Sync
- Business Profile (Clean State, Dynamic Geographic Market)
- Research Records, Content, Competitors, Calendar, Automations
"""
import sqlite3
import json
import uuid
import os
import io
import csv
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "marketing_os_app.db"

def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def normalize_email(email: Optional[str]) -> str:
    if not email or "@" not in str(email):
        return "default@marketing-os.local"
    return str(email).strip().lower()

def init_app_db():
    conn = get_connection()
    cur = conn.cursor()
    
    # 1. Bảng quản lý người dùng (App Users)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS app_users (
        email TEXT PRIMARY KEY,
        name TEXT,
        picture TEXT,
        login_count INTEGER DEFAULT 1,
        ip_address TEXT DEFAULT '',
        user_agent TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Bảng phiên đăng nhập (Sessions)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS app_sessions (
        token TEXT PRIMARY KEY,
        email TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3. Bảng cấu hình hệ thống (Configs - e.g. Google Sheet Webhook URL)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS app_configs (
        key TEXT PRIMARY KEY,
        value TEXT
    );
    """)

    # 4. Bảng lưu trữ hồ sơ doanh nghiệp theo người dùng (Multi-tenant User Profiles)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_profiles (
        user_email TEXT PRIMARY KEY,
        brand_name TEXT NOT NULL DEFAULT '',
        industry TEXT NOT NULL DEFAULT '',
        business_model TEXT NOT NULL DEFAULT 'B2C / B2B',
        products_services TEXT NOT NULL DEFAULT '',
        price_range TEXT DEFAULT '',
        target_audience TEXT NOT NULL DEFAULT '',
        competitors TEXT DEFAULT '',
        channels TEXT DEFAULT 'Facebook, TikTok, Google, YouTube, Website',
        monthly_budget REAL DEFAULT 0,
        brand_voice TEXT DEFAULT 'Chuyên nghiệp, Uy tín',
        gemini_api_key TEXT DEFAULT '',
        gemini_model TEXT DEFAULT 'gemini-2.5-flash',
        region TEXT DEFAULT 'Toàn quốc',
        market_scope_type TEXT DEFAULT 'province',
        market_location TEXT DEFAULT 'Toàn quốc',
        content_direction TEXT DEFAULT 'educational',
        phone_hotline TEXT DEFAULT '',
        website_url TEXT DEFAULT '',
        social_channels TEXT DEFAULT '',
        usp_advantages TEXT DEFAULT '',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 5. Bảng lưu trữ kết quả nghiên cứu thị trường & chiến lược
    cur.execute("""
    CREATE TABLE IF NOT EXISTS research_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL DEFAULT 'default@marketing-os.local',
        category TEXT NOT NULL, -- 'market_research', 'personas', 'battlecards', 'strategy', 'catalyst_loop'
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        metadata_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 6. Bảng lưu trữ nội dung đã tạo (Content Studio & Calendar)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS content_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL DEFAULT 'default@marketing-os.local',
        channel TEXT NOT NULL,
        topic TEXT NOT NULL,
        pillar TEXT,
        funnel_stage TEXT,
        hook TEXT,
        body TEXT NOT NULL,
        cta TEXT,
        video_script TEXT,
        image_prompt TEXT,
        status TEXT DEFAULT 'draft',
        publish_date TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 7. Bảng ghi nhận chỉ số & đơn hàng thực tế
    cur.execute("""
    CREATE TABLE IF NOT EXISTS performance_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL DEFAULT 'default@marketing-os.local',
        date TEXT NOT NULL,
        ad_spend REAL DEFAULT 0,
        revenue REAL DEFAULT 0,
        orders_count INTEGER DEFAULT 0,
        leads_count INTEGER DEFAULT 0,
        impressions INTEGER DEFAULT 0,
        clicks INTEGER DEFAULT 0,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 8. Bảng lưu trữ Lịch biên tập 30 Ngày (Calendar Schedules)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS calendar_schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL DEFAULT 'default@marketing-os.local',
        day_number INTEGER NOT NULL,
        channel TEXT NOT NULL,
        pillar TEXT,
        funnel_stage TEXT,
        topic TEXT NOT NULL,
        draft_content TEXT,
        status TEXT DEFAULT 'scheduled',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 9. Bảng lưu trữ Nhật ký Vận Hành Tự Động (Auto-Pilot Execution Logs)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS automation_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL DEFAULT 'default@marketing-os.local',
        task_code TEXT NOT NULL,
        task_name TEXT NOT NULL,
        status TEXT NOT NULL,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 10. Bảng lưu trữ Đối thủ cạnh tranh được AI rà quét & Quản lý Tình báo
    cur.execute("""
    CREATE TABLE IF NOT EXISTS discovered_competitors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL DEFAULT 'default@marketing-os.local',
        name TEXT NOT NULL,
        website TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        social TEXT DEFAULT '',
        notes TEXT DEFAULT '',
        competitor_type TEXT DEFAULT 'Trực tiếp',
        price_segment TEXT DEFAULT '',
        core_products TEXT DEFAULT '',
        key_strengths TEXT DEFAULT '',
        vulnerabilities TEXT DEFAULT '',
        battlecard_content TEXT DEFAULT '',
        is_manual INTEGER DEFAULT 0,
        market_context TEXT DEFAULT '',
        scanned_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 11. Bảng lưu trữ Khách hàng tiềm năng & Phễu Mini CRM (Lead Records)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS lead_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL DEFAULT 'default@marketing-os.local',
        full_name TEXT NOT NULL,
        phone TEXT DEFAULT '',
        email TEXT DEFAULT '',
        source TEXT DEFAULT 'Website / Form',
        channel TEXT DEFAULT 'Direct',
        product_interest TEXT DEFAULT '',
        status TEXT DEFAULT 'new', -- 'new', 'consulting', 'won', 'lost'
        deal_value REAL DEFAULT 0,
        notes TEXT DEFAULT '',
        utm_source TEXT DEFAULT '',
        utm_campaign TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_leads_user ON lead_records(user_email);")

    # Nâng cấp các cột nếu DB đã tồn tại
    cols = [
        ("app_users", "login_count", "INTEGER DEFAULT 1"),
        ("app_users", "ip_address", "TEXT DEFAULT ''"),
        ("app_users", "user_agent", "TEXT DEFAULT ''"),
        ("research_records", "user_email", "TEXT DEFAULT 'default@marketing-os.local'"),
        ("content_items", "user_email", "TEXT DEFAULT 'default@marketing-os.local'"),
        ("content_items", "published_webhook", "INTEGER DEFAULT 0"),
        ("content_items", "webhook_published_at", "TIMESTAMP"),
        ("performance_metrics", "user_email", "TEXT DEFAULT 'default@marketing-os.local'"),
        ("calendar_schedules", "user_email", "TEXT DEFAULT 'default@marketing-os.local'"),
        ("automation_logs", "user_email", "TEXT DEFAULT 'default@marketing-os.local'"),
        ("discovered_competitors", "user_email", "TEXT DEFAULT 'default@marketing-os.local'"),
        ("lead_records", "user_email", "TEXT DEFAULT 'default@marketing-os.local'"),
    ]
    for table, col, def_val in cols:
        try:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {def_val}")
        except Exception:
            pass

    conn.commit()
    conn.close()

# --- Auth Management & User Tracking ---
def create_or_update_user(email: str, name: str = "", picture: str = "", ip: str = "", user_agent: str = "") -> dict:
    init_app_db()
    email_norm = normalize_email(email)
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT email, login_count FROM app_users WHERE LOWER(email) = ?", (email_norm,))
    existing = cur.fetchone()
    
    if existing:
        new_count = (existing["login_count"] or 1) + 1
        cur.execute("""
        UPDATE app_users SET
            name = CASE WHEN ? != '' THEN ? ELSE name END,
            picture = CASE WHEN ? != '' THEN ? ELSE picture END,
            login_count = ?,
            ip_address = CASE WHEN ? != '' THEN ? ELSE ip_address END,
            user_agent = CASE WHEN ? != '' THEN ? ELSE user_agent END,
            last_login = CURRENT_TIMESTAMP
        WHERE LOWER(email) = ?
        """, (name, name, picture, picture, new_count, ip, ip, user_agent, user_agent, email_norm))
    else:
        new_count = 1
        cur.execute("""
        INSERT INTO app_users (email, name, picture, login_count, ip_address, user_agent, last_login)
        VALUES (?, ?, ?, 1, ?, ?, CURRENT_TIMESTAMP)
        """, (email_norm, name or email_norm.split("@")[0], picture, ip, user_agent))
        
    conn.commit()
    
    cur.execute("SELECT * FROM app_users WHERE LOWER(email) = ?", (email_norm,))
    user = dict(cur.fetchone())
    conn.close()
    
    # Đảm bảo profile riêng cho user này luôn được khởi tạo
    get_profile(email_norm)
    return user

def create_session(email: str) -> str:
    init_app_db()
    email_norm = normalize_email(email)
    conn = get_connection()
    cur = conn.cursor()
    token = str(uuid.uuid4())
    cur.execute("INSERT INTO app_sessions (token, email) VALUES (?, ?)", (token, email_norm))
    conn.commit()
    conn.close()
    return token

def verify_session(token: str) -> Optional[dict]:
    if not token:
        return None
    init_app_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT u.email, u.name, u.picture, u.login_count, u.last_login
    FROM app_sessions s
    JOIN app_users u ON LOWER(s.email) = LOWER(u.email)
    WHERE s.token = ?
    """, (token,))
    row = cur.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def delete_session(token: str):
    init_app_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM app_sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()

def get_all_users() -> List[dict]:
    init_app_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT 
        u.email, u.name, u.picture, u.login_count, u.ip_address, u.user_agent,
        u.created_at, u.last_login,
        p.brand_name, p.industry, p.updated_at as profile_updated_at
    FROM app_users u
    LEFT JOIN user_profiles p ON LOWER(u.email) = LOWER(p.user_email)
    ORDER BY u.last_login DESC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def export_users_csv() -> str:
    """Xuất danh sách tài khoản theo định dạng CSV UTF-8 BOM để mở trực tiếp trong Google Sheets / Excel"""
    users = get_all_users()
    output = io.StringIO()
    # UTF-8 BOM
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow([
        "Email (Gmail)", "Họ Tên", "Số Lượt Đăng Nhập", "Địa Chỉ IP",
        "Trình Duyệt / Thiết Bị", "Thương Hiệu Cấu Hình", "Ngành Nghề",
        "Ngày Đăng Ký Lần Đầu", "Lần Đăng Nhập Gần Nhất"
    ])
    for u in users:
        writer.writerow([
            u.get("email", ""),
            u.get("name", ""),
            u.get("login_count", 1),
            u.get("ip_address", ""),
            u.get("user_agent", ""),
            u.get("brand_name", "") or "Chưa tạo",
            u.get("industry", "") or "Chưa tạo",
            u.get("created_at", ""),
            u.get("last_login", "")
        ])
    return output.getvalue()

# --- Config Management (Google Sheet Webhook URL) ---
def get_app_config(key: str, default: str = "") -> str:
    init_app_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT value FROM app_configs WHERE key = ?", (key,))
    row = cur.fetchone()
    conn.close()
    if row and row["value"]:
        return row["value"]
    return os.getenv(key, default)

def set_app_config(key: str, value: str):
    init_app_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO app_configs (key, value) VALUES (?, ?)
    ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (key, value))
    conn.commit()
    conn.close()

# --- Multi-Tenant Profile Management ---
def get_profile(user_email: str = "default@marketing-os.local") -> dict:
    init_app_db()
    email_norm = normalize_email(user_email)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_profiles WHERE LOWER(user_email) = ?", (email_norm,))
    row = cur.fetchone()
    if not row:
        cur.execute("""
        INSERT INTO user_profiles (
            user_email, brand_name, industry, business_model, products_services, price_range,
            target_audience, competitors, channels, monthly_budget, brand_voice, gemini_model,
            market_scope_type, market_location, region, content_direction
        ) VALUES (
            ?, '', '', 'B2C / B2B', '', '',
            '', '',
            'Facebook, TikTok, Google, YouTube, Website', 0,
            'Chuyên nghiệp, Uy tín', 'gemini-2.5-flash',
            'province', 'Toàn quốc', 'Toàn quốc', 'educational'
        )
        """, (email_norm,))
        conn.commit()
        cur.execute("SELECT * FROM user_profiles WHERE LOWER(user_email) = ?", (email_norm,))
        row = cur.fetchone()
        
    conn.close()
    return dict(row) if row else {}

def update_profile(data: dict, user_email: str = "default@marketing-os.local") -> dict:
    init_app_db()
    email_norm = normalize_email(user_email)
    conn = get_connection()
    cur = conn.cursor()
    
    # Ensure profile row exists
    get_profile(email_norm)
    
    cur.execute("""
    UPDATE user_profiles SET
        brand_name = ?,
        industry = ?,
        business_model = ?,
        products_services = ?,
        price_range = ?,
        target_audience = ?,
        competitors = ?,
        channels = ?,
        monthly_budget = ?,
        brand_voice = ?,
        gemini_api_key = ?,
        gemini_model = ?,
        market_scope_type = ?,
        market_location = ?,
        region = ?,
        content_direction = ?,
        phone_hotline = ?,
        website_url = ?,
        social_channels = ?,
        usp_advantages = ?,
        updated_at = CURRENT_TIMESTAMP
    WHERE LOWER(user_email) = ?
    """, (
        data.get("brand_name", ""),
        data.get("industry", ""),
        data.get("business_model", ""),
        data.get("products_services", ""),
        data.get("price_range", ""),
        data.get("target_audience", ""),
        data.get("competitors", ""),
        data.get("channels", ""),
        float(data.get("monthly_budget", 0) or 0),
        data.get("brand_voice", ""),
        data.get("gemini_api_key", ""),
        data.get("gemini_model", "gemini-2.5-flash"),
        data.get("market_scope_type", "province"),
        data.get("market_location", data.get("region", "Toàn quốc")),
        data.get("market_location", data.get("region", "Toàn quốc")),
        data.get("content_direction", "educational"),
        data.get("phone_hotline", ""),
        data.get("website_url") or data.get("website", ""),
        data.get("social_channels", ""),
        data.get("usp_advantages") or data.get("product_advantages", ""),
        email_norm
    ))
    conn.commit()
    conn.close()
    return get_profile(email_norm)

# --- Multi-Tenant Research Records ---
def save_research_record(category: str, title: str, content: str, metadata: dict = None, user_email: str = "default@marketing-os.local"):
    init_app_db()
    email_norm = normalize_email(user_email)
    conn = get_connection()
    cur = conn.cursor()
    meta_json = json.dumps(metadata or {}, ensure_ascii=False)
    cur.execute("""
    INSERT INTO research_records (user_email, category, title, content, metadata_json)
    VALUES (?, ?, ?, ?, ?)
    """, (email_norm, category, title, content, meta_json))
    conn.commit()
    conn.close()

def get_latest_research(user_email: str = "default@marketing-os.local") -> dict:
    init_app_db()
    email_norm = normalize_email(user_email)
    conn = get_connection()
    cur = conn.cursor()
    results = {}
    for cat in ["market_research", "battlecards", "personas"]:
        cur.execute("""
        SELECT * FROM research_records 
        WHERE category = ? AND LOWER(user_email) = ?
        ORDER BY id DESC LIMIT 1
        """, (cat, email_norm))
        row = cur.fetchone()
        results[cat] = dict(row) if row else None
    conn.close()
    return results

# --- Multi-Tenant Automation Logs ---
def log_automation(task_code: str, task_name: str, status: str, details: str, user_email: str = "default@marketing-os.local"):
    init_app_db()
    email_norm = normalize_email(user_email)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO automation_logs (user_email, task_code, task_name, status, details)
    VALUES (?, ?, ?, ?, ?)
    """, (email_norm, task_code, task_name, status, details))
    conn.commit()
    conn.close()

def get_automation_logs(limit: int = 30, user_email: str = "default@marketing-os.local") -> list:
    init_app_db()
    email_norm = normalize_email(user_email)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT * FROM automation_logs 
    WHERE LOWER(user_email) = ?
    ORDER BY id DESC LIMIT ?
    """, (email_norm, limit))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# --- Multi-Tenant Calendar Schedules ---
def save_calendar_items(items: list, user_email: str = "default@marketing-os.local"):
    init_app_db()
    email_norm = normalize_email(user_email)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM calendar_schedules WHERE LOWER(user_email) = ?", (email_norm,))
    for it in items:
        cur.execute("""
        INSERT INTO calendar_schedules (user_email, day_number, channel, pillar, funnel_stage, topic, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            email_norm,
            it.get("day", 1),
            it.get("channel", "Facebook"),
            it.get("pillar", "Help"),
            it.get("funnel_stage", "TOFU"),
            it.get("topic", ""),
            it.get("status", "scheduled")
        ))
    conn.commit()
    conn.close()

def get_calendar_items(user_email: str = "default@marketing-os.local") -> list:
    init_app_db()
    email_norm = normalize_email(user_email)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM calendar_schedules WHERE LOWER(user_email) = ? ORDER BY day_number ASC", (email_norm,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# --- Multi-Tenant Competitors Management ---
def add_or_update_competitor(comp: dict, user_email: str = "default@marketing-os.local") -> int:
    init_app_db()
    email_norm = normalize_email(user_email)
    conn = get_connection()
    cur = conn.cursor()
    comp_id = comp.get("id")
    name = comp.get("name", "").strip()
    website = comp.get("website", "").strip()
    phone = comp.get("phone", "").strip()
    social = comp.get("social", "").strip()
    notes = comp.get("notes", "").strip()
    comp_type = comp.get("type") or comp.get("competitor_type", "Trực tiếp")
    price_seg = comp.get("price_segment", "")
    core_prod = comp.get("core_products", "")
    strengths = comp.get("key_strengths", "")
    vulns = comp.get("vulnerabilities", "")
    battlecard = comp.get("battlecard_content", "")
    is_manual = comp.get("is_manual", 1)
    market_ctx = comp.get("market_context", "")

    if comp_id:
        cur.execute("""
        UPDATE discovered_competitors SET
            name = CASE WHEN ? != '' THEN ? ELSE name END,
            website = CASE WHEN ? != '' THEN ? ELSE website END,
            phone = CASE WHEN ? != '' THEN ? ELSE phone END,
            social = CASE WHEN ? != '' THEN ? ELSE social END,
            notes = CASE WHEN ? != '' THEN ? ELSE notes END,
            competitor_type = CASE WHEN ? != '' THEN ? ELSE competitor_type END,
            price_segment = CASE WHEN ? != '' THEN ? ELSE price_segment END,
            core_products = CASE WHEN ? != '' THEN ? ELSE core_products END,
            key_strengths = CASE WHEN ? != '' THEN ? ELSE key_strengths END,
            vulnerabilities = CASE WHEN ? != '' THEN ? ELSE vulnerabilities END,
            battlecard_content = CASE WHEN ? != '' THEN ? ELSE battlecard_content END,
            is_manual = ?,
            market_context = CASE WHEN ? != '' THEN ? ELSE market_context END
        WHERE id = ? AND LOWER(user_email) = ?
        """, (
            name, name, website, website, phone, phone, social, social, notes, notes,
            comp_type, comp_type, price_seg, price_seg, core_prod, core_prod,
            strengths, strengths, vulns, vulns, battlecard, battlecard,
            is_manual, market_ctx, market_ctx, comp_id, email_norm
        ))
    else:
        cur.execute("SELECT id FROM discovered_competitors WHERE LOWER(name) = LOWER(?) AND LOWER(user_email) = ?", (name, email_norm))
        row = cur.fetchone()
        if row:
            comp_id = row[0]
            cur.execute("""
            UPDATE discovered_competitors SET
                website = CASE WHEN ? != '' THEN ? ELSE website END,
                phone = CASE WHEN ? != '' THEN ? ELSE phone END,
                social = CASE WHEN ? != '' THEN ? ELSE social END,
                notes = CASE WHEN ? != '' THEN ? ELSE notes END,
                competitor_type = ?,
                price_segment = CASE WHEN ? != '' THEN ? ELSE price_segment END,
                core_products = CASE WHEN ? != '' THEN ? ELSE core_products END,
                key_strengths = CASE WHEN ? != '' THEN ? ELSE key_strengths END,
                vulnerabilities = CASE WHEN ? != '' THEN ? ELSE vulnerabilities END,
                battlecard_content = CASE WHEN ? != '' THEN ? ELSE battlecard_content END,
                is_manual = ?,
                market_context = CASE WHEN ? != '' THEN ? ELSE market_context END
            WHERE id = ? AND LOWER(user_email) = ?
            """, (website, website, phone, phone, social, social, notes, notes, comp_type, price_seg, price_seg, core_prod, core_prod, strengths, strengths, vulns, vulns, battlecard, battlecard, is_manual, market_ctx, market_ctx, comp_id, email_norm))
        else:
            cur.execute("""
            INSERT INTO discovered_competitors (
                user_email, name, website, phone, social, notes, competitor_type,
                price_segment, core_products, key_strengths, vulnerabilities,
                battlecard_content, is_manual, market_context
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (email_norm, name, website, phone, social, notes, comp_type, price_seg, core_prod, strengths, vulns, battlecard, is_manual, market_ctx))
            comp_id = cur.lastrowid

    # Auto sync profile competitors list for this user
    cur.execute("SELECT name FROM discovered_competitors WHERE LOWER(user_email) = ? ORDER BY id ASC", (email_norm,))
    all_names = [r[0] for r in cur.fetchall() if r[0]]
    if all_names:
        cur.execute("UPDATE user_profiles SET competitors = ? WHERE LOWER(user_email) = ?", (", ".join(all_names), email_norm))

    conn.commit()
    conn.close()
    return comp_id

def delete_competitor(comp_id: int, user_email: str = "default@marketing-os.local"):
    init_app_db()
    email_norm = normalize_email(user_email)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM discovered_competitors WHERE id = ? AND LOWER(user_email) = ?", (comp_id, email_norm))
    cur.execute("SELECT name FROM discovered_competitors WHERE LOWER(user_email) = ? ORDER BY id ASC", (email_norm,))
    all_names = [r[0] for r in cur.fetchall() if r[0]]
    cur.execute("UPDATE user_profiles SET competitors = ? WHERE LOWER(user_email) = ?", (", ".join(all_names), email_norm))
    conn.commit()
    conn.close()

def save_competitor_battlecard(comp_id: int, battlecard_text: str, user_email: str = "default@marketing-os.local"):
    init_app_db()
    email_norm = normalize_email(user_email)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    UPDATE discovered_competitors 
    SET battlecard_content = ?, scanned_at = CURRENT_TIMESTAMP
    WHERE id = ? AND LOWER(user_email) = ?
    """, (battlecard_text, comp_id, email_norm))
    conn.commit()
    conn.close()

def get_competitor_by_id(comp_id: int, user_email: str = "default@marketing-os.local") -> Optional[dict]:
    init_app_db()
    email_norm = normalize_email(user_email)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM discovered_competitors WHERE id = ? AND LOWER(user_email) = ?", (comp_id, email_norm))
    row = cur.fetchone()
    if not row:
        cur.execute("SELECT * FROM discovered_competitors WHERE id = ?", (comp_id,))
        row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def save_discovered_competitors(items: list, market_context: str = "", user_email: str = "default@marketing-os.local"):
    init_app_db()
    email_norm = normalize_email(user_email)
    conn = get_connection()
    cur = conn.cursor()
    # Chỉ xóa những đối thủ auto-discovered cũ của user này, GIỮ NGUYÊN các đối thủ do user tự nhập (is_manual = 1)
    cur.execute("DELETE FROM discovered_competitors WHERE is_manual = 0 AND LOWER(user_email) = ?", (email_norm,))
    for it in items:
        name = it.get("name", "").strip()
        if not name:
            continue
        cur.execute("SELECT id FROM discovered_competitors WHERE LOWER(name) = LOWER(?) AND LOWER(user_email) = ?", (name, email_norm))
        row = cur.fetchone()
        if row:
            cur.execute("""
            UPDATE discovered_competitors SET
                website = CASE WHEN (website IS NULL OR website = '') THEN ? ELSE website END,
                phone = CASE WHEN (phone IS NULL OR phone = '') THEN ? ELSE phone END,
                social = CASE WHEN (social IS NULL OR social = '') THEN ? ELSE social END,
                competitor_type = CASE WHEN (competitor_type IS NULL OR competitor_type = '') THEN ? ELSE competitor_type END,
                price_segment = CASE WHEN (price_segment IS NULL OR price_segment = '') THEN ? ELSE price_segment END,
                core_products = CASE WHEN (core_products IS NULL OR core_products = '') THEN ? ELSE core_products END,
                key_strengths = CASE WHEN (key_strengths IS NULL OR key_strengths = '') THEN ? ELSE key_strengths END,
                vulnerabilities = CASE WHEN (vulnerabilities IS NULL OR vulnerabilities = '') THEN ? ELSE vulnerabilities END,
                market_context = ?
            WHERE id = ?
            """, (
                it.get("website", ""),
                it.get("phone", ""),
                it.get("social", ""),
                it.get("type") or it.get("competitor_type", "Trực tiếp"),
                it.get("price_segment", ""),
                it.get("core_products", ""),
                it.get("key_strengths", ""),
                it.get("vulnerabilities", ""),
                market_context,
                row[0]
            ))
        else:
            cur.execute("""
            INSERT INTO discovered_competitors (
                user_email, name, website, phone, social, notes, competitor_type,
                price_segment, core_products, key_strengths, vulnerabilities,
                is_manual, market_context
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
            """, (
                email_norm,
                name,
                it.get("website", ""),
                it.get("phone", ""),
                it.get("social", ""),
                it.get("notes", ""),
                it.get("type") or it.get("competitor_type", "Trực tiếp"),
                it.get("price_segment", ""),
                it.get("core_products", ""),
                it.get("key_strengths", ""),
                it.get("vulnerabilities", ""),
                market_context
            ))

    # Auto sync profile competitors list with all competitors
    cur.execute("SELECT name FROM discovered_competitors WHERE LOWER(user_email) = ? ORDER BY id ASC", (email_norm,))
    all_names = [r[0] for r in cur.fetchall() if r[0]]
    if all_names:
        cur.execute("UPDATE user_profiles SET competitors = ? WHERE LOWER(user_email) = ?", (", ".join(all_names), email_norm))

    conn.commit()
    conn.close()

def clear_all_competitors(user_email: str = "default@marketing-os.local"):
    init_app_db()
    email_norm = normalize_email(user_email)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM discovered_competitors WHERE LOWER(user_email) = ?", (email_norm,))
    cur.execute("UPDATE user_profiles SET competitors = '' WHERE LOWER(user_email) = ?", (email_norm,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Đã xóa toàn bộ đối thủ trong danh sách."}

def get_discovered_competitors(user_email: str = "default@marketing-os.local") -> list:
    init_app_db()
    email_norm = normalize_email(user_email)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM discovered_competitors WHERE LOWER(user_email) = ? ORDER BY is_manual DESC, id ASC", (email_norm,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# --- Multi-Tenant Content Items ---
def save_content_package(channel: str, topic: str, body: str, cta: str, video_script: str = "", image_prompt: str = "", status: str = "ready", user_email: str = "default@marketing-os.local") -> int:
    init_app_db()
    email_norm = normalize_email(user_email)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO content_items (user_email, channel, topic, body, cta, video_script, image_prompt, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (email_norm, channel, topic, body, cta, video_script, image_prompt, status))
    conn.commit()
    item_id = cur.lastrowid
    conn.close()
    return item_id

def get_content_items(user_email: str = "default@marketing-os.local") -> list:
    init_app_db()
    email_norm = normalize_email(user_email)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM content_items WHERE LOWER(user_email) = ? ORDER BY id DESC LIMIT 100", (email_norm,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def update_content_item_status(item_id: int, new_status: str, user_email: str = "default@marketing-os.local") -> bool:
    init_app_db()
    email_norm = normalize_email(user_email)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    UPDATE content_items
    SET status = ?
    WHERE id = ? AND LOWER(user_email) = ?
    """, (new_status, item_id, email_norm))
    updated = cur.rowcount > 0
    conn.commit()
    conn.close()
    return updated

def delete_content_item(item_id: int, user_email: str = "default@marketing-os.local") -> bool:
    init_app_db()
    email_norm = normalize_email(user_email)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM content_items WHERE id = ? AND LOWER(user_email) = ?", (item_id, email_norm))
    deleted = cur.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def mark_content_webhook_published(item_id: int, user_email: str = "default@marketing-os.local") -> bool:
    init_app_db()
    email_norm = normalize_email(user_email)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    UPDATE content_items
    SET status = 'published', published_webhook = 1, webhook_published_at = CURRENT_TIMESTAMP
    WHERE id = ? AND LOWER(user_email) = ?
    """, (item_id, email_norm))
    updated = cur.rowcount > 0
    conn.commit()
    conn.close()
    return updated

# --- Multi-Tenant Lead Records & Mini CRM ---
def create_lead(lead_data: dict, user_email: str = "default@marketing-os.local") -> dict:
    init_app_db()
    email_norm = normalize_email(user_email)
    conn = get_connection()
    cur = conn.cursor()
    full_name = (lead_data.get("full_name") or "").strip() or "Khách hàng mới"
    phone = (lead_data.get("phone") or "").strip()
    email = (lead_data.get("email") or "").strip()
    source = (lead_data.get("source") or "Website / Form").strip()
    channel = (lead_data.get("channel") or "Direct").strip()
    product_interest = (lead_data.get("product_interest") or "").strip()
    status = (lead_data.get("status") or "new").strip().lower()
    if status not in ["new", "consulting", "won", "lost"]:
        status = "new"
    try:
        deal_value = float(lead_data.get("deal_value") or 0)
    except (ValueError, TypeError):
        deal_value = 0.0
    notes = (lead_data.get("notes") or "").strip()
    utm_source = (lead_data.get("utm_source") or "").strip()
    utm_campaign = (lead_data.get("utm_campaign") or "").strip()

    cur.execute("""
    INSERT INTO lead_records (
        user_email, full_name, phone, email, source, channel,
        product_interest, status, deal_value, notes, utm_source, utm_campaign
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        email_norm, full_name, phone, email, source, channel,
        product_interest, status, deal_value, notes, utm_source, utm_campaign
    ))
    conn.commit()
    lead_id = cur.lastrowid
    
    cur.execute("SELECT * FROM lead_records WHERE id = ?", (lead_id,))
    row = dict(cur.fetchone())
    conn.close()
    return row

def get_leads(user_email: str = "default@marketing-os.local", status: str = None, search: str = "") -> list:
    init_app_db()
    email_norm = normalize_email(user_email)
    conn = get_connection()
    cur = conn.cursor()
    
    query = "SELECT * FROM lead_records WHERE LOWER(user_email) = ?"
    params = [email_norm]
    
    if status and status.strip() and status != "all":
        query += " AND status = ?"
        params.append(status.strip().lower())
        
    if search and search.strip():
        term = f"%{search.strip().lower()}%"
        query += " AND (LOWER(full_name) LIKE ? OR LOWER(phone) LIKE ? OR LOWER(email) LIKE ? OR LOWER(product_interest) LIKE ?)"
        params.extend([term, term, term, term])
        
    query += " ORDER BY id DESC"
    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def update_lead_status(lead_id: int, status: str, user_email: str = "default@marketing-os.local") -> bool:
    init_app_db()
    email_norm = normalize_email(user_email)
    st = status.strip().lower()
    if st not in ["new", "consulting", "won", "lost"]:
        return False
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    UPDATE lead_records
    SET status = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ? AND LOWER(user_email) = ?
    """, (st, lead_id, email_norm))
    updated = cur.rowcount > 0
    conn.commit()
    conn.close()
    return updated

def update_lead(lead_id: int, lead_data: dict, user_email: str = "default@marketing-os.local") -> bool:
    init_app_db()
    email_norm = normalize_email(user_email)
    conn = get_connection()
    cur = conn.cursor()
    
    fields = []
    values = []
    for k in ["full_name", "phone", "email", "source", "channel", "product_interest", "status", "deal_value", "notes", "utm_source", "utm_campaign"]:
        if k in lead_data:
            fields.append(f"{k} = ?")
            values.append(lead_data[k])
            
    if not fields:
        conn.close()
        return False
        
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.extend([lead_id, email_norm])
    sql = f"UPDATE lead_records SET {', '.join(fields)} WHERE id = ? AND LOWER(user_email) = ?"
    cur.execute(sql, values)
    updated = cur.rowcount > 0
    conn.commit()
    conn.close()
    return updated

def delete_lead(lead_id: int, user_email: str = "default@marketing-os.local") -> bool:
    init_app_db()
    email_norm = normalize_email(user_email)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM lead_records WHERE id = ? AND LOWER(user_email) = ?", (lead_id, email_norm))
    deleted = cur.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def get_lead_stats(user_email: str = "default@marketing-os.local") -> dict:
    init_app_db()
    email_norm = normalize_email(user_email)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT 
        COUNT(*) as total_leads,
        SUM(CASE WHEN status = 'new' THEN 1 ELSE 0 END) as new_count,
        SUM(CASE WHEN status = 'consulting' THEN 1 ELSE 0 END) as consulting_count,
        SUM(CASE WHEN status = 'won' THEN 1 ELSE 0 END) as won_count,
        SUM(CASE WHEN status = 'lost' THEN 1 ELSE 0 END) as lost_count,
        SUM(CASE WHEN status = 'won' THEN deal_value ELSE 0 END) as total_won_value,
        SUM(deal_value) as total_pipeline_value
    FROM lead_records
    WHERE LOWER(user_email) = ?
    """, (email_norm,))
    row = dict(cur.fetchone() or {})
    conn.close()
    
    total = row.get("total_leads") or 0
    won = row.get("won_count") or 0
    win_rate = round((won / total * 100), 1) if total > 0 else 0.0
    
    return {
        "total_leads": total,
        "new_count": row.get("new_count") or 0,
        "consulting_count": row.get("consulting_count") or 0,
        "won_count": won,
        "lost_count": row.get("lost_count") or 0,
        "win_rate": win_rate,
        "total_won_value": round(row.get("total_won_value") or 0, 0),
        "total_pipeline_value": round(row.get("total_pipeline_value") or 0, 0)
    }

# --- Multi-Tenant Analytics ---
def get_analytics_summary(user_email: str = "default@marketing-os.local") -> dict:
    init_app_db()
    email_norm = normalize_email(user_email)
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
    WHERE LOWER(user_email) = ?
    """, (email_norm,))
    totals = dict(cur.fetchone())

    spend = totals["total_spend"]
    rev = totals["total_rev"]
    orders = totals["total_orders"]
    leads = totals["total_leads"]

    mer = (rev / spend) if spend > 0 else 0.0
    roas = mer
    cac = (spend / orders) if orders > 0 else 0.0
    cpl = (spend / leads) if leads > 0 else 0.0

    cur.execute("""
    SELECT date, ad_spend, revenue, orders_count, leads_count 
    FROM performance_metrics 
    WHERE LOWER(user_email) = ?
    ORDER BY date DESC LIMIT 14
    """, (email_norm,))
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

def record_performance_metric(metric_data: dict, user_email: str = "default@marketing-os.local"):
    init_app_db()
    email_norm = normalize_email(user_email)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO performance_metrics (user_email, date, ad_spend, revenue, orders_count, leads_count, impressions, clicks, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        email_norm,
        metric_data.get("date", ""),
        metric_data.get("ad_spend", 0),
        metric_data.get("revenue", 0),
        metric_data.get("orders_count", 0),
        metric_data.get("leads_count", 0),
        metric_data.get("impressions", 0),
        metric_data.get("clicks", 0),
        metric_data.get("notes", "")
    ))
    conn.commit()
    conn.close()

# --- Multi-Tenant Reset Clean Slate ---
def reset_database_clean(user_email: str = "default@marketing-os.local"):
    """Xóa sạch toàn bộ dữ liệu của người dùng hiện tại và đưa workspace về trạng thái tinh khôi ban đầu"""
    init_app_db()
    email_norm = normalize_email(user_email)
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("DELETE FROM research_records WHERE LOWER(user_email) = ?", (email_norm,))
    cur.execute("DELETE FROM content_items WHERE LOWER(user_email) = ?", (email_norm,))
    cur.execute("DELETE FROM calendar_schedules WHERE LOWER(user_email) = ?", (email_norm,))
    cur.execute("DELETE FROM automation_logs WHERE LOWER(user_email) = ?", (email_norm,))
    cur.execute("DELETE FROM discovered_competitors WHERE LOWER(user_email) = ?", (email_norm,))
    cur.execute("DELETE FROM performance_metrics WHERE LOWER(user_email) = ?", (email_norm,))
    cur.execute("DELETE FROM lead_records WHERE LOWER(user_email) = ?", (email_norm,))
    
    cur.execute("""
    UPDATE user_profiles SET
        brand_name = '',
        industry = '',
        business_model = 'B2C / B2B',
        products_services = '',
        price_range = '',
        target_audience = '',
        competitors = '',
        channels = 'Facebook, TikTok, Google, YouTube, Website',
        monthly_budget = 0,
        brand_voice = 'Chuyên nghiệp, Uy tín',
        market_scope_type = 'province',
        market_location = 'Toàn quốc',
        region = 'Toàn quốc',
        content_direction = 'educational',
        phone_hotline = '',
        website_url = '',
        social_channels = '',
        usp_advantages = '',
        updated_at = CURRENT_TIMESTAMP
    WHERE LOWER(user_email) = ?
    """, (email_norm,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": f"Đã xóa sạch dữ liệu và đưa không gian làm việc của {email_norm} về trạng thái mới tinh hoàn toàn!"}

if __name__ == "__main__":
    init_app_db()
    print("Database multi-tenant schema ready.")
