# -*- coding: utf-8 -*-
"""
Script gọi trực tiếp Google AI Studio (Gemini API) cho Marketing OS.
Yêu cầu: pip install google-generativeai
Thiết lập API key: set GEMINI_API_KEY=your_key_here
"""
import os
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def run_task(task_code="A01"):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[THÔNG BÁO] Chưa tìm thấy biến môi trường GEMINI_API_KEY.")
        print("Để chạy qua AI Studio API, vui lòng thiết lập: set GEMINI_API_KEY=your_key")
        print("Hoặc copy trực tiếp prompt trong ai_studio/prompts_collection.json dán vào web https://aistudio.google.com/")
        return

    try:
        import google.generativeai as genai
    except ImportError:
        print("[LỖI] Chưa cài đặt thư viện google-generativeai. Chạy: pip install google-generativeai")
        return

    genai.configure(api_key=api_key)
    
    with open(ROOT / "ai_studio" / "prompts_collection.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    matched = None
    for p in data["prompts"]:
        if p["id"].endswith(task_code.lower()) or task_code.upper() in p["display_name"]:
            matched = p
            break
            
    if not matched:
        print(f"[LỖI] Không tìm thấy mã task: {task_code}")
        return

    print(f"=== ĐANG CHẠY TASK {matched['display_name']} QUA GEMINI API ===")
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(matched["prompt"])
    print(response.text)

if __name__ == "__main__":
    task = sys.argv[1] if len(sys.argv) > 1 else "A01"
    run_task(task)
