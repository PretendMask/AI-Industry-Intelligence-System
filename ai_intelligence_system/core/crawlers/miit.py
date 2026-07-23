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
        self.logger.info("[MIIT-步骤1] 按日期抓取 {} ~ {}", start_date, end_date)
        all_entries: list[dict[str, Any]] = []
        seen: set[str] = set()
        self.logger.info("[MIIT-步骤2] 请求 {} 个列表页", len(self.list_urls))
        for list_url in self.list_urls:
            try:
                self.logger.info("[MIIT-步骤2] 请求列表页: {}", list_url)
                html = await self.fetch_text(client, list_url, encoding="utf-8")
                self.logger.info("[MIIT-步骤2] 列表页响应: {} 字符", len(html))
                parsed = self._parse_list(html, list_url)
                self.logger.info("[MIIT-步骤2] 该页解析出 {} 条", len(parsed))
                for e in parsed:
                    if e["url"] not in seen:
                        seen.add(e["url"])
                        all_entries.append(e)
            except CrawlerError as exc:
                self.logger.warning("[MIIT-步骤2] 列表页失败 {}: {}", list_url, exc)

        self.logger.info("[MIIT-步骤3] 合并所有列表页: {} 条原始条目", len(all_entries))
        candidates = all_entries[: self._max_items * 3]
        self.logger.info("[MIIT-步骤3] 取前 {} 条候选条目", len(candidates))
        
        if not candidates:
            self.logger.warning("[MIIT-步骤3] 无候选条目")
            return []
            
        if self._fetch_detail:
            self.logger.info("[MIIT-步骤4] 抓取 {} 条详情页 (并发={})", len(candidates), self._detail_concurrency)
            items = await self.fetch_details_batch(client, candidates)
            self.logger.info("[MIIT-步骤4] 详情抓取完成 {} 条, 按日期过滤 {}~{}", len(items), start_date, end_date)
            filtered = [
                i for i in items
                if in_date_range(i.publish_time, start_date, end_date)
            ]
            self.logger.info("[MIIT-步骤4] 日期过滤后 {} 条", len(filtered))
            return self.trim_items(filtered)
            
        self.logger.info("[MIIT-步骤4] 按日期范围过滤: {} ~ {}", start_date, end_date)
        filtered = [
            e
            for e in candidates
            if in_date_range(e.get("publish_time"), start_date, end_date)
        ]
        self.logger.info("[MIIT-步骤4] 日期过滤后 {} 条 (截取前{}条)", len(filtered), self._max_items)
        filtered = filtered[: self._max_items]
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
        self.logger.debug("[MIIT-详情] 抓取详情页: {}", url)
        raw = await self.fetch_html_raw(client, url)
        self.logger.debug("[MIIT-详情] 详情页响应: {} 字符", len(raw))
        
        soup = BeautifulSoup(raw, "html.parser")
        parsed = extract_gov_article(soup)
        self.logger.debug("[MIIT-详情] 解析结果: title={} content_len={}", 
                         parsed.get("title", "")[:50], len(parsed.get("content") or ""))
        
        publish_time = parsed.get("publish_time") or entry.get("publish_time")
        if not publish_time:
            publish_time = parse_date_from_url(url)
            self.logger.debug("[MIIT-详情] 从URL解析时间: {}", publish_time)
        content = parsed.get("content") or ""
        if not content:
            self.logger.warning("[MIIT-详情] 正文为空: {}", url)
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
        links = soup.select('a[href*="/art/"]')
        self.logger.debug("[MIIT-解析] 页面共 {} 个包含/art/的链接", len(links))
        for a in links:
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
        self.logger.debug("[MIIT-解析] 有效条目: {}", len(out))
        return out
