"""国家发改委（NDRC）新闻爬虫。"""

from __future__ import annotations

from datetime import date
from typing import Any

import httpx
from bs4 import BeautifulSoup

from ai_intelligence_system.core.base_crawler import BaseCrawler, CrawlerError, NewsItem
from ai_intelligence_system.core.crawler_factory import register
from ai_intelligence_system.core.crawlers._parse_utils import (
    extract_gov_article,
    in_date_range,
    is_article_href,
    normalize_publish_time,
    parse_date_from_url,
)

_LIST_URL = "https://www.ndrc.gov.cn/xwdt/index.html"


@register("ndrc")
class NdrcCrawler(BaseCrawler):
    source_id = "ndrc"
    source_name = "国家发改委"
    base_url = "https://www.ndrc.gov.cn/xwdt/"
    list_url = _LIST_URL

    async def fetch_by_date(
        self,
        client: httpx.AsyncClient,
        start_date: date,
        end_date: date,
    ) -> list[NewsItem]:
        self.logger.info("按日期抓取 {} ~ {}", start_date, end_date)
        html = await self.fetch_text(client, self.list_url, encoding="utf-8")
        entries = self._parse_list(html)
        filtered = [
            e
            for e in entries
            if in_date_range(e.get("publish_time"), start_date, end_date)
        ][: self._max_items]
        if not filtered:
            self.logger.warning("日期范围内无新闻条目")
            return []
        if self._fetch_detail:
            return await self.fetch_details_batch(client, filtered)
        return [
            self.make_item(
                title=e["title"],
                url=e["url"],
                publish_time=e.get("publish_time"),
                list_url=self.list_url,
            )
            for e in filtered
        ]

    async def fetch_article_item(
        self,
        client: httpx.AsyncClient,
        entry: dict[str, Any],
    ) -> NewsItem:
        url = entry["url"]
        raw = await self.fetch_html_raw(client, url)
        soup = BeautifulSoup(raw, "html.parser")
        parsed = extract_gov_article(soup)
        publish_time = parsed.get("publish_time") or entry.get("publish_time")
        if not publish_time:
            publish_time = parse_date_from_url(url)
        content = parsed.get("content") or ""
        if not content:
            raise CrawlerError(f"正文为空: {url}")
        return self.make_item(
            title=parsed.get("title") or entry["title"],
            url=url,
            publish_time=publish_time,
            content=content,
            raw_html=raw,
            list_url=self.list_url,
        )

    def _parse_list(self, html: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        seen: set[str] = set()
        out: list[dict[str, Any]] = []
        for a in soup.select("a[href]"):
            href = (a.get("href") or "").strip()
            title = (a.get_text() or "").strip()
            if not title or len(title) < 6 or not is_article_href(href):
                continue
            url = self.resolve_url(href, page_url=self.list_url)
            if url in seen:
                continue
            seen.add(url)
            pt = normalize_publish_time(a.parent.get_text(" ", strip=True) if a.parent else "")
            if not pt:
                pt = parse_date_from_url(url)
            out.append({"title": title, "url": url, "publish_time": pt})
        return out
