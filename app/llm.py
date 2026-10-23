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
import random
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

DEFAULT_TEXT_MODELS = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.0-flash-lite", "gemini-1.5-pro"]
_EXCLUDE_TEXT = ("image", "tts", "audio", "live", "embedding", "robotics", "computer-use", "learnlm",
                 "gemma", "aqa", "veo", "imagen", "lyria", "omni", "thinking-exp")


class LLMError(Exception):
    def __init__(self, message: str, code: str = "error", retry_next_model: bool = False, *,
                 retry_after: Optional[float] = None, quota_kind: str = "", short: str = ""):
        super().__init__(message)
        self.message = message
        self.code = code
        self.retry_next_model = retry_next_model
        self.retry_after = retry_after   # giây Gemini đề nghị chờ (RetryInfo)
        self.quota_kind = quota_kind     # minute | day | zero | unknown (chỉ với lỗi 429)
        self.short = short or message    # mô tả ngắn để gộp lỗi nhiều model


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
    detail = f" Gemini báo: {message}" if message else ""
    if resp.status_code in (401, 403):
        raise LLMError("API key không có quyền dùng Gemini API (kiểm tra giới hạn của key, dự án Google Cloud hoặc billing)." + detail,
                       "forbidden")
    if resp.status_code == 404:
        raise LLMError(f"Model không tồn tại hoặc không còn hỗ trợ.{detail}", "model_not_found", retry_next_model=True)
    if resp.status_code == 429:
        kind, retry_after = _quota_details(err)
        short = {"minute": "vượt giới hạn số lượt/phút", "day": "hết hạn mức trong ngày",
                 "zero": "key không có hạn mức cho model này (thường cần bật billing)"}.get(kind, "bị giới hạn tốc độ (429)")
        if "search" in low or "grounding" in low:
            short += " của tìm kiếm Google"
        raise LLMError(f"Gemini báo {short}.{detail}", "quota", retry_next_model=True,
                       retry_after=retry_after, quota_kind=kind, short=short)
    if resp.status_code >= 500:
        short = "đang quá tải (503)" if resp.status_code == 503 else f"lỗi máy chủ (HTTP {resp.status_code})"
        raise LLMError(f"Máy chủ Gemini {short}, thường tự hết sau ít phút.{detail}", "server", retry_next_model=True,
                       short=short)
    if resp.status_code == 400 and status == "FAILED_PRECONDITION":
        raise LLMError("Gemini từ chối yêu cầu (thường do vùng/billing của dự án)." + detail, "forbidden")
    raise LLMError(f"Yêu cầu bị từ chối (HTTP {resp.status_code}).{detail}", "bad_request", retry_next_model=True, short=f"lỗi tham số (400)")


def _quota_details(err: Dict[str, Any]) -> Tuple[str, Optional[float]]:
    """Đọc QuotaFailure/RetryInfo trong lỗi 429 để biết là giới hạn theo phút, theo ngày hay hạn mức 0."""
    retry_after: Optional[float] = None
    ids: List[str] = []
    for d in err.get("details") or []:
        if not isinstance(d, dict):
            continue
        typ = str(d.get("@type", ""))
        if typ.endswith("RetryInfo"):
            m = re.match(r"^\s*([\d.]+)s\s*$", str(d.get("retryDelay", "")))
            if m:
                retry_after = float(m.group(1))
        elif typ.endswith("QuotaFailure"):
            for v in d.get("violations") or []:
                ids.append(f"{v.get('quotaId', '')} {v.get('quotaMetric', '')}".lower())
    text = " ".join(ids) + " " + str(err.get("message", "")).lower()
    if "limit: 0" in text or "limit:0" in text:
        return "zero", retry_after
    if "perday" in text or "per_day" in text or "per day" in text:
        return "day", retry_after
    if "perminute" in text or "per_minute" in text or "per minute" in text or retry_after is not None:
        return "minute", retry_after
    return "unknown", retry_after


SERVER_RETRIES = 2          # lỗi 5xx (thường 503 quá tải): thử lại cùng model
MAX_QUOTA_WAIT = 30.0       # chỉ chờ khi Gemini đề nghị chờ ngắn (giới hạn theo phút)
_sleep = time.sleep         # tách ra để test không phải chờ thật


def _post(api_key: str, path: str, body: Dict[str, Any], timeout: float = 240) -> Dict[str, Any]:
    """Gọi API; tự thử lại khi Gemini quá tải (5xx) hoặc vượt giới hạn/phút có đề nghị thời gian chờ."""
    server_tries = quota_tries = 0
    while True:
        try:
            resp = requests.post(f"{API_BASE}/{path}", headers=_headers(api_key), json=body, timeout=(10, timeout))
        except requests.RequestException as exc:
            raise LLMError(f"Không kết nối được Gemini API: {exc.__class__.__name__}", "network", retry_next_model=True,
                           short="mất kết nối") from exc
        try:
            _raise_for(resp)
            return resp.json()
        except LLMError as exc:
            if exc.code == "server" and server_tries < SERVER_RETRIES:
                server_tries += 1
                wait = 2.0 * server_tries + random.random()
                log.info("Gemini %s on %s, retry in %.1fs", exc.short, path, wait)
                _sleep(wait)
                continue
            if (exc.code == "quota" and quota_tries < 1 and exc.quota_kind in ("minute", "unknown")
                    and exc.retry_after is not None and exc.retry_after <= MAX_QUOTA_WAIT):
                quota_tries += 1
                log.info("Gemini rate limit on %s, waiting %.1fs", path, exc.retry_after)
                _sleep(exc.retry_after + 0.5)
                continue
            raise


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


def output_limit(api_key: str, model: str, default: int = 8192) -> int:
    """Giới hạn token đầu ra của model theo models.list (đã lưu đệm). Không có thông tin thì dùng mức an toàn."""
    with _cache_lock:
        cached = _model_cache.get(_key_id(api_key))
    for m in (cached[1] if cached else []):
        if _short(m.get("name", "")) == model:
            try:
                return int(m.get("outputTokenLimit") or default)
            except (TypeError, ValueError):
                return default
    return default


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
        # Ưu tiên các model có hạn mức miễn phí dồi dào và ổn định nhất (2.0-flash, 1.5-flash) lên đầu
        if "2.0-flash" in name and "lite" not in name:
            ga_priority = 4
        elif "1.5-flash" in name and "8b" not in name:
            ga_priority = 3
        elif "2.0-flash-lite" in name or "1.5-flash-8b" in name:
            ga_priority = 2
        elif "1.5-pro" in name or "2.0-pro" in name:
            ga_priority = 1
        else:
            ga_priority = 0
        if "flash-lite" in name:
            family = 2
        elif "flash" in name:
            family = 3
        elif "pro" in name:
            family = 1
        else:
            family = 0
        return (ga_priority, stable, alias, family, _version(name))

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
        return ranked[:10]
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
    if not text.strip():
        all_text = "".join(p.get("text", "") for p in parts)
        if all_text.strip() and ("{" in all_text or "[" in all_text):
            text = all_text
    if not text.strip() and finish == "MAX_TOKENS":
        raise LLMError("Model dùng hết giới hạn token trước khi trả kết quả.", "truncated", retry_next_model=True, short="hết giới hạn token")
    return text, cand.get("groundingMetadata") or {}, parts


def _finish_reason(payload: Dict[str, Any]) -> str:
    cands = payload.get("candidates") or []
    return str(cands[0].get("finishReason", "")) if cands else ""


def _grounding(meta: Dict[str, Any]) -> Tuple[List[Dict[str, str]], List[str]]:
    sources, seen = [], set()
    for chunk in meta.get("groundingChunks") or []:
        web = chunk.get("web") or {}
        uri = web.get("uri", "")
        if uri and uri not in seen:
            seen.add(uri)
            sources.append({"title": web.get("title") or web.get("domain") or uri, "url": uri})
    return sources, list(meta.get("webSearchQueries") or [])


FALLBACK_BUDGET = 200.0     # giây tối đa cho việc thử lần lượt các model


def _call_with_fallback(api_key: str, models: List[str], body_for: Any) -> Tuple[str, Dict[str, Any]]:
    """Thử lần lượt các model; nếu tất cả đều lỗi, báo lý do của TỪNG model để biết chính xác vì sao."""
    failures: List[Tuple[str, LLMError]] = []
    started = time.time()
    for model in models:
        if failures and time.time() - started > FALLBACK_BUDGET:
            break
        try:
            payload = _post(api_key, f"models/{model}:generateContent", body_for(model))
            _extract(payload)
            return model, payload
        except LLMError as exc:
            if not exc.retry_next_model:
                raise
            failures.append((model, exc))
            log.warning("model %s failed (%s: %s), trying next", model, exc.code, exc.short)
    if not failures:
        raise LLMError("Không có model nào khả dụng.", "no_model")
    if len(failures) == 1:
        raise failures[0][1]
    codes = {e.code for _, e in failures}
    code = codes.pop() if len(codes) == 1 else "unavailable"
    summary = "; ".join(f"{m}: {e.short}" for m, e in failures)
    hint = {"quota": " Kiểm tra hạn mức tại aistudio.google.com/usage hoặc chọn model khác trong Cài đặt.",
            "server": " Gemini đang quá tải, thử lại sau vài phút."}.get(code, "")
    raise LLMError(f"Đã thử {len(failures)} model nhưng đều lỗi — {summary}.{hint}", code)


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


def _num_from_text(value: str) -> Optional[float]:
    s = value.strip().replace(" ", "").replace("%", "").replace("đ", "").replace("VND", "").replace("vnd", "")
    if re.fullmatch(r"-?\d{1,3}([.,]\d{3})+", s):
        s = re.sub(r"[.,]", "", s)
    s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def coerce_to_schema(data: Any, schema: Optional[Dict[str, Any]]) -> Any:
    """Sửa các lệch nhỏ hay gặp khi model không bị ép schema: enum khác hoa/thường, số viết dạng chữ,
    số nguyên dạng 3.0, chuỗi đơn thay cho mảng, mảng dài quá maxItems, thiếu mảng bắt buộc.
    Không bịa nội dung: chỉ đổi kiểu/định dạng, thiếu trường văn bản vẫn bị báo lỗi."""
    if not isinstance(schema, dict):
        return data
    t = schema.get("type")
    if "enum" in schema and isinstance(data, str) and data not in schema["enum"]:
        low = data.strip().lower()
        for opt in schema["enum"]:
            if isinstance(opt, str) and opt.strip().lower() == low:
                return opt
        return data
    if t in ("number", "integer"):
        if isinstance(data, str):
            num = _num_from_text(data)
            if num is not None:
                data = num
        if t == "integer" and isinstance(data, float) and data.is_integer():
            return int(data)
        return data
    if t == "string" and isinstance(data, (int, float)) and not isinstance(data, bool):
        return str(data)
    if t == "array":
        if isinstance(data, (str, dict)) and data != "":
            data = [data]
        if not isinstance(data, list):
            return data
        items = [coerce_to_schema(x, schema.get("items")) for x in data]
        if isinstance(schema.get("maxItems"), int):
            items = items[: schema["maxItems"]]
        return items
    if t == "object" and isinstance(data, dict):
        props = schema.get("properties") or {}
        out = {k: coerce_to_schema(v, props.get(k)) for k, v in data.items()}
        for key in schema.get("required") or []:
            if key not in out and (props.get(key) or {}).get("type") == "array":
                out[key] = []
        return out
    return data


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
                  preferred_model: str = "", temperature: float = 0.5, max_output_tokens: int = 32768) -> LLMResult:
    """Sinh JSON đúng schema. Trả LLMResult(ok=False) kèm lý do nếu không được."""
    try:
        models = pick_models(api_key, preferred_model, "text")
    except LLMError as exc:
        return LLMResult(ok=False, error=exc.message, error_code=exc.code)

    schema_text = json.dumps(schema, ensure_ascii=False)
    full_prompt = (f"{prompt}\n\nĐỊNH DẠNG BẮT BUỘC: trả về DUY NHẤT một đối tượng JSON hợp lệ theo JSON Schema sau, "
                   f"không kèm giải thích:\n{schema_text}")
    use_schema_field = {"on": True}
    use_thinking = {"on": True}

    def body_for(_model: str) -> Dict[str, Any]:
        gen: Dict[str, Any] = {"temperature": temperature,
                               "maxOutputTokens": min(max_output_tokens, output_limit(api_key, _model)),
                               "responseMimeType": "application/json"}
        if use_schema_field["on"]:
            gen["responseJsonSchema"] = schema
        if use_thinking["on"] and ("2.5" in _model or "thinking" in _model):
            gen["thinkingConfig"] = {"thinkingBudget": 0}
        return {"systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": full_prompt}]}],
                "generationConfig": gen}

    try:
        try:
            model, payload = _call_with_fallback(api_key, models, body_for)
        except LLMError as exc:
            if exc.code == "bad_request" and (use_schema_field["on"] or use_thinking["on"]):
                use_schema_field["on"] = False
                use_thinking["on"] = False
                model, payload = _call_with_fallback(api_key, models, body_for)
            else:
                raise
        text, _, _ = _extract(payload)
        truncated = _finish_reason(payload) == "MAX_TOKENS"
        try:
            data = coerce_to_schema(parse_json_text(text), schema)
            errors = _schema_errors(data, schema)
        except ValueError as exc:
            data, errors = None, [str(exc)]
        if errors and truncated:
            log.warning("generate_json truncated output model=%s chars=%s", model, len(text))
            return LLMResult(ok=False, model=model, text=text, error_code="truncated",
                             error="Kết quả quá dài nên bị Gemini cắt giữa chừng. Thử rút gọn yêu cầu (ít ngày/ít kênh hơn) "
                                   "hoặc chọn model khác trong Cài đặt.")
        if errors:
            log.info("generate_json repair model=%s errors=%s", model, errors[:3])
            repair = (f"Kết quả JSON trước đó chưa đúng schema. Lỗi: {errors}\n\nKết quả trước:\n{text[:12000]}\n\n"
                      f"Hãy trả lại JSON đã sửa, giữ nguyên nội dung đúng, theo schema:\n{schema_text}")
            repair_gen: Dict[str, Any] = {"temperature": 0.1, "maxOutputTokens": min(max_output_tokens, output_limit(api_key, model)),
                                         "responseMimeType": "application/json"}
            if "2.5" in model or "thinking" in model:
                repair_gen["thinkingConfig"] = {"thinkingBudget": 0}
            payload = _post(api_key, f"models/{model}:generateContent", {
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": repair}]}],
                "generationConfig": repair_gen,
            })
            text, _, _ = _extract(payload)
            data = coerce_to_schema(parse_json_text(text), schema)
            errors = _schema_errors(data, schema)
            if errors:
                return LLMResult(ok=False, model=model, text=text, error="AI trả về dữ liệu sai cấu trúc: " + "; ".join(errors[:3]),
                                 error_code="invalid_output")
        return LLMResult(ok=True, data=data, text=text, model=model)
    except LLMError as exc:
        log.warning("generate_json failed code=%s msg=%s", exc.code, exc.message)
        return LLMResult(ok=False, error=exc.message, error_code=exc.code)
    except ValueError as exc:
        log.warning("generate_json unreadable JSON: %s", exc)
        return LLMResult(ok=False, error=f"Không đọc được JSON từ AI: {exc}", error_code="invalid_output")


def generate_grounded(api_key: str, *, system: str, prompt: str, preferred_model: str = "",
                      temperature: float = 0.3) -> LLMResult:
    """Sinh văn bản có tìm kiếm Google (grounding). Trả kèm danh sách nguồn thật từ groundingMetadata."""
    try:
        models = pick_models(api_key, preferred_model, "text")
    except LLMError as exc:
        return LLMResult(ok=False, error=exc.message, error_code=exc.code)

    def body_for(_model: str) -> Dict[str, Any]:
        tool = {"google_search": {}} if _version(_model) >= 2.0 or not _version(_model) else {"google_search_retrieval": {"dynamic_retrieval_config": {"mode": "MODE_DYNAMIC"}}}
        gen: Dict[str, Any] = {"temperature": temperature, "maxOutputTokens": min(12288, output_limit(api_key, _model))}
        if "2.5" in _model or "thinking" in _model:
            gen["thinkingConfig"] = {"thinkingBudget": 0}
        return {"systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "tools": [tool],
                "generationConfig": gen}

    try:
        model, payload = _call_with_fallback(api_key, models, body_for)
        text, meta, _ = _extract(payload)
        sources, queries = _grounding(meta)
        return LLMResult(ok=True, text=text, model=model, grounded=bool(sources), sources=sources, search_queries=queries)
    except LLMError as exc:
        log.warning("generate_grounded failed code=%s msg=%s", exc.code, exc.message)
        return LLMResult(ok=False, error=exc.message, error_code=exc.code)


def check_key(api_key: str, *, generate_test: bool = False, preferred_model: str = "") -> Dict[str, Any]:
    """Kiểm tra key bằng models.list; generate_test=True thử thêm một lần sinh nội dung rất nhỏ."""
    try:
        models = list_models(api_key, force=True)
    except LLMError as exc:
        return {"ok": False, "error": exc.message, "code": exc.code}
    text = rank_text_models(models)
    out: Dict[str, Any] = {"ok": True, "text_models": text[:12], "image_models": pick_models(api_key, kind="image"),
                           "video_models": pick_models(api_key, kind="video")}
    if generate_test:
        # Thử sinh một JSON rất nhỏ theo schema: phát hiện lỗi billing/vùng/quota mà models.list không lộ ra
        res = generate_json(api_key, system="Bạn là trợ lý kiểm tra kết nối.", prompt="Trả về ok = true.",
                            schema={"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"]},
                            preferred_model=preferred_model, temperature=0, max_output_tokens=2048)
        out["generate"] = {"ok": res.ok, "model": res.model, "error": res.error, "error_code": res.error_code}
    return out


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

    gemini_exc: Optional[LLMError] = None
    if models:
        try:
            try:
                model, payload = _call_with_fallback(api_key, models, body_for)
            except LLMError as exc:
                if exc.code == "bad_request":
                    with_config["on"] = False
                    model, payload = _call_with_fallback(api_key, models, body_for)
                else:
                    raise
            _, _, parts = _extract(payload)
            for part in parts:
                inline = part.get("inlineData") or part.get("inline_data")
                if inline and inline.get("data"):
                    mime = inline.get("mimeType") or inline.get("mime_type") or "image/png"
                    return base64.b64decode(inline["data"]), mime, model
        except LLMError as exc:
            gemini_exc = exc
            log.warning("Gemini image failed (%s: %s), trying fallback", exc.code, exc.message)
    else:
        gemini_exc = LLMError("API key không có model ảnh.", "no_model")

    # Dự phòng qua engine tạo ảnh AI mở Pollinations (Flux / SDXL) khi Gemini image không có hạn mức (limit: 0) hoặc chưa bật billing
    try:
        import urllib.parse
        ratio_dims = {
            "1:1": (1024, 1024), "4:5": (896, 1120), "9:16": (768, 1344),
            "16:9": (1344, 768), "3:4": (864, 1152), "4:3": (1152, 864)
        }
        w, h = ratio_dims.get(aspect_ratio, (1024, 1024))
        p_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width={w}&height={h}&nologo=true"
        resp = requests.get(p_url, timeout=(10, 45))
        if resp.status_code == 200 and resp.content and resp.content[:4] in (b"\x89PNG", b"\xff\xd8\xff\xe0", b"\xff\xd8\xff\xe1", b"RIFF"):
            ctype = resp.headers.get("Content-Type", "image/jpeg").split(";")[0]
            return resp.content, ctype, "pollinations-ai"
    except Exception as e_poll:
        log.warning("Fallback image generation error: %s", e_poll)

    raise gemini_exc or LLMError("Không thể tạo ảnh.", "error")


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
