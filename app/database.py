# -*- coding: utf-8 -*-
"""
Database layer for Marketing Automation App
SQLite database: marketing_os_app.db
- Business Profile
- Research Records (Market, Competitors, Personas)
- Content Items
- Calendar Schedules
- Automation Logs (Real-time Auto-Pilot Feed)
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "marketing_os_app.db"

def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_app_db():
    conn = get_connection()
    cur = conn.cursor()
    
    # 1. Bảng lưu trữ hồ sơ doanh nghiệp
    cur.execute("""
    CREATE TABLE IF NOT EXISTS business_profile (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        brand_name TEXT NOT NULL,
        industry TEXT NOT NULL,
        business_model TEXT NOT NULL,
        products_services TEXT NOT NULL,
        price_range TEXT,
        target_audience TEXT NOT NULL,
        competitors TEXT,
        channels TEXT,
        monthly_budget REAL DEFAULT 0,
        brand_voice TEXT,
        gemini_api_key TEXT,
        gemini_model TEXT DEFAULT 'gemini-1.5-flash',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Bảng lưu trữ kết quả nghiên cứu thị trường & chiến lược
    cur.execute("""
    CREATE TABLE IF NOT EXISTS research_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL, -- 'market_research', 'personas', 'battlecards', 'strategy'
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        metadata_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3. Bảng lưu trữ nội dung đã tạo (Content Studio & Calendar)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS content_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel TEXT NOT NULL, -- 'tiktok', 'facebook', 'seo_blog', 'email', 'ads'
        topic TEXT NOT NULL,
        pillar TEXT,
        funnel_stage TEXT,
        hook TEXT,
        body TEXT NOT NULL,
        cta TEXT,
        status TEXT DEFAULT 'draft', -- 'draft', 'approved', 'scheduled', 'published'
        publish_date TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 4. Bảng ghi nhận chỉ số & đơn hàng thực tế
    cur.execute("""
    CREATE TABLE IF NOT EXISTS performance_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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

    # 5. Bảng lưu trữ Lịch biên tập 30 Ngày (Calendar Schedules)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS calendar_schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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

    # 6. Bảng lưu trữ Nhật ký Vận Hành Tự Động (Auto-Pilot Execution Logs)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS automation_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_code TEXT NOT NULL,
        task_name TEXT NOT NULL,
        status TEXT NOT NULL, -- 'SUCCESS', 'RUNNING', 'FAILED'
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 7. Bảng lưu trữ Đối thủ cạnh tranh được AI rà quét (Discovered Competitors)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS discovered_competitors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        website TEXT,
        competitor_type TEXT DEFAULT 'Trực tiếp',
        price_segment TEXT,
        core_products TEXT,
        key_strengths TEXT,
        vulnerabilities TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Tự động nâng cấp cột mới nếu DB đã tồn tại
    try:
        cur.execute("ALTER TABLE business_profile ADD COLUMN region TEXT DEFAULT 'Toàn quốc'")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE business_profile ADD COLUMN content_direction TEXT DEFAULT 'educational'")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE content_items ADD COLUMN video_script TEXT")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE content_items ADD COLUMN image_prompt TEXT")
    except Exception:
        pass

    # Insert default initial profile if empty
    cur.execute("SELECT COUNT(*) FROM business_profile WHERE id = 1")
    if cur.fetchone()[0] == 0:
        cur.execute("""
        INSERT INTO business_profile (
            id, brand_name, industry, business_model, products_services, price_range,
            target_audience, competitors, channels, monthly_budget, brand_voice, gemini_model
        ) VALUES (
            1,
            'CÔNG TY CỔ PHẦN CHẾ TẠO MÁY TMT',
            'SẢN XUẤT MÁY MÓC',
            'B2B / Nhà thầu',
            'MÁY UỐN THÉP XÂY DỰNG',
            '100TR',
            'NGƯỜI LÀM TRONG NGÀNH XÂY DỰNG, NHÀ THẦU, ĐỘI CAI THẦU',
            'https://cokhitudongchiho.com/ , http://www.maybedaihoangminh.com/ , https://mayxaydungtudong.com/ , https://maybedaiphuclong.com/',
            'Facebook, YOUTUBE, WEBSITE',
            40000000,
            'Thực chiến, Cơ khí, Uy tín',
            'gemini-2.0-flash'
        );
        """)

    conn.commit()
    conn.close()

def get_profile():
    init_app_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM business_profile WHERE id = 1")
    row = cur.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {}

def update_profile(data: dict):
    init_app_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    UPDATE business_profile SET
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
        updated_at = CURRENT_TIMESTAMP
    WHERE id = 1
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
        data.get("gemini_model", "gemini-1.5-flash")
    ))
    conn.commit()
    conn.close()
    return get_profile()

def save_research_record(category: str, title: str, content: str, metadata: dict = None):
    init_app_db()
    conn = get_connection()
    cur = conn.cursor()
    meta_json = json.dumps(metadata or {}, ensure_ascii=False)
    cur.execute("""
    INSERT INTO research_records (category, title, content, metadata_json)
    VALUES (?, ?, ?, ?)
    """, (category, title, content, meta_json))
    conn.commit()
    conn.close()

def get_latest_research():
    init_app_db()
    conn = get_connection()
    cur = conn.cursor()
    results = {}
    for cat in ["market_research", "battlecards", "personas"]:
        cur.execute("""
        SELECT * FROM research_records 
        WHERE category = ? 
        ORDER BY id DESC LIMIT 1
        """, (cat,))
        row = cur.fetchone()
        if row:
            results[cat] = dict(row)
        else:
            results[cat] = None
    conn.close()
    return results

def log_automation(task_code: str, task_name: str, status: str, details: str):
    init_app_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO automation_logs (task_code, task_name, status, details)
    VALUES (?, ?, ?, ?)
    """, (task_code, task_name, status, details))
    conn.commit()
    conn.close()

def get_automation_logs(limit: int = 30):
    init_app_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT * FROM automation_logs 
    ORDER BY id DESC LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def save_calendar_items(items: list):
    init_app_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM calendar_schedules")
    for it in items:
        cur.execute("""
        INSERT INTO calendar_schedules (day_number, channel, pillar, funnel_stage, topic, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            it.get("day", 1),
            it.get("channel", "Facebook"),
            it.get("pillar", "Help"),
            it.get("funnel_stage", "TOFU"),
            it.get("topic", ""),
            it.get("status", "scheduled")
        ))
    conn.commit()
    conn.close()

def get_calendar_items():
    init_app_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM calendar_schedules ORDER BY day_number ASC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def save_discovered_competitors(items: list):
    init_app_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM discovered_competitors")
    for it in items:
        cur.execute("""
        INSERT INTO discovered_competitors (name, website, competitor_type, price_segment, core_products, key_strengths, vulnerabilities)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            it.get("name", ""),
            it.get("website", ""),
            it.get("type") or it.get("competitor_type", "Trực tiếp"),
            it.get("price_segment", ""),
            it.get("core_products", ""),
            it.get("key_strengths", ""),
            it.get("vulnerabilities", "")
        ))
    conn.commit()
    conn.close()

def get_discovered_competitors() -> list:
    init_app_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM discovered_competitors ORDER BY id ASC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def save_content_package(channel: str, topic: str, body: str, cta: str, video_script: str = "", image_prompt: str = "", status: str = "ready") -> int:
    init_app_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO content_items (channel, topic, body, cta, video_script, image_prompt, status)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (channel, topic, body, cta, video_script, image_prompt, status))
    conn.commit()
    item_id = cur.lastrowid
    conn.close()
    return item_id

if __name__ == "__main__":
    init_app_db()
    print("Database initialized successfully.")
