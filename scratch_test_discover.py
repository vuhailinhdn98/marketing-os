# -*- coding: utf-8 -*-
import sys, json, requests
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.database import get_profile
from app.ai_engine import search_live_web

p = get_profile()
key = p.get("gemini_api_key", "").strip()
brand = p.get("brand_name", "SmartOSC")
industry = p.get("industry", "IT, làm website")
products = p.get("products_services", "website, app, hệ thống")
price = p.get("price_range", "50tr")
audience = p.get("target_audience", "Doanh nghiệp muốn làm website")

q = f"{industry} {products} uy tín việt nam"
web_res = search_live_web(q, max_results=4)
snippets = []
for r in web_res:
    t = r.get("title", "")
    s = r.get("snippet", "")
    u = r.get("url", "")
    snippets.append(f"- {t}: {s} ({u})")
web_str = "\n".join(snippets)

prompt = f"""Bạn là Giám đốc Tình báo Cạnh tranh cấp cao tại Việt Nam.
Doanh nghiệp của ta:
- Tên thương hiệu: {brand}
- Ngành nghề: {industry}
- Sản phẩm/Dịch vụ chủ lực: {products} (Phân khúc giá: {price})
- Đối tượng khách hàng: {audience}

Chủ doanh nghiệp KHÔNG BIẾT đối thủ của mình là ai trên thị trường.
Nhiệm vụ của bạn: Dựa vào thông tin trên, dữ liệu tìm kiếm web dưới đây và sự am hiểu thị trường Việt Nam, hãy tự động rà quét và tìm ra 4-5 đối thủ cạnh tranh có thật (trực tiếp và gián tiếp) đang hoạt động tại Việt Nam trong phân khúc {price}.

DỮ LIỆU TÌM KIẾM WEB:
{web_str}

Trả về DUY NHẤT một mảng JSON (không thêm bất kỳ lời dẫn hay ghi chú nào ngoài JSON):
[
  {{
    "name": "Tên đối thủ",
    "website": "URL website (ví dụ https://mona.media)",
    "type": "Trực tiếp",
    "price_segment": "Tầm trung (30-80 triệu)",
    "core_products": "Thiết kế web độc quyền, phần mềm quản lý",
    "key_strengths": "Điểm mạnh",
    "vulnerabilities": "Điểm yếu/Tử huyệt"
  }}
]"""

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={key}"
payload = {"contents": [{"parts": [{"text": prompt}]}]}
r = requests.post(url, json=payload, timeout=30)
if r.status_code == 200:
    res = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    print("SUCCESSFUL DISCOVERY RESULT:")
    print(res)
else:
    print("FAILED:", r.status_code, r.text)
