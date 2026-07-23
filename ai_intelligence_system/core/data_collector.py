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
        logger.info("DataCollector 初始化: 源={} max_items={} fetch_detail={} detail_concurrency={} incremental={}",
                     self._source_ids, self._max_items_per_source, self._fetch_detail,
                     self._detail_concurrency, self._incremental)

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
        logger.info("=" * 60)
        logger.info("[步骤1] 解析日期范围: days={} start_date={} end_date={}", days, start_date, end_date)
        start, end = self._history.resolve_range(
            days=days, start=start_date, end=end_date
        )
        logger.info("[步骤1] 日期范围: {} ~ {}", start, end)
        logger.info("[步骤2] 创建爬虫实例: source_ids={}", self._source_ids)
        crawlers = create_many(
            self._source_ids,
            timeout_sec=self._timeout_sec,
            max_items=self._max_items_per_source,
            fetch_detail=self._fetch_detail,
            detail_concurrency=self._detail_concurrency,
            history_store=self._history,
            incremental=self._incremental,
        )
        logger.info("[步骤2] 创建爬虫数量: {} 个", len(crawlers))
        if not crawlers:
            logger.warning("无可用爬虫，已注册: {}", list_registered())
            return []

        logger.info(
            "[步骤3] 采集任务开始：源={} 日期={} ~ {} incremental={}",
            [c.source_id for c in crawlers],
            start,
            end,
            self._incremental,
        )

        headers = BaseCrawler.default_headers
        logger.info("[步骤4] 创建 HTTP 客户端: timeout={}s", self._timeout_sec)
        async with httpx.AsyncClient(
            headers=headers,
            follow_redirects=True,
            timeout=httpx.Timeout(self._timeout_sec),
        ) as client:
            logger.info("[步骤5] 并行启动 {} 个爬虫任务", len(crawlers))
            tasks = [
                self._run_one(client, crawler, start, end) for crawler in crawlers
            ]
            batches = await asyncio.gather(*tasks)
            logger.info("[步骤5] 所有爬虫任务完成, 各源返回: {}", 
                         {crawlers[i].source_id: len(batch) for i, batch in enumerate(batches)})

        merged: list[NewsItem] = []
        for batch in batches:
            merged.extend(batch)

        logger.info("[步骤6] 去重前共 {} 条新闻", len(merged))
        deduped = self._deduplicate(merged)
        logger.info("[步骤7] 采集完成：原始 {} 条，去重后 {} 条", len(merged), len(deduped))
        logger.info("=" * 60)
        return deduped

    async def _run_one(
        self,
        client: httpx.AsyncClient,
        crawler: BaseCrawler,
        start: date,
        end: date,
    ) -> list[NewsItem]:
        sid = crawler.source_id
        logger.info("--- [{}] 开始爬取 ---", sid)
        try:
            if self._incremental and not hasattr(crawler, "_force_range"):
                logger.info("[{}] 增量模式: 查询待抓取日期 {} ~ {}", sid, start, end)
                pending = self._history.pending_dates(sid, start, end, incremental=True)
                logger.info("[{}] 待抓取日期: {} 天 = {}", sid, len(pending), pending)
                if not pending:
                    logger.info("[{}] 无新增日期可抓, 跳过", sid)
                    return []
                run_start, run_end = pending[0], pending[-1]
                logger.info("[{}] 实际抓取范围: {} ~ {}", sid, run_start, run_end)
            else:
                pending = None
                run_start, run_end = start, end
                logger.info("[{}] 非增量模式: 直接抓取 {} ~ {}", sid, run_start, run_end)

            logger.info("[{}] 调用 fetch_by_date: {} ~ {}", sid, run_start, run_end)
            items = await crawler.fetch_by_date(client, run_start, run_end)
            logger.info("[{}] fetch_by_date 返回 {} 条新闻", sid, len(items))

            if self._incremental:
                dates_to_mark = pending if pending else self._history.pending_dates(
                    sid, start, end, incremental=False
                )
                if dates_to_mark:
                    logger.info("[{}] 标记 {} 个日期为已完成: {}", sid, len(dates_to_mark), dates_to_mark)
                    self._history.mark_dates_completed(sid, dates_to_mark)

            if not items and self._skip_empty_sources:
                logger.warning("[{}] 爬虫未返回数据", sid)
            else:
                logger.info("[{}] 爬虫最终返回 {} 条", sid, len(items))
            return items
        except CrawlerError as exc:
            logger.error("[{}] 爬虫业务异常: {}", sid, exc)
            return []
        except Exception as exc:  # noqa: BLE001
            logger.exception("[{}] 爬虫未预期异常: {}", sid, exc)
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
