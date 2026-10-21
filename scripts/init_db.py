# -*- coding: utf-8 -*-
"""
Hệ điều hành Marketing OS - scripts/init_db.py
Khởi tạo cơ sở dữ liệu SQLite data/marketing.db với đầy đủ cấu trúc bảng, chỉ mục (indexes) và ràng buộc.
"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "marketing.db"

TABLE_DEFINITIONS = [
    """
    CREATE TABLE IF NOT EXISTS ads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        platform TEXT NOT NULL,
        campaign TEXT NOT NULL,
        adset TEXT NOT NULL,
        impressions INTEGER DEFAULT 0,
        clicks INTEGER DEFAULT 0,
        spend REAL DEFAULT 0.0,
        conversions INTEGER DEFAULT 0,
        revenue REAL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(date, platform, campaign, adset)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS web (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        source TEXT NOT NULL,
        medium TEXT NOT NULL,
        sessions INTEGER DEFAULT 0,
        users INTEGER DEFAULT 0,
        new_users INTEGER DEFAULT 0,
        conversions INTEGER DEFAULT 0,
        revenue REAL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(date, source, medium)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS social (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        platform TEXT NOT NULL,
        post_id TEXT NOT NULL,
        post_type TEXT,
        reach INTEGER DEFAULT 0,
        impressions INTEGER DEFAULT 0,
        engagements INTEGER DEFAULT 0,
        followers INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(date, platform, post_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS email (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        campaign TEXT NOT NULL,
        sent INTEGER DEFAULT 0,
        delivered INTEGER DEFAULT 0,
        opens INTEGER DEFAULT 0,
        clicks INTEGER DEFAULT 0,
        unsubscribes INTEGER DEFAULT 0,
        conversions INTEGER DEFAULT 0,
        revenue REAL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(date, campaign)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS seo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        query TEXT NOT NULL,
        page TEXT NOT NULL,
        clicks INTEGER DEFAULT 0,
        impressions INTEGER DEFAULT 0,
        ctr REAL DEFAULT 0.0,
        position REAL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(date, query, page)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        order_id TEXT NOT NULL UNIQUE,
        customer_id TEXT NOT NULL,
        channel TEXT NOT NULL,
        product TEXT NOT NULL,
        quantity INTEGER DEFAULT 1,
        revenue REAL DEFAULT 0.0,
        is_new_customer INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        lead_id TEXT NOT NULL UNIQUE,
        source TEXT NOT NULL,
        campaign TEXT,
        stage TEXT NOT NULL,
        value REAL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS spend (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        category TEXT NOT NULL,
        vendor TEXT NOT NULL,
        amount REAL DEFAULT 0.0,
        campaign TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
]

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_ads_date ON ads(date);",
    "CREATE INDEX IF NOT EXISTS idx_ads_platform ON ads(platform);",
    "CREATE INDEX IF NOT EXISTS idx_web_date ON web(date);",
    "CREATE INDEX IF NOT EXISTS idx_social_date ON social(date);",
    "CREATE INDEX IF NOT EXISTS idx_email_date ON email(date);",
    "CREATE INDEX IF NOT EXISTS idx_seo_date ON seo(date);",
    "CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(date);",
    "CREATE INDEX IF NOT EXISTS idx_sales_cust ON sales(customer_id);",
    "CREATE INDEX IF NOT EXISTS idx_leads_date ON leads(date);",
    "CREATE INDEX IF NOT EXISTS idx_spend_date ON spend(date);"
]

def init_database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for table_sql in TABLE_DEFINITIONS:
        cursor.execute(table_sql)
    for idx_sql in INDEXES:
        cursor.execute(idx_sql)
    conn.commit()
    conn.close()
    print(f"[OK] Khoi tao thanh cong database tai: {DB_PATH}")

if __name__ == "__main__":
    init_database()
