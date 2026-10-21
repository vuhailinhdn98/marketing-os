# -*- coding: utf-8 -*-
"""
Hệ điều hành Marketing OS - scripts/budget_pacing.py
Kiểm soát tốc độ chi tiêu ngân sách (Pacing):
- Tính toán tỷ lệ chi tiêu thực tế so với số ngày đã trôi qua trong tháng
- Cảnh báo nếu chi tiêu quá nhanh (Over-pacing) hoặc quá chậm (Under-pacing)
"""
import sys
import sqlite3
import calendar
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "marketing.db"

def check_budget_pacing():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT MAX(date) FROM ads")
    max_d = cur.fetchone()[0]
    if not max_d:
        conn.close()
        return

    latest_date = datetime.strptime(max_d, "%Y-%m-%d")
    month_str = latest_date.strftime("%Y-%m")
    day_of_month = latest_date.day
    _, total_days_in_month = calendar.monthrange(latest_date.year, latest_date.month)

    cur.execute("SELECT COALESCE(SUM(spend), 0.0) FROM ads WHERE date LIKE ?", (f"{month_str}%",))
    total_ad_spend = cur.fetchone()[0]

    cur.execute("SELECT COALESCE(SUM(amount), 0.0) FROM spend WHERE date LIKE ?", (f"{month_str}%",))
    total_other_spend = cur.fetchone()[0]

    conn.close()

    total_actual = total_ad_spend + total_other_spend
    # Ngân sách tháng tiêu chuẩn: 450.000.000 VNĐ
    monthly_budget = 450000000.0
    expected_pacing_pct = (day_of_month / total_days_in_month) * 100
    actual_pacing_pct = (total_actual / monthly_budget) * 100
    pacing_diff = actual_pacing_pct - expected_pacing_pct

    print(f"=== BÁO CÁO TIẾN ĐỘ NGÂN SÁCH THÁNG {month_str} ===")
    print(f"Số ngày đã qua: {day_of_month}/{total_days_in_month} ngày (Tiến độ thời gian: {expected_pacing_pct:.1f}%)")
    print(f"Ngân sách kế hoạch: {monthly_budget:,.0f} VNĐ")
    print(f"Thực chi tích lũy: {total_actual:,.0f} VNĐ (Tiến độ giải ngân: {actual_pacing_pct:.1f}%)")
    
    if abs(pacing_diff) <= 5.0:
        print(f"[ON TRACK] Pacing hoàn hảo: Biên độ sai lệch chỉ {pacing_diff:+.1f}%.")
    elif pacing_diff > 5.0:
        print(f"[CẢNH BÁO OVER-PACING] Đang tiêu nhanh hơn tiến độ {pacing_diff:+.1f}%. Cần rà soát các chiến dịch có CPA tăng cao.")
    else:
        print(f"[CẢNH BÁO UNDER-PACING] Đang tiêu chậm hơn tiến độ {pacing_diff:+.1f}%. Cần mở rộng quy mô tệp hoặc tăng giá thầu.")

if __name__ == "__main__":
    check_budget_pacing()
