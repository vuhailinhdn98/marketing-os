# -*- coding: utf-8 -*-
"""Chuyển kết quả JSON của tác vụ thành Markdown để xem, sao chép và tải về."""
from __future__ import annotations

from typing import Any, Dict, List

LABELS = {
    "executive_summary": "Tóm tắt", "big_bets": "3 cược lớn", "priorities_90d": "Ưu tiên 90 ngày", "outcome_12m": "Kết quả 12 tháng",
    "market_quality": "Cổng chất lượng thị trường", "magnitude": "Độ lớn vấn đề", "frequency": "Tần suất", "verdict": "Kết luận",
    "key_message": "Thông điệp chính", "aarrr": "AARRR", "stage": "Giai đoạn", "running": "Đang chạy", "will_run": "Sẽ chạy",
    "skip": "Bỏ qua", "channel": "Kênh", "reason": "Lý do", "roadmap": "Lộ trình 90 ngày", "phase": "Chặng", "actions": "Hành động",
    "action": "Việc", "aarrr_stage": "AARRR", "owner": "Phụ trách", "due": "Hạn", "kpi": "KPI", "mechanism": "Cơ chế",
    "allocation": "Phân bổ 70/20/10", "proven_70": "70% — đang hiệu quả", "next_20": "20% — tăng trưởng kế tiếp",
    "experiments_10": "10% — thử nghiệm", "orb_check": "Kiểm tra Owned–Rented–Borrowed", "flow": "Luồng",
    "leads_to_owned": "Dẫn về kênh sở hữu", "fix": "Cách sửa", "kpis": "KPI", "name": "Tên", "target": "Mục tiêu",
    "deadline": "Hạn", "formula": "Công thức", "measurement": "Đo lường", "north_star": "North Star", "leading": "Chỉ số dẫn dắt",
    "metric": "Chỉ số", "open_decisions": "Quyết định còn mở", "ideas": "Ý tưởng", "idea": "Ý tưởng", "leading_metric": "Chỉ số dẫn dắt",
    "stop_condition": "Điều kiện dừng", "cost_level": "Mức chi", "time_to_impact": "Thời gian ra kết quả", "first_step": "Bước đầu",
    "slc_check": "Kiểm tra SLC", "simple": "Simple", "lovable": "Lovable", "complete": "Complete", "ready": "Sẵn sàng",
    "owned": "Owned (sở hữu)", "rented": "Rented (thuê)", "borrowed": "Borrowed (mượn)", "timeline": "Lịch", "week": "Tuần",
    "risks": "Rủi ro", "plain_rewrite": "Ưu đãi viết lại bằng lời thường", "levers": "4 đòn bẩy giá trị", "score": "Điểm",
    "components": "6 thành phần", "present": "Có", "comment": "Nhận xét", "weakest_lever": "Đòn bẩy yếu nhất",
    "change": "Thay đổi", "why": "Vì sao", "new_offer_copy": "Ưu đãi mới", "how_to_test": "Cách thử", "expected_lift": "Mức tăng ước lượng",
    "range": "Khoảng", "label": "Nhãn", "formula_used": "Công thức", "emotion_used": "Tử huyệt cảm xúc", "variants": "Phương án",
    "headline": "Tiêu đề", "hook": "Hook", "hook_type": "Loại hook", "body": "Nội dung", "cta": "CTA", "rationale": "Lý do chọn",
    "recommended": "Phương án đề xuất", "visual_brief": "Gợi ý hình ảnh", "hashtags": "Hashtag", "claims_to_verify": "Cần xác nhận",
    "passes": "7 lượt biên tập", "issues": "Vấn đề", "changes": "Đã sửa", "final_text": "Bản cuối", "cta_check": "Kiểm tra CTA",
    "pillars": "Trụ cột", "share_pct": "Tỉ lệ %", "purpose": "Mục đích", "findable_or_shareable": "Loại", "funnel_stage": "Giai đoạn phễu",
    "example_topics": "Chủ đề mẫu", "search_keywords": "Từ khóa", "mix_note": "Ghi chú", "atoms": "Mẩu nội dung", "format": "Định dạng",
    "angle": "Góc", "text": "Nội dung", "campaign": "Chiến dịch", "objective": "Mục tiêu", "audience_label": "Tệp", "offer_label": "Ưu đãi",
    "adsets": "Nhóm quảng cáo", "name_audience": "Tệp", "audience": "Mô tả tệp", "role": "Vai trò", "exclusions": "Loại trừ",
    "daily_budget_vnd": "Ngân sách/ngày (VND)", "angles": "Góc tiếp cận", "primary_text": "Nội dung chính", "remarketing": "Remarketing theo tầng",
    "message": "Thông điệp", "offer": "Ưu đãi", "test_plan": "Kế hoạch thử", "kpi_formula": "KPI suy ra", "operating_rules": "Luật vận hành",
    "total_budget_vnd": "Tổng ngân sách (VND)", "days": "Số ngày", "expected_results": "Kết quả dự kiến", "basis": "Cơ sở",
    "lines": "Hạng mục", "program": "Chương trình", "item": "Hạng mục", "unit_price": "Đơn giá", "unit": "Đơn vị", "quantity": "SL",
    "projected_total": "Thành tiền", "allocation_note": "Ghi chú phân bổ", "total_projected": "Tổng dự kiến",
    "jtbd": "Việc khách cần làm", "type": "Loại", "evidence_lines": "Dòng bằng chứng", "confidence": "Độ tin cậy", "pains": "Nỗi đau",
    "triggers": "Sự kiện kích hoạt", "desired_outcomes": "Kết quả mong muốn", "alternatives": "Phương án thay thế",
    "verbatim_quotes": "Câu nguyên văn", "quote": "Câu", "line": "Dòng", "persona": "Persona", "allowed": "Đủ dữ liệu", "summary": "Tóm tắt",
    "data_points": "Số điểm dữ liệu", "steps": "Các bước", "step": "Bước", "goal": "Mục tiêu", "questions_to_ask": "Câu hỏi nên hỏi",
    "objections": "Xử lý từ chối", "objection": "Khách nói", "response": "Trả lời", "source": "Nguồn", "upsell": "Upsell", "downsell": "Downsell",
    "follow_up": "Follow-up", "adapt_for_type": "Điều chỉnh theo kiểu khách", "reply": "Câu trả lời", "tone_notes": "Lưu ý giọng",
    "internal_actions": "Việc nội bộ", "follow_up_at": "Hẹn theo dõi", "avoid_phrases_found": "Cụm cần tránh còn sót",
    "flow_name": "Tên chuỗi", "audience_rule": "Điều kiện vào chuỗi", "messages": "Tin nhắn", "day": "Ngày", "subject": "Tiêu đề",
    "preview": "Preview", "exit_conditions": "Điều kiện thoát", "referral_program": "Chương trình giới thiệu", "trigger": "Thời điểm mời",
    "reward_referrer": "Thưởng người giới thiệu", "reward_friend": "Thưởng bạn mới", "reward_timing": "Thời điểm thưởng",
    "consent_rule": "Quy tắc đồng ý", "sms_segments": "Số tin SMS", "internal_note": "Ghi chú nội bộ", "answer_40_60": "Câu trả lời trực tiếp",
    "supporting_points": "Ý bổ trợ", "facts_needed": "Cần bổ sung sự thật", "clusters": "Cụm từ khóa", "keywords": "Từ khóa",
    "content_idea": "Ý tưởng nội dung", "page_type": "Loại trang", "local_keywords": "Từ khóa địa phương", "next_step": "Bước tiếp",
    "brief": "Brief", "must_say": "Phải nói", "must_not_say": "Không được nói", "disclosure_requirement": "Yêu cầu công khai quảng cáo",
    "deliverables": "Sản phẩm bàn giao", "fit_assessment": "Độ khớp tệp", "contract_clauses": "Điều khoản hợp đồng", "checklist": "Checklist",
    "before": "Trước sự kiện", "during": "Trong sự kiện", "after": "Sau sự kiện", "task": "Việc", "follow_up_template": "Mẫu follow-up",
    "quality_meeting_definition": "Thế nào là cuộc gặp chất lượng", "metric_formula": "Công thức đo", "angle_rationale": "Vì sao chọn góc này",
    "headline_options": "Tiêu đề đề xuất", "pitch_email": "Thư pitch", "press_release_outline": "Khung thông cáo",
    "media_kit_checklist": "Media kit", "proof_needed": "Bằng chứng cần có", "bottleneck_stage": "Nút thắt", "evidence": "Bằng chứng",
    "experiment": "Thử nghiệm", "title": "Tên", "hypothesis": "Giả thuyết", "primary_metric": "Chỉ số chính", "guardrail_metric": "Chỉ số bảo vệ",
    "sample_or_duration": "Cỡ mẫu/thời gian", "quick_actions": "Việc nhanh", "council": "Góc nhìn hội đồng", "lens": "Góc nhìn",
    "market_size": "Quy mô thị trường", "method": "Phương pháp", "bottom_up_formula": "Công thức bottom-up", "inputs_needed": "Dữ liệu cần thu",
    "figures": "Số liệu", "value": "Giá trị", "sections": "Phân tích", "points": "Nhận định", "swot": "SWOT", "strengths": "Điểm mạnh",
    "weaknesses": "Điểm yếu", "opportunities": "Cơ hội", "threats": "Nguy cơ", "gtm_4_weeks": "Kế hoạch 4 tuần", "competitors": "Đối thủ",
    "website": "Website", "what_they_sell": "Bán gì", "price_info": "Giá", "positioning": "Định vị", "products": "Sản phẩm", "channels": "Kênh",
    "customer_complaints": "Khách phàn nàn", "where_we_win": "Nơi mình thắng", "objection_scripts": "Khi khách so sánh",
    "watch_items": "Cần theo dõi", "video_script": "Kịch bản video", "time": "Thời lượng", "visual": "Hình", "audio": "Lời/âm thanh",
    "on_screen_text": "Chữ trên màn hình", "image_prompt": "Prompt ảnh", "rows": "Lịch", "date": "Ngày", "pillar": "Trụ cột", "topic": "Chủ đề",
    "intent": "Loại", "holiday": "Ngày lễ", "mix": "Tỉ lệ thực tế %", "missing_info": "Cần bổ sung", "lesson": "Bài học", "kpi_block": "KPI",
}
SKIP = {"source_ids", "tag", "lesson", "missing_info", "evidence_lines"}


def _label(key: str) -> str:
    return LABELS.get(key, key.replace("_", " ").capitalize())


def _scalar(v: Any) -> str:
    if isinstance(v, bool):
        return "Có" if v else "Không"
    if isinstance(v, float) and v.is_integer():
        return f"{int(v):,}".replace(",", ".")
    if isinstance(v, (int, float)):
        return f"{v:,}".replace(",", ".") if abs(v) >= 1000 else str(v)
    return str(v).replace("\n", " ").replace("|", "/") if v is not None else ""


def _point(p: Dict[str, Any]) -> str:
    refs = "".join(f"[{i}]" for i in p.get("source_ids") or [])
    tag = p.get("tag", "")
    tag_txt = "" if tag == "Có nguồn" else f" {tag}"
    return f"{p.get('text', '')}{tag_txt} {refs}".rstrip()


def _is_point(v: Any) -> bool:
    return isinstance(v, dict) and "text" in v and "tag" in v


def _render(value: Any, depth: int) -> List[str]:
    out: List[str] = []
    if _is_point(value):
        return [_point(value)]
    if isinstance(value, dict):
        for k, v in value.items():
            if k in SKIP or v in (None, "", [], {}):
                continue
            if isinstance(v, (dict, list)) and not _is_point(v):
                out.append(f"{'#' * min(depth, 6)} {_label(k)}")
                out += _render(v, depth + 1)
            else:
                out.append(f"- **{_label(k)}:** {_point(v) if _is_point(v) else _scalar(v)}")
        return out
    if isinstance(value, list):
        if all(not isinstance(x, (dict, list)) for x in value):
            return [f"- {_scalar(x)}" for x in value]
        if all(_is_point(x) for x in value):
            return [f"- {_point(x)}" for x in value]
        flat = all(isinstance(x, dict) and all(not isinstance(y, (dict, list)) or k in SKIP for k, y in x.items()) for x in value)
        if flat and value:
            keys = [k for k in value[0].keys() if k not in SKIP]
            out.append("| " + " | ".join(_label(k) for k in keys) + " |")
            out.append("|" + "---|" * len(keys))
            for x in value:
                out.append("| " + " | ".join(_scalar(x.get(k, "")) for k in keys) + " |")
            return out
        for i, x in enumerate(value, 1):
            if isinstance(x, dict):
                title = next((str(x[k]) for k in ("name", "title", "phase", "stage", "angle", "step", "headline", "channel") if x.get(k)), f"#{i}")
                out.append(f"{'#' * min(depth, 6)} {i}. {title}")
                out += _render(x, depth + 1)
            else:
                out += _render(x, depth + 1)
        return out
    return [_scalar(value)]


def to_markdown(title: str, data: Dict[str, Any], provenance: Dict[str, Any]) -> str:
    lines = [f"# {title}", ""]
    meta = []
    if provenance.get("model"):
        meta.append(f"AI: {provenance['model']}")
    meta.append("có tìm kiếm Google" if provenance.get("grounded") else "không tìm kiếm web")
    if provenance.get("generated_at"):
        meta.append(provenance["generated_at"])
    if provenance.get("context_version"):
        meta.append(f"hồ sơ v{provenance['context_version']}")
    lines.append("*" + " · ".join(meta) + "*")
    lines.append("")
    lines += _render(data, 2)
    if "competitors" in data and not data["competitors"]:
        lines += ["", "*Chưa tìm thấy đối thủ phù hợp tiêu chí tại khu vực đã chọn.*"]
    if data.get("missing_info"):
        lines += ["", "## Cần bổ sung"] + [f"- {x}" for x in data["missing_info"]]
    if data.get("lesson"):
        lines += ["", "## Bài học"] + [f"- {x}" for x in data["lesson"]]
    sources = provenance.get("sources") or []
    if sources:
        lines += ["", "## Nguồn"] + [f"{i}. [{s.get('title') or s.get('url')}]({s.get('url')})" for i, s in enumerate(sources, 1)]
    return "\n".join(lines).strip() + "\n"
