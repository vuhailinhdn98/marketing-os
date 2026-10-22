@echo off
chcp 65001 > nul
title Marketing OS
cd /d "%~dp0"
echo ==============================================================
echo    DANG KHOI DONG MARKETING OS...
echo ==============================================================
python -c "import fastapi, uvicorn, requests, bs4, jsonschema, google.auth, ddgs" 1>nul 2>nul
if errorlevel 1 (
  echo Dang cai dat thu vien can thiet lan dau, vui long cho...
  python -m pip install -r requirements.txt
  if errorlevel 1 (
    echo Khong cai duoc thu vien. Kiem tra Python 3.10+ va ket noi mang roi chay lai.
    pause
    exit /b 1
  )
)
python run_app.py
pause
