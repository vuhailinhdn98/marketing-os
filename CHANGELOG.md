# Nhật ký thay đổi

## 4.0.1 — 22/10/2026

- “Kiểm tra kết nối” thử tạo một nội dung thật rất nhỏ và hiện nguyên văn lý do Gemini từ chối (billing, vùng, quota, model) thay vì chỉ kiểm danh sách model.
- Thông báo lỗi Gemini kèm câu gốc của Gemini; ghi log lỗi phía máy chủ (không ghi key).
- Giới hạn token theo từng model (đọc từ models.list), nới trần token cho model có “suy nghĩ”, báo rõ khi kết quả bị cắt.
- Tự sửa lệch định dạng nhỏ trong JSON của AI (hoa/thường của lựa chọn, số viết dạng chữ, mảng thiếu) trước khi kiểm schema.
- Tăng thời gian chờ Gemini lên 240 giây cho tác vụ dài.

## 4.0.0 — 22/10/2026

Viết lại phần ứng dụng web theo phương án nâng cấp (Đợt 0–4), dựa trên bộ skill marketing tổng hợp.

### Bảo mật và dữ liệu (Đợt 0)
- Đăng nhập bằng mật khẩu (scrypt) hoặc Google ID token đã xác minh; phiên lưu dạng băm SHA-256, hết hạn, đổi mật khẩu thì đăng xuất mọi thiết bị. Bản cũ cho đăng nhập chỉ bằng email.
- Giới hạn đăng nhập sai theo email + IP và theo email trên mọi IP.
- Gỡ file `app/static/marketing_os.zip` (bản sao CSDL bị công khai qua đường dẫn tĩnh) và các script nháp.
- CSDL chuyển sang `DATA_DIR` (mặc định `data/runtime/`, không đưa lên Git); lần đầu tự sao chép CSDL cũ `data/marketing_os_app.db`. Migration đánh số, chạy lặp lại an toàn.
- Chống SSRF khi tải website đối thủ; webhook chỉ nhận https công khai.
- CSP, X-Frame-Options, nosniff; không còn script nội tuyến.
- Sao lưu JSON (không chứa API key), làm mới workspace, xóa tài khoản.
- Cảnh báo khi chạy trên ổ đĩa tạm (Render free).

### Không còn nội dung tự chế
- Bỏ toàn bộ “động cơ nội bộ” sinh nội dung mẫu và số liệu giả khi AI lỗi. AI lỗi → trạng thái “Chưa tạo được” kèm lý do và cách xử lý.
- Gemini: tự dò model khả dụng, đổi model khi hết hạn mức/ngừng hỗ trợ, JSON theo schema, sửa JSON hỏng, tìm kiếm Google có nguồn cho tác vụ nghiên cứu.
- Kết quả nghiên cứu của bản cũ được gắn nhãn “Chưa kiểm chứng”.

### Skill Engine (Đợt 1)
- Hồ sơ bối cảnh 12 mục + kinh tế đơn vị, có phiên bản và nhật ký thay đổi, phỏng vấn nhanh.
- 26 tác vụ có JSON Schema và hậu xử lý bằng code (tính lại tỉ lệ, ngân sách, KPI, kiểm câu nguyên văn VoC…).
- Cổng tuân thủ G01–G11; nội dung tài trợ/KOL bắt buộc ghi “Quảng cáo”.

### Nội dung & lịch (Đợt 2)
- Kho nội dung 7 trạng thái có cổng duyệt, phương án AI, checklist quảng bá, xuất bản qua webhook (chỉ “Đã đăng” khi webhook nhận 2xx).
- Lịch nội dung theo ngày thật, ngày lễ dương lịch + âm lịch (thuật toán Hồ Ngọc Đức, múi giờ +7) và mùa sale.
- Tạo ảnh (Gemini) và video (Veo).

### Khách hàng & đo lường (Đợt 3)
- CRM 6 tầng + Mất, ghi nhận đồng ý tiếp thị có bằng chứng (Luật 91/2025/QH15, NĐ 356/2025/NĐ-CP), nhận lead từ form bên ngoài, chẩn đoán nút thắt phễu.
- Growth Console: MER, ROAS so với ROAS hòa vốn, lãi gộp sau marketing, CAC đúng nghĩa, nhập CSV từ nền tảng, ngày bất thường, dự báo, ngân sách & nhịp chi, UTM, thử nghiệm, máy tính A/B và LTV.

### Mở rộng (Đợt 4)
- Local SEO & AI search (NAP, checklist, JSON-LD), PR/KOL/sự kiện, vòng lặp tuần.

### Giao diện
- Viết lại giao diện: điều hướng theo nhóm, chạy tốt trên điện thoại, hiển thị nguồn/model/cổng tuân thủ cho mọi kết quả, giờ hiển thị theo giờ Việt Nam.

### Lưu ý khi nâng cấp
- Phiên đăng nhập cũ hết hiệu lực. Người dùng cũ chọn **Tạo tài khoản** với đúng email để đặt mật khẩu và giữ dữ liệu.
- Cài lại thư viện: `pip install -r requirements.txt` (thêm `jsonschema`, `google-auth`, `ddgs`).
- Cập nhật tham chiếu pháp lý: Nghị định 13/2023/NĐ-CP đã được thay bằng Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15 và Nghị định 356/2025/NĐ-CP.
