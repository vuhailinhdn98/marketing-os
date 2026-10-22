# -*- coding: utf-8 -*-
"""
Lớp gọi Gemini API (Google AI Studio) qua REST generateContent.

Nguyên tắc:
- Không bao giờ âm thầm trả nội dung mẫu khi AI lỗi: trả LLMResult(ok=False, error=...) để giao diện báo rõ.
- Danh sách model lấy từ models.list của chính API key (không ghi cứng tên model sắp hết hạn).
- Đầu ra có cấu trúc: yêu cầu JSON + kiểm tra bằng JSON Schema, sửa lại một lần nếu sai.
- Nghiên cứu có nguồn: bật công cụ google_search, đọc groundingMetadata để lấy URL nguồn thật.
- API key gửi trong header x-goog-api-key, không nằm trong URL.
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import requests

log = logging.getLogger("marketing_os.llm")

API_BASE = "https://generativelanguage.googleapis.com/v1beta"
MODEL_CACHE_TTL = 3600
_model_cache: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}
_cache_lock = threading.Lock()

DEFAULT_TEXT_MODELS = ["gemini-2.5-flash", "gemini-flash-latest"]
_EXCLUDE_TEXT = ("image", "tts", "audio", "live", "embedding", "robotics", "computer-use", "learnlm",
                 "gemma", "aqa", "veo", "imagen", "lyria", "omni", "thinking-exp")


class LLMError(Exception):
    def __init__(self, message: str, code: str = "error", retry_next_model: bool = False):
        super().__init__(message)
        self.message = message
        self.code = code
        self.retry_next_model = retry_next_model


@dataclass
class LLMResult:
    ok: bool
    text: str = ""
    data: Any = None
    model: str = ""
    grounded: bool = False
    sources: List[Dict[str, str]] = field(default_factory=list)
    search_queries: List[str] = field(default_factory=list)
    error: str = ""
    error_code: str = ""

    def provenance(self, **extra: Any) -> Dict[str, Any]:
        prov = {
            "status": "ai" if self.ok else "not_generated",
            "model": self.model,
            "grounded": self.grounded,
            "sources": self.sources,
            "search_queries": self.search_queries,
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        if not self.ok:
            prov["error"] = self.error
            prov["error_code"] = self.error_code
        prov.update(extra)
        return prov


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

def _headers(api_key: str) -> Dict[str, str]:
    return {"x-goog-api-key": api_key, "Content-Type": "application/json"}


def _raise_for(resp: requests.Response) -> None:
    if resp.status_code == 200:
        return
    try:
        err = resp.json().get("error", {})
    except ValueError:
        err = {}
    message = str(err.get("message", ""))[:300]
    status = str(err.get("status", ""))
    low = message.lower()
    if resp.status_code == 400 and ("api key not valid" in low or "api_key_invalid" in low or status == "INVALID_ARGUMENT" and "key" in low and "api" in low):
        raise LLMError("Gemini API key không hợp lệ. Kiểm tra lại key trong mục Cài đặt.", "invalid_key")
    if resp.status_code in (401, 403):
        raise LLMError("API key không có quyền dùng Gemini API (kiểm tra giới hạn key hoặc billing).", "forbidden")
    if resp.status_code == 404:
        raise LLMError(f"Model không tồn tại hoặc không hỗ trợ: {message}", "model_not_found", retry_next_model=True)
    if resp.status_code == 429:
        raise LLMError("Đã hết hạn mức (quota) của model này.", "quota", retry_next_model=True)
    if resp.status_code >= 500:
        raise LLMError(f"Máy chủ Gemini lỗi tạm thời (HTTP {resp.status_code}).", "server", retry_next_model=True)
    raise LLMError(f"Yêu cầu bị từ chối (HTTP {resp.status_code}): {message}", "bad_request")


def _post(api_key: str, path: str, body: Dict[str, Any], timeout: float = 120) -> Dict[str, Any]:
    try:
        resp = requests.post(f"{API_BASE}/{path}", headers=_headers(api_key), json=body, timeout=(10, timeout))
    except requests.RequestException as exc:
        raise LLMError(f"Không kết nối được Gemini API: {exc.__class__.__name__}", "network", retry_next_model=True) from exc
    _raise_for(resp)
    return resp.json()


# ---------------------------------------------------------------------------
# Danh sách model
# ---------------------------------------------------------------------------

def _key_id(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()[:16]


def list_models(api_key: str, force: bool = False) -> List[Dict[str, Any]]:
    kid = _key_id(api_key)
    now = time.time()
    with _cache_lock:
        cached = _model_cache.get(kid)
        if cached and not force and now - cached[0] < MODEL_CACHE_TTL:
            return cached[1]
    models: List[Dict[str, Any]] = []
    page_token = ""
    for _ in range(5):
        params = {"pageSize": 200}
        if page_token:
            params["pageToken"] = page_token
        try:
            resp = requests.get(f"{API_BASE}/models", headers=_headers(api_key), params=params, timeout=(10, 30))
        except requests.RequestException as exc:
            raise LLMError(f"Không kết nối được Gemini API: {exc.__class__.__name__}", "network") from exc
        _raise_for(resp)
        payload = resp.json()
        models.extend(payload.get("models", []))
        page_token = payload.get("nextPageToken", "")
        if not page_token:
            break
    with _cache_lock:
        _model_cache[kid] = (now, models)
    return models


def clear_model_cache() -> None:
    with _cache_lock:
        _model_cache.clear()


def _short(name: str) -> str:
    return name.split("/", 1)[1] if name.startswith("models/") else name


def _version(name: str) -> float:
    m = re.search(r"gemini-(\d+(?:\.\d+)?)", name)
    return float(m.group(1)) if m else 0.0


def rank_text_models(models: List[Dict[str, Any]], preferred: str = "") -> List[str]:
    names = []
    for m in models:
        name = _short(m.get("name", ""))
        methods = m.get("supportedGenerationMethods") or []
        if not name.startswith("gemini") or "generateContent" not in methods:
            continue
        if any(token in name for token in _EXCLUDE_TEXT):
            continue
        names.append(name)

    def score(name: str) -> Tuple:
        stable = 0 if ("preview" in name or "exp" in name) else 1
        alias = 0 if "latest" in name else 1
        if "flash-lite" in name:
            family = 2
        elif "flash" in name:
            family = 3
        elif "pro" in name:
            family = 1
        else:
            family = 0
        return (alias, stable, family, _version(name))

    ordered = sorted(set(names), key=score, reverse=True)
    if preferred and preferred in ordered:
        ordered.remove(preferred)
        ordered.insert(0, preferred)
    return ordered


def pick_models(api_key: str, preferred: str = "", kind: str = "text") -> List[str]:
    try:
        models = list_models(api_key)
    except LLMError as exc:
        if exc.code in ("invalid_key", "forbidden"):
            raise
        models = []
    if kind == "text":
        ranked = rank_text_models(models, preferred)
        if not ranked:
            ranked = ([preferred] if preferred else []) + [m for m in DEFAULT_TEXT_MODELS if m != preferred]
        return ranked[:4]
    if kind == "image":
        names = [_short(m.get("name", "")) for m in models
                 if "image" in m.get("name", "") and "generateContent" in (m.get("supportedGenerationMethods") or [])
                 and "gemini" in m.get("name", "")]
        names.sort(key=lambda n: (("preview" not in n), ("flash" in n), _version(n)), reverse=True)
        return names[:3] or ["gemini-2.5-flash-image"]
    if kind == "video":
        names = [_short(m.get("name", "")) for m in models
                 if "veo" in m.get("name", "") and "predictLongRunning" in (m.get("supportedGenerationMethods") or [])]
        names.sort(key=lambda n: (("fast" in n), ("preview" not in n), n), reverse=True)
        return names[:2]
    return []


# ---------------------------------------------------------------------------
# Sinh nội dung
# ---------------------------------------------------------------------------

def _extract(payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]]]:
    feedback = payload.get("promptFeedback") or {}
    if feedback.get("blockReason"):
        raise LLMError(f"Yêu cầu bị bộ lọc an toàn của Gemini chặn ({feedback['blockReason']}).", "blocked")
    candidates = payload.get("candidates") or []
    if not candidates:
        raise LLMError("Gemini không trả về kết quả.", "empty", retry_next_model=True)
    cand = candidates[0]
    finish = cand.get("finishReason", "")
    if finish in ("SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST", "SPII", "RECITATION"):
        raise LLMError(f"Kết quả bị Gemini chặn ({finish}).", "blocked")
    parts = (cand.get("content") or {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
    return text, cand.get("groundingMetadata") or {}, parts


def _grounding(meta: Dict[str, Any]) -> Tuple[List[Dict[str, str]], List[str]]:
    sources, seen = [], set()
    for chunk in meta.get("groundingChunks") or []:
        web = chunk.get("web") or {}
        uri = web.get("uri", "")
        if uri and uri not in seen:
            seen.add(uri)
            sources.append({"title": web.get("title") or web.get("domain") or uri, "url": uri})
    return sources, list(meta.get("webSearchQueries") or [])


def _call_with_fallback(api_key: str, models: List[str], body_for: Any) -> Tuple[str, Dict[str, Any]]:
    last: Optional[LLMError] = None
    for model in models:
        try:
            return model, _post(api_key, f"models/{model}:generateContent", body_for(model))
        except LLMError as exc:
            last = exc
            if not exc.retry_next_model:
                raise
            log.info("model %s failed (%s), trying next", model, exc.code)
    raise last or LLMError("Không có model nào khả dụng.", "no_model")


def parse_json_text(text: str) -> Any:
    s = (text or "").strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", s, re.S)
    if fence:
        s = fence.group(1).strip()
    try:
        return json.loads(s)
    except ValueError:
        pass
    starts = [i for i in (s.find("{"), s.find("[")) if i >= 0]
    if not starts:
        raise ValueError("Không tìm thấy JSON trong kết quả.")
    start = min(starts)
    end = max(s.rfind("}"), s.rfind("]"))
    return json.loads(s[start:end + 1])


def _schema_errors(data: Any, schema: Optional[Dict[str, Any]]) -> List[str]:
    if not schema:
        return []
    try:
        import jsonschema
    except ImportError:  # pragma: no cover
        return []
    validator = jsonschema.Draft202012Validator(schema)
    return [f"{'/'.join(str(p) for p in e.path) or '(gốc)'}: {e.message}" for e in validator.iter_errors(data)][:12]


def generate_json(api_key: str, *, system: str, prompt: str, schema: Dict[str, Any],
                  preferred_model: str = "", temperature: float = 0.5, max_output_tokens: int = 16384) -> LLMResult:
    """Sinh JSON đúng schema. Trả LLMResult(ok=False) kèm lý do nếu không được."""
    try:
        models = pick_models(api_key, preferred_model, "text")
    except LLMError as exc:
        return LLMResult(ok=False, error=exc.message, error_code=exc.code)

    schema_text = json.dumps(schema, ensure_ascii=False)
    full_prompt = (f"{prompt}\n\nĐỊNH DẠNG BẮT BUỘC: trả về DUY NHẤT một đối tượng JSON hợp lệ theo JSON Schema sau, "
                   f"không kèm giải thích:\n{schema_text}")
    use_schema_field = {"on": True}

    def body_for(_model: str) -> Dict[str, Any]:
        gen: Dict[str, Any] = {"temperature": temperature, "maxOutputTokens": max_output_tokens,
                               "responseMimeType": "application/json"}
        if use_schema_field["on"]:
            gen["responseJsonSchema"] = schema
        return {"systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": full_prompt}]}],
                "generationConfig": gen}

    try:
        try:
            model, payload = _call_with_fallback(api_key, models, body_for)
        except LLMError as exc:
            if exc.code == "bad_request" and use_schema_field["on"]:
                use_schema_field["on"] = False  # model/phiên bản API không nhận responseJsonSchema
                model, payload = _call_with_fallback(api_key, models, body_for)
            else:
                raise
        text, _, _ = _extract(payload)
        try:
            data = parse_json_text(text)
            errors = _schema_errors(data, schema)
        except ValueError as exc:
            data, errors = None, [str(exc)]
        if errors:
            repair = (f"Kết quả JSON trước đó chưa đúng schema. Lỗi: {errors}\n\nKết quả trước:\n{text[:12000]}\n\n"
                      f"Hãy trả lại JSON đã sửa, giữ nguyên nội dung đúng, theo schema:\n{schema_text}")
            payload = _post(api_key, f"models/{model}:generateContent", {
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": repair}]}],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": max_output_tokens,
                                     "responseMimeType": "application/json"},
            })
            text, _, _ = _extract(payload)
            data = parse_json_text(text)
            errors = _schema_errors(data, schema)
            if errors:
                return LLMResult(ok=False, model=model, text=text, error="AI trả về dữ liệu sai cấu trúc: " + "; ".join(errors[:3]),
                                 error_code="invalid_output")
        return LLMResult(ok=True, data=data, text=text, model=model)
    except LLMError as exc:
        return LLMResult(ok=False, error=exc.message, error_code=exc.code)
    except ValueError as exc:
        return LLMResult(ok=False, error=f"Không đọc được JSON từ AI: {exc}", error_code="invalid_output")


def generate_grounded(api_key: str, *, system: str, prompt: str, preferred_model: str = "",
                      temperature: float = 0.3) -> LLMResult:
    """Sinh văn bản có tìm kiếm Google (grounding). Trả kèm danh sách nguồn thật từ groundingMetadata."""
    try:
        models = pick_models(api_key, preferred_model, "text")
    except LLMError as exc:
        return LLMResult(ok=False, error=exc.message, error_code=exc.code)

    def body_for(_model: str) -> Dict[str, Any]:
        return {"systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "tools": [{"google_search": {}}],
                "generationConfig": {"temperature": temperature, "maxOutputTokens": 12288}}

    try:
        model, payload = _call_with_fallback(api_key, models, body_for)
        text, meta, _ = _extract(payload)
        sources, queries = _grounding(meta)
        return LLMResult(ok=True, text=text, model=model, grounded=bool(sources), sources=sources, search_queries=queries)
    except LLMError as exc:
        return LLMResult(ok=False, error=exc.message, error_code=exc.code)


def check_key(api_key: str) -> Dict[str, Any]:
    """Kiểm tra key bằng models.list (không tốn hạn mức sinh nội dung)."""
    try:
        models = list_models(api_key, force=True)
    except LLMError as exc:
        return {"ok": False, "error": exc.message, "code": exc.code}
    text = rank_text_models(models)
    return {"ok": True, "text_models": text[:12], "image_models": pick_models(api_key, kind="image"),
            "video_models": pick_models(api_key, kind="video")}


# ---------------------------------------------------------------------------
# Ảnh và video
# ---------------------------------------------------------------------------

def generate_image(api_key: str, prompt: str, aspect_ratio: str = "1:1") -> Tuple[bytes, str, str]:
    models = pick_models(api_key, kind="image")
    with_config = {"on": True}

    def body_for(_model: str) -> Dict[str, Any]:
        gen: Dict[str, Any] = {"responseModalities": ["TEXT", "IMAGE"]}
        if with_config["on"]:
            gen["imageConfig"] = {"aspectRatio": aspect_ratio}
        return {"contents": [{"role": "user", "parts": [{"text": prompt}]}], "generationConfig": gen}

    try:
        model, payload = _call_with_fallback(api_key, models, body_for)
    except LLMError as exc:
        if exc.code != "bad_request":
            raise
        with_config["on"] = False
        model, payload = _call_with_fallback(api_key, models, body_for)
    _, _, parts = _extract(payload)
    for part in parts:
        inline = part.get("inlineData") or part.get("inline_data")
        if inline and inline.get("data"):
            mime = inline.get("mimeType") or inline.get("mime_type") or "image/png"
            return base64.b64decode(inline["data"]), mime, model
    raise LLMError("Model không trả về ảnh (có thể prompt bị từ chối).", "empty")


def start_video(api_key: str, prompt: str, aspect_ratio: str = "16:9") -> Tuple[str, str]:
    models = pick_models(api_key, kind="video")
    if not models:
        raise LLMError("API key này không có model Veo (video). Tạo video thường cần tài khoản trả phí.", "no_model")
    last: Optional[LLMError] = None
    for model in models:
        try:
            payload = _post(api_key, f"models/{model}:predictLongRunning",
                            {"instances": [{"prompt": prompt}], "parameters": {"aspectRatio": aspect_ratio}}, timeout=60)
            name = payload.get("name", "")
            if not name:
                raise LLMError("Gemini không trả về mã tác vụ video.", "empty")
            return name, model
        except LLMError as exc:
            last = exc
            if not exc.retry_next_model:
                raise
    raise last or LLMError("Không tạo được video.", "error")


def poll_video(api_key: str, operation_name: str) -> Dict[str, Any]:
    """Trả {'done': False} | {'done': True, 'bytes': ..., 'mime': ...} | {'done': True, 'error': ...}."""
    if not re.match(r"^[\w./-]+$", operation_name or ""):
        return {"done": True, "error": "Mã tác vụ không hợp lệ."}
    try:
        resp = requests.get(f"{API_BASE}/{operation_name}", headers=_headers(api_key), timeout=(10, 30))
    except requests.RequestException as exc:
        return {"done": False, "warning": f"Mất kết nối khi kiểm tra: {exc.__class__.__name__}"}
    try:
        _raise_for(resp)
    except LLMError as exc:
        return {"done": True, "error": exc.message}
    op = resp.json()
    if not op.get("done"):
        return {"done": False}
    if op.get("error"):
        return {"done": True, "error": str(op["error"].get("message", "Lỗi tạo video"))[:300]}
    response = op.get("response") or {}
    samples = ((response.get("generateVideoResponse") or {}).get("generatedSamples")
               or response.get("generatedVideos") or [])
    if not samples:
        return {"done": True, "error": "Video bị lọc an toàn hoặc không có kết quả."}
    video = samples[0].get("video") or {}
    if video.get("bytesBase64Encoded"):
        return {"done": True, "bytes": base64.b64decode(video["bytesBase64Encoded"]), "mime": video.get("mimeType", "video/mp4")}
    uri = video.get("uri", "")
    if not uri.startswith("https://generativelanguage.googleapis.com/"):
        return {"done": True, "error": "Địa chỉ tải video không hợp lệ."}
    try:
        dl = requests.get(uri, headers={"x-goog-api-key": api_key}, timeout=(10, 120), allow_redirects=True)
    except requests.RequestException as exc:
        return {"done": False, "warning": f"Chưa tải được video: {exc.__class__.__name__}"}
    if dl.status_code != 200:
        return {"done": True, "error": f"Tải video lỗi HTTP {dl.status_code}."}
    return {"done": True, "bytes": dl.content, "mime": dl.headers.get("Content-Type", "video/mp4")}
