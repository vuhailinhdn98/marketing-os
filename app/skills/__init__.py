# -*- coding: utf-8 -*-
"""
Gói skill marketing-master: nạp từng mục theo yêu cầu thay vì nhồi cả bộ vào prompt.

Mục được đánh số như trong file nguồn: "0" … "17"; mục con "5.3", "10.2"… lấy theo tiêu đề "### N.M".
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List

PACK_PATH = Path(__file__).resolve().parent / "marketing_master.md"


@lru_cache(maxsize=1)
def _sections() -> Dict[str, str]:
    text = PACK_PATH.read_text(encoding="utf-8")
    text = re.sub(r"^---.*?---\s*", "", text, flags=re.S)
    out: Dict[str, str] = {}
    top = re.split(r"(?m)^## ", text)
    for chunk in top:
        m = re.match(r"(\d+)\.\s", chunk)
        if not m:
            continue
        key = m.group(1)
        out[key] = "## " + chunk.strip()
        for sub in re.split(r"(?m)^### ", chunk)[1:]:
            sm = re.match(r"(\d+\.\d+)\s", sub)
            if sm:
                out[sm.group(1)] = "### " + sub.strip()
    return out


def section_ids() -> List[str]:
    return sorted(_sections().keys(), key=lambda k: [int(x) for x in k.split(".")])


def get_sections(ids: Iterable[str]) -> str:
    secs = _sections()
    chosen: List[str] = []
    seen = set()
    for sid in ids:
        sid = str(sid)
        if sid in seen:
            continue
        # Bỏ mục con nếu đã nạp mục cha
        parent = sid.split(".")[0]
        if "." in sid and parent in seen:
            continue
        if sid in secs:
            chosen.append(secs[sid])
            seen.add(sid)
    return "\n\n".join(chosen)


BASE_ROLE = (
    "Bạn là Marketing OS — một fractional CMO kiêm người thầy cho chủ doanh nghiệp nhỏ tại Việt Nam. "
    "Bạn làm ra sản phẩm marketing dùng được ngay và giải thích ngắn gọn vì sao. "
    "Viết tiếng Việt tự nhiên, rõ, cụ thể, không sáo rỗng, không dùng emoji trừ khi kênh đăng cần."
)

OUTPUT_RULES = """QUY TẮC BẮT BUỘC CHO MỌI ĐẦU RA:
1. Chỉ dùng thông tin có trong HỒ SƠ BỐI CẢNH và DỮ LIỆU ĐẦU VÀO. Không bịa số liệu, khách hàng, review, testimonial, giải thưởng, cam kết, chính sách, đối thủ hay điểm yếu của đối thủ.
2. Thiếu thông tin cần thiết: viết [THIẾU DỮ LIỆU] tại chỗ đó và liệt kê điều cần hỏi trong trường "missing_info".
3. Con số không có trong hồ sơ hoặc nguồn: gắn [Unverified]; suy luận của bạn: gắn [Inference]; dự đoán: gắn [Speculation].
4. Không dùng khan hiếm/đếm ngược giả, không hù dọa, không quảng cáo trá hình, không tuyên bố chữa bệnh. Không đề xuất quét UID, mua data, gửi tin cho người chưa đồng ý.
5. Mỗi đề xuất chiến thuật nêu: giai đoạn phễu/AARRR, cơ chế vì sao hiệu quả, chỉ số đo, điều kiện dừng nếu là thử nghiệm.
6. Trường "lesson": 2–4 câu ngắn giải thích nguyên lý marketing đã dùng để người dùng tự làm được lần sau.
7. Chỉ trả về JSON đúng schema."""


def system_prompt(section_list: Iterable[str]) -> str:
    ids = ["0"] + [s for s in section_list if s != "0"]
    return f"{BASE_ROLE}\n\nLUẬT LẤY TỪ SKILL MARKETING-MASTER:\n\n{get_sections(ids)}\n\n{OUTPUT_RULES}"
