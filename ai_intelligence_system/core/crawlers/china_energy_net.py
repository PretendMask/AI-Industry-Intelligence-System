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
        self.logger.info("[china5e-步骤1] 按日期抓取 {} ~ {}", start_date, end_date)
        self.logger.info("[china5e-步骤2] 请求新闻列表: {}", self.list_url)
        html = await self.fetch_text(client, self.list_url, encoding="utf-8")
        self.logger.info("[china5e-步骤2] 列表页响应: {} 字符", len(html))
        
        self.logger.info("[china5e-步骤3] 解析新闻列表HTML")
        entries = self._parse_news_list(html)
        self.logger.info("[china5e-步骤3] 解析到 {} 条原始条目", len(entries))
        
        self.logger.info("[china5e-步骤4] 按日期范围过滤: {} ~ {}", start_date, end_date)
        filtered = [
            e
            for e in entries
            if in_date_range(e.get("publish_time"), start_date, end_date)
        ]
        self.logger.info("[china5e-步骤4] 日期过滤后 {} 条 (截取前{}条)", len(filtered), self._max_items)
        filtered = filtered[: self._max_items]
        
        if not filtered:
            self.logger.warning("[china5e-步骤4] 日期范围内无新闻条目")
            return []
            
        if self._fetch_detail:
            self.logger.info("[china5e-步骤5] 抓取 {} 条详情页 (并发={})", len(filtered), self._detail_concurrency)
            items = await self.fetch_details_batch(client, filtered)
            self.logger.info("[china5e-步骤5] 详情抓取完成，共 {} 条", len(items))
            return items
            
        self.logger.info("[china5e] 跳过详情抓取，仅返回列表数据")
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
        self.logger.debug("[china5e-详情] 抓取详情页: {}", url)
        raw = await self.fetch_html_raw(client, url)
        self.logger.debug("[china5e-详情] 详情页响应: {} 字符", len(raw))
        
        soup = BeautifulSoup(raw, "html.parser")
        parsed = extract_gov_article(soup)
        body = soup.select_one(".showcontent")
        if body:
            parsed["content"] = body.get_text("\n", strip=True)
            self.logger.debug("[china5e-详情] 使用.showcontent作为正文: {} 字符", len(parsed["content"]))
        self.logger.debug("[china5e-详情] 解析结果: title={} content_len={}", 
                         parsed.get("title", "")[:50], len(parsed.get("content") or ""))
        
        publish_time = parsed.get("publish_time") or entry.get("publish_time")
        content = parsed.get("content") or ""
        if not content:
            self.logger.warning("[china5e-详情] 正文为空: {}", url)
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
        all_links = soup.select("a[href]")
        self.logger.debug("[china5e-解析] 页面共 {} 个链接", len(all_links))
        for a in all_links:
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
        self.logger.debug(r"[china5e-解析] 有效条目: {} (匹配/news/news-\d+-1.html)", len(out))
        return out
