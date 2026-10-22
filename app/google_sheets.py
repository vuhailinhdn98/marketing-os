# -*- coding: utf-8 -*-
"""
Google Sheets Integration Module for Marketing OS
- Webhook dispatcher for real-time user login logging to Google Sheets
- Export all users to Google Sheets compatible CSV/TSV format
- Ready-to-use Google Apps Script deployment code
"""
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

def dispatch_login_to_google_sheet(webhook_url: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gửi dữ liệu đăng nhập của người dùng đến Google Sheet thông qua Google Apps Script Webhook.
    """
    if not webhook_url or not webhook_url.startswith("https://script.google.com/"):
        return {"status": "skipped", "message": "Chưa cấu hình Google Sheet Webhook hợp lệ."}

    payload = {
        "action": "LOGIN",
        "email": user_data.get("email", ""),
        "name": user_data.get("name", ""),
        "login_count": user_data.get("login_count", 1),
        "ip_address": user_data.get("ip_address", ""),
        "user_agent": user_data.get("user_agent", ""),
        "timestamp": user_data.get("last_login", "")
    }

    try:
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=data_bytes,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = response.read().decode("utf-8")
            return {"status": "success", "response": res_body}
    except Exception as e:
        print(f"[GOOGLE SHEETS ERROR] Lỗi khi gửi webhook đến Google Sheet: {e}")
        return {"status": "error", "error": str(e)}

def get_google_apps_script_template() -> str:
    """
    Trả về mã Google Apps Script để dán trực tiếp vào tiện ích mở rộng của Google Sheets.
    """
    return """/**
 * GOOGLE APPS SCRIPT CHO MARKETING OS
 * Tự động ghi nhận và quản lý danh sách tài khoản Gmail đăng nhập vào Marketing OS
 *
 * HƯỚNG DẪN CÀI ĐẶT TRONG 30 GIÂY:
 * 1. Mở Google Sheet mới hoặc hiện có của bạn.
 * 2. Vào menu: Tiện ích mở rộng (Extensions) -> Apps Script.
 * 3. Xóa hết code cũ và dán toàn bộ đoạn code này vào.
 * 4. Nhấp nút 'Triển khai' (Deploy) -> 'Tùy chọn triển khai mới' (New deployment).
 * 5. Chọn loại: 'Ứng dụng web' (Web app).
 *    - Thực thi dưới dạng: 'Tôi' (Me).
 *    - Ai có quyền truy cập: 'Bất kỳ ai' (Anyone).
 * 6. Sao chép URL ứng dụng web (Web App URL) và dán vào mục Cấu hình Google Sheet trong Marketing OS!
 */

function doPost(e) {
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    var data = JSON.parse(e.postData.contents);
    
    // Tạo tiêu đề nếu trang tính còn trống
    if (sheet.getLastRow() === 0) {
      sheet.appendRow([
        "Thời Gian Gần Nhất",
        "Tài Khoản Gmail",
        "Họ Tên Người Dùng",
        "Số Lượt Truy Cập",
        "Địa Chỉ IP",
        "Trình Duyệt / Thiết Bị",
        "Trạng Thái"
      ]);
      // Định dạng dòng tiêu đề
      var headerRange = sheet.getRange(1, 1, 1, 7);
      headerRange.setBackground("#0ea5e9").setFontColor("#ffffff").setFontWeight("bold");
    }

    var email = data.email || "";
    var name = data.name || "";
    var count = data.login_count || 1;
    var ip = data.ip_address || "";
    var ua = data.user_agent || "";
    var nowStr = Utilities.formatDate(new Date(), "Asia/Ho_Chi_Minh", "yyyy-MM-dd HH:mm:ss");

    // Tìm kiếm xem email này đã từng đăng nhập chưa
    var values = sheet.getDataRange().getValues();
    var foundRow = -1;
    for (var i = 1; i < values.length; i++) {
      if (values[i][1] && values[i][1].toString().toLowerCase() === email.toLowerCase()) {
        foundRow = i + 1;
        break;
      }
    }

    if (foundRow > 0) {
      // Đã có -> Cập nhật số lượt và thời gian mới nhất
      var currentCount = parseInt(sheet.getRange(foundRow, 4).getValue()) || 1;
      sheet.getRange(foundRow, 1).setValue(nowStr);
      sheet.getRange(foundRow, 3).setValue(name || sheet.getRange(foundRow, 3).getValue());
      sheet.getRange(foundRow, 4).setValue(currentCount + 1);
      if (ip) sheet.getRange(foundRow, 5).setValue(ip);
      if (ua) sheet.getRange(foundRow, 6).setValue(ua);
      sheet.getRange(foundRow, 7).setValue("Hoạt động");
    } else {
      // Người dùng mới -> Thêm dòng mới
      sheet.appendRow([nowStr, email, name, count, ip, ua, "Hoạt động"]);
    }

    return ContentService.createTextOutput(JSON.stringify({
      status: "success",
      message: "Đã ghi nhận tài khoản " + email + " vào Google Sheet thành công!"
    })).setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({
      status: "error",
      message: err.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet(e) {
  return ContentService.createTextOutput(JSON.stringify({
    status: "online",
    service: "Marketing OS Google Sheets Integration Endpoint"
  })).setMimeType(ContentService.MimeType.JSON);
}
"""
