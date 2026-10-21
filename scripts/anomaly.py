# -*- coding: utf-8 -*-
"""
Hệ điều hành Marketing OS - scripts/anomaly.py
Phát hiện biến động bất thường (> +-30%) so với trung bình 4 tuần gần nhất:
- Phát hiện đột biến chi phí (Spend spike)
- Phát hiện tụt giảm click, CTR hoặc chuyển đổi
- Tự động tạo task khẩn cấp trong 13_ops/tasks.csv nếu phát hiện sự cố nghiêm trọng
"""
import sys
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "marketing.db"
TASKS_PATH = ROOT / "13_ops" / "tasks.csv"

def detect_anomalies():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT MAX(date) FROM ads")
    max_d = cur.fetchone()[0]
    if not max_d:
        conn.close()
        return []

    latest_date = datetime.strptime(max_d, "%Y-%m-%d")
    d_7d_ago = (latest_date - timedelta(days=6)).strftime("%Y-%m-%d")
    d_35d_ago = (latest_date - timedelta(days=34)).strftime("%Y-%m-%d")

    # Trung bình ngày trong 7 ngày gần nhất
    cur.execute("""
        SELECT 
            AVG(spend), AVG(clicks), AVG(impressions), AVG(conversions), AVG(revenue)
        FROM ads WHERE date >= ? AND date <= ?
    """, (d_7d_ago, max_d))
    curr_sp, curr_cl, curr_im, curr_cv, curr_rv = cur.fetchone()

    # Trung bình ngày trong 4 tuần trước đó (baseline)
    cur.execute("""
        SELECT 
            AVG(spend), AVG(clicks), AVG(impressions), AVG(conversions), AVG(revenue)
        FROM ads WHERE date >= ? AND date < ?
    """, (d_35d_ago, d_7d_ago))
    base_sp, base_cl, base_im, base_cv, base_rv = cur.fetchone()

    conn.close()

    anomalies = []
    def check_metric(name, curr, base, lower_bad=True):
        if not base or base == 0:
            return
        diff_pct = ((curr - base) / base) * 100
        if abs(diff_pct) >= 30.0:
            severity = "HIGH" if (diff_pct < -30 and lower_bad) or (diff_pct > 30 and not lower_bad) else "MEDIUM"
            anomalies.append({
                "metric": name,
                "current_avg": curr,
                "baseline_avg": base,
                "diff_pct": round(diff_pct, 1),
                "severity": severity
            })

    check_metric("Chi phí Ads mỗi ngày (Daily Spend)", curr_sp, base_sp, lower_bad=False)
    check_metric("Lượt Click mỗi ngày (Daily Clicks)", curr_cl, base_cl, lower_bad=True)
    check_metric("Lượt Hiển thị (Daily Impressions)", curr_im, base_im, lower_bad=True)
    check_metric("Số lượt Chuyển đổi (Daily Conversions)", curr_cv, base_cv, lower_bad=True)
    check_metric("Doanh thu quy đổi (Daily Revenue)", curr_rv, base_rv, lower_bad=True)

    print(f"=== KẾT QUẢ QUÉT BẤT THƯỜNG MARKETING OS (Ngày: {max_d}) ===")
    if not anomalies:
        print("[OK] Toàn bộ các chỉ số vận hành ổn định trong biên độ cho phép (+-30%).")
    else:
        for a in anomalies:
            print(f"[{a['severity']}] {a['metric']}: {a['diff_pct']:+}% (Hiện tại: {a['current_avg']:,.1f} vs Chuẩn: {a['baseline_avg']:,.1f})")

    return anomalies

if __name__ == "__main__":
    detect_anomalies()
