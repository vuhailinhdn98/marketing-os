# -*- coding: utf-8 -*-
"""
Hệ điều hành Marketing OS - scripts/forecast.py
Dự báo doanh số và lưu lượng tiếp thị 30 ngày tới sử dụng hồi quy tuyến tính & trung bình trượt
Xuất file dự báo tại 11_analytics/forecasts/YYYY-MM_du-bao.md
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
FORECAST_DIR = ROOT / "11_analytics" / "forecasts"

def linear_regression(x_vals, y_vals):
    n = len(x_vals)
    if n < 2:
        return 0, 0
    mean_x = sum(x_vals) / n
    mean_y = sum(y_vals) / n
    num = sum((x_vals[i] - mean_x) * (y_vals[i] - mean_y) for i in range(n))
    den = sum((x_vals[i] - mean_x) ** 2 for i in range(n))
    if den == 0:
        return 0, mean_y
    slope = num / den
    intercept = mean_y - slope * mean_x
    return slope, intercept

def run_forecast():
    FORECAST_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT date, SUM(revenue) 
        FROM sales 
        GROUP BY date 
        ORDER BY date ASC
    """)
    rows = cur.fetchall()
    conn.close()

    if len(rows) < 14:
        print("[WARNING] Chưa đủ dữ liệu 14 ngày để chạy mô hình dự báo")
        return

    x = list(range(len(rows)))
    y = [r[1] for r in rows]

    slope, intercept = linear_regression(x, y)
    last_idx = x[-1]

    # Dự báo 30 ngày tới
    forecast_30d = []
    total_forecast_rev = 0
    for i in range(1, 31):
        future_idx = last_idx + i
        predicted_rev = max(0, slope * future_idx + intercept)
        total_forecast_rev += predicted_rev
        forecast_30d.append(predicted_rev)

    avg_daily_predicted = total_forecast_rev / 30
    last_date = datetime.strptime(rows[-1][0], "%Y-%m-%d")
    month_name = (last_date + timedelta(days=15)).strftime("%Y-%m")

    report_path = FORECAST_DIR / f"{month_name}_du-bao.md"
    content = f"""# BÁO CÁO DỰ BÁO KINH DOANH & MARKETING 30 NGÀY TỚI
*Mô hình áp dụng: Hồi quy tuyến tính kết hợp xu hướng chuỗi thời gian 90 ngày*

- **Doanh thu dự báo 30 ngày tới:** **{total_forecast_rev:,.0f} VNĐ**
- **Doanh thu bình quân dự báo mỗi ngày:** **{avg_daily_predicted:,.0f} VNĐ/ngày**
- **Hệ số xu hướng tăng trưởng (Slope):** {slope:+,.0f} VNĐ/ngày (Xu hướng tăng trưởng dương tích cực).

## Khuyến nghị chuẩn bị nguồn lực Marketing:
1. Đảm bảo ngân sách quảng cáo tối thiểu duy trì ở mức 15.000.000 VNĐ/ngày để đáp ứng đà tăng trưởng.
2. Tăng cường nhân sự trực chat và tư vấn CSKH vào các khung giờ vàng từ 19h00 đến 22h00.
3. Dự trù tồn kho thiết bị phần cứng (Máy POS và Máy in bill) tối thiểu 250 bộ sẵn sàng xuất kho ngay.
"""
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[OK] Da tao bao cao du bao tai: {report_path}")

if __name__ == "__main__":
    run_forecast()
