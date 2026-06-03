"""爬虫公共解析工具。"""

from __future__ import annotations

import re
from datetime import date
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

_DATE_PATTERNS = (
    re.compile(r"(\d{4})[年./-](\d{1,2})[月./-](\d{1,2})"),
    re.compile(r"/(\d{4})(\d{2})(\d{2})/"),  # /20260527/
    re.compile(r"/(\d{4})/(\d{1,2})/"),  # /art/2026/
)

_HTML_EXT = re.compile(r"\.(s?html?|htm)$", re.IGNORECASE)


def normalize_publish_time(text: str | None) -> str | None:
    """统一为 YYYY-MM-DD。"""
    if not text:
        return None
    raw = text.replace("发布时间：", "").replace("发布时间:", "").strip()
    for pat in _DATE_PATTERNS:
        m = pat.search(raw)
        if not m:
            continue
        g = m.groups()
        if len(g) == 3 and len(g[0]) == 4 and len(g[1]) == 4 and len(g[2]) == 2:
            # URL style YYYYMMDD in middle group - actually groups are y,m,d from first pattern
            y, mo, d = g
            if len(mo) == 2 and len(d) == 2 and int(mo) <= 12:
                return f"{y}-{int(mo):02d}-{int(d):02d}"
        if len(g) == 3:
            y, mo, d = g[0], g[1], g[2]
            if len(y) == 4 and len(str(mo)) <= 2:
                return f"{y}-{int(mo):02d}-{int(d):02d}"
    return None


def parse_date_from_url(url: str) -> str | None:
    """从 URL 路径提取 YYYYMMDD（如 /20260527/）。"""
    m = re.search(r"/(\d{4})(\d{2})(\d{2})/", url)
    if m:
        y, mo, d = m.groups()
        return f"{y}-{mo}-{d}"
    return None


def to_date(publish_time: str | None) -> date | None:
    if not publish_time:
        return None
    try:
        return date.fromisoformat(publish_time[:10])
    except ValueError:
        return None


def in_date_range(publish_time: str | None, start: date, end: date) -> bool:
    d = to_date(publish_time)
    if d is None:
        return False
    return start <= d <= end


def is_article_href(href: str) -> bool:
    if not href or href.startswith(("javascript:", "mailto:", "#")):
        return False
    return bool(_HTML_EXT.search(href))


def extract_gov_article(soup: BeautifulSoup) -> dict[str, Any]:
    title_el = soup.select_one("h1, h2, .xxgk_title, .article-title")
    title = (title_el.get_text(strip=True) if title_el else "").strip()
    if not title and soup.find("title"):
        title = soup.find("title").get_text(strip=True).split("-")[0].strip()

    body_el = soup.select_one(
        ".TRS_Editor, #zoom, .ccontent, .showcontent, .article-content, "
        "div.main-colum, .content"
    )
    if not body_el or len(body_el.get_text(strip=True)) < 80:
        body_el = soup.select_one("div.article")
    content = body_el.get_text("\n", strip=True) if body_el else ""

    publish_time = None
    for el in soup.select(
        ".pages-date, .time, .date, .source-time, span.time, .article-time"
    ):
        publish_time = normalize_publish_time(el.get_text())
        if publish_time:
            break

    return {"title": title, "content": content, "publish_time": publish_time}


def same_domain(url: str, domain: str) -> bool:
    host = urlparse(url).netloc.lower()
    return domain.lower() in host
