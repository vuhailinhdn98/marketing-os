@echo off
chcp 65001 > nul
title Chia Se Marketing OS Ra Toan Cau (Cloudflare HTTPS)
echo ==============================================================
echo    🚀 ĐANG TẠO ĐƯỜNG LINK WEBSITE CÔNG KHAI (HTTPS) CHO MARKETING OS
echo ==============================================================
echo.
echo Khi đường link xuất hiện (dạng: https://xxxx.trycloudflare.com),
echo bạn có thể gửi link cho bất kỳ ai hoặc mở bằng điện thoại 4G/Wifi.
echo.
echo Lưu ý: Giữ cửa sổ này mở để duy trì đường link website.
echo ==============================================================
echo.
"%~dp0cloudflared.exe" tunnel --url http://127.0.0.1:8000
pause
