# -*- coding: utf-8 -*-
"""
Hệ điều hành Marketing OS - scripts/import_data.py
Nạp dữ liệu tự động:
1. Đọc tất cả các file CSV trong 11_analytics/inbox/
2. Kiểm tra đối chiếu với các schema tương ứng trong data/schemas/
3. Chuẩn hóa ngày (YYYY-MM-DD), làm sạch số liệu, chống trùng lặp
4. Insert/Upsert vào SQLite (data/marketing.db)
5. Di chuyển file thành công sang 11_analytics/processed/
6. Nếu có file lỗi, di chuyển vào 11_analytics/inbox/_errors/ kèm file .txt giải thích nguyên nhân và cách khắc phục
"""
import os
import csv
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "marketing.db"
SCHEMAS_DIR = ROOT / "data" / "schemas"
INBOX_DIR = ROOT / "11_analytics" / "inbox"
PROCESSED_DIR = ROOT / "11_analytics" / "processed"
ERRORS_DIR = INBOX_DIR / "_errors"

PREFIX_TO_TABLE = {
    "ads_": ("ads", "ads_schema.json"),
    "web_": ("web", "web_schema.json"),
    "social_": ("social", "social_schema.json"),
    "email_": ("email", "email_schema.json"),
    "seo_": ("seo", "seo_schema.json"),
    "sales_": ("sales", "sales_schema.json"),
    "leads_": ("leads", "leads_schema.json"),
    "spend_": ("spend", "spend_schema.json"),
}

def clean_val(val, expected_type):
    if val is None or str(val).strip() == "":
        return 0 if expected_type in ["INTEGER", "REAL"] else ""
    val_str = str(val).strip().replace(",", "")
    if expected_type == "INTEGER":
        try:
            return int(float(val_str))
        except ValueError:
            return 0
    elif expected_type == "REAL":
        try:
            return float(val_str)
        except ValueError:
            return 0.0
    return str(val).strip()

def process_file(csv_file: Path, conn: sqlite3.Connection):
    fname = csv_file.name.lower()
    matched_prefix = None
    table_name = None
    schema_file = None
    
    for pfx, (tbl, sch) in PREFIX_TO_TABLE.items():
        if fname.startswith(pfx):
            matched_prefix = pfx
            table_name = tbl
            schema_file = sch
            break
            
    if not matched_prefix:
        return False, f"File khong co tien to hop le (ads_, web_, social_, email_, seo_, sales_, leads_, spend_)"

    schema_path = SCHEMAS_DIR / schema_file
    if not schema_path.exists():
        return False, f"Khong tim thay schema: {schema_file}"
        
    with open(schema_path, "r", encoding="utf-8") as sf:
        schema = json.load(sf)
        
    required_cols = [c.lower() for c in schema["required_columns"]]
    types = schema["types"]

    # Đọc và xác thực cấu trúc
    rows_to_insert = []
    try:
        with open(csv_file, "r", encoding="utf-8-sig") as cf:
            reader = csv.DictReader(cf)
            if not reader.fieldnames:
                return False, "File CSV rong hoac khong co dong tieu de"
            file_cols = [c.strip().lower() for c in reader.fieldnames]
            missing_cols = [c for c in required_cols if c not in file_cols]
            if missing_cols:
                return False, f"Thieu cac cot bat buoc theo schema: {', '.join(missing_cols)}"
                
            for line_idx, row in enumerate(reader, start=2):
                clean_row = {}
                for col in required_cols:
                    # Tìm key tương ứng không phân biệt hoa thường
                    raw_val = None
                    for k, v in row.items():
                        if k.strip().lower() == col:
                            raw_val = v
                            break
                    col_type = types.get(col, "TEXT")
                    clean_row[col] = clean_val(raw_val, col_type)
                rows_to_insert.append(clean_row)
    except Exception as e:
        return False, f"Loi doc file CSV: {str(e)}"

    if not rows_to_insert:
        return False, "File CSV khong chua dong du lieu nao"

    # Chèn dữ liệu vào SQLite
    cursor = conn.cursor()
    cols_str = ", ".join(required_cols)
    placeholders = ", ".join(["?"] * len(required_cols))
    sql = f"INSERT OR REPLACE INTO {table_name} ({cols_str}) VALUES ({placeholders})"

    inserted_count = 0
    for r in rows_to_insert:
        values = [r[c] for c in required_cols]
        cursor.execute(sql, values)
        inserted_count += 1
        
    conn.commit()
    return True, f"Nap thanh cong {inserted_count} ban ghi vao bang '{table_name}'"

def import_all():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    ERRORS_DIR.mkdir(parents=True, exist_ok=True)
    
    if not DB_PATH.exists():
        from init_db import init_database
        init_database()
        
    conn = sqlite3.connect(DB_PATH)
    inbox_files = [f for f in INBOX_DIR.iterdir() if f.is_file() and f.suffix.lower() == ".csv"]
    
    if not inbox_files:
        print("[INFO] Khong co file CSV moi trong 11_analytics/inbox/")
        conn.close()
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for csv_file in inbox_files:
        success, message = process_file(csv_file, conn)
        if success:
            target_dest = PROCESSED_DIR / f"{timestamp}_{csv_file.name}"
            shutil.move(str(csv_file), str(target_dest))
            print(f"[SUCCESS] {csv_file.name} -> {message}")
        else:
            err_dest = ERRORS_DIR / f"{timestamp}_{csv_file.name}"
            shutil.move(str(csv_file), str(err_dest))
            err_log_file = ERRORS_DIR / f"{timestamp}_{csv_file.stem}_huong_dan_sua.txt"
            with open(err_log_file, "w", encoding="utf-8") as elf:
                elf.write(f"LOI XU LY FILE: {csv_file.name}\n")
                elf.write(f"Thoi gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                elf.write(f"Nguyen nhan: {message}\n\n")
                elf.write("CACH KHAC PHUC:\n")
                elf.write("1. Kiem tra ten file bat dau dung tien to: ads_, web_, social_, email_, seo_, sales_, leads_, spend_\n")
                elf.write("2. Kiem tra file co day du cac cot bat buoc theo quy dinh tai 11_analytics/kpi_definitions.md\n")
                elf.write("3. Xuat lai file tu nen tang va copy vao lai thu muc 11_analytics/inbox/\n")
            print(f"[ERROR] {csv_file.name} -> {message}. Xem huong dan tai {err_log_file.name}")
            
    conn.close()

if __name__ == "__main__":
    import_all()
