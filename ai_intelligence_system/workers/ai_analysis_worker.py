"""在 QThread 中执行 DeepSeek 分析并可选入库。"""

from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any, cast

from loguru import logger
from PySide6.QtCore import QObject, Signal, Slot

from ai_intelligence_system.config.settings import AppSettings
from ai_intelligence_system.core import analyzer
from ai_intelligence_system.core.ai_analyzer import AiAnalyzer
from ai_intelligence_system.core.ai_client import DeepSeekClient
from ai_intelligence_system.core.analyzer import TimeRange
from ai_intelligence_system.core.data_collector import DataCollector
from ai_intelligence_system.core.crawler_factory import create_many
from ai_intelligence_system.core.base_crawler import NewsItem
from ai_intelligence_system.core import database as db
from ai_intelligence_system.models.intelligence_record import IntelligenceRecord


class CrawlPipelineWorker(QObject):
    """后台爬取新闻并实时推送步骤状态。"""

    step_changed = Signal(str, str, str)
    finished_ok = Signal(int)
    failed = Signal(str)
    log_line = Signal(str)

    def __init__(self, settings: AppSettings, days: int = 3) -> None:
        super().__init__()
        self._settings = settings
        self._days = max(1, days)

    @Slot()
    def run(self) -> None:
        try:
            self._emit_step("连接网站", "进行中", "准备连接已配置数据源")
            source_ids = self._settings.crawl_source_ids
            crawlers = create_many(source_ids, max_items=self._settings.crawl_max_items_per_source)
            for crawler in crawlers:
                self._emit_step(
                    "连接网站",
                    "进行中",
                    f"{crawler.source_name or crawler.source_id}｜{crawler.base_url or '未配置URL'}",
                )
            self._emit_step("连接网站", "成功", "、".join(source_ids) or "未配置")

            self._emit_step("请求新闻列表", "进行中", f"抓取最近 {self._days} 天新闻")
            collector = DataCollector(
                source_ids=source_ids,
                max_items_per_source=self._settings.crawl_max_items_per_source,
                incremental=True,
                progress_cb=self._on_collect_progress,
            )
            items = collector.collect(days=self._days)
            for item in items[:50]:
                self._emit_step(
                    "请求新闻列表",
                    "进行中",
                    f"文章：{item.title}｜{item.url}",
                )
            self._emit_step("请求新闻列表", "成功", f"获取 {len(items)} 条候选新闻")

            self._emit_step("解析新闻内容", "进行中", "正在整理正文与摘要")
            valid_items = [item for item in items if item.title and item.url]
            for item in valid_items[:30]:
                content_len = len(item.content or "")
                self._emit_step("解析新闻内容", "进行中", f"已解析：{item.title}｜正文 {content_len} 字")
            self._emit_step("解析新闻内容", "成功", f"有效新闻 {len(valid_items)} 条")

            self._emit_step("写入SQLite数据库", "进行中", "正在增量入库并按 URL 去重")
            engine = db.create_engine_for_path(self._settings.database_path)
            db.init_db(engine)
            factory = db.make_session_factory(engine)
            with db.session_scope(factory) as session:
                inserted = db.upsert_news_items(session, valid_items)
            self._emit_step("写入SQLite数据库", "成功", f"新增入库 {inserted} 条")

            self._emit_step("爬取完成", "成功", f"候选 {len(items)} 条，新增 {inserted} 条")
            self.finished_ok.emit(inserted)
        except Exception as exc:  # noqa: BLE001
            logger.exception("爬取流程失败")
            self._emit_step("爬取完成", "失败", str(exc))
            self.failed.emit(str(exc))

    def _emit_step(self, name: str, status: str, detail: str = "") -> None:
        line = f"{name}：{status} {detail}".strip()
        self.log_line.emit(line)
        self.step_changed.emit(name, status, detail)

    def _on_collect_progress(self, msg: str) -> None:
        """DataCollector 实时进度回调：让 UI 在长网络等待期间持续收到更新。"""
        self._emit_step("请求新闻列表", "进行中", msg)


def _with_heartbeat(emit, label: str, fn, interval: float = 10):
    """执行 fn（可能长时间阻塞）期间每隔 interval 秒通过 emit 上报一次心跳。"""
    started = time.monotonic()
    emit(f"已提交{label}请求，等待响应…")
    stop = threading.Event()

    def _beat() -> None:
        while not stop.wait(interval):
            emit(f"正在等待{label}响应… 已等待 {int(time.monotonic() - started)} 秒")

    th = threading.Thread(target=_beat, daemon=True)
    th.start()
    try:
        result = fn()
    finally:
        stop.set()
    emit(f"{label}响应完成，耗时 {int(time.monotonic() - started)} 秒。")
    return result


class NewsLoadWorker(QObject):
    """从 SQLite 加载新闻展示表。"""

    loaded = Signal(list, list)
    failed = Signal(str)

    def __init__(self, database_path: str, days: int = 7, source: str = "全部", limit: int = 500,
                 start_date: Any | None = None, end_date: Any | None = None) -> None:
        super().__init__()
        self._database_path = database_path
        self._days = days
        self._source = source
        self._limit = limit
        self._start_date = start_date
        self._end_date = end_date

    @Slot()
    def run(self) -> None:
        try:
            engine = db.create_engine_for_path(self._database_path)
            db.init_db(engine)
            factory = db.make_session_factory(engine)
            with db.session_scope(factory) as session:
                if self._start_date is not None and self._end_date is not None:
                    rows = db.list_news_by_date_range(
                        session,
                        start_date=self._start_date,
                        end_date=self._end_date,
                        source=self._source,
                        limit=self._limit,
                    )
                else:
                    rows = db.list_recent_news(session, days=self._days, source=self._source, limit=self._limit)
                sources = db.list_news_sources(session)
                out: list[dict[str, Any]] = []
                for row in rows:
                    out.append(
                        {
                            "id": row.id,
                            "title": row.title,
                            "url": row.url,
                            "publish_time": row.publish_time.isoformat() if row.publish_time else "",
                            "source": row.source,
                            "summary": row.summary,
                            "content": row.content,
                            "crawled_at": row.crawled_at.isoformat() if row.crawled_at else "",
                        }
                    )
            self.loaded.emit(out, sources)
        except Exception as exc:  # noqa: BLE001
            logger.exception("加载新闻失败")
            self.failed.emit(str(exc))


class RecentNewsAnalysisWorker(QObject):
    """基于 SQLite 最近新闻执行 AI 分析。"""

    finished_ok = Signal(dict)
    failed = Signal(str)
    log_line = Signal(str)

    def __init__(self, settings: AppSettings, days: int = 3, user_extra: str = "", persist: bool = True) -> None:
        super().__init__()
        self._settings = settings
        self._days = max(1, days)
        self._user_extra = user_extra
        self._persist = persist

    @Slot()
    def run(self) -> None:
        try:
            self.log_line.emit(f"从 SQLite 读取最近 {self._days} 天新闻作为 AI 输入…")
            engine = db.create_engine_for_path(self._settings.database_path)
            db.init_db(engine)
            factory = db.make_session_factory(engine)
            with db.session_scope(factory) as session:
                records = db.list_recent_news(session, days=self._days, limit=200)
            if not records:
                raise ValueError("SQLite 中没有可分析的最近新闻，请先执行爬取。")

            news_items = []
            for record in records:
                news_items.append(
                    NewsItem(
                        title=record.title,
                        url=record.url,
                        source=record.source,
                        publish_time=record.publish_time.isoformat() if record.publish_time else None,
                        content=record.content,
                        raw_html="",
                        metadata={"from_sqlite": True, "news_record_id": record.id},
                    )
                )

            ai = AiAnalyzer(
                api_key=self._settings.deepseek_api_key,
                base_url=self._settings.deepseek_base_url,
                model=self._settings.deepseek_model,
                system_prompt=self._settings.custom_system_prompt.strip() or None,
            )
            parsed = _with_heartbeat(
                self.log_line.emit,
                "DeepSeek 模型",
                lambda: ai.analyze(
                    news_items,
                    keywords=self._settings.industry_keywords,
                    time_range=analyzer.days_to_time_range(self._days),
                    extra_instruction=(
                        "请输出新闻摘要、行业趋势判断、潜在影响分析。"
                        + (f"\n补充要求：{self._user_extra}" if self._user_extra else "")
                    ),
                ),
            )
            if self._persist:
                self._save_to_db(parsed)
            self.finished_ok.emit(parsed)
        except Exception as exc:  # noqa: BLE001
            logger.exception("最近新闻 AI 分析失败")
            self.failed.emit(str(exc))

    def _save_to_db(self, parsed: dict[str, Any]) -> None:
        helper = AiAnalysisWorker(self._settings, user_extra="", time_range="3d", persist=True)
        helper._save_to_db(parsed)


class AiAnalysisWorker(QObject):
    """执行一次「手动分析」：调用模型 → 解析 JSON → 可选写入 SQLite。"""

    finished_ok = Signal(dict)  # 解析后的结构化 dict
    failed = Signal(str)
    log_line = Signal(str)

    def __init__(self, settings: AppSettings, user_extra: str, time_range: str, persist: bool = True) -> None:
        super().__init__()
        self._settings = settings
        self._user_extra = user_extra
        self._time_range = time_range  # "24h" | "3d" | "7d"
        self._persist = persist

    @Slot()
    def run(self) -> None:
        try:
            self.log_line.emit("开始定向爬取权威网站…")
            tr = self._time_range if self._time_range in ("24h", "3d", "7d", "15d", "30d") else "24h"
            days_map = {"24h": 1, "3d": 3, "7d": 7, "15d": 15, "30d": 30}
            collector = DataCollector(
                source_ids=self._settings.crawl_source_ids,
                max_items_per_source=self._settings.crawl_max_items_per_source,
            )
            news_items = collector.collect(days=days_map.get(tr, 7))
            self.log_line.emit(f"采集完成，共 {len(news_items)} 条新闻。")
            if not news_items:
                raise ValueError(
                    "未采集到任何新闻，请检查网络或 crawl_source_ids 配置（默认 ndrc）"
                )

            self.log_line.emit("开始基于本地数据调用 DeepSeek 分析…")
            ai = AiAnalyzer(
                api_key=self._settings.deepseek_api_key,
                base_url=self._settings.deepseek_base_url,
                model=self._settings.deepseek_model,
                system_prompt=self._settings.custom_system_prompt.strip() or None,
            )
            parsed = _with_heartbeat(
                self.log_line.emit,
                "DeepSeek 模型",
                lambda: ai.analyze(
                    news_items,
                    keywords=self._settings.industry_keywords,
                    time_range=cast(TimeRange, tr),
                    extra_instruction=self._user_extra,
                ),
            )
            self.log_line.emit("模型返回已解析为 JSON。")

            if self._persist:
                self._save_to_db(parsed)
                self.log_line.emit("已写入本地数据库。")

            self.finished_ok.emit(parsed)
        except Exception as exc:  # noqa: BLE001
            logger.exception("AI 分析失败")
            self.failed.emit(str(exc))

    def _save_to_db(self, parsed: dict[str, Any]) -> None:
        engine = db.create_engine_for_path(self._settings.database_path)
        db.init_db(engine)
        factory = db.make_session_factory(engine)
        now = datetime.now(timezone.utc)
        title = str(parsed.get("title") or "未命名情报")
        source = str(parsed.get("source") or "")
        source_url = str(
            parsed.get("source_url")
            or parsed.get("url")
            or parsed.get("link")
            or parsed.get("reference_url")
            or ""
        ).strip()
        summary = str(parsed.get("summary") or "")
        impact = str(parsed.get("impact") or "")
        score = float(parsed.get("score") or 0)
        stage = str(parsed.get("stage") or "")
        tags = analyzer.flatten_tags(parsed.get("tags"))
        analysis = str(parsed.get("analysis") or "")
        raw_json = json.dumps(parsed, ensure_ascii=False)

        record = IntelligenceRecord(
            timestamp=now,
            title=title[:512],
            source=source[:256],
            source_url=source_url,
            content=analysis,
            summary=summary,
            impact=impact,
            score=score,
            stage=stage[:128],
            tags=tags,
            raw_json=raw_json,
        )
        with db.session_scope(factory) as session:
            db.insert_record(session, record)


class DashboardLoadWorker(QObject):
    """加载仪表盘与表格所需的最近记录。"""

    loaded = Signal(list)  # list[dict] 轻量序列化
    failed = Signal(str)

    def __init__(self, database_path: str, limit: int = 50) -> None:
        super().__init__()
        self._database_path = database_path
        self._limit = limit

    @Slot()
    def run(self) -> None:
        try:
            engine = db.create_engine_for_path(self._database_path)
            db.init_db(engine)
            factory = db.make_session_factory(engine)
            with db.session_scope(factory) as session:
                rows = db.list_recent_records(session, self._limit)
                # 必须在 Session 仍打开时把字段拷成 dict，否则 commit/close 后会话过期触发 DetachedInstanceError
                out: list[dict[str, Any]] = []
                for r in rows:
                    out.append(
                        {
                            "id": r.id,
                            "timestamp": r.timestamp.isoformat() if r.timestamp else "",
                            "title": r.title,
                            "source": r.source,
                            "source_url": r.source_url,
                            "summary": r.summary,
                            "content": r.content,
                            "score": r.score,
                            "stage": r.stage,
                            "tags": r.tags,
                            "raw_json": r.raw_json,
                        }
                    )
            self.loaded.emit(out)
        except Exception as exc:  # noqa: BLE001
            logger.exception("加载记录失败")
            self.failed.emit(str(exc))


class SettingsSaveWorker(QObject):
    """在后台线程写配置文件，避免磁盘抖动阻塞 UI（可选）。"""

    finished_ok = Signal()
    failed = Signal(str)

    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self._settings = settings

    @Slot()
    def run(self) -> None:
        try:
            from ai_intelligence_system.config.settings import save_settings

            save_settings(self._settings)
            self.finished_ok.emit()
        except Exception as exc:  # noqa: BLE001
            logger.exception("保存配置失败")
            self.failed.emit(str(exc))


class EmailSendWorker(QObject):
    """后台发送邮件，支持失败重试。"""

    finished_ok = Signal()
    failed = Signal(str)
    log_line = Signal(str)

    def __init__(self, settings: AppSettings, subject: str, html: str, retries: int = 2) -> None:
        super().__init__()
        self._settings = settings
        self._subject = subject
        self._html = html
        self._retries = retries

    @Slot()
    def run(self) -> None:
        from ai_intelligence_system.core.email_sender import send_html_email

        last_error = ""
        for attempt in range(1, self._retries + 2):
            try:
                self.log_line.emit(f"正在发送邮件，第 {attempt} 次尝试…")
                logger.info(
                    "邮件发送尝试：attempt={} retries={} subject={} recipients={}",
                    attempt,
                    self._retries,
                    self._subject,
                    len(self._settings.mail_recipients),
                )
                send_html_email(
                    host=self._settings.smtp_host,
                    port=int(self._settings.smtp_port),
                    user=self._settings.smtp_user,
                    password=self._settings.smtp_password,
                    recipients=self._settings.mail_recipients,
                    subject=self._subject,
                    html_body=self._html,
                    use_ssl=self._settings.smtp_use_ssl,
                )
                self.log_line.emit("邮件发送成功。")
                self.finished_ok.emit()
                return
            except Exception as exc:  # noqa: BLE001
                last_error = str(exc)
                logger.exception("发送邮件失败，第 {} 次尝试", attempt)
                self.log_line.emit(f"邮件发送失败，第 {attempt} 次尝试：{last_error}")
                if attempt <= self._retries:
                    time.sleep(3)
        self.failed.emit(last_error or "邮件发送失败")
        logger.error("邮件最终发送失败：subject={} error={}", self._subject, last_error)


class ExportCsvWorker(QObject):
    """导出全部情报为 CSV（UTF-8 BOM，便于 Excel 打开）。"""

    finished_ok = Signal(str)
    failed = Signal(str)

    def __init__(self, database_path: str, target_path: str) -> None:
        super().__init__()
        self._database_path = database_path
        self._target_path = target_path

    @Slot()
    def run(self) -> None:
        import csv

        try:
            engine = db.create_engine_for_path(self._database_path)
            db.init_db(engine)
            factory = db.make_session_factory(engine)
            with db.session_scope(factory) as session:
                rows = db.list_all_records(session)
                row_tuples: list[tuple[Any, ...]] = []
                for r in rows:
                    row_tuples.append(
                        (
                            r.id,
                            r.timestamp.isoformat() if r.timestamp else "",
                            r.title,
                            r.source,
                            r.source_url,
                            r.summary,
                            r.impact,
                            r.score,
                            r.stage,
                            r.tags,
                        )
                    )
            headers = [
                "id",
                "timestamp",
                "title",
                "source",
                "source_url",
                "summary",
                "impact",
                "score",
                "stage",
                "tags",
            ]
            with open(self._target_path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(headers)
                for tup in row_tuples:
                    w.writerow(list(tup))
            self.finished_ok.emit(self._target_path)
        except Exception as exc:  # noqa: BLE001
            logger.exception("导出 CSV 失败")
            self.failed.emit(str(exc))


class TestConnectionWorker(QObject):
    """测试 DeepSeek 连接：发送最小请求并回显模型回复。"""

    finished_ok = Signal(str)
    failed = Signal(str)

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        super().__init__()
        self._api_key = api_key
        self._base_url = base_url
        self._model = model

    @Slot()
    def run(self) -> None:
        try:
            client = DeepSeekClient(
                api_key=self._api_key,
                base_url=self._base_url,
                model=self._model,
                timeout_sec=30,
            )
            data = client.chat_completion(
                [{"role": "user", "content": "请只回复两个字：正常"}],
                temperature=0.0,
                response_format_json=False,
            )
            content = (client.extract_message_content(data) or "").strip() or "（空回复）"
            self.finished_ok.emit(content)
        except Exception as exc:  # noqa: BLE001
            logger.exception("模型连接测试失败")
            self.failed.emit(str(exc))
