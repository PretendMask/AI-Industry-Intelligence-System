"""定时任务服务：在专用 QThread 内按设置时间触发任务信号。"""

from __future__ import annotations

from datetime import datetime

from loguru import logger
from PySide6.QtCore import QObject, QTimer, Signal, Slot

from ai_intelligence_system.config.settings import AppSettings, SchedulerSlot


class SchedulerService(QObject):
    """使用 QTimer 轮询当前时间，并通过信号通知主线程启动任务。"""

    tick = Signal(str)
    job_due = Signal(str)
    job_failed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._timer: QTimer | None = None
        self._settings: AppSettings | None = None
        self._last_run: dict[str, str] = {}

    @Slot(object)
    def configure(self, settings: AppSettings) -> None:
        self._settings = settings
        self._last_run.clear()
        self.tick.emit("scheduler_configured")
        logger.info("调度配置已更新：{}", self._describe_schedule())
        if self._timer is not None:
            self._on_timer_tick()

    @Slot()
    def start(self) -> None:
        if self._timer is not None:
            return
        self._timer = QTimer(self)
        self._timer.setInterval(30 * 1000)
        self._timer.timeout.connect(self._on_timer_tick)
        self._timer.start()
        logger.info("调度服务已启动：每 30 秒检查一次定时任务")
        self.tick.emit("scheduler_started")
        self._on_timer_tick()

    @Slot()
    def stop(self) -> None:
        if self._timer is None:
            return
        self._timer.stop()
        self._timer.deleteLater()
        self._timer = None
        logger.info("调度服务已停止")
        self.tick.emit("scheduler_stopped")

    @Slot()
    def _on_timer_tick(self) -> None:
        try:
            settings = self._settings
            if settings is None:
                self.tick.emit("scheduler_waiting_for_config")
                return
            now = datetime.now()
            current_hm = now.strftime("%H:%M")
            current_day = now.strftime("%Y-%m-%d")
            slots = {
                "morning": settings.scheduler_morning,
                "noon": settings.scheduler_noon,
                "evening": settings.scheduler_evening,
            }
            for name, slot in slots.items():
                if self._is_due(name, slot, current_hm, current_day):
                    self._last_run[name] = current_day
                    logger.info("定时任务触发：{} {}", name, current_hm)
                    self.tick.emit(f"scheduler_job_due:{name}@{current_hm}")
                    self.job_due.emit(name)
        except Exception as exc:  # noqa: BLE001
            logger.exception("调度检查异常: {}", exc)
            self.job_failed.emit(str(exc))

    def _is_due(self, name: str, slot: SchedulerSlot, current_hm: str, current_day: str) -> bool:
        if not slot.enabled:
            return False
        if slot.time.strip() != current_hm:
            return False
        return self._last_run.get(name) != current_day

    def _describe_schedule(self) -> str:
        if self._settings is None:
            return "未配置"
        return ", ".join(
            f"{name}={'开启' if slot.enabled else '关闭'}@{slot.time}"
            for name, slot in {
                "morning": self._settings.scheduler_morning,
                "noon": self._settings.scheduler_noon,
                "evening": self._settings.scheduler_evening,
            }.items()
        )
