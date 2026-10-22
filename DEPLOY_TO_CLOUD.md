# 🌐 ĐƯA MARKETING OS LÊN MẠNG

Từ bản 4.0, mọi người phải **đăng nhập** (mật khẩu hoặc Google) và mỗi tài khoản là một workspace riêng, nên có thể chia sẻ link an toàn hơn bản cũ. Vẫn nên đọc phần “Trước khi mở ra Internet”.

---

## Trước khi mở ra Internet

1. **Đặt `ADMIN_EMAILS`** = email của bạn. Nếu bỏ trống, ai đăng ký đầu tiên sẽ thành quản trị.
2. **Giữ dữ liệu bền**: đặt `DATA_DIR` vào ổ đĩa không bị xóa khi khởi động lại (xem từng cách bên dưới). Ứng dụng hiện cảnh báo màu vàng khi phát hiện đang chạy trên ổ đĩa tạm.
3. Sau khi tạo đủ tài khoản cho nhóm, đặt `ALLOW_REGISTRATION=0`.
4. Thường xuyên vào **Cài đặt → Tải bản sao lưu (JSON)**.
5. Tài khoản từ bản cũ (chỉ nhập email, chưa có mật khẩu): người dùng chọn **Tạo tài khoản** với đúng email cũ để đặt mật khẩu và giữ dữ liệu cũ. Hãy làm việc này **ngay sau khi nâng cấp**, trước khi chia sẻ link, để người khác không nhận thay email của bạn.

Danh sách biến môi trường đầy đủ: [`.env.example`](.env.example).

---

## Cách 1: Điện thoại cùng mạng Wi-Fi

1. Chạy `python run_app.py` trên máy tính.
2. Trên điện thoại mở `http://<IP-máy-tính>:8000` (xem IP bằng lệnh `ipconfig` trên Windows, dòng IPv4).

## Cách 2: Link tạm thời qua Cloudflare Tunnel

1. Tải `cloudflared.exe` (Cloudflare) đặt cạnh `share_online_tunnel.bat`.
2. Chạy `start_marketing_os.bat`, rồi nhấp đúp `share_online_tunnel.bat`.
3. Gửi link `https://xxxx.trycloudflare.com` hiện ra. Giữ máy tính và cửa sổ mở để link còn hoạt động.

Đăng nhập bằng Google qua link tạm thời cần thêm đúng địa chỉ đó vào “Authorized JavaScript origins”; dùng mật khẩu thì không cần.

## Cách 3: Chạy 24/7 trên Render.com

Dự án có sẵn `render.yaml`, `Procfile`, `Dockerfile`.

1. Đưa mã lên GitHub → Render → **New + → Blueprint** → chọn repo. Render đọc `render.yaml` và hỏi giá trị `ADMIN_EMAILS`, `GOOGLE_CLIENT_ID` (có thể để trống).
2. **Gói Free**: ổ đĩa là tạm thời — dữ liệu (tài khoản, hồ sơ, khách hàng…) **mất mỗi lần dịch vụ khởi động lại hoặc triển khai lại**, và dịch vụ ngủ khi không có truy cập. Chỉ dùng để thử.
   Mẹo khi còn dùng gói Free: đặt `GEMINI_API_KEY` (và `ADMIN_EMAILS`) trong mục Environment của Render để không phải dán lại key sau mỗi lần dữ liệu bị xóa — key máy chủ chỉ tài khoản quản trị dùng được, trừ khi đặt thêm `SHARE_SERVER_GEMINI_KEY=1`.
3. **Dùng thật**: nâng dịch vụ lên gói trả phí có **Persistent Disk**, gắn disk vào `/var/data` (mẫu có sẵn, đang để dạng chú thích trong `render.yaml`) và đặt `DATA_DIR=/var/data`.
4. Kiểm tra: mở `https://<tên-dịch-vụ>.onrender.com/healthz` phải thấy `{"ok": true, ...}`.

## Cách 4: Docker (VPS, NAS, máy chủ riêng)

```bash
docker build -t marketing-os .
docker run -d --name marketing-os -p 8000:8000 \
  -v marketing-os-data:/data \
  -e ADMIN_EMAILS=ban@congty.vn \
  marketing-os
```
Ảnh Docker đặt sẵn `DATA_DIR=/data`; volume `marketing-os-data` giữ dữ liệu qua các lần cập nhật. Đặt sau reverse proxy có HTTPS (Caddy, Nginx) khi mở ra Internet.

---

## Đăng nhập Google (tùy chọn)

1. Google Cloud Console → APIs & Services → Credentials → **Create OAuth client ID** → loại *Web application*.
2. *Authorized JavaScript origins*: thêm địa chỉ website (vd `https://marketing-os.onrender.com`, `http://localhost:8000`).
3. Đặt `GOOGLE_CLIENT_ID` = Client ID vừa tạo. Nút “Tiếp tục với Google” sẽ tự hiện trên trang đăng nhập.

## Xuất bản tự động & nhận lead

- **Webhook xuất bản** (Cài đặt): dán URL https của Zapier/Make/n8n; bài đã duyệt bấm “Xuất bản qua webhook” sẽ gửi JSON tới đó.
- **Nhận lead từ website** (CRM → Nhận lead từ form): dán mã form mẫu vào landing page; mỗi workspace có địa chỉ bí mật riêng, đổi được bất cứ lúc nào.
