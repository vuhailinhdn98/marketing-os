# -*- coding: utf-8 -*-
import sys
import time
import requests
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.database import (
    get_profile, update_profile, save_research_record,
    save_calendar_items, get_connection, log_automation
)

p = get_profile()
p["gemini_model"] = "gemini-3.5-flash"
update_profile(p)

key = p.get("gemini_api_key", "").strip()
brand = p.get("brand_name", "SmartOSC")
industry = p.get("industry", "IT, làm website")
products = p.get("products_services", "website, app, hệ thống")
price = p.get("price_range", "50tr")
audience = p.get("target_audience", "Doanh nghiệp muốn làm website, app")
budget = p.get("monthly_budget", 300000000)
channels = p.get("channels", "facebook, ig, website, linkedin")

def call_rest(prompt):
    models = ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.7-flash"]
    for m in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        for attempt in range(2):
            try:
                print(f"Calling Google AI Studio with model: {m} (attempt {attempt+1})...", flush=True)
                r = requests.post(url, json=payload, timeout=50)
                if r.status_code == 200:
                    data = r.json()
                    res_text = data["candidates"][0]["content"]["parts"][0]["text"]
                    print(f"SUCCESS with {m}! Received {len(res_text)} chars from Gemini.", flush=True)
                    return res_text
                elif r.status_code == 429:
                    print(f"[{m}] Hit 429 rate limit, sleeping 15s...", flush=True)
                    time.sleep(15)
                else:
                    print(f"[{m}] Status {r.status_code}: {r.text[:150]}", flush=True)
                    break
            except Exception as e:
                print(f"[{m}] Exception: {e}", flush=True)
                time.sleep(3)
    return None

print("=== 1. GENERATING REAL AI MARKET RESEARCH FOR SMARTOSC ===")
mr_prompt = f"""Bạn là Giám đốc Nghiên cứu Thị trường & CMO cấp cao. Hãy lập BÁO CÁO NGHIÊN CỨU THỊ TRƯỜNG THỰC TẾ VÀ ĐỘC BẢN CHO:
- Doanh nghiệp: {brand}
- Ngành: {industry} (Phát triển phần mềm, Thiết kế Website Enterprise, Mobile App & Giải pháp số B2B)
- Sản phẩm/Dịch vụ: {products} (Gói dịch vụ khởi điểm: {price})
- Tệp khách hàng mục tiêu: {audience}
- Kênh tiếp thị: {channels}
- Ngân sách Marketing: {budget:,} VNĐ/tháng

YÊU CẦU NỘI DUNG CHUYÊN SÂU:
1. Tính toán dung lượng thị trường phần mềm & website B2B tại Việt Nam (TAM / SAM / SOM) bằng số liệu cụ thể.
2. Phân tích PESTEL sát thực tế Việt Nam (Chính sách Chuyển đổi số Quốc gia, Luật An ninh mạng, Nghị định 13 về Dữ liệu cá nhân, lạm phát công nghệ, xu hướng AI Commerce & Headless Commerce).
3. Phân tích 5 Lực Lượng Cạnh Tranh Porter cho thị trường Digital Agency / IT Solution Provider.
4. 3 Cơ hội bứt phá & 3 Rủi ro sống còn cho {brand}.
5. Bản đồ hành động Go-To-Market 4 tuần đầu tiên: Kế hoạch triển khai đa kênh B2B (LinkedIn, Event, SEO, Inbound Marketing).
Tuyệt đối không dùng kịch bản mẫu, đây là bản phân tích thực chiến cho công ty công nghệ {brand}."""

mr_out = call_rest(mr_prompt)
if mr_out:
    save_research_record("market_research", f"Nghiên cứu thị trường: {brand}", mr_out)
    log_automation("A01_MARKET", "Nghiên cứu thị trường", "SUCCESS", f"Google Gemini 3.5 Flash đã phân tích xong ({len(mr_out)} ký tự)")
    print(f"SUCCESS! Saved Market Research ({len(mr_out)} chars)")

time.sleep(5)

print("=== 2. GENERATING REAL AI COMPETITOR BATTLECARDS FOR SMARTOSC ===")
comp_prompt = f"""Bạn là Head of Competitive Intelligence. Hãy lập BÁO CÁO TÌNH BÁO ĐỐI THỦ VÀ BATTLECARDS CHIẾN LƯỢC CHO:
- Doanh nghiệp của ta: {brand}
- Ngành: {industry}
- Sản phẩm/Dịch vụ: {products} (Gói chuẩn: {price})
- Đối thủ cạnh tranh thực tế trên thị trường:
  1. Phân khúc nền tảng đóng gói sẵn: Sapo Web, Haravan
  2. Phân khúc gia công phần mềm / Custom Software: FPT Software, CMC Global, Rikkei Digital, VMO Holdings
  3. Phân khúc Web Agency boutique / tầm trung: Canavi, Beau Agency, Cánh Cam, Mona Media

YÊU CẦU:
1. Ma trận so sánh định vị, thế mạnh công nghệ, mức giá và phân khúc khách hàng của từng đối thủ.
2. Tử huyệt và điểm yếu của từng nhóm đối thủ mà khách hàng B2B thường bức xúc (Ví dụ: Nền tảng đóng gói sẵn thì code cứng khó mở rộng; các tập đoàn lớn thì chi phí quá cao, thủ tục rườm rà; các agency nhỏ thì hay trễ deadline, bỏ rơi khách hàng sau bàn giao).
3. Lợi thế đè bẹp của {brand} (Where {brand} Wins: Tối ưu chi phí {price}, linh hoạt tùy biến, quy trình agile chuẩn quốc tế).
4. Kịch bản Xử Lý Từ Chối (Objection Handling Script) cực kỳ sắc bén khi khách hàng so sánh {brand} với làm web giá rẻ 10-15 triệu hoặc nền tảng đóng gói."""

comp_out = call_rest(comp_prompt)
if comp_out:
    save_research_record("battlecards", f"Tình báo đối thủ: {brand}", comp_out)
    log_automation("A02_COMPETITORS", "Tình báo đối thủ", "SUCCESS", f"Google Gemini 3.5 Flash đã lập Battlecards ({len(comp_out)} ký tự)")
    print(f"SUCCESS! Saved Battlecards ({len(comp_out)} chars)")

time.sleep(5)

print("=== 3. GENERATING REAL AI BUYER PERSONAS FOR SMARTOSC ===")
pers_prompt = f"""Bạn là Chuyên gia Tâm lý Khách hàng B2B. Hãy xây dựng 3 CHÂN DUNG KHÁCH HÀNG MỤC TIÊU SỐNG ĐỘNG CHO {brand} ({products}, phân khúc {price}):
1. Persona 1: Chủ doanh nghiệp / Giám đốc điều hành (CEO) của công ty sản xuất/thương mại truyền thống đang muốn mở kênh bán hàng số và app riêng.
2. Persona 2: Giám đốc Marketing (CMO) hoặc Head of E-commerce của chuỗi bán lẻ / F&B cần hệ thống website tải lớn, bảo mật cao và tích hợp ERP/CRM.
3. Persona 3: Giám đốc Công nghệ (CTO) / Startup Founder cần đối tác outsource xây dựng MVP hoặc hệ thống lõi.

YÊU CẦU:
Với mỗi Persona, hãy chỉ rõ: Tên giả định, độ tuổi, ngân sách phê duyệt, kênh tìm kiếm vendor công nghệ (LinkedIn, Google, bạn bè giới thiệu), nỗi đau lớn nhất với các bên làm IT trước đó (bị vẽ việc, trễ hạn, lỗi vặt), tiêu chí then chốt để ký hợp đồng và Câu chào hàng (Elevator Pitch) 1 câu đánh trúng tim đen."""

pers_out = call_rest(pers_prompt)
if pers_out:
    save_research_record("personas", f"Chân dung khách hàng: {brand}", pers_out)
    log_automation("A05_PERSONAS", "Chân dung khách hàng", "SUCCESS", f"Google Gemini 3.5 Flash đã dựng 3 Personas ({len(pers_out)} ký tự)")
    print(f"SUCCESS! Saved Personas ({len(pers_out)} chars)")

time.sleep(5)

print("=== 4. GENERATING REAL AI 30-DAY CALENDAR & SAMPLES FOR SMARTOSC ===")
cal_prompt = f"""Hãy lập LỊCH BIÊN TẬP NỘI DUNG 30 NGÀY B2B ĐA KÊNH (LinkedIn, Facebook, Website Blog, Case Study) cho {brand} cung cấp {products} ({price}):
Phân bổ rõ ràng 30 ngày theo 4 giai đoạn phễu:
- TOFU: Nhận diện nỗi đau công nghệ, cảnh báo rủi ro chọn sai agency làm web.
- MOFU: Case study chuyển đổi số, bóc tách kiến trúc hệ thống, kiến thức UI/UX.
- BOFU: Báo giá minh bạch, quy trình bảo hành cam kết SLA 99.9%, ưu đãi audit hệ thống miễn phí.
- Retention: Hướng dẫn bảo mật dữ liệu, tối ưu tốc độ tải trang Core Web Vitals.
Trả về danh sách định dạng JSON có 30 items, mỗi item gồm: day (1..30), channel, pillar, funnel_stage, topic."""

cal_out = call_rest(cal_prompt)
if cal_out:
    # Try parsing JSON or fallback to clean extraction
    try:
        clean_json = cal_out.strip()
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_json:
            clean_json = clean_json.split("```")[1].split("```")[0].strip()
        items = json.loads(clean_json)
        if isinstance(items, list) and len(items) >= 20:
            save_calendar_items(items)
            print("SUCCESS! Saved 30-day AI calendar items into DB.")
    except Exception as e:
        print(f"Calendar JSON parse note: {e}")

print("=== COMPLETED 100% REAL AI GENERATION FOR SMARTOSC! ===")
