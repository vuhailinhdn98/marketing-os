# -*- coding: utf-8 -*-
"""
Growth Console (skill §13): số liệu nhập tay, nhập CSV từ nền tảng, ngân sách dự kiến – thực chi, UTM, thử nghiệm.
Mọi phép tính nằm trong app.metrics để có test riêng.
"""
from __future__ import annotations

import calendar as _cal
import csv
import io
import json
import math
import re
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app import metrics
from app.config import ROOT
from app.context import get_path, load_context
from app.database import dumps, execute, loads, normalize_email, one, rows

PROGRAMS = ["Quảng cáo trả phí", "Content", "Sự kiện", "PR", "Branding & Creative", "Product Marketing", "Khác"]


class DataError(ValueError):
    pass


def _f(value: Any, name: str, allow_none: bool = False) -> Optional[float]:
    if value is None or value == "":
        if allow_none:
            return None
        return 0.0
    try:
        out = float(value)
    except (TypeError, ValueError):
        raise DataError(f"{name} phải là số.")
    if not math.isfinite(out):
        raise DataError(f"{name} phải là số hữu hạn.")
    if out < 0:
        raise DataError(f"{name} không được âm.")
    return out


def _date(value: Any) -> str:
    try:
        return date.fromisoformat(str(value)[:10]).isoformat()
    except ValueError:
        raise DataError("Ngày phải theo dạng YYYY-MM-DD.")


# ---------------------------------------------------------------------------
# Số liệu nhập tay theo ngày
# ---------------------------------------------------------------------------

def record_metric(owner: str, data: Dict[str, Any]) -> int:
    owner = normalize_email(owner)
    vals = {
        "date": _date(data.get("date")),
        "channel": str(data.get("channel") or "").strip()[:60],
        "campaign": str(data.get("campaign") or "").strip()[:120],
        "ad_spend": _f(data.get("ad_spend"), "Chi quảng cáo"),
        "other_marketing_cost": _f(data.get("other_marketing_cost"), "Chi phí marketing khác"),
        "revenue": _f(data.get("revenue"), "Doanh thu"),
        "ad_attributed_revenue": _f(data.get("ad_attributed_revenue"), "Doanh thu từ quảng cáo", True),
        "orders_count": int(_f(data.get("orders_count"), "Số đơn") or 0),
        "new_customers": None if data.get("new_customers") in (None, "") else int(_f(data.get("new_customers"), "Khách mới") or 0),
        "leads_count": int(_f(data.get("leads_count"), "Số lead") or 0),
        "messages_count": int(_f(data.get("messages_count"), "Tin nhắn") or 0),
        "impressions": int(_f(data.get("impressions"), "Lượt hiển thị") or 0),
        "clicks": int(_f(data.get("clicks"), "Lượt click") or 0),
        "notes": str(data.get("notes") or "")[:500],
    }
    if vals["ad_attributed_revenue"] is not None and vals["ad_attributed_revenue"] > vals["revenue"]:
        raise DataError("Doanh thu từ quảng cáo không thể lớn hơn tổng doanh thu.")
    if vals["new_customers"] is not None and vals["orders_count"] and vals["new_customers"] > vals["orders_count"]:
        raise DataError("Số khách mới không thể lớn hơn số đơn.")
    cols = ", ".join(["user_email"] + list(vals))
    return execute(f"INSERT INTO performance_metrics ({cols}) VALUES ({', '.join(['?'] * (len(vals) + 1))})",
                   [owner] + list(vals.values()))


def delete_metric(owner: str, metric_id: int) -> bool:
    return execute("DELETE FROM performance_metrics WHERE id = ? AND user_email = ?", (metric_id, normalize_email(owner))) > 0


def list_metrics(owner: str, start: str, end: str) -> List[Dict[str, Any]]:
    return rows("SELECT * FROM performance_metrics WHERE user_email = ? AND date BETWEEN ? AND ? ORDER BY date DESC, id DESC",
                (normalize_email(owner), start, end))


def _period(days: int, end: Optional[str] = None) -> Tuple[str, str]:
    end_d = date.fromisoformat(end) if end else date.today()
    return (end_d - timedelta(days=max(1, days) - 1)).isoformat(), end_d.isoformat()


def summary(owner: str, days: int = 30, end: Optional[str] = None) -> Dict[str, Any]:
    owner = normalize_email(owner)
    start, stop = _period(days, end)
    ctx = load_context(owner)
    gm = get_path(ctx, "unit_economics.gross_margin_pct")
    fixed_month = get_path(ctx, "unit_economics.marketing_fixed_cost_month_vnd") or 0
    data = list_metrics(owner, start, stop)
    tot = defaultdict(float)
    attributed_known = new_known = True
    for r in data:
        for k in ("ad_spend", "other_marketing_cost", "revenue", "orders_count", "leads_count", "messages_count", "impressions", "clicks"):
            tot[k] += float(r.get(k) or 0)
        if r.get("ad_attributed_revenue") is None:
            attributed_known = False
        else:
            tot["ad_attributed_revenue"] += float(r["ad_attributed_revenue"])
        if r.get("new_customers") is None:
            new_known = False
        else:
            tot["new_customers"] += float(r["new_customers"])
    other = tot["other_marketing_cost"] + float(fixed_month) * days / 30.0
    ue = metrics.unit_economics(
        revenue=tot["revenue"], ad_spend=tot["ad_spend"], other_cost=round(other), gross_margin_pct=gm,
        orders=int(tot["orders_count"]), new_customers=int(tot["new_customers"]) if (new_known and data) else None,
        leads=int(tot["leads_count"]), messages=int(tot["messages_count"]),
        ad_attributed_revenue=tot["ad_attributed_revenue"] if (attributed_known and data) else None)
    if fixed_month:
        ue["notes"].append(f"Đã cộng chi phí marketing cố định {int(fixed_month):,} đ/tháng (phân bổ theo số ngày) vào CAC và MER.".replace(",", "."))
    by_day: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    by_channel: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for r in data:
        for k in ("ad_spend", "revenue", "orders_count", "leads_count", "other_marketing_cost"):
            by_day[r["date"]][k] += float(r.get(k) or 0)
            by_channel[r.get("channel") or "Chưa ghi kênh"][k] += float(r.get(k) or 0)
    series = [{"date": d, **{k: round(v, 0) for k, v in vals.items()}} for d, vals in sorted(by_day.items())]
    channels = [{"channel": c, **{k: round(v, 0) for k, v in vals.items()},
                 "mer": metrics._r(metrics._div(vals["revenue"], vals["ad_spend"] + vals["other_marketing_cost"]))}
                for c, vals in sorted(by_channel.items(), key=lambda kv: -kv[1]["revenue"])]
    return {"period": {"start": start, "end": stop, "days": days}, "entries": len(data), "unit_economics": ue,
            "series": series, "channels": channels, "gross_margin_pct": gm}


# ---------------------------------------------------------------------------
# Nhập CSV từ nền tảng
# ---------------------------------------------------------------------------

def _schemas() -> Dict[str, Dict[str, Any]]:
    out = {}
    for path in (ROOT / "data" / "schemas").glob("*_schema.json"):
        try:
            spec = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        out[spec.get("table_name") or path.stem.replace("_schema", "")] = spec
    return out


SCHEMAS = _schemas()


def import_kinds() -> List[Dict[str, Any]]:
    return [{"kind": k, "description": v.get("description", ""), "required_columns": v.get("required_columns", [])}
            for k, v in sorted(SCHEMAS.items())]


def detect_kind(filename: str) -> Optional[str]:
    base = Path(filename or "").name.lower()
    for kind in SCHEMAS:
        if base.startswith(kind + "_") or base.startswith(kind + "-") or base == f"{kind}.csv":
            return kind
    return None


def _num(raw: str) -> float:
    s = str(raw).strip().replace(" ", "")
    if s == "":
        return 0.0
    if re.fullmatch(r"-?\d{1,3}(\.\d{3})+(,\d+)?", s):  # 1.234.567,89
        s = s.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"-?\d{1,3}(,\d{3})+(\.\d+)?", s):  # 1,234,567.89
        s = s.replace(",", "")
    else:
        s = s.replace(",", ".")
    return float(s)


def import_csv(owner: str, kind: str, filename: str, content: bytes, replace_period: bool = True) -> Dict[str, Any]:
    owner = normalize_email(owner)
    spec = SCHEMAS.get(kind)
    if not spec:
        raise DataError("Loại dữ liệu không hỗ trợ.")
    if len(content) > 10 * 1024 * 1024:
        raise DataError("File quá lớn (tối đa 10 MB).")
    text = content.decode("utf-8-sig", errors="replace")
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    headers = [h.strip().lower() for h in (reader.fieldnames or [])]
    required = spec.get("required_columns", [])
    missing = [c for c in required if c not in headers]
    if missing:
        raise DataError(f"Thiếu cột bắt buộc: {', '.join(missing)}. Cột cần có: {', '.join(required)}.")
    types = spec.get("types", {})
    parsed, errors = [], []
    for i, raw in enumerate(reader, start=2):
        row = {str(k).strip().lower(): (v or "").strip() for k, v in raw.items() if k}
        try:
            out: Dict[str, Any] = {}
            for col in required:
                t = types.get(col, "TEXT")
                val = row.get(col, "")
                if t == "DATE":
                    out[col] = _date(val)
                elif t in ("INTEGER", "REAL"):
                    out[col] = _num(val)
                    if t == "INTEGER":
                        out[col] = int(round(out[col]))
                else:
                    out[col] = val[:200]
            parsed.append(out)
        except (DataError, ValueError) as exc:
            if len(errors) < 20:
                errors.append(f"Dòng {i}: {exc}")
    if not parsed:
        raise DataError("Không đọc được dòng dữ liệu hợp lệ nào. " + "; ".join(errors[:3]))
    dates = sorted(r["date"] for r in parsed)
    import_id = execute("INSERT INTO data_imports (user_email, kind, filename, row_count, errors_json) VALUES (?, ?, ?, ?, ?)",
                        (owner, kind, filename[:200], len(parsed), dumps(errors)))
    if replace_period:
        execute("DELETE FROM data_rows WHERE user_email = ? AND kind = ? AND row_date BETWEEN ? AND ?",
                (owner, kind, dates[0], dates[-1]))
    from app.database import connect
    with connect() as conn:
        conn.executemany("INSERT INTO data_rows (user_email, kind, row_date, payload_json, import_id) VALUES (?, ?, ?, ?, ?)",
                         [(owner, kind, r["date"], dumps(r), import_id) for r in parsed])
    return {"import_id": import_id, "kind": kind, "rows": len(parsed), "skipped": len(errors), "errors": errors,
            "date_range": [dates[0], dates[-1]]}


def imports(owner: str) -> List[Dict[str, Any]]:
    data = rows("SELECT * FROM data_imports WHERE user_email = ? ORDER BY id DESC LIMIT 50", (normalize_email(owner),))
    for d in data:
        d["errors"] = loads(d.pop("errors_json", None), [])
    return data


def _rows_of(owner: str, kind: str, start: str, end: str) -> List[Dict[str, Any]]:
    data = rows("SELECT payload_json FROM data_rows WHERE user_email = ? AND kind = ? AND row_date BETWEEN ? AND ? ORDER BY row_date",
                (normalize_email(owner), kind, start, end))
    return [loads(r["payload_json"], {}) for r in data]


def imported_report(owner: str, days: int = 90, end: Optional[str] = None) -> Dict[str, Any]:
    start, stop = _period(days, end)
    rep: Dict[str, Any] = {"period": {"start": start, "end": stop}}
    ads = _rows_of(owner, "ads", start, stop)
    if ads:
        camp: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        daily: Dict[str, float] = defaultdict(float)
        for r in ads:
            key = f"{r.get('platform', '')} · {r.get('campaign', '')}"
            for k in ("impressions", "clicks", "spend", "conversions", "revenue"):
                camp[key][k] += float(r.get(k) or 0)
            daily[r["date"]] += float(r.get("spend") or 0)
        rep["ads"] = sorted([{"campaign": k, **{m: round(v, 0) for m, v in vals.items()},
                              "ctr_pct": metrics._r(metrics._div(vals["clicks"] * 100, vals["impressions"])),
                              "cpc": metrics._r(metrics._div(vals["spend"], vals["clicks"]), 0),
                              "cpa": metrics._r(metrics._div(vals["spend"], vals["conversions"]), 0),
                              "roas": metrics._r(metrics._div(vals["revenue"], vals["spend"]))}
                             for k, vals in camp.items()], key=lambda x: -x["spend"])
        series = sorted(daily.items())
        rep["ads_spend_anomalies"] = metrics.anomalies(series)
    sales = _rows_of(owner, "sales", start, stop)
    if sales:
        daily_rev: Dict[str, float] = defaultdict(float)
        customers, new_customers, orders = set(), set(), set()
        by_channel: Dict[str, float] = defaultdict(float)
        for r in sales:
            daily_rev[r["date"]] += float(r.get("revenue") or 0)
            customers.add(r.get("customer_id"))
            orders.add(r.get("order_id"))
            by_channel[r.get("channel") or "?"] += float(r.get("revenue") or 0)
            if int(float(r.get("is_new_customer") or 0)) == 1:
                new_customers.add(r.get("customer_id"))
        revenue = sum(daily_rev.values())
        series = sorted(daily_rev.items())
        rep["sales"] = {"revenue": round(revenue), "orders": len(orders), "customers": len(customers),
                        "new_customers": len(new_customers),
                        "aov": metrics._r(metrics._div(revenue, len(orders)), 0),
                        "orders_per_customer": metrics._r(metrics._div(len(orders), len(customers))),
                        "by_channel": [{"channel": k, "revenue": round(v)} for k, v in sorted(by_channel.items(), key=lambda kv: -kv[1])],
                        "series": [{"date": d, "revenue": round(v)} for d, v in series],
                        "anomalies": metrics.anomalies(series),
                        "forecast_30d": metrics.linear_forecast(series, 30)}
    web = _rows_of(owner, "web", start, stop)
    if web:
        src: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        for r in web:
            key = f"{r.get('source', '')} / {r.get('medium', '')}"
            for k in ("sessions", "users", "new_users", "conversions", "revenue"):
                src[key][k] += float(r.get(k) or 0)
        rep["web"] = sorted([{"source_medium": k, **{m: round(v) for m, v in vals.items()},
                              "cvr_pct": metrics._r(metrics._div(vals["conversions"] * 100, vals["sessions"]))}
                             for k, vals in src.items()], key=lambda x: -x["sessions"])
    social = _rows_of(owner, "social", start, stop)
    if social:
        posts = []
        for r in social:
            reach = float(r.get("reach") or 0)
            posts.append({"date": r["date"], "platform": r.get("platform"), "post_id": r.get("post_id"),
                          "post_type": r.get("post_type"), "reach": reach,
                          "engagement_rate_pct": metrics._r(metrics._div(float(r.get("engagements") or 0) * 100, reach))})
        ranked = sorted([p for p in posts if p["engagement_rate_pct"] is not None], key=lambda p: -p["engagement_rate_pct"])
        rep["social"] = {"posts": len(posts), "top3": ranked[:3], "bottom3": ranked[-3:][::-1] if len(ranked) > 3 else []}
    email = _rows_of(owner, "email", start, stop)
    if email:
        camp_e: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        for r in email:
            for k in ("sent", "delivered", "opens", "clicks", "unsubscribes", "conversions", "revenue"):
                camp_e[r.get("campaign", "")][k] += float(r.get(k) or 0)
        rep["email"] = [{"campaign": k, "open_rate_pct": metrics._r(metrics._div(v["opens"] * 100, v["delivered"])),
                         "ctor_pct": metrics._r(metrics._div(v["clicks"] * 100, v["opens"])),
                         "unsub_rate_pct": metrics._r(metrics._div(v["unsubscribes"] * 100, v["delivered"])),
                         "revenue": round(v["revenue"])} for k, v in camp_e.items()]
    seo = _rows_of(owner, "seo", start, stop)
    if seo:
        q: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        for r in seo:
            d = q[r.get("query", "")]
            d["clicks"] += float(r.get("clicks") or 0)
            d["impressions"] += float(r.get("impressions") or 0)
            d["pos_x_impr"] += float(r.get("position") or 0) * float(r.get("impressions") or 0)
        rep["seo"] = sorted([{"query": k, "clicks": round(v["clicks"]), "impressions": round(v["impressions"]),
                              "avg_position": metrics._r(metrics._div(v["pos_x_impr"], v["impressions"]), 1)}
                             for k, v in q.items()], key=lambda x: -x["impressions"])[:30]
    spend = _rows_of(owner, "spend", start, stop)
    if spend:
        cat: Dict[str, float] = defaultdict(float)
        for r in spend:
            cat[r.get("category") or "Khác"] += float(r.get("amount") or 0)
        rep["spend"] = [{"category": k, "amount": round(v)} for k, v in sorted(cat.items(), key=lambda kv: -kv[1])]
    leads_rows = _rows_of(owner, "leads", start, stop)
    if leads_rows:
        stages: Dict[str, int] = defaultdict(int)
        for r in leads_rows:
            stages[r.get("stage") or "?"] += 1
        rep["leads"] = [{"stage": k, "count": v} for k, v in stages.items()]
    return rep


# ---------------------------------------------------------------------------
# Ngân sách dự kiến – thực chi
# ---------------------------------------------------------------------------

def add_budget_line(owner: str, data: Dict[str, Any]) -> int:
    month = str(data.get("month") or "")
    if not re.fullmatch(r"\d{4}-\d{2}", month):
        raise DataError("Tháng phải theo dạng YYYY-MM.")
    program = data.get("program")
    if program not in PROGRAMS:
        raise DataError("Chương trình phải là một trong: " + ", ".join(PROGRAMS))
    item = str(data.get("item") or "").strip()
    if not item:
        raise DataError("Thiếu hạng mục.")
    price = _f(data.get("unit_price"), "Đơn giá") or 0
    qty = _f(data.get("quantity"), "Số lượng") or 0
    actual = _f(data.get("actual_total"), "Thực chi") or 0
    return execute("INSERT INTO budget_lines (user_email, month, program, item, unit_price, unit, quantity, projected_total, actual_total, notes) "
                   "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   (normalize_email(owner), month, program, item[:200], price, str(data.get("unit") or "")[:40], qty,
                    round(price * qty), actual, str(data.get("notes") or "")[:300]))


def update_budget_actual(owner: str, line_id: int, actual_total: Any) -> bool:
    return execute("UPDATE budget_lines SET actual_total = ? WHERE id = ? AND user_email = ?",
                   (_f(actual_total, "Thực chi"), line_id, normalize_email(owner))) > 0


def delete_budget_line(owner: str, line_id: int) -> bool:
    return execute("DELETE FROM budget_lines WHERE id = ? AND user_email = ?", (line_id, normalize_email(owner))) > 0


def budget_month(owner: str, month: str) -> Dict[str, Any]:
    if not re.fullmatch(r"\d{4}-\d{2}", month or ""):
        raise DataError("Tháng phải theo dạng YYYY-MM.")
    lines = rows("SELECT * FROM budget_lines WHERE user_email = ? AND month = ? ORDER BY program, id", (normalize_email(owner), month))
    by_program: Dict[str, Dict[str, float]] = {p: {"projected": 0.0, "actual": 0.0} for p in PROGRAMS}
    for l in lines:
        l["variance"] = round((l["actual_total"] or 0) - (l["projected_total"] or 0))
        by_program[l["program"]]["projected"] += l["projected_total"] or 0
        by_program[l["program"]]["actual"] += l["actual_total"] or 0
    projected = sum(v["projected"] for v in by_program.values())
    actual = sum(v["actual"] for v in by_program.values())
    y, m = int(month[:4]), int(month[5:])
    days_in = _cal.monthrange(y, m)[1]
    today = date.today()
    pace = None
    if today.year == y and today.month == m and projected:
        pace = metrics.pacing(planned_month_budget=projected, spent_to_date=actual, day_of_month=today.day, days_in_month=days_in)
    return {"month": month, "lines": lines,
            "programs": [{"program": p, "projected": round(v["projected"]), "actual": round(v["actual"]),
                          "variance": round(v["actual"] - v["projected"])} for p, v in by_program.items()],
            "projected_total": round(projected), "actual_total": round(actual), "variance": round(actual - projected), "pacing": pace}


# ---------------------------------------------------------------------------
# UTM và thử nghiệm
# ---------------------------------------------------------------------------

def create_utm(owner: str, data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        url = metrics.utm_build(base_url=str(data.get("base_url") or ""), source=str(data.get("utm_source") or ""),
                                medium=str(data.get("utm_medium") or ""), campaign=str(data.get("utm_campaign") or ""),
                                content=str(data.get("utm_content") or ""), term=str(data.get("utm_term") or ""))
    except ValueError as exc:
        raise DataError(str(exc))
    from urllib.parse import parse_qs, urlparse
    q = parse_qs(urlparse(url).query)
    rec = {k: (q.get(k) or [""])[0] for k in ("utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term")}
    link_id = execute("INSERT INTO utm_links (user_email, label, base_url, utm_source, utm_medium, utm_campaign, utm_content, utm_term, full_url) "
                      "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      (normalize_email(owner), str(data.get("label") or "")[:120], str(data.get("base_url"))[:500],
                       rec["utm_source"], rec["utm_medium"], rec["utm_campaign"], rec["utm_content"], rec["utm_term"], url))
    return {"id": link_id, "full_url": url, **rec}


def list_utm(owner: str) -> List[Dict[str, Any]]:
    return rows("SELECT * FROM utm_links WHERE user_email = ? ORDER BY id DESC LIMIT 200", (normalize_email(owner),))


def delete_utm(owner: str, link_id: int) -> bool:
    return execute("DELETE FROM utm_links WHERE id = ? AND user_email = ?", (link_id, normalize_email(owner))) > 0


EXP_FIELDS = ["title", "funnel_stage", "hypothesis", "change_desc", "primary_metric", "guardrail_metric", "stop_condition",
              "start_date", "end_date", "status", "result", "learning"]
EXP_STATUSES = ["planned", "running", "done", "stopped"]


def save_experiment(owner: str, data: Dict[str, Any], exp_id: Optional[int] = None) -> int:
    clean = {k: str(data.get(k) or "").strip()[:1000] for k in EXP_FIELDS if k in data}
    if "status" in clean and clean["status"] not in EXP_STATUSES:
        raise DataError("Trạng thái thử nghiệm không hợp lệ.")
    if exp_id is None:
        if not clean.get("title"):
            raise DataError("Thiếu tên thử nghiệm.")
        cols = ["user_email"] + list(clean)
        return execute(f"INSERT INTO experiments ({', '.join(cols)}) VALUES ({', '.join(['?'] * len(cols))})",
                       [normalize_email(owner)] + list(clean.values()))
    if not clean:
        return exp_id
    sets = ", ".join(f"{k} = ?" for k in clean)
    if execute(f"UPDATE experiments SET {sets} WHERE id = ? AND user_email = ?", list(clean.values()) + [exp_id, normalize_email(owner)]) == 0:
        raise DataError("Không tìm thấy thử nghiệm.")
    return exp_id


def list_experiments(owner: str) -> List[Dict[str, Any]]:
    return rows("SELECT * FROM experiments WHERE user_email = ? ORDER BY id DESC", (normalize_email(owner),))


def delete_experiment(owner: str, exp_id: int) -> bool:
    return execute("DELETE FROM experiments WHERE id = ? AND user_email = ?", (exp_id, normalize_email(owner))) > 0
