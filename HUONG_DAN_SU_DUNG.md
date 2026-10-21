# 📖 HƯỚNG DẪN SỬ DỤNG HỆ THỐNG TỰ ĐỘNG HÓA MARKETING OS
*(Ứng Dụng Phần Mềm Vận Hành Marketing Toàn Diện - Dành Cho Doanh Nghiệp)*

Chào mừng bạn đến với **Marketing OS**! Đây là **phần mềm hệ thống tự động hóa marketing hoàn chỉnh**, có giao diện đồ họa (Web App), tích hợp trực tiếp **Google AI Studio (Gemini 1.5)** và động cơ trí tuệ nhân tạo nội bộ.

---

## 🚀 1. CÁCH KHỞI ĐỘNG HỆ THỐNG (1 CÚ CLICK)

Bạn có 2 cách cực kỳ đơn giản để mở phần mềm:
- **Cách 1 (Nhanh nhất):** Nhấp đúp chuột vào file **[`start_marketing_os.bat`](file:///C:/Users/Admin/.gemini/antigravity/scratch/marketing-os/start_marketing_os.bat)**.
- **Cách 2 (Bằng dòng lệnh):** Mở terminal và gõ:
  ```bash
  cd C:\Users\Admin\.gemini\antigravity\scratch\marketing-os
  python run_app.py
  ```

👉 Trình duyệt sẽ tự động bật lên địa chỉ: **`http://localhost:8000`**.

---

## 🖥️ 2. HƯỚNG DẪN SỬ DỤNG GIAO DIỆN PHẦN MỀM

Giao diện phần mềm được chia thành các phân hệ chuyên nghiệp:

### 🏢 Phân hệ 1: Hồ sơ Doanh nghiệp & Kết nối AI Studio
- **Nhập thông tin doanh nghiệp của bạn:**
  - Tên thương hiệu, Ngành hàng, Mô hình (B2C, D2C, B2B...).
  - Sản phẩm/dịch vụ chủ lực, khoảng giá, khách hàng mục tiêu.
  - Danh sách 3–5 đối thủ cạnh tranh chính.
  - Ngân sách và giọng điệu thương hiệu mong muốn.
- **Kết nối Google AI Studio (Tùy chọn):** Dán Gemini API Key từ `https://aistudio.google.com/` vào ô API Key. *(Nếu chưa có key, hệ thống vẫn tự động chạy bằng Động cơ Thông minh Nội bộ)*.
- **Bấm "Lưu Hồ Sơ":** Toàn bộ hệ thống sẽ cập nhật ngay lập tức theo thông tin của bạn!

### 🔍 Phân hệ 2: Nghiên cứu Thị trường AI (Market Research)
- Nhấp nút **"Chạy Phân Tích Bằng AI"**:
- Hệ thống sẽ tự động quét, tính toán và xuất báo cáo:
  - Quy mô thị trường **TAM / SAM / SOM** cho ngành của bạn.
  - Phân tích vĩ mô **PESTEL** (Chính trị, Kinh tế, Xã hội, Công nghệ...).
  - Phân tích **5 Lực lượng Cạnh tranh Porter**.
  - 3 Cơ hội tăng trưởng và 3 rủi ro cần phòng tránh.

### ⚔️ Phân hệ 3: Tình báo Đối thủ & Battlecards
- Nhấp nút **"Soi Đối Thủ & Tạo Battlecards"**:
- Hệ thống tự động phân tích từng đối thủ bạn đã nhập:
  - Điểm mạnh, điểm yếu cốt tử của đối thủ.
  - Vũ khí và lợi thế để bạn giành chiến thắng (Where We Win).
  - **Kịch bản xử lý từ chối (Objection Handling):** Hướng dẫn nhân viên phản hồi khi khách hàng so sánh giá hoặc khen đối thủ.

### 🎯 Phân hệ 4: Chân dung Khách hàng (Buyer Personas)
- Nhấp nút **"Tạo 3 Chân Dung Khách Hàng"**:
- AI tự động xây dựng 3 nhóm khách hàng mục tiêu với đầy đủ: Nỗi đau, mong muốn, kênh tiêu thụ thông tin và thông điệp tiếp cận (Elevator Pitch) hiệu quả nhất.

### ✍️ Phân hệ 5: Xưởng Sản Xuất Nội Dung (Content Studio)
- Chọn kênh muốn tạo: **TikTok (Video ngắn 9:16 có hook 3s)**, **Facebook Post**, **Blog SEO**, **Email Nurture**, hoặc **Quảng cáo Ads Copy**.
- Nhập chủ đề bạn muốn viết (hoặc bấm chọn nhanh gợi ý).
- Nhấp **"Tạo Nội Dung Bằng AI"**: Bản thảo hoàn chỉnh sẽ xuất hiện ngay lập tức kèm nút **"Sao chép toàn bộ"**.

### 📅 Phân hệ 6: Lịch Nội Dung 30 Ngày (Content Calendar)
- Nhấp **"Tạo Kế Hoạch 30 Ngày Mới"**: Hệ thống tự động sinh ma trận 30 ngày đăng bài bám sát theo phễu (TOFU/MOFU/BOFU) và các trụ cột nội dung.

### 📊 Phân hệ 7: Báo Cáo & Chỉ Số (Dashboard)
- Theo dõi các chỉ số quan trọng: **MER** (Hiệu quả tổng), **ROAS** (Lợi nhuận ads), **CAC** (Chi phí thu nạp khách mới).
- Có form nhập nhanh chi tiêu và đơn hàng mỗi ngày.

---

## 🤖 3. VẬN HÀNH TỰ ĐỘNG THEO LỊCH (CRON JOBS)

Bên cạnh giao diện phần mềm trực quan, toàn bộ **18 lịch chạy tự động** (A01 - A17) đã được cài đặt sẵn vào Antigravity.
- Bạn có thể xem và bật các lịch tự động tại: [Trang Automations của Antigravity](sidecar://dashboard).
- Ví dụ:
  - **07:00 sáng:** Tự động tạo bản tin thị trường ngày.
  - **08:00 sáng:** Tự động soạn bản nháp nội dung cho 2 ngày tới.
  - **08:30 sáng:** Lập báo cáo Standup công việc trong ngày.
  - **22:00 đêm:** Tự động sao lưu dữ liệu và kiểm tra sức khỏe hệ thống.

---
*Bây giờ bạn chỉ cần nhấp đúp vào [`start_marketing_os.bat`](file:///C:/Users/Admin/.gemini/antigravity/scratch/marketing-os/start_marketing_os.bat) để bắt đầu sử dụng phần mềm!*
