# SOP 02: QUY TRÌNH XUẤT CSV & NẠP DỮ LIỆU ĐỊNH KỲ (13_ops/sops/SOP_02_data_import_and_qa.md)

1. **Mục đích:** Chuẩn hóa quy trình đưa số liệu quảng cáo, bán hàng, traffic từ các nền tảng bên ngoài vào hệ thống Marketing OS mà không cần cấp quyền API.
2. **Lịch biểu thực hiện:**
   - Thứ 2 & Thứ 6 hàng tuần (hoặc hàng ngày nếu chạy chiến dịch lớn): Xuất file báo cáo CSV từ Meta Business Suite, Google Ads, TikTok Studio, GA4, CRM.
   - Đặt tên file bắt đầu bằng tiền tố quy định: `ads_`, `web_`, `social_`, `email_`, `seo_`, `sales_`, `leads_`, `spend_`.
   - Thả file vào thư mục: `11_analytics/inbox/`.
3. **Quy trình xử lý tự động:**
   - Hàng đêm lúc 22:00 (hoặc trước mỗi buổi báo cáo), Automation A17 chạy lệnh `python scripts/import_data.py`.
   - Hệ thống tự động kiểm tra đối chiếu schema, làm sạch định dạng ngày và số, nạp vào SQLite và di chuyển file sang `11_analytics/processed/`.
   - Nếu file thiếu cột hoặc sai định dạng, hệ thống đưa vào `11_analytics/inbox/_errors/` kèm hướng dẫn sửa.
