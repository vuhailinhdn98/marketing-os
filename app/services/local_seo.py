# -*- coding: utf-8 -*-
"""Local SEO (skill §11.3) và dữ liệu có cấu trúc cho AI search (§11.4) — chỉ từ thông tin trong hồ sơ, không tự chế."""
from __future__ import annotations

import json
from typing import Any, Dict, List

from app.context import get_path, is_filled


def nap(ctx: Dict[str, Any]) -> Dict[str, str]:
    return {"name": get_path(ctx, "brand.name") or "", "address": get_path(ctx, "brand.address") or "",
            "phone": get_path(ctx, "brand.hotline") or "", "website": get_path(ctx, "brand.website") or "",
            "hours": get_path(ctx, "brand.opening_hours") or ""}


def checklist(ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
    n = nap(ctx)
    faq = [f for f in (ctx.get("faq") or []) if f.get("q") and f.get("a")]
    items = [
        {"item": "Tên, địa chỉ, SĐT (NAP) đã có trong hồ sơ", "done": bool(n["name"] and n["address"] and n["phone"]),
         "how": "Điền Tên thương hiệu, Địa chỉ, Hotline trong Hồ sơ bối cảnh."},
        {"item": "Giờ mở cửa đã có", "done": bool(n["hours"]), "how": "Điền Giờ mở cửa trong Hồ sơ bối cảnh."},
        {"item": "Website hoặc fanpage chính đã có", "done": bool(n["website"] or get_path(ctx, "brand.social_links")),
         "how": "Thêm website hoặc link fanpage."},
        {"item": "Có ít nhất 3 câu hỏi thường gặp đã xác nhận", "done": len(faq) >= 3, "how": "Thêm FAQ trong Hồ sơ bối cảnh."},
        {"item": "Google Business Profile: chọn đúng danh mục chính và phụ", "done": None, "how": "Tự kiểm trong business.google.com."},
        {"item": "Google Business Profile: ít nhất 10 ảnh thật (mặt tiền, bên trong, sản phẩm)", "done": None, "how": "Tự kiểm."},
        {"item": "Đăng bài/ảnh mới trên Google Business Profile mỗi tuần", "done": None, "how": "Đưa vào lịch nội dung."},
        {"item": "Trả lời mọi đánh giá trong 48 giờ (dùng tác vụ Trả lời đánh giá)", "done": None, "how": "Skill Studio → SEO & Local."},
        {"item": "NAP giống hệt nhau trên Facebook, Zalo, Foody, sàn TMĐT", "done": None,
         "how": "So từng ký tự với NAP chuẩn bên dưới."},
        {"item": "Không đổi quà lấy đánh giá, không viết đánh giá giả", "done": None, "how": "Chính sách Google và Luật Quảng cáo."},
    ]
    return items


def json_ld(ctx: Dict[str, Any]) -> Dict[str, Any]:
    n = nap(ctx)
    warnings: List[str] = []
    business: Dict[str, Any] = {"@context": "https://schema.org", "@type": "LocalBusiness"}
    if n["name"]:
        business["name"] = n["name"]
    else:
        warnings.append("Thiếu tên thương hiệu.")
    one_liner = get_path(ctx, "product.one_liner")
    if one_liner:
        business["description"] = one_liner
    if n["address"]:
        business["address"] = {"@type": "PostalAddress", "streetAddress": n["address"], "addressCountry": "VN"}
        loc = get_path(ctx, "market.location")
        if loc:
            business["address"]["addressLocality"] = loc
    else:
        warnings.append("Thiếu địa chỉ: Google cần địa chỉ để hiểu doanh nghiệp địa phương.")
    if n["phone"]:
        business["telephone"] = n["phone"]
    if n["website"]:
        business["url"] = n["website"]
    socials = [s for s in (get_path(ctx, "brand.social_links") or []) if str(s).startswith("http")]
    if socials:
        business["sameAs"] = socials
    prices = [float(p.get("price_vnd") or 0) for p in (get_path(ctx, "product.price_points") or []) if p.get("price_vnd")]
    if prices:
        lo, hi = int(min(prices)), int(max(prices))
        business["priceRange"] = f"{lo:,}–{hi:,} VND".replace(",", ".") if lo != hi else f"{lo:,} VND".replace(",", ".")
    if n["hours"]:
        warnings.append("Giờ mở cửa chưa đưa vào schema vì cần định dạng chuẩn (vd Mo-Su 06:30-22:00); thêm thủ công nếu muốn.")
    out = {"local_business": business, "warnings": warnings}
    faq = [f for f in (ctx.get("faq") or []) if f.get("q") and f.get("a")]
    if faq:
        out["faq_page"] = {"@context": "https://schema.org", "@type": "FAQPage",
                           "mainEntity": [{"@type": "Question", "name": f["q"],
                                           "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faq]}
    else:
        warnings.append("Chưa có FAQ đã xác nhận nên không tạo FAQPage (không tự chế câu trả lời).")
    snippet = [f'<script type="application/ld+json">\n{json.dumps(business, ensure_ascii=False, indent=2)}\n</script>']
    if "faq_page" in out:
        snippet.append(f'<script type="application/ld+json">\n{json.dumps(out["faq_page"], ensure_ascii=False, indent=2)}\n</script>')
    out["html"] = "\n".join(snippet)
    return out


def toolkit(ctx: Dict[str, Any]) -> Dict[str, Any]:
    return {"nap": nap(ctx), "checklist": checklist(ctx), "schema": json_ld(ctx),
            "ready": is_filled(get_path(ctx, "brand.name")) and is_filled(get_path(ctx, "brand.address"))}
