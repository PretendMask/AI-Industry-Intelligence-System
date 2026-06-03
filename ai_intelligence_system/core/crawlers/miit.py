"""工业和信息化部（MIIT）新闻爬虫。"""

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

_LIST_URLS = (
    "https://www.miit.gov.cn/xwfb/index.html",
    "https://www.miit.gov.cn/zwgk/index.html",
)


@register("miit")
class MiitCrawler(BaseCrawler):
    source_id = "miit"
    source_name = "工业和信息化部"
    base_url = "https://www.miit.gov.cn/"
    list_urls = _LIST_URLS

    async def fetch_by_date(
        self,
        client: httpx.AsyncClient,
        start_date: date,
        end_date: date,
    ) -> list[NewsItem]:
        self.logger.info("按日期抓取 MIIT {} ~ {}", start_date, end_date)
        all_entries: list[dict[str, Any]] = []
        seen: set[str] = set()
        for list_url in self.list_urls:
            try:
                html = await self.fetch_text(client, list_url, encoding="utf-8")
                for e in self._parse_list(html, list_url):
                    if e["url"] not in seen:
                        seen.add(e["url"])
                        all_entries.append(e)
            except CrawlerError as exc:
                self.logger.warning("列表页失败 {}: {}", list_url, exc)

        candidates = all_entries[: self._max_items * 3]
        if not candidates:
            return []
        if self._fetch_detail:
            items = await self.fetch_details_batch(client, candidates)
            return self.trim_items(
                [
                    i
                    for i in items
                    if in_date_range(i.publish_time, start_date, end_date)
                ]
            )
        filtered = [
            e
            for e in candidates
            if in_date_range(e.get("publish_time"), start_date, end_date)
        ][: self._max_items]
        return [
            self.make_item(
                title=e["title"],
                url=e["url"],
                publish_time=e.get("publish_time"),
                list_url=e.get("list_url"),
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
            list_url=entry.get("list_url"),
        )

    def _parse_list(self, html: str, list_url: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        out: list[dict[str, Any]] = []
        for a in soup.select('a[href*="/art/"]'):
            href = (a.get("href") or "").strip()
            title = (a.get_text() or "").strip()
            if not title or len(title) < 6 or not is_article_href(href):
                continue
            url = self.resolve_url(href, page_url=list_url)
            pt = normalize_publish_time(a.parent.get_text(" ", strip=True) if a.parent else "")
            if not pt:
                pt = parse_date_from_url(url)
            out.append(
                {"title": title, "url": url, "publish_time": pt, "list_url": list_url}
            )
        return out
