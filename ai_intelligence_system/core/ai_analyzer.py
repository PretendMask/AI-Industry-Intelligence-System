"""基于本地抓取数据的 AI 聚合分析（不联网检索）。"""

from __future__ import annotations

import json
from typing import Any, cast

from loguru import logger

from ai_intelligence_system.core import analyzer
from ai_intelligence_system.core.ai_client import DeepSeekClient
from ai_intelligence_system.core.analyzer import TimeRange, parse_analysis_json
from ai_intelligence_system.core.base_crawler import NewsItem

CRAWL_BASED_SYSTEM_PROMPT = """你是资深新能源、电力与人工智能产业研究分析师。
你将收到由本地定向爬虫从权威网站抓取的原始新闻条目（JSON 数组），请**仅基于这些条目**进行归纳与研判，不得虚构未提供的新闻，不得声称已联网检索。
你必须只输出 **一个合法 JSON 对象**（不要 Markdown 代码围栏，不要多余文字），字段如下：
{
  "title": "字符串，简报标题",
  "source": "字符串，综合后的主要信息来源（可写多个机构，用顿号分隔）",
  "source_url": "字符串，最重要的一条原文 URL；若无则填空字符串",
  "time": "字符串，ISO8601 或人类可读时间范围",
  "summary": "字符串，一句话摘要",
  "impact": "字符串，利好/利空行业或环节说明",
  "score": 1到10的整数，情绪强度评分,
  "stage": "字符串，必须是以下之一：信息冲击期 / 情绪加速期 / 利多兑现期 / 不确定",
  "tags": ["字符串标签"],
  "related": ["潜在关联方向"],
  "analysis": "字符串，完整分析文本（分段清晰，引用关键政策/新闻要点并标注来源名称）"
}
要求：
- source_url 只能使用用户提供的 news_items 中已有的 url 字段，不得编造。
- 若材料不足以支撑结论，在 analysis 中说明数据缺口。
- 确保 score 为整数，JSON 可被标准库 json.loads 解析。"""


def build_news_context(items: list[NewsItem], *, max_items: int = 30) -> str:
    """将 NewsItem 序列化为模型可读的 JSON 文本。"""
    payload = [it.to_prompt_dict() for it in items[:max_items]]
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_crawl_user_prompt(
    *,
    items: list[NewsItem],
    keywords: list[str],
    time_range: TimeRange,
    extra_instruction: str = "",
) -> str:
    kw = "、".join(keywords) if keywords else "新能源、电力、人工智能产业链"
    window = analyzer.time_range_label(time_range)
    base = (
        f"关注关键词：{kw}。\n"
        f"分析时间窗口：{window}。\n"
        f"共提供 {len(items)} 条爬虫抓取的新闻条目（见 news_items）。\n"
        "请输出符合系统提示约束的 JSON。\n\n"
        "news_items:\n"
        f"{build_news_context(items)}"
    )
    if extra_instruction.strip():
        base += "\n\n用户补充要求：\n" + extra_instruction.strip()
    return base


class AiAnalyzer:
    """接收 NewsItem 列表，调用 DeepSeek 生成结构化情报分析。"""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://api.deepseek.com",
        model: str = "deepseek-chat",
        system_prompt: str | None = None,
    ) -> None:
        self._client = DeepSeekClient(api_key=api_key, base_url=base_url, model=model)
        self._system_prompt = (system_prompt or "").strip() or CRAWL_BASED_SYSTEM_PROMPT

    def analyze(
        self,
        items: list[NewsItem],
        *,
        keywords: list[str],
        time_range: TimeRange | str = "24h",
        extra_instruction: str = "",
    ) -> dict[str, Any]:
        if not items:
            raise ValueError("无可分析的新闻数据：请先运行数据采集")

        tr = time_range if time_range in ("24h", "3d", "7d") else "24h"
        user_msg = build_crawl_user_prompt(
            items=items,
            keywords=keywords,
            time_range=cast(TimeRange, tr),
            extra_instruction=extra_instruction,
        )

        logger.info("开始 AI 分析，新闻条数={} time_range={}", len(items), tr)
        data = self._client.chat_completion(
            [
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": user_msg},
            ]
        )
        content = self._client.extract_message_content(data)
        parsed = parse_analysis_json(content)
        logger.info("AI 分析完成，标题={}", parsed.get("title", ""))
        return parsed
