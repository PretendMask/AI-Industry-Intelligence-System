"""证券时报爬虫模板 — 添加新源时参考本文件与 ndrc.py。

启用步骤：在 crawlers/__init__.py 的 _AUTO_IMPORTS 中加入 "stcn"，
并在 settings.crawl_source_ids 中加入 "stcn"。
"""

from __future__ import annotations

import httpx

from ai_intelligence_system.core.base_crawler import BaseCrawler, NewsItem
from ai_intelligence_system.core.crawler_factory import register


@register("stcn")
class StcnCrawler(BaseCrawler):
    source_id = "stcn"
    source_name = "证券时报"
    base_url = "https://www.stcn.com/"
    list_url = "https://www.stcn.com/article/list/kx.html"  # TODO: 按实际栏目调整

    async def crawl(self, client: httpx.AsyncClient) -> list[NewsItem]:
        # TODO: 解析列表页 → 抓取详情 → NewsItem(...)
        self.logger.warning("{} 尚未实现，返回空列表", self.source_name)
        return []
