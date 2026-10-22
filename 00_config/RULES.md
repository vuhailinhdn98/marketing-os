# QUY TẮC VẬN HÀNH MARKETING OS (00_config/RULES.md)

Chào mừng bạn đến với hệ thống Marketing OS. Đây là bộ quy tắc chuẩn mực áp dụng cho toàn bộ các Agent, Automations và Nhân sự tham gia vận hành hệ thống.

---

## 1. Nguyên tắc cốt lõi (Core Principles)
1. **Dữ liệu thật & Nguồn xác thực**:
   - Số liệu nội bộ chỉ được trích xuất từ cơ sở dữ liệu `data/marketing.db` hoặc các file CSV đã qua kiểm duyệt trong `11_analytics/processed/`.
   - Mọi số liệu nghiên cứu bên ngoài phải có đầy đủ: Tên nguồn, Đường dẫn URL và Ngày truy cập.
   - Tuyệt đối KHÔNG bịa đặt số liệu hay phỏng đoán vô căn cứ. Nếu thiếu thông tin, phải ghi rõ `[THIẾU DỮ LIỆU]` kèm hướng dẫn cách bổ sung.
2. **Ngôn ngữ chuẩn mực**:
   - Sử dụng Tiếng Việt thương mại chuyên nghiệp, văn phong rõ ràng, gãy gọn, đúng ngữ pháp và chính tả.
   - Thuật ngữ chuyên ngành Marketing quốc tế (CTR, CPA, ROAS, CAC, LTV, Top-of-Funnel...) được giữ nguyên hoặc kèm chú thích theo `00_config/glossary.md`.
3. **Quy chuẩn lưu trữ và đặt tên**:
   - Tên file tài liệu theo định dạng: `YYYY-MM-DD_<ten-khong-dau-ngan-gon>.md`.
   - File báo cáo tuần: `YYYY-Www_bao-cao-tuan.md`.
   - File báo cáo tháng: `YYYY-MM_bao-cao-thang.md`.
   - File báo cáo quý: `YYYY-Qx_bao-cao-quy.md`.
4. **Quy trình phê duyệt nội dung (Content Lifecycle)**:
   - `idea` (Ý tưởng) ➔ `draft` (Bản nháp) ➔ `review` (Chờ duyệt) ➔ `approved` (Đã duyệt) ➔ `scheduled` (Lên lịch) ➔ `published` (Đã đăng) ➔ `measured` (Đã đo lường).
   - Mọi nội dung xuất bản phải có ít nhất 1 bước review tuân thủ thương hiệu (`A16 - Kiểm duyệt thương hiệu`).
5. **Ghi nhật ký hệ thống**:
   - Mọi lượt chạy automation bắt buộc phải ghi 1 dòng log vào `13_ops/logs/automation_log.md`:
     `[YYYY-MM-DD HH:MM:SS] <MÃ_AUTOMATION> | <KẾT QUẢ: THÀNH CÔNG/CẢNH BÁO/LỖI> | <ĐƯỜNG DẪN ĐẦU RA> | <GHI CHÚ>`

---

## 2. Tiêu chuẩn thương hiệu & Tuân thủ pháp lý
- Tuân thủ Luật Quảng cáo Việt Nam và các nghị định hướng dẫn liên quan.
- Tuân thủ Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15 (hiệu lực 01/01/2026) và Nghị định 356/2025/NĐ-CP (thay Nghị định 13/2023/NĐ-CP) trong toàn bộ các chiến dịch CRM và Lead Generation: chỉ gửi tiếp thị cho người đã đồng ý rõ ràng, lưu bằng chứng đồng ý, cho phép rút lại đồng ý và xóa dữ liệu.
- Không đưa ra các cam kết sai sự thật hoặc cam kết tuyệt đối vi phạm chính sách của nền tảng (như 100% khỏi bệnh, cam kết lợi nhuận tài chính phi thực tế...).
