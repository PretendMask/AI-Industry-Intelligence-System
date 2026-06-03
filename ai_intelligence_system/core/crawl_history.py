"""爬虫按日抓取进度（JSON 持久化，支持增量只抓新日期）。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

from loguru import logger

from ai_intelligence_system.utils.paths import data_dir

_DEFAULT_PATH = data_dir() / "crawl_history.json"


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _date_str(d: date) -> str:
    return d.isoformat()


def _parse_date(s: str) -> date:
    return date.fromisoformat(s[:10])


def iter_dates(start: date, end: date) -> list[date]:
    if start > end:
        return []
    out: list[date] = []
    cur = start
    while cur <= end:
        out.append(cur)
        cur += timedelta(days=1)
    return out


@dataclass
class SourceCrawlRecord:
    source_id: str
    completed_dates: list[str] = field(default_factory=list)
    last_run_at: str | None = None

    def completed_set(self) -> set[str]:
        return set(self.completed_dates)


@dataclass
class CrawlHistoryFile:
    version: int = 1
    sources: dict[str, SourceCrawlRecord] = field(default_factory=dict)


class CrawlHistoryStore:
    """读写 data/crawl_history.json。"""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or _DEFAULT_PATH
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> CrawlHistoryFile:
        if not self._path.exists():
            return CrawlHistoryFile()
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            sources: dict[str, SourceCrawlRecord] = {}
            for sid, rec in (raw.get("sources") or {}).items():
                sources[sid] = SourceCrawlRecord(
                    source_id=sid,
                    completed_dates=list(rec.get("completed_dates") or []),
                    last_run_at=rec.get("last_run_at"),
                )
            return CrawlHistoryFile(version=int(raw.get("version") or 1), sources=sources)
        except (json.JSONDecodeError, OSError, TypeError, ValueError) as exc:
            logger.warning("读取 crawl_history 失败，将使用空记录: {}", exc)
            return CrawlHistoryFile()

    def save(self, data: CrawlHistoryFile) -> None:
        payload = {
            "version": data.version,
            "sources": {
                sid: {
                    "completed_dates": sorted(rec.completed_set()),
                    "last_run_at": rec.last_run_at,
                }
                for sid, rec in data.sources.items()
            },
        }
        self._path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.debug("已写入 crawl_history: {}", self._path)

    def get_record(self, source_id: str) -> SourceCrawlRecord:
        data = self.load()
        sid = source_id.strip().lower()
        if sid not in data.sources:
            data.sources[sid] = SourceCrawlRecord(source_id=sid)
        return data.sources[sid]

    def pending_dates(
        self,
        source_id: str,
        start: date,
        end: date,
        *,
        incremental: bool = True,
    ) -> list[date]:
        """返回尚未标记完成的日期列表（升序）。"""
        all_days = iter_dates(start, end)
        if not incremental:
            return all_days
        done = self.get_record(source_id).completed_set()
        return [d for d in all_days if _date_str(d) not in done]

    def mark_dates_completed(
        self,
        source_id: str,
        dates: Iterable[date | str],
    ) -> None:
        data = self.load()
        sid = source_id.strip().lower()
        rec = data.sources.setdefault(sid, SourceCrawlRecord(source_id=sid))
        for d in dates:
            ds = _date_str(_parse_date(d)) if isinstance(d, str) else _date_str(d)
            if ds not in rec.completed_dates:
                rec.completed_dates.append(ds)
        rec.completed_dates = sorted(set(rec.completed_dates))
        rec.last_run_at = datetime.now(timezone.utc).isoformat()
        data.sources[sid] = rec
        self.save(data)
        logger.info("已记录爬虫 {} 完成日期 {} 个", sid, len(rec.completed_dates))

    def resolve_range(
        self,
        *,
        days: int | None = None,
        start: date | None = None,
        end: date | None = None,
    ) -> tuple[date, date]:
        end_d = end or _today()
        if start is not None:
            return start, end_d
        lookback = max(1, days or 7)
        return end_d - timedelta(days=lookback - 1), end_d
