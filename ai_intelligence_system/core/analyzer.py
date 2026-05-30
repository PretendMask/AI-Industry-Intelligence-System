"""分析 Prompt 与结构化结果解析。"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

DEFAULT_SYSTEM_PROMPT = """你是资深新能源、电力与人工智能产业研究分析师。
请基于用户给定的关键词与时间范围，综合判断近期值得关注的行业情报要点。
你必须只输出 **一个合法 JSON 对象**（不要 Markdown 代码围栏，不要多余文字），字段如下：
{
  "title": "字符串，简报标题",
  "source": "字符串，信息来源名称/机构/媒体名称，必须具体，不能只写公开报道或网络资料",
  "source_url": "字符串，原始消息网页 URL 或官方公告 URL；必须是真实可访问的完整 http/https 地址；如果无法确认原文 URL，填空字符串",
  "time": "字符串，ISO8601 或人类可读时间范围",
  "summary": "字符串，一句话摘要",
  "impact": "字符串，利好/利空行业或环节说明",
  "score": 1到10的整数，情绪强度评分,
  "stage": "字符串，必须是以下之一：信息冲击期 / 情绪加速期 / 利多兑现期 / 不确定",
  "tags": ["字符串标签"],
  "related": ["潜在关联方向"],
  "analysis": "字符串，完整分析文本（分段清晰）"
}
要求：
- 不要编造来源地址；source_url 只能填写你确信存在的原始新闻、官方公告、监管文件、公司公告或政策文件链接。
- 如果无法给出可信原文链接，source_url 必须为空字符串，并在 summary 或 analysis 中说明“缺少可核验原文链接”。
- 优先选择官方/交易所/监管机构/公司官网/主流媒体原文链接，而不是转载页或搜索结果页。
确保 score 为整数，JSON 可被标准库 json.loads 解析。"""


TimeRange = Literal["24h", "3d", "7d"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def time_range_label(tr: TimeRange) -> str:
    if tr == "24h":
        return "最近 24 小时"
    if tr == "3d":
        return "最近 3 天"
    return "最近 7 天"


def build_user_prompt(
    *,
    keywords: list[str],
    time_range: TimeRange,
    extra_instruction: str = "",
) -> str:
    start = utc_now()
    if time_range == "24h":
        window_start = start - timedelta(hours=24)
    elif time_range == "3d":
        window_start = start - timedelta(days=3)
    else:
        window_start = start - timedelta(days=7)

    kw = "、".join(keywords) if keywords else "新能源、电力、人工智能产业链"
    base = (
        f"关注关键词：{kw}。\n"
        f"分析时间窗口：{time_range_label(time_range)}（约从 {window_start.isoformat()} 至 {start.isoformat()}）。\n"
        "请输出符合系统提示约束的 JSON。"
    )
    if extra_instruction.strip():
        base += "\n用户补充要求：\n" + extra_instruction.strip()
    return base


def parse_analysis_json(text: str) -> dict[str, Any]:
    """从模型返回文本中提取 JSON（容错去除 ```json 围栏）。"""
    raw = text.strip()
    fence = re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```$", raw, re.IGNORECASE)
    if fence:
        raw = fence.group(1).strip()
    return json.loads(raw)


def flatten_tags(tags: Any) -> str:
    if isinstance(tags, list):
        return ",".join(str(x) for x in tags)
    return str(tags or "")
