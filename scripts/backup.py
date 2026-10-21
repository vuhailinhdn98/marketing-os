# -*- coding: utf-8 -*-
"""
Hệ điều hành Marketing OS - scripts/backup.py
Sao lưu cơ sở dữ liệu SQLite và các file cấu hình, CSV quan trọng:
- Lưu vào thư mục backups/YYYY-MM-DD_HHMMSS/
- Tự động dọn dẹp và giữ lại tối đa 14 bản sao lưu gần nhất
"""
import sys
import shutil
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
BACKUPS_DIR = ROOT / "backups"
DB_PATH = ROOT / "data" / "marketing.db"

FILES_TO_BACKUP = [
    ROOT / "00_config" / "business_profile.md",
    ROOT / "00_config" / "brand_guidelines.md",
    ROOT / "00_config" / "goals_okr.md",
    ROOT / "03_campaigns" / "campaign_registry.csv",
    ROOT / "04_content" / "calendar" / "content_calendar.csv",
    ROOT / "05_seo" / "keyword_map.csv",
    ROOT / "07_ads" / "media_plan.csv",
    ROOT / "07_ads" / "experiments.csv",
    ROOT / "12_finance" / "budget_plan.csv",
    ROOT / "12_finance" / "spend_tracker.csv",
    ROOT / "13_ops" / "tasks.csv",
    ROOT / "13_ops" / "approvals.csv",
]

def perform_backup():
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    backup_folder = BACKUPS_DIR / timestamp
    backup_folder.mkdir(parents=True, exist_ok=True)

    copied_count = 0
    # 1. Backup SQLite DB
    if DB_PATH.exists():
        shutil.copy2(str(DB_PATH), str(backup_folder / "marketing.db"))
        copied_count += 1

    # 2. Backup critical CSVs and Markdown
    for f in FILES_TO_BACKUP:
        if f.exists():
            dest = backup_folder / f.name
            shutil.copy2(str(f), str(dest))
            copied_count += 1

    print(f"[OK] Da sao luu {copied_count} tep tin vao: {backup_folder}")

    # 3. Clean up older backups (keep last 14)
    all_backups = sorted([d for d in BACKUPS_DIR.iterdir() if d.is_dir()])
    if len(all_backups) > 14:
        for old_b in all_backups[:-14]:
            shutil.rmtree(str(old_b), ignore_errors=True)
            print(f"[CLEANUP] Da xoa ban sao luu cu: {old_b.name}")

if __name__ == "__main__":
    perform_backup()
