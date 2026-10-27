# -*- coding: utf-8 -*-
"""
Tầng dữ liệu của Marketing OS — chạy được trên hai loại cơ sở dữ liệu:

- Postgres (khi có biến môi trường DATABASE_URL, ví dụ Neon/Supabase): dữ liệu nằm ngoài máy chủ web nên
  KHÔNG mất khi Render gói free ngủ, khởi động lại hay triển khai lại. Đây là cấu hình nên dùng trên cloud.
- SQLite (mặc định khi không có DATABASE_URL): một file tại DATA_DIR/marketing_os.db, hợp cho máy cá nhân
  hoặc máy chủ có ổ đĩa bền.

Mã nghiệp vụ chỉ dùng connect / rows / one / execute với dấu hỏi (?) làm tham số và SQL dùng được ở cả hai nơi;
lớp này tự đổi sang cú pháp Postgres. Mọi bảng nghiệp vụ đều có user_email để tách workspace của từng tài khoản.
"""
from __future__ import annotations

import datetime as _dt
import decimal
import json
import logging
import re
import shutil
import sqlite3
import threading
from contextlib import contextmanager
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence

from app import config

log = logging.getLogger("marketing_os.db")

_init_lock = threading.Lock()
_initialized_for: Optional[str] = None
_pool = None            # psycopg_pool.ConnectionPool khi dùng Postgres
_pool_url: str = ""


def normalize_email(email: Optional[str]) -> str:
    return str(email or "").strip().lower()


def using_postgres() -> bool:
    return bool(config.settings.database_url)


def backend_name() -> str:
    return "postgres" if using_postgres() else "sqlite"


# ---------------------------------------------------------------------------
# Postgres: đổi cú pháp và chuẩn hóa giá trị trả về cho giống SQLite
# ---------------------------------------------------------------------------

# Bảng có khóa tự tăng "id" — INSERT vào các bảng này trả về id mới (giống lastrowid của SQLite)
_SERIAL_TABLES = {
    "research_records", "content_items", "performance_metrics", "calendar_schedules", "automation_logs",
    "discovered_competitors", "lead_records", "context_versions", "skill_runs", "budget_lines", "utm_links",
    "experiments", "data_imports", "data_rows", "media_jobs", "humanize_history",
}
_INSERT_TABLE_RE = re.compile(r"^\s*INSERT\s+INTO\s+([A-Za-z_][A-Za-z0-9_]*)", re.I)


def _pg_sql(sql: str) -> str:
    """Đổi tham số ? sang %s (bỏ qua chuỗi trong nháy đơn) và nhân đôi % để psycopg không hiểu nhầm."""
    out: List[str] = []
    in_quote = False
    for ch in sql:
        if ch == "'":
            in_quote = not in_quote
            out.append(ch)
        elif ch == "%":
            out.append("%%")
        elif ch == "?" and not in_quote:
            out.append("%s")
        else:
            out.append(ch)
    return "".join(out)


def _pg_params(params: Iterable[Any]) -> tuple:
    # SQLite lưu True/False thành 1/0; cột cờ trong lược đồ là INTEGER nên đổi bool sang int cho Postgres
    return tuple(int(p) if isinstance(p, bool) else p for p in params)


def _pg_value(v: Any) -> Any:
    """Trả giá trị giống SQLite: thời điểm là chuỗi 'YYYY-MM-DD HH:MM:SS' (giờ UTC), số thập phân là int/float."""
    if isinstance(v, _dt.datetime):
        if v.tzinfo is not None:
            v = v.astimezone(_dt.timezone.utc).replace(tzinfo=None)
        return v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, _dt.date):
        return v.isoformat()
    if isinstance(v, decimal.Decimal):
        return int(v) if v == v.to_integral_value() else float(v)
    if isinstance(v, memoryview):
        return v.tobytes()
    return v


class _PgCursor:
    """Bọc con trỏ psycopg để có rowcount, lastrowid, fetchone/fetchall trả dict như sqlite3.Row."""

    def __init__(self, cur: Any, lastrowid: Optional[int] = None):
        self._cur = cur
        self.rowcount = cur.rowcount
        self.lastrowid = lastrowid

    def _norm(self, row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        return None if row is None else {k: _pg_value(v) for k, v in row.items()}

    def fetchone(self) -> Optional[Dict[str, Any]]:
        return self._norm(self._cur.fetchone())

    def fetchall(self) -> List[Dict[str, Any]]:
        return [self._norm(r) for r in self._cur.fetchall()]  # type: ignore[misc]


class _PgConnection:
    """Giao diện execute/executemany giống sqlite3.Connection trên một kết nối psycopg."""

    def __init__(self, conn: Any):
        self._conn = conn

    def execute(self, sql: str, params: Iterable[Any] = ()) -> _PgCursor:
        params = _pg_params(params)
        m = _INSERT_TABLE_RE.match(sql)
        wants_id = bool(m and m.group(1).lower() in _SERIAL_TABLES and "RETURNING" not in sql.upper())
        text = _pg_sql(sql) + (" RETURNING id" if wants_id else "")
        cur = self._conn.cursor()
        cur.execute(text, params)
        lastrowid = None
        if wants_id:
            row = cur.fetchone()
            lastrowid = row["id"] if row else None
        return _PgCursor(cur, lastrowid)

    def executemany(self, sql: str, seq: Sequence[Iterable[Any]]) -> None:
        cur = self._conn.cursor()
        cur.executemany(_pg_sql(sql), [_pg_params(p) for p in seq])

    def commit(self) -> None:
        self._conn.commit()

    def rollback(self) -> None:
        self._conn.rollback()


def _pg_pool():
    global _pool, _pool_url
    url = config.settings.database_url
    if _pool is not None and _pool_url == url:
        return _pool
    try:
        from psycopg.rows import dict_row
        from psycopg_pool import ConnectionPool
    except ImportError as exc:  # pragma: no cover - phụ thuộc môi trường
        raise RuntimeError("Đã đặt DATABASE_URL nhưng máy chủ thiếu thư viện psycopg / psycopg-pool "
                           "(chạy: pip install -r requirements.txt).") from exc
    if _pool is not None:
        _pool.close()
    # prepare_threshold=None: tắt prepared statement để chạy được qua bộ gom kết nối (PgBouncer/Neon pooler).
    # timezone=UTC: CURRENT_TIMESTAMP lưu giờ UTC giống SQLite; giao diện tự đổi sang giờ người xem.
    # max_idle < 5 phút: Neon gói free tự tắt máy sau 5 phút không dùng, kết nối cũ sẽ chết.
    _pool = ConnectionPool(
        url, min_size=1, max_size=config.settings.db_pool_size, open=True, timeout=30, max_idle=240,
        check=ConnectionPool.check_connection,
        kwargs={"row_factory": dict_row, "prepare_threshold": None, "options": "-c timezone=UTC",
                "connect_timeout": 15},
    )
    _pool_url = url
    return _pool


def _connect_sqlite() -> sqlite3.Connection:
    path = config.settings.db_path
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def connect() -> Iterator[Any]:
    """Một giao dịch: tự commit khi xong, rollback khi lỗi. Dùng conn.execute(sql, params) với tham số '?'."""
    ensure_db()
    if using_postgres():
        with _pg_pool().connection() as raw:
            conn = _PgConnection(raw)
            try:
                yield conn
                raw.commit()
            except Exception:
                raw.rollback()
                raise
        return
    conn = _connect_sqlite()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def rows(sql: str, params: Iterable[Any] = ()) -> List[Dict[str, Any]]:
    with connect() as conn:
        return [dict(r) for r in conn.execute(sql, tuple(params)).fetchall()]


def one(sql: str, params: Iterable[Any] = ()) -> Optional[Dict[str, Any]]:
    with connect() as conn:
        r = conn.execute(sql, tuple(params)).fetchone()
        return dict(r) if r else None


def execute(sql: str, params: Iterable[Any] = ()) -> int:
    """Chạy một câu lệnh ghi. Trả về id mới (INSERT vào bảng có id tự tăng) hoặc số dòng bị ảnh hưởng."""
    with connect() as conn:
        cur = conn.execute(sql, tuple(params))
        return cur.lastrowid if sql.lstrip().upper().startswith("INSERT") else cur.rowcount


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def loads(value: Optional[str], default: Any = None) -> Any:
    if value in (None, ""):
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# Migration
# ---------------------------------------------------------------------------

BASE_SCHEMA = [
    """CREATE TABLE IF NOT EXISTS app_users (
        email TEXT PRIMARY KEY,
        name TEXT,
        picture TEXT,
        login_count INTEGER DEFAULT 0,
        ip_address TEXT DEFAULT '',
        user_agent TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS app_configs (key TEXT PRIMARY KEY, value TEXT)""",
    """CREATE TABLE IF NOT EXISTS user_profiles (
        user_email TEXT PRIMARY KEY,
        brand_name TEXT NOT NULL DEFAULT '',
        industry TEXT NOT NULL DEFAULT '',
        business_model TEXT NOT NULL DEFAULT '',
        products_services TEXT NOT NULL DEFAULT '',
        price_range TEXT DEFAULT '',
        target_audience TEXT NOT NULL DEFAULT '',
        competitors TEXT DEFAULT '',
        channels TEXT DEFAULT '',
        monthly_budget REAL DEFAULT 0,
        brand_voice TEXT DEFAULT '',
        gemini_api_key TEXT DEFAULT '',
        gemini_model TEXT DEFAULT '',
        region TEXT DEFAULT '',
        market_scope_type TEXT DEFAULT 'province',
        market_location TEXT DEFAULT '',
        content_direction TEXT DEFAULT 'educational',
        phone_hotline TEXT DEFAULT '',
        website_url TEXT DEFAULT '',
        social_channels TEXT DEFAULT '',
        usp_advantages TEXT DEFAULT '',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS research_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        category TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        metadata_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS content_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
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
    )""",
    """CREATE TABLE IF NOT EXISTS performance_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        date TEXT NOT NULL,
        ad_spend REAL DEFAULT 0,
        revenue REAL DEFAULT 0,
        orders_count INTEGER DEFAULT 0,
        leads_count INTEGER DEFAULT 0,
        impressions INTEGER DEFAULT 0,
        clicks INTEGER DEFAULT 0,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS calendar_schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        day_number INTEGER NOT NULL,
        channel TEXT NOT NULL,
        pillar TEXT,
        funnel_stage TEXT,
        topic TEXT NOT NULL,
        draft_content TEXT,
        status TEXT DEFAULT 'planned',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS automation_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        task_code TEXT NOT NULL,
        task_name TEXT NOT NULL,
        status TEXT NOT NULL,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS discovered_competitors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
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
    )""",
    """CREATE TABLE IF NOT EXISTS lead_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        full_name TEXT NOT NULL,
        phone TEXT DEFAULT '',
        email TEXT DEFAULT '',
        source TEXT DEFAULT '',
        channel TEXT DEFAULT '',
        product_interest TEXT DEFAULT '',
        status TEXT DEFAULT 'new',
        deal_value REAL DEFAULT 0,
        notes TEXT DEFAULT '',
        utm_source TEXT DEFAULT '',
        utm_campaign TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
]

# (bảng, cột, kiểu) — thêm cột nếu chưa có
ADDED_COLUMNS = [
    ("app_users", "login_count", "INTEGER DEFAULT 0"),
    ("app_users", "ip_address", "TEXT DEFAULT ''"),
    ("app_users", "user_agent", "TEXT DEFAULT ''"),
    ("app_users", "password_hash", "TEXT DEFAULT ''"),
    ("app_users", "is_admin", "INTEGER DEFAULT 0"),
    ("app_users", "auth_provider", "TEXT DEFAULT ''"),
    ("app_users", "ingest_secret", "TEXT DEFAULT ''"),
    ("research_records", "user_email", "TEXT NOT NULL DEFAULT ''"),
    ("research_records", "provenance_json", "TEXT"),
    ("research_records", "guardrail_json", "TEXT"),
    ("content_items", "user_email", "TEXT NOT NULL DEFAULT ''"),
    ("content_items", "published_webhook", "INTEGER DEFAULT 0"),
    ("content_items", "webhook_published_at", "TIMESTAMP"),
    ("content_items", "format", "TEXT DEFAULT ''"),
    ("content_items", "provenance_json", "TEXT"),
    ("content_items", "guardrail_json", "TEXT"),
    ("content_items", "variants_json", "TEXT"),
    ("content_items", "updated_at", "TIMESTAMP"),
    ("performance_metrics", "user_email", "TEXT NOT NULL DEFAULT ''"),
    ("performance_metrics", "channel", "TEXT DEFAULT ''"),
    ("performance_metrics", "campaign", "TEXT DEFAULT ''"),
    ("performance_metrics", "other_marketing_cost", "REAL DEFAULT 0"),
    ("performance_metrics", "ad_attributed_revenue", "REAL"),
    ("performance_metrics", "new_customers", "INTEGER"),
    ("performance_metrics", "messages_count", "INTEGER DEFAULT 0"),
    ("calendar_schedules", "user_email", "TEXT NOT NULL DEFAULT ''"),
    ("calendar_schedules", "plan_date", "TEXT"),
    ("calendar_schedules", "format", "TEXT DEFAULT ''"),
    ("calendar_schedules", "hook", "TEXT DEFAULT ''"),
    ("calendar_schedules", "cta", "TEXT DEFAULT ''"),
    ("calendar_schedules", "metric", "TEXT DEFAULT ''"),
    ("calendar_schedules", "intent", "TEXT DEFAULT ''"),
    ("calendar_schedules", "holiday", "TEXT DEFAULT ''"),
    ("calendar_schedules", "content_item_id", "INTEGER"),
    ("calendar_schedules", "provenance_json", "TEXT"),
    ("automation_logs", "user_email", "TEXT NOT NULL DEFAULT ''"),
    ("discovered_competitors", "user_email", "TEXT NOT NULL DEFAULT ''"),
    ("discovered_competitors", "evidence_json", "TEXT"),
    ("discovered_competitors", "provenance_json", "TEXT"),
    ("lead_records", "user_email", "TEXT NOT NULL DEFAULT ''"),
    ("lead_records", "consent_marketing", "INTEGER DEFAULT 0"),
    ("lead_records", "consent_at", "TIMESTAMP"),
    ("lead_records", "consent_source", "TEXT DEFAULT ''"),
    ("lead_records", "consent_text", "TEXT DEFAULT ''"),
    ("lead_records", "lost_from_stage", "TEXT DEFAULT ''"),
    ("lead_records", "lost_reason", "TEXT DEFAULT ''"),
    ("lead_records", "purchase_count", "INTEGER DEFAULT 0"),
    ("lead_records", "referred_by", "TEXT DEFAULT ''"),
    ("lead_records", "stage_changed_at", "TIMESTAMP"),
    ("lead_records", "utm_medium", "TEXT DEFAULT ''"),
]

NEW_TABLES = [
    """CREATE TABLE IF NOT EXISTS auth_sessions (
        token_hash TEXT PRIMARY KEY,
        email TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL,
        user_agent TEXT DEFAULT ''
    )""",
    """CREATE TABLE IF NOT EXISTS context_profiles (
        user_email TEXT PRIMARY KEY,
        data_json TEXT NOT NULL,
        version INTEGER NOT NULL DEFAULT 1,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS context_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        version INTEGER NOT NULL,
        data_json TEXT NOT NULL,
        change_note TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS skill_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        task TEXT NOT NULL,
        title TEXT DEFAULT '',
        input_json TEXT,
        output_json TEXT,
        provenance_json TEXT,
        guardrail_json TEXT,
        status TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS budget_lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        month TEXT NOT NULL,
        program TEXT NOT NULL,
        item TEXT NOT NULL,
        unit_price REAL DEFAULT 0,
        unit TEXT DEFAULT '',
        quantity REAL DEFAULT 0,
        projected_total REAL DEFAULT 0,
        actual_total REAL DEFAULT 0,
        notes TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS utm_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        label TEXT DEFAULT '',
        base_url TEXT NOT NULL,
        utm_source TEXT NOT NULL,
        utm_medium TEXT NOT NULL,
        utm_campaign TEXT NOT NULL,
        utm_content TEXT DEFAULT '',
        utm_term TEXT DEFAULT '',
        full_url TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS experiments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        title TEXT NOT NULL,
        funnel_stage TEXT DEFAULT '',
        hypothesis TEXT DEFAULT '',
        change_desc TEXT DEFAULT '',
        primary_metric TEXT DEFAULT '',
        guardrail_metric TEXT DEFAULT '',
        stop_condition TEXT DEFAULT '',
        start_date TEXT DEFAULT '',
        end_date TEXT DEFAULT '',
        status TEXT DEFAULT 'planned',
        result TEXT DEFAULT '',
        learning TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS data_imports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        kind TEXT NOT NULL,
        filename TEXT DEFAULT '',
        row_count INTEGER DEFAULT 0,
        errors_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS data_rows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        kind TEXT NOT NULL,
        row_date TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        import_id INTEGER
    )""",
    """CREATE TABLE IF NOT EXISTS media_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        kind TEXT NOT NULL,
        prompt TEXT NOT NULL,
        aspect_ratio TEXT DEFAULT '',
        model TEXT DEFAULT '',
        status TEXT NOT NULL,
        file_name TEXT DEFAULT '',
        mime_type TEXT DEFAULT '',
        operation_name TEXT DEFAULT '',
        error TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS humanize_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        title TEXT DEFAULT '',
        original_text TEXT NOT NULL,
        humanized_text TEXT NOT NULL,
        mode TEXT DEFAULT 'Tự nhiên',
        tone TEXT DEFAULT 'Thân thiện',
        audience TEXT DEFAULT 'Đại chúng',
        strength TEXT DEFAULT 'Cao',
        ai_before_pct REAL DEFAULT 95.0,
        human_after_pct REAL DEFAULT 98.6,
        detectors_json TEXT DEFAULT '{}',
        metrics_json TEXT DEFAULT '{}',
        radar_json TEXT DEFAULT '{}',
        suggestions_json TEXT DEFAULT '[]',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
]

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_humanize_user ON humanize_history(user_email)",
    "CREATE INDEX IF NOT EXISTS idx_leads_user ON lead_records(user_email)",
    "CREATE INDEX IF NOT EXISTS idx_content_user ON content_items(user_email)",
    "CREATE INDEX IF NOT EXISTS idx_research_user ON research_records(user_email, category)",
    "CREATE INDEX IF NOT EXISTS idx_runs_user ON skill_runs(user_email, task)",
    "CREATE INDEX IF NOT EXISTS idx_rows_user ON data_rows(user_email, kind, row_date)",
    "CREATE INDEX IF NOT EXISTS idx_metrics_user ON performance_metrics(user_email, date)",
    "CREATE INDEX IF NOT EXISTS idx_sessions_email ON auth_sessions(email)",
]


def _columns(conn: sqlite3.Connection, table: str) -> set:
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _migrate(conn: sqlite3.Connection) -> None:
    for stmt in BASE_SCHEMA + NEW_TABLES:
        conn.execute(stmt)
    for table, col, decl in ADDED_COLUMNS:
        if col not in _columns(conn, table):
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")
    for stmt in INDEXES:
        conn.execute(stmt)
    # Trạng thái lead cũ 'lost' giữ nguyên; giá trị lạ đưa về 'new'
    conn.execute(
        "UPDATE lead_records SET status='new' WHERE status NOT IN "
        "('new','consulting','won','repeat','referral','loyal','lost')"
    )
    # Reset model mặc định không hợp lệ hoặc bị hạn chế access (gemini-2.5-flash)
    conn.execute(
        "UPDATE user_profiles SET gemini_model = '' WHERE gemini_model = 'gemini-2.5-flash'"
    )


def ensure_db() -> None:
    """Khởi tạo DB đúng một lần cho mỗi đường dẫn (an toàn khi gọi nhiều lần)."""
    global _initialized_for
    path = str(config.settings.db_path)
    if _initialized_for == path:
        return
    with _init_lock:
        if _initialized_for == path:
            return
        db_path = config.settings.db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        legacy = config.settings.legacy_db_path
        if not db_path.exists() and legacy.exists() and legacy.resolve() != db_path.resolve():
            shutil.copy2(str(legacy), str(db_path))
        conn = _connect()
        try:
            conn.execute("PRAGMA journal_mode = WAL")
            _migrate(conn)
            conn.commit()
        finally:
            conn.close()
        _initialized_for = path


def reset_for_tests() -> None:
    global _initialized_for
    _initialized_for = None


# ---------------------------------------------------------------------------
# Tiện ích dùng chung
# ---------------------------------------------------------------------------

def get_app_config(key: str, default: str = "") -> str:
    row = one("SELECT value FROM app_configs WHERE key = ?", (key,))
    return row["value"] if row and row.get("value") else default


def set_app_config(key: str, value: str) -> None:
    execute(
        "INSERT INTO app_configs (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )


def log_automation(user_email: str, task_code: str, task_name: str, status: str, details: str = "") -> None:
    execute(
        "INSERT INTO automation_logs (user_email, task_code, task_name, status, details) VALUES (?, ?, ?, ?, ?)",
        (normalize_email(user_email), task_code, task_name, status, details[:2000]),
    )


def get_automation_logs(user_email: str, limit: int = 30) -> List[Dict[str, Any]]:
    return rows(
        "SELECT * FROM automation_logs WHERE user_email = ? ORDER BY id DESC LIMIT ?",
        (normalize_email(user_email), int(limit)),
    )
