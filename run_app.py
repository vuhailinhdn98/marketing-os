# -*- coding: utf-8 -*-
"""
Hệ thống Tự Động Hóa Marketing - run_app.py
Khởi động Marketing OS trên máy cá nhân (mặc định http://localhost:8000).
"""
import sys
import os
import webbrowser
import threading
import time
from pathlib import Path

# Thêm thư mục hiện tại vào sys.path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://localhost:8000")

def main():
    port = int(os.environ.get("PORT", 8000))
    print("=" * 65)
    print("  🚀 KHỞI ĐỘNG HỆ THỐNG TỰ ĐỘNG HÓA MARKETING OS")
    print(f"  🌐 Mở trình duyệt: http://localhost:{port}")
    print("  ⚡ AI: Google Gemini (thêm API key trong Cài đặt). Không có key thì tác vụ AI báo chưa tạo được, không tự chế nội dung.")
    print("=" * 65)

    # Chỉ mở trình duyệt tự động khi chạy máy cá nhân (không phải trên Cloud)
    if "PORT" not in os.environ:
        threading.Thread(target=open_browser, daemon=True).start()

    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False, log_level="info")

if __name__ == "__main__":
    main()
