# 📖 HƯỚNG DẪN SỬ DỤNG MARKETING OS 4.0

Marketing OS là web app giúp chủ shop và người làm marketing ở doanh nghiệp nhỏ làm marketing có quy trình: hiểu khách trước, viết nội dung có kiểm duyệt, ghi khách vào phễu và đo bằng số thật.

Nguyên tắc của hệ thống:
- **Bối cảnh trước, chiến thuật sau**: mọi tác vụ AI đọc Hồ sơ bối cảnh. Thiếu thông tin cốt lõi thì hệ thống hỏi lại, không đoán.
- **Không tự chế**: khi AI lỗi hoặc chưa có key, màn hình báo “Chưa tạo được” kèm lý do; không có nội dung mẫu hay số liệu giả.
- **Có nguồn gốc**: mỗi kết quả ghi model, thời điểm, phiên bản hồ sơ, nguồn tìm kiếm (nếu có).
- **Có cổng duyệt**: nội dung còn lỗi tuân thủ không thể chuyển sang “Đã duyệt” hay xuất bản.

---

## 1. Khởi động

- Windows: nhấp đúp **`start_marketing_os.bat`** (lần đầu tự cài thư viện).
- Hoặc: `pip install -r requirements.txt` rồi `python run_app.py`, mở **http://localhost:8000**.

**Tạo tài khoản** bằng email + mật khẩu (ít nhất 8 ký tự, có chữ và số). Tài khoản đầu tiên là quản trị.
Đã dùng bản cũ (chỉ nhập email)? Chọn **Tạo tài khoản** với đúng email cũ để đặt mật khẩu; dữ liệu cũ được giữ.

## 2. Ba việc đầu tiên

1. **Cài đặt → Gemini API**: dán key lấy tại https://aistudio.google.com/apikey → **Kiểm tra kết nối** (hiện danh sách model khả dụng). Để trống “Model ưu tiên” để hệ thống tự chọn và tự đổi model khi hết hạn mức.
2. **Hồ sơ bối cảnh → Phỏng vấn nhanh 5 câu**: trả lời các mục cốt lõi (sản phẩm, ai mua, giá, biên lãi gộp, kênh, khu vực…). Lặp lại đến khi thanh đầy đủ trên 70%.
3. **Tổng quan → Khởi động nhanh**: chạy nền trụ cột nội dung, lịch 14 ngày và ý tưởng marketing; theo dõi ở “Nhật ký hệ thống”.

## 3. Các màn hình

### Tổng quan
Độ đầy đủ hồ sơ, số liệu nhanh, quy trình 6 bước mỗi tuần, các dịp lễ trong 60 ngày tới kèm ngày nên bắt đầu chuẩn bị, kết quả AI gần đây và nhật ký.

### Hồ sơ bối cảnh
12 nhóm thông tin theo skill marketing: thương hiệu, sản phẩm & kinh tế đơn vị, khách hàng & vấn đề, 4 lực chuyển đổi, cạnh tranh, ngôn ngữ khách, bằng chứng & FAQ, mục tiêu & kênh.
- Ô nhiều dòng: mỗi dòng một ý. Danh sách giá: `Tên | giá`. Lời từ chối: `khách nói | cách trả lời`. Bằng chứng: `loại | nội dung | nguồn | có/không được phép dùng`. FAQ: `câu hỏi | câu trả lời`.
- Mỗi lần lưu tạo một phiên bản; ghi “Vì sao thay đổi” để sau này biết lý do (xem **Nhật ký thay đổi**).

### Skill Studio
26 tác vụ chia 8 nhóm: Chiến lược, Ưu đãi & Nội dung, Quảng cáo, Khách hàng & Bán hàng, Giữ chân, SEO & Local, PR & KOL, Đo lường. Tác vụ có biểu tượng Google dùng tìm kiếm thật và liệt kê nguồn.
- Thiếu thông tin hồ sơ → hiện câu hỏi ngay trong khung kết quả; trả lời xong bấm **Lưu và chạy lại**.
- Kết quả có: model & nguồn, **cổng tuân thủ** (đỏ = phải sửa, vàng = nên xem), phần **Hệ thống đã kiểm/tính lại** (các con số do code tính, không do AI), **Cần bổ sung**, **Bài học**.
- Nút lưu đúng chỗ: phương án bài viết → Kho nội dung; lịch → Lịch nội dung; ngân sách → Ngân sách tháng; vòng lặp tuần → Thử nghiệm; tìm/hồ sơ đối thủ → Danh sách đối thủ; VoC → câu nguyên văn vào Hồ sơ; prompt ảnh → Ảnh & Video.
- Tải `.md`, sao chép, xem lại lịch sử và **Chạy lại với đầu vào này**.

### Nghiên cứu & Đối thủ
Danh sách đối thủ (nhập tay hoặc từ tìm kiếm, có link nguồn), battlecard, nút lập/cập nhật hồ sơ đối thủ. Kết quả nghiên cứu của bản cũ nằm trong mục riêng, gắn nhãn “Chưa kiểm chứng”.

### Kho nội dung
Bảng 7 cột: Ý tưởng → Bản nháp → Chờ duyệt → Đã duyệt → Đã lên lịch → Đã đăng → Đã đo.
- Mở thẻ để sửa, xem cổng tuân thủ, đổi phương án AI, chuyển trạng thái, **Biên tập bằng AI**.
- Sửa bài đã duyệt → tự quay về Chờ duyệt.
- Có khan hiếm thật (“chỉ còn 20 hộp”)? Ghi bằng chứng vào ô “Bằng chứng giới hạn có thật”.
- **Xuất bản qua webhook** (Zapier/Make/n8n, cấu hình trong Cài đặt): chỉ đánh dấu “Đã đăng” khi webhook nhận thành công. Sau khi đăng có checklist quảng bá 11 bước.

### Lịch nội dung
Xem 14/31/60 ngày, có ngày lễ dương lịch, âm lịch và mùa sale. Mỗi dòng: kênh, giai đoạn phễu, trụ cột, loại (tìm được/chia sẻ được/thử nghiệm), hook, CTA, chỉ số đo. **Viết bằng AI** mở Gói nội dung đa kênh; **Đưa vào kho** tạo ý tưởng trong Kho nội dung.

### Ảnh & Video
Tạo ảnh từ mô tả (model ảnh Gemini) và video (Veo, cần key có bật thanh toán; bấm **Kiểm tra** để cập nhật). Không dùng người nổi tiếng, nhân vật hay logo có bản quyền.

### Khách hàng (CRM)
Phễu 6 tầng (Mới → Đang tư vấn → Mua lần đầu → Mua lần 2+ → Giới thiệu → Thân quen) và cột Mất (ghi lý do).
- **Đồng ý tiếp thị**: chỉ đánh dấu khi khách đồng ý rõ ràng, ghi lại khách đồng ý điều gì, qua kênh nào. Khách rút lại → bấm “Khách rút lại đồng ý”.
- **CSV đã đồng ý**: danh sách được phép gửi tiếp thị. **CSV tất cả**: lưu trữ nội bộ.
- **Nhận lead từ form**: lấy mã form mẫu dán vào landing page; lead tự vào cột Mới kèm UTM.
- Bảng **nút thắt** chỉ ra bước chuyển yếu nhất (cần ít nhất 5 khách mỗi tầng).

### Growth Console
- **Tổng quan**: doanh thu, tổng chi marketing, **MER** (doanh thu ÷ tổng chi), **ROAS** so với **ROAS hòa vốn** (= 1 ÷ biên lãi gộp), **lãi gộp sau marketing**, **CAC** (chỉ tính khi có số khách mới), chi phí mỗi đơn, chi phí mỗi lead; biểu đồ theo ngày; bảng theo kênh.
- **Nhập số liệu**: nhập tay theo ngày/kênh; hoặc nhập CSV từ nền tảng (đặt tên file `ads_`, `sales_`, `web_`, `social_`, `email_`, `seo_`, `spend_`, `leads_`…; file mẫu trong `data/samples/`). Nhập lại cùng khoảng ngày sẽ thay dữ liệu cũ, không nhân đôi. Báo cáo CSV có ngày bất thường (lệch ±30%) và dự báo tuyến tính (chỉ tham khảo).
- **Ngân sách**: hạng mục dự kiến/thực chi theo 7 chương trình, chênh lệch, nhịp chi trong tháng.
- **Link UTM**: tạo link chuẩn hóa (chữ thường, không dấu).
- **Thử nghiệm**: giả thuyết → thay đổi → chỉ số chính → chỉ số bảo vệ → điều kiện dừng → kết quả → bài học.
- **Máy tính**: ngân sách ngược từ mục tiêu, KPI phễu quảng cáo, LTV/CAC & hoàn vốn, kiểm định A/B, cỡ mẫu.

### Local SEO & AI search
NAP chuẩn, checklist Google Business Profile, mã JSON-LD (LocalBusiness, FAQPage chỉ từ FAQ đã xác nhận) để dán vào website.

### Kiểm duyệt nội dung
Dán bất kỳ bài/quảng cáo/tin nhắn nào để kiểm theo G01–G11 trước khi đăng.

### Cài đặt
Gemini key và model, webhook xuất bản, địa chỉ nhận lead, đổi mật khẩu, **tải bản sao lưu**, làm mới workspace (gõ `XOA`), xóa tài khoản. Quản trị viên xem danh sách tài khoản và đồng bộ Google Sheet.

## 4. Nhịp làm việc gợi ý mỗi tuần

| Ngày | Việc |
|---|---|
| Thứ 2 | Nhập số liệu tuần trước → Growth Console → tác vụ **Vòng lặp tuần** → tạo 1 thử nghiệm |
| Thứ 2–3 | Viết bài theo lịch (Gói nội dung / Copy Studio) → duyệt trong Kho nội dung |
| Hằng ngày | Ghi khách mới vào CRM, chuyển tầng, trả lời đánh giá |
| Cuối tháng | Cập nhật thực chi ngân sách, rà Hồ sơ bối cảnh, lập ngân sách tháng sau |

## 5. Các tự động hóa Antigravity

18 playbook A01–A17 trong `13_ops/` vẫn dùng được như trước. Ứng dụng web không phụ thuộc chúng.
