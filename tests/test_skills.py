# -*- coding: utf-8 -*-
"""Skill Engine: chạy đủ 26 tác vụ với Gemini giả, kiểm hậu xử lý, nguồn, cổng tuân thủ và các thao tác lưu."""
import re
from datetime import date, timedelta

import pytest

from app import llm
from tests.conftest import register
from tests.fake_gemini import FakeGemini

FULL_CONTEXT = {
    "brand.name": "Phê Ly", "brand.industry": "Quán cà phê take-away", "product.one_liner": "Cà phê muối mang đi trong 3 phút",
    "product.price_points": [{"name": "Cà phê muối", "price_vnd": 29000}, {"name": "Bạc xỉu", "price_vnd": 25000}],
    "unit_economics.avg_order_value_vnd": 45000, "unit_economics.gross_margin_pct": 60,
    "customers.buyer": "Dân văn phòng quanh Nguyễn Phước Lan", "customers.jtbd": ["Tỉnh táo ca chiều"],
    "problem.core": "Muốn cà phê ngon mà không phải ngồi lâu", "differentiation.only_we_have": "Muối tự làm từ kem phô mai",
    "goals.business_goal": "Tăng từ 80 lên 150 ly/ngày trước 31/03/2027", "goals.primary_conversion": "Đặt món qua Zalo",
    "channels_active": ["Facebook", "TikTok", "Zalo OA"], "market.location": "Hải Châu, Đà Nẵng",
    "competitors.direct": ["Quán ABC"], "brand.address": "12 Nguyễn Phước Lan, Đà Nẵng", "brand.hotline": "0905000000",
}


@pytest.fixture
def fake(monkeypatch):
    return FakeGemini().install(monkeypatch)


@pytest.fixture
def ready(client, fake):
    h = register(client)
    assert client.patch("/api/context", json={"patch": FULL_CONTEXT, "note": "test"}, headers=h).status_code == 200
    assert client.post("/api/settings/ai", json={"api_key": "AIzaSy" + "t" * 33}, headers=h).status_code == 200
    return h


def _default_inputs(task, today):
    vals = {}
    for spec in task["inputs"]:
        name, typ = spec["name"], spec["type"]
        if typ == "select":
            vals[name] = spec["options"][0]
        elif typ == "multiselect":
            vals[name] = ["Facebook", "TikTok"] if spec.get("options") == "channels" else spec["options"][:1]
        elif typ == "number":
            vals[name] = spec.get("default") or 100000
        elif typ == "date":
            vals[name] = today
        elif typ == "checkbox":
            vals[name] = True
        else:
            vals[name] = "Dữ liệu thử cho " + spec["label"]
    if task["id"] == "content_calendar":
        vals.update({"days": 7, "posts_per_day": 1})
    if task["id"] == "budget_plan":
        vals.update({"month": "2026-11", "total_budget_vnd": 5_000_000})
    if task["id"] == "voc_extract":
        vals["raw_feedback"] = "Google Maps: Nội dung mẫu ngon\nInbox: Có giao không em?"
    return vals


def test_catalog_and_every_task_runs(client, ready, fake):
    cat = client.get("/api/skills", headers=ready).json()
    assert len(cat["tasks"]) == 26
    today = date.today().isoformat()
    for task in cat["tasks"]:
        res = client.post(f"/api/skills/{task['id']}/run", json={"inputs": _default_inputs(task, today)}, headers=ready).json()
        assert res["status"] == "ok", (task["id"], res)
        assert res["run_id"] and res["markdown"].startswith("# ")
        assert res["provenance"]["model"] == "gemini-9.0-flash"
        assert res["provenance"]["status"] == "ai"
        assert "lesson" in res["output"]
        if task["grounded"]:
            assert res["provenance"]["grounded"] is True and len(res["provenance"]["sources"]) >= 2
    runs = client.get("/api/skills/runs", headers=ready).json()["runs"]
    assert len(runs) == 26


def test_system_prompt_contains_only_relevant_sections(client, ready, fake):
    client.post("/api/skills/offer_lab/run", json={"inputs": {"offer_current": "Mua 2 ly tặng 1 bánh"}}, headers=ready)
    system = fake.calls[-1]["body"]["systemInstruction"]["parts"][0]["text"]
    assert "## 6. Thiết kế ưu đãi" in system and "## 0. Nguyên tắc" in system
    assert "## 10. Quảng cáo trả phí" not in system
    prompt = fake.calls[-1]["body"]["contents"][0]["parts"][0]["text"]
    assert "Phê Ly" in prompt and "Chất lượng vượt trội" not in prompt
    assert fake.calls[-1]["body"]["generationConfig"]["responseMimeType"] == "application/json"


def test_needs_context_lists_questions(client, fake):
    h = register(client)
    client.post("/api/settings/ai", json={"api_key": "AIzaSy" + "t" * 33}, headers=h)
    res = client.post("/api/skills/offer_lab/run", json={"inputs": {"offer_current": "x"}}, headers=h).json()
    assert res["status"] == "needs_context"
    assert {m["path"] for m in res["missing"]} == {"product.one_liner", "customers.buyer", "problem.core"}
    assert all(m["question"] for m in res["missing"])
    assert fake.calls == []


def test_no_key_is_not_generated(client):
    h = register(client)
    client.patch("/api/context", json={"patch": FULL_CONTEXT}, headers=h)
    res = client.post("/api/skills/marketing_ideas/run", json={"inputs": {"stage": "Giai đoạn đầu", "budget_level": "0 đồng"}}, headers=h).json()
    assert res["status"] == "not_generated" and res["provenance"]["error_code"] == "no_key"


def test_invalid_key(client, ready, fake):
    from app.database import execute
    execute("UPDATE user_profiles SET gemini_api_key = 'INVALID'")
    res = client.post("/api/skills/marketing_ideas/run", json={"inputs": {"stage": "Giai đoạn đầu", "budget_level": "0 đồng"}}, headers=ready).json()
    assert res["status"] == "not_generated" and res["provenance"]["error_code"] == "invalid_key"
    assert client.post("/api/settings/ai/check", headers=ready).json()["ok"] is False


def test_server_key_only_for_admin_unless_shared(client, fake, monkeypatch):
    from app import config
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSy" + "s" * 33)
    config.reload_settings()
    admin = register(client, "admin@example.com")
    other = register(client, "other@example.com")
    for h in (admin, other):
        client.patch("/api/context", json={"patch": FULL_CONTEXT}, headers=h)
    inputs = {"inputs": {"stage": "Giai đoạn đầu", "budget_level": "0 đồng"}}
    assert client.post("/api/skills/marketing_ideas/run", json=inputs, headers=admin).json()["status"] == "ok"
    assert client.post("/api/skills/marketing_ideas/run", json=inputs, headers=other).json()["status"] == "not_generated"


def test_model_fallback_on_quota(client, ready, fake):
    fake.fail_first = [llm.LLMError("quota", "quota", retry_next_model=True)]
    res = client.post("/api/skills/marketing_ideas/run", json={"inputs": {"stage": "Giai đoạn đầu", "budget_level": "0 đồng"}}, headers=ready).json()
    assert res["status"] == "ok" and res["provenance"]["model"] == "gemini-9.0-flash-lite"


def test_json_repair_and_schema_field_fallback(client, ready, fake):
    fake.bad_json_once = True
    res = client.post("/api/skills/marketing_ideas/run", json={"inputs": {"stage": "Giai đoạn đầu", "budget_level": "0 đồng"}}, headers=ready).json()
    assert res["status"] == "ok"
    fake.reject_schema_field = True
    res = client.post("/api/skills/marketing_ideas/run", json={"inputs": {"stage": "Giai đoạn đầu", "budget_level": "0 đồng"}}, headers=ready).json()
    assert res["status"] == "ok"


def test_invalid_inputs(client, ready):
    res = client.post("/api/skills/ads_plan/run", json={"inputs": {"platform": "MYSPACE", "objective": "Tin nhắn"}}, headers=ready).json()
    assert res["status"] == "invalid_input" and len(res["errors"]) >= 2
    res = client.post("/api/skills/content_calendar/run", json={"inputs": {"start_date": "2026-13-01", "days": 50, "channels": ["Myspace"]}},
                      headers=ready).json()
    assert res["status"] == "invalid_input"


def test_offer_lab_recomputes_weakest(client, ready, fake):
    def override(data, prompt):
        data["levers"] = [{"name": "Kết quả mơ ước", "score": 8, "reason": "r"}, {"name": "Khả năng đạt được cảm nhận", "score": 3, "reason": "r"},
                          {"name": "Thời gian chờ", "score": 7, "reason": "r"}, {"name": "Công sức/hy sinh", "score": 12, "reason": "r"}]
        data["weakest_lever"] = "Thời gian chờ"
        data["expected_lift"] = {"range": "+20%", "label": "chắc chắn"}
        return data
    fake.overrides["Offer Lab"] = override
    res = client.post("/api/skills/offer_lab/run", json={"inputs": {"offer_current": "Mua 2 tặng 1"}}, headers=ready).json()
    assert res["output"]["weakest_lever"] == "Khả năng đạt được cảm nhận"
    assert res["output"]["expected_lift"]["label"] == "[Unverified]"
    assert max(l["score"] for l in res["output"]["levers"]) == 10


def test_calendar_dates_channels_mix_and_save(client, ready, fake):
    start = date(2026, 2, 14)

    def override(data, prompt):
        dates = re.findall(r"- (\d{4}-\d{2}-\d{2}) \(", prompt)
        rows = []
        for i, d in enumerate(dates):
            intent = "findable" if i < 4 else "shareable" if i < 6 else "experiment"
            rows.append({"date": d, "channel": "Facebook", "pillar": "Giáo dục", "topic": f"Chủ đề {i}", "format": "Ảnh",
                         "hook": "h", "cta": "Nhắn Zalo đặt món", "metric": "Tin nhắn", "intent": intent, "funnel_stage": "Nhận biết"})
        rows.append({"date": dates[0], "channel": "Myspace", "pillar": "x", "topic": "Sai kênh", "format": "x", "hook": "x", "cta": "x",
                     "metric": "x", "intent": "findable", "funnel_stage": "Nhận biết"})
        rows.append({"date": "2030-01-01", "channel": "Facebook", "pillar": "x", "topic": "Sai ngày", "format": "x", "hook": "x", "cta": "x",
                     "metric": "x", "intent": "findable", "funnel_stage": "Nhận biết"})
        data["rows"] = rows
        return data
    fake.overrides["Lịch nội dung"] = override
    res = client.post("/api/skills/content_calendar/run", json={"inputs": {"start_date": start.isoformat(), "days": 7,
                                                                           "channels": ["Facebook", "TikTok"], "posts_per_day": 1}},
                      headers=ready).json()
    rows = res["output"]["rows"]
    assert len(rows) == 7 and all(r["channel"] == "Facebook" for r in rows)
    assert rows[0]["holiday"] == "Lễ Tình nhân"
    assert res["output"]["mix"] == {"findable": 57, "shareable": 29, "experiment": 14}
    prompt = fake.calls[-1]["body"]["contents"][0]["parts"][0]["text"]
    assert "Tết Nguyên Đán" in prompt
    saved = client.post(f"/api/skills/runs/{res['run_id']}/to-calendar", headers=ready).json()
    assert saved["saved"] == 7
    cal = client.get(f"/api/calendar?start={start.isoformat()}&days=7", headers=ready).json()
    assert len(cal["items"]) == 7 and cal["items"][0]["plan_date"] == start.isoformat()
    assert any(h["name"] == "Tết Nguyên Đán (mùng 1)" for h in cal["holidays"])


def test_ads_plan_names_budget_kpi(client, ready, fake):
    def override(data, prompt):
        data["adsets"] = [{"name_audience": "Broad Đà Nẵng", "audience": "a", "role": "đã chứng minh (70%)", "exclusions": []},
                          {"name_audience": "Văn phòng Hải Châu", "audience": "b", "role": "thử nghiệm (30%)", "exclusions": []}]
        data["campaign"]["audience_label"] = "Broad Đà Nẵng"
        return data
    fake.overrides["Ads Studio"] = override
    res = client.post("/api/skills/ads_plan/run", json={"inputs": {"platform": "META", "objective": "Tin nhắn", "daily_budget_vnd": 200000,
                                                                   "days": 10, "offer": "Combo 2", "period_tag": "2026Q4",
                                                                   "cost_per_result_estimate_vnd": 8000}}, headers=ready).json()
    out = res["output"]
    assert out["campaign"]["name"] == "META_Tin-Nhan_Broad-Da-Nang_Combo-2_2026q4"
    assert [a["daily_budget_vnd"] for a in out["adsets"]] == [140000, 60000]
    assert out["kpi"]["total_budget_vnd"] == 2_000_000 and out["kpi"]["expected_results"] == 250
    assert any("20%" in r for r in out["operating_rules"])


def test_budget_plan_recomputes_and_saves(client, ready, fake):
    def override(data, prompt):
        data["lines"] = [{"program": "Quảng cáo trả phí", "item": "FB tin nhắn", "unit_price": 100000, "unit": "VND/ngày", "quantity": 30,
                          "kpi_formula": "tin nhắn = ngân sách ÷ chi phí/tin"},
                         {"program": "Content", "item": "Chụp ảnh", "unit_price": 1500000, "unit": "VND/buổi", "quantity": 2, "kpi_formula": "-"}]
        return data
    fake.overrides["Lập ngân sách"] = override
    res = client.post("/api/skills/budget_plan/run", json={"inputs": {"month": "2026-11", "total_budget_vnd": 5_000_000}}, headers=ready).json()
    assert res["output"]["total_projected"] == 6_000_000
    assert any(n["code"] == "G08" and "vượt" in n["message"] for n in res["notes"])
    saved = client.post(f"/api/skills/runs/{res['run_id']}/to-budget", headers=ready).json()
    assert saved["saved"] == 2
    bud = client.get("/api/budget?month=2026-11", headers=ready).json()
    assert bud["projected_total"] == 6_000_000


def test_grounded_sources_and_unverified(client, ready, fake):
    def override(data, prompt):
        data["sections"] = [{"title": "Kinh tế", "points": [{"text": "Có số liệu", "source_ids": [1], "tag": "Có nguồn"},
                                                             {"text": "Không có nguồn mà ghi có", "source_ids": [9], "tag": "Có nguồn"}]}]
        return data
    fake.overrides["Nghiên cứu thị trường"] = override
    res = client.post("/api/skills/market_research/run", json={"inputs": {"location": "Đà Nẵng", "objective": "Mở điểm mới?"}}, headers=ready).json()
    pts = res["output"]["sections"][0]["points"]
    assert pts[0]["tag"] == "Có nguồn" and pts[1]["tag"] == "[Unverified]" and pts[1]["source_ids"] == []
    assert "## Nguồn" in res["markdown"] and "https://nguon-a.vn/bai-1" in res["markdown"]
    tools_call = [c for c in fake.calls if "tools" in c["body"]]
    assert tools_call and tools_call[-1]["body"]["tools"] == [{"google_search": {}}]


def test_discovery_drops_unsourced_and_saves(client, ready, fake):
    def override(data, prompt):
        data["competitors"] = [{"name": "Cà phê Có Nguồn", "type": "Trực tiếp", "website": "", "what_they_sell": "cà phê",
                                "price_info": "", "source_ids": [2]},
                               {"name": "Đối thủ bịa", "type": "Trực tiếp", "website": "", "what_they_sell": "", "price_info": "", "source_ids": []},
                               {"name": "Quán ABC", "type": "Trực tiếp", "website": "", "what_they_sell": "", "price_info": "", "source_ids": []}]
        return data
    fake.overrides["Rà soát đối thủ"] = override
    res = client.post("/api/skills/competitor_discovery/run", json={"inputs": {"location": "Đà Nẵng"}}, headers=ready).json()
    names = [c["name"] for c in res["output"]["competitors"]]
    assert names == ["Cà phê Có Nguồn", "Quán ABC"]
    client.post(f"/api/skills/runs/{res['run_id']}/to-competitors", headers=ready)
    comps = client.get("/api/competitors", headers=ready).json()["competitors"]
    saved = {c["name"]: c for c in comps}
    assert saved["Cà phê Có Nguồn"]["evidence"][0]["url"] == "https://nguon-b.vn/bai-2"


def test_voc_rejects_fake_quotes_and_small_samples(client, ready, fake):
    def override(data, prompt):
        data["verbatim_quotes"] = [{"quote": "chờ hơi lâu", "line": 1}, {"quote": "ngon nhất Đà Nẵng", "line": 2}]
        data["pains"] = [{"text": "Chờ lâu", "evidence_lines": [1, 99]}, {"text": "Bịa", "evidence_lines": [50]}]
        data["persona"] = {"allowed": True, "summary": "Persona đầy đủ"}
        return data
    fake.overrides["VoC"] = override
    res = client.post("/api/skills/voc_extract/run", json={"inputs": {"raw_feedback": "Google Maps: Ngon nhưng chờ hơi lâu\nInbox: Có giao không?"}},
                      headers=ready).json()
    out = res["output"]
    assert [q["quote"] for q in out["verbatim_quotes"]] == ["chờ hơi lâu"]
    assert len(out["pains"]) == 1 and out["pains"][0]["evidence_lines"] == [1] and out["pains"][0]["confidence"] == "Thấp"
    assert out["persona"]["allowed"] is False and out["data_points"] == 2
    added = client.post(f"/api/skills/runs/{res['run_id']}/to-context", json={}, headers=ready).json()
    assert added["added"] == 1
    ctx = client.get("/api/context", headers=ready).json()["context"]
    assert ctx["customer_language"]["verbatim"][0]["quote"] == "chờ hơi lâu"


def test_kol_brief_gets_disclosure(client, ready, fake):
    res = client.post("/api/skills/kol_brief/run", json={"inputs": {"kol_name": "Bếp Nhà Lan", "audience_fit": "Dân văn phòng", "campaign_goal": "Thử món"}},
                      headers=ready).json()
    assert "Quảng cáo" in res["output"]["brief"]["disclosure_requirement"]
    assert not any(b["code"] == "G06" for b in res["guardrails"]["blockers"])
    assert any(n["code"] == "KOL" for n in res["notes"])  # chưa tick "đã dùng sản phẩm"


def test_copy_to_content_and_gating(client, ready, fake):
    def override(data, prompt):
        data["variants"] = [{"headline": "Cà phê muối 3 phút", "hook": "h", "hook_type": "Giá trị",
                             "body": "Chỉ còn 5 suất cuối hôm nay!", "cta": "Nhắn Zalo đặt món", "rationale": "r"},
                            {"headline": "B", "hook": "h", "hook_type": "Tò mò", "body": "Ghé quán thử ly đầu.", "cta": "Ghé quán", "rationale": "r"}]
        data["recommended"] = 7
        return data
    fake.overrides["Copy Studio"] = override
    res = client.post("/api/skills/copy_studio/run", json={"inputs": {"channel": "Bài Facebook", "topic": "Cà phê muối"}}, headers=ready).json()
    assert res["output"]["recommended"] == 0
    assert any(b["code"] == "G03" for b in res["guardrails"]["blockers"])
    item = client.post(f"/api/skills/runs/{res['run_id']}/to-content", json={"variant": 0}, headers=ready).json()["item"]
    assert item["guardrails"]["blockers"]
    blocked = client.patch(f"/api/content/{item['id']}/status", json={"status": "approved"}, headers=ready)
    assert blocked.status_code == 400 and "tuân thủ" in blocked.json()["detail"]
    fixed = client.put(f"/api/content/{item['id']}", json={"body": "Ghé quán thử ly cà phê muối đầu tiên."}, headers=ready).json()["item"]
    assert fixed["guardrails"]["blockers"] == []
    ok = client.patch(f"/api/content/{item['id']}/status", json={"status": "approved"}, headers=ready)
    assert ok.status_code == 200
    pub = client.post(f"/api/content/{item['id']}/publish", headers=ready)
    assert pub.status_code == 400 and "webhook" in pub.json()["detail"]


def test_publish_marks_only_on_success(client, ready, monkeypatch):
    from app.services import content as content_service
    item = client.post("/api/content", json={"channel": "Facebook", "topic": "Bài thử", "body": "Ghé quán nhé."}, headers=ready).json()["item"]
    client.patch(f"/api/content/{item['id']}/status", json={"status": "approved"}, headers=ready)
    monkeypatch.setattr(content_service, "webhook_url", lambda owner: "https://hooks.example.com/x")
    monkeypatch.setattr(content_service, "post_json", lambda url, payload: (False, "Máy nhận trả HTTP 500"))
    res = client.post(f"/api/content/{item['id']}/publish", headers=ready).json()
    assert res["delivered"] is False and res["item"]["status"] == "approved"
    monkeypatch.setattr(content_service, "post_json", lambda url, payload: (True, "HTTP 200"))
    res = client.post(f"/api/content/{item['id']}/publish", headers=ready).json()
    assert res["delivered"] is True and res["item"]["status"] == "published"


def test_weekly_loop_uses_real_bottleneck_and_saves_experiment(client, ready, fake):
    for i in range(10):
        lead = client.post("/api/leads", json={"full_name": f"K{i}", "phone": f"09000000{i}"}, headers=ready).json()["lead"]
        if i < 8:
            client.patch(f"/api/leads/{lead['id']}/status", json={"status": "consulting"}, headers=ready)
        if i < 1:
            client.patch(f"/api/leads/{lead['id']}/status", json={"status": "won"}, headers=ready)
    res = client.post("/api/skills/weekly_loop/run", json={"inputs": {}}, headers=ready).json()
    assert res["output"]["bottleneck_stage"] == "Đang tư vấn → Đã mua lần đầu"
    exp = client.post(f"/api/skills/runs/{res['run_id']}/to-experiment", headers=ready).json()
    assert exp["experiment_id"]
    assert client.get("/api/experiments", headers=ready).json()["experiments"][0]["status"] == "planned"


def test_run_history_markdown_download_and_delete(client, ready, fake):
    res = client.post("/api/skills/marketing_ideas/run", json={"inputs": {"stage": "Giai đoạn đầu", "budget_level": "0 đồng"}}, headers=ready).json()
    md = client.get(f"/api/skills/runs/{res['run_id']}/markdown", headers=ready)
    assert md.status_code == 200 and "attachment" in md.headers["content-disposition"]
    assert client.delete(f"/api/skills/runs/{res['run_id']}", headers=ready).status_code == 200
    assert client.get(f"/api/skills/runs/{res['run_id']}", headers=ready).status_code == 404


def test_quickstart_logs(client, ready, fake):
    assert client.post("/api/autopilot/run", headers=ready).status_code == 200
    logs = client.get("/api/autopilot/status", headers=ready).json()["logs"]
    statuses = {l["task_code"]: l["status"] for l in reversed(logs)}
    assert statuses.get("CONTENT_PILLARS") == "SUCCESS" and statuses.get("QUICKSTART") == "DONE"


def test_media_image(client, ready, fake, tmp_path):
    job = client.post("/api/media/image", json={"prompt": "Ly cà phê muối trên bàn gỗ, ánh nắng sáng", "aspect_ratio": "1:1"},
                      headers=ready).json()["job"]
    assert job["status"] == "done" and job["model"] == "gemini-9.0-flash-image"
    f = client.get(f"/api/media/{job['id']}/file", headers=ready)
    assert f.status_code == 200 and f.content.startswith(b"\x89PNG")
    bad = client.post("/api/media/image", json={"prompt": "Doraemon cầm ly cà phê muối"}, headers=ready)
    assert bad.status_code == 400


def test_coerce_to_schema_fixes_small_deviations():
    schema = {"type": "object", "required": ["stage", "n", "tags", "missing_info"], "properties": {
        "stage": {"type": "string", "enum": ["Nhận biết", "Cân nhắc"]}, "n": {"type": "integer"},
        "price": {"type": "number"}, "tags": {"type": "array", "items": {"type": "string"}, "maxItems": 2},
        "missing_info": {"type": "array", "items": {"type": "string"}}, "label": {"type": "string"}}}
    out = llm.coerce_to_schema({"stage": " nhận biết ", "n": "3", "price": "1.200.000 đ", "tags": "một", "label": 5}, schema)
    assert out == {"stage": "Nhận biết", "n": 3, "price": 1200000.0, "tags": ["một"], "label": "5", "missing_info": []}
    assert llm.coerce_to_schema({"tags": ["a", "b", "c"]}, schema)["tags"] == ["a", "b"]


def test_check_key_runs_generation_probe(client, ready, fake):
    r = client.post("/api/settings/ai/check", headers=ready).json()
    assert r["ok"] and r["generate"]["ok"] and r["generate"]["model"].startswith("gemini-9.0")
    fake.fail_first = [llm.LLMError("Gemini từ chối yêu cầu (thường do vùng/billing). Gemini báo: billing", "forbidden")]
    r = client.post("/api/settings/ai/check", headers=ready).json()
    assert r["ok"] and not r["generate"]["ok"] and "billing" in r["generate"]["error"]


def test_truncated_output_reports_clearly(client, ready, fake):
    orig = fake._post

    def cut(api_key, path, body, timeout=120):
        res = orig(api_key, path, body, timeout)
        if "generateContent" in path and "tools" not in body:
            res["candidates"][0]["content"]["parts"][0]["text"] = res["candidates"][0]["content"]["parts"][0]["text"][:40]
            res["candidates"][0]["finishReason"] = "MAX_TOKENS"
        return res
    llm._post = cut
    res = client.post("/api/skills/content_pillars/run", json={"inputs": {}}, headers=ready).json()
    assert res["status"] == "not_generated" and res["provenance"]["error_code"] == "truncated"
