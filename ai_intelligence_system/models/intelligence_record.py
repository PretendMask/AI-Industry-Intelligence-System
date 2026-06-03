"""情报记录 ORM（与 REQUIREMENTS.md 字段对齐）。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class IntelligenceRecord(Base):
    __tablename__ = "intelligence_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), default="")
    source: Mapped[str] = mapped_column(String(256), default="")
    source_url: Mapped[str] = mapped_column(Text, default="")
    content: Mapped[str] = mapped_column(Text, default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    impact: Mapped[str] = mapped_column(Text, default="")  # 利好/利空行业等 JSON 或文本
    score: Mapped[float] = mapped_column(Float, default=0.0)
    stage: Mapped[str] = mapped_column(String(128), default="")
    tags: Mapped[str] = mapped_column(Text, default="")  # 逗号分隔或 JSON
    raw_json: Mapped[str] = mapped_column(Text, default="")


class NewsRecord(Base):
    __tablename__ = "news_records"
    __table_args__ = (UniqueConstraint("url", name="uq_news_records_url"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(512), default="")
    url: Mapped[str] = mapped_column(Text, nullable=False)
    publish_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    source: Mapped[str] = mapped_column(String(256), default="", index=True)
    content: Mapped[str] = mapped_column(Text, default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    raw_html: Mapped[str] = mapped_column(Text, default="")
    metadata_json: Mapped[str] = mapped_column(Text, default="")
    crawled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
