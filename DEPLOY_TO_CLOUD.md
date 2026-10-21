# 🌐 HƯỚNG DẪN ĐƯA HỆ THỐNG MARKETING OS LÊN MẠNG INTERNET

Hệ thống được thiết kế bằng FastAPI & SQLite chuẩn hiện đại, giúp bạn có thể đưa lên mạng theo 3 cách tùy nhu cầu:

---

## 📱 CÁCH 1: XEM NGAY TRÊN ĐIỆN THOẠI (CÙNG MẠNG WIFI - 0 GIÂY CÀI ĐẶT)
Nếu bạn đang ở nhà hoặc công ty và điện thoại kết nối chung mạng Wifi với máy tính:
1. Mở trình duyệt trên điện thoại (Safari hoặc Chrome).
2. Gõ địa chỉ IP nội bộ của máy tính:
   ```
   http://192.168.1.16:8000
   ```
3. Bạn có thể sử dụng đầy đủ mọi tính năng, bấm tạo bài, xem chiến lược mượt mà ngay trên điện thoại!

---

## 🌍 CÁCH 2: TẠO LINK TRUY CẬP TỪ XA BẰNG 4G / CHIA SẺ CHO BẠN BÈ (30 GIÂY)
Nếu bạn muốn ra ngoài quán cafe dùng 4G, hoặc muốn gửi link cho đối tác/nhân viên cùng xem:
1. Nhấp đúp chuột vào file: **`share_online_tunnel.bat`**.
2. Một cửa sổ sẽ hiện ra cấp cho bạn 1 đường link công khai dạng:
   ```
   your url is: https://funny-cat-42.loca.lt
   ```
3. Gửi đường link này cho bất kỳ ai hoặc mở bằng 4G trên điện thoại. Họ có thể truy cập thẳng vào hệ thống Marketing OS của bạn!
*(Lưu ý: Giữ máy tính và cửa sổ đó mở để duy trì đường link)*.

---

## ☁️ CÁCH 3: ĐƯA LÊN CLOUD CHẠY 24/7 MIỄN PHÍ (KHÔNG CẦN BẬT MÁY TÍNH)
Nếu bạn muốn hệ thống luôn luôn chạy trên mạng 24/24 kể cả khi tắt máy tính:

### Nền tảng khuyến nghị: Render.com (Miễn phí 100%)
Toàn bộ file cấu hình triển khai đám mây đã được chuẩn bị sẵn trong thư mục dự án:
- `requirements.txt`: Danh sách thư viện.
- `render.yaml`: Cấu hình dịch vụ Render.
- `Procfile`: Lệnh khởi động.
- `Dockerfile`: Container đóng gói sẵn.

**Các bước đưa lên Render.com:**
1. Tạo 1 tài khoản miễn phí tại `https://render.com`.
2. Tạo 1 kho lưu trữ (Repository) trên GitHub và tải toàn bộ thư mục `marketing-os` lên GitHub của bạn.
3. Trên trang chủ Render, bấm **New +** ➔ Chọn **Web Service**.
4. Kết nối với Repository GitHub của bạn.
5. Render sẽ tự động nhận diện file `render.yaml` và build trong 2 phút.
6. Sau khi xong, Render sẽ cấp cho bạn một tên miền cố định vĩnh viễn (ví dụ: `https://marketing-os-app.onrender.com`).
7. Bạn có thể truy cập ở bất kỳ đâu, chia sẻ cho cả công ty cùng dùng 24/7!
