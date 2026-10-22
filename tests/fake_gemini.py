# -*- coding: utf-8 -*-
"""Giả lập Gemini API cho test: sinh JSON hợp lệ từ chính JSON Schema của tác vụ, cho phép ghi đè từng tác vụ."""
from __future__ import annotations

import copy
import json
import re
from typing import Any, Callable, Dict, List, Optional

from app import llm

MODELS = [
    {"name": "models/gemini-9.0-flash", "supportedGenerationMethods": ["generateContent"]},
    {"name": "models/gemini-9.0-flash-lite", "supportedGenerationMethods": ["generateContent"]},
    {"name": "models/gemini-9.0-pro", "supportedGenerationMethods": ["generateContent"]},
    {"name": "models/gemini-9.0-flash-image", "supportedGenerationMethods": ["generateContent"]},
    {"name": "models/text-embedding-004", "supportedGenerationMethods": ["embedContent"]},
    {"name": "models/veo-9.0-fast-generate", "supportedGenerationMethods": ["predictLongRunning"]},
]


def instance(schema: Dict[str, Any]) -> Any:
    t = schema.get("type")
    if "enum" in schema:
        return schema["enum"][0]
    if t == "object":
        return {k: instance(v) for k, v in schema.get("properties", {}).items()}
    if t == "array":
        n = max(schema.get("minItems") or 1, 1)
        return [instance(schema["items"]) for _ in range(n)]
    if t == "integer":
        return 1
    if t == "number":
        return 1.0
    if t == "boolean":
        return True
    return "Nội dung mẫu"


class FakeGemini:
    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []
        self.overrides: Dict[str, Callable[[Dict[str, Any], str], Any]] = {}
        self.fail_first: List[llm.LLMError] = []
        self.grounding_sources = [{"web": {"uri": "https://nguon-a.vn/bai-1", "title": "nguon-a.vn"}},
                                  {"web": {"uri": "https://nguon-b.vn/bai-2", "title": "nguon-b.vn"}}]
        self.bad_json_once = False
        self.reject_schema_field = False

    def install(self, monkeypatch) -> "FakeGemini":
        monkeypatch.setattr(llm, "list_models", lambda key, force=False: self._list(key))
        monkeypatch.setattr(llm, "_post", self._post)
        return self

    def _list(self, key: str) -> List[Dict[str, Any]]:
        if key == "INVALID":
            raise llm.LLMError("Gemini API key không hợp lệ. Kiểm tra lại key trong mục Cài đặt.", "invalid_key")
        return MODELS

    @staticmethod
    def _task_title(prompt: str) -> str:
        m = re.search(r"NHIỆM VỤ: (.+)", prompt)
        return m.group(1).strip() if m else ""

    def _post(self, api_key: str, path: str, body: Dict[str, Any], timeout: float = 120) -> Dict[str, Any]:
        self.calls.append({"path": path, "body": copy.deepcopy(body)})
        if self.fail_first:
            raise self.fail_first.pop(0)
        if self.reject_schema_field and "responseJsonSchema" in body.get("generationConfig", {}):
            raise llm.LLMError("Yêu cầu bị từ chối (HTTP 400): Unknown name responseJsonSchema", "bad_request")
        prompt = body["contents"][0]["parts"][0]["text"]
        if "tools" in body:
            return {"candidates": [{"content": {"parts": [{"text": "Báo cáo tìm kiếm: thị trường có số liệu từ nguồn A [1]."}]},
                                    "groundingMetadata": {"groundingChunks": self.grounding_sources,
                                                          "webSearchQueries": ["truy vấn mẫu"]}}]}
        if "responseModalities" in body.get("generationConfig", {}):
            import base64
            return {"candidates": [{"content": {"parts": [{"inlineData": {"mimeType": "image/png",
                                                                          "data": base64.b64encode(b"\x89PNG fake").decode()}}]}}]}
        if self.bad_json_once:
            self.bad_json_once = False
            return {"candidates": [{"content": {"parts": [{"text": "đây không phải JSON"}]}}]}
        schema = body.get("generationConfig", {}).get("responseJsonSchema")
        if schema is None:
            m = re.search(r"(?:JSON Schema sau, không kèm giải thích:|theo schema:)\n(\{.*\})\s*$", prompt, re.S)
            schema = json.loads(m.group(1)) if m else {"type": "object", "properties": {}}
        title = self._task_title(prompt)
        data = instance(schema)
        for key, fn in self.overrides.items():
            if key in title:
                data = fn(data, prompt)
        return {"candidates": [{"content": {"parts": [{"text": json.dumps(data, ensure_ascii=False)}]}, "finishReason": "STOP"}]}
