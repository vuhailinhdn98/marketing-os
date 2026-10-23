# -*- coding: utf-8 -*-
"""Kiểm thử chuyên sâu tính năng Viết lại & Humanize AI (Bypass 99%) và AI Market Radar."""
from app.services.humanize import (
    analyze_ai_text,
    run_humanize,
    detect_keyword_cannibalization,
    list_humanize_history,
    get_humanize_record,
)


def test_service_analyze_ai_text():
    sample_ai_text = (
        "Trong thời đại số ngày nay, công nghệ AI đóng vai trò vô cùng quan trọng "
        "trong việc tối ưu hóa quy trình marketing. Để đạt được kết quả như mong muốn, "
        "chúng ta không chỉ áp dụng công cụ mà còn phải liên tục đổi mới tư duy. "
        "Tóm lại, chuyển đổi số là một yếu tố không thể thiếu đối với mọi doanh nghiệp."
    )
    result = analyze_ai_text(sample_ai_text)
    assert result["word_count"] > 20
    assert result["sentence_count"] >= 3
    assert len(result["cliches_found"]) >= 2  # phát hiện các cụm từ sáo rỗng AI tiếng Việt
    assert result["ai_score"] >= 50
    assert result["human_score"] <= 50
    assert "detectors" in result
    assert result["detectors"]["gptzero"]["ai_probability"] >= 50
    assert result["detectors"]["turnitin"]["ai_probability"] >= 50
    assert "quality_radar" in result
    assert result["quality_radar"]["naturalness"] > 0


def test_service_run_humanize_local_engine():
    user_email = "test_humanize@example.com"
    sample_text = (
        "Trong thời đại số ngày nay, Marketing OS đóng vai trò quan trọng đối với các doanh nghiệp SMB. "
        "Việc triển khai AI SEO giúp tăng trưởng lượng truy cập tự nhiên một cách bền vững."
    )
    keywords = ["Marketing OS", "AI SEO"]
    res = run_humanize(
        user_email,
        sample_text,
        mode="Tự nhiên",
        tone="Chuyên gia",
        audience="Chủ doanh nghiệp",
        keywords=keywords
    )

    assert res["id"] > 0
    assert res["humanized_text"]
    assert res["human_probability_after"] >= 80
    assert res["ai_probability_after"] <= 20
    # Bảo toàn từ khóa SEO được chỉ định
    for kw in keywords:
        assert kw.lower() in res["humanized_text"].lower()

    # Kiểm tra các detector đo lường sau khi viết lại
    assert res["detectors"]["turnitin"]["after"] <= 5.0
    assert res["detectors"]["gptzero"]["after"] <= 5.0
    assert res["quality_radar"]["naturalness"] >= 75


def test_service_cannibalization_detection(client, auth):
    # Tạo 2 bài viết có cùng từ khóa mục tiêu để kiểm tra cảnh báo ăn thịt từ khóa
    res1 = client.post(
        "/api/content",
        json={
            "topic": "content chuẩn SEO cho người mới bắt đầu",
            "body": "Nội dung bài viết về content chuẩn SEO chi tiết...",
            "channel": "Facebook",
            "status": "draft",
        },
        headers=auth,
    )
    assert res1.status_code == 200

    res2 = client.post(
        "/api/content",
        json={
            "topic": "content chuẩn SEO top 10 mẹo thực chiến",
            "body": "Nội dung bài viết thứ 2 cũng tối ưu content chuẩn SEO...",
            "channel": "Facebook",
            "status": "draft",
        },
        headers=auth,
    )
    assert res2.status_code == 200

    cannibal_res = client.post("/api/seo/cannibalization", headers=auth).json()
    assert "report" in cannibal_res
    report = cannibal_res["report"]
    assert report["cannibalized_count"] >= 1
    groups = report["groups"]
    assert any("content chuẩn seo" in g["keyword"].lower() for g in groups)
    assert len(groups[0]["articles"]) >= 2


def test_humanize_api_endpoints_workflow(client, auth):
    # 1. Unauthenticated request should return 401
    unauth = client.post("/api/humanize/analyze", json={"text": "Bài viết mẫu"})
    assert unauth.status_code == 401

    # 2. Analyze API
    raw_text = (
        "Trong thời đại công nghệ số ngày nay, trí tuệ nhân tạo đóng vai trò hết sức quan trọng. "
        "Không chỉ giúp tự động hóa mà còn nâng cao hiệu suất làm việc vượt bậc."
    )
    an_res = client.post("/api/humanize/analyze", json={"text": raw_text}, headers=auth)
    assert an_res.status_code == 200
    analysis = an_res.json()["analysis"]
    assert analysis["word_count"] > 0
    assert analysis["ai_score"] >= 40
    assert len(analysis["cliches_found"]) >= 1

    # 3. Rewrite API
    rw_res = client.post(
        "/api/humanize/rewrite",
        json={
            "text": raw_text,
            "mode": "Tự nhiên",
            "tone": "Thuyết phục",
            "keywords": ["trí tuệ nhân tạo", "hiệu suất"],
        },
        headers=auth,
    )
    assert rw_res.status_code == 200
    rw_data = rw_res.json()
    assert rw_data["ok"] is True
    result = rw_data["result"]
    assert result["human_probability_after"] >= 80
    assert "trí tuệ nhân tạo" in result["humanized_text"].lower()
    hist_id = result["id"]
    assert hist_id > 0

    # 4. History API
    hist_list = client.get("/api/humanize/history", headers=auth).json()
    assert "history" in hist_list
    assert len(hist_list["history"]) >= 1
    assert any(item["id"] == hist_id for item in hist_list["history"])

    # 5. History detail API
    hist_detail = client.get(f"/api/humanize/{hist_id}", headers=auth).json()
    assert hist_detail["record"]["id"] == hist_id
    assert hist_detail["record"]["human_after_pct"] >= 80


def test_seo_radar_api(client, auth):
    radar_res = client.post(
        "/api/seo/radar",
        json={"industry": "F&B Nhà Hàng", "location": "Hà Nội"},
        headers=auth
    )
    assert radar_res.status_code == 200
    data = radar_res.json()
    assert data["ok"] is True
    radar = data["radar"]
    assert radar["industry"] == "F&B Nhà Hàng"
    assert radar["location"] == "Hà Nội"
    assert len(radar["trends"]) > 0
    assert radar["health_score"] > 0
