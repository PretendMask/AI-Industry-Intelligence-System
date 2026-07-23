"""国家能源局（NEA）新闻爬虫。"""

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
    parse_date_from_url,
    same_domain,
)

_HOME = "https://www.nea.gov.cn/"


@register("nea")
class NeaCrawler(BaseCrawler):
    source_id = "nea"
    source_name = "国家能源局"
    base_url = _HOME
    list_url = _HOME

    async def fetch_by_date(
        self,
        client: httpx.AsyncClient,
        start_date: date,
        end_date: date,
    ) -> list[NewsItem]:
        self.logger.info("[NEA-步骤1] 按日期抓取 {} ~ {}", start_date, end_date)
        self.logger.info("[NEA-步骤2] 请求首页: {}", self.list_url)
        html = await self.fetch_text(client, self.list_url, encoding="utf-8")
        self.logger.info("[NEA-步骤2] 首页响应: {} 字符", len(html))
        
        self.logger.info("[NEA-步骤3] 解析首页HTML")
        entries = self._parse_home_list(html)
        self.logger.info("[NEA-步骤3] 解析到 {} 条原始条目", len(entries))
        
        self.logger.info("[NEA-步骤4] 按日期范围过滤: {} ~ {}", start_date, end_date)
        filtered = [
            e
            for e in entries
            if in_date_range(e.get("publish_time"), start_date, end_date)
        ]
        self.logger.info("[NEA-步骤4] 日期过滤后 {} 条 (截取前{}条)", len(filtered), self._max_items)
        filtered = filtered[: self._max_items]
        
        if not filtered:
            self.logger.warning("[NEA-步骤4] 日期范围内无新闻条目")
            return []
            
        if self._fetch_detail:
            self.logger.info("[NEA-步骤5] 抓取 {} 条详情页 (并发={})", len(filtered), self._detail_concurrency)
            items = await self.fetch_details_batch(client, filtered)
            self.logger.info("[NEA-步骤5] 详情抓取完成，共 {} 条", len(items))
            return items
            
        self.logger.info("[NEA] 跳过详情抓取，仅返回列表数据")
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
        self.logger.debug("[NEA-详情] 抓取详情页: {}", url)
        raw = await self.fetch_html_raw(client, url)
        self.logger.debug("[NEA-详情] 详情页响应: {} 字符", len(raw))
        
        soup = BeautifulSoup(raw, "html.parser")
        parsed = extract_gov_article(soup)
        self.logger.debug("[NEA-详情] 解析结果: title={} content_len={}", 
                         parsed.get("title", "")[:50], len(parsed.get("content") or ""))
        
        publish_time = parsed.get("publish_time") or entry.get("publish_time")
        if not publish_time:
            publish_time = parse_date_from_url(url)
            self.logger.debug("[NEA-详情] 从URL解析时间: {}", publish_time)
        content = parsed.get("content") or ""
        if not content:
            self.logger.warning("[NEA-详情] 正文为空: {}", url)
            raise CrawlerError(f"正文为空: {url}")
        return self.make_item(
            title=parsed.get("title") or entry["title"],
            url=url,
            publish_time=publish_time,
            content=content,
            raw_html=raw,
            list_url=self.list_url,
        )

    def _parse_home_list(self, html: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        seen: set[str] = set()
        out: list[dict[str, Any]] = []
        all_links = soup.select("a[href]")
        self.logger.debug("[NEA-解析] 页面共 {} 个链接", len(all_links))
        for a in all_links:
            href = (a.get("href") or "").strip()
            title = (a.get_text() or "").strip()
            if not title or len(title) < 8 or not is_article_href(href):
                continue
            url = self.resolve_url(href, page_url=self.list_url)
            if not same_domain(url, "nea.gov.cn") or "zfxxgk." in url:
                continue
            pt = parse_date_from_url(url)
            if not pt:
                continue
            if url in seen:
                continue
            seen.add(url)
            out.append({"title": title, "url": url, "publish_time": pt})
        self.logger.debug("[NEA-解析] 有效条目: {} (标题>=8字, 同域, 含日期)", len(out))
        return out
