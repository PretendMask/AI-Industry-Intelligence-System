"""SQLite 数据库：引擎、会话与初始化。"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import json
import threading

from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from ai_intelligence_system.models.intelligence_record import Base, IntelligenceRecord, NewsRecord
from ai_intelligence_system.core.base_crawler import NewsItem


_INIT_DB_LOCK = threading.Lock()


def create_engine_for_path(database_path: str) -> Engine:
    url = f"sqlite:///{database_path}"
    return create_engine(
        url,
        echo=False,
        future=True,
        connect_args={"check_same_thread": False},
    )


def init_db(engine: Engine) -> None:
    with _INIT_DB_LOCK:
        Base.metadata.create_all(engine, checkfirst=True)
        ensure_schema_compatibility(engine)


def ensure_schema_compatibility(engine: Engine) -> None:
    inspector = inspect(engine)
    if "intelligence_records" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("intelligence_records")}
    if "source_url" not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE intelligence_records ADD COLUMN source_url TEXT DEFAULT ''"))


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    """expire_on_commit=False：只读场景在 with 内取数，避免提交后意外过期。"""
    return sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        future=True,
        expire_on_commit=False,
    )


@contextmanager
def session_scope(session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def insert_record(session: Session, record: IntelligenceRecord) -> IntelligenceRecord:
    session.add(record)
    session.flush()
    return record


def list_recent_records(session: Session, limit: int = 10) -> list[IntelligenceRecord]:
    stmt = select(IntelligenceRecord).order_by(IntelligenceRecord.timestamp.desc()).limit(limit)
    return list(session.scalars(stmt).all())


def list_all_records(session: Session) -> list[IntelligenceRecord]:
    stmt = select(IntelligenceRecord).order_by(IntelligenceRecord.timestamp.desc())
    return list(session.scalars(stmt).all())


def _parse_news_datetime(value: str | None) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(text[: len(fmt)], fmt)
                break
            except ValueError:
                continue
        else:
            return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _summarize_news(item: NewsItem, limit: int = 180) -> str:
    text = " ".join((item.content or item.title or "").split())
    return text[:limit]


def upsert_news_items(session: Session, items: list[NewsItem]) -> int:
    inserted = 0
    existing_urls = {
        str(url)
        for url in session.scalars(select(NewsRecord.url).where(NewsRecord.url.in_([i.url for i in items if i.url]))).all()
    }
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    for item in items:
        if not item.url or item.url in existing_urls:
            continue
        record = NewsRecord(
            title=item.title[:512],
            url=item.url,
            publish_time=_parse_news_datetime(item.publish_time),
            source=item.source[:256],
            content=item.content,
            summary=_summarize_news(item),
            raw_html=item.raw_html,
            metadata_json=json.dumps(item.metadata or {}, ensure_ascii=False),
            crawled_at=now,
        )
        session.add(record)
        existing_urls.add(item.url)
        inserted += 1
    session.flush()
    return inserted


def list_recent_news(
    session: Session,
    *,
    days: int | None = 7,
    source: str | None = None,
    limit: int = 500,
) -> list[NewsRecord]:
    stmt = select(NewsRecord)
    if days and days > 0:
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
        stmt = stmt.where(NewsRecord.publish_time >= cutoff)
    if source and source != "全部":
        stmt = stmt.where(NewsRecord.source == source)
    stmt = stmt.order_by(NewsRecord.publish_time.desc().nullslast(), NewsRecord.crawled_at.desc()).limit(limit)
    return list(session.scalars(stmt).all())


def list_news_sources(session: Session) -> list[str]:
    stmt = select(NewsRecord.source).where(NewsRecord.source != "").distinct().order_by(NewsRecord.source.asc())
    return [str(source) for source in session.scalars(stmt).all()]
