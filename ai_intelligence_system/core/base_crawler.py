"""爬虫抽象基类与统一新闻数据结构。"""

from __future__ import annotations

import abc
import asyncio
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any

import httpx
from loguru import logger

from ai_intelligence_system.core.crawl_history import CrawlHistoryStore


class CrawlerError(Exception):
    """爬虫业务异常（可预期的抓取失败）。"""


@dataclass(slots=True)
class NewsItem:
    """单条新闻/公告的标准结构。"""

    title: str
    url: str
    source: str
    publish_time: str | None = None
    content: str = ""
    raw_html: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    crawled_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # 兼容旧字段
    @property
    def published_at(self) -> str | None:
        return self.publish_time

    @property
    def summary(self) -> str:
        return (self.content or self.title)[:280]

    def dedup_key(self) -> str:
        key = (self.url or "").strip().lower()
        if key:
            return key
        return f"{self.source.strip().lower()}::{self.title.strip().lower()}"

    def to_prompt_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "publish_time": self.publish_time,
            "content": (self.content or self.title)[:4000],
            "metadata": self.metadata,
        }


class BaseCrawler(abc.ABC):
    """定向站点爬虫：子类实现列表采集与 `fetch_by_date`。"""

    source_id: str = ""
    source_name: str = ""
    base_url: str = ""

    default_headers: dict[str, str] = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    def __init__(
        self,
        *,
        timeout_sec: float = 30.0,
        max_items: int = 30,
        fetch_detail: bool = True,
        detail_concurrency: int = 5,
        history_store: CrawlHistoryStore | None = None,
        incremental: bool = True,
    ) -> None:
        self._timeout_sec = timeout_sec
        self._max_items = max(1, max_items)
        self._fetch_detail = fetch_detail
        self._detail_concurrency = max(1, detail_concurrency)
        self._history = history_store or CrawlHistoryStore()
        self._incremental = incremental
        self._last_crawled_dates: list[date] = []

    @property
    def logger(self):
        return logger.bind(crawler=self.source_id or self.__class__.__name__)

    @abc.abstractmethod
    async def fetch_by_date(
        self,
        client: httpx.AsyncClient,
        start_date: date,
        end_date: date,
    ) -> list[NewsItem]:
        """抓取发布时间在 [start_date, end_date] 内的新闻。"""

    async def crawl(self, client: httpx.AsyncClient) -> list[NewsItem]:
        """默认增量：仅抓取历史中尚未完成的日期（最近 7 天窗口）。"""
        from ai_intelligence_system.core.crawl_history import _today

        end = _today()
        start = end.replace(day=max(1, end.day - 6))  # 占位，实际用 resolve_incremental
        return await self.crawl_incremental(client, days=7)

    async def crawl_incremental(
        self,
        client: httpx.AsyncClient,
        *,
        days: int = 7,
    ) -> list[NewsItem]:
        start, end = self._history.resolve_range(days=days)
        pending = self._history.pending_dates(
            self.source_id, start, end, incremental=self._incremental
        )
        if not pending:
            self.logger.info("无待抓取新日期（{} ~ {}）", start, end)
            return []
        p_start, p_end = pending[0], pending[-1]
        items = await self.fetch_by_date(client, p_start, p_end)
        self._history.mark_dates_completed(self.source_id, pending)
        self._last_crawled_dates = pending
        return self.trim_items(items)

    async def fetch_text(
        self,
        client: httpx.AsyncClient,
        url: str,
        *,
        encoding: str | None = None,
    ) -> str:
        self.logger.debug("HTTP 请求: GET {}", url)
        try:
            resp = await client.get(url, timeout=self._timeout_sec)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            self.logger.error("HTTP 状态错误: {} {}", url, exc.response.status_code)
            raise CrawlerError(f"HTTP 状态 {exc.response.status_code}: {url}") from exc
        except httpx.TimeoutException as exc:
            self.logger.error("HTTP 超时: {}", url)
            raise CrawlerError(f"HTTP 超时: {url}") from exc
        except httpx.HTTPError as exc:
            self.logger.error("HTTP 请求失败: {} - {}", url, exc)
            raise CrawlerError(f"HTTP 请求失败: {url}") from exc

        # 必须在访问 resp.text 之前设置 encoding，否则 httpx 会抛出 ValueError
        if encoding:
            resp.encoding = encoding
        elif not resp.encoding or resp.encoding.lower() == "iso-8859-1":
            resp.encoding = resp.charset_encoding or "utf-8"
        self.logger.debug("HTTP 响应: status={} encoding={} length={}", resp.status_code, resp.encoding, len(resp.text))
        return resp.text

    async def fetch_html_raw(
        self,
        client: httpx.AsyncClient,
        url: str,
        *,
        encoding: str | None = "utf-8",
    ) -> str:
        return await self.fetch_text(client, url, encoding=encoding)

    def resolve_url(self, href: str, *, page_url: str | None = None) -> str:
        from urllib.parse import urljoin

        base = page_url or self.base_url
        return urljoin(base, href.strip())

    def trim_items(self, items: list[NewsItem]) -> list[NewsItem]:
        return items[: self._max_items]

    def make_item(
        self,
        *,
        title: str,
        url: str,
        publish_time: str | None,
        content: str = "",
        raw_html: str = "",
        list_url: str | None = None,
    ) -> NewsItem:
        meta: dict[str, Any] = {}
        if list_url:
            meta["list_url"] = list_url
        return NewsItem(
            title=title,
            url=url,
            source=self.source_name,
            publish_time=publish_time,
            content=content,
            raw_html=raw_html,
            metadata=meta,
        )

    async def fetch_details_batch(
        self,
        client: httpx.AsyncClient,
        entries: list[dict[str, Any]],
    ) -> list[NewsItem]:
        """并发抓取详情页。"""
        self.logger.info("开始批量抓取详情: {} 条, 并发数={}", len(entries), self._detail_concurrency)
        sem = asyncio.Semaphore(self._detail_concurrency)
        items: list[NewsItem] = []
        success_count = [0]
        fail_count = [0]

        async def one(entry: dict[str, Any]) -> NewsItem | None:
            async with sem:
                try:
                    result = await self.fetch_article_item(client, entry)
                    success_count[0] += 1
                    self.logger.debug("详情抓取成功 [{}/{}]: {}", success_count[0] + fail_count[0], len(entries), entry.get("url"))
                    return result
                except CrawlerError as exc:
                    fail_count[0] += 1
                    self.logger.warning("详情失败 [{}/{}] {}: {}", success_count[0] + fail_count[0], len(entries), entry.get("url"), exc)
                except Exception as exc:  # noqa: BLE001
                    fail_count[0] += 1
                    self.logger.exception("详情异常 [{}/{}] {}: {}", success_count[0] + fail_count[0], len(entries), entry.get("url"), exc)
                return None

        results = await asyncio.gather(*[one(e) for e in entries])
        for r in results:
            if r is not None:
                items.append(r)
        self.logger.info("批量详情抓取完成: 成功{} / 失败{} / 总计{}", success_count[0], fail_count[0], len(entries))
        return items

    async def fetch_article_item(
        self,
        client: httpx.AsyncClient,
        entry: dict[str, Any],
    ) -> NewsItem:
        """子类可覆盖：默认仅列表字段。"""
        return self.make_item(
            title=entry["title"],
            url=entry["url"],
            publish_time=entry.get("publish_time"),
            content=entry.get("content") or "",
        )
