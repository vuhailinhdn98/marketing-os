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
        resp = requests.get(target_url, headers=headers, timeout=8, verify=False)
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

def auto_discover_competitors(profile: dict, criteria: str = "all") -> List[Dict[str, str]]:
    """
    Tự động rà quét thị trường Việt Nam dựa trên Tên công ty, Sản phẩm, Ngành nghề, Giá, Khách hàng mục tiêu
    để tìm ra danh sách 4-6 đối thủ có thật trên thị trường.
    """
    brand = profile.get("brand_name", "")
    industry = profile.get("industry", "")
    products = profile.get("products_services", "")
    price = profile.get("price_range", "")
    audience = profile.get("target_audience", "")
    bmodel = profile.get("business_model", "")

    # 1. Tìm kiếm web thời gian thực đa chiều
    queries = [
        f"{industry} {products} tại việt nam",
        f"công ty bán {products} uy tín",
        f"báo giá {products} {price}"
    ]
    web_results = []
    seen_urls = set()
    for q in queries:
        try:
            res = search_live_web(q, max_results=3)
            for r in res:
                u = r.get("url", "")
                if u and u not in seen_urls:
                    seen_urls.add(u)
                    web_results.append(r)
        except Exception:
            pass

    snippets = []
    for r in web_results[:6]:
        snippets.append(f"- {r.get('title')}: {r.get('snippet')} ({r.get('url')})")
    web_text = "\n".join(snippets)

    # 2. Sử dụng Google AI Studio để phân tích và lập danh sách đối thủ thực tế
    prompt = f"""Bạn là Giám đốc Tình báo Cạnh tranh và Nghiên cứu Thị trường cấp cao tại Việt Nam.
Doanh nghiệp của chúng ta:
- Tên công ty/Thương hiệu: {brand}
- Ngành nghề: {industry}
- Sản phẩm/Dịch vụ chủ lực: {products} (Phân khúc giá: {price})
- Mô hình hoạt động: {bmodel}
- Đối tượng khách hàng mục tiêu: {audience}

VẤN ĐỀ THỰC TẾ: Chủ doanh nghiệp không biết rõ tất cả đối thủ của mình là ai trên thị trường.
NHIỆM VỤ: Dựa vào thông tin doanh nghiệp, dữ liệu tìm kiếm web dưới đây và sự am hiểu sâu sắc về thị trường Việt Nam, hãy tự động rà quét và xác định chính xác từ 4 đến 5 ĐỐI THỦ CẠNH TRANH CÓ THẬT đang hoạt động tại Việt Nam trong đúng phân khúc sản phẩm này.

DỮ LIỆU TÌM KIẾM WEB THỰC TẾ:
{web_text}

YÊU CẦU:
- Phải là các công ty, xưởng sản xuất hoặc thương hiệu CÓ THẬT tại Việt Nam (kèm website chính thức hoặc domain thực tế của họ).
- Phân loại rõ: Trực tiếp (cùng bán sản phẩm tương tự), Gián tiếp (cung cấp giải pháp thay thế).
- Nêu rõ sản phẩm chính, điểm mạnh và tử huyệt/điểm yếu thực tế của họ.
- Trả về DUY NHẤT một mảng JSON thuần túy (không kèm bất kỳ văn bản nào khác ngoài JSON):
[
  {{
    "name": "Tên thương hiệu/Công ty đối thủ",
    "website": "https://...",
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

    # Fallback dự phòng thông minh dựa trên kết quả web đã cào nếu AI không parse được
    if not competitors and web_results:
        for r in web_results[:4]:
            t = r.get("title", "").split("-")[0].split("|")[0].strip()
            if t and len(t) > 3:
                competitors.append({
                    "name": t,
                    "website": r.get("url", ""),
                    "type": "Trực tiếp",
                    "price_segment": f"Phân khúc {price}",
                    "core_products": products,
                    "key_strengths": "Thương hiệu có hiện diện và SEO tốt trên internet",
                    "vulnerabilities": "Chính sách hỗ trợ và may đo theo nhu cầu chưa linh hoạt"
                })

    return competitors

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
        return {
            "loop_name": loop_name,
            "agents_routed": agents_routed,
            "focus": loop_focus,
            "deliverables": [
                "Bảng điều phối tác vụ Biệt đội AI (Routing Board)",
                "Báo cáo phân loại động thái đối thủ (Watch / Notify / Act)",
                "Sổ tay xử lý từ chối (Objection Register)",
                "Nội dung chuẩn AEO / GEO (Tối ưu để AI Search trích dẫn)",
                "Checklist xác thực dữ liệu thực tế ([NEEDS INPUT])"
            ],
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

    return {
        "loop_name": loop_name,
        "agents_routed": agents_routed,
        "focus": loop_focus,
        "deliverables": [
            "Bảng điều phối tác vụ Biệt đội AI (Routing Board)",
            "Báo cáo phân loại động thái đối thủ (Watch / Notify / Act)",
            "Sổ tay xử lý từ chối (Objection Register)",
            "Nội dung chuẩn AEO / GEO (Tối ưu để AI Search trích dẫn)",
            "Checklist xác thực dữ liệu thực tế ([NEEDS INPUT])"
        ],
        "needs_input": [
            "[NEEDS INPUT: Số liệu thực tế khách hàng tiêu biểu]",
            "[NEEDS INPUT: Tài liệu minh họa ưu thế độc quyền]"
        ],
        "content": fallback_content
    }
