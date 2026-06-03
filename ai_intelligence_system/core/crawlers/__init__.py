"""内置爬虫：导入即注册到 CrawlerFactory。"""

from __future__ import annotations

import importlib

_AUTO_IMPORTS = (
    "ndrc",
    "national_energy_admin",
    "miit",
    "china_energy_net",
)


def _ensure_registered() -> None:
    for mod in _AUTO_IMPORTS:
        importlib.import_module(f"{__name__}.{mod}")


_ensure_registered()
