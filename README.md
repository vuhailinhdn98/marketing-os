# 🚀 MARKETING OS 4.0 – HỆ ĐIỀU HÀNH MARKETING CHO DOANH NGHIỆP NHỎ

Web app làm marketing hằng ngày: **Hồ sơ bối cảnh → Skill Studio (26 tác vụ) → Kho nội dung có cổng duyệt → Lịch nội dung → CRM 6 tầng → Growth Console (MER, ROAS hòa vốn, CAC, LTV)**. AI dùng Google Gemini; mọi kết quả ghi rõ model, nguồn và bị kiểm tuân thủ trước khi đăng. Khi AI lỗi hoặc chưa có key, hệ thống **báo chưa tạo được**, không chèn nội dung mẫu hay số liệu tự chế.

## Chạy trên máy (Windows/macOS/Linux)

```bash
pip install -r requirements.txt
python run_app.py            # mở http://localhost:8000
```
Trên Windows có thể nhấp đúp `start_marketing_os.bat` (tự cài thư viện còn thiếu rồi chạy).

1. Mở http://localhost:8000 → **Tạo tài khoản**. Tài khoản đầu tiên là **quản trị** (hoặc đặt `ADMIN_EMAILS`).
2. **Cài đặt** → dán Gemini API key (miễn phí tại https://aistudio.google.com/apikey) → **Kiểm tra kết nối**.
3. **Hồ sơ bối cảnh** → bấm **Phỏng vấn nhanh** để điền các mục cốt lõi.
4. **Tổng quan** → **Khởi động nhanh** (trụ cột nội dung → lịch 14 ngày → ý tưởng marketing).

Chi tiết từng màn hình: [`HUONG_DAN_SU_DUNG.md`](HUONG_DAN_SU_DUNG.md). Đưa lên mạng: [`DEPLOY_TO_CLOUD.md`](DEPLOY_TO_CLOUD.md). Thay đổi so với bản cũ: [`CHANGELOG.md`](CHANGELOG.md).

## Kiến trúc

| Thành phần | Vị trí | Ghi chú |
|---|---|---|
| API (FastAPI) | `app/main.py`, `app/routers/` | Đăng nhập bằng mật khẩu (scrypt) hoặc Google; phiên lưu dạng băm, hết hạn 30 ngày |
| Skill Engine | `app/skills/` | Bộ skill marketing (`marketing_master.md`) + 26 tác vụ có JSON Schema, hậu xử lý bằng code |
| Cổng tuân thủ | `app/guardrails.py` | G01–G11: số liệu có nguồn, không khan hiếm giả, ghi “Quảng cáo” cho KOL, chỉ tiếp thị người đã đồng ý… |
| Đo lường | `app/metrics.py` | MER, ROAS hòa vốn = 1 ÷ biên lãi gộp, CAC, LTV trên lãi gộp, A/B test, cỡ mẫu, nhịp chi |
| Lịch Việt Nam | `app/vn_calendar.py` | Ngày lễ dương lịch, âm lịch (Tết, Trung thu, Giỗ Tổ…), mùa sale |
| Dữ liệu | `DATA_DIR` (mặc định `data/runtime/`) | SQLite + file ảnh/video. Không đưa lên Git |
| Giao diện | `app/static/` | HTML + JS thuần, không cần build |

Thư mục tài liệu marketing (`00_config` … `13_ops`, `templates/`, `ai_studio/`, `scripts/`, `dashboard/`) giữ nguyên như bản trước.

## Biến môi trường

Xem [`.env.example`](.env.example). Quan trọng nhất khi chạy trên cloud: `DATA_DIR` trỏ vào ổ đĩa bền, `ADMIN_EMAILS`, và (tùy chọn) `GOOGLE_CLIENT_ID`, `GEMINI_API_KEY`.

## Kiểm thử

```bash
pip install -r requirements-dev.txt
pytest -q
```
Bộ test dùng Gemini giả (không gọi mạng), DB tạm riêng cho từng test: đăng nhập/bảo mật, SSRF, đủ 26 tác vụ, cổng tuân thủ, số liệu, CRM, nhập CSV, lịch âm.

## Lưu ý pháp lý

Dữ liệu khách hàng chỉ dùng để tiếp thị khi khách đã đồng ý rõ ràng, có lưu bằng chứng và cho phép rút lại (Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15, Nghị định 356/2025/NĐ-CP). Kiểm tra tự động không thay thế tư vấn pháp lý cho ngành có điều kiện (thực phẩm chức năng, mỹ phẩm, y tế, tài chính).
