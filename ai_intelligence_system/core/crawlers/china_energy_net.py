"""中国能源网（china5e.com）新闻爬虫。"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

import httpx
from bs4 import BeautifulSoup

from ai_intelligence_system.core.base_crawler import BaseCrawler, CrawlerError, NewsItem
from ai_intelligence_system.core.crawler_factory import register
from ai_intelligence_system.core.crawlers._parse_utils import (
    extract_gov_article,
    in_date_range,
    normalize_publish_time,
)

_LIST_URL = "https://www.china5e.com/news/"
_NEWS_HREF = re.compile(r"/news/news-\d+-1\.html", re.I)


@register("china5e")
class China5eCrawler(BaseCrawler):
    source_id = "china5e"
    source_name = "中国能源网"
    base_url = "https://www.china5e.com/"
    list_url = _LIST_URL

    async def fetch_by_date(
        self,
        client: httpx.AsyncClient,
        start_date: date,
        end_date: date,
    ) -> list[NewsItem]:
        self.logger.info("按日期抓取 china5e {} ~ {}", start_date, end_date)
        html = await self.fetch_text(client, self.list_url, encoding="utf-8")
        entries = self._parse_news_list(html)
        filtered = [
            e
            for e in entries
            if in_date_range(e.get("publish_time"), start_date, end_date)
        ][: self._max_items]
        if not filtered:
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
        body = soup.select_one(".showcontent")
        if body:
            parsed["content"] = body.get_text("\n", strip=True)
        publish_time = parsed.get("publish_time") or entry.get("publish_time")
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

    def _parse_news_list(self, html: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        seen: set[str] = set()
        out: list[dict[str, Any]] = []
        for a in soup.select("a[href]"):
            href = (a.get("href") or "").strip()
            if not _NEWS_HREF.search(href):
                continue
            title = (a.get_text() or "").strip()
            if not title or len(title) < 4:
                continue
            url = self.resolve_url(href, page_url=self.list_url)
            if url in seen:
                continue
            seen.add(url)
            parent_text = a.parent.get_text(" ", strip=True) if a.parent else ""
            pt = normalize_publish_time(parent_text)
            out.append({"title": title, "url": url, "publish_time": pt})
        return out
