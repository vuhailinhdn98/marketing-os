# HƯỚNG DẪN TRIỂN KHAI MARKETING OS TRÊN GOOGLE AI STUDIO (ai_studio/AI_STUDIO_GUIDE.md)

Hệ thống Marketing OS được thiết kế theo cấu trúc Module chuẩn mực, cho phép bạn vận hành linh hoạt trên cả hai môi trường:
1. **Chạy Local tự động qua Antigravity Automations** (Đã cấu hình sẵn 18 Automations trong hệ thống).
2. **Chạy Trực tiếp trên Google AI Studio** (Giao diện web trực quan của Google hoặc gọi qua Gemini API).

---

## 1. CÁCH ĐƯA LÊN GOOGLE AI STUDIO (GIAO DIỆN WEB)

### Bước 1: Mở Google AI Studio
- Truy cập: `https://aistudio.google.com/` và đăng nhập tài khoản Google.
- Nhấp chọn **Create New Prompt** (Nên chọn **System Instructions** hoặc **Chat Prompt**).

### Bước 2: Thiết lập Cấu hình Mô hình (Model Settings)
- **Model:** Chọn `Gemini 1.5 Pro` (Dành cho tác vụ chiến lược, nghiên cứu sâu A11-A15) hoặc `Gemini 1.5 Flash` (Dành cho tác vụ sản xuất nội dung nhanh hàng ngày A01, A03, A04).
- **Temperature:** Đặt `0.3 - 0.5` cho tác vụ phân tích số liệu và báo cáo; Đặt `0.7 - 0.8` cho tác vụ sáng tạo nội dung và viết kịch bản video.
- **Top P:** `0.95`.

### Bước 3: Cài đặt System Instruction
- Mở file `ai_studio/system_instruction.txt`.
- Copy toàn bộ nội dung và dán vào ô **System Instructions** ở cột bên trái của Google AI Studio.

### Bước 4: Tải lên Hồ sơ Doanh nghiệp & Dữ liệu
- Ở khung chat, nhấp biểu tượng **Add Files (Đính kèm)**:
  - Đính kèm file `00_config/business_profile.md` (Hồ sơ doanh nghiệp).
  - Đính kèm file `00_config/brand_guidelines.md` (Nguyên tắc thương hiệu).
  - Đính kèm file báo cáo CSV gần nhất (ví dụ `data/samples/ads_sample.csv` hoặc file export thực tế của bạn).

### Bước 5: Sử dụng Prompt Collection
- Mở file `ai_studio/prompts_collection.json`.
- Khi cần chạy module nào (ví dụ A03 để viết bài, A06 để làm báo cáo tuần), chỉ cần copy prompt của module đó và dán vào khung chat của AI Studio. AI sẽ phân tích các file bạn đính kèm và trả về kết quả trọn vẹn theo đúng cấu trúc.

---

## 2. CÁCH GỌI QUA PYTHON SDK (GEMINI API)
Nếu bạn có API Key từ Google AI Studio, bạn có thể chạy script tự động bằng Python:
```bash
pip install google-generativeai
python ai_studio/run_ai_studio_api.py --task A01
```
*(Tham khảo script mẫu đã tạo sẵn tại `ai_studio/run_ai_studio_api.py`)*.
