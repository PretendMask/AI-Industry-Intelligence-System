"""SQLite 数据库：引擎、会话与初始化。"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from ai_intelligence_system.models.intelligence_record import Base, IntelligenceRecord


def create_engine_for_path(database_path: str) -> Engine:
    url = f"sqlite:///{database_path}"
    return create_engine(url, echo=False, future=True)


def init_db(engine: Engine) -> None:
    Base.metadata.create_all(engine)
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
