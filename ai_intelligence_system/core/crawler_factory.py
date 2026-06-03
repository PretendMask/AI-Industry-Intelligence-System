"""爬虫注册表与工厂。"""

from __future__ import annotations

from typing import Any, TypeVar

from ai_intelligence_system.core.base_crawler import BaseCrawler, CrawlerError

C = TypeVar("C", bound=BaseCrawler)

_REGISTRY: dict[str, type[BaseCrawler]] = {}


def register(source_id: str):
    """装饰器：将爬虫类注册到工厂。"""

    def decorator(cls: type[C]) -> type[C]:
        sid = (source_id or getattr(cls, "source_id", "") or cls.__name__).strip().lower()
        if not sid:
            raise ValueError("source_id 不能为空")
        if sid in _REGISTRY and _REGISTRY[sid] is not cls:
            raise ValueError(f"爬虫 source_id 冲突: {sid}")
        cls.source_id = sid
        _REGISTRY[sid] = cls
        return cls

    return decorator


def register_crawler(cls: type[C]) -> type[C]:
    """按类属性 source_id 注册（无装饰器时使用）。"""
    sid = (getattr(cls, "source_id", "") or cls.__name__).strip().lower()
    if not sid:
        raise ValueError("source_id 不能为空")
    _REGISTRY[sid] = cls
    return cls


def list_registered() -> list[str]:
    return sorted(_REGISTRY.keys())


def create(source_id: str, **kwargs: Any) -> BaseCrawler:
    """根据 source_id 实例化爬虫。"""
    sid = source_id.strip().lower()
    cls = _REGISTRY.get(sid)
    if cls is None:
        known = ", ".join(list_registered()) or "(无)"
        raise CrawlerError(f"未知爬虫 source_id={sid!r}，已注册: {known}")
    return cls(**kwargs)


def create_many(source_ids: list[str] | None = None, **kwargs: Any) -> list[BaseCrawler]:
    """批量创建爬虫；source_ids 为空则创建全部已注册爬虫。"""
    ids = source_ids or list_registered()
    return [create(sid, **kwargs) for sid in ids]
