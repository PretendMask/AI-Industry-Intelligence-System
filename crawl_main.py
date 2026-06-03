"""新闻爬虫入口示例：并行抓取最近 N 天权威站点新闻。

用法（项目根目录）：
    python crawl_main.py
    python crawl_main.py --days 3 --sources ndrc nea miit china5e
    python crawl_main.py --days 7 --no-incremental
    python crawl_main.py --start 2026-05-28 --end 2026-06-03
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from loguru import logger

from ai_intelligence_system.core.data_collector import DataCollector


def _parse_date(s: str) -> date:
    return date.fromisoformat(s)


def main() -> None:
    parser = argparse.ArgumentParser(description="多源新闻爬虫（异步 httpx）")
    parser.add_argument(
        "--sources",
        nargs="*",
        default=list(DataCollector.DEFAULT_SOURCES),
        help="爬虫 source_id，默认全部",
    )
    parser.add_argument("--days", type=int, default=7, help="最近 N 天（与 --start/--end 二选一）")
    parser.add_argument("--start", type=str, default="", help="开始日期 YYYY-MM-DD")
    parser.add_argument("--end", type=str, default="", help="结束日期 YYYY-MM-DD")
    parser.add_argument("--max-items", type=int, default=15, help="每个源最多条数")
    parser.add_argument(
        "--no-incremental",
        action="store_true",
        help="忽略 crawl_history，强制重抓日期范围内所有天",
    )
    parser.add_argument("--json-out", type=str, default="", help="将结果写入 JSON 文件")
    args = parser.parse_args()

    start_d = _parse_date(args.start) if args.start else None
    end_d = _parse_date(args.end) if args.end else None

    collector = DataCollector(
        source_ids=args.sources,
        max_items_per_source=args.max_items,
        incremental=not args.no_incremental,
    )
    logger.info("已注册爬虫: {}", collector.registered_sources())

    items = collector.collect(
        days=None if start_d else args.days,
        start_date=start_d,
        end_date=end_d,
    )

    payload = [it.to_prompt_dict() | {"raw_html_len": len(it.raw_html)} for it in items]
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    logger.info("共 {} 条新闻", len(items))

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("已写入 {}", out_path)


if __name__ == "__main__":
    main()
