"""在 QThread 中执行 DeepSeek 分析并可选入库。"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any, cast

from loguru import logger
from PySide6.QtCore import QObject, Signal, Slot

from ai_intelligence_system.config.settings import AppSettings
from ai_intelligence_system.core.ai_client import DeepSeekClient
from ai_intelligence_system.core import analyzer
from ai_intelligence_system.core.analyzer import TimeRange
from ai_intelligence_system.core import database as db
from ai_intelligence_system.models.intelligence_record import IntelligenceRecord


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
            self.log_line.emit("开始调用 DeepSeek…")
            system = (
                self._settings.custom_system_prompt.strip()
                or analyzer.DEFAULT_SYSTEM_PROMPT
            )
            tr = self._time_range if self._time_range in ("24h", "3d", "7d") else "24h"
            user_msg = analyzer.build_user_prompt(
                keywords=self._settings.industry_keywords,
                time_range=cast(TimeRange, tr),
                extra_instruction=self._user_extra,
            )
            client = DeepSeekClient(
                api_key=self._settings.deepseek_api_key,
                base_url=self._settings.deepseek_base_url,
                model=self._settings.deepseek_model,
            )
            data = client.chat_completion(
                [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_msg},
                ]
            )
            content = client.extract_message_content(data)
            parsed = analyzer.parse_analysis_json(content)
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
