# -*- coding: utf-8 -*-
"""Gemini thật trả 429/503 khá thường xuyên: kiểm thử thử lại, chờ theo RetryInfo, và báo lỗi theo từng model."""
import pytest

from app import llm


class Resp:
    def __init__(self, status, payload):
        self.status_code = status
        self._payload = payload

    def json(self):
        return self._payload


def err(status, message, code_status, details=None):
    return Resp(status, {"error": {"code": status, "message": message, "status": code_status, "details": details or []}})


OK = Resp(200, {"candidates": [{"content": {"parts": [{"text": "{\"ok\": true}"}]}, "finishReason": "STOP"}]})
PER_MINUTE = err(429, "Quota exceeded for metric generate_content_free_tier_requests, limit: 10", "RESOURCE_EXHAUSTED", [
    {"@type": "type.googleapis.com/google.rpc.QuotaFailure",
     "violations": [{"quotaMetric": "generativelanguage.googleapis.com/generate_content_free_tier_requests",
                     "quotaId": "GenerateRequestsPerMinutePerProjectPerModel-FreeTier"}]},
    {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "7s"}])
LIMIT_ZERO = err(429, "Quota exceeded for metric: generate_content_free_tier_input_token_count, limit: 0", "RESOURCE_EXHAUSTED", [
    {"@type": "type.googleapis.com/google.rpc.QuotaFailure",
     "violations": [{"quotaId": "GenerateContentInputTokensPerModelPerMinute-FreeTier"}]}])
PER_DAY = err(429, "Quota exceeded", "RESOURCE_EXHAUSTED", [
    {"@type": "type.googleapis.com/google.rpc.QuotaFailure", "violations": [{"quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier"}]}])
OVERLOADED = err(503, "The model is overloaded. Please try again later.", "UNAVAILABLE")


@pytest.fixture
def seq(monkeypatch):
    calls, waits = [], []

    def install(responses):
        queue = list(responses)

        def fake_post(url, headers=None, json=None, timeout=None):
            calls.append(url.rsplit("/", 1)[-1])
            return queue.pop(0)
        monkeypatch.setattr(llm.requests, "post", fake_post)
        monkeypatch.setattr(llm, "_sleep", lambda s: waits.append(s))
        return calls, waits
    return install


def test_quota_kinds_parsed():
    assert llm._quota_details(PER_MINUTE.json()["error"]) == ("minute", 7.0)
    assert llm._quota_details(LIMIT_ZERO.json()["error"])[0] == "zero"
    assert llm._quota_details(PER_DAY.json()["error"])[0] == "day"


def test_503_retried_on_same_model(seq):
    calls, waits = seq([OVERLOADED, OVERLOADED, OK])
    assert llm._post("k", "models/gemini-a:generateContent", {})["candidates"]
    assert calls == ["gemini-a:generateContent"] * 3 and len(waits) == 2


def test_per_minute_429_waits_retry_delay(seq):
    calls, waits = seq([PER_MINUTE, OK])
    llm._post("k", "models/gemini-a:generateContent", {})
    assert len(calls) == 2 and waits == [7.5]


def test_limit_zero_and_per_day_do_not_wait(seq):
    for resp in (LIMIT_ZERO, PER_DAY):
        calls, waits = seq([resp])
        with pytest.raises(llm.LLMError) as e:
            llm._post("k", "models/gemini-a:generateContent", {})
        assert e.value.code == "quota" and waits == []
        calls.clear()


def test_all_models_fail_reports_each_reason(seq):
    seq([LIMIT_ZERO, OVERLOADED, OVERLOADED, OVERLOADED, PER_DAY])
    with pytest.raises(llm.LLMError) as e:
        llm._call_with_fallback("k", ["gemini-x", "gemini-y", "gemini-z"], lambda m: {})
    msg = e.value.message
    assert "gemini-x: key không có hạn mức" in msg and "gemini-y: đang quá tải (503)" in msg and "gemini-z: hết hạn mức trong ngày" in msg
    assert e.value.code == "unavailable"


def test_fallback_succeeds_on_next_model(seq):
    calls, _ = seq([LIMIT_ZERO, OK])
    model, payload = llm._call_with_fallback("k", ["gemini-x", "gemini-y"], lambda m: {})
    assert model == "gemini-y" and calls == ["gemini-x:generateContent", "gemini-y:generateContent"]
