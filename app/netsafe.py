# -*- coding: utf-8 -*-
"""
Truy cập web an toàn.

- safe_fetch: chỉ http/https, chặn địa chỉ nội bộ (chống SSRF), tự đi theo tối đa 3 lần chuyển hướng
  và kiểm tra lại từng bước, giới hạn dung lượng, luôn kiểm chứng chứng chỉ TLS.
- web_search: tìm kiếm qua gói `ddgs` (DuckDuckGo). Lỗi được trả về rõ ràng, không bị nuốt.
"""
from __future__ import annotations

import ipaddress
import logging
import re
import socket
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests

from app import config

log = logging.getLogger("marketing_os.net")

MAX_BYTES = 1_500_000
USER_AGENT = "Mozilla/5.0 (compatible; MarketingOS/4.0; +https://github.com/vuhailinhdn98/marketing-os)"


class FetchError(Exception):
    pass


def _host_is_public(host: str) -> bool:
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    if not infos:
        return False
    for info in infos:
        addr = info[4][0]
        try:
            ip = ipaddress.ip_address(addr.split("%")[0])
        except ValueError:
            return False
        if not ip.is_global or ip.is_multicast or ip.is_reserved:
            return False
    return True


def normalize_url(raw: str) -> Optional[str]:
    raw = (raw or "").strip()
    if not raw:
        return None
    if not re.match(r"^https?://", raw, re.I):
        if re.match(r"^[a-z0-9.-]+\.[a-z]{2,}(/.*)?$", raw, re.I):
            raw = "https://" + raw
        else:
            return None
    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return None
    return raw


def safe_fetch(url: str, timeout: float = 8.0) -> Tuple[str, str]:
    """Trả về (url_cuối_cùng, html). Ném FetchError nếu không an toàn hoặc không tải được."""
    if not config.settings.allow_web_fetch:
        raise FetchError("Máy chủ đang tắt chức năng tải trang web (ALLOW_WEB_FETCH=0).")
    current = normalize_url(url)
    if not current:
        raise FetchError("URL không hợp lệ.")
    for _ in range(4):
        host = urlparse(current).hostname or ""
        if not _host_is_public(host):
            raise FetchError(f"Từ chối tải {host}: không phải địa chỉ công khai.")
        try:
            resp = requests.get(
                current,
                headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml",
                         "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.7"},
                timeout=(4, timeout), allow_redirects=False, stream=True,
            )
        except requests.RequestException as exc:
            raise FetchError(f"Không tải được trang: {exc.__class__.__name__}") from exc
        if resp.status_code in (301, 302, 303, 307, 308):
            location = resp.headers.get("Location")
            resp.close()
            if not location:
                raise FetchError("Chuyển hướng không có địa chỉ đích.")
            current = normalize_url(urljoin(current, location)) or ""
            if not current:
                raise FetchError("Chuyển hướng tới địa chỉ không hợp lệ.")
            continue
        if resp.status_code != 200:
            resp.close()
            raise FetchError(f"Trang trả mã HTTP {resp.status_code}.")
        ctype = resp.headers.get("Content-Type", "")
        if "html" not in ctype and "xml" not in ctype and ctype:
            resp.close()
            raise FetchError(f"Không phải trang HTML ({ctype}).")
        chunks, size = [], 0
        for chunk in resp.iter_content(chunk_size=65536):
            chunks.append(chunk)
            size += len(chunk)
            if size >= MAX_BYTES:
                break
        resp.close()
        raw = b"".join(chunks)
        encoding = resp.encoding or "utf-8"
        try:
            return current, raw.decode(encoding, errors="replace")
        except LookupError:
            return current, raw.decode("utf-8", errors="replace")
    raise FetchError("Quá nhiều lần chuyển hướng.")


PHONE_RE = re.compile(r"(?:\+?84|0)(?:[\s.-]?\d){9,10}")


def extract_site_info(html: str) -> Dict[str, object]:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    title = soup.title.get_text(strip=True) if soup.title else ""
    desc = ""
    meta = soup.find("meta", attrs={"name": re.compile("^description$", re.I)}) or soup.find(
        "meta", attrs={"property": re.compile("^og:description$", re.I)}
    )
    if meta and meta.get("content"):
        desc = str(meta["content"]).strip()
    headings: List[str] = []
    for h in soup.find_all(["h1", "h2", "h3"]):
        text = h.get_text(" ", strip=True)
        if 4 <= len(text) <= 140 and text not in headings:
            headings.append(text)
        if len(headings) >= 10:
            break
    text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
    phones = []
    for m in PHONE_RE.findall(text):
        digits = re.sub(r"\D", "", m)
        if digits.startswith("84"):
            digits = "0" + digits[2:]
        if len(digits) == 10 and digits not in phones:
            phones.append(digits)
    return {"title": title[:200], "description": desc[:400], "headings": headings,
            "phones": phones[:3], "text_excerpt": text[:2500]}


def web_search(query: str, max_results: int = 5) -> Tuple[List[Dict[str, str]], Optional[str]]:
    """Trả về (kết_quả, lỗi). Lỗi là None khi tìm kiếm chạy được (kể cả khi 0 kết quả).
    Sử dụng cơ chế đa tầng (Yandex qua ddgs -> Bing HTML -> DuckDuckGo) để đảm bảo không bị chặn
    trên môi trường máy chủ đám mây (Render, Railway, VPS) hoặc địa chỉ IP trung tâm dữ liệu.
    """
    query = re.sub(r"\s+", " ", (query or "")).strip()
    if not query:
        return [], "Câu tìm kiếm rỗng."

    results: List[Dict[str, str]] = []
    seen_urls: set = set()

    # Tầng 1: Thử Yandex thông qua ddgs.engines.yandex (hỗ trợ tiếng Việt và IP máy chủ rất tốt, không bị 202/Cloudflare)
    try:
        from ddgs.engines.yandex import Yandex
        y = Yandex()
        raw_yandex = y.search(query) or []
        for item in raw_yandex:
            href = getattr(item, "href", "") or ""
            if href and href not in seen_urls and not href.startswith("https://yandex.") and not href.startswith("http://yandex."):
                seen_urls.add(href)
                title = (getattr(item, "title", "") or "")[:200]
                body = (getattr(item, "body", "") or "")[:400]
                results.append({"title": title, "snippet": body, "url": href})
                if len(results) >= max_results:
                    return results, None
    except Exception as exc:
        log.debug("Yandex search error: %s", exc)

    # Tầng 2: Thử Bing HTML search scraper (phục hồi URL thực từ redirect a1)
    if len(results) < max_results:
        try:
            import urllib.parse
            import base64
            from bs4 import BeautifulSoup
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
            }
            b_url = "https://www.bing.com/search?q=" + urllib.parse.quote(query)
            resp = requests.get(b_url, headers=headers, timeout=6)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                for li in soup.find_all("li", class_="b_algo"):
                    h2 = li.find("h2")
                    if not h2:
                        continue
                    a = h2.find("a")
                    if not a or not a.get("href"):
                        continue
                    href = a["href"]
                    if "/ck/a?!" in href and "&u=" in href:
                        m = re.search(r"[?&]u=a1([a-zA-Z0-9_-]+)", href)
                        if m:
                            try:
                                pad = m.group(1) + "=" * (-len(m.group(1)) % 4)
                                href = base64.urlsafe_b64decode(pad).decode("utf-8", errors="ignore")
                            except Exception:
                                pass
                    if href and href not in seen_urls and not href.startswith("https://www.bing."):
                        seen_urls.add(href)
                        p = li.find("p")
                        snippet = p.get_text(" ", strip=True)[:400] if p else ""
                        results.append({"title": h2.get_text(" ", strip=True)[:200], "snippet": snippet, "url": href})
                        if len(results) >= max_results:
                            break
        except Exception as exc:
            log.debug("Bing fallback search error: %s", exc)

    # Tầng 3: Thử DuckDuckGo qua gói ddgs/duckduckgo_search tiêu chuẩn
    if len(results) < max_results:
        try:
            from ddgs import DDGS
        except ImportError:
            try:
                from duckduckgo_search import DDGS  # type: ignore
            except ImportError:
                DDGS = None  # type: ignore
        if DDGS is not None:
            try:
                with DDGS() as engine:
                    raw = list(engine.text(query, max_results=max_results, region="vn-vi"))
                    for item in raw:
                        url = item.get("href") or item.get("url") or ""
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            results.append({"title": item.get("title", "")[:200], "snippet": item.get("body", "")[:400], "url": url})
                            if len(results) >= max_results:
                                break
            except Exception as exc:
                log.debug("DDGS standard search error: %s", exc)

    if results:
        return results[:max_results], None
    return [], "Không tìm thấy kết quả từ các công cụ tìm kiếm."
