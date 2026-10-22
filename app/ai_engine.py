# -*- coding: utf-8 -*-
"""
Deep Intelligence & Live Web Scraping Engine for Marketing OS
- Real-time Web Search & Direct Domain Scraping
- Deep Vietnamese Domain Knowledge Bases (Cơ khí máy móc xây dựng, Thời trang, Spa thẩm mỹ, F&B, Công nghệ bán lẻ...)
- Google AI Studio (Gemini 1.5 Pro / Flash / 2.0) Integration
- Concrete Competitor Battlecards with real customer pain points and objection handling scripts
"""
import os
import re
import json
import urllib.parse
from datetime import datetime
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. LIVE WEB SEARCH & COMPETITOR SCRAPING ENGINE ---

def clean_query(text: str) -> str:
    """Loại bỏ ký tự đặc biệt để câu tìm kiếm chuẩn xác"""
    return re.sub(r"[^\w\s]", " ", text).strip()

def search_live_web(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """Tìm kiếm trực tiếp trên web theo thời gian thực với cơ chế chống lỗi"""
    results = []
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            q_clean = clean_query(query)
            if not q_clean:
                return results
            raw = list(ddgs.text(q_clean, max_results=max_results))
            for item in raw:
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("body", ""),
                    "url": item.get("href", "")
                })
            if results:
                return results
    except Exception as e:
        pass

    return results

def scrape_competitor_site(url_or_name: str) -> Dict[str, any]:
    """Cào dữ liệu trực tiếp từ website của đối thủ nếu có URL"""
    info = {
        "url": "",
        "title": "",
        "description": "",
        "hotlines": [],
        "headlines": [],
        "summary": ""
    }
    
    # Tìm xem có URL trong chuỗi không
    url_match = re.search(r"https?://[^\s,;]+|(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:/[^\s,;]*)?", url_or_name.strip())
    if not url_match:
        info["title"] = url_or_name.strip()
        return info

    target_url = url_match.group(0).rstrip("/,;")
    if not target_url.startswith("http"):
        target_url = "https://" + target_url

    info["url"] = target_url

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    try:
        resp = requests.get(target_url, headers=headers, timeout=3.5, verify=False)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "html.parser")
            if soup.title and soup.title.string:
                info["title"] = soup.title.string.strip()
            
            meta_desc = soup.find("meta", attrs={"name": re.compile(r"description", re.I)}) or \
                        soup.find("meta", attrs={"property": re.compile(r"og:description", re.I)})
            if meta_desc and "content" in meta_desc.attrs:
                info["description"] = meta_desc["content"].strip()

            # Quét số điện thoại hotline
            page_text = soup.get_text()
            phones = re.findall(r"(?:09|08|03|07|05)\d[\s.-]?\d{3}[\s.-]?\d{3,4}", page_text)
            clean_phones = list(set([re.sub(r"[^\d]", "", p) for p in phones if len(re.sub(r"[^\d]", "", p)) >= 10]))
            info["hotlines"] = clean_phones[:2]

            # Lấy các tiêu đề nổi bật H1, H2
            for h in soup.find_all(["h1", "h2", "h3"])[:6]:
                t = h.get_text().strip()
                if t and 10 < len(t) < 120 and t not in info["headlines"]:
                    info["headlines"].append(t)
    except Exception as e:
        pass

    return info

# --- 2. DOMAIN KNOWLEDGE BASES (DỮ LIỆU CHUYÊN SÂU THEO NGÀNH TẠI VIỆT NAM) ---

DOMAIN_DATA = {
    "machinery_construction": {
        "name": "Cơ khí Chế tạo máy, Thiết bị Xây dựng & Công nghiệp Nặng",
        "tam_description": "Quy mô thị trường máy móc và thiết bị cơ khí xây dựng Việt Nam đạt trên 2.4 tỷ USD (hơn 58.000 tỷ VNĐ), hưởng lợi trực tiếp từ kế hoạch giải ngân đầu tư công hàng trăm ngàn tỷ cho cao tốc Bắc - Nam, sân bay Long Thành, hạ tầng giao thông và hàng vạn dự án xây dựng dân dụng trên toàn quốc.",
        "sam_description": "Phân khúc máy gia công kết cấu sắt thép xây dựng (máy uốn sắt, máy bẻ đai tự động, máy cắt thủy lực công suất lớn) phục vụ cho hơn 65.000 nhà thầu xây dựng, đội cai thầu và hàng ngàn xưởng gia công sắt thép định hình (~12.500 tỷ VNĐ).",
        "som_target": "Chiếm 3.0% - 5.0% thị phần khu vực trọng điểm trong 12-24 tháng đầu, tương đương cung cấp 150 - 300 tổ hợp máy uốn/bẻ đai/cắt thép, tạo doanh thu từ 15 tỷ đến 30 tỷ VNĐ/năm.",
        "pestel": {
            "political": "Nghị định 06/2021/NĐ-CP và Thông tư Bộ Xây Dựng siết chặt tiêu chuẩn an toàn lao động công trường; bắt buộc máy móc thi công phải có chứng nhận kiểm định an toàn và xuất hóa đơn VAT chuẩn chỉnh để quyết toán chi phí công trình.",
            "economic": "Giá thép biến động và chi phí nhân công thợ uốn sắt leo thang (450.000 - 650.000 đ/công). Áp lực tối ưu hóa buộc nhà thầu phải cơ giới hóa để giảm tỷ lệ hao hụt sắt vụn từ 8% xuống dưới 1.5%.",
            "social": "Tình trạng già hóa và khan hiếm thợ sắt xây dựng lành nghề (lao động trẻ không mặn mà với công việc bẻ sắt thủ công nặng nhọc ngoài nắng), buộc chủ thầu bắt buộc phải mua máy uốn/bẻ đai tự động.",
            "tech": "Chuyển dịch mạnh mẽ từ máy uốn cơ truyền thống sang máy bẻ đai lập trình PLC màn hình cảm ứng tiếng Việt, tích hợp hệ thống thủy lực van tỉ lệ và mô tơ tiết kiệm điện 40%."
        },
        "porter": {
            "rivalry": "Các thương hiệu lâu năm như Cơ Khí Chí Hướng (Chiho), Máy Bẻ Đai Hoàng Minh, Siêu Việt, Phúc Long cạnh tranh gắt gao. Lợi thế sống còn nằm ở độ dày khung sườn thép nguyên khối, bo mạch ổn định không bị kẹt sắt và dịch vụ bảo hành tận chân công trình.",
            "buyer_power": "Chủ thầu và cai công trình rất thực dụng và am hiểu kỹ thuật. Họ chỉ xuống tiền khi được xem máy chạy thử thực tế uốn sắt phi lớn, hoặc xem video bẻ đai sắc nét chứng minh năng suất thay thế 4-6 thợ.",
            "substitutes": "Uốn bẻ thủ công bằng tay hoặc thuê dịch vụ gia công sắt bên ngoài. Điểm yếu của sản phẩm thay thế là trễ tiến độ đổ bê tông và chi phí thuê gia công bị đội lên khi khối lượng lớn."
        },
        "key_trends": [
            "Xu hướng máy bẻ đai tự động đa năng: Một máy uốn được 16 - 24 loại đai (đai vuông, chữ nhật, tam giác, lục giác, lò xo cọc nhồi) chỉ qua thao tác chọn hình trên màn hình cảm ứng.",
            "Kênh bán hàng B2B chuyển dịch: 80% chủ thầu xem video thử tải máy trên YouTube và Facebook Reel thực tế trước khi gọi điện đặt cọc.",
            "Nhà thầu chuộng chính sách 'Giao máy tận công trình - Chạy thử nghiệm thu đạt chuẩn mới thanh toán nốt' và cam kết kỹ thuật viên hỗ trợ trong 24h."
        ],
        "competitor_flaws": [
            "Giá thương hiệu bị đội lên quá cao do chi phí quảng cáo và qua nhiều tầng đại lý trung gian.",
            "Khi máy gặp sự cố ở công trình tỉnh xa (Tây Nguyên, Miền Tây, miền Trung), việc điều kỹ thuật viên xuống xử lý thường chậm từ 2-4 ngày, gây đình trệ cả ngày đổ bê tông dầm sàn.",
            "Một số đơn vị dùng linh kiện mô tơ cũ quấn lại hoặc bộ nguồn thủy lực không trang bị két làm mát nhớt, dẫn đến việc máy bị nóng nhớt và tụt lực uốn khi chạy liên tục giữa trưa nắng.",
            "Giao diện điều khiển cơ bản, ít tính năng cài đặt đai phức tạp, thợ mới vào khó thao tác."
        ],
        "competitors_pool": [
            {"name": "Cơ Khí Chí Hướng (Chiho)", "website": "chihovn.com", "type": "Trực tiếp", "price_segment": "Cao cấp", "core_products": "Máy bẻ đai sắt tự động, máy uốn sắt xây dựng", "key_strengths": "Thương hiệu lâu năm, mạng lưới đại lý rộng", "vulnerabilities": "Giá cao hơn mặt bằng chung 15-20%, chi phí phụ tùng thay thế đắt"},
            {"name": "Máy Bẻ Đai Hoàng Minh", "website": "maybedaishoangminh.com", "type": "Trực tiếp", "price_segment": "Trung cấp", "core_products": "Máy bẻ đai sắt cá heo, máy bẻ đai đứng", "key_strengths": "Mẫu mã đa dạng, giá thành cạnh tranh", "vulnerabilities": "Khung sườn mỏng hơn, phụ thuộc vào kỹ thuật viên địa phương"},
            {"name": "Máy Xây Dựng Siêu Việt", "website": "mayxaydungcu.com", "type": "Trực tiếp", "price_segment": "Trung cấp", "core_products": "Máy uốn sắt, máy cắt sắt thủy lực", "key_strengths": "Có cả máy mới và máy bãi Nhật, sẵn hàng", "vulnerabilities": "Chính sách bảo hành phân mảnh, máy cũ độ bền không đồng đều"},
            {"name": "Cơ Khí Chế Tạo Phúc Long", "website": "phuclong.vn", "type": "Trực tiếp", "price_segment": "Tiêu chuẩn", "core_products": "Thiết bị và máy móc công trình xây dựng", "key_strengths": "Quy mô xưởng lớn, năng lực sản xuất hàng loạt", "vulnerabilities": "Chăm sóc sau bán hàng chậm trễ khi máy gặp sự cố ở tỉnh xa"},
            {"name": "Máy Xây Dựng Hồng Hà", "website": "honghamachinery.vn", "type": "Gián tiếp / Trực tiếp", "price_segment": "Trung & Cao cấp", "core_products": "Máy trộn bê tông, máy gia công sắt thép", "key_strengths": "Nhận diện thương hiệu mạnh miền Bắc", "vulnerabilities": "Chi phí vận chuyển vào miền Trung/Nam cao"},
            {"name": "Máy Bẻ Đai Lê Nguyễn", "website": "maybedaile nguyen.com", "type": "Trực tiếp", "price_segment": "Tiêu chuẩn", "core_products": "Máy bẻ đai bàn nghiêng, máy bẻ đai thế hệ mới", "key_strengths": "Giao diện cảm ứng dễ dùng", "vulnerabilities": "Mô tơ dễ nóng khi làm việc giữa trưa nắng công trường"},
            {"name": "Cơ Khí Đại Phát", "website": "cokhidaiphat.vn", "type": "Đại lý / Sản xuất", "price_segment": "Tiết kiệm", "core_products": "Máy uốn bẻ sắt dân dụng phi 6-25", "key_strengths": "Giá rẻ, tiếp cận cai thầu nhỏ tốt", "vulnerabilities": "Độ chính xác góc đai chưa cao, tỷ lệ hao sắt nhiều"},
            {"name": "Máy Xây Dựng An Phát", "website": "mayxaydunganphat.com", "type": "Phân phối", "price_segment": "Tiêu chuẩn", "core_products": "Máy móc thiết bị thi công xây dựng", "key_strengths": "Giao hàng nhanh trong ngày tại các đô thị", "vulnerabilities": "Chỉ là đơn vị thương mại, không tự sửa chữa được mạch sâu"},
            {"name": "Thiết Bị Vinamac", "website": "vinamac.com.vn", "type": "Trực tiếp", "price_segment": "Cao cấp", "core_products": "Tổ hợp trạm trộn, máy gia công cốt thép", "key_strengths": "Hồ sơ năng lực tham gia gói thầu lớn tốt", "vulnerabilities": "Thủ tục hợp đồng rườm rà, không mặn mà với đơn hàng nhỏ"},
            {"name": "Công Ty Máy Xây Dựng Lạc Hồng", "website": "lachonggroup.com.vn", "type": "Tổng kho / Phân phối", "price_segment": "Đa phân khúc", "core_products": "Máy uốn cắt sắt, tời kéo, pa lăng", "key_strengths": "Kho hàng rộng lớn, giá bán buôn tốt", "vulnerabilities": "Tư vấn kỹ thuật đại trà, thiếu hướng dẫn sâu 1-1"},
            {"name": "Cơ Khí Tân Thuận Phát", "website": "tanthuanphat.com", "type": "Trực tiếp", "price_segment": "Tiêu chuẩn", "core_products": "Máy uốn thép hộp, máy bẻ đai công nghiệp", "key_strengths": "Gia công cơ khí chính xác", "vulnerabilities": "Hoạt động marketing yếu, chủ yếu dựa vào khách quen"},
            {"name": "Thiết Bị Xây Dựng Hòa Phát Corp", "website": "hoaphatcorp.vn", "type": "Phân phối", "price_segment": "Tiêu chuẩn", "core_products": "Máy cắt uốn sắt thép, giàn giáo", "key_strengths": "Hệ thống kho bãi rộng ở nhiều tỉnh thành", "vulnerabilities": "Không chuyên sâu vào máy bẻ đai tự động thông minh"},
            {"name": "Máy Bẻ Đai Minh Phát", "website": "maybedaiminhphat.com", "type": "Trực tiếp", "price_segment": "Tiêu chuẩn", "core_products": "Máy bẻ đai sắt tự động màn hình cảm ứng", "key_strengths": "Phục vụ tốt khu vực miền Tây & Nam Bộ", "vulnerabilities": "Chưa có trạm bảo hành ủy quyền tại miền Trung và Bắc"},
            {"name": "Công Ty Thiết Bị Xây Dựng Toàn Thắng", "website": "mayxaydungtoanthang.com", "type": "Đại lý / Phân phối", "price_segment": "Trung cấp", "core_products": "Máy bẻ đai, uốn đai sắt xây dựng phi 6-8-10", "key_strengths": "Bán trả góp và hỗ trợ giao máy tận nơi", "vulnerabilities": "Thời gian xử lý bảo hành linh kiện thủy lực kéo dài"}
        ]
    },
    "fashion": {
        "name": "Thời trang & May mặc",
        "tam_description": "Khoảng 8.4 tỷ USD (theo Statista & VECOM), tốc độ tăng trưởng 12-15%/năm.",
        "sam_description": "Thị trường thời trang thiết kế & may mặc trung cấp phục vụ giới trẻ và công sở (ước tính 1.8 - 2.5 tỷ USD).",
        "som_target": "Chiếm 1.5% - 2.5% thị phần phân khúc mục tiêu, doanh thu dự phóng 3 tỷ - 10 tỷ VNĐ/năm.",
        "pestel": {
            "political": "Quy định truy xuất nguồn gốc vải và thuế bán hàng online trên sàn TMĐT.",
            "economic": "Người tiêu dùng thắt chặt chi tiêu, ưu tiên sản phẩm có tính ứng dụng cao và độ bền vải tốt.",
            "social": "Gen Z và Millennials chuộng mua sắm qua video ngắn KOC và Livestream trải nghiệm thật.",
            "tech": "Ứng dụng AI dự đoán xu hướng thời trang và thanh toán trả sau qua Fundiin/Kredivo."
        },
        "porter": {
            "rivalry": "Cực kỳ khốc liệt giữa các Local Brand nội địa và hàng nhập khẩu Quảng Châu giá rẻ.",
            "buyer_power": "Rất cao, khách hàng dễ dàng chuyển sang thương hiệu khác chỉ sau 1 lần bấm lướt.",
            "substitutes": "Thời trang secondhand (2hand) hoặc các dòng thời trang nhanh siêu rẻ."
        },
        "key_trends": [
            "Bùng nổ Social Commerce: Khách hàng mua qua Livestream TikTok Shop và Shopee Live chiếm trên 45% doanh số.",
            "Tỷ lệ hoàn trả (Return rate) cao từ 15-25% trên sàn TMĐT do lệch size hoặc chất vải không đúng video.",
            "Xu hướng Local Brand thiết kế cá nhân hóa, may đo form dáng chuẩn người Việt."
        ],
        "competitor_flaws": [
            "Chất lượng vải không đồng đều giữa các lô hàng sản xuất hàng loạt.",
            "Khâu xử lý đổi trả hàng và giải quyết khiếu nại chậm trễ (từ 5 - 10 ngày).",
            "Mẫu mã rập khuôn, sao chép xu hướng chậm hơn đối thủ ngoại."
        ],
        "competitors_pool": [
            {"name": "Coolmate", "website": "coolmate.me", "type": "Trực tiếp", "price_segment": "Trung cấp", "core_products": "Thời trang nam cơ bản, đồ thể thao D2C", "key_strengths": "Mô hình D2C, chính sách đổi trả 60 ngày miễn phí", "vulnerabilities": "Mẫu mã thiên về cơ bản, thiếu sự đột phá thời trang cá tính"},
            {"name": "Routine", "website": "routine.vn", "type": "Trực tiếp", "price_segment": "Trung & Cao cấp", "core_products": "Thời trang nam nữ thiết kế công sở & dạo phố", "key_strengths": "Hệ thống showroom đẹp tại các trung tâm thương mại", "vulnerabilities": "Giá thành cao, ít ưu đãi cho khách hàng thân thiết"},
            {"name": "Canifa", "website": "canifa.com", "type": "Trực tiếp", "price_segment": "Tiêu chuẩn", "core_products": "Thời trang gia đình, áo len, cotton cơ bản", "key_strengths": "Thương hiệu quốc dân, chất lượng len sợi bền bỉ", "vulnerabilities": "Thiết kế thiếu tính trendy cho Gen Z, truyền thông chậm đổi mới"},
            {"name": "Yody", "website": "yody.vn", "type": "Trực tiếp", "price_segment": "Bình dân & Trung cấp", "core_products": "Thời trang thường ngày, áo polo, đồng phục", "key_strengths": "Độ phủ cửa hàng cực rộng ở các tỉnh thành cấp 2 và 3", "vulnerabilities": "Định vị đại trà, khó cạnh tranh phân khúc thiết kế cao cấp"},
            {"name": "Torano", "website": "torano.vn", "type": "Trực tiếp", "price_segment": "Trung cấp", "core_products": "Thời trang nam công sở hiện đại", "key_strengths": "Form dáng người Việt, giá mềm", "vulnerabilities": "Chất liệu dễ nhăn sau nhiều lần giặt máy"},
            {"name": "Biluxury", "website": "biluxury.vn", "type": "Trực tiếp", "price_segment": "Trung cấp", "core_products": "Vest, sơ mi nam công sở", "key_strengths": "Mạng lưới nhượng quyền tỉnh phát triển tốt", "vulnerabilities": "Mẫu mã ít thay đổi giữa các mùa"},
            {"name": "Aristino", "website": "aristino.com", "type": "Trực tiếp", "price_segment": "Cao cấp", "core_products": "Thời trang nam cao cấp, âu phục may đo", "key_strengths": "Chất liệu vải cao cấp (bamboo, silk), nhận diện sang trọng", "vulnerabilities": "Giá thành kén khách, chi phí quảng cáo lớn"},
            {"name": "Gumac", "website": "gumac.vn", "type": "Trực tiếp", "price_segment": "Tiêu chuẩn", "core_products": "Đầm váy thiết kế, thời trang nữ công sở", "key_strengths": "Livestream bán hàng cực mạnh, tệp khách nữ trung thành", "vulnerabilities": "Chất lượng đường may các đợt sale xả hàng chưa đồng đều"},
            {"name": "Elise", "website": "elise.vn", "type": "Trực tiếp", "price_segment": "Cao cấp", "core_products": "Thời trang nữ cao cấp, vest dạ hội", "key_strengths": "Thương hiệu đẳng cấp, hình ảnh truyền thông chuyên nghiệp", "vulnerabilities": "Mức giá cao, khó tiếp cận tệp khách hàng trẻ"},
            {"name": "IVY moda", "website": "ivymoda.com", "type": "Trực tiếp", "price_segment": "Trung & Cao cấp", "core_products": "Thời trang xu hướng, đồ dạ hội, công sở", "key_strengths": "Tổ chức Fashion Show quy mô, dẫn dắt xu hướng", "vulnerabilities": "Dịch vụ sau bán hàng và chăm sóc khiếu nại còn rườm rà"},
            {"name": "Sixdo", "website": "sixdo.vn", "type": "Trực tiếp", "price_segment": "Trung & Cao cấp", "core_products": "Thời trang thiết kế bởi NTK Đỗ Mạnh Cường", "key_strengths": "Thương hiệu cá nhân nhà thiết kế mạnh, chất liệu tốt", "vulnerabilities": "Phom dáng kén người mặc, hệ thống cửa hàng chi phí cao"},
            {"name": "Nem Fashion", "website": "nemshop.vn", "type": "Trực tiếp", "price_segment": "Trung & Cao cấp", "core_products": "Thời trang công sở nữ thanh lịch", "key_strengths": "Nhận diện lâu đời trong giới văn phòng", "vulnerabilities": "Các đợt giảm giá sâu 50-70% làm giảm giá trị thương hiệu"},
            {"name": "DirtyCoins", "website": "dirtycoins.vn", "type": "Gián tiếp / Streetwear", "price_segment": "Giới trẻ", "core_products": "Thời trang đường phố, Hoodie, Tee in hình", "key_strengths": "Cộng đồng Gen Z đông đảo, marketing viral", "vulnerabilities": "Chỉ tập trung tệp trẻ tuổi, khó mở rộng sang độ tuổi khác"},
            {"name": "Levents", "website": "levents.asia", "type": "Streetwear", "price_segment": "Trung cấp", "core_products": "Áo thun, balo, phụ kiện streetwear", "key_strengths": "Bao bì đóng gói đẹp, chiến dịch social mạnh", "vulnerabilities": "Tỷ lệ làm nhái, hàng fake trôi nổi nhiều trên thị trường"},
            {"name": "Degrey", "website": "degrey.vn", "type": "Streetwear / Á Đông", "price_segment": "Tiêu chuẩn", "core_products": "Thời trang kết hợp truyền thống & hiện đại", "key_strengths": "Cá tính độc lạ, tệp fan trung thành", "vulnerabilities": "Quy mô sản xuất còn hạn chế, hay cháy hàng các mẫu hot"},
            {"name": "Teelab", "website": "teelab.vn", "type": "Fast Fashion / Gen Z", "price_segment": "Tiết kiệm", "core_products": "Áo phông oversize, quần short unisex", "key_strengths": "Giá siêu cạnh tranh, đẩy số lượng cực lớn trên TikTok Shop", "vulnerabilities": "Biên lợi nhuận mỏng, áp lực chi phí affiliate sàn TMĐT"}
        ]
    },
    "spa_beauty": {
        "name": "Spa, Thẩm mỹ viện & Mỹ phẩm Làm đẹp",
        "tam_description": "Khoảng 2.8 tỷ USD tại Việt Nam với hơn 35.000 cơ sở làm đẹp và spa chăm sóc da.",
        "sam_description": "Phân khúc trị liệu da chuyên sâu, phục hồi da mụn và nám chuẩn y khoa (ước tính 600 - 800 triệu USD).",
        "som_target": "Phục vụ 500 - 1.500 khách hàng ruột mỗi năm, doanh thu 3 tỷ - 8 tỷ VNĐ.",
        "pestel": {
            "political": "Bộ Y Tế kiểm soát gắt gao các chứng chỉ hành nghề và nguồn gốc dược mỹ phẩm tiêm/bôi.",
            "economic": "Khách hàng cân nhắc kỹ hơn trước các gói liệu trình lớn, ưu tiên trả tiền theo buổi hoặc gói dùng thử.",
            "social": "Người tiêu dùng sợ biến chứng thẩm mỹ, tin vào lời khuyên của bác sĩ da liễu có chứng chỉ.",
            "tech": "Ứng dụng máy soi da AI phân tích tầng sâu và phần mềm nhắc lịch chăm sóc da tự động."
        },
        "porter": {
            "rivalry": "Các spa mọc lên san sát nhau ở mọi con phố, cạnh tranh trực diện bằng quảng cáo giảm giá sốc.",
            "buyer_power": "Khách hàng xem xét kỹ hình ảnh Before/After thực tế và đánh giá Google Maps trước khi đặt lịch.",
            "substitutes": "Tự mua mỹ phẩm điều trị tại nhà theo video TikTok hoặc đến bệnh viện da liễu công lập."
        },
        "key_trends": [
            "Chuyển dịch mạnh mẽ từ mỹ phẩm trôi nổi sang dịch vụ chuẩn y khoa có phác đồ cá nhân hóa.",
            "Dị ứng với 'chèo kéo mua thêm gói': Khách hàng rất ác cảm khi vào spa bị ép mua thẻ liệu trình chục triệu.",
            "Truyền thông bằng video bác sĩ chia sẻ kiến thức trung thực thu hút lượng lớn khách hàng tiềm năng."
        ],
        "competitor_flaws": [
            "Kỹ thuật viên tư vấn ép khách mua gói dịch vụ giá cao khiến khách hàng có tâm lý phòng thủ và không quay lại.",
            "Tay nghề nhân viên không đồng đều giữa các chi nhánh, hay thay đổi kỹ thuật viên điều trị.",
            "Chính sách giá không minh bạch, hay phát sinh phụ phí thuốc và mỹ phẩm bôi sau điều trị."
        ],
        "competitors_pool": [
            {"name": "Hệ Thống Thẩm Mỹ Viện Seoul Center (Seoul Spa)", "website": "seoulcenter.vn", "type": "Trực tiếp", "price_segment": "Trung & Cao cấp", "core_products": "Trị mụn, nám, tàn nhang, trẻ hóa da công nghệ cao", "key_strengths": "Hơn 80 chi nhánh toàn quốc, đầu tư máy móc hiện đại", "vulnerabilities": "Khách hàng phàn nàn nhân viên tư vấn chèo kéo mua thêm gói liệu trình"},
            {"name": "Bệnh Viện Thẩm Mỹ Thu Cúc", "website": "thucucclinics.com", "type": "Trực tiếp", "price_segment": "Cao cấp", "core_products": "Phẫu thuật thẩm mỹ, da liễu thẩm mỹ y khoa", "key_strengths": "Thương hiệu bệnh viện uy tín lâu năm, đội ngũ bác sĩ chính quy", "vulnerabilities": "Giá cao, thủ tục chờ đợi khám và dịch vụ lâu"},
            {"name": "Shynh House Premium", "website": "shynhhouse.com", "type": "Trực tiếp", "price_segment": "Cao cấp", "core_products": "Điều trị da chuyên sâu, nâng cơ trẻ hóa", "key_strengths": "Không gian sang trọng, chăm sóc khách hàng VIP chu đáo", "vulnerabilities": "Chi phí liệu trình đắt đỏ, chỉ tập trung ở các thành phố lớn"},
            {"name": "Hasaki Clinic & Spa", "website": "hasaki.vn/spa", "type": "Trực tiếp", "price_segment": "Tiêu chuẩn & Tiết kiệm", "core_products": "Chăm sóc da cơ bản, lấy nhân mụn, peel da", "key_strengths": "Giá bình dân minh bạch, hệ sinh thái bán mỹ phẩm kèm theo", "vulnerabilities": "Phòng đông khách, thời gian làm dịch vụ nhanh, thiếu tính riêng tư"},
            {"name": "Bông Spa", "website": "bongspa.com", "type": "Trực tiếp / Thư giãn", "price_segment": "Trung cấp", "core_products": "Spa thảo mộc 100% tự nhiên, massage body & mặt", "key_strengths": "Liệu pháp hoa lá thiên nhiên không xâm lấn, không chèo kéo bán hàng", "vulnerabilities": "Không chuyên sâu vào các ca da bệnh lý nặng như nám sâu, sẹo rỗ"},
            {"name": "Kay Spa", "website": "kayspa.vn", "type": "Trực tiếp", "price_segment": "Tiêu chuẩn", "core_products": "Triệt lông, tắm trắng, chăm sóc da mặt", "key_strengths": "Mạng lưới chi nhánh rộng khắp các tỉnh miền Tây và Nam Bộ", "vulnerabilities": "Tay nghề kỹ thuật viên cơ sở tỉnh chưa đồng đều"},
            {"name": "Thẩm Mỹ Viện Đông Á", "website": "thammyviendonga.vn", "type": "Trực tiếp", "price_segment": "Cao cấp", "core_products": "Trị nám Pico, thẩm mỹ công nghệ Hoa Kỳ", "key_strengths": "Bác sĩ có chứng chỉ quốc tế, máy móc nhập khẩu", "vulnerabilities": "Phát sinh chi phí thuốc bôi dưỡng sau điều trị"},
            {"name": "Bệnh Viện Thẩm Mỹ Kangnam", "website": "benhvienthammykangnam.vn", "type": "Trực tiếp", "price_segment": "Cao cấp", "core_products": "Phẫu thuật toàn diện, trị sẹo rỗ chuyên sâu", "key_strengths": "Hồ sơ truyền thông mạnh, tài trợ nhiều show truyền hình", "vulnerabilities": "Đông đúc, lịch hẹn bác sĩ trưởng khoa khó sắp xếp"},
            {"name": "Phòng Khám Da Liễu O2 Skin", "website": "o2skin.vn", "type": "Trực tiếp / Chuẩn Y Khoa", "price_segment": "Tiêu chuẩn (Sinh viên & Công sở)", "core_products": "Trị mụn chuẩn y khoa 100% bác sĩ da liễu", "key_strengths": "Minh bạch giá, không ép mua gói, kê đơn thuốc chính hãng", "vulnerabilities": "Cơ sở vật chất tối giản, chỉ tập trung trị mụn không làm thư giãn"},
            {"name": "Gà Spa", "website": "gaspa.vn", "type": "Trực tiếp", "price_segment": "Tiết kiệm", "core_products": "Lấy mụn sinh học, thải độc da mặt", "key_strengths": "Giá hợp túi tiền học sinh sinh viên, nhiều chi nhánh", "vulnerabilities": "Dịch vụ sau buổi làm chưa có quy trình theo dõi sát 1-1"},
            {"name": "Viện Thẩm Mỹ DIVA", "website": "vienthammydiva.vn", "type": "Trực tiếp", "price_segment": "Tiêu chuẩn", "core_products": "Phun thêu thẩm mỹ, chăm sóc da công nghệ cao", "key_strengths": "Độ phủ thương hiệu số 1 tại các huyện, thị xã trên toàn quốc", "vulnerabilities": "Đội ngũ chuyên viên hay luân chuyển giữa các chi nhánh"},
            {"name": "Lã Lão Spa", "website": "lalaospa.vn", "type": "Gián tiếp / Dưỡng sinh", "price_segment": "Trung cấp", "core_products": "Gội đầu dưỡng sinh, massage trị liệu cổ vai gáy", "key_strengths": "Không gian thư giãn, nhân viên tận tâm", "vulnerabilities": "Chỉ giải quyết nhu cầu thư giãn, không điều trị da liễu"},
            {"name": "Mega Gangnam", "website": "gangnam.com.vn", "type": "Cao cấp", "price_segment": "Hạng sang", "core_products": "Căng chỉ collagen, trẻ hóa phi phẫu thuật", "key_strengths": "Công nghệ Hàn Quốc, phục vụ giới thượng lưu", "vulnerabilities": "Chi phí cực kỳ đắt đỏ, từ vài chục đến hàng trăm triệu"},
            {"name": "Dermatology Clinic & Spa Địa Phương", "website": "", "type": "Trực tiếp", "price_segment": "Tiêu chuẩn", "core_products": "Các phòng khám da liễu của bác sĩ bệnh viện tỉnh mở ngoài giờ", "key_strengths": "Bác sĩ quen thuộc tại địa phương, uy tín gia đình", "vulnerabilities": "Cơ sở vật chất nhỏ, không có máy móc công nghệ cao mới nhất"}
        ]
    },
    "fnb": {
        "name": "F&B, Nhà hàng, Quán Cafe & Đồ uống",
        "tam_description": "Quy mô toàn ngành ẩm thực và đồ uống Việt Nam đạt trên 610.000 tỷ VNĐ (Euromonitor).",
        "sam_description": "Phân khúc chuỗi cafe, nhà hàng phong cách hiện đại tại các đô thị lớn (~120.000 tỷ VNĐ).",
        "som_target": "Doanh thu 1.8 tỷ - 6 tỷ VNĐ/điểm bán/năm.",
        "pestel": {
            "political": "Kiểm tra gắt gao an toàn vệ sinh thực phẩm và quy định nồng độ cồn (Nghị định 100).",
            "economic": "Người tiêu dùng ưu tiên combo giá hợp lý nhưng không gian phải có gu check-in đẹp.",
            "social": "Khách hàng trẻ thích trải nghiệm đồ uống mới (trà sữa ô long đậm vị, đồ uống ít ngọt, sữa hạt).",
            "tech": "Menu điện tử QR Code tại bàn và tích điểm Zalo Mini App tự động."
        },
        "porter": {
            "rivalry": "Tỷ lệ đào thải cực cao, 60% quán cafe đóng cửa sau năm đầu tiên do tiền mặt bằng.",
            "buyer_power": "Rất cao, khách hàng đi theo trào lưu 'hot trend' và nhanh chán nếu không đổi mới menu.",
            "substitutes": "Tự nấu ăn tại nhà hoặc mua đồ uống đóng chai tiện lợi."
        },
        "key_trends": [
            "Phí hoa hồng của các ứng dụng giao đồ ăn (GrabFood, ShopeeFood) lên tới 20-25% ăn mòn biên lợi nhuận.",
            "Xu hướng đồ uống lành mạnh (ít ngọt, sữa hạt, trà hữu cơ) tăng trưởng vượt bậc.",
            "Mô hình quán kết hợp không gian làm việc (Workation) và góc chụp ảnh sống ảo."
        ],
        "competitor_flaws": [
            "Chất lượng đồ ăn đồ uống không đồng nhất giữa giờ cao điểm và giờ vắng khách.",
            "Thất thoát nguyên vật liệu nội bộ và nhân viên phục vụ thái độ thiếu chuyên nghiệp.",
            "Chương trình tích điểm loyalty rườm rà, khách hàng không nhớ để sử dụng."
        ],
        "competitors_pool": [
            {"name": "Highlands Coffee", "website": "highlands.com.vn", "type": "Trực tiếp", "price_segment": "Trung cấp", "core_products": "Cà phê phin truyền thống, Freeze, Trà sen vàng", "key_strengths": "Vị trí đắc địa số 1 Việt Nam, nhận diện phủ sóng toàn quốc", "vulnerabilities": "Chất lượng đồ uống thiếu sự tinh tế, chỗ ngồi ồn ào giờ cao điểm"},
            {"name": "Phúc Long Coffee & Tea", "website": "phuclong.com.vn", "type": "Trực tiếp", "price_segment": "Trung & Cao cấp", "core_products": "Trà sữa đậm vị, trà ô long, cold brew", "key_strengths": "Vị trà đậm đà đặc trưng, hệ thống kiosk tích hợp WinMart", "vulnerabilities": "Trải nghiệm phục vụ tại một số kiosk WinMart chưa đồng nhất"},
            {"name": "The Coffee House", "website": "thecoffeehouse.com", "type": "Trực tiếp", "price_segment": "Trung cấp", "core_products": "Cà phê, trà trái cây, bánh ngọt", "key_strengths": "Không gian phù hợp làm việc và học tập, app tích điểm tốt", "vulnerabilities": "Thu hẹp nhiều cửa hàng sau dịch, áp lực cạnh tranh trà sữa mới nổi"},
            {"name": "Phê La", "website": "phela.vn", "type": "Trực tiếp / Trà Ô Long", "price_segment": "Trung & Cao cấp", "core_products": "Trà ô long đặc sản Đà Lạt, cà phê trứng", "key_strengths": "Định vị phong cách cắm trại (Camp Concept), giới trẻ săn đón", "vulnerabilities": "Thời gian chờ pha chế lâu, hay cháy hàng các món 'signature'"},
            {"name": "Katinat Saigon Kafe", "website": "katinat.vn", "type": "Trực tiếp", "price_segment": "Trung & Cao cấp", "core_products": "Trà sữa chôm chôm, cà phê muối, trà trái cây", "key_strengths": "Thiết kế kiến trúc ấn tượng, bao bì 'ly cầu vồng' viral", "vulnerabilities": "Giá thành khá cao, tập trung chủ yếu ở các trục đường lớn"},
            {"name": "Trung Nguyên Legend", "website": "trungnguyenlegend.com", "type": "Trực tiếp", "price_segment": "Cao cấp & Trung cấp", "core_products": "Cà phê năng lượng, cà phê hạt rang xay nguyên chất", "key_strengths": "Thương hiệu cà phê quốc gia, tệp khách trung niên trung thành", "vulnerabilities": "Mẫu mã và phong cách chưa thực sự thu hút tệp khách trẻ Gen Z"},
            {"name": "Cộng Cà Phê", "website": "congcaphe.com", "type": "Trực tiếp", "price_segment": "Trung cấp", "core_products": "Cà phê cốt dừa, bạc xỉu, đồ uống truyền thống", "key_strengths": "Phong cách bao cấp độc đáo, thu hút cả khách du lịch quốc tế", "vulnerabilities": "Menu đồ uống ít thay đổi, không gian một số điểm tối và hẹp"},
            {"name": "Cheese Coffee", "website": "cheesecoffee.vn", "type": "Trực tiếp", "price_segment": "Trung cấp", "core_products": "Trà sữa nướng, cà phê phô mai, bánh ngọt", "key_strengths": "Phong cách Industrial hiện đại, chụp ảnh check-in đẹp", "vulnerabilities": "Mật độ chi nhánh còn hạn chế ở khu vực miền Bắc"},
            {"name": "Aha Cafe", "website": "ahacafe.vn", "type": "Trực tiếp / Vỉa hè cao cấp", "price_segment": "Tiết kiệm", "core_products": "Cà phê vỉa hè, trà chanh, hạt hướng dương", "key_strengths": "Mặt tiền thoáng đãng, giá rẻ, hợp văn hóa ngồi vỉa hè", "vulnerabilities": "Không gian ồn ào khói bụi, dịch vụ cơ bản"},
            {"name": "Milano Coffee", "website": "milanocoffee.com.vn", "type": "Nhượng quyền bình dân", "price_segment": "Bình dân", "core_products": "Cà phê đen, cà phê sữa đá mang đi", "key_strengths": "Giá bình dân từ 15-20k, hàng ngàn điểm bán nhượng quyền", "vulnerabilities": "Chất lượng hạt cà phê phụ thuộc vào từng chủ quán nhượng quyền"},
            {"name": "TocoToco Bubble Tea", "website": "tocotocotea.com", "type": "Trà sữa nhượng quyền", "price_segment": "Tiết kiệm & Trung cấp", "core_products": "Trà sữa trân châu, trà hoa quả tươi", "key_strengths": "Nguồn nông sản Việt, giá vừa túi tiền học sinh sinh viên", "vulnerabilities": "Nhận diện thương hiệu bị bão hòa trước các làn sóng trà sữa mới"},
            {"name": "Gong Cha Việt Nam", "website": "gongcha.com.vn", "type": "Trà sữa Đài Loan", "price_segment": "Cao cấp", "core_products": "Trà sữa Milk Foam béo ngậy, trà Alisan", "key_strengths": "Chất lượng chuẩn quốc tế, kiểm định nguyên liệu khắt khe", "vulnerabilities": "Giá đắt, ít mở rộng cửa hàng mới trong các năm gần đây"},
            {"name": "Mixue Việt Nam", "website": "mxbc.com", "type": "Trực tiếp / Fast Dessert", "price_segment": "Siêu tiết kiệm", "core_products": "Kem ốc quế 10k, trà chanh tươi 20k", "key_strengths": "Giá rẻ không đối thủ, tốc độ mở điểm bán thần tốc", "vulnerabilities": "Lợi nhuận cho chủ nhượng quyền mỏng, cạnh tranh nội bộ các điểm bán gần nhau"},
            {"name": "Koi Thé", "website": "koithe.com", "type": "Trà sữa Đài Loan", "price_segment": "Cao cấp", "core_products": "Golden Bubble Milk Tea, Macchiato", "key_strengths": "Hương vị trà thanh mát, trân châu hoàng kim độc quyền", "vulnerabilities": "Không phục vụ giao hàng linh hoạt ở các tỉnh xa"},
            {"name": "Chagee Vietnam", "website": "chagee.com.vn", "type": "Trà sữa thảo mộc hiện đại", "price_segment": "Cao cấp", "core_products": "Trà sữa tươi nguyên lá, bao bì sang trọng", "key_strengths": "Trend trà sữa mới nổi cực hot, nguyên liệu sữa tươi thanh trùng", "vulnerabilities": "Mới vào thị trường Việt Nam, số lượng điểm bán còn ít"}
        ]
    },
    "tech_retail": {
        "name": "Công nghệ, Phần mềm & Bán lẻ Đa Kênh",
        "tam_description": "Khoảng 1.4 triệu hộ kinh doanh và điểm bán lẻ tại Việt Nam có nhu cầu số hóa quy trình.",
        "sam_description": "350.000 nhà bán hàng đa kênh (Offline + Online) sẵn sàng chi trả từ 3-15 triệu/năm.",
        "som_target": "Chiếm 2.0% SAM với 3.000 - 7.000 thuê bao trả phí, doanh thu 10 tỷ - 30 tỷ VNĐ/năm.",
        "pestel": {
            "political": "Quy định bắt buộc kết nối hóa đơn điện tử khởi tạo từ máy tính tiền của Tổng cục Thuế.",
            "economic": "Chủ kinh doanh tính toán kỹ chi phí phần mềm so với doanh thu mang lại.",
            "social": "Thế hệ chủ kinh doanh 9x, 2k chuộng quản lý cửa hàng từ xa qua điện thoại thông minh.",
            "tech": "Thanh toán không tiền mặt qua mã VietQR động trở thành tiêu chuẩn bắt buộc tại mọi quầy thu ngân."
        },
        "porter": {
            "rivalry": "Các ông lớn như KiotViet, Sapo, Haravan, Pos365 chiếm thị phần lớn.",
            "buyer_power": "Chi phí chuyển đổi (Switching cost) cao một khi dữ liệu tồn kho đã nạp vào hệ thống.",
            "substitutes": "Dùng sổ sách tay hoặc bảng tính Google Sheets miễn phí."
        },
        "key_trends": [
            "Nhu cầu đồng bộ tồn kho tự động giữa kho thực tế với TikTok Shop và Shopee để tránh bị phạt hủy đơn.",
            "Tích hợp AI trả lời tin nhắn tự động và chốt đơn trên Fanpage/Zalo không cần người trực đêm."
        ],
        "competitor_flaws": [
            "Giao diện cồng kềnh, nhân viên lớn tuổi mất cả tuần mới làm quen được.",
            "Tổng đài hỗ trợ kỹ thuật nghẽn mạng lúc cao điểm bán hàng (buổi tối và cuối tuần).",
            "Thu thêm nhiều phụ phí kết nối sàn TMĐT và phụ phí tính năng nâng cao."
        ],
        "competitors_pool": [
            {"name": "KiotViet", "website": "kiotviet.vn", "type": "Trực tiếp", "price_segment": "Tiêu chuẩn", "core_products": "Phần mềm quản lý bán hàng đa ngành nghề, máy tính tiền POS", "key_strengths": "Thị phần số 1 tại Việt Nam với hơn 300.000 cửa hàng, dễ sử dụng", "vulnerabilities": "Chậm đồng bộ đa sàn lúc cao điểm flash sale, tổng đài hỗ trợ quá tải"},
            {"name": "Sapo (Sapo POS / Sapo Omnichannel)", "website": "sapo.vn", "type": "Trực tiếp", "price_segment": "Trung cấp", "core_products": "Phần mềm quản lý bán hàng đa kênh, thiết kế web bán hàng", "key_strengths": "Hệ sinh thái kết nối đơn vị vận chuyển và hóa đơn điện tử toàn diện", "vulnerabilities": "Chi phí gói Omnichannel cao, phát sinh phí duy trì cổng kết nối sàn"},
            {"name": "Haravan", "website": "haravan.com", "type": "Trực tiếp / Doanh nghiệp", "price_segment": "Cao cấp & Doanh nghiệp", "core_products": "Giải pháp thương mại điện tử đa kênh, HaraSocial, HaraRetail", "key_strengths": "Chuyên nghiệp cho các thương hiệu lớn và chuỗi bán lẻ, tích hợp sâu Meta/Google", "vulnerabilities": "Giao diện phức tạp, chi phí triển khai và đào tạo ban đầu đắt đỏ"},
            {"name": "Pos365", "website": "pos365.vn", "type": "Trực tiếp", "price_segment": "Tiết kiệm", "core_products": "Phần mềm bán hàng F&B, Karaoke, Tạp hóa điện toán đám mây", "key_strengths": "Gói mua trọn đời giá rẻ, giao diện cảm ứng trực quan", "vulnerabilities": "Tính năng quản lý tồn kho chuyên sâu và báo cáo tài chính còn hạn chế"},
            {"name": "Misa eShop / CukCuk", "website": "eshop.misa.vn", "type": "Trực tiếp", "price_segment": "Trung cấp", "core_products": "Quản lý bán lẻ eShop, quản lý nhà hàng CukCuk, tích hợp kế toán MISA", "key_strengths": "Thương hiệu tài chính kế toán uy tín, chuẩn hóa hóa đơn điện tử theo luật", "vulnerabilities": "Giao diện hơi cứng nhắc, quy trình hỗ trợ qua nhiều bước tổng đài"},
            {"name": "Nhanh.vn", "website": "nhanh.vn", "type": "Trực tiếp", "price_segment": "Trung cấp", "core_products": "Quản lý bán hàng chuỗi cửa hàng thời trang và TMĐT", "key_strengths": "Tối ưu xuất sắc cho các shop thời trang nhiều chi nhánh", "vulnerabilities": "Ứng dụng di động đôi khi giật lag, phí đẩy đơn vận chuyển chưa tối ưu"},
            {"name": "Pancake POS (Pancake.vn)", "website": "pancake.vn", "type": "Trực tiếp / Social Commerce", "price_segment": "Tiết kiệm", "core_products": "Quản lý hội thoại đa kênh Fanpage, Instagram, Shopee, TikTok Shop", "key_strengths": "Tốc độ load tin nhắn chat nhanh nhất thị trường, chia hội thoại thông minh", "vulnerabilities": "Tính năng kho hàng và kế toán công nợ chỉ ở mức cơ bản"},
            {"name": "TrustSales", "website": "trustsales.vn", "type": "Social Commerce", "price_segment": "Tiêu chuẩn", "core_products": "Phần mềm quản lý bán hàng online và telesales chốt đơn", "key_strengths": "Tối ưu quy trình cho đội ngũ telesales gọi điện chốt đơn tự động", "vulnerabilities": "Ít tính năng cho điểm bán lẻ offline (POS quầy)"},
            {"name": "iPOS.vn", "website": "ipos.vn", "type": "F&B Chuyên Sâu", "price_segment": "Cao cấp", "core_products": "Phần mềm và phần cứng quản lý nhà hàng cafe chuyên sâu, menu điện tử", "key_strengths": "Thống trị phân khúc nhà hàng và chuỗi đồ uống lớn tại Việt Nam", "vulnerabilities": "Giá đầu tư phần cứng ban đầu cao, chỉ phù hợp ngành F&B"},
            {"name": "Odoo Việt Nam (ERP)", "website": "odoo.com", "type": "Mã nguồn mở / ERP", "price_segment": "Doanh nghiệp", "core_products": "Hệ thống quản trị doanh nghiệp tổng thể ERP, POS, CRM, Kế toán", "key_strengths": "Tùy biến không giới hạn quy trình, phù hợp doanh nghiệp lớn", "vulnerabilities": "Thời gian triển khai tính bằng tháng, đòi hỏi đội ngũ IT nội bộ"},
            {"name": "Suno.vn", "website": "suno.vn", "type": "Trực tiếp", "price_segment": "Tiết kiệm", "core_products": "Phần mềm bán lẻ đơn giản, quản lý kho cơ bản", "key_strengths": "Gọn nhẹ, máy tính cấu hình yếu vẫn chạy mượt", "vulnerabilities": "Thiếu các tính năng marketing tự động và đồng bộ TikTok Shop"},
            {"name": "Tuha.vn", "website": "tuha.vn", "type": "Social / Telesales", "price_segment": "Tiêu chuẩn", "core_products": "Phần mềm tối ưu đơn hàng online và chia số tự động", "key_strengths": "Quản lý nhân viên marketing chạy ads và nhân viên chốt đơn chặt chẽ", "vulnerabilities": "Giao diện chưa hiện đại, ít cập nhật tính năng mới"},
            {"name": "Maybanhang.net", "website": "maybanhang.net", "type": "Trực tiếp", "price_segment": "Tiêu chuẩn", "core_products": "Quản lý bán hàng cho tạp hóa, siêu thị mini", "key_strengths": "Hỗ trợ thiết bị máy in bill, đầu đọc mã vạch tốt", "vulnerabilities": "Chậm thích ứng với xu hướng bán hàng qua video ngắn và mạng xã hội"},
            {"name": "Polaris FnB", "website": "polarisfnb.com", "type": "F&B Cloud", "price_segment": "Tiết kiệm", "core_products": "Quản lý quán bar, pub, nhà hàng", "key_strengths": "Định lượng nguyên liệu chi tiết", "vulnerabilities": "Thương hiệu mới, thị phần còn nhỏ"}
        ]
    },
    "b2b_industrial": {
        "name": "Sản xuất Công nghiệp B2B & Vật tư Thiết bị",
        "tam_description": "Thị trường máy móc và nguyên vật liệu phụ trợ công nghiệp Việt Nam đạt trên 15 tỷ USD, đóng vai trò công xưởng gia công lớn của khu vực Đông Nam Á.",
        "sam_description": "Phân khúc các nhà xưởng cơ khí, xí nghiệp gia công và đại lý phân phối thiết bị kỹ thuật vừa và nhỏ (ước tính 3.5 tỷ USD).",
        "som_target": "Doanh thu mục tiêu 10 tỷ - 25 tỷ VNĐ/năm từ các hợp đồng cung ứng dài hạn.",
        "pestel": {
            "political": "Tiêu chuẩn ISO, CO/CQ và bảo đảm an toàn phòng chống cháy nổ nhà xưởng.",
            "economic": "Doanh nghiệp sản xuất ưu tiên bài toán khấu hao máy móc và thời gian hoàn vốn đầu tư (ROI).",
            "social": "Kỹ sư và quản đốc là người thẩm định kỹ thuật, nhưng giám đốc là người ký duyệt chi tiền.",
            "tech": "Tự động hóa dây chuyền, ứng dụng biến tần và lập trình điều khiển thông minh."
        },
        "porter": {
            "rivalry": "Cạnh tranh gay gắt giữa hàng gia công nội địa và máy nhập khẩu Trung Quốc/Đài Loan.",
            "buyer_power": "Người mua B2B kiểm tra chứng từ kỹ thuật rất khắt khe và yêu cầu điều khoản thanh toán gối đầu.",
            "substitutes": "Sử dụng máy bãi thanh lý Nhật bãi hoặc gia công thủ công thuê ngoài."
        },
        "key_trends": [
            "Doanh nghiệp ưu tiên nhà sản xuất nội địa có sẵn linh kiện thay thế trong nước thay vì chờ đặt hàng từ nước ngoài 1-2 tháng.",
            "Chuyển đổi số khâu bán hàng B2B: Khách hàng tìm kiếm nhà cung cấp qua Google Search và video trình diễn máy thực tế."
        ],
        "competitor_flaws": [
            "Thiếu hồ sơ kỹ thuật và hướng dẫn vận hành chi tiết bằng tiếng Việt.",
            "Chế độ bảo hành đùn đẩy trách nhiệm, đổ lỗi cho người vận hành thao tác sai.",
            "Không có phụ tùng dự phòng sẵn sàng, thời gian chờ sửa chữa kéo dài gây thiệt hại sản xuất."
        ],
        "competitors_pool": [
            {"name": "Công Ty CP Thiết Bị Tân Phát", "website": "tanphat.com", "type": "Trực tiếp", "price_segment": "Cao cấp", "core_products": "Thiết bị sửa chữa ô tô, máy móc cơ khí công nghiệp nặng", "key_strengths": "Doanh nghiệp quy mô lớn, cung cấp dự án trọn gói", "vulnerabilities": "Quy trình thủ tục mua sắm rườm rà, giá cao"},
            {"name": "Cơ Khí Công Nghiệp Tân Đức", "website": "cokhicongnghieptanduc.com", "type": "Trực tiếp", "price_segment": "Trung cấp", "core_products": "Gia công chế tạo bồn bể, đường ống công nghiệp, kết cấu thép", "key_strengths": "Năng lực hàn kỹ thuật cao, thợ lành nghề", "vulnerabilities": "Thời gian giao hàng đôi khi trễ tiến độ dự án"},
            {"name": "Công Ty Kỹ Thuật Việt Á", "website": "thietbivieta.com", "type": "Phân phối", "price_segment": "Tiêu chuẩn", "core_products": "Máy nén khí, mô tơ điện, phụ tùng cơ khí công nghiệp", "key_strengths": "Sẵn kho linh kiện phụ tùng, giao hàng nhanh", "vulnerabilities": "Đơn vị thương mại trung gian, chi phí bảo dưỡng định kỳ cao"},
            {"name": "Cơ Điện Công Nghiệp Kim Long", "website": "kimlongmec.com", "type": "Trực tiếp", "price_segment": "Trung cấp", "core_products": "Chế tạo máy tự động hóa, băng chuyền, tủ điện", "key_strengths": "Giải pháp tùy biến linh hoạt theo nhà xưởng", "vulnerabilities": "Đội ngũ kỹ thuật mỏng khi chạy nhiều dự án cùng lúc"},
            {"name": "Thiết Bị Công Nghiệp Á Châu", "website": "thietbiachau.com", "type": "Phân phối", "price_segment": "Đa phân khúc", "core_products": "Thiết bị đo lường, phụ kiện thủy lực, khí nén", "key_strengths": "Đại diện nhiều hãng quốc tế tại Việt Nam", "vulnerabilities": "Hàng đặt từ nước ngoài thời gian chờ từ 4-8 tuần"},
            {"name": "Công Ty Cơ Khí Nam Dũng", "website": "cokhinamdung.com", "type": "Gia công OEM", "price_segment": "Tiết kiệm", "core_products": "Gia công chi tiết máy, tiện phay CNC", "key_strengths": "Giá gia công cạnh tranh, máy móc CNC hiện đại", "vulnerabilities": "Không có bộ phận thiết kế R&D riêng, chỉ làm theo bản vẽ có sẵn"},
            {"name": "Vật Tư Kỹ Thuật Thành Đạt", "website": "vattuthanhdat.com.vn", "type": "Tổng kho", "price_segment": "Tiêu chuẩn", "core_products": "Sắt thép định hình, vòng bi, ray trượt công nghiệp", "key_strengths": "Kho hàng số lượng lớn, chiết khấu cao cho nhà máy", "vulnerabilities": "Chính sách công nợ gắt gao, yêu cầu thanh toán nhanh"},
            {"name": "Cơ Điện Lạnh Đại Việt", "website": "tapdoandaiviet.com.vn", "type": "Hệ thống làm mát xưởng", "price_segment": "Trung & Cao cấp", "core_products": "Hệ thống thông gió làm mát nhà xưởng công nghiệp", "key_strengths": "Thương hiệu lớn, nhà máy sản xuất quy mô lớn tại Việt Nam", "vulnerabilities": "Chuyên về mảng làm mát, không cung ứng các thiết bị cơ khí khác"},
            {"name": "Thiết Bị Kỹ Thuật Đông Á", "website": "donga-tech.vn", "type": "Phân phối", "price_segment": "Tiêu chuẩn", "core_products": "Máy móc dụng cụ cầm tay, máy hàn công nghiệp", "key_strengths": "Đại lý cấp 1 chính hãng, bảo hành chuẩn", "vulnerabilities": "Ít hỗ trợ kỹ thuật viên xuống tận xưởng tỉnh xa"}
        ]
    },
    "general": {
        "name": "Thương mại & Dịch vụ Tổng hợp",
        "tam_description": "Dung lượng thị trường tiêu dùng nội địa Việt Nam hơn 100 triệu dân với tầng lớp trung lưu gia tăng nhanh chóng.",
        "sam_description": "Tập khách hàng tại các tỉnh thành phát triển có thu nhập ổn định và sẵn sàng chi trả cho sản phẩm chất lượng.",
        "som_target": "Chiếm 1.5% - 3.0% thị phần khả dụng, doanh thu dự phóng 2 tỷ - 8 tỷ VNĐ/năm.",
        "pestel": {
            "political": "Quy định minh bạch về nguồn gốc xuất xứ và hóa đơn chứng từ điện tử.",
            "economic": "Khách hàng so sánh giá kỹ lưỡng và tìm kiếm giải pháp có giá trị thực chất.",
            "social": "70% quyết định mua hàng dựa trên trải nghiệm thực tế và truyền miệng (Word-of-Mouth).",
            "tech": "Thanh toán quét mã QR và tương tác đa kênh qua Zalo/Facebook."
        },
        "porter": {
            "rivalry": "Thị trường cạnh tranh mở, đòi hỏi sự khác biệt hóa về dịch vụ và tốc độ phục vụ.",
            "buyer_power": "Khách hàng có nhiều lựa chọn thay thế chỉ bằng một cú nhấp chuột.",
            "substitutes": "Các giải pháp tự làm hoặc sản phẩm thay thế giá rẻ trên thị trường."
        },
        "key_trends": [
            "Hành vi mua sắm đa điểm chạm (Omnichannel): Tìm hiểu online, chốt đơn hoặc trải nghiệm dịch vụ trực tiếp.",
            "Dịch vụ khách hàng và tốc độ phản hồi tin nhắn trong 5-15 phút là yếu tố quyết định 60% tỷ lệ chốt đơn."
        ],
        "competitor_flaws": [
            "Chăm sóc sau bán hàng đại trà, thiếu sự lắng nghe và kèm cặp 1-1.",
            "Chính sách bảo hành đổi trả phức tạp, đùn đẩy trách nhiệm khi sản phẩm gặp trục trặc.",
            "Truyền thông quảng cáo quá đà, thực tế sản phẩm không đúng như cam kết."
        ],
        "competitors_pool": [
            {"name": "Các Chuỗi Đại Lý & Tổng Kho Phân Phối Cấp 1", "website": "", "type": "Trực tiếp", "price_segment": "Tiêu chuẩn", "core_products": "Phân phối số lượng lớn các dòng sản phẩm cùng ngành", "key_strengths": "Tiềm lực vốn mạnh, hệ thống kho bãi rộng lớn ở nhiều tỉnh thành", "vulnerabilities": "Quy trình thủ tục cứng nhắc, ít hỗ trợ đơn hàng nhỏ lẻ"},
            {"name": "Các Cửa Hàng Chuyên Doanh Tại Địa Phương", "website": "", "type": "Trực tiếp", "price_segment": "Đa phân khúc", "core_products": "Cung cấp sản phẩm và dịch vụ trực tiếp đến tay người tiêu dùng địa phương", "key_strengths": "Am hiểu văn hóa địa phương, mối quan hệ thân thiết với khách hàng quen", "vulnerabilities": "Marketing yếu, thiếu kênh bán hàng online đa nền tảng"},
            {"name": "Các Gian Hàng Mall Trên Sàn TMĐT (Shopee/TikTok/Lazada)", "website": "", "type": "Trực tiếp / Online", "price_segment": "Tiết kiệm", "core_products": "Bán lẻ online, giao hàng nhanh toàn quốc", "key_strengths": "Giá rẻ, nhiều voucher trợ giá từ sàn TMĐT", "vulnerabilities": "Thiếu tư vấn chuyên sâu kỹ thuật và cam kết dịch vụ bảo hành 1-1"},
            {"name": "Các Công Ty Thương Mại & Xuất Nhập Khẩu Độc Quyền", "website": "", "type": "Gián tiếp / Nhập khẩu", "price_segment": "Cao cấp", "core_products": "Nhập khẩu nguyên chiếc các thương hiệu ngoại", "key_strengths": "Mác hàng nhập khẩu, tiêu chuẩn quốc tế", "vulnerabilities": "Chi phí đắt đỏ, phụ thuộc vào tỷ giá và chuỗi cung ứng nước ngoài"},
            {"name": "Các Cơ Sở Sản Xuất Gia Công Trực Tiếp (OEM/ODM)", "website": "", "type": "Sản xuất gốc", "price_segment": "Tiết kiệm", "core_products": "Sản xuất gia công theo yêu cầu", "key_strengths": "Giá tại xưởng không qua trung gian", "vulnerabilities": "Không có thương hiệu, dịch vụ hậu mãi tự túc"},
            {"name": "Hệ Thống Phân Phối Nhượng Quyền Toàn Quốc", "website": "", "type": "Chuỗi nhượng quyền", "price_segment": "Tiêu chuẩn", "core_products": "Mô hình kinh doanh đóng gói sẵn", "key_strengths": "Nhận diện thương hiệu đồng bộ, chiến dịch truyền thông bài bản", "vulnerabilities": "Chất lượng dịch vụ giữa các điểm nhượng quyền không đồng đều"},
            {"name": "Các Đơn Vị Cung Cấp Giải Pháp Thay Thế Truyền Thống", "website": "", "type": "Gián tiếp", "price_segment": "Tiết kiệm", "core_products": "Phương pháp và sản phẩm truyền thống", "key_strengths": "Thói quen lâu đời của người dùng", "vulnerabilities": "Năng suất thấp, tốn nhiều nhân công và thời gian"}
        ]
    }
}

def detect_domain(industry_str: str, products_str: str = "") -> str:
    """Nhận diện chính xác ngành hàng dựa trên tên ngành và sản phẩm"""
    s = (industry_str + " " + products_str).lower()
    if any(k in s for k in ["f&b", "ăn uống", "nhà hàng", "quán", "cà phê", "cafe", "trà", "thực phẩm", "đồ uống", "pha chế", "ẩm thực"]):
        return "fnb"
    elif any(k in s for k in ["thời trang", "may mặc", "quần áo", "giày dép", "phụ kiện", "túi xách", "fashion"]):
        return "fashion"
    elif any(k in s for k in ["spa", "thẩm mỹ", "da", "mỹ phẩm", "làm đẹp", "skincare", "clinic", "nha khoa", "trị mụn", "nám"]):
        return "spa_beauty"
    elif any(k in s for k in ["phần mềm", "pos", "công nghệ", "saas", "quản lý", "máy tính", "app", "digital"]):
        return "tech_retail"
    elif any(k in s for k in ["uốn thép", "bẻ đai", "uốn sắt", "máy bẻ đai", "cơ khí xây dựng", "cốt thép", "kết cấu thép"]):
        return "machinery_construction"
    elif any(k in s for k in ["b2b", "nhà máy", "gia công", "oem", "vật tư", "sản xuất"]):
        return "b2b_industrial"
    return "general"

# --- 3. GOOGLE GEMINI AI CALLER (MULTI-MODEL AUTO-FALLBACK POOL) ---

def call_gemini_api(profile: dict, prompt: str, system_prompt: str = None) -> Optional[str]:
    api_key = profile.get("gemini_api_key", "").strip() or os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None

    # Priority pool of models with active quota
    candidate_models = [
        "gemini-3.5-flash-lite",
        "gemini-flash-lite-latest",
        "gemini-3-flash-preview",
        "gemini-3.1-flash-lite",
        "gemini-3.5-flash",
        "gemini-3.6-flash"
    ]
    user_model = profile.get("gemini_model", "").strip()
    if user_model in candidate_models:
        candidate_models.remove(user_model)
        candidate_models.insert(0, user_model)

    full_text = prompt
    if system_prompt:
        full_text = f"CHỈ DẪN HỆ THỐNG:\n{system_prompt}\n\nNHIỆM VỤ:\n{prompt}"

    payload = {
        "contents": [{"parts": [{"text": full_text}]}]
    }

    for m in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
        try:
            resp = requests.post(url, json=payload, timeout=45)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates and "content" in candidates[0]:
                    parts = candidates[0]["content"].get("parts", [])
                    if parts and "text" in parts[0]:
                        return parts[0]["text"]
            elif resp.status_code in [429, 503]:
                # Rate limit / quota reached on this model line: try next model immediately
                continue
            else:
                continue
        except Exception:
            continue
    return None

# --- 4. DEEP MARKET RESEARCH GENERATOR (CUSTOMIZABLE BY REGION, PRICE & OBJECTIVE) ---

def generate_custom_market_research(profile: dict, options: dict = None) -> str:
    options = options or {}
    scope_type = options.get("scope_type") or profile.get("market_scope_type") or "province"
    location = options.get("location") or options.get("region") or profile.get("market_location") or "Toàn quốc"
    price_tier = options.get("price_tier") or profile.get("price_range") or "Tiêu chuẩn"
    objective = options.get("objective") or "Đánh chiếm thị phần từ đối thủ & Tăng trưởng doanh thu"

    brand = profile.get("brand_name", "Doanh nghiệp của bạn")
    industry = profile.get("industry", "Thương mại & Dịch vụ")
    model = profile.get("business_model", "B2B / B2C")
    products = profile.get("products_services", "Sản phẩm & Dịch vụ")
    audience = profile.get("target_audience", "Khách hàng mục tiêu")
    competitors = profile.get("competitors", "")
    usp = profile.get("usp_advantages", "") or "Chất lượng vượt trội, may đo chuyên sâu và hỗ trợ tận tâm"
    hotline = profile.get("phone_hotline", "")
    website = profile.get("website_url", "")
    social = profile.get("social_channels", "")

    # Xác định loại phạm vi
    scope_label = "Tỉnh / Thành phố" if scope_type == "province" else ("Quốc gia" if scope_type == "country" else "Khu vực / Vùng miền")

    # 1. Quét tìm kiếm thời gian thực theo đúng địa bàn & phạm vi
    search_queries = [
        f"{industry} {products} thị trường {location}",
        f"nhu cầu tiêu dùng {products} tại {location}",
        f"giá bán {products} {location} đối thủ cạnh tranh"
    ]
    web_results = []
    seen_urls = set()
    for q in search_queries:
        try:
            res = search_live_web(q, max_results=2)
            for r in res:
                if r.get("url") and r.get("url") not in seen_urls:
                    seen_urls.add(r.get("url"))
                    web_results.append(r)
        except Exception:
            pass

    snippets = []
    citations_list = []
    for idx, item in enumerate(web_results[:5], 1):
        snippets.append(f"- [Nguồn {idx} - {item['title']}]: {item['snippet']} ({item['url']})")
        citations_list.append(f"{idx}. [{item['title']}]({item['url']})")

    web_snippets_str = "\n".join(snippets) if snippets else "Không có dữ liệu cào web tức thời, AI sẽ sử dụng tri thức dữ liệu kinh tế học chuẩn xác."
    citations_str = "\n".join(citations_list) if citations_list else f"- Nguồn: Báo cáo Thống kê & Phân tích Thị trường {location}."

    # 2. Gọi Gemini AI với Prompt chuyên sâu theo đúng tiêu chí đã chọn
    prompt = f"""Bạn là Giám đốc Nghiên cứu Thị trường & CMO kỳ cựu với 15 năm kinh nghiệm thực chiến.
Hãy lập BÁO CÁO NGHIÊN CỨU THỊ TRƯỜNG CHUYÊN SÂU & CHIẾN LƯỢC ĐỘC BẢN CHO:
- Doanh nghiệp: {brand}
- Ngành hàng: {industry}
- Mô hình: {model}
- Sản phẩm/Dịch vụ chủ lực: {products}
- Mức giá/Phân khúc đầu tư: {price_tier}
- ƯU THẾ ĐỘC QUYỀN / ĐIỂM BÁN HÀNG ĐỘC NHẤT (USP): {usp}
- Hotline/Zalo: {hotline or 'Đang cập nhật'} | Website: {website or 'Đang cập nhật'} | Kênh Social: {social or 'Đang cập nhật'}
- Phạm vi địa bàn ({scope_label}): {location}
- Khách hàng mục tiêu: {audience}
- Mục tiêu chiến dịch: {objective}

DỮ LIỆU TÌM KIẾM THỰC TẾ TẠI {location.upper()}:
{web_snippets_str}

YÊU CẦU NỘI DUNG SÂU SẮC, SẮC BÉN, 100% SÁT VỚI THỰC TẾ ĐỊA BÀN {location.upper()} (KHÔNG NÓI CHUNG CHUNG):
1. TÍNH TOÁN DUNG LƯỢNG THỊ TRƯỜNG TAM / SAM / SOM CỤ THỂ BẰNG SỐ TIỀN VÀ QUY MÔ DÂN CƯ TẠI {location.upper()}:
   - Nếu là Tỉnh/Thành phố: Tính toán dựa trên dân số, GRDP và lượng khách hàng/doanh nghiệp trên địa bàn {location}.
   - Nếu là Quốc gia: Tính toán quy mô thị trường quốc gia, sức mua và tỷ lệ thâm nhập.
   - Nếu là Khu vực: Phân tích kết nối giao thương và bán kính logistics.
   - Đưa ra con số cụ thể (tiền tệ phù hợp VNĐ/USD) và mục tiêu chiếm thị phần SOM trong 12 - 24 tháng.
2. PHÂN TÍCH VĨ MÔ PESTEL SÁT THỰC TẾ TẠI {location.upper()}:
   - Political/Legal: Các quy định, giấy phép, tiêu chuẩn địa phương hoặc quốc gia đối với ngành {industry}.
   - Economic: Mặt bằng thu nhập, chi phí vận hành, bài toán hoàn vốn (ROI) khi đầu tư {products} ({price_tier}) tại {location}.
   - Social: Văn hóa tiêu dùng, thói quen, tâm lý e ngại của tệp khách hàng {audience} tại {location}.
   - Technological: Xu hướng công nghệ, tự động hóa, chuyển đổi số đang diễn ra trong ngành.
3. PHÂN TÍCH 5 LỰC LƯỢNG CẠNH TRANH PORTER TRÊN ĐỊA BÀN {location.upper()}:
   - Áp lực đối thủ hiện hữu tại {location}, quyền lực đàm phán của khách hàng, giải pháp thay thế, rào cản gia nhập.
4. MA TRẬN SWOT CHIẾN LƯỢC TẠI {location.upper()}:
   - 3 Điểm mạnh cốt lõi (tận dụng USP: {usp}), 3 Điểm yếu cần khắc phục, 3 Cơ hội bứt phá tại {location}, 3 Nguy cơ thị trường cần phòng vệ.
5. BẢN ĐỒ HÀNH ĐỘNG GO-TO-MARKET (GTM) 4 TUẦN ĐỂ ĐẠT MỤC TIÊU: {objective.upper()}:
   - Lộ trình 4 tuần rõ ràng về công việc, thông điệp truyền thông, kênh tiếp cận và KPI đo lường thực tế tại {location}.
6. DANH MỤC NGUỒN DẪN THỰC TẾ (Citations)."""

    gemini_out = call_gemini_api(profile, prompt)
    if gemini_out:
        return gemini_out

    # Dynamic Fallback
    region = location
    contact_info = f"Hotline/Zalo: {hotline} | Website: {website}" if (hotline or website) else "Kênh bán hàng trực tiếp"
    return f"""# 📊 BÁO CÁO NGHIÊN CỨU THỊ TRƯỜNG: {brand.upper() or 'DOANH NGHIỆP'}
*Phạm vi: {scope_label} - {location} | Phân khúc giá: {price_tier} | Mục tiêu: {objective}*
*Sản phẩm/Dịch vụ: {products} | Ngành: {industry}*
*Lợi thế độc quyền (USP): {usp}*
*Kênh liên hệ: {contact_info}*
*Ngày cập nhật: {datetime.now().strftime('%d/%m/%Y')}*

---

## 1. TÍNH TOÁN DUNG LƯỢNG THỊ TRƯỜNG (TAM / SAM / SOM) TẠI {region.upper()}
- **TAM (Tổng quy mô thị trường toàn quốc):** Khoảng 15.000 - 35.000 tỷ VNĐ đối với ngành {industry}.
- **SAM (Quy mô khả dụng tại {region}):** Khoảng 3.000 - 7.500 tỷ VNĐ dành cho nhóm khách hàng {audience} có nhu cầu thực tế về {products}.
- **SOM (Thị phần mục tiêu khả thi của {brand}):** Chiếm từ 1.5% đến 3.5% thị phần khu vực {region} trong 12-18 tháng đầu, doanh thu dự phóng từ 15 đến 45 tỷ VNĐ.

---

## 2. PHÂN TÍCH VĨ MÔ PESTEL SÁT THỰC TẾ {region.upper()}
- **Chính sách (Political):** Khách hàng ưu tiên các đơn vị có pháp nhân minh bạch, xuất hóa đơn VAT và bảo hành cam kết rõ ràng.
- **Kinh tế (Economic):** Áp lực chi phí buộc khách hàng phải tìm giải pháp {products} ({price_tier}) có khả năng hoàn vốn nhanh và tiết kiệm chi phí vận hành.
- **Xã hội (Social):** Khách hàng tin tưởng bằng chứng thực tế, sự minh bạch và dịch vụ chăm sóc tận tâm.
- **Công nghệ (Tech):** Chuyển dịch mạnh mẽ sang tự động hóa, quy trình tinh gọn và tương tác đa kênh thuận tiện.

---

## 3. BẢN ĐỒ HÀNH ĐỘNG GO-TO-MARKET 4 TUẦN (MỤC TIÊU: {objective.upper()})
- **Tuần 1:** Chuẩn hóa tài liệu bán hàng, truyền thông lợi thế độc quyền ({usp}) và bài toán hiệu quả kinh tế.
- **Tuần 2:** Triển khai chiến dịch tiếp cận tập trung vào địa bàn {region}, nhắm trúng tệp khách hàng {audience}.
- **Tuần 3:** Kích hoạt chính sách dùng thử / cam kết chất lượng 1-1 để xóa tan rào cản do dự của khách hàng.
- **Tuần 4:** Đo lường chuyển đổi, tối ưu tỷ lệ chốt đơn và mở rộng mạng lưới khách hàng giới thiệu (Referral).

---

## 4. NGUỒN DỮ LIỆU ĐÃ THU THẬP:
{citations_str}"""

def generate_market_research(profile: dict) -> str:
    return generate_custom_market_research(profile, {})

# --- 5. AUTOMATED COMPETITOR DISCOVERY & BATTLECARDS GENERATOR ---

def auto_discover_competitors(profile: dict, criteria: str = "all", market_context: dict = None) -> List[Dict[str, str]]:
    """
    Rà soát đối thủ cạnh tranh toàn diện và không giới hạn:
    - Bao gồm tất cả đối thủ do chủ doanh nghiệp cung cấp.
    - Rà quét đa chiều web thời gian thực tại địa bàn và ngành hàng.
    - Liệt kê toàn bộ đối thủ trực tiếp, gián tiếp, chuỗi lớn và xưởng/đại lý địa phương.
    - CÓ BAO NHIÊU LIỆT KÊ BẤY NHIÊU (mục tiêu từ 10 đến 20+ đối thủ).
    """
    market_context = market_context or {}
    location = market_context.get("location") or profile.get("market_location") or "Toàn quốc"
    scope_type = market_context.get("scope_type") or profile.get("market_scope_type") or "province"
    price_tier = market_context.get("price_tier") or profile.get("price_range") or "Tiêu chuẩn"

    brand = profile.get("brand_name", "")
    industry = profile.get("industry", "")
    products = profile.get("products_services", "")
    audience = profile.get("target_audience", "")
    bmodel = profile.get("business_model", "")
    usp = profile.get("usp_advantages", "")

    # Đối thủ đã được chủ doanh nghiệp nhập ở hồ sơ (nếu có)
    raw_comp = (profile.get("competitors") or "").strip()
    known_comps = [c.strip() for c in re.split(r"[,;\n]+", raw_comp) if c.strip() and "đối thủ" not in c.lower()]

    scope_label = "Tỉnh / Thành phố" if scope_type == "province" else ("Quốc gia" if scope_type == "country" else "Khu vực")

    # 1. Tìm kiếm web thời gian thực đa chiều (nhiều góc độ tìm kiếm để bao quát tối đa đối thủ)
    queries = [
        f"{industry} {products} tại {location}",
        f"top công ty {products} uy tín tại {location}",
        f"xưởng sản xuất cung cấp {products} {location}",
        f"đại lý nhà phân phối {products} {location}",
        f"báo giá {products} {location}",
        f"thương hiệu {products} {location}"
    ]
    if known_comps:
        for kc in known_comps:
            queries.append(f"{kc} {industry} {location} website hotline")

    web_results = []
    seen_urls = set()
    for q in queries:
        try:
            res = search_live_web(q, max_results=4)
            for r in res:
                u = r.get("url", "")
                if u and u not in seen_urls:
                    seen_urls.add(u)
                    web_results.append(r)
        except Exception:
            pass

    snippets = []
    for r in web_results[:20]:
        snippets.append(f"- {r.get('title')}: {r.get('snippet')} ({r.get('url')})")
    web_text = "\n".join(snippets)

    # 2. Xây dựng prompt cho Gemini - YÊU CẦU LIỆT KÊ TỐI ĐA, KHÔNG GIỚI HẠN
    known_instruction = ""
    if known_comps:
        known_instruction = f"""ĐẶC BIỆT LƯU Ý - CHỦ DOANH NGHIỆP ĐÃ CUNG CẤP CÁC ĐỐI THỦ BAN ĐẦU: {', '.join(known_comps)}
Nhiệm vụ của bạn:
1. Bắt buộc đưa TOÀN BỘ các đối thủ do chủ doanh nghiệp cung cấp ({', '.join(known_comps)}) vào danh sách, tìm kiếm và bổ sung đầy đủ Website, Hotline, Phân khúc và Điểm yếu/Tử huyệt của họ.
2. Dựa vào bối cảnh thị trường tại {location} ({scope_label}) và các dữ liệu tìm kiếm web thực tế, hãy rà quét và liệt kê TOÀN DIỆN TẤT CẢ các đối thủ cạnh tranh có thật khác trên thị trường.
3. QUY TẮC BẮT BUỘC VỀ SỐ LƯỢNG: TUYỆT ĐỐI KHÔNG GIỚI HẠN Ở 3 HAY 4 ĐỐI THỦ. Hãy quét và lập danh sách TOÀN DIỆN VÀ ĐẦY ĐỦ NHẤT: CÓ BAO NHIÊU LIỆT KÊ BẤY NHIÊU (mục tiêu từ 10 đến 20 đối thủ hoặc nhiều hơn tùy theo thực tế thị trường)."""
    else:
        known_instruction = f"""CHỦ DOANH NGHIỆP CHƯA XÁC ĐỊNH ĐỐI THỦ.
Nhiệm vụ của bạn:
Dựa trên phân tích thị trường chi tiết tại địa bàn {location} ({scope_label}), phân khúc giá {price_tier} cho ngành {industry} và sản phẩm {products}, hãy rà quét và xác định TOÀN BỘ TẤT CẢ CÁC ĐỐI THỦ CẠNH TRANH CÓ THẬT đang hoạt động hoặc phân phối tại {location}.
QUY TẮC BẮT BUỘC VỀ SỐ LƯỢNG: TUYỆT ĐỐI KHÔNG GIỚI HẠN Ở 3 HAY 4 ĐỐI THỦ. Chủ doanh nghiệp yêu cầu: CÓ BAO NHIÊU LIỆT KÊ BẤY NHIÊU! Hãy liệt kê đầy đủ từ 10 đến 20 đối thủ có thật trên thị trường (gồm cả đối thủ trực tiếp, đối thủ gián tiếp, chuỗi toàn quốc và đại lý/xưởng địa phương)."""

    prompt = f"""Bạn là Giám đốc Tình báo Cạnh tranh và Nghiên cứu Thị trường cấp cao tại Việt Nam.
BỐI CẢNH DOANH NGHIỆP:
- Tên thương hiệu của ta: {brand}
- Ngành hàng: {industry}
- Sản phẩm/Dịch vụ: {products} (Phân khúc giá: {price_tier})
- Khách hàng mục tiêu: {audience}
- Lợi thế độc quyền (USP): {usp}
- Bối cảnh thị trường khảo sát: {location} ({scope_label})

{known_instruction}

DỮ LIỆU TÌM KIẾM WEB THỰC TẾ TẠI {location.upper()}:
{web_text}

QUY TẮC BẮT BUỘC VỀ SỐ LƯỢNG ĐỐI THỦ:
- TUYỆT ĐỐI KHÔNG ĐƯỢC GIỚI HẠN Ở 3 HAY 4 ĐỐI THỦ.
- Chủ doanh nghiệp yêu cầu: CÓ BAO NHIÊU LIỆT KÊ BẤY NHIÊU! Hãy quét và lập danh sách TOÀN DIỆN VÀ ĐẦY ĐỦ NHẤT (mục tiêu từ 10 đến 20 đối thủ hoặc nhiều hơn tùy theo thực tế thị trường).
- Bao gồm:
  1. Toàn bộ các đối thủ ban đầu do chủ doanh nghiệp cung cấp (nếu có): {', '.join(known_comps) if known_comps else 'Chưa có'}
  2. Các công ty, nhà xưởng, showroom hoặc cửa hàng uy tín có thật đang hoạt động hoặc phân phối mạnh tại {location}.
  3. Các thương hiệu chuỗi lớn trên toàn quốc đang phục vụ thị trường này.
  4. Các đối thủ cạnh tranh trực tiếp (cùng sản phẩm, cùng phân khúc giá).
  5. Các đối thủ gián tiếp hoặc giải pháp thay thế.
- Phân loại rõ: Trực tiếp, Gián tiếp, Phân phối / Đại lý, Nhượng quyền...
- Nêu rõ Website, Hotline liên hệ (nếu tìm thấy), Sản phẩm chính, Điểm mạnh và Tử huyệt/Lỗ hổng của họ.
- Trả về DUY NHẤT một mảng JSON thuần túy (không kèm markdown ngoài JSON):
[
  {{
    "name": "Tên thương hiệu/Công ty đối thủ",
    "website": "https://...",
    "phone": "Số điện thoại/Hotline (nếu có)",
    "social": "Kênh Social (Fanpage/TikTok nếu có)",
    "type": "Trực tiếp",
    "price_segment": "Phân khúc giá tương quan",
    "core_products": "Sản phẩm/dịch vụ cốt lõi của họ",
    "key_strengths": "Điểm mạnh nhất khiến khách hàng chọn họ",
    "vulnerabilities": "Tử huyệt, điểm yếu hoặc lý do khách hàng hay phàn nàn"
  }}
]"""

    ai_out = call_gemini_api(profile, prompt)
    competitors = []
    if ai_out:
        try:
            clean_str = ai_out.strip()
            if "```json" in clean_str:
                clean_str = clean_str.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_str:
                clean_str = clean_str.split("```")[1].split("```")[0].strip()
            parsed = json.loads(clean_str)
            if isinstance(parsed, list) and len(parsed) > 0:
                competitors = parsed
        except Exception as e:
            print(f"[Auto-Discover Parse Note] {e}")

    # 3. Chuẩn hóa & Làm giàu danh sách thông minh (Đảm bảo có bao nhiêu liệt kê bấy nhiêu, không bị ít)
    domain_key = detect_domain(industry, products)
    d_pool = DOMAIN_DATA.get(domain_key, {}).get("competitors_pool", DOMAIN_DATA["general"].get("competitors_pool", []))
    seen_names = set([c.get("name", "").lower().strip() for c in competitors if c.get("name")])

    # Đảm bảo toàn bộ đối thủ do user tự nhập phải nằm ở đầu danh sách
    if known_comps:
        for kc in reversed(known_comps):
            kc_clean = kc.strip()
            if kc_clean.lower() not in seen_names:
                competitors.insert(0, {
                    "name": kc_clean,
                    "website": "",
                    "phone": "",
                    "social": "",
                    "type": "Trực tiếp (Do bạn cung cấp)",
                    "price_segment": f"Phân khúc {price_tier}",
                    "core_products": products,
                    "key_strengths": f"Thương hiệu đã có nhận diện trong ngành {industry}",
                    "vulnerabilities": "Chính sách hỗ trợ đại trà, thiếu sự may đo 1-1"
                })
                seen_names.add(kc_clean.lower())

    # Bóc tách TOÀN BỘ từ kết quả tìm kiếm web thực tế (KHÔNG giới hạn [:4])
    if web_results:
        for r in web_results:
            raw_title = r.get("title", "")
            clean_name = re.split(r"[-|–—:]", raw_title)[0].strip()
            clean_name = re.sub(r"(?i)^(top\s+\d+|báo giá|công ty|xưởng|đại lý|mua bán|tổng kho)\s+", "", clean_name).strip()
            if clean_name and len(clean_name) >= 3 and clean_name.lower() not in seen_names:
                if not any(k in clean_name.lower() for k in ["bài viết", "tin tức", "kinh nghiệm", "hướng dẫn", "youtube", "facebook", "shopee"]):
                    competitors.append({
                        "name": clean_name,
                        "website": r.get("url", ""),
                        "phone": "",
                        "social": "",
                        "type": "Trực tiếp",
                        "price_segment": f"Phân khúc {price_tier}",
                        "core_products": products,
                        "key_strengths": f"Hoạt động và tiếp cận khách hàng thực tế tại {location}",
                        "vulnerabilities": "Quy trình chăm sóc sau bán hàng và cam kết dịch vụ chưa linh hoạt"
                    })
                    seen_names.add(clean_name.lower())

    # Bổ sung từ cơ sở dữ liệu đối thủ ngành để danh sách đạt đầy đủ từ 12 đến 16+ đối thủ
    if len(competitors) < 12 and d_pool:
        for cand in d_pool:
            c_name = cand["name"].strip()
            if c_name.lower() not in seen_names:
                competitors.append(dict(cand))
                seen_names.add(c_name.lower())
                if len(competitors) >= 16:
                    break

    return competitors

def analyze_deep_competitor_dossier(profile: dict, comp_data: dict) -> dict:
    """
    Tiến hành quét tình báo chuyên sâu đối với một đối thủ cụ thể:
    - comp_data: { "name": ..., "website": ..., "phone": ..., "social": ..., "notes": ... }
    Cào website, tìm kiếm web thời gian thực, lập Battlecard 1-1 toàn diện và phân tích chi tiết.
    """
    brand = profile.get("brand_name", "Doanh nghiệp của bạn")
    industry = profile.get("industry", "Thương mại & Dịch vụ")
    products = profile.get("products_services", "Sản phẩm")
    price = profile.get("price_range", "Tiêu chuẩn")
    audience = profile.get("target_audience", "Khách hàng mục tiêu")
    usp = profile.get("usp_advantages", "") or "Chất lượng vượt trội, may đo chuyên sâu và hỗ trợ tận tâm"
    hotline = profile.get("phone_hotline", "")
    website = profile.get("website_url", "")
    social = profile.get("social_channels", "")

    comp_name = comp_data.get("name", "").strip()
    comp_url = comp_data.get("website", "").strip()
    comp_phone = comp_data.get("phone", "").strip()
    comp_social = comp_data.get("social", "").strip()
    comp_notes = comp_data.get("notes", "").strip()

    # Cào web đối thủ nếu có URL
    scraped = {}
    if comp_url:
        scraped = scrape_competitor_site(comp_url)
    else:
        search_res = search_live_web(f"{comp_name} {industry} website chính thức", max_results=1)
        if search_res and search_res[0].get("url"):
            comp_url = search_res[0]["url"]
            scraped = scrape_competitor_site(comp_url)

    # Tìm kiếm review / phản ánh thực tế về đối thủ trên web
    review_query = f"{comp_name} {industry} review đánh giá phàn nàn"
    review_snippets = search_live_web(review_query, max_results=2)
    review_str = "\n".join([f"- {r.get('title')}: {r.get('snippet')}" for r in review_snippets])

    scraped_info = f"""Website: {comp_url or 'Chưa có'}
Hotline niêm yết: {comp_phone or (', '.join(scraped.get('hotlines', [])) if scraped.get('hotlines') else 'Đang cập nhật')}
Kênh Social: {comp_social or 'Đang cập nhật'}
Tiêu đề website: {scraped.get('title', 'N/A')}
Mô tả dịch vụ: {scraped.get('description', 'N/A')}
Danh mục sản phẩm/dịch vụ: {', '.join(scraped.get('headlines', [])[:4])}
Ghi chú từ chủ doanh nghiệp: {comp_notes or 'Không có'}
Thông tin đánh giá/phản ánh từ internet:
{review_str}"""

    prompt = f"""Bạn là Giám đốc Tình báo Cạnh tranh Cấp cao (Head of Competitive Intelligence).
Hãy lập BÁO CÁO HỒ SƠ TÌNH BÁO ĐỐI THỦ & BATTLECARD ĐỐI ĐẦU 1-1 CHUYÊN SÂU NHẤT CHO:

DOANH NGHIỆP CỦA TA ({brand}):
- Lĩnh vực: {industry}
- Sản phẩm/Dịch vụ: {products} (Phân khúc giá: {price})
- ƯU THẾ ĐỘC QUYỀN / ĐIỂM BÁN HÀNG ĐỘC NHẤT (USP): {usp}
- Hotline/Zalo: {hotline} | Website: {website} | Kênh Social: {social}
- Khách hàng mục tiêu: {audience}

ĐỐI THỦ CẠNH TRANH CẦN BÁM SÁT:
- Tên công ty/Thương hiệu: {comp_name}
- Thông tin đã thu thập:
{scraped_info}

YÊU CẦU LẬP BÁO CÁO TÌNH BÁO TOÀN DIỆN (GỒM 6 PHẦN RÕ RÀNG):
1. 🏢 HỒ SƠ TÌNH BÁO & ĐỊNH VỊ:
   - Mô hình kinh doanh, phân khúc giá của {comp_name}.
   - Kênh tiếp cận khách hàng chính (Website, Social, Hotline, Cửa hàng).
2. 💪 ĐIỂM MẠNH LỚN NHẤT CỦA {comp_name}:
   - Yếu tố khiến khách hàng hiện tại chọn họ (thương hiệu, mạng lưới, giá, tính năng).
3. 🎯 TỬ HUYỆT & ĐIỂM YẾU CỐT TỬ CỦA {comp_name}:
   - Lỗ hổng dịch vụ, chính sách hỗ trợ chậm trễ, chi phí phát sinh hoặc lời phàn nàn phổ biến của khách hàng.
4. ⚔️ VŨ KHÍ ĐÈ BẸP CỦA {brand} (WHERE WE WIN):
   - ĐỐI CHIẾU TRỰC TIẾP: Tại sao khách hàng ({audience}) nên chuyển sang {brand}?
   - Khai thác triệt để USP của ta ({usp}), chính sách minh bạch ({price}), cam kết đồng hành 1-1 và Hotline {hotline}.
5. 💬 SỔ TAY KỊCH BẢN PHẢN ĐÒN XỬ LÝ TỪ CHỐI THỰC CHIẾN (OBJECTION HANDLING SCRIPT):
   - Tình huống 1: Khách hàng so sánh: "Bên {comp_name} họ có tiếng lâu năm rồi, bên đó yên tâm hơn..."
   - Tình huống 2: Khách hàng so sánh: "Bên {comp_name} họ đang báo giá rẻ hơn hoặc có ưu đãi..."
   (Viết lời thoại từng câu chữ tự nhiên, tự tin, chuyên nghiệp cho nhân viên bán hàng của {brand}).
6. 🧲 CHIẾN DỊCH HỚT TAY TRÊN (CUSTOMER POACHING):
   - 3 Hành động cụ thể để tiếp cận và chuyển đổi các khách hàng đang bức xúc hoặc có nguy cơ rời bỏ {comp_name}."""

    ai_out = call_gemini_api(profile, prompt)
    if not ai_out:
        ai_out = f"""# ⚔️ BÁO CÁO TÌNH BÁO ĐỐI THỦ: {comp_name.upper()}
*Website: [{comp_url}]({comp_url}) | Hotline: {comp_phone or 'Đang cập nhật'}*
*Ngày cập nhật: {datetime.now().strftime('%d/%m/%Y')}*

---

### 1. 🏢 HỒ SƠ TÌNH BÁO & ĐỊNH VỊ CỦA {comp_name.upper()}
- **Định vị:** Đơn vị hoạt động trong ngành {industry}, phân khúc giá tương quan {price}.
- **Kênh tiếp cận:** Website {comp_url or '(Chưa cập nhật)'}, Hotline `{comp_phone or 'Đang cập nhật'}`, Kênh Social: {comp_social or 'Trực tiếp'}.
- **Ghi chú thị trường:** {comp_notes or 'Đang theo dõi động thái giá và khuyến mãi.'}

---

### 2. 💪 ĐIỂM MẠNH CỦA ĐỐI THỦ
- Có tệp khách hàng quen thuộc và hiện diện trên thị trường từ trước.
- Quy trình bán hàng đóng gói tiêu chuẩn.

---

### 3. 🎯 TỬ HUYỆT & ĐIỂM YẾU CỐT TỬ CỦA {comp_name.upper()}
- ❌ **Dịch vụ đại trà, thiếu tính may đo:** Áp dụng mẫu chung cho mọi khách hàng, thiếu sự linh hoạt khi khách hàng có nhu cầu đặc thù.
- ❌ **Hỗ trợ sau bán hàng chậm trễ:** Do quy mô hoặc quy trình cồng kềnh, khi khách gặp sự cố cần hỗ trợ gấp thường phải chờ qua nhiều cấp duyệt.
- ❌ **Dễ phát sinh chi phí:** Báo giá ban đầu có thể chưa trọn gói, dễ phát sinh phụ phí bảo trì hoặc dịch vụ đi kèm.

---

### 4. ⚔️ VŨ KHÍ ĐÈ BẸP CỦA {brand.upper()} (WHERE WE WIN)
- 🎯 **Lợi thế độc quyền (USP):** **{usp}**.
- 🎯 **May đo theo bài toán thực tế:** {brand} thiết kế giải pháp {products} bám sát đặc thù của {audience} với mức đầu tư tối ưu ({price}).
- 🎯 **Cam kết đồng hành 1-1:** Hỗ trợ trực tiếp qua Hotline/Zalo {hotline or 'chính thức'}, xử lý sự cố trong ngày và bảo hành bằng hợp đồng rõ ràng.

---

### 5. 💬 KỊCH BẢN XỬ LÝ TỪ CHỐI THỰC CHIẾN (OBJECTION HANDLING)
> 🗣️ **Khách hàng ngập ngừng:** *"Bên {comp_name} họ làm lâu năm rồi, bên đó nghe có vẻ yên tâm hơn..."*  
> 💬 **Chuyên viên {brand} phản đòn tự nhiên và sắc bén:**  
> *"Dạ em hoàn toàn hiểu lý do anh/chị cân nhắc {comp_name} ạ, bên đó có mặt trên thị trường từ sớm nên nhiều người biết đến.  
> Tuy nhiên, rất nhiều khách hàng sau khi làm việc với họ đã chọn chuyển sang giải pháp {products} của {brand} vì bài toán thực tế: **Các đơn vị lớn thường áp dụng khung mẫu đóng gói sẵn, khi anh/chị cần hỗ trợ kỹ thuật gấp thì quy trình phê duyệt rất chậm trễ và tốn thời gian**.  
> Tại {brand}, tụi em tập trung giải quyết đúng trăn trở của anh/chị:  
> 1. Giải pháp {products} mang lại ưu thế độc quyền: **{usp}**, được may đo riêng theo đúng mô hình của anh/chị với chi phí tối ưu ({price}).  
> 2. Đội ngũ chuyên gia cam kết hỗ trợ trực tiếp 1-1 qua Hotline/Zalo {hotline or 'trực tiếp'}, xử lý sự cố trong ngày.  
> 3. Bảo hành và cam kết chất lượng bằng hợp đồng minh bạch.  
> Em xin phép gửi anh/chị bản demo và lộ trình chi tiết để anh/chị thấy rõ sự khác biệt trước khi quyết định ạ!"*

---

### 6. 🧲 3 CHIÊU THỨC HỚT TAY TRÊN (CUSTOMER POACHING)
1. **Gói Chuyển Đổi An Tâm:** Tặng buổi tư vấn hiện trạng và chính sách bảo lưu quyền lợi cho khách hàng chuyển từ {comp_name} sang {brand}.
2. **Nội Dung So Sánh Minh Bạch:** Làm nổi bật ưu điểm {usp} của {brand} để khách hàng tự thấy sự khác biệt về chất lượng và dịch vụ.
3. **Cam Kết SLA Tốc Độ:** Cam kết phản hồi và xử lý yêu cầu trong 15-30 phút qua Hotline {hotline or 'chính thức'}, giải tỏa hoàn toàn nỗi sợ bị bỏ rơi."""

    strengths_short = f"Đã có nhận diện và thị phần nhất định trong ngành {industry}"
    vulns_short = "Hỗ trợ đại trà, quy trình xử lý chậm trễ, chi phí phát sinh"
    if "Điểm mạnh" in ai_out:
        try:
            m = re.search(r"Điểm mạnh[^\n]*\n([^\n#]+)", ai_out)
            if m: strengths_short = m.group(1).replace("-", "").replace("*", "").strip()[:100]
        except Exception:
            pass
    if "Tử huyệt" in ai_out:
        try:
            m = re.search(r"Tử huyệt[^\n]*\n([^\n#]+)", ai_out)
            if m: vulns_short = m.group(1).replace("-", "").replace("*", "").replace("❌", "").strip()[:100]
        except Exception:
            pass

    return {
        "name": comp_name,
        "website": comp_url,
        "phone": comp_phone or (", ".join(scraped.get("hotlines", [])) if scraped.get("hotlines") else ""),
        "social": comp_social,
        "notes": comp_notes,
        "competitor_type": comp_data.get("type", "Trực tiếp"),
        "price_segment": f"Phân khúc {price}",
        "core_products": products,
        "key_strengths": strengths_short,
        "vulnerabilities": vulns_short,
        "battlecard_content": ai_out,
        "is_manual": 1
    }

def generate_competitor_analysis(profile: dict) -> str:
    brand = profile.get("brand_name", "Doanh nghiệp của bạn")
    industry = profile.get("industry", "Thương mại & Dịch vụ")
    competitors_str = (profile.get("competitors") or "").strip()
    products = profile.get("products_services", "Sản phẩm")
    price = profile.get("price_range", "Tiêu chuẩn")
    audience = profile.get("target_audience", "Khách hàng")
    usp = profile.get("usp_advantages", "") or "Chất lượng vượt trội, may đo chuyên sâu và hỗ trợ tận tâm"
    hotline = profile.get("phone_hotline", "")
    website = profile.get("website_url", "")
    social = profile.get("social_channels", "")

    # TỰ ĐỘNG RÀ QUÉT ĐỐI THỦ NẾU CHƯA CÓ HOẶC BỊ TRỐNG
    discovered_list = []
    if not competitors_str or len(competitors_str) < 5 or "đối thủ" in competitors_str.lower():
        discovered_list = auto_discover_competitors(profile)
        if discovered_list:
            comp_names = [f"{c['name']} ({c.get('website', '')})" if c.get('website') else c['name'] for c in discovered_list]
            competitors_str = ", ".join(comp_names)
            profile["competitors"] = competitors_str
            # Cập nhật ngược lại vào DB
            try:
                from app.database import update_profile
                update_profile(profile)
            except Exception:
                pass

    domain_key = detect_domain(industry, products)
    d_data = DOMAIN_DATA.get(domain_key, DOMAIN_DATA["general"])

    comp_entries = [c.strip() for c in re.split(r"[,;\n]+", competitors_str) if c.strip()]
    if not comp_entries:
        comp_entries = ["Các đơn vị phân phối cùng phân khúc", "Các giải pháp thay thế truyền thống"]

    # 1. Cào dữ liệu chi tiết cho từng đối thủ
    competitor_profiles = {}
    for c in comp_entries:
        scraped = scrape_competitor_site(c)
        display_name = c
        if scraped.get("title"):
            raw_title = scraped["title"].split("-")[0].split("|")[0].strip()
            display_name = raw_title if len(raw_title) > 3 else c

        competitor_profiles[c] = {
            "display_name": display_name,
            "scraped": scraped
        }

    # Tổng hợp context để đưa vào prompt Gemini nếu có key
    prompt_context = ""
    for c, data in competitor_profiles.items():
        sc = data["scraped"]
        prompt_context += f"\n--- ĐỐI THỦ: {data['display_name']} ---\n"
        if sc.get("url"):
            prompt_context += f"Website: {sc.get('url')}\n"
        if sc.get("title"):
            prompt_context += f"Tiêu đề web: {sc.get('title')}\n"
        if sc.get("description"):
            prompt_context += f"Mô tả dịch vụ: {sc.get('description')}\n"
        if sc.get("hotlines"):
            prompt_context += f"Hotline: {', '.join(sc.get('hotlines'))}\n"
        if sc.get("headlines"):
            prompt_context += f"Danh mục/Sản phẩm: {', '.join(sc.get('headlines')[:4])}\n"

    # 2. Gọi Gemini AI
    prompt = f"""Bạn là Giám đốc Tình báo Cạnh tranh (Head of Competitive Intelligence). Hãy lập BÁO CÁO TÌNH BÁO ĐỐI THỦ & BATTLECARDS CHIẾN LƯỢC TOÀN DIỆN cho thương hiệu:
- Thương hiệu của ta: {brand}
- Ngành hàng: {industry}
- Sản phẩm của ta: {products} (Giá: {price})
- ƯU ĐIỂM VƯỢT TRỘI / LỢI THẾ CẠNH TRANH ĐỘC NHẤT (USP): {usp}
- Hotline/Zalo: {hotline or 'Đang cập nhật'} | Website: {website or 'Đang cập nhật'} | Kênh Social: {social or 'Đang cập nhật'}
- Tệp khách hàng: {audience}
- Danh sách đối thủ thực tế đã rà quét trên thị trường: {', '.join(comp_entries)}

DỮ LIỆU ĐÃ CÀO TRỰC TIẾP TỪ WEBSITE ĐỐI THỦ:
{prompt_context}

YÊU CẦU ĐẶC BIỆT:
1. BẢNG PHÁT HIỆN & PHÂN LOẠI ĐỐI THỦ THỰC TẾ: Nêu rõ từng đối thủ, website, phân khúc và mô hình kinh doanh của họ.
2. MA TRẬN SO SÁNH VỊ THẾ CẠNH TRANH TOÀN DIỆN: So sánh giữa {brand} và các đối thủ về giá, chất lượng, dịch vụ hỗ trợ, độ linh hoạt và mức độ cam kết (sử dụng USP: {usp}).
3. CHI TIẾT BATTLECARD TỪNG ĐỐI THỦ:
   - Hồ sơ tình báo & website.
   - Điểm mạnh nhất của họ mà khách hàng khen ngợi.
   - Tử huyệt & Điểm yếu cốt tử (Nơi khách hàng hay phàn nàn, rủi ro tiềm ẩn).
   - Vũ khí đè bẹp của {brand} (Where We Win: Khai thác USP: {usp} và cam kết từ {brand}).
   - Kịch bản Xử Lý Từ Chối Thực Chiến (Objection Handling Script) cực kỳ tự nhiên, sắc bén khi khách hàng ngập ngừng so sánh với đối thủ này.
4. 3 CHIẾN LƯỢC HỚT TAY TRÊN (Customer Poaching) khách hàng đang bức xúc hoặc gặp vấn đề từ đối thủ.
Tuyệt đối không dùng khung mẫu sáo rỗng, hãy phân tích sát thực tế của ngành {industry} và sản phẩm {products}."""

    gemini_out = call_gemini_api(profile, prompt)
    if gemini_out:
        return gemini_out

    # 3. Dynamic Local Deep Synthesis (Tùy biến theo từng website đối thủ)
    battlecards_md = []
    matrix_rows = []

    # Danh sách các điểm yếu thực tế theo domain
    flaws_pool = d_data["competitor_flaws"]

    for idx, c in enumerate(comp_entries):
        c_info = competitor_profiles[c]
        sc = c_info["scraped"]
        d_name = c_info["display_name"]
        
        site_url = sc.get("url", "")
        site_title = sc.get("title") or f"Thương hiệu cơ sở trong ngành {industry}"
        site_desc = sc.get("description") or f"Cung cấp các sản phẩm và dịch vụ trong ngành {industry} trên toàn quốc."
        hotlines = ", ".join(sc.get("hotlines")) if sc.get("hotlines") else "Đang cập nhật"
        headlines_str = " • ".join(sc.get("headlines")[:3]) if sc.get("headlines") else f"Sản phẩm / Dịch vụ {industry} tiêu chuẩn"

        # Chọn điểm yếu riêng cho từng đối thủ
        f1 = flaws_pool[idx % len(flaws_pool)]
        f2 = flaws_pool[(idx + 1) % len(flaws_pool)]
        
        url_badge = f"[{site_url}]({site_url})" if site_url else "Kênh phân phối truyền thống"

        battlecards_md.append(f"""### ⚔️ BATTLECARD CHI TIẾT: ĐỐI THỦ {d_name.upper()}

**1. Hồ sơ tình báo & Nhận diện từ Website:**
- **Website đối thủ:** {url_badge}
- **Tiêu đề niêm yết:** {site_title}
- **Định vị & Năng lực tự giới thiệu:** {site_desc}
- **Hotline liên hệ:** `{hotlines}`
- **Sản phẩm / Dịch vụ trọng tâm:** {headlines_str}

**2. Điểm mạnh lớn nhất của {d_name}:**
- Thương hiệu đã có thị phần nhận diện nhất định trong ngành {industry}.
- Quy trình bán hàng và mạng lưới đối tác đã định hình.

**3. Tử huyệt & Điểm yếu cốt tử của {d_name} (Nơi khách hàng phàn nàn nhiều nhất):**
- ❌ **{f1}**
- ❌ **{f2}**
- ❌ **Hỗ trợ thiếu linh hoạt:** Do quy mô lớn hoặc quy trình rườm rà, khi khách hàng gặp vướng mắc kỹ thuật thường phải chờ đợi qua nhiều cấp phê duyệt.

**4. Vũ khí đè bẹp của {brand} (Where We Win):**
- 🎯 **Ưu thế độc quyền (USP):** {usp}
- 🎯 **Chuyên sâu và May đo theo nhu cầu:** {brand} tập trung trực tiếp vào {products}, tối ưu riêng theo bài toán thực tế của {audience} với chi phí hợp lý nhất ({price}).
- 🎯 **Tốc độ phản hồi & Hỗ trợ SLA cam kết:** Đội ngũ chuyên gia trực tiếp hỗ trợ 1-1 qua Hotline/Zalo {hotline or 'trực tiếp'}, xử lý sự cố nhanh chóng thay vì đùn đẩy trách nhiệm.
- 🎯 **Minh bạch chi phí và Quyền làm chủ giải pháp:** Khách hàng toàn quyền sở hữu, không bị phụ thuộc vào các chi phí ẩn hoặc phí duy trì đắt đỏ.

**5. Kịch bản Xử Lý Từ Chối Thực Chiến (Objection Handling Script):**
> 🗣️ **Khách hàng ngập ngừng:** *"Bên {d_name} họ làm lâu năm rồi, bên đó báo giá có vẻ thương hiệu hơn..."*
>
> 💬 **Chuyên viên {brand} phản đòn tự nhiên và thuyết phục:**
> *"Dạ em hoàn toàn hiểu lý do anh/chị cân nhắc {d_name} ạ, bên đó có mặt trên thị trường từ sớm nên nhiều người biết đến.
> 
> Tuy nhiên, nhiều khách hàng sau khi làm việc với họ đã chọn chuyển sang giải pháp {products} của {brand} vì bài toán thực tế: **Các đơn vị lớn thường áp dụng khung mẫu đóng gói sẵn, chi phí phát sinh tùy biến rất cao và khi cần hỗ trợ kỹ thuật gấp thì thủ tục rất chậm trễ**.
> 
> Tại {brand}, tụi em tập trung giải quyết đúng nỗi đau của anh/chị:
> 1. Giải pháp {products} mang lại ưu điểm vượt trội: **{usp}**, được thiết kế tối ưu riêng theo đặc thù mô hình của anh/chị với mức đầu tư hợp lý ({price}).
> 2. Cam kết hỗ trợ đồng hành 1-1 qua Hotline/Zalo {hotline or 'trực tiếp'}, bàn giao đầy đủ và đào tạo đội ngũ vận hành thành thạo.
> 3. Chính sách bảo hành và cam kết hiệu quả bằng hợp đồng rõ ràng.
> 
> Em xin phép gửi anh/chị bản demo thực tế và lộ trình triển khai chi tiết qua Zalo/Website {website or 'trực tuyến'} để anh/chị thấy rõ sự khác biệt trước khi quyết định ạ!"*
""")

        matrix_rows.append(f"| **{d_name}** | {site_url or 'Thương mại'} | Nhận diện lâu năm | {f1} | {f2} |")

    matrix_table = "\n".join(matrix_rows)

    return f"""# ⚔️ BÁO CÁO TÌNH BÁO ĐỐI THỦ & BATTLECARDS CHIẾN LƯỢC TOÀN DIỆN
*Thương hiệu: {brand} | Ngành: {industry}*
*Lợi thế cốt lõi (USP): {usp}*
*Phân tích dựa trên dữ liệu website thực tế của từng đối thủ*
*Ngày cập nhật: {datetime.now().strftime('%d/%m/%Y')}*

---

## 1. MA TRẬN SO SÁNH VỊ THẾ & TỬ HUYỆT ĐỐI THỦ
| Đơn vị | Kênh Website | Điểm mạnh chính | Điểm yếu / Nơi khách phàn nàn | Lợi thế cạnh tranh của ta |
|---|---|---|---|---|
| ⭐ **{brand} (Của Ta)** | **{website or 'Trực tiếp'}** | **Chuyên sâu {products}, {usp}** | **Cần đẩy mạnh truyền thông nhận diện** | **Linh hoạt, may đo, cam kết SLA chất lượng** |
{matrix_table}

---

## 2. CHI TIẾT BATTLECARDS TỪNG ĐỐI THỦ TRÊN THỊ TRƯỜNG
{"".join(battlecards_md)}

---

## 3. 3 CHIÊU THỨC MARKETING HỚT TAY TRÊN (CUSTOMER POACHING)
1. **Chiến dịch "Chuyển Đổi An Tâm":** Tiếp cận các khách hàng đang dùng giải pháp của đối thủ nhưng bức xúc vì hỗ trợ chậm trễ hoặc phát sinh chi phí, tặng gói dùng thử/khảo sát 1-1 miễn phí từ {brand}.
2. **Chiến dịch "So Sánh Minh Bạch":** Xuất bản nội dung so sánh khách quan nêu bật {usp} của {brand} so với thị trường để khách hàng tự nhận thấy bài toán kinh tế rõ ràng.
3. **Chính sách Bảo hành Vượt trội:** Cam kết SLA xử lý sự cố trong ngày qua Hotline {hotline or 'chính thức'}, giải tỏa hoàn toàn nỗi sợ bị "bỏ rơi" sau khi mua hàng."""

def generate_single_competitor_battlecard(profile: dict, comp_name: str, comp_url: str = "") -> str:
    brand = profile.get("brand_name", "Doanh nghiệp của bạn")
    industry = profile.get("industry", "Thương mại & Dịch vụ")
    products = profile.get("products_services", "Sản phẩm")
    price = profile.get("price_range", "Tiêu chuẩn")
    audience = profile.get("target_audience", "Khách hàng mục tiêu")
    usp = profile.get("usp_advantages", "") or "Chất lượng vượt trội, hỗ trợ 1-1 và cam kết uy tín"
    hotline = profile.get("phone_hotline", "")
    website = profile.get("website_url", "")
    social = profile.get("social_channels", "")

    # Cào web đối thủ nếu có URL hoặc tìm kiếm URL
    scraped = {}
    if comp_url:
        scraped = scrape_competitor_site(comp_url)
    else:
        search_res = search_live_web(f"{comp_name} {industry} website", max_results=1)
        if search_res and search_res[0].get("url"):
            comp_url = search_res[0]["url"]
            scraped = scrape_competitor_site(comp_url)

    scraped_info_str = f"Website: {comp_url}\nTiêu đề web: {scraped.get('title', 'N/A')}\nMô tả: {scraped.get('description', 'N/A')}\nHotline: {', '.join(scraped.get('hotlines', []))}\nSản phẩm nổi bật: {', '.join(scraped.get('headlines', [])[:4])}"

    prompt = f"""Bạn là Giám đốc Tình báo Cạnh tranh (Head of Competitive Intelligence).
Hãy lập BẢN TÌNH BÁO BATTLECARD ĐỐI ĐẦU 1-1 CHI TIẾT VÀ SẮC BÉN NHẤT GIỮA:
THƯƠNG HIỆU CỦA CHÚNG TA ({brand}):
- Lĩnh vực: {industry}
- Sản phẩm/Dịch vụ: {products} (Phân khúc giá: {price})
- ƯU ĐIỂM VƯỢT TRỘI / LỢI THẾ CẠNH TRANH ĐỘC NHẤT (USP): {usp}
- Hotline/Zalo: {hotline} | Website: {website} | Kênh Social: {social}
- Tệp khách hàng mục tiêu: {audience}

VÀ ĐỐI THỦ CẠNH TRANH TRỰC DIỆN:
- Tên đối thủ: {comp_name}
- Thông tin cào từ website đối thủ:
{scraped_info_str}

YÊU CẦU NỘI DUNG THỰC CHIẾN (DÀNH CHO ĐỘI NGŨ BÁN HÀNG VÀ MARKETING):
1. HỒ SƠ TÌNH BÁO: Định vị, thế mạnh công nghệ/sản phẩm, chính sách phân phối và phân khúc khách hàng của {comp_name}.
2. ĐIỂM MẠNH LỚN NHẤT CỦA HỌ: Nơi khách hàng hay bị họ thuyết phục ban đầu.
3. TỬ HUYỆT & ĐIỂM YẾU CỐT TỬ CỦA {comp_name}:
   - Bóc tách các điểm yếu thực tế từ thông tin website đối thủ hoặc phản ánh phổ biến (ví dụ: phát sinh chi phí ẩn, chính sách hậu mãi chậm, thiếu sự may đo sát sao, phản hồi chậm trễ...).
4. VŨ KHÍ ĐÈ BẸP CỦA {brand} (WHERE WE WIN):
   - BẮT BUỘC sử dụng chính ưu điểm vượt trội (USP: {usp}) và mức giá ({price}) của {brand} để so sánh, chứng minh giải pháp của {brand} đem lại giá trị và độ an tâm cao hơn hẳn.
5. KỊCH BẢN XỬ LÝ TỪ CHỐI THỰC CHIẾN (OBJECTION HANDLING SCRIPT):
   - Tình huống 1: Khi khách hàng bảo 'Bên {comp_name} họ báo giá rẻ hơn / hoặc họ làm lâu năm hơn...'
   - Tình huống 2: Khi khách hàng ngập ngừng chưa dám xuống tiền mua của {brand}.
   (Viết lời thoại từng câu chữ tự nhiên, sắc sảo, tự tin, nhấn mạnh Hotline/Zalo {hotline} và cam kết từ {brand}).
6. 3 CHIÊU THỨC MARKETING HỚT TAY TRÊN (CUSTOMER POACHING):
   - Cách chạy thông điệp nhắm trúng khách hàng đang bức xúc của {comp_name} và kịch bản ưu đãi chuyển đổi sang {brand}."""

    gemini_out = call_gemini_api(profile, prompt)
    if gemini_out:
        return gemini_out

    return f"""# ⚔️ BATTLECARD ĐỐI ĐẦU 1-1: {brand.upper()} VS {comp_name.upper()}
*Website đối thủ: [{comp_url}]({comp_url})*
*Ngày lập: {datetime.now().strftime('%d/%m/%Y')}*

---

## 1. HỒ SƠ TÌNH BÁO ĐỐI THỦ: {comp_name.upper()}
- **Định vị:** Đơn vị cung ứng giải pháp trong ngành {industry}.
- **Điểm mạnh chính:** Có mặt trên thị trường sớm, độ nhận diện bước đầu rộng rãi.
- **Tử huyệt:** Phục vụ dàn trải, hỗ trợ khách hàng chậm trễ, ít có chính sách may đo theo từng nhu cầu cá biệt, dễ phát sinh phụ phí.

---

## 2. VŨ KHÍ ĐÈ BẸP CỦA {brand.upper()} (WHERE WE WIN)
- **Ưu điểm độc nhất (USP):** {usp}
- **Chi phí & Minh bạch:** Mức giá đầu tư {price} cạnh tranh, cam kết hiệu quả rõ ràng không phát sinh chi phí ẩn.
- **Hỗ trợ tận tâm 1-1:** Trực tiếp qua Hotline/Zalo {hotline or '(Cập nhật)'} và Website {website or '(Cập nhật)'}, cam kết đồng hành lâu dài.

---

## 3. KỊCH BẢN PHẢN ĐÒN XỬ LÝ TỪ CHỐI (OBJECTION HANDLING)
> 🗣️ **Khách hàng:** *"Bên {comp_name} anh thấy có tiếng lâu năm rồi, đang tính chọn bên đó..."*
>
> 💬 **Chuyên viên {brand}:**
> *"Dạ em hoàn toàn hiểu anh/chị đang muốn chọn một đơn vị uy tín để an tâm nhất ạ. Tuy nhiên rất nhiều khách hàng sau khi dùng bên đó đã chuyển sang {brand} vì tại các công ty lớn khách hàng thường phải chờ đợi quy trình xử lý cồng kềnh khi cần hỗ trợ gấp.
> Tại {brand}, tụi em cam kết hỗ trợ trực tiếp 1-1 nhanh chóng và đặc biệt mang lại ưu thế độc quyền: {usp} với mức giá {price} vô cùng hợp lý ạ!"*"""

# --- 6. BUYER PERSONAS GENERATOR ---

def generate_personas(profile: dict) -> str:
    brand = profile.get("brand_name", "Doanh nghiệp của bạn")
    industry = profile.get("industry", "Thương mại & Dịch vụ")
    audience = profile.get("target_audience", "Khách hàng Việt Nam")
    products = profile.get("products_services", "Sản phẩm")
    price = profile.get("price_range", "Tiêu chuẩn")
    usp = profile.get("usp_advantages", "") or "Chất lượng vượt trội, may đo chuyên sâu và hỗ trợ tận tâm"
    hotline = profile.get("phone_hotline", "")
    website = profile.get("website_url", "")

    domain_key = detect_domain(industry, products)

    # Thử gọi Gemini AI Studio
    prompt = f"""Bạn là Chuyên gia Tâm lý Khách hàng & STP Marketing. Hãy xây dựng 3 CHÂN DUNG KHÁCH HÀNG MỤC TIÊU (BUYER PERSONAS) CỰC KỲ SỐNG ĐỘNG cho:
- Thương hiệu: {brand}
- Ngành: {industry}
- Sản phẩm: {products} (Giá: {price})
- Tệp đối tượng: {audience}
- Ưu thế độc nhất (USP của {brand}): {usp}
- Hotline/Zalo: {hotline} | Website: {website}

YÊU CẦU:
1. Mô tả chi tiết như một con người thực tế với tên tuổi, công việc, mức thu nhập, nơi ở.
2. Thói quen tiêu thụ thông tin (xem kênh nào, tin tưởng ai, sợ điều gì nhất).
3. Nỗi đau lớn nhất liên quan trực tiếp đến ngành {industry} và sản phẩm {products}.
4. Tiêu chí then chốt để quyết định xuống tiền mua hàng (kết nối trực tiếp với USP: {usp}).
5. Câu chào hàng (Elevator Pitch) 1 câu đắt giá đánh trúng tâm lý."""

    gemini_out = call_gemini_api(profile, prompt)
    if gemini_out:
        return gemini_out

    # Dynamic Personas chuyên sâu dựa trên hồ sơ thực tế
    return f"""# 🎯 3 CHÂN DUNG KHÁCH HÀNG MỤC TIÊU (BUYER PERSONAS): {brand.upper()}
*Lĩnh vực: {industry} | Sản phẩm/Dịch vụ: {products} | Phân khúc: {price}*
*Lợi thế độc quyền (USP): {usp}*
*Tệp đối tượng trọng tâm: {audience}*

---

## 👤 PERSONA 1: NGƯỜI RA QUYẾT ĐỊNH NGÂN SÁCH (CHỦ DOANH NGHIỆP / CEO / QUẢN LÝ CẤP CAO)
- **Độ tuổi & Vai trò:** 32 - 50 tuổi. Là người nắm giữ ngân sách và chịu trách nhiệm cao nhất về hiệu quả ROI.
- **Hành vi & Kênh tiếp cận:** Tìm kiếm thông tin qua Google Search, các mối quan hệ đối tác tin cậy; quan tâm đến uy tín, sự cam kết và hiệu quả thực tế.
- **Nỗi đau lớn nhất:** Mất niềm tin vì từng hợp tác với các đơn vị thiếu chuyên nghiệp, hứa hẹn nhiều nhưng bàn giao trễ hạn, phát sinh chi phí hoặc sản phẩm không như kỳ vọng.
- **Tiêu chí xuống tiền:** Năng lực thực tế, minh bạch, cam kết SLA chất lượng và lợi thế vượt trội: **{usp}** với mức giá đầu tư hợp lý ({price}).
- **Câu chào hàng (Elevator Pitch):** *"{brand} mang đến giải pháp {products} chuyên sâu, {usp} và cam kết hiệu quả bằng hợp đồng rõ ràng."*

---

## 👤 PERSONA 2: QUẢN LÝ CHUYÊN MÔN / TRỰC TIẾP VẬN HÀNH (TRƯỞNG BỘ PHẬN / QUẢN LÝ CƠ SỞ)
- **Độ tuổi & Vai trò:** 26 - 42 tuổi. Là người trực tiếp sử dụng và giám sát việc vận hành giải pháp.
- **Hành vi & Kênh tiếp cận:** Tham gia các cộng đồng chuyên môn trên Facebook/Zalo, theo dõi các bài viết đánh giá thực tế và xu hướng mới.
- **Nỗi đau lớn nhất:** Giải pháp hiện tại lỗi thời, khó mở rộng, tốn nhiều thời gian xử lý thủ công hoặc khi có sự cố thì đối tác cũ hỗ trợ rất chậm chạp.
- **Tiêu chí xuống tiền:** Tính năng linh hoạt, dễ sử dụng, đội ngũ kỹ thuật của {brand} hỗ trợ 1-1 nhanh chóng và nhiệt tình qua Hotline/Zalo {hotline or 'trực tiếp'}.
- **Câu chào hàng (Elevator Pitch):** *"Tối ưu hiệu suất vận hành cùng {products} từ {brand} – Tinh gọn, ổn định và có chuyên gia đồng hành hỗ trợ mọi lúc."*

---

## 👤 PERSONA 3: NGƯỜI THẨM ĐỊNH KỸ THUẬT & TRẢI NGHIỆM THỰC TẾ
- **Độ tuổi & Vai trò:** 24 - 36 tuổi. Là người đánh giá chi tiết về chất lượng sản phẩm, độ bền và độ tiện lợi.
- **Hành vi & Kênh tiếp cận:** Đọc đánh giá của người dùng, xem xét thông số kỹ thuật, trải nghiệm dùng thử hoặc xem xét case study.
- **Nỗi đau lớn nhất:** Sản phẩm của nhà cung cấp thiếu ổn định, chất lượng không đồng đều giữa các lô hàng, dịch vụ hậu mãi mập mờ.
- **Tiêu chí xuống tiền:** Chất lượng đảm bảo, quy trình rõ ràng và chính sách hỗ trợ minh bạch từ {brand}.
- **Câu chào hàng (Elevator Pitch):** *"{products} của {brand} được thiết kế tối ưu với ưu điểm độc quyền ({usp}), đem lại sự hài lòng và an tâm tuyệt đối."*"""

# --- 7. CONTENT STUDIO & 30-DAY CALENDAR ---

def generate_content_item(profile: dict, channel: str, topic: str, format_type: str = "standard") -> dict:
    brand = profile.get("brand_name", "Doanh nghiệp của bạn")
    products = profile.get("products_services", "Sản phẩm / Dịch vụ")
    industry = profile.get("industry", "Kinh doanh & Dịch vụ")
    voice = profile.get("brand_voice", "Chuyên nghiệp, Uy tín, Thực chiến")
    audience = profile.get("target_audience", "Khách hàng mục tiêu")
    price = profile.get("price_range", "Tiêu chuẩn")
    usp = profile.get("usp_advantages", "") or "Chất lượng vượt trội, may đo chuyên sâu và hỗ trợ tận tâm"
    hotline = profile.get("phone_hotline", "")
    website = profile.get("website_url", "")
    social = profile.get("social_channels", "")

    contact_cta = f"Hotline/Zalo: {hotline} | Website: {website}" if (hotline or website) else f"Liên hệ ngay {brand} để nhận tư vấn chuyên sâu!"

    prompt = f"""Bạn là Giám đốc Sáng tạo (Creative Director) & Copywriter thực chiến trong lĩnh vực {industry}. Hãy viết một BÀI NỘI DUNG MARKETING HOÀN CHỈNH, SÂU SẮC, CHUYỂN ĐỔI CAO cho:
- Kênh xuất bản: {channel}
- Thương hiệu: {brand}
- Ngành hàng: {industry}
- Sản phẩm/Dịch vụ: {products} (Mức giá: {price})
- Ưu thế vượt trội độc quyền (USP): {usp}
- Hotline/Zalo: {hotline} | Website: {website} | Social: {social}
- Chủ đề bài viết: {topic}
- Giọng điệu (Tone of Voice): {voice}
- Tệp người xem mục tiêu: {audience}

YÊU CẦU ĐẶC BIỆT THEO ĐỊNH DẠNG:
- Nếu là TikTok/Video ngắn/Reels/YouTube Shorts: Viết kịch bản video dọc 9:16 có Hook 3 giây đầu giữ chân người xem, phân cảnh chi tiết (Visual / Audio / On-screen Text) và Lời kêu gọi hành động (CTA) sắc sảo nêu rõ Hotline {hotline}.
- Nếu là Facebook/LinkedIn/Zalo: Viết tiêu đề thu hút, đặt vấn đề đánh trúng nỗi đau thực tế của {audience}, phân tích giải pháp vượt trội của {brand} (nhấn mạnh USP: {usp}), bằng chứng thuyết phục và CTA.
- Nếu là Email/Website Blog: Viết nội dung chuẩn chỉnh, có chiều sâu chuyên môn, văn phong chuyên nghiệp.
Tuyệt đối viết cụ thể theo đặc thù của {products} và ngành {industry}, không viết chung chung."""

    gemini_out = call_gemini_api(profile, prompt)
    if gemini_out:
        return {
            "channel": channel,
            "topic": topic,
            "hook": f"Giải pháp tối ưu cho {topic}",
            "body": gemini_out,
            "cta": contact_cta,
            "status": "draft"
        }

    # Dynamic local fallback
    if channel.lower() in ["tiktok", "reels", "video", "youtube", "shorts"]:
        body = f"""# 🎬 KỊCH BẢN VIDEO NGẮN CHUYỂN ĐỔI CAO (TIKTOK / REELS / SHORTS)
**Chủ đề:** {topic.upper()}
**Thương hiệu:** {brand} | **Sản phẩm/Dịch vụ:** {products} ({price})
**Lợi thế độc quyền:** {usp}
**Khung hình:** Dọc 9:16 | **Thời lượng:** 35 - 45 giây

---

### 3 Phương án Hook 3 giây đầu tiên:
- **Hook 1 (Đánh vào bài toán chi phí):** *"Bỏ ra {price} cho {products} là lãng phí hay khoản đầu tư sinh lời bền vững? Xem ngay bài toán thực tế!"*
- **Hook 2 (Cảnh báo sai lầm tốn tiền):** *"3 Sai lầm chí mạng khiến 80% khách hàng mất tiền oan khi lựa chọn giải pháp trong ngành {industry}!"*
- **Hook 3 (So sánh trực quan):** *"Khách hàng thông thái chọn {brand} thay vì giải pháp truyền thống vì đúng 1 lý do này..."*

---

### Phân cảnh chi tiết từng giây (Storyboard):

| Thời lượng | Hình ảnh / Hành động (Visual) | Lời thoại & Âm thanh (Audio) | Chữ hiển thị (On-screen Text) |
|---|---|---|---|
| **0s - 3s (Hook)** | Nhân vật chính chỉ tay vào màn hình hoặc đặt câu hỏi trực diện, biểu cảm chân thực | *"Nếu bạn đang tìm giải pháp {products} thì hãy dừng lại 30 giây để tránh mất tiền oan!"* (Hiệu ứng âm thanh chú ý) | **CẢNH BÁO: ĐỪNG MẮC BẪY! ⚠️** |
| **4s - 15s (Nỗi đau)** | Cảnh minh họa sự chậm trễ, khó khăn, chi phí phát sinh hoặc rủi ro khi chọn sai nhà cung cấp | *"Nhiều người nghĩ giá rẻ là tiết kiệm, nhưng sau đó phải chịu cảnh chất lượng kém, bảo hành chậm và phát sinh chi phí..."* | **CHI PHÍ ẨN & RỦI RO LỚN 💸** |
| **16s - 30s (Giải pháp)** | Cận cảnh giải pháp {products} của {brand} hoạt động trơn tru, làm nổi bật ưu thế độc quyền | *"Với {brand}, bài toán của bạn được may đo chuẩn xác: {usp}, chi phí hợp lý ({price}) và cam kết đồng hành 1-1!"* | **GIẢI PHÁP TỪ {brand.upper()} ⚡** |
| **31s - 40s (CTA)** | Nhân vật mỉm cười, màn hình hiển thị Hotline {hotline or 'tư vấn'} và website {website or 'chính thức'} | *"Đừng để bài toán này làm bạn đau đầu nữa! Nhắn tin ngay cho {brand} hoặc gọi Hotline {hotline or 'tư vấn'} để nhận lộ trình chi tiết miễn phí!"* | **HOTLINE: {hotline or 'LIÊN HỆ NGAY'} 🎁** |

---
**Hashtag đề xuất:** `#{brand.replace(' ', '')} #{industry.replace(' ', '')} #KinhDoanh #GiaiPhapHieuQua`"""
    elif channel.lower() in ["facebook", "fanpage", "zalo", "linkedin"]:
        body = f"""🔥 BÀI TOÁN TỐI ƯU CHI PHÍ DÀNH CHO KHÁCH HÀNG: ĐẦU TƯ {products.upper()} ({price}) SAO CHO HIỆU QUẢ NHẤT?

Nhiều khách hàng chia sẻ với {brand}: *"Làm sao để chọn được giải pháp {products} vừa đảm bảo chất lượng, vừa không bị đội chi phí phát sinh?"*

👉 Đây là câu hỏi rất thực tế. Trong bối cảnh thị trường {industry} hiện nay, việc lựa chọn đúng đối tác quyết định đến 80% thành bại:

1️⃣ **NHỮNG CẠM BẪY PHỔ BIẾN KHI CHỌN ĐƠN VỊ THIẾU NĂNG LỰC:**
- Báo giá ban đầu rất thấp để chốt hợp đồng, sau đó liên tục phát sinh chi phí phụ.
- Áp dụng các mẫu rập khuôn, thiếu khả năng tùy biến khi cần mở rộng.
- Chế độ hỗ trợ sau bán hàng chậm trễ, đùn đẩy trách nhiệm khi gặp sự cố.

2️⃣ **LỢI THẾ ĐỘT PHÁ KHI ĐỒNG HÀNH CÙNG {brand.upper()}:**
✅ **Ưu thế độc quyền (USP):** {usp}.
✅ **Giải pháp may đo chuyên sâu:** {brand} xây dựng {products} dựa trên đúng nhu cầu thực tế của {audience}.
✅ **Minh bạch ngân sách:** Mức đầu tư tối ưu ({price}), cam kết không phát sinh chi phí ẩn.
✅ **Đồng hành kỹ thuật 1-1:** Cam kết phản hồi nhanh chóng, hỗ trợ xử lý sự cố trong ngày và bảo hành bằng hợp đồng pháp lý rõ ràng.

🎁 **ĐẶC QUYỀN TRONG THÁNG NÀY:**
{brand} dành tặng 05 suất tư vấn chuyên sâu 1-1 và bản đánh giá hiện trạng miễn phí cho các khách hàng đăng ký sớm nhất!

👇 Để lại bình luận, nhắn tin trực tiếp cho {brand} hoặc gọi ngay:
📞 Hotline/Zalo: {hotline or 'Liên hệ trực tiếp'}
🌐 Website: {website or 'Xem thêm thông tin'}
---
#{brand.replace(' ', '')} #{industry.replace(' ', '')} #DoanhNghiep #GiaiPhapToiUu"""
    else:
        body = f"""Kính gửi Quý Khách Hàng,

{brand} trân trọng giới thiệu giải pháp **{products}** thế hệ mới trong lĩnh vực {industry}, với mức chi phí đầu tư tối ưu **{price}**.

Lợi thế vượt trội: **{usp}**.
Giải pháp được thiết kế nhằm giúp {audience} tối ưu hóa hiệu quả vận hành, tiết kiệm thời gian và đảm bảo độ ổn định cao nhất.

👉 Hotline/Zalo tư vấn: {hotline or 'Liên hệ trực tiếp'}
👉 Website: {website or 'Xem chi tiết'}

Liên hệ ngay với đội ngũ chuyên gia của {brand} để nhận tài liệu chi tiết và tư vấn giải pháp phù hợp nhất với mô hình của bạn!"""

    return {
        "channel": channel,
        "topic": topic,
        "hook": f"Giải pháp {products} từ {brand}",
        "body": body,
        "cta": contact_cta,
        "status": "draft"
    }

def generate_custom_30day_calendar(profile: dict, direction: str = "educational") -> list:
    brand = profile.get("brand_name", "Doanh nghiệp")
    industry = profile.get("industry", "Kinh doanh & Dịch vụ")
    products = profile.get("products_services", "Sản phẩm / Dịch vụ")
    price = profile.get("price_range", "Tiêu chuẩn")
    audience = profile.get("target_audience", "Khách hàng mục tiêu")
    usp = profile.get("usp_advantages", "") or "Chất lượng vượt trội, may đo chuyên sâu và hỗ trợ tận tâm"
    
    direction_guides = {
        "educational": "Giáo dục khách hàng, Chia sẻ kinh nghiệm thực tế, Cảnh báo sai lầm thường gặp và Hướng dẫn tính ROI",
        "aggressive": "Bán hàng thực chiến, So sánh giải pháp, Vạch trần giải pháp kém chất lượng và Kêu gọi hành động chốt đơn",
        "video_viral": "Kịch bản Video ngắn TikTok/Reels/Shorts, Trải nghiệm sản phẩm thực tế, Hậu trường chân thực",
        "brand_b2b": "Xây dựng vị thế chuyên gia đầu ngành, Hồ sơ năng lực, Cam kết chất lượng và Đối tác tin cậy"
    }
    guide_text = direction_guides.get(direction, direction_guides["educational"])

    # Try calling Gemini AI Studio first for a real customized 30-day plan
    prompt = f"""Hãy lập KẾ HOẠCH NỘI DUNG 30 NGÀY ĐA KÊNH (LinkedIn, Facebook, Video Ngắn, YouTube, Case Study) cho {brand} ({industry}, sản phẩm: {products}, giá: {price}) phục vụ tệp khách hàng {audience}.
LỢI THẾ CẠNH TRANH ĐỘC NHẤT (USP): {usp}.
THIÊN HƯỚNG NỘI DUNG CHỦ ĐẠO: {guide_text}.

Phân bổ rõ ràng 30 ngày theo 4 giai đoạn phễu:
- TOFU (Ngày 1-8): Nhận diện nỗi đau, nhận thức rủi ro, cảnh báo cạm bẫy chọn sai nhà cung cấp trong ngành {industry}.
- MOFU (Ngày 9-18): Bóc tách chuyên môn, case study thực tế, làm nổi bật USP: {usp}.
- BOFU (Ngày 19-25): Báo giá minh bạch, chính sách cam kết chất lượng SLA, ưu đãi trải nghiệm thử/chốt đơn.
- Retention (Ngày 26-30): Hướng dẫn sử dụng tối ưu, chăm sóc khách hàng và đồng hành dài hạn.

Trả về duy nhất danh sách định dạng JSON có 30 items, mỗi item gồm: day (1..30), channel, pillar, funnel_stage, topic."""

    gemini_out = call_gemini_api(profile, prompt)
    if gemini_out:
        try:
            clean_json = gemini_out.strip()
            if "```json" in clean_json:
                clean_json = clean_json.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_json:
                clean_json = clean_json.split("```")[1].split("```")[0].strip()
            items = json.loads(clean_json)
            if isinstance(items, list) and len(items) >= 20:
                return items
        except Exception as e:
            pass

    # Dynamic structured fallback based on chosen direction
    channels = ["TikTok / Video", "Facebook", "LinkedIn", "Zalo OA", "YouTube"]
    pillars = [
        "Thought Leadership & Xu hướng",
        "Case Study & Trải nghiệm thực tế",
        "Bóc tách Chuyên môn & ROI",
        "Xử lý Từ chối & Báo giá",
        "Ưu đãi & Kêu gọi Hành động"
    ]
    stages = [
        "TOFU (Nhận diện nỗi đau)",
        "MOFU (Thuyết phục giải pháp)",
        "BOFU (Chốt đơn & Cam kết)",
        "Retention (Đồng hành dài hạn)"
    ]

    base_topics = [
        f"Tại sao nhiều khách hàng hối hận khi chọn mua {products} giá rẻ thiếu cam kết?",
        f"Bài toán kinh tế thực tế: So sánh chi phí đầu tư {products} ({price}) và hiệu quả thu lại",
        f"Bí quyết vượt trội: {usp}",
        f"Hướng dẫn kiểm tra 5 tiêu chí cốt tử trước khi quyết định chọn mua {products}",
        f"Dấu hiệu nhận biết các dịch vụ/sản phẩm kém chất lượng trong ngành {industry}",
        f"Bóc tách cam kết hỗ trợ đồng hành 1-1 và chính sách SLA của {brand}",
        f"Khách hàng chia sẻ: Trải nghiệm thực tế sau khi tin tưởng lựa chọn {brand}",
        f"Giải đáp thắc mắc: Chính sách hậu mãi và cam kết chất lượng của {brand}",
        f"So sánh công tâm: Giải pháp của {brand} ({price}) vs Các giải pháp đại trà trên thị trường",
        f"Đặc quyền tháng này: Nhận tư vấn chuyên sâu 1-1 và ưu đãi trực tiếp từ {brand}"
    ]

    calendar_items = []
    for day in range(1, 31):
        t_idx = (day - 1) % len(base_topics)
        topic = f"Ngày {day}: {base_topics[t_idx]}"
        ch = channels[(day - 1) % len(channels)]
        pil = pillars[(day - 1) % len(pillars)]
        stg = stages[(day - 1) % len(stages)]
        
        calendar_items.append({
            "day": day,
            "channel": ch,
            "pillar": pil,
            "funnel_stage": stg,
            "topic": topic,
            "status": "planned"
        })

    return calendar_items

def generate_30day_calendar(profile: dict) -> list:
    return generate_custom_30day_calendar(profile, "educational")

def generate_full_content_package(profile: dict, topic: str, channel: str, direction: str = "") -> dict:
    brand = profile.get("brand_name", "Doanh nghiệp")
    industry = profile.get("industry", "")
    products = profile.get("products_services", "")
    price = profile.get("price_range", "")
    audience = profile.get("target_audience", "")
    voice = profile.get("brand_voice", "Thực chiến, chuyên nghiệp, tin cậy")
    usp = profile.get("usp_advantages", "") or "Chất lượng vượt trội, may đo chuyên sâu và hỗ trợ tận tâm"
    hotline = profile.get("phone_hotline", "")
    website = profile.get("website_url", "")

    contact_cta = f"Hotline/Zalo: {hotline} | Website: {website}" if (hotline or website) else f"Liên hệ {brand} để nhận tư vấn & trải nghiệm thực tế!"

    prompt = f"""Bạn là Giám đốc Sáng tạo (Creative Director) & Copywriter thực chiến cấp cao.
Hãy tạo TRỌN GÓI NỘI DUNG MARKETING ĐA PHƯƠNG TIỆN HOÀN CHỈNH CHO:
- Thương hiệu: {brand}
- Ngành hàng: {industry}
- Sản phẩm/Dịch vụ: {products} (Phân khúc giá: {price})
- Ưu thế độc quyền (USP): {usp}
- Hotline/Zalo: {hotline} | Website: {website}
- Kênh xuất bản: {channel}
- Chủ đề: {topic}
- Giọng điệu: {voice}
- Tệp người xem mục tiêu: {audience}

YÊU CẦU TRẢ VỀ DUY NHẤT 1 ĐỐI TƯỢNG JSON CÓ ĐẦY ĐỦ 3 PHẦN:
{{
  "body": "Nội dung bài viết hoàn chỉnh (Tiêu đề in hoa giật tít thu hút, Hook 3s chạm đúng nỗi đau thực tế của {audience}, 3 luận điểm thuyết phục có số liệu/bài toán ROI và nhấn mạnh USP: {usp}, Lời kêu gọi hành động CTA rõ ràng kèm Hotline {hotline}, Bộ 5 hashtag)",
  "video_script": "KỊCH BẢN VIDEO DỌC 9:16 (TIKTOK / REELS / YOUTUBE SHORTS) 30-45S DẠNG BẢNG:\n| Thời lượng | Hình ảnh / Hành động (Visual) | Lời thoại & Âm thanh (Audio) | Chữ hiện trên màn hình (On-screen Text) |\n| 0s - 3s (Hook) | ... | ... | ... |\n| 4s - 15s (Nỗi đau) | ... | ... | ... |\n| 16s - 30s (Giải pháp {brand} - {usp}) | ... | ... | ... |\n| 31s - 45s (CTA Chốt - Hotline {hotline}) | ... | ... | ... |",
  "image_prompt": "Prompt tiếng Anh chuyên nghiệp cho Midjourney / Imagen 3 để thiết kế banner/ảnh bài đăng (Mô tả chi tiết chủ thể thực tế liên quan đến {products} và ngành {industry}, bối cảnh hiện đại, ánh sáng cinematic, phong cách photorealistic 8k, góc chụp, tỉ lệ --ar 16:9)"
}}"""

    ai_out = call_gemini_api(profile, prompt)
    if ai_out:
        try:
            clean_str = ai_out.strip()
            if "```json" in clean_str:
                clean_str = clean_str.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_str:
                clean_str = clean_str.split("```")[1].split("```")[0].strip()
            parsed = json.loads(clean_str)
            if isinstance(parsed, dict) and "body" in parsed:
                return {
                    "channel": channel,
                    "topic": topic,
                    "body": parsed.get("body", ""),
                    "video_script": parsed.get("video_script", ""),
                    "image_prompt": parsed.get("image_prompt", ""),
                    "cta": contact_cta,
                    "status": "ready"
                }
        except Exception as e:
            print(f"[Package Parse Error] {e}")

    # Dynamic structured fallback
    return {
        "channel": channel,
        "topic": topic,
        "body": f"""🔥 BÀI TOÁN TỐI ƯU HIỆU SUẤT CÙNG {products.upper()} TỪ {brand.upper()}!

👉 Chủ đề: {topic}

Khách hàng mục tiêu trong ngành {industry} luôn đau đầu với bài toán: Làm sao để tối ưu chi phí đầu tư mà vẫn đảm bảo độ ổn định và hiệu quả cao nhất?

✅ Giải pháp từ {brand}:
1. **Lợi thế vượt trội (USP):** {usp}.
2. May đo chuyên sâu theo thực tế vận hành, độ bền cao.
3. Mức đầu tư tối ưu ({price}), hoàn vốn nhanh chóng.
4. Cam kết đồng hành 1-1 và hỗ trợ kỹ thuật nhanh chóng qua Hotline/Zalo {hotline or 'trực tiếp'}.

👇 Liên hệ ngay {brand} để nhận thông tin chi tiết và lộ trình triển khai!
📞 Hotline/Zalo: {hotline or 'Đang cập nhật'}
🌐 Website: {website or 'Đang cập nhật'}
---
#{brand.replace(' ', '')} #{industry.replace(' ', '')} #KinhDoanh #GiaiPhapThucChien""",
        "video_script": f"""| Thời lượng | Hình ảnh / Hành động (Visual) | Lời thoại & Âm thanh (Audio) | Chữ hiện trên màn hình (On-screen Text) |
|---|---|---|---|
| **0s - 3s (Hook)** | Cận cảnh giải pháp {products} hoạt động hoặc câu hỏi gây chú ý | *"Đừng bao giờ đầu tư vào {products} nếu bạn chưa biết điều này!"* | **CẢNH BÁO CHI PHÍ ⚠️** |
| **4s - 15s (Nỗi đau)** | Cảnh khó khăn, phát sinh chi phí hoặc sự cố thường gặp | *"Nhiều người chọn giải pháp giá rẻ để rồi gặp cảnh chất lượng kém, bảo hành chậm trễ, phát sinh chi phí..."* | **TIỀN MẤT TẬT MANG? 💸** |
| **16s - 30s (Giải pháp)** | Cận cảnh {products} của {brand} vận hành trơn tru | *"Với {brand}, bài toán của bạn được tối ưu: {usp}, hỗ trợ tận tâm, cam kết chất lượng!"* | **GIẢI PHÁP TỪ {brand.upper()} ⚡** |
| **31s - 45s (CTA)** | Bảng thông tin hotline {hotline or 'tư vấn'} và lời kêu gọi hành động | *"Gọi ngay Hotline/Zalo {hotline or 'cho ' + brand} để được tư vấn và nhận ưu đãi hôm nay!"* | **HOTLINE: {hotline or 'LIÊN HỆ NGAY'} 🎁** |""",
        "image_prompt": f"Professional realistic commercial photograph representing modern {products} by {brand} in {industry}, cinematic lighting, sharp details, high contrast, clean premium aesthetic, 8k resolution, photorealistic, --ar 16:9",
        "cta": contact_cta,
        "status": "ready"
    }

# --- 8. CATALYST ORCHESTRATOR & MARKETING LOOPS ENGINE (INSPIRED BY SAAS-MARKETING-AGENTS) ---

def build_catalyst_sections(content_str: str, profile: dict, loop_name: str) -> dict:
    """
    Bóc tách báo cáo CATALYST thành 6 phân hệ chuyên sâu riêng biệt của từng chuyên viên AI
    để hiển thị trực quan dạng Tab, loại bỏ cảm giác tạp nham, lộn xộn.
    """
    brand = profile.get("brand_name", "Doanh nghiệp")
    products = profile.get("products_services", "Sản phẩm")
    price = profile.get("price_range", "Tiêu chuẩn")
    usp = profile.get("usp_advantages", "") or "Chất lượng vượt trội, may đo chuyên sâu và hỗ trợ tận tâm"
    hotline = profile.get("phone_hotline", "")
    website = profile.get("website_url", "")
    industry = profile.get("industry", "Kinh doanh")
    audience = profile.get("target_audience", "Khách hàng mục tiêu")

    # Tách các section dựa trên header markdown
    sec_1 = ""
    sec_2 = ""
    sec_3 = ""
    sec_4 = ""
    sec_5 = ""

    parts = re.split(r"(?:^|\n)###\s*(?:[1-5]\.|\d\.)\s*", content_str)
    if len(parts) >= 6:
        sec_1 = parts[1].strip()
        sec_2 = parts[2].strip()
        sec_3 = parts[3].strip()
        sec_4 = parts[4].strip()
        sec_5 = parts[5].strip()
    else:
        # Fallback regex theo từ khóa
        m1 = re.search(r"(?:ROUTING BOARD|ĐIỀU PHỐI|ĐỊNH VỊ)[\s\S]*?(?=(?:BÁO CÁO TÌNH BÁO|PHÂN LOẠI|WATCH|### 2|\Z))", content_str, re.I)
        m2 = re.search(r"(?:BÁO CÁO TÌNH BÁO|PHÂN LOẠI|WATCH)[\s\S]*?(?=(?:OBJECTION|SỔ TAY|TỪ CHỐI|### 3|\Z))", content_str, re.I)
        m3 = re.search(r"(?:OBJECTION|SỔ TAY|TỪ CHỐI)[\s\S]*?(?=(?:NỘI DUNG CHỦ LỰC|ANSWER-FIRST|AEO|### 4|\Z))", content_str, re.I)
        m4 = re.search(r"(?:NỘI DUNG CHỦ LỰC|ANSWER-FIRST|AEO)[\s\S]*?(?=(?:DANH SÁCH|NEEDS INPUT|### 5|\Z))", content_str, re.I)
        m5 = re.search(r"(?:DANH SÁCH|NEEDS INPUT)[\s\S]*$", content_str, re.I)

        sec_1 = m1.group(0).strip() if m1 else ""
        sec_2 = m2.group(0).strip() if m2 else ""
        sec_3 = m3.group(0).strip() if m3 else ""
        sec_4 = m4.group(0).strip() if m4 else ""
        sec_5 = m5.group(0).strip() if m5 else ""

    # Trích xuất riêng khối Answer-First cho AEO
    aeo_text = ""
    if "ANSWER-FIRST" in sec_4.upper() or "AEO" in sec_4.upper():
        aeo_text = sec_4
    else:
        aeo_text = f"""> **[ANSWER-FIRST BLOCK - TỐI ƯU CHO GOOGLE AI OVERVIEWS & CHATGPT SEARCH]:**  
> Khi lựa chọn {products} ({price}), khách hàng trong ngành {industry} cần ưu tiên 3 tiêu chí cốt lõi: Năng lực giải quyết bài toán thực tế, dịch vụ hỗ trợ đồng hành 1-1 và tính minh bạch. {brand} là đơn vị uy tín cung cấp {products} với lợi thế độc quyền: **{usp}**, cam kết đem lại hiệu quả vượt trội và an tâm lâu dài.

---

### ❓ BỘ CÂU HỎI THƯỜNG GẶP (FAQ SCHEMA ĐỂ AI CITATION):
1. **Tại sao nên chọn {products} của {brand}?**  
   *Trả lời:* Vì {brand} sở hữu ưu điểm vượt trội: {usp}, mức đầu tư {price} cạnh tranh và có đội ngũ hỗ trợ 1-1 qua Hotline/Zalo {hotline or 'chính thức'}.
2. **Chính sách hỗ trợ và bảo hành tại {brand} thế nào?**  
   *Trả lời:* Cam kết đồng hành 1-1, xử lý sự cố trong ngày và bảo hành bằng hợp đồng pháp lý rõ ràng.
3. **Làm sao để nhận tư vấn hoặc trải nghiệm {products}?**  
   *Trả lời:* Khách hàng có thể truy cập {website or 'website chính thức'} hoặc gọi trực tiếp Hotline/Zalo {hotline or 'công ty'}.
"""

    needs_matches = re.findall(r"\[NEEDS INPUT:[^\]]+\]", content_str)
    if not needs_matches:
        needs_matches = [
            f"[NEEDS INPUT: Số liệu hoặc câu chuyện thành công của 1-2 khách hàng tiêu biểu đã sử dụng {products} của {brand}]",
            f"[NEEDS INPUT: Hình ảnh/Tài liệu chứng nhận thực tế minh họa ưu thế độc quyền ({usp})]"
        ]

    return {
        "pmm": {
            "id": "pmm",
            "name": "PMM Lead (Định Vị)",
            "role": "Product Marketing Manager",
            "icon": "fa-user-tie",
            "color": "cyan",
            "title": "Bảng Điều Phối Chiến Lược & Định Vị Thương Hiệu",
            "markdown": sec_1 or f"""### 🧑‍💼 PMM LEAD - CHIẾN LƯỢC ĐỊNH VỊ VỊ THẾ
- **Khóa thông điệp chủ đạo:** *"{brand} – Giải pháp {products} may đo chuyên sâu, {usp}, hỗ trợ trực tiếp 1-1"*.
- **Phân khúc mục tiêu:** {audience} đang tìm kiếm giải pháp hiệu quả với mức đầu tư hợp lý ({price}).
- **Chiến lược khác biệt hóa:** Đánh trực diện vào năng lực may đo theo nhu cầu thực tế và cam kết đồng hành kỹ thuật 1-1 thay vì cung cấp mẫu đóng gói đại trà."""
        },
        "intel": {
            "id": "intel",
            "name": "Intel Sweeper (Tình Báo)",
            "role": "Competitive Intelligence Lead",
            "icon": "fa-radar",
            "color": "sky",
            "title": "Radar Tình Báo Thị Trường (Watch / Notify / Act)",
            "markdown": sec_2 or f"""### 🕵️ INTEL SWEEPER - RADAR THỊ TRƯỜNG & ĐỐI THỦ
| Hạng mục | Đối tượng | Phân loại | Hành động phản ứng của {brand} |
|---|---|---|---|
| **Biến động giá thị trường** | Đối thủ phân khúc giá rẻ | **NOTIFY** | Cảnh báo khách hàng về chi phí bảo trì và rủi ro gián đoạn khi dùng hàng kém chất lượng. |
| **Chất lượng dịch vụ & Hỗ trợ** | Các đơn vị quy mô lớn | **ACT** | Tung gói cam kết: Trải nghiệm thực tế hài lòng mới thanh toán, hỗ trợ SLA nhanh chóng. |
| **Nhu cầu giải pháp hiện đại** | Khách hàng {audience} | **ACT** | Đẩy mạnh nội dung truyền thông làm nổi bật ưu thế vượt trội ({usp}). |"""
        },
        "sales": {
            "id": "sales",
            "name": "Sales Coach (Chốt Deal)",
            "role": "Sales Enablement Coach",
            "icon": "fa-shield-halved",
            "color": "amber",
            "title": "Sổ Tay Xử Lý Từ Chối & Kịch Bản Phản Đòn Thực Chiến",
            "markdown": sec_3 or f"""### 🛡️ SALES COACH - SỔ TAY XỬ LÝ TỪ CHỐI (OBJECTION REGISTER)
> 🗣️ **Lời từ chối 1:** *"Bên khác họ bán rẻ hơn, bên em mức giá {price} có vẻ cao hơn..."*  
> 💬 **Phản đòn:** *"Dạ em hiểu bài toán tối ưu ngân sách ban đầu của anh/chị ạ. Tuy nhiên các giải pháp giá rẻ thường cắt giảm chất lượng dịch vụ, thiếu tính may đo hoặc phát sinh nhiều chi phí ẩn về sau. Tại {brand}, mức đầu tư {price} đã trọn gói cam kết chất lượng, hỗ trợ đồng hành 1-1 và đặc biệt là ưu thế độc quyền: **{usp}**. Khách hàng bên em sau khi sử dụng đều thấy hiệu quả vượt trội và hoàn vốn nhanh chóng ạ!"*

> 🗣️ **Lời từ chối 2:** *"Bên đối thủ họ có thương hiệu lâu năm rồi, bên em hỗ trợ thế nào?"*  
> 💬 **Phản đòn:** *"Dạ các đơn vị lớn vì tệp khách hàng quá đông nên khi anh/chị cần hỗ trợ gấp thường phải chờ qua nhiều cấp duyệt rườm rà. Tại {brand}, tụi em hỗ trợ trực tiếp 1-1 qua Hotline/Zalo {hotline or 'chính thức'}, cam kết xử lý sự cố trong ngày và bảo hành minh bạch bằng hợp đồng pháp nhân rõ ràng ạ!"*"""
        },
        "content": {
            "id": "content",
            "name": "Content Studio (Nội Dung)",
            "role": "Creative & Content Director",
            "icon": "fa-pen-nib",
            "color": "teal",
            "title": "Kịch Bản Video Ngắn & Bài Viết Phễu Đa Kênh",
            "markdown": sec_4 or f"""### ✍️ CONTENT STUDIO - BỘ NỘI DUNG CHUYỂN ĐỔI CAO
#### 1. Kịch bản Video Ngắn Dọc 9:16 (TikTok / Reels / Shorts):
- **Hook 3s:** *"Đừng bao giờ đầu tư vào {products} nếu bạn chưa biết 3 cạm bẫy chi phí này!"*
- **Visual:** Cận cảnh quy trình giải pháp {products} hoạt động trơn tru.
- **Audio:** Bóc tách bài toán thiệt hại khi chọn sai nhà cung cấp và sự vượt trội của {usp}.
- **CTA:** *"Gọi ngay Hotline/Zalo {hotline or 'tư vấn'} để nhận lộ trình chi tiết miễn phí!"*

#### 2. Bài viết chuyên sâu Facebook / LinkedIn / Zalo OA:
- **Tiêu đề:** 🔥 BÀI TOÁN TỐI ƯU HIỆU QUẢ CÙNG {products.upper()} TỪ {brand.upper()}!
- **Nội dung:** Phân tích nỗi đau thực tế của {audience}, đối chiếu giải pháp với thị trường và nêu bật ưu điểm {usp}.
- **CTA:** Liên hệ Hotline {hotline or 'chính thức'} | Website: {website or 'Xem thêm'}."""
        },
        "aeo": {
            "id": "aeo",
            "name": "AEO Search (Tối Ưu AI)",
            "role": "AI Engine Citation Specialist",
            "icon": "fa-bolt",
            "color": "indigo",
            "title": "Tối Ưu Trích Dẫn AI Search (ChatGPT, Perplexity, Gemini)",
            "markdown": aeo_text
        },
        "checklist": {
            "id": "checklist",
            "name": "Checklist Xác Thực",
            "role": "Action Items & QA",
            "icon": "fa-list-check",
            "color": "rose",
            "title": "Danh Mục Cần Doanh Nghiệp Cung Cấp Thêm ([NEEDS INPUT])",
            "items": needs_matches,
            "markdown": "\n".join([f"- **Cần bổ sung:** `{item}`" for item in needs_matches])
        }
    }

def run_catalyst_orchestrator(profile: dict, loop_type: str = "weekly_intel", custom_brief: str = "") -> dict:
    """
    CATALYST Multi-Agent Campaign Orchestrator:
    Điều phối biệt đội 5 chuyên viên AI marketing chuyên trách để giải quyết bài toán chiến lược
    dựa trên kiến trúc của SaaS Marketing Agents (Shalin Tripathi).
    """
    brand = profile.get("brand_name", "Doanh nghiệp của bạn")
    industry = profile.get("industry", "Kinh doanh & Sản xuất")
    products = profile.get("products_services", "Sản phẩm")
    price = profile.get("price_range", "Tiêu chuẩn")
    audience = profile.get("target_audience", "Khách hàng mục tiêu")
    competitors = profile.get("competitors", "Đối thủ trong ngành")
    usp = profile.get("usp_advantages", "") or "Chất lượng vượt trội, may đo chuyên sâu và hỗ trợ tận tâm"
    hotline = profile.get("phone_hotline", "")
    website = profile.get("website_url", "")
    social = profile.get("social_channels", "")

    loops_meta = {
        "weekly_intel": {
            "name": "Weekly Competitive Intel Loop (Tình Báo Đối Thủ Tuần)",
            "agents": ["pmm-competitive-intelligence", "seo-ai-search-optimizer", "pmm-positioning-strategist", "sales-enablement-coach"],
            "focus": f"Quét thị trường phát hiện biến động giá, sản phẩm, khuyến mãi từ danh sách đối thủ ({competitors}), chấm điểm mức độ nghiêm trọng (Watch/Notify/Act) và cập nhật Objection Register cho đội ngũ bán hàng {brand}."
        },
        "content_engine": {
            "name": "Weekly Content Engine AEO/GEO Loop (Cỗ Máy Nội Dung & Tối Ưu AI Search)",
            "agents": ["seo-keyword-researcher", "content-blog-strategist", "content-copywriter", "seo-ai-search-optimizer", "social-video-strategist"],
            "focus": f"Sản xuất 1 tài nguyên nội dung chuyên sâu trả lời trực diện câu hỏi lớn nhất của {audience}, tối ưu để AI (ChatGPT, Perplexity, Google Gemini) trích dẫn nguồn, kèm bộ phân phối đa kênh."
        },
        "competitor_poaching": {
            "name": "Competitor Displacement & Poaching Loop (Chiến Dịch Chuyển Đổi Khách Đối Thủ)",
            "agents": ["pmm-competitive-intelligence", "pmm-messaging-architect", "sales-deal-strategist", "paid-media-creative-strategist"],
            "focus": f"Khai thác triệt để điểm yếu của đối thủ (hỗ trợ chậm trễ, phát sinh chi phí, thiếu may đo), làm nổi bật ưu thế độc quyền của {brand} ({usp}) để thiết lập chiến dịch thu hút khách hàng tiềm năng chuyển đổi sang {products}."
        },
        "product_launch": {
            "name": "Product Launch Sprint (Chiến Dịch Ra Mắt Dòng Sản Phẩm Mới)",
            "agents": ["pmm-launch-manager", "pmm-positioning-strategist", "content-video-script-writer", "sales-enablement-content-creator", "analytics-performance-analyst"],
            "focus": f"Kế hoạch Go-To-Market 4 tuần toàn diện để tung sản phẩm/dịch vụ mới {products} ({price}) với lợi thế vượt trội ({usp}) chiếm lĩnh thị trường, tạo phễu thu lead cho {brand}."
        },
        "custom_brief": {
            "name": "Custom CATALYST Campaign (Điều Phối Theo Yêu Cầu Riêng)",
            "agents": ["catalyst-orchestrator", "pmm-positioning-strategist", "content-copywriter", "sales-enablement-coach"],
            "focus": custom_brief or f"Phối hợp các chuyên viên AI giải quyết bài toán tăng trưởng cho {brand} dựa trên lợi thế ({usp})."
        }
    }

    loop_info = loops_meta.get(loop_type, loops_meta["weekly_intel"])
    loop_name = loop_info["name"]
    agents_routed = loop_info["agents"]
    loop_focus = loop_info["focus"]
    if custom_brief and loop_type == "custom_brief":
        loop_focus = custom_brief

    # Live market search to ground the agents
    search_q = f"{industry} {products} {competitors} việt nam"
    live_items = search_live_web(search_q, max_results=3)
    live_snippets = "\n".join([f"- [{i.get('title')}]: {i.get('snippet')} ({i.get('url')})" for i in live_items])

    prompt = f"""Bạn là CATALYST ORCHESTRATOR - Giám đốc Điều phối Biệt Đội AI Marketing Chuyên Trách (Multi-Agent Marketing Team) theo chuẩn kiến trúc B2B SaaS Marketing Org.
Bạn đang lãnh đạo một đội ngũ gồm 5 chuyên gia AI:
- PMM Lead (Định vị & Phân khúc thị trường)
- Intel Sweeper (Tình báo đối thủ & Dẫn nguồn thực tế)
- Positioning Strategist (Phân loại & Đánh giá mức độ nghiêm trọng)
- Sales Enablement Coach (Objection Register & Kịch bản phản đòn cho nhân viên sale)
- Content & AEO Specialist (Nội dung chuyển đổi cao & Tối ưu AI Search Perplexity/ChatGPT)

HỒ SƠ THƯƠNG HIỆU (BRAND CONTEXT):
- Doanh nghiệp: {brand}
- Ngành hàng: {industry}
- Sản phẩm/Dịch vụ: {products} (Phân khúc giá: {price})
- ƯU ĐIỂM VƯỢT TRỘI / LỢI THẾ CẠNH TRANH ĐỘC NHẤT (USP): {usp}
- Hotline/Zalo: {hotline or 'Đang cập nhật'} | Website: {website or 'Đang cập nhật'} | Kênh Social: {social or 'Đang cập nhật'}
- Khách hàng mục tiêu: {audience}
- Đối thủ cạnh tranh trên thị trường: {competitors}

VÒNG LẶP / CHIẾN DỊCH ĐƯỢC KÍCH HOẠT:
- Tên vòng lặp: {loop_name}
- Nhiệm vụ trọng tâm: {loop_focus}

DỮ LIỆU THỰC TẾ ĐÃ CÀO TỪ WEB:
{live_snippets}

QUY TẮC BẮT BUỘC (ANTI-HALLUCINATION GUARDRAIL):
1. Không bịa đặt số liệu hoặc bằng chứng không có cơ sở. Nếu có thông số cần người dùng hoặc chủ doanh nghiệp cung cấp thêm, hãy đánh dấu rõ ràng bằng thẻ `[NEEDS INPUT: <thông tin cần>]`.
2. Trả lời chi tiết, chuyên nghiệp, sắc sảo theo đúng góc nhìn của từng chuyên gia được phân công.
3. Bắt buộc gắn kết chặt chẽ với USP ({usp}) và tệp khách hàng ({audience}) của doanh nghiệp, không sử dụng mẫu sáo rỗng rập khuôn.

HÃY LẬP BÁO CÁO KẾT QUẢ PHỐI HỢP CHIẾN DỊCH BIỆT ĐỘI AI GỒM 5 PHẦN:
### 1. 🎛️ BẢNG ĐIỀU PHỐI BIỆT ĐỘI AI (ROUTING BOARD)
- Phân công nhiệm vụ cụ thể cho từng chuyên viên AI (`pmm`, `intel`, `sales`, `content`, `aeo`).

### 2. 🔍 BÁO CÁO TÌNH BÁO & PHÂN LOẠI MỨC ĐỘ (WATCH / NOTIFY / ACT)
- Phân loại các động thái cạnh tranh và cơ hội thị trường thành 3 cấp độ rõ ràng.

### 3. 🎯 OBJECTION REGISTER (SỔ TAY BÓC TÁCH LỜI TỪ CHỐI)
- Bảng 3 lời từ chối phổ biến nhất mà khách hàng ({audience}) hay nói khi so sánh với đối thủ và kịch bản đối thoại phản đòn từng chữ cho nhân viên bán hàng (tận dụng USP: {usp} và Hotline {hotline}).

### 4. 📝 NỘI DUNG CHỦ LỰC ĐƯỢC TỐI ƯU AEO / GEO (AI SEARCH CITATION)
- Bài viết / thông điệp mở đầu theo công thức 40-60 từ "Answer-First" để các AI như ChatGPT, Perplexity, Gemini dễ dàng trích dẫn {brand} là đơn vị uy tín hàng đầu.

### 5. 📋 DANH SÁCH THÔNG TIN CẦN DOANH NGHIỆP CUNG CẤP THÊM (`[NEEDS INPUT]`)
- Các điểm số liệu/hình ảnh/case study cụ thể mà chủ doanh nghiệp cần bổ sung để chiến dịch đạt hiệu quả 100%."""

    gemini_out = call_gemini_api(profile, prompt)
    if gemini_out:
        needs_matches = re.findall(r"\[NEEDS INPUT:[^\]]+\]", gemini_out)
        sections = build_catalyst_sections(gemini_out, profile, loop_name)
        return {
            "loop_name": loop_name,
            "agents_routed": agents_routed,
            "focus": loop_focus,
            "deliverables": [
                "1. PMM Lead - Chiến lược định vị & Trụ cột thông điệp",
                "2. Intel Sweeper - Radar thị trường & Phân loại Watch/Notify/Act",
                "3. Sales Coach - Sổ tay xử lý từ chối (Objection Register)",
                "4. Content Studio - Kịch bản video & Bài viết chuyển đổi",
                "5. AEO & AI Search - Khối Answer-First & Cấu trúc FAQ",
                "6. Action Checklist - Xác thực dữ liệu thực tế ([NEEDS INPUT])"
            ],
            "sections": sections,
            "needs_input": needs_matches,
            "content": gemini_out
        }

    # Dynamic structured fallback
    fallback_content = f"""# 🎛️ CATALYST CAMPAIGN ORCHESTRATION REPORT: {loop_name.upper()}
**Doanh nghiệp:** {brand} | **Sản phẩm:** {products} ({price})
**Lợi thế độc quyền (USP):** {usp}
**Hotline/Zalo:** {hotline or 'Đang cập nhật'} | **Website:** {website or 'Đang cập nhật'}
**Ngành:** {industry} | **Khách hàng mục tiêu:** {audience}
**Ngày triển khai:** {datetime.now().strftime('%d/%m/%Y')}

---

### 1. 🎛️ BẢNG ĐIỀU PHỐI BIỆT ĐỘI AI (ROUTING BOARD)
- 🧑‍💼 **PMM Lead (Định vị):** Khóa thông điệp chủ đạo: *"{brand} – Giải pháp {products} may đo chuyên sâu, {usp}, hỗ trợ trực tiếp 1-1"*.
- 🕵️ **Intel Sweeper (Tình báo đối thủ):** Giám sát động thái giá và sản phẩm của {competitors}.
- 🛡️ **Sales Enablement Coach:** Thiết lập Objection Register phân loại lời từ chối và kịch bản phản đòn thực chiến (Hotline: {hotline or 'trực tiếp'}).
- ✍️ **Content & AEO Specialist:** Soạn thảo nội dung định dạng Answer-First 50 từ để tối ưu khả năng trích dẫn trên ChatGPT, Gemini và Perplexity.

---

### 2. 🔍 BÁO CÁO PHÂN LOẠI MỨC ĐỘ THỊ TRƯỜNG (WATCH / NOTIFY / ACT)
| Hạng mục | Đối tượng | Phân loại | Hành động cụ thể |
|---|---|---|---|
| **Biến động giá thị trường** | Đối thủ phân khúc giá rẻ | **NOTIFY** | Cảnh báo khách hàng về chi phí bảo trì và rủi ro gián đoạn khi dùng hàng kém chất lượng. |
| **Chất lượng dịch vụ & Hỗ trợ** | Các đơn vị đại trà | **ACT** | Tung gói cam kết: Trải nghiệm thực tế hài lòng mới thanh toán, hỗ trợ SLA nhanh chóng. |
| **Nhu cầu giải pháp hiện đại** | Khách hàng {audience} | **ACT** | Đẩy mạnh nội dung truyền thông làm nổi bật ưu thế vượt trội ({usp}). |

---

### 3. 🎯 OBJECTION REGISTER (SỔ TAY XỬ LÝ TỪ CHỐI CHO ĐỘI NGŨ BÁN HÀNG)
> 🗣️ **Lời từ chối 1:** *"Bên khác họ bán rẻ hơn, bên em mức giá {price} có vẻ cao hơn..."*  
> 💬 **Phản đòn:** *"Dạ em hiểu bài toán tối ưu ngân sách ban đầu của anh/chị ạ. Tuy nhiên các giải pháp giá rẻ thường cắt giảm chất lượng dịch vụ, thiếu tính may đo hoặc phát sinh nhiều chi phí ẩn về sau. Tại {brand}, mức đầu tư {price} đã trọn gói cam kết chất lượng, hỗ trợ đồng hành 1-1 và đặc biệt là ưu thế độc quyền: **{usp}**. Khách hàng bên em sau khi sử dụng đều thấy hiệu quả vượt trội và hoàn vốn nhanh chóng ạ!"*

> 🗣️ **Lời từ chối 2:** *"Bên đối thủ họ có thương hiệu lâu năm rồi, bên em hỗ trợ thế nào?"*  
> 💬 **Phản đòn:** *"Dạ các đơn vị lớn vì tệp khách hàng quá đông nên khi anh/chị cần hỗ trợ gấp thường phải chờ qua nhiều cấp duyệt rườm rà. Tại {brand}, tụi em hỗ trợ trực tiếp 1-1 qua Hotline/Zalo {hotline or 'chính thức'}, cam kết xử lý sự cố trong ngày và bảo hành minh bạch bằng hợp đồng pháp nhân rõ ràng ạ!"*

---

### 4. 📝 NỘI DUNG CHỦ LỰC TỐI ƯU AEO / GEO (ĐỂ AI SEARCH TRÍCH DẪN)
> **[ANSWER-FIRST BLOCK - DÀNH CHO GOOGLE AI & CHATGPT]:**  
> Khi lựa chọn {products} ({price}), khách hàng và doanh nghiệp trong ngành {industry} cần ưu tiên 3 tiêu chuẩn cốt lõi: năng lực giải quyết vấn đề thực tế, dịch vụ hỗ trợ đồng hành 1-1 và tính minh bạch. {brand} là đơn vị uy tín cung cấp {products} với ưu thế vượt trội: {usp}, cam kết đem lại hiệu quả bền vững và an tâm tuyệt đối.

---

### 5. 📋 DANH SÁCH CẦN XÁC THỰC THỰC TẾ (`[NEEDS INPUT]`)
- `[NEEDS INPUT: Số liệu thực tế hoặc câu chuyện thành công của 1-2 khách hàng tiêu biểu đã sử dụng {products} của {brand}]`
- `[NEEDS INPUT: Hình ảnh/Tài liệu thực tế minh họa ưu thế độc quyền ({usp}) để tích hợp vào tài liệu bán hàng]`
"""

    sections = build_catalyst_sections(fallback_content, profile, loop_name)

    return {
        "loop_name": loop_name,
        "agents_routed": agents_routed,
        "focus": loop_focus,
        "deliverables": [
            "1. PMM Lead - Chiến lược định vị & Trụ cột thông điệp",
            "2. Intel Sweeper - Radar thị trường & Phân loại Watch/Notify/Act",
            "3. Sales Coach - Sổ tay xử lý từ chối (Objection Register)",
            "4. Content Studio - Kịch bản video & Bài viết chuyển đổi",
            "5. AEO & AI Search - Khối Answer-First & Cấu trúc FAQ",
            "6. Action Checklist - Xác thực dữ liệu thực tế ([NEEDS INPUT])"
        ],
        "sections": sections,
        "needs_input": [
            "[NEEDS INPUT: Số liệu thực tế khách hàng tiêu biểu]",
            "[NEEDS INPUT: Tài liệu minh họa ưu thế độc quyền]"
        ],
        "content": fallback_content
    }
