# SOP 01: QUY TRÌNH XUẤT BẢN NỘI DUNG ĐA KÊNH (13_ops/sops/SOP_01_content_publishing.md)

1. **Mục đích:** Đảm bảo mọi nội dung đăng tải trên các kênh mạng xã hội, website, blog đều trải qua kiểm duyệt chất lượng và thống nhất nhận diện thương hiệu.
2. **Quy trình 5 bước:**
   - **Bước 1 (Lên kế hoạch):** Thứ 6 hàng tuần, Automation A08 lập khung lịch nội dung tuần tới vào `04_content/calendar/content_calendar.csv` với trạng thái `planned`.
   - **Bước 2 (Sản xuất bản nháp):** Hàng ngày lúc 08:00, Automation A03 đọc lịch và tạo bản nháp tại `04_content/drafts/`, cập nhật trạng thái `review` và đẩy vào `13_ops/approvals.csv`.
   - **Bước 3 (Thẩm định thương hiệu):** Automation A16 và Brand Lead kiểm tra bản nháp theo thang điểm 10. Nếu đạt >= 7 điểm -> Chuyển trạng thái `approved`. Nếu < 7 điểm -> Sửa chữa hoặc từ chối.
   - **Bước 4 (Đóng gói xuất bản):** Tạo thư mục `04_content/publish_packs/YYYY-MM-DD/` gồm: File nội dung cuối cùng, hình ảnh/video thiết kế, và checklist đăng tải.
   - **Bước 5 (Đăng bài & Báo cáo):** Nhân sự đăng tải thủ công lên các kênh và cập nhật trạng thái thành `published`.
