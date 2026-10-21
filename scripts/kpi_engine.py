# -*- coding: utf-8 -*-
"""
Hệ điều hành Marketing OS - scripts/kpi_engine.py
Động cơ tính toán chỉ số KPI trọng yếu từ cơ sở dữ liệu SQLite:
- CTR, CPC, CPM, CVR, CPA, CPL, ROAS, MER
- CAC, LTV, Tỷ lệ LTV:CAC, AOV, Returning Customer Rate
- Tỷ lệ tương tác mạng xã hội (Engagement Rate), Open Rate, CTOR email
- Vị trí SEO trung bình & Tỷ lệ hoàn thành ngân sách (Pacing)
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

def get_connection():
    return sqlite3.connect(DB_PATH)

def calculate_kpis(days=30):
    """Tính toán toàn bộ các KPI trong số ngày gần nhất (mặc định 30 ngày)"""
    conn = get_connection()
    cursor = conn.cursor()
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    # 1. Paid Ads KPIs
    cursor.execute("""
        SELECT 
            COALESCE(SUM(impressions), 0),
            COALESCE(SUM(clicks), 0),
            COALESCE(SUM(spend), 0.0),
            COALESCE(SUM(conversions), 0),
            COALESCE(SUM(revenue), 0.0)
        FROM ads WHERE date >= ?
    """, (cutoff_date,))
    impr, clicks, spend, conv, ad_rev = cursor.fetchone()

    ctr = (clicks / impr * 100) if impr > 0 else 0.0
    cpc = (spend / clicks) if clicks > 0 else 0.0
    cpm = (spend / impr * 1000) if impr > 0 else 0.0
    cvr = (conv / clicks * 100) if clicks > 0 else 0.0
    cpa = (spend / conv) if conv > 0 else 0.0
    roas = (ad_rev / spend) if spend > 0 else 0.0

    # 2. Total Revenue & Sales KPIs
    cursor.execute("""
        SELECT 
            COALESCE(COUNT(order_id), 0),
            COALESCE(SUM(revenue), 0.0),
            COALESCE(SUM(CASE WHEN is_new_customer = 1 THEN 1 ELSE 0 END), 0),
            COALESCE(SUM(CASE WHEN is_new_customer = 0 THEN 1 ELSE 0 END), 0)
        FROM sales WHERE date >= ?
    """, (cutoff_date,))
    total_orders, total_sales_rev, new_cust_orders, return_cust_orders = cursor.fetchone()
    
    aov = (total_sales_rev / total_orders) if total_orders > 0 else 0.0
    returning_rate = (return_cust_orders / total_orders * 100) if total_orders > 0 else 0.0

    # 3. Marketing Total Spend & MER, CAC
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0.0) FROM spend WHERE date >= ?
    """, (cutoff_date,))
    other_spend = cursor.fetchone()[0]
    total_marketing_spend = spend + other_spend

    mer = (total_sales_rev / total_marketing_spend) if total_marketing_spend > 0 else 0.0
    cac = (total_marketing_spend / new_cust_orders) if new_cust_orders > 0 else 0.0
    # Ước tính LTV = AOV * 3.5 lần mua trung bình * 0.65 Gross Margin
    ltv = aov * 3.5 * 0.65
    ltv_to_cac = (ltv / cac) if cac > 0 else 0.0

    # 4. Leads & CPL
    cursor.execute("""
        SELECT 
            COALESCE(COUNT(lead_id), 0),
            COALESCE(SUM(CASE WHEN stage = 'Won' THEN 1 ELSE 0 END), 0),
            COALESCE(SUM(value), 0.0)
        FROM leads WHERE date >= ?
    """, (cutoff_date,))
    total_leads, won_leads, pipeline_val = cursor.fetchone()
    cpl = (spend / total_leads) if total_leads > 0 else 0.0
    lead_to_win_cvr = (won_leads / total_leads * 100) if total_leads > 0 else 0.0

    # 5. Social & Community
    cursor.execute("""
        SELECT 
            COALESCE(SUM(reach), 0),
            COALESCE(SUM(engagements), 0)
        FROM social WHERE date >= ?
    """, (cutoff_date,))
    soc_reach, soc_eng = cursor.fetchone()
    soc_eng_rate = (soc_eng / soc_reach * 100) if soc_reach > 0 else 0.0

    # 6. Email KPIs
    cursor.execute("""
        SELECT 
            COALESCE(SUM(sent), 0),
            COALESCE(SUM(delivered), 0),
            COALESCE(SUM(opens), 0),
            COALESCE(SUM(clicks), 0)
        FROM email WHERE date >= ?
    """, (cutoff_date,))
    em_sent, em_deliv, em_opens, em_clicks = cursor.fetchone()
    open_rate = (em_opens / em_deliv * 100) if em_deliv > 0 else 0.0
    ctor = (em_clicks / em_opens * 100) if em_opens > 0 else 0.0

    # 7. SEO Stats
    cursor.execute("""
        SELECT 
            COALESCE(SUM(clicks), 0),
            COALESCE(SUM(impressions), 0),
            COALESCE(AVG(position), 0.0)
        FROM seo WHERE date >= ?
    """, (cutoff_date,))
    seo_clicks, seo_impr, avg_pos = cursor.fetchone()
    seo_ctr = (seo_clicks / seo_impr * 100) if seo_impr > 0 else 0.0

    conn.close()

    return {
        "period_days": days,
        "cutoff_date": cutoff_date,
        "ads": {
            "impressions": impr,
            "clicks": clicks,
            "spend": spend,
            "conversions": conv,
            "revenue": ad_rev,
            "ctr_pct": round(ctr, 2),
            "cpc": round(cpc, 0),
            "cpm": round(cpm, 0),
            "cvr_pct": round(cvr, 2),
            "cpa": round(cpa, 0),
            "roas": round(roas, 2)
        },
        "financials": {
            "total_sales_revenue": round(total_sales_rev, 0),
            "total_marketing_spend": round(total_marketing_spend, 0),
            "mer": round(mer, 2),
            "total_orders": total_orders,
            "new_customers": new_cust_orders,
            "returning_customers": return_cust_orders,
            "returning_rate_pct": round(returning_rate, 2),
            "aov": round(aov, 0),
            "cac": round(cac, 0),
            "ltv": round(ltv, 0),
            "ltv_to_cac": round(ltv_to_cac, 2)
        },
        "leads": {
            "total_leads": total_leads,
            "won_leads": won_leads,
            "cpl": round(cpl, 0),
            "win_rate_pct": round(lead_to_win_cvr, 2),
            "pipeline_value": round(pipeline_val, 0)
        },
        "social": {
            "reach": soc_reach,
            "engagements": soc_eng,
            "engagement_rate_pct": round(soc_eng_rate, 2)
        },
        "email": {
            "sent": em_sent,
            "delivered": em_deliv,
            "opens": em_opens,
            "clicks": em_clicks,
            "open_rate_pct": round(open_rate, 2),
            "ctor_pct": round(ctor, 2)
        },
        "seo": {
            "clicks": seo_clicks,
            "impressions": seo_impr,
            "ctr_pct": round(seo_ctr, 2),
            "avg_position": round(avg_pos, 1)
        }
    }

def print_summary():
    kpis = calculate_kpis(30)
    print("=== MARKETING OS - TONG HOP KPI 30 NGAY QUA ===")
    print(f"Doanh thu tong: {kpis['financials']['total_sales_revenue']:,.0f} VND")
    print(f"Tong chi Marketing: {kpis['financials']['total_marketing_spend']:,.0f} VND | MER: {kpis['financials']['mer']}x")
    print(f"ROAS Quang cao: {kpis['ads']['roas']}x | Chi ads: {kpis['ads']['spend']:,.0f} VND")
    print(f"CAC: {kpis['financials']['cac']:,.0f} VND | LTV uoc tinh: {kpis['financials']['ltv']:,.0f} VND | LTV/CAC: {kpis['financials']['ltv_to_cac']}x")
    print(f"Tong Lead: {kpis['leads']['total_leads']} | CPL: {kpis['leads']['cpl']:,.0f} VND | Ty le chot: {kpis['leads']['win_rate_pct']}%")
    print(f"Ty le Open Email: {kpis['email']['open_rate_pct']}% | CTR SEO: {kpis['seo']['ctr_pct']}% | Top rank: {kpis['seo']['avg_position']}")

if __name__ == "__main__":
    print_summary()
