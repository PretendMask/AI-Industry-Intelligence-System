"""命令行：爬虫采集 → AI 分析。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from loguru import logger

from ai_intelligence_system.config.settings import load_settings
from ai_intelligence_system.core.ai_analyzer import AiAnalyzer
from ai_intelligence_system.core.data_collector import DataCollector


def main() -> None:
    parser = argparse.ArgumentParser(description="爬虫采集 + 可选 AI 分析")
    parser.add_argument("--sources", nargs="*", default=None)
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--max-items", type=int, default=10)
    parser.add_argument("--time-range", choices=["24h", "3d", "7d"], default="3d")
    parser.add_argument("--no-ai", action="store_true")
    parser.add_argument("--no-incremental", action="store_true")
    args = parser.parse_args()

    settings = load_settings()
    sources = args.sources or settings.crawl_source_ids
    collector = DataCollector(
        source_ids=sources,
        max_items_per_source=args.max_items,
        incremental=not args.no_incremental,
    )
    items = collector.collect(days=args.days)
    logger.info("采集 {} 条", len(items))

    if args.no_ai:
        print(json.dumps([it.to_prompt_dict() for it in items], ensure_ascii=False, indent=2))
        return

    if not settings.deepseek_api_key:
        raise SystemExit("请配置 DeepSeek API Key")

    analyzer = AiAnalyzer(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        model=settings.deepseek_model,
        system_prompt=settings.custom_system_prompt.strip() or None,
    )
    result = analyzer.analyze(
        items,
        keywords=settings.industry_keywords,
        time_range=args.time_range,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
