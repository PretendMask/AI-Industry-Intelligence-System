"""应用配置：Pydantic 模型 + JSON 持久化（敏感字段加密存储）。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from ai_intelligence_system.utils import crypto
from ai_intelligence_system.utils.paths import default_database_path, user_config_path


class SchedulerSlot(BaseModel):
    """单个定时任务开关、频率与时间（HH:MM）。"""

    enabled: bool = True
    time: str = "07:30"
    frequency: str = "daily"  # daily | weekly
    weekday: int = 0  # 0=周一 ... 6=周日，仅 weekly 生效


class AppSettings(BaseSettings):
    """运行时配置（非密文字段）；密文在 JSON 中单独加密字段保存。"""

    model_config = SettingsConfigDict(
        env_prefix="AI_INTELLIGENCE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    log_level: str = Field(default="INFO", description="loguru 日志级别")

    # DeepSeek（内存中明文，从文件解密加载）
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # 邮件
    smtp_host: str = ""
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_ssl: bool = True
    mail_recipients: list[str] = Field(default_factory=list)

    # 定时
    scheduler_morning: SchedulerSlot = Field(
        default_factory=lambda: SchedulerSlot(enabled=True, time="07:30")
    )
    scheduler_noon: SchedulerSlot = Field(
        default_factory=lambda: SchedulerSlot(enabled=True, time="12:30")
    )
    scheduler_evening: SchedulerSlot = Field(
        default_factory=lambda: SchedulerSlot(enabled=True, time="20:00")
    )

    # 业务
    industry_keywords: list[str] = Field(
        default_factory=lambda: [
            "光伏",
            "储能",
            "锂电池",
            "电网",
            "算力",
            "GPU",
        ]
    )
    database_path: str = Field(default_factory=lambda: str(default_database_path()))

    # 定向爬虫（source_id 列表，见 core/crawler_factory）
    crawl_source_ids: list[str] = Field(
        default_factory=lambda: ["ndrc", "nea", "miit", "china5e"]
    )
    crawl_max_items_per_source: int = Field(default=10, ge=1, le=50)

    # 手动分析默认 Prompt 可由界面覆盖后保存
    custom_system_prompt: str = ""


class _PersistedConfig(BaseModel):
    """磁盘 JSON 结构。"""

    log_level: str = "INFO"
    deepseek_api_key_enc: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    smtp_host: str = ""
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_password_enc: str = ""
    smtp_use_ssl: bool = True
    mail_recipients: list[str] = Field(default_factory=list)
    scheduler_morning: SchedulerSlot = Field(
        default_factory=lambda: SchedulerSlot(enabled=True, time="07:30")
    )
    scheduler_noon: SchedulerSlot = Field(
        default_factory=lambda: SchedulerSlot(enabled=True, time="12:30")
    )
    scheduler_evening: SchedulerSlot = Field(
        default_factory=lambda: SchedulerSlot(enabled=True, time="20:00")
    )
    industry_keywords: list[str] = Field(default_factory=list)
    database_path: str = ""
    crawl_source_ids: list[str] = Field(
        default_factory=lambda: ["ndrc", "nea", "miit", "china5e"]
    )
    crawl_max_items_per_source: int = 10
    custom_system_prompt: str = ""


def _persist_path() -> Path:
    return user_config_path()


def load_settings() -> AppSettings:
    path = _persist_path()
    if not path.exists():
        return AppSettings()
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    persisted = _PersistedConfig.model_validate(raw)
    db_path = persisted.database_path or str(default_database_path())
    return AppSettings(
        log_level=persisted.log_level,
        deepseek_api_key=crypto.decrypt_secret(persisted.deepseek_api_key_enc),
        deepseek_base_url=persisted.deepseek_base_url,
        deepseek_model=persisted.deepseek_model,
        smtp_host=persisted.smtp_host,
        smtp_port=persisted.smtp_port,
        smtp_user=persisted.smtp_user,
        smtp_password=crypto.decrypt_secret(persisted.smtp_password_enc),
        smtp_use_ssl=persisted.smtp_use_ssl,
        mail_recipients=persisted.mail_recipients,
        scheduler_morning=persisted.scheduler_morning,
        scheduler_noon=persisted.scheduler_noon,
        scheduler_evening=persisted.scheduler_evening,
        industry_keywords=persisted.industry_keywords or AppSettings().industry_keywords,
        database_path=db_path,
        crawl_source_ids=persisted.crawl_source_ids
        or ["ndrc", "nea", "miit", "china5e"],
        crawl_max_items_per_source=persisted.crawl_max_items_per_source or 10,
        custom_system_prompt=persisted.custom_system_prompt,
    )


def save_settings(settings: AppSettings) -> None:
    path = _persist_path()
    persisted = _PersistedConfig(
        log_level=settings.log_level,
        deepseek_api_key_enc=crypto.encrypt_secret(settings.deepseek_api_key),
        deepseek_base_url=settings.deepseek_base_url,
        deepseek_model=settings.deepseek_model,
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_user=settings.smtp_user,
        smtp_password_enc=crypto.encrypt_secret(settings.smtp_password),
        smtp_use_ssl=settings.smtp_use_ssl,
        mail_recipients=settings.mail_recipients,
        scheduler_morning=settings.scheduler_morning,
        scheduler_noon=settings.scheduler_noon,
        scheduler_evening=settings.scheduler_evening,
        industry_keywords=settings.industry_keywords,
        database_path=settings.database_path,
        crawl_source_ids=settings.crawl_source_ids,
        crawl_max_items_per_source=settings.crawl_max_items_per_source,
        custom_system_prompt=settings.custom_system_prompt,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(persisted.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
