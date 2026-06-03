"""统一数据采集：多源并行、按日增量、去重合并。"""

from __future__ import annotations

import asyncio
from datetime import date

import httpx
from loguru import logger

from ai_intelligence_system.core.base_crawler import BaseCrawler, CrawlerError, NewsItem
from ai_intelligence_system.core.crawl_history import CrawlHistoryStore
from ai_intelligence_system.core.crawler_factory import create_many, list_registered

import ai_intelligence_system.core.crawlers  # noqa: F401


class DataCollector:
    """注册并调度全部爬虫，支持按日期范围与增量抓取。"""

    DEFAULT_SOURCES = ("ndrc", "nea", "miit", "china5e")

    def __init__(
        self,
        source_ids: list[str] | None = None,
        *,
        timeout_sec: float = 30.0,
        max_items_per_source: int = 20,
        fetch_detail: bool = True,
        detail_concurrency: int = 5,
        skip_empty_sources: bool = True,
        incremental: bool = True,
        history_store: CrawlHistoryStore | None = None,
    ) -> None:
        self._source_ids = list(source_ids or self.DEFAULT_SOURCES)
        self._timeout_sec = timeout_sec
        self._max_items_per_source = max_items_per_source
        self._fetch_detail = fetch_detail
        self._detail_concurrency = detail_concurrency
        self._skip_empty_sources = skip_empty_sources
        self._incremental = incremental
        self._history = history_store or CrawlHistoryStore()

    def collect(
        self,
        *,
        days: int | None = 7,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[NewsItem]:
        return asyncio.run(
            self.collect_async(days=days, start_date=start_date, end_date=end_date)
        )

    async def collect_async(
        self,
        *,
        days: int | None = 7,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[NewsItem]:
        start, end = self._history.resolve_range(
            days=days, start=start_date, end=end_date
        )
        crawlers = create_many(
            self._source_ids,
            timeout_sec=self._timeout_sec,
            max_items=self._max_items_per_source,
            fetch_detail=self._fetch_detail,
            detail_concurrency=self._detail_concurrency,
            history_store=self._history,
            incremental=self._incremental,
        )
        if not crawlers:
            logger.warning("无可用爬虫，已注册: {}", list_registered())
            return []

        logger.info(
            "采集任务：源={} 日期={} ~ {} incremental={}",
            [c.source_id for c in crawlers],
            start,
            end,
            self._incremental,
        )

        headers = BaseCrawler.default_headers
        async with httpx.AsyncClient(
            headers=headers,
            follow_redirects=True,
            timeout=httpx.Timeout(self._timeout_sec),
        ) as client:
            tasks = [
                self._run_one(client, crawler, start, end) for crawler in crawlers
            ]
            batches = await asyncio.gather(*tasks)

        merged: list[NewsItem] = []
        for batch in batches:
            merged.extend(batch)

        deduped = self._deduplicate(merged)
        logger.info("采集完成：原始 {} 条，去重后 {} 条", len(merged), len(deduped))
        return deduped

    async def _run_one(
        self,
        client: httpx.AsyncClient,
        crawler: BaseCrawler,
        start: date,
        end: date,
    ) -> list[NewsItem]:
        sid = crawler.source_id
        try:
            if self._incremental and not hasattr(crawler, "_force_range"):
                pending = self._history.pending_dates(sid, start, end, incremental=True)
                if not pending:
                    logger.info("爬虫 {} 无新增日期可抓", sid)
                    return []
                run_start, run_end = pending[0], pending[-1]
            else:
                pending = None
                run_start, run_end = start, end

            items = await crawler.fetch_by_date(client, run_start, run_end)

            if self._incremental:
                dates_to_mark = pending if pending else self._history.pending_dates(
                    sid, start, end, incremental=False
                )
                if dates_to_mark:
                    self._history.mark_dates_completed(sid, dates_to_mark)

            if not items and self._skip_empty_sources:
                logger.warning("爬虫 {} 未返回数据", sid)
            else:
                logger.info("爬虫 {} 返回 {} 条", sid, len(items))
            return items
        except CrawlerError as exc:
            logger.error("爬虫 {} 失败: {}", sid, exc)
            return []
        except Exception as exc:  # noqa: BLE001
            logger.exception("爬虫 {} 异常: {}", sid, exc)
            return []

    @staticmethod
    def _deduplicate(items: list[NewsItem]) -> list[NewsItem]:
        seen: set[str] = set()
        out: list[NewsItem] = []
        for item in items:
            key = item.dedup_key()
            if key in seen:
                continue
            seen.add(key)
            out.append(item)
        return out

    @staticmethod
    def registered_sources() -> list[str]:
        return list_registered()
