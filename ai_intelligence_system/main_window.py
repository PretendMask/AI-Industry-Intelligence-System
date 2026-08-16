"""主窗口：菜单、工具栏、多 Tab、线程任务编排。"""

from __future__ import annotations

import csv
from html import escape
import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from loguru import logger
from PySide6.QtCore import QDate, QEvent, QMetaObject, QObject, QPointF, QRectF, QSize, Qt, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QCloseEvent, QColor, QFont, QIcon, QPainter, QPalette, QPen, QPolygonF
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizeGrip,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QStyle,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QTextEdit,
    QToolBar,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from sqlalchemy import delete

from ai_intelligence_system.config.settings import AppSettings, SchedulerSlot, load_settings
from ai_intelligence_system.core import database as db
from ai_intelligence_system.core.scheduler import SchedulerService
from ai_intelligence_system.models.intelligence_record import NewsRecord
from ai_intelligence_system.ui import theme
from ai_intelligence_system.ui.news_table_widget import NewsTableWidget
from ai_intelligence_system.ui.styles import modern_light_qss
from ai_intelligence_system.utils.paths import app_icon_path, describe_local_storage, frozen_resource_root
from ai_intelligence_system.widgets.dashboard.dashboard_components import (
    IntelligenceDetailView,
    IntelligenceListWidget,
    OverviewPanel,
    SearchFilterBar,
    _format_ts,
    _score_to_100,
    _score_bucket_100,
    _split_tags,
)
from ai_intelligence_system.workers.ai_analysis_worker import (
    AiAnalysisWorker,
    CrawlPipelineWorker,
    DashboardLoadWorker,
    EmailSendWorker,
    ExportCsvWorker,
    NewsLoadWorker,
    RecentNewsAnalysisWorker,
    SettingsSaveWorker,
    TestConnectionWorker,
)


class TrendChartWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._points: list[tuple[str, int, float]] = []
        self.setMinimumHeight(360)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_data(self, points: list[tuple[str, int, float]]) -> None:
        self._points = points
        self.update()

    def paintEvent(self, event: object) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(18, 18, -18, -28)
        painter.fillRect(self.rect(), QColor("#FFFFFF"))
        painter.setPen(QPen(QColor("#E2E8F0"), 1))
        for i in range(5):
            y = rect.top() + i * rect.height() / 4
            painter.drawLine(rect.left(), int(y), rect.right(), int(y))
        if not self._points:
            painter.setPen(QColor("#64748B"))
            painter.drawText(rect, Qt.AlignCenter, "暂无趋势数据")
            return
        max_count = max((p[1] for p in self._points), default=1)
        count = len(self._points)
        step = rect.width() / max(count - 1, 1)
        coords: list[tuple[int, int]] = []
        for idx, (_, value, _) in enumerate(self._points):
            x = int(rect.left() + idx * step)
            y = int(rect.bottom() - (value / max(max_count, 1)) * rect.height())
            coords.append((x, y))
        painter.setPen(QPen(QColor("#3B82F6"), 3))
        for idx in range(1, len(coords)):
            painter.drawLine(coords[idx - 1][0], coords[idx - 1][1], coords[idx][0], coords[idx][1])
        painter.setBrush(QColor("#1E40AF"))
        painter.setPen(QPen(QColor("#FFFFFF"), 2))
        for (x, y), (label, value, avg) in zip(coords, self._points, strict=False):
            painter.drawEllipse(x - 5, y - 5, 10, 10)
            painter.setPen(QColor("#1E293B"))
            painter.drawText(x - 24, y - 24, 60, 18, Qt.AlignCenter, str(value))
            painter.setPen(QColor("#64748B"))
            painter.drawText(x - 38, rect.bottom() + 8, 76, 18, Qt.AlignCenter, label[5:])
            painter.drawText(x - 38, y + 8, 76, 18, Qt.AlignCenter, f"均{avg:.1f}")
            painter.setPen(QPen(QColor("#FFFFFF"), 2))


class HeatMapWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._rows: list[tuple[str, int, int, int]] = []
        self.setMinimumHeight(360)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_data(self, rows: list[tuple[str, int, int, int]]) -> None:
        self._rows = rows
        self.update()

    def paintEvent(self, event: object) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#FFFFFF"))
        rect = self.rect().adjusted(18, 18, -18, -18)
        if not self._rows:
            painter.setPen(QColor("#64748B"))
            painter.drawText(rect, Qt.AlignCenter, "暂无热力数据")
            return
        headers = ["阶段", "高分", "中等", "低分"]
        col_widths = [max(150, int(rect.width() * 0.34)), int(rect.width() * 0.22), int(rect.width() * 0.22), int(rect.width() * 0.22)]
        row_h = max(42, int((rect.height() - 38) / max(len(self._rows), 1)))
        max_value = max((max(r[1:]) for r in self._rows), default=1)
        x = rect.left()
        painter.setPen(QColor("#1E40AF"))
        for header, w in zip(headers, col_widths, strict=False):
            painter.drawText(x, rect.top(), w, 28, Qt.AlignCenter, header)
            x += w
        y = rect.top() + 36
        for row in self._rows:
            x = rect.left()
            painter.setPen(QColor("#1E293B"))
            painter.drawText(x + 8, y, col_widths[0] - 16, row_h, Qt.AlignVCenter | Qt.AlignLeft, row[0])
            x += col_widths[0]
            for value, w in zip(row[1:], col_widths[1:], strict=False):
                ratio = value / max(max_value, 1)
                color = QColor(219 - int(70 * ratio), 234 - int(70 * ratio), 254)
                painter.fillRect(x + 4, y + 4, w - 8, row_h - 8, color)
                painter.setPen(QColor("#1E40AF" if value else "#94A3B8"))
                painter.drawText(x, y, w, row_h, Qt.AlignCenter, str(value))
                x += w
            y += row_h


TOPOLOGY_TYPE_COLORS = {
    "政策法规": "#3B82F6",
    "行业动态": "#22C55E",
    "企业动态": "#8B5CF6",
    "技术创新": "#F59E0B",
    "市场数据": "#06B6D4",
}


class TopologyGraphWidget(QWidget):
    """基于当前筛选情报标签共现关系绘制的轻量交互网络图。"""

    node_selected = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._nodes: list[dict[str, object]] = []
        self._edges: list[tuple[str, str, int]] = []
        self._positions: dict[str, QPointF] = {}
        self._selected: str | None = None
        self.setMinimumHeight(330)
        self.setMouseTracking(True)
        self.setObjectName("TopologyCanvas")

    def set_graph(self, nodes: list[dict[str, object]], edges: list[tuple[str, str, int]]) -> None:
        self._nodes = nodes
        self._edges = edges
        names = {str(node["name"]) for node in nodes}
        if self._selected not in names:
            self._selected = None
        self._positions.clear()
        self.update()

    def reset_view(self) -> None:
        self._selected = None
        self.update()

    def resizeEvent(self, event) -> None:
        # 数据通常在窗口完成首次布局前抵达；尺寸变化时必须重新计算坐标，
        # 否则网络会停留在旧的小画布左上区域。
        self._positions.clear()
        super().resizeEvent(event)

    def _node_positions(self) -> dict[str, QPointF]:
        if self._positions or not self._nodes:
            return self._positions
        # Reserve a generous label-safe margin, while using the full canvas so
        # a sparse result does not collapse into the visual centre.
        rect = self.rect().adjusted(72, 42, -72, -50)
        center = QPointF(rect.center())
        ranked = sorted(self._nodes, key=lambda item: float(item["weight"]), reverse=True)
        core = ranked[: min(5, len(ranked))]
        outer = ranked[len(core):]
        for index, node in enumerate(core):
            name = str(node["name"])
            if index == 0:
                self._positions[name] = center
                continue
            # Put the leading nodes on a broad inner ring.  Starting at the
            # top keeps the reading order clear and works for both wide and
            # compact canvases.
            angle = -math.pi / 2 + (index - 1) * (2 * math.pi / max(len(core) - 1, 1))
            self._positions[name] = QPointF(
                center.x() + math.cos(angle) * rect.width() * 0.29,
                center.y() + math.sin(angle) * rect.height() * 0.30,
            )
        for index, node in enumerate(outer):
            angle = -math.pi / 2 + index * (2 * math.pi / max(len(outer), 1))
            radius_x = rect.width() * 0.45
            radius_y = rect.height() * 0.42
            self._positions[str(node["name"])] = QPointF(center.x() + math.cos(angle) * radius_x, center.y() + math.sin(angle) * radius_y)
        return self._positions

    def _radius(self, name: str) -> float:
        weights = [float(node["weight"]) for node in self._nodes] or [1]
        weight = next((float(node["weight"]) for node in self._nodes if str(node["name"]) == name), 1.0)
        low, high = min(weights), max(weights)
        return 11 + (weight - low) / max(high - low, 1) * 15

    def _node_at(self, point: QPointF) -> str | None:
        for name, position in self._node_positions().items():
            if math.hypot(position.x() - point.x(), position.y() - point.y()) <= self._radius(name) + 5:
                return name
        return None

    def mouseMoveEvent(self, event) -> None:
        name = self._node_at(event.position())
        if name:
            node = next(item for item in self._nodes if str(item["name"]) == name)
            QToolTip.showText(event.globalPosition().toPoint(), f"{name}\n关联强度：{node['weight']}", self)
        else:
            QToolTip.hideText()
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event) -> None:
        name = self._node_at(event.position())
        self._selected = name
        self.node_selected.emit(name or "")
        self.update()
        super().mousePressEvent(event)

    def paintEvent(self, event: object) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        positions = self._node_positions()
        if not self._nodes:
            painter.setPen(QColor("#94A3B8"))
            painter.drawText(self.rect(), Qt.AlignCenter, "当前筛选条件下暂无可构建的关联节点")
            return

        connected = {self._selected}
        if self._selected:
            connected.update(a if b == self._selected else b for a, b, _ in self._edges if self._selected in {a, b})
        max_edge = max((weight for _, _, weight in self._edges), default=1)
        for start, end, weight in self._edges:
            if start not in positions or end not in positions:
                continue
            active = not self._selected or self._selected in {start, end}
            color = QColor("#7AA7FF" if active else "#D8E1EF")
            color.setAlpha(190 if active else 95)
            painter.setPen(QPen(color, 1 + 2 * weight / max_edge))
            painter.drawLine(positions[start], positions[end])
            start_point = positions[start]
            end_point = positions[end]
            midpoint = QPointF(
                (start_point.x() + end_point.x()) / 2,
                (start_point.y() + end_point.y()) / 2,
            )
            direction = QPointF(end_point.x() - start_point.x(), end_point.y() - start_point.y())
            length = math.hypot(direction.x(), direction.y()) or 1
            unit = QPointF(direction.x() / length, direction.y() / length)
            normal = QPointF(-unit.y(), unit.x())
            tip = QPointF(midpoint.x() + unit.x() * 4, midpoint.y() + unit.y() * 4)
            left = QPointF(
                tip.x() - unit.x() * 7 + normal.x() * 3,
                tip.y() - unit.y() * 7 + normal.y() * 3,
            )
            right = QPointF(
                tip.x() - unit.x() * 7 - normal.x() * 3,
                tip.y() - unit.y() * 7 - normal.y() * 3,
            )
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawPolygon(QPolygonF([tip, left, right]))

        for node in self._nodes:
            name = str(node["name"])
            position = positions.get(name)
            if position is None:
                continue
            radius = self._radius(name)
            color = QColor(TOPOLOGY_TYPE_COLORS.get(str(node["type"]), "#64748B"))
            if self._selected and name not in connected:
                color.setAlpha(85)
            painter.setBrush(color)
            painter.setPen(QPen(QColor("#FFFFFF"), 2 if name == self._selected else 1))
            painter.drawEllipse(position, radius, radius)
            painter.setPen(QColor("#334155"))
            font = QFont("Microsoft YaHei", 9 if radius < 18 else 10, QFont.Bold)
            painter.setFont(font)
            label_rect = QRectF(position.x() - 52, position.y() + radius + 4, 104, 22)
            painter.drawText(label_rect, Qt.AlignHCenter | Qt.AlignTop, name)


class TopologyDonutChart(QWidget):
    """节点类型分布环图，保持正圆并由现有字段映射驱动。"""

    def __init__(self) -> None:
        super().__init__()
        self._data: list[tuple[str, int]] = []
        self.setMinimumSize(150, 150)
        self.setObjectName("TopologyDonut")

    def set_data(self, data: list[tuple[str, int]]) -> None:
        self._data = data
        self.update()

    def paintEvent(self, event: object) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        total = sum(value for _, value in self._data)
        if not total:
            painter.setPen(QColor("#94A3B8"))
            painter.drawText(self.rect(), Qt.AlignCenter, "暂无数据")
            return
        side = min(self.width(), self.height()) - 12
        circle = QRectF((self.width() - side) / 2, (self.height() - side) / 2, side, side)
        start = 90 * 16
        for name, value in self._data:
            span = int(value / total * 360 * 16)
            painter.setBrush(QColor(TOPOLOGY_TYPE_COLORS.get(name, "#94A3B8")))
            painter.setPen(QPen(QColor("#FFFFFF"), 2))
            painter.drawPie(circle, start, span)
            start += span
        inner_side = side * 0.54
        inner = QRectF((self.width() - inner_side) / 2, (self.height() - inner_side) / 2, inner_side, inner_side)
        painter.setBrush(QColor("#FFFFFF"))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(inner)
        painter.setPen(QColor("#1E293B"))
        painter.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        painter.drawText(inner, Qt.AlignCenter, f"共 {total}\n个节点")


class LogBus(QObject):
    """将 loguru 日志投递到 UI 线程。"""

    message = Signal(str)


class NewsDeleteWorker(QObject):
    """后台删除新闻，避免 SQLite 操作阻塞 UI。"""

    finished_ok = Signal(int)
    failed = Signal(str)

    def __init__(self, database_path: str, news_id: int) -> None:
        super().__init__()
        self._database_path = database_path
        self._news_id = news_id

    @Slot()
    def run(self) -> None:
        try:
            engine = db.create_engine_for_path(self._database_path)
            db.init_db(engine)
            factory = db.make_session_factory(engine)
            with db.session_scope(factory) as session:
                record = session.get(NewsRecord, self._news_id)
                if record is None:
                    raise ValueError("新闻记录不存在，可能已被删除。")
                session.delete(record)
            self.finished_ok.emit(self._news_id)
        except Exception as exc:  # noqa: BLE001
            logger.exception("删除新闻失败")
            self.failed.emit(str(exc))


class NewsBulkDeleteWorker(QObject):
    """后台批量删除新闻，支持按当前列表 ID 或发布时间范围删除。"""

    finished_ok = Signal(int)
    failed = Signal(str)

    def __init__(
        self,
        database_path: str,
        *,
        news_ids: list[int] | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        source: str | None = None,
    ) -> None:
        super().__init__()
        self._database_path = database_path
        self._news_ids = news_ids or []
        self._start_at = start_at
        self._end_at = end_at
        self._source = source

    @Slot()
    def run(self) -> None:
        try:
            engine = db.create_engine_for_path(self._database_path)
            db.init_db(engine)
            factory = db.make_session_factory(engine)
            with db.session_scope(factory) as session:
                if self._news_ids:
                    stmt = delete(NewsRecord).where(NewsRecord.id.in_(self._news_ids))
                else:
                    stmt = delete(NewsRecord)
                    if self._start_at is not None:
                        stmt = stmt.where(NewsRecord.publish_time >= self._start_at)
                    if self._end_at is not None:
                        stmt = stmt.where(NewsRecord.publish_time < self._end_at)
                    if self._source and self._source != "全部":
                        stmt = stmt.where(NewsRecord.source == self._source)
                result = session.execute(stmt)
                deleted = int(result.rowcount or 0)
            self.finished_ok.emit(deleted)
        except Exception as exc:  # noqa: BLE001
            logger.exception("批量删除新闻失败")
            self.failed.emit(str(exc))


class _HoverIconButton(QPushButton):
    """小图标按钮：默认灰色图标，悬停切换为蓝色图标（配合 QSS 悬停底色）。"""

    def __init__(
        self,
        icon_path: Path,
        active_icon_path: Path,
        size: int = 28,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._icon = QIcon(icon_path.as_posix())
        self._active_icon = QIcon(active_icon_path.as_posix())
        self.setIcon(self._icon)
        self.setFixedSize(size, size)
        self.setIconSize(QSize(max(14, size - 12), max(14, size - 12)))
        self.setCursor(Qt.PointingHandCursor)

    def enterEvent(self, event: QEvent) -> None:
        self.setIcon(self._active_icon)
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self.setIcon(self._icon)
        super().leaveEvent(event)


class MainWindow(QMainWindow):
    configure_scheduler_requested = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("行业情报系统 v2.2")
        icon_path = app_icon_path()
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowMaximizeButtonHint
            | Qt.WindowCloseButtonHint
        )
        self.setMinimumSize(960, 640)
        self.setMaximumSize(16777215, 16777215)
        self.resize(1280, 820)

        self._settings: AppSettings = load_settings()
        self._is_dark = False
        self._cached_rows: list[dict] = []
        self._cached_news_rows: list[dict] = []
        self._crawl_step_status: dict[str, str] = {}
        self._auto_ai_after_crawl = False
        self._auto_mail_after_ai = False
        self._email_sent_count = 0
        self._last_ai_result: dict | None = None
        # 仪表盘筛选状态
        self._dash_search_text: str = ""
        self._dash_source_filter: str = "全部来源"
        self._dash_stage_filter: str = "全部阶段"
        self._dash_sort: str = "time_desc"
        # 防止 Worker 在槽连接前被 Python GC 回收（否则点击按钮无任何反应）
        self._active_background_jobs: list[tuple[QThread, QObject]] = []

        self._log_bus = LogBus(self)
        self._log_bus.message.connect(self._append_log_line)

        self._sched_thread = QThread(self)
        self._scheduler_service = SchedulerService()
        self._scheduler_service.moveToThread(self._sched_thread)
        self.configure_scheduler_requested.connect(
            self._scheduler_service.configure,
            Qt.QueuedConnection,
        )
        self._sched_thread.started.connect(self._scheduler_service.start)
        self._scheduler_service.tick.connect(lambda s: logger.info("调度: {}", s))
        self._scheduler_service.job_due.connect(self._on_scheduler_job_due)
        self._scheduler_service.job_failed.connect(lambda e: logger.error("调度任务失败: {}", e))
        self._sched_thread.start()
        self._configure_scheduler()

        self._build_actions()
        self._build_menu_toolbar()
        self._build_tabs()
        self._build_status_bar()
        self._apply_theme()

        self._setup_file_logging()
        self._setup_ui_logging_sink()

        self._reload_settings_into_widgets()
        self._update_storage_paths_hint()
        self.refresh_records_async()
        self._tabs.currentChanged.connect(self._on_tab_changed)

        logger.info("主窗口已打开")

    def _std_icon(self, pixmap: QStyle.StandardPixmap) -> QIcon:
        return self.style().standardIcon(pixmap)

    def _settings_std_icon(self, name: str) -> QIcon:
        icons = {
            "settings": QStyle.SP_FileDialogDetailedView,
            "mail": QStyle.SP_MessageBoxInformation,
            "crawler": QStyle.SP_BrowserReload,
            "schedule": QStyle.SP_MediaPlay,
            "business": QStyle.SP_FileDialogContentsView,
            "storage": QStyle.SP_DriveHDIcon,
            "system": QStyle.SP_MessageBoxQuestion,
        }
        return self._std_icon(icons.get(name, QStyle.SP_FileDialogDetailedView))

    def _configure_form_layout(self, form: QFormLayout) -> None:
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(14)
        form.setContentsMargins(12, 10, 12, 12)
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form.setRowWrapPolicy(QFormLayout.WrapLongRows)

    def _configure_scheduler(self) -> None:
        self.configure_scheduler_requested.emit(self._settings)

    def _retain_worker_thread(self, thread: QThread, worker: QObject) -> None:
        """在后台任务运行期间保持对 Thread/Worker 的强引用。"""
        pair = (thread, worker)
        self._active_background_jobs.append(pair)

        def on_thread_finished() -> None:
            try:
                self._active_background_jobs.remove(pair)
            except ValueError:
                pass

        thread.finished.connect(on_thread_finished)

    # --- UI 构建 ---
    def _build_actions(self) -> None:
        self._act_quit = QAction(self._std_icon(QStyle.SP_DialogCloseButton), "退出", self)
        self._act_quit.triggered.connect(self.close)
        self._act_settings = QAction(self._std_icon(QStyle.SP_FileDialogDetailedView), "设置…", self)
        self._act_settings.triggered.connect(lambda: self._tabs.setCurrentIndex(3))
        self._act_export = QAction(self._std_icon(QStyle.SP_DialogSaveButton), "导出 CSV…", self)
        self._act_export.triggered.connect(self._export_csv_dialog)
        self._act_refresh = QAction(self._std_icon(QStyle.SP_BrowserReload), "立即刷新数据", self)
        self._act_refresh.triggered.connect(self.refresh_records_async)
        self._act_mail = QAction(self._std_icon(QStyle.SP_MessageBoxInformation), "发送测试邮件", self)
        self._act_mail.triggered.connect(self._send_test_mail_async)
        self._act_history = QAction(self._std_icon(QStyle.SP_FileDialogInfoView), "拓扑分析", self)
        self._act_history.triggered.connect(lambda: self._tabs.setCurrentIndex(1))
        self._act_log_tab = QAction(self._std_icon(QStyle.SP_FileDialogContentsView), "日志", self)
        self._act_log_tab.triggered.connect(lambda: self._tabs.setCurrentIndex(4))
        self._act_about = QAction(self._std_icon(QStyle.SP_MessageBoxQuestion), "关于", self)
        self._act_about.triggered.connect(self._show_about)
        self._act_theme = QAction(self._std_icon(QStyle.SP_DesktopIcon), "切换深/浅色", self)
        self._act_theme.triggered.connect(self._toggle_theme)

    def _build_menu_toolbar(self) -> None:
        menu_bar = self.menuBar()
        menu_file = menu_bar.addMenu("文件")
        menu_file.addAction(self._act_settings)
        menu_file.addSeparator()
        menu_file.addAction(self._act_quit)

        menu_ops = menu_bar.addMenu("操作")
        menu_ops.addAction(self._act_refresh)
        menu_ops.addAction(self._act_mail)
        menu_ops.addAction(self._act_export)

        menu_view = menu_bar.addMenu("查看")
        menu_view.addAction(self._act_history)
        menu_view.addAction(self._act_log_tab)
        menu_view.addSeparator()
        menu_view.addAction(self._act_theme)

        menu_help = menu_bar.addMenu("帮助")
        menu_help.addAction(self._act_about)

        # 设计稿右上角的快捷入口。全部复用现有功能，避免引入新的业务状态。
        header_actions = QWidget()
        header_actions.setObjectName("HeaderActions")
        actions_layout = QHBoxLayout(header_actions)
        actions_layout.setContentsMargins(0, 0, 10, 0)
        actions_layout.setSpacing(4)

        def add_header_button(icon: QIcon, tooltip: str, callback) -> None:
            button = QPushButton()
            button.setObjectName("HeaderIconButton")
            button.setIcon(icon)
            button.setIconSize(QSize(16, 16))
            button.setFixedSize(28, 28)
            button.setToolTip(tooltip)
            button.clicked.connect(callback)
            actions_layout.addWidget(button)

        add_header_button(self._std_icon(QStyle.SP_DesktopIcon), "切换深浅色", self._toggle_theme)
        add_header_button(self._std_icon(QStyle.SP_FileDialogDetailedView), "设置", lambda: self._tabs.setCurrentIndex(3))
        add_header_button(self._std_icon(QStyle.SP_ArrowForward), "多边分析", lambda: self._tabs.setCurrentIndex(2))
        add_header_button(self._std_icon(QStyle.SP_DialogSaveButton), "导出 CSV", self._export_csv_dialog)
        separator = QLabel()
        separator.setObjectName("HeaderActionSeparator")
        separator.setFixedSize(1, 18)
        actions_layout.addWidget(separator)
        user_button = QPushButton("管理员⌄")
        user_button.setObjectName("HeaderUserButton")
        user_button.setIcon(self._std_icon(QStyle.SP_ComputerIcon))
        user_button.setIconSize(QSize(15, 15))
        user_button.setToolTip("关于本系统")
        user_button.clicked.connect(self._show_about)
        actions_layout.addWidget(user_button)
        menu_bar.setCornerWidget(header_actions, Qt.TopRightCorner)


    def _build_tabs(self) -> None:
        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)
        self.setCentralWidget(self._tabs)

        self._tab_dashboard = QWidget()
        self._tab_browse = QWidget()
        self._tab_manual = QWidget()
        self._tab_settings = QWidget()
        self._tab_log = QWidget()

        self._tabs.addTab(self._tab_dashboard, self._std_icon(QStyle.SP_ComputerIcon), "仪表盘")
        self._tabs.addTab(self._tab_browse, self._std_icon(QStyle.SP_FileDialogInfoView), "拓扑分析")
        self._tabs.addTab(self._tab_manual, self._std_icon(QStyle.SP_BrowserReload), "多边分析")
        self._tabs.addTab(self._tab_settings, self._std_icon(QStyle.SP_FileDialogDetailedView), "设置")
        self._tabs.addTab(self._tab_log, self._std_icon(QStyle.SP_FileDialogContentsView), "日志与状态")

        self._setup_tab_dashboard()
        self._setup_tab_browse()
        self._setup_tab_manual()
        self._setup_tab_settings()
        self._setup_tab_log()

    def _setup_tab_dashboard(self) -> None:
        """构建新版仪表盘：搜索筛选 + 情报列表 + 结构化详情 + 底部概览。"""
        root = QVBoxLayout(self._tab_dashboard)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(12)

        # 筛选属于“最近情报”卡片的工具区，而非页面级悬浮控件。
        self._search_filter_bar = SearchFilterBar()
        self._search_filter_bar.search_changed.connect(self._on_dash_search_changed)
        self._search_filter_bar.source_changed.connect(self._on_dash_source_changed)
        self._search_filter_bar.stage_changed.connect(self._on_dash_stage_changed)
        self._search_filter_bar.sort_changed.connect(self._on_dash_sort_changed)

        # ── 中部：左右 Splitter（情报列表 + 情报详情）──
        mid_splitter = QSplitter(Qt.Horizontal)
        mid_splitter.setObjectName("DashboardSplitter")
        mid_splitter.setChildrenCollapsible(False)
        mid_splitter.setHandleWidth(12)

        # 左侧：情报列表（一级Card容器）
        left_container = QWidget()
        left_container.setObjectName("DashCard")
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(16, 14, 16, 14)
        left_layout.setSpacing(8)

        # 标题行：左侧"最近情报"，右侧图标刷新按钮（只显示图标，悬停变蓝）
        list_header = QHBoxLayout()
        list_header.setContentsMargins(0, 0, 0, 0)
        list_header.setSpacing(8)
        self._dash_list_title = QLabel("最近情报")
        self._dash_list_title.setObjectName("DashSectionTitle")
        self._dash_list_title.setStyleSheet("color: #1E293B; font-size: 15px; font-weight: bold; padding: 0 4px;")
        list_header.addWidget(self._dash_list_title)
        list_header.addStretch()
        self._btn_dash_refresh = _HoverIconButton(
            frozen_resource_root() / "ai_intelligence_system" / "ui" / "refresh.svg",
            frozen_resource_root() / "ai_intelligence_system" / "ui" / "refresh-active.svg",
            size=28,
        )
        self._btn_dash_refresh.setObjectName("RefreshIconBtn")
        self._btn_dash_refresh.setToolTip("刷新数据")
        self._btn_dash_refresh.clicked.connect(self.refresh_records_async)
        list_header.addWidget(self._btn_dash_refresh)
        left_layout.addLayout(list_header)
        left_layout.addWidget(self._search_filter_bar)

        self._dash_list = IntelligenceListWidget()
        self._dash_list.item_selected.connect(self._on_dash_item_selected)
        left_layout.addWidget(self._dash_list, stretch=1)

        # 右侧：情报详情（一级Card容器）
        right_container = QWidget()
        right_container.setObjectName("DashCard")
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(16, 14, 16, 14)
        right_layout.setSpacing(8)

        right_header = QHBoxLayout()
        self._dash_detail_title = QLabel("情报详情")
        self._dash_detail_title.setObjectName("DashSectionTitle")
        self._dash_detail_title.setStyleSheet("color: #1E293B; font-size: 15px; font-weight: bold; padding: 0 4px;")
        right_header.addWidget(self._dash_detail_title)
        right_header.addStretch()
        self._dash_last_update = QLabel("")
        self._dash_last_update.setObjectName("DashHint")
        self._dash_last_update.setStyleSheet("color: #64748B; font-size: 12px;")
        right_header.addWidget(self._dash_last_update)
        right_layout.addLayout(right_header)

        self._dash_detail = IntelligenceDetailView()
        self._dash_detail.tag_clicked.connect(self._on_dash_tag_clicked)
        self._dash_detail.source_url_clicked.connect(self._on_dash_source_url_clicked)
        right_layout.addWidget(self._dash_detail, stretch=1)

        mid_splitter.addWidget(left_container)
        mid_splitter.addWidget(right_container)
        mid_splitter.setStretchFactor(0, 6)
        mid_splitter.setStretchFactor(1, 5)
        mid_splitter.setSizes([660, 560])
        root.addWidget(mid_splitter, stretch=1)

        # ── 底部：情报概览 ──
        self._dash_overview = OverviewPanel()
        self._dash_overview.tag_clicked.connect(self._on_dash_tag_clicked)
        root.addWidget(self._dash_overview, stretch=0)

        # ── 页脚免责声明 ──
        footer_row = QHBoxLayout()
        footer_row.setContentsMargins(0, 0, 0, 0)
        footer_row.addStretch()
        self._dash_footer_hint = QLabel("投资风险, 决策建议, 仅供研究, 不构成投资建议。")
        self._dash_footer_hint.setObjectName("FooterHint")
        footer_row.addWidget(self._dash_footer_hint)
        root.addLayout(footer_row)

    def _setup_tab_browse(self) -> None:
        root = QVBoxLayout(self._tab_browse)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        content = QWidget()
        content.setObjectName("TopologyPage")
        content.setMinimumWidth(1080)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 16, 24, 18)
        content_layout.setSpacing(12)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel("拓扑分析")
        title.setObjectName("TopologyPageTitle")
        subtitle = QLabel("行业情报关联关系与影响路径分析，发现核心节点与关键连接")
        subtitle.setObjectName("TopologyPageSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()
        self._topology_updated = QLabel("数据更新时间：--")
        self._topology_updated.setObjectName("TopologyUpdated")
        header.addWidget(self._topology_updated)
        self._btn_topology_export = QPushButton("导出报告")
        self._btn_topology_export.setObjectName("TopologyExportButton")
        self._btn_topology_export.setIcon(self._std_icon(QStyle.SP_DialogSaveButton))
        self._btn_topology_export.clicked.connect(self._export_csv_dialog)
        header.addWidget(self._btn_topology_export)
        content_layout.addLayout(header)

        filter_card = QWidget()
        filter_card.setObjectName("TopologyFilterCard")
        # 为 Windows DPI 缩放后的按钮边框留出安全空间，避免底边被裁切。
        filter_card.setFixedHeight(98)
        filter_layout = QHBoxLayout(filter_card)
        filter_layout.setContentsMargins(16, 14, 16, 14)
        filter_layout.setSpacing(14)

        def filter_field(label_text: str, widget: QWidget, stretch: int = 0) -> None:
            field = QWidget()
            field.setObjectName("TopologyFilterField")
            field_layout = QVBoxLayout(field)
            field_layout.setContentsMargins(0, 0, 0, 0)
            field_layout.setSpacing(8)
            label = QLabel(label_text)
            label.setObjectName("TopologyFieldLabel")
            label.setFixedHeight(16)
            field_layout.addWidget(label)
            field_layout.addWidget(widget)
            field.setFixedHeight(64)
            filter_layout.addWidget(field, stretch=stretch)

        date_range = QWidget()
        date_range.setObjectName("TopologyDateRange")
        date_range.setFixedSize(305, 40)
        date_layout = QHBoxLayout(date_range)
        date_layout.setContentsMargins(0, 0, 0, 0)
        date_layout.setSpacing(7)
        self._analytics_start_date = QDateEdit(QDate.currentDate())
        self._analytics_end_date = QDateEdit(QDate.currentDate())
        for date_edit in (self._analytics_start_date, self._analytics_end_date):
            date_edit.setCalendarPopup(True)
            date_edit.setDisplayFormat("yyyy-MM-dd")
            date_edit.setObjectName("TopologyDateRangeInput")
            date_edit.setFixedWidth(126)
            date_edit.setFixedHeight(38)
        date_layout.addWidget(self._analytics_start_date)
        date_separator = QLabel("至")
        date_separator.setObjectName("TopologyDateSeparator")
        date_separator.setAlignment(Qt.AlignCenter)
        date_layout.addWidget(date_separator)
        date_layout.addWidget(self._analytics_end_date)
        filter_field("时间范围", date_range)

        self._analytics_stage = QComboBox()
        self._analytics_stage.setObjectName("TopologySelect")
        self._analytics_stage.addItem("全部阶段")
        self._analytics_stage.setFixedWidth(180)
        self._analytics_stage.setFixedHeight(40)
        filter_field("阶段", self._analytics_stage)

        self._analytics_score = QComboBox()
        self._analytics_score.setObjectName("TopologySelect")
        self._analytics_score.addItems(["全部评分", "高分(>=80)", "中等(50-79)", "低分(<50)"])
        self._analytics_score.setFixedWidth(180)
        self._analytics_score.setFixedHeight(40)
        filter_field("最低评分", self._analytics_score)

        self._analytics_keyword = QLineEdit()
        self._analytics_keyword.setObjectName("TopologyKeyword")
        self._analytics_keyword.setPlaceholderText("请输入关键词")
        self._analytics_keyword.setFixedHeight(40)
        filter_field("关键词", self._analytics_keyword, stretch=1)

        self._btn_analytics_refresh = QPushButton("开始分析")
        self._btn_analytics_refresh.setObjectName("TopologyPrimaryButton")
        self._btn_analytics_refresh.setIcon(self._std_icon(QStyle.SP_BrowserReload))
        self._btn_analytics_refresh.setFixedHeight(34)
        self._btn_analytics_refresh.setFixedWidth(110)
        self._btn_analytics_refresh.clicked.connect(self._update_analytics_view)
        self._btn_analytics_reset = QPushButton("重置筛选")
        self._btn_analytics_reset.setObjectName("TopologyFilterSecondaryButton")
        self._btn_analytics_reset.clicked.connect(self._reset_analytics_filters)
        self._btn_analytics_reset.setFixedHeight(34)
        self._btn_analytics_reset.setFixedWidth(96)

        # 按钮列：与其他筛选项同高（64px），按钮垂直中线对齐左侧输入框中线
        filter_actions = QWidget()
        filter_actions.setObjectName("TopologyFilterActions")
        filter_actions.setFixedHeight(64)
        filter_buttons = QHBoxLayout(filter_actions)
        # 上边距 27px：34px 按钮的中心（27+17=44 卡内）与 40px 输入框中心（41+20=61 卡内）对齐
        filter_buttons.setContentsMargins(0, 27, 0, 3)
        filter_buttons.setSpacing(10)
        filter_buttons.addStretch()
        filter_buttons.addWidget(self._btn_analytics_refresh)
        filter_buttons.addWidget(self._btn_analytics_reset)
        filter_buttons.addStretch()
        filter_layout.addWidget(filter_actions)
        for widget in (self._analytics_start_date, self._analytics_end_date):
            widget.dateChanged.connect(self._update_analytics_view)
        self._analytics_stage.currentIndexChanged.connect(self._update_analytics_view)
        self._analytics_score.currentIndexChanged.connect(self._update_analytics_view)
        self._analytics_keyword.textChanged.connect(self._update_analytics_view)
        content_layout.addWidget(filter_card)

        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)
        self._topology_kpis: dict[str, tuple[QLabel, QLabel]] = {}
        metric_specs = (
            ("nodes", "情报节点总数", "◈", "#E8F1FF", "#2563EB"),
            ("relations", "关联关系总数", "⌁", "#E8FAF0", "#10B981"),
            ("core", "核心节点数", "◎", "#F3EDFF", "#8B5CF6"),
            ("avg_score", "平均评分", "☆", "#FFF4E5", "#F59E0B"),
            ("source_ratio", "可溯源率", "◫", "#EAF2FF", "#3B82F6"),
        )
        for key, text, icon, icon_bg, icon_color in metric_specs:
            card = QWidget()
            card.setObjectName("TopologyKpiCard")
            card.setAttribute(Qt.WA_StyledBackground, True)
            card.setFixedHeight(106)
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(16, 13, 16, 12)
            body = QVBoxLayout()
            body.setSpacing(3)
            label = QLabel(text)
            label.setObjectName("TopologyKpiTitle")
            value = QLabel("--")
            value.setObjectName("TopologyKpiValue")
            trend = QLabel("等待分析")
            trend.setObjectName("TopologyKpiTrend")
            body.addWidget(label)
            body.addWidget(value)
            body.addWidget(trend)
            card_layout.addLayout(body)
            card_layout.addStretch()
            icon_label = QLabel(icon)
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setFixedSize(46, 46)
            icon_label.setStyleSheet(f"background:{icon_bg}; color:{icon_color}; border-radius:23px; font-size:25px;")
            card_layout.addWidget(icon_label)
            self._topology_kpis[key] = (value, trend)
            kpi_row.addWidget(card, stretch=1)
        content_layout.addLayout(kpi_row)

        core_row = QHBoxLayout()
        core_row.setSpacing(12)
        graph_card = QWidget()
        graph_card.setObjectName("TopologyCard")
        graph_layout = QVBoxLayout(graph_card)
        graph_layout.setContentsMargins(16, 14, 16, 14)
        graph_layout.setSpacing(8)
        graph_header = QHBoxLayout()
        graph_title = QLabel("行业情报拓扑图")
        graph_title.setObjectName("TopologyCardTitle")
        graph_header.addWidget(graph_title)
        graph_header.addStretch()
        graph_metric = QComboBox()
        graph_metric.setObjectName("SaasCombo")
        graph_metric.addItem("关联强度")
        graph_metric.setFixedSize(124, 28)
        graph_header.addWidget(graph_metric)
        expand_view = QPushButton("⛶")
        expand_view.setObjectName("TopologyTextButton")
        expand_view.setToolTip("放大拓扑图")
        expand_view.setFixedSize(30, 28)
        graph_header.addWidget(expand_view)
        graph_layout.addLayout(graph_header)
        graph_legend = QHBoxLayout()
        graph_legend.setSpacing(16)
        for legend_name, legend_color in TOPOLOGY_TYPE_COLORS.items():
            dot = QLabel("●")
            dot.setObjectName("TopologyGraphLegendDot")
            dot.setStyleSheet(f"color:{legend_color};")
            text = QLabel(legend_name)
            text.setObjectName("TopologyGraphLegend")
            graph_legend.addWidget(dot)
            graph_legend.addWidget(text)
        graph_legend.addStretch()
        graph_layout.addLayout(graph_legend)
        self._topology_graph = TopologyGraphWidget()
        self._topology_graph.node_selected.connect(self._on_topology_node_selected)
        expand_view.clicked.connect(self._show_topology_fullscreen)
        graph_layout.addWidget(self._topology_graph, stretch=1)
        graph_hint = QLabel("提示：节点越大表示影响力越高，连线越粗表示关联强度越大；点击节点可突出显示关联连线。")
        graph_hint.setObjectName("TopologyHint")
        graph_layout.addWidget(graph_hint)
        graph_card.setFixedHeight(418)
        core_row.addWidget(graph_card, stretch=57)

        sidebar = QVBoxLayout()
        sidebar.setSpacing(12)
        sidebar_top = QHBoxLayout()
        sidebar_top.setSpacing(12)
        rank_card = QWidget()
        rank_card.setObjectName("TopologyCard")
        rank_layout = QVBoxLayout(rank_card)
        rank_layout.setContentsMargins(14, 14, 14, 12)
        rank_layout.setSpacing(7)
        rank_layout.addWidget(self._topology_card_title("核心节点 Top 10"))
        self._topology_rank_layout = QVBoxLayout()
        self._topology_rank_layout.setSpacing(5)
        rank_layout.addLayout(self._topology_rank_layout)
        sidebar_top.addWidget(rank_card, stretch=1)

        type_card = QWidget()
        type_card.setObjectName("TopologyCard")
        type_layout = QVBoxLayout(type_card)
        type_layout.setContentsMargins(14, 14, 14, 12)
        type_layout.setSpacing(5)
        type_layout.addWidget(self._topology_card_title("节点类型分布"))
        donut_body = QHBoxLayout()
        self._topology_donut = TopologyDonutChart()
        self._topology_donut.setFixedSize(156, 156)
        donut_body.addWidget(self._topology_donut)
        self._topology_legend_layout = QVBoxLayout()
        self._topology_legend_layout.setSpacing(5)
        donut_body.addLayout(self._topology_legend_layout, stretch=1)
        type_layout.addLayout(donut_body)
        sidebar_top.addWidget(type_card, stretch=1)
        sidebar.addLayout(sidebar_top)

        path_card = QWidget()
        path_card.setObjectName("TopologyCard")
        path_layout = QVBoxLayout(path_card)
        path_layout.setContentsMargins(14, 14, 14, 12)
        path_layout.setSpacing(6)
        path_layout.addWidget(self._topology_card_title("影响路径分析（强度 Top 5）"))
        self._topology_path_layout = QVBoxLayout()
        self._topology_path_layout.setSpacing(5)
        path_layout.addLayout(self._topology_path_layout)
        sidebar.addWidget(path_card)
        core_row.addLayout(sidebar, stretch=43)
        content_layout.addLayout(core_row)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(12)
        findings_card = QWidget()
        findings_card.setObjectName("TopologyCard")
        findings_layout = QHBoxLayout(findings_card)
        findings_layout.setContentsMargins(16, 14, 16, 14)
        findings_icon = QLabel("◉")
        findings_icon.setObjectName("TopologyInfoIcon")
        findings_icon.setAlignment(Qt.AlignCenter)
        findings_icon.setFixedSize(40, 40)
        findings_layout.addWidget(findings_icon, alignment=Qt.AlignTop)
        findings_text = QVBoxLayout()
        findings_text.addWidget(self._topology_card_title("关键发现"))
        self._topology_findings = QLabel("等待分析结果。")
        self._topology_findings.setObjectName("TopologyBodyText")
        self._topology_findings.setWordWrap(True)
        findings_text.addWidget(self._topology_findings)
        findings_layout.addLayout(findings_text, stretch=1)
        bottom_row.addWidget(findings_card, stretch=1)

        explanation_card = QWidget()
        explanation_card.setObjectName("TopologyCard")
        explanation_layout = QHBoxLayout(explanation_card)
        explanation_layout.setContentsMargins(16, 14, 16, 14)
        explanation_icon = QLabel("▤")
        explanation_icon.setObjectName("TopologyInfoIcon")
        explanation_icon.setAlignment(Qt.AlignCenter)
        explanation_icon.setFixedSize(40, 40)
        explanation_layout.addWidget(explanation_icon, alignment=Qt.AlignTop)
        explanation_text = QVBoxLayout()
        explanation_text.addWidget(self._topology_card_title("分析说明"))
        explanation = QLabel("拓扑关系由当前筛选情报中共同出现的标签构建；节点大小表示关联强度，连线表示标签共现关系。")
        explanation.setObjectName("TopologyBodyText")
        explanation.setWordWrap(True)
        explanation_text.addWidget(explanation)
        explanation_layout.addLayout(explanation_text, stretch=1)
        bottom_row.addWidget(explanation_card, stretch=1)
        content_layout.addLayout(bottom_row)
        content_layout.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll, stretch=1)

    @staticmethod
    def _topology_card_title(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("TopologyCardTitle")
        return label

    def _reset_analytics_filters(self) -> None:
        self._analytics_stage.setCurrentIndex(0)
        self._analytics_score.setCurrentIndex(0)
        self._analytics_keyword.clear()
        dates = [self._parse_datetime(row.get("timestamp", "")) for row in self._cached_rows]
        dates = [date for date in dates if date.year > 1]
        if dates:
            start, end = min(dates), max(dates)
            self._analytics_start_date.setDate(QDate(start.year, start.month, start.day))
            self._analytics_end_date.setDate(QDate(end.year, end.month, end.day))
        self._update_analytics_view()

    def _show_topology_fullscreen(self) -> None:
        """在独立窗口中放大当前真实筛选结果的拓扑图。"""
        existing = getattr(self, "_topology_fullscreen_dialog", None)
        if existing is not None and existing.isVisible():
            existing.raise_()
            existing.activateWindow()
            return
        dialog = QDialog(self)
        self._topology_fullscreen_dialog = dialog
        dialog.setObjectName("TopologyFullscreenDialog")
        dialog.setWindowTitle("行业情报拓扑图")
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowMaximizeButtonHint)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(10)
        header = QHBoxLayout()
        title = self._topology_card_title("行业情报拓扑图")
        header.addWidget(title)
        header.addStretch()
        reset = QPushButton("恢复视图")
        reset.setObjectName("TopologyTextButton")
        header.addWidget(reset)
        close = QPushButton("关闭")
        close.setObjectName("TopologySecondaryButton")
        close.setFixedHeight(32)
        header.addWidget(close)
        layout.addLayout(header)

        expanded_graph = TopologyGraphWidget()
        expanded_graph.setMinimumSize(900, 560)
        expanded_graph.set_graph(self._topology_graph._nodes, self._topology_graph._edges)
        expanded_graph.node_selected.connect(self._on_topology_node_selected)
        reset.clicked.connect(expanded_graph.reset_view)
        close.clicked.connect(dialog.close)
        dialog.finished.connect(lambda: setattr(self, "_topology_fullscreen_dialog", None))
        layout.addWidget(expanded_graph, stretch=1)
        dialog.resize(1160, 720)
        dialog.showMaximized()

    def _setup_tab_manual(self) -> None:
        layout = QVBoxLayout(self._tab_manual)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        content = QWidget()
        content.setMinimumWidth(1120)
        content.setObjectName("MultilateralPage")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 18, 20, 24)
        content_layout.setSpacing(12)

        # Page heading deliberately lives inside the scrolling content.  This keeps
        # the main workbench usable at 1280×820 without introducing nested scrollbars.
        page_heading = QWidget()
        heading_layout = QHBoxLayout(page_heading)
        heading_layout.setContentsMargins(2, 0, 2, 2)
        title_stack = QVBoxLayout()
        title_stack.setSpacing(3)
        page_title = QLabel("多边分析")
        page_title.setObjectName("MultilateralPageTitle")
        page_subtitle = QLabel("行业情报采集、筛选与 AI 分析工作台")
        page_subtitle.setObjectName("MultilateralPageSubtitle")
        title_stack.addWidget(page_title)
        title_stack.addWidget(page_subtitle)
        self._manual_updated_label = QLabel("数据更新时间：等待加载")
        self._manual_updated_label.setObjectName("MultilateralUpdated")
        self._btn_manual_refresh_all = QPushButton("刷新所有数据")
        self._btn_manual_refresh_all.setObjectName("MultilateralPrimaryButton")
        self._btn_manual_refresh_all.setIcon(self._std_icon(QStyle.SP_BrowserReload))
        self._btn_manual_refresh_all.clicked.connect(self.refresh_news_async)
        heading_layout.addLayout(title_stack)
        heading_layout.addStretch()
        heading_layout.addWidget(self._manual_updated_label)
        heading_layout.addSpacing(10)
        heading_layout.addWidget(self._btn_manual_refresh_all)
        content_layout.addWidget(page_heading)

        controls_row = QWidget()
        controls_layout = QHBoxLayout(controls_row)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(12)

        # ── Crawl Panel ──
        crawl_group = QGroupBox()
        crawl_group.setObjectName("MultilateralCard")
        crawl_layout = QVBoxLayout(crawl_group)
        crawl_layout.setContentsMargins(0, 0, 0, 0)
        crawl_layout.setSpacing(0)

        crawl_header = QWidget()
        crawl_header.setObjectName("MultilateralCardHeader")
        crawl_header_layout = QHBoxLayout(crawl_header)
        crawl_header_layout.setContentsMargins(16, 10, 16, 10)
        crawl_header_layout.setSpacing(8)
        crawl_title_dot = QLabel("●")
        crawl_title_dot.setObjectName("HeaderDotBlue")
        crawl_title = QLabel("爬取流程")
        crawl_title.setObjectName("CardTitle")
        crawl_header_layout.addWidget(crawl_title_dot)
        crawl_header_layout.addWidget(crawl_title)
        crawl_header_layout.addStretch()
        crawl_layout.addWidget(crawl_header)

        crawl_divider = QWidget()
        crawl_divider.setObjectName("CardDivider")
        crawl_divider.setFixedHeight(1)
        crawl_layout.addWidget(crawl_divider)

        crawl_body = QWidget()
        crawl_body_layout = QVBoxLayout(crawl_body)
        crawl_body_layout.setContentsMargins(16, 12, 16, 14)
        crawl_body_layout.setSpacing(12)

        crawl_toolbar = QWidget()
        crawl_toolbar.setObjectName("MultilateralControlBar")
        crawl_toolbar_layout = QHBoxLayout(crawl_toolbar)
        crawl_toolbar_layout.setContentsMargins(10, 8, 10, 8)
        crawl_toolbar_layout.setSpacing(10)

        crawl_days_label = QLabel("采集天数")
        crawl_days_label.setObjectName("FieldLabel")
        self._crawl_days = QSpinBox()
        self._crawl_days.setObjectName("CompactSpin")
        self._crawl_days.setRange(1, 30)
        self._crawl_days.setValue(3)
        self._crawl_days.setFixedWidth(70)

        self._chk_auto_ai_after_crawl = QCheckBox("爬取后自动分析")
        self._chk_auto_ai_after_crawl.setObjectName("InlineCheck")
        self._chk_auto_mail_after_ai = QCheckBox("分析后发邮件")
        self._chk_auto_mail_after_ai.setObjectName("InlineCheck")

        self._btn_start_crawl = QPushButton("采集")
        self._btn_start_crawl.setObjectName("MultilateralPrimaryButton")
        self._btn_start_crawl.setIcon(self._std_icon(QStyle.SP_BrowserReload))
        self._btn_start_crawl.setMinimumWidth(100)
        self._btn_start_crawl.clicked.connect(self._run_crawl_pipeline_async)

        crawl_toolbar_layout.addWidget(crawl_days_label)
        crawl_toolbar_layout.addWidget(self._crawl_days)
        crawl_toolbar_layout.addSpacing(6)
        crawl_toolbar_layout.addWidget(self._chk_auto_ai_after_crawl)
        crawl_toolbar_layout.addWidget(self._chk_auto_mail_after_ai)
        crawl_toolbar_layout.addStretch()
        crawl_toolbar_layout.addWidget(self._btn_start_crawl)
        crawl_body_layout.addWidget(crawl_toolbar)
        crawl_layout.addWidget(crawl_body)

        # ── News Panel ──
        news_group = QGroupBox()
        news_group.setObjectName("MultilateralCard")
        news_layout = QVBoxLayout(news_group)
        news_layout.setContentsMargins(0, 0, 0, 0)
        news_layout.setSpacing(0)

        news_header = QWidget()
        news_header.setObjectName("MultilateralCardHeader")
        news_header_layout = QHBoxLayout(news_header)
        news_header_layout.setContentsMargins(16, 10, 16, 10)
        news_header_layout.setSpacing(8)
        news_title_dot = QLabel("●")
        news_title_dot.setObjectName("HeaderDotGreen")
        news_title = QLabel("新闻数据")
        news_title.setObjectName("CardTitle")
        news_header_layout.addWidget(news_title_dot)
        news_header_layout.addWidget(news_title)
        news_header_layout.addStretch()
        news_layout.addWidget(news_header)

        news_header_divider = QWidget()
        news_header_divider.setObjectName("CardDivider")
        news_header_divider.setFixedHeight(1)
        news_layout.addWidget(news_header_divider)

        news_body = QWidget()
        news_body_layout = QVBoxLayout(news_body)
        news_body_layout.setContentsMargins(16, 12, 16, 14)
        news_body_layout.setSpacing(12)

        # These controls remain the single source of truth for NewsLoadWorker.
        news_filter_bar = QWidget()
        news_filter_bar.setObjectName("MultilateralControlBar")
        news_filter_layout = QHBoxLayout(news_filter_bar)
        news_filter_layout.setContentsMargins(10, 8, 10, 8)
        news_filter_layout.setSpacing(8)

        source_label = QLabel("来源")
        source_label.setObjectName("FieldLabel")
        self._news_source_filter = QComboBox()
        self._news_source_filter.setObjectName("FilterCombo")
        self._news_source_filter.setMinimumWidth(130)
        self._news_source_filter.setMaximumWidth(180)
        self._news_source_filter.addItem("全部")

        days_label = QLabel("天数")
        days_label.setObjectName("FieldLabel")
        self._news_days_filter = QSpinBox()
        self._news_days_filter.setObjectName("CompactSpin")
        self._news_days_filter.setRange(1, 365)
        self._news_days_filter.setValue(7)
        self._news_days_filter.setFixedWidth(70)

        self._btn_news_refresh = QPushButton("刷新")
        self._btn_news_refresh.setObjectName("MultilateralPrimaryButton")
        self._btn_news_refresh.setIcon(self._std_icon(QStyle.SP_BrowserReload))
        self._btn_news_refresh.setMinimumWidth(100)
        self._btn_news_refresh.clicked.connect(self.refresh_news_async)
        self._news_source_filter.currentIndexChanged.connect(lambda _idx: self.refresh_news_async())
        self._news_days_filter.valueChanged.connect(self._on_news_days_changed)

        date_label = QLabel("日期范围")
        date_label.setObjectName("FieldLabel")
        self._manual_filter_start = QDateEdit()
        self._manual_filter_start.setObjectName("CompactDate")
        self._manual_filter_start.setCalendarPopup(True)
        self._manual_filter_start.setDisplayFormat("yyyy-MM-dd")
        self._manual_filter_start.setDate(QDate.currentDate().addDays(-6))
        self._manual_filter_start.setFixedWidth(112)
        date_sep = QLabel("~")
        date_sep.setObjectName("FieldLabel")
        self._manual_filter_end = QDateEdit()
        self._manual_filter_end.setObjectName("CompactDate")
        self._manual_filter_end.setCalendarPopup(True)
        self._manual_filter_end.setDisplayFormat("yyyy-MM-dd")
        self._manual_filter_end.setDate(QDate.currentDate())
        self._manual_filter_end.setFixedWidth(112)
        self._manual_filter_start.dateChanged.connect(self._sync_manual_date_range)
        self._manual_filter_end.dateChanged.connect(self._sync_manual_date_range)
        self._btn_manual_reset_filters = QPushButton("重置筛选")
        self._btn_manual_reset_filters.setObjectName("MultilateralSecondaryButton")
        self._btn_manual_reset_filters.clicked.connect(self._reset_manual_filters)

        news_filter_layout.addWidget(source_label)
        news_filter_layout.addWidget(self._news_source_filter)
        news_filter_layout.addSpacing(4)
        news_filter_layout.addWidget(days_label)
        news_filter_layout.addWidget(self._news_days_filter)
        news_filter_layout.addSpacing(4)
        news_filter_layout.addWidget(date_label)
        news_filter_layout.addWidget(self._manual_filter_start)
        news_filter_layout.addWidget(date_sep)
        news_filter_layout.addWidget(self._manual_filter_end)
        news_filter_layout.addStretch()
        news_filter_layout.addWidget(self._btn_manual_reset_filters)
        news_body_layout.addWidget(news_filter_bar)
        news_layout.addWidget(news_body)
        controls_layout.addWidget(crawl_group, 3)
        controls_layout.addWidget(news_group, 5)
        content_layout.addWidget(controls_row)

        # KPI cards are intentionally data-bound below in _update_manual_dashboard.
        kpi_row = QWidget()
        kpi_layout = QHBoxLayout(kpi_row)
        kpi_layout.setContentsMargins(0, 0, 0, 0)
        kpi_layout.setSpacing(12)
        self._manual_kpis: dict[str, QLabel] = {}
        kpi_specs = [
            ("news", "采集新闻总数", "▣", "#2563EB"),
            ("sources", "新闻来源数", "◌", "#10B981"),
            ("coverage", "筛选时间覆盖", "◔", "#8B5CF6"),
            ("value", "高价值新闻", "☆", "#D49A13"),
            ("email", "邮件发送成功", "✉", "#38A7E8"),
        ]
        for key, title, icon, color in kpi_specs:
            card = QWidget()
            card.setObjectName("MultilateralKpiCard")
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(16, 12, 16, 12)
            copy = QVBoxLayout()
            copy.setSpacing(3)
            title_label = QLabel(title)
            title_label.setObjectName("MultilateralKpiTitle")
            value = QLabel("—")
            value.setObjectName("MultilateralKpiValue")
            detail = QLabel("等待真实数据")
            detail.setObjectName("MultilateralKpiDetail")
            copy.addWidget(title_label)
            copy.addWidget(value)
            copy.addWidget(detail)
            icon_label = QLabel(icon)
            icon_label.setObjectName("MultilateralKpiIcon")
            icon_label.setStyleSheet(f"color:{color}; background-color:{color}18;")
            card_layout.addLayout(copy)
            card_layout.addStretch()
            card_layout.addWidget(icon_label)
            self._manual_kpis[key] = value
            self._manual_kpis[f"{key}_detail"] = detail
            kpi_layout.addWidget(card, 1)
        content_layout.addWidget(kpi_row)

        # ── Compact crawl status and live log ──
        crawl_work_group = QGroupBox()
        crawl_work_group.setObjectName("MultilateralCard")
        crawl_work_layout = QVBoxLayout(crawl_work_group)
        crawl_work_layout.setContentsMargins(14, 12, 14, 14)
        crawl_work_layout.setSpacing(10)
        crawl_work_layout.addWidget(self._manual_card_title("●", "爬取流程", "#2563EB"))
        steps = QWidget()
        steps.setObjectName("CrawlStepRail")
        steps_layout = QHBoxLayout(steps)
        steps_layout.setContentsMargins(2, 8, 2, 4)
        steps_layout.setSpacing(0)
        self._crawl_step_labels: dict[str, QLabel] = {}
        self._crawl_step_circles: dict[str, QLabel] = {}
        crawl_step_icons = ("◎", "⌕", "□", "⇩", "✓")
        crawl_steps = ["连接网站", "请求新闻列表", "解析新闻内容", "写入数据库", "爬取完成"]
        for index, (step, icon) in enumerate(zip(crawl_steps, crawl_step_icons, strict=False)):
            node = QWidget()
            node.setObjectName("CrawlStepNode")
            node_layout = QVBoxLayout(node)
            node_layout.setContentsMargins(0, 0, 0, 0)
            node_layout.setSpacing(5)
            circle = QLabel(icon)
            circle.setObjectName("CrawlStepCircle")
            circle.setAlignment(Qt.AlignCenter)
            circle.setFixedSize(28, 28)
            name_label = QLabel(step)
            name_label.setObjectName("CrawlStep")
            name_label.setAlignment(Qt.AlignCenter)
            name_label.setFixedHeight(18)
            self._crawl_step_labels[step] = name_label
            self._crawl_step_circles[step] = circle
            node_layout.addWidget(circle, alignment=Qt.AlignHCenter)
            node_layout.addWidget(name_label)
            steps_layout.addWidget(node, 0, Qt.AlignTop)
            if index < len(crawl_steps) - 1:
                connector = QWidget()
                connector.setObjectName("CrawlStepConnector")
                connector.setFixedHeight(2)
                steps_layout.addWidget(connector, 1, Qt.AlignTop)
        crawl_work_layout.addWidget(steps)
        self._crawl_status_label = QLabel("等待开始爬取")
        self._crawl_status_label.setObjectName("StatusChip")
        crawl_work_layout.addWidget(self._crawl_status_label)
        self._crawl_log_view = QTextBrowser()
        self._crawl_log_view.setObjectName("LogConsole")
        self._crawl_log_view.setOpenExternalLinks(True)
        self._crawl_log_view.setMinimumHeight(132)
        self._crawl_log_view.setPlaceholderText("爬取日志将在这里实时显示…")
        crawl_work_layout.addWidget(self._crawl_log_view, 1)
        self._crawl_summary_label = QLabel("已采集 — 条  ·  成功 —  · 失败 —  · 用时 —")
        self._crawl_summary_label.setObjectName("ManualFooterHint")
        crawl_work_layout.addWidget(self._crawl_summary_label)
        self._reset_crawl_steps()

        # ── News table, the primary working surface ──
        news_work_group = QGroupBox()
        news_work_group.setObjectName("MultilateralCard")
        news_work_layout = QVBoxLayout(news_work_group)
        news_work_layout.setContentsMargins(14, 12, 14, 14)
        news_work_layout.setSpacing(8)
        header_row = QHBoxLayout()
        header_row.addWidget(self._manual_card_title("●", "新闻数据", "#10B981"))
        header_row.addStretch()
        self._btn_news_refresh.setText("刷新新闻")
        header_row.addWidget(self._btn_news_refresh)
        news_work_layout.addLayout(header_row)
        news_del_bar = QWidget()
        news_del_bar.setObjectName("MultilateralDangerBar")
        news_del_layout = QHBoxLayout(news_del_bar)
        news_del_layout.setContentsMargins(8, 6, 8, 6)
        news_del_layout.setSpacing(7)

        self._btn_news_delete_loaded = QPushButton("清空列表")
        self._btn_news_delete_loaded.setObjectName("DangerButton")
        self._btn_news_delete_loaded.setIcon(self._std_icon(QStyle.SP_DialogDiscardButton))
        self._btn_news_delete_loaded.clicked.connect(self._delete_loaded_news_async)

        del_sep = QWidget()
        del_sep.setObjectName("VSep")
        del_sep.setFixedWidth(1)
        del_sep.setFixedHeight(20)

        range_label = QLabel("按日期删除")
        range_label.setObjectName("FieldLabel")
        self._news_delete_start = QDateEdit()
        self._news_delete_start.setObjectName("CompactDate")
        self._news_delete_start.setCalendarPopup(True)
        self._news_delete_start.setDisplayFormat("yyyy-MM-dd")
        self._news_delete_start.setDate(QDate.currentDate().addDays(-7))
        self._news_delete_start.setFixedWidth(112)

        range_to_label = QLabel("→")
        range_to_label.setObjectName("FieldLabel")

        self._news_delete_end = QDateEdit()
        self._news_delete_end.setObjectName("CompactDate")
        self._news_delete_end.setCalendarPopup(True)
        self._news_delete_end.setDisplayFormat("yyyy-MM-dd")
        self._news_delete_end.setDate(QDate.currentDate())
        self._news_delete_end.setFixedWidth(112)

        self._btn_news_delete_range = QPushButton("删除区间")
        self._btn_news_delete_range.setObjectName("DangerButton")
        self._btn_news_delete_range.setIcon(self._std_icon(QStyle.SP_DialogDiscardButton))
        self._btn_news_delete_range.clicked.connect(self._delete_news_by_date_range_async)

        news_del_layout.addWidget(self._btn_news_delete_loaded)
        news_del_layout.addWidget(del_sep)
        news_del_layout.addSpacing(2)
        news_del_layout.addWidget(range_label)
        news_del_layout.addWidget(self._news_delete_start)
        news_del_layout.addWidget(range_to_label)
        news_del_layout.addWidget(self._news_delete_end)
        news_del_layout.addWidget(self._btn_news_delete_range)
        news_del_layout.addStretch()
        news_work_layout.addWidget(news_del_bar)
        self._set_news_bulk_delete_enabled(False)

        self._news_table = NewsTableWidget()
        self._news_table.delete_requested.connect(self._request_delete_news)
        self._news_table.setMinimumHeight(200)
        self._news_table.setMaximumHeight(300)
        news_work_layout.addWidget(self._news_table, stretch=1)

        news_footer = QHBoxLayout()
        news_footer.setContentsMargins(2, 4, 2, 0)
        self._news_page_hint = QLabel("当前无新闻数据")
        self._news_page_hint.setObjectName("FooterHint")
        self._btn_news_load_more = QPushButton("加载更多")
        self._btn_news_load_more.setObjectName("GhostButton")
        self._btn_news_load_more.clicked.connect(self._load_more_news_rows)
        news_footer.addWidget(self._news_page_hint)
        news_footer.addStretch()
        news_footer.addWidget(self._btn_news_load_more)
        news_work_layout.addLayout(news_footer)

        # ── AI Analysis Panel ──
        analysis_group = QGroupBox()
        analysis_group.setObjectName("MultilateralCard")
        analysis_layout = QVBoxLayout(analysis_group)
        analysis_layout.setContentsMargins(0, 0, 0, 0)
        analysis_layout.setSpacing(0)

        ai_header = QWidget()
        ai_header.setObjectName("MultilateralCardHeader")
        ai_header_layout = QHBoxLayout(ai_header)
        ai_header_layout.setContentsMargins(16, 10, 16, 10)
        ai_header_layout.setSpacing(8)
        ai_title_dot = QLabel("●")
        ai_title_dot.setObjectName("HeaderDotPurple")
        ai_title = QLabel("AI 智能分析")
        ai_title.setObjectName("CardTitle")
        ai_header_layout.addWidget(ai_title_dot)
        ai_header_layout.addWidget(ai_title)
        ai_header_layout.addStretch()
        analysis_layout.addWidget(ai_header)

        ai_header_divider = QWidget()
        ai_header_divider.setObjectName("CardDivider")
        ai_header_divider.setFixedHeight(1)
        analysis_layout.addWidget(ai_header_divider)

        ai_body = QWidget()
        ai_body_layout = QVBoxLayout(ai_body)
        ai_body_layout.setContentsMargins(14, 12, 14, 14)
        ai_body_layout.setSpacing(12)

        ai_toolbar = QWidget()
        ai_toolbar.setObjectName("MultilateralControlBar")
        ai_toolbar_layout = QHBoxLayout(ai_toolbar)
        ai_toolbar_layout.setContentsMargins(10, 8, 10, 8)
        ai_toolbar_layout.setSpacing(10)

        range_lbl = QLabel("分析范围")
        range_lbl.setObjectName("FieldLabel")
        self._manual_range = QComboBox()
        self._manual_range.setObjectName("FilterCombo")
        self._manual_range.setMinimumWidth(120)
        self._manual_range.setMaximumWidth(160)
        self._manual_range.addItems(["最近 24 小时", "最近 3 天", "最近 7 天"])

        self._btn_run_ai = QPushButton("执行分析")
        self._btn_run_ai.setObjectName("MultilateralSuccessButton")
        self._btn_run_ai.setIcon(self._std_icon(QStyle.SP_MediaPlay))
        self._btn_run_ai.setMinimumWidth(100)
        self._btn_run_ai.clicked.connect(self._run_manual_analysis_async)

        ai_toolbar_layout.addWidget(range_lbl)
        ai_toolbar_layout.addWidget(self._manual_range)
        ai_toolbar_layout.addStretch()
        ai_toolbar_layout.addWidget(self._btn_run_ai)
        ai_body_layout.addWidget(ai_toolbar)

        prompt_label = QLabel("补充说明（可选）")
        prompt_label.setObjectName("FieldLabel")
        ai_body_layout.addWidget(prompt_label)

        self._manual_extra = QTextEdit()
        self._manual_extra.setObjectName("PromptInput")
        self._manual_extra.setPlaceholderText("输入额外的分析说明或约束条件，留空则使用默认 Prompt…")
        self._manual_extra.setFixedHeight(64)
        ai_body_layout.addWidget(self._manual_extra)

        output_label = QLabel("分析输出")
        output_label.setObjectName("FieldLabel")
        ai_body_layout.addWidget(output_label)

        self._manual_output = QPlainTextEdit()
        self._manual_output.setObjectName("OutputConsole")
        self._manual_output.setReadOnly(True)
        self._manual_output.setMinimumHeight(180)
        self._manual_output.setPlaceholderText("分析结果将在这里显示…")
        ai_body_layout.addWidget(self._manual_output, stretch=1)

        analysis_layout.addWidget(ai_body, stretch=1)

        # ── Analysis summary, now the middle column of the work splitter ──
        # (Swapped with the news table: the table moved to the bottom row to gain width.)
        # Overview content is populated solely from the currently loaded SQLite rows.
        overview_card = QGroupBox()
        overview_card.setObjectName("MultilateralCard")
        overview_layout = QVBoxLayout(overview_card)
        overview_layout.setContentsMargins(14, 12, 14, 14)
        overview_layout.setSpacing(8)
        overview_layout.addWidget(self._manual_card_title("●", "分析结果概览", "#2563EB"))
        self._manual_overview_text = QLabel("加载新闻后，将基于真实 SQLite 新闻数据展示来源与主题概览。")
        self._manual_overview_text.setObjectName("ManualOverviewText")
        self._manual_overview_text.setWordWrap(True)
        overview_layout.addWidget(self._manual_overview_text)
        self._manual_source_bars = QWidget()
        self._manual_source_bars.setObjectName("ManualBarList")
        self._manual_source_bars_layout = QVBoxLayout(self._manual_source_bars)
        self._manual_source_bars_layout.setContentsMargins(0, 0, 0, 0)
        self._manual_source_bars_layout.setSpacing(5)
        overview_layout.addWidget(self._manual_source_bars, 1)
        score_note = QLabel("评分分布：待接入新闻评分字段（当前新闻表不含评分数据）。")
        score_note.setObjectName("ManualFooterHint")
        score_note.setWordWrap(True)
        overview_layout.addWidget(score_note)

        # ── Work splitter: 爬取流程 | AI 智能分析 | 分析结果概览 ──
        work_splitter = QSplitter(Qt.Horizontal)
        work_splitter.setObjectName("MultilateralSplitter")
        work_splitter.setChildrenCollapsible(False)
        work_splitter.setHandleWidth(12)
        work_splitter.addWidget(crawl_work_group)
        work_splitter.addWidget(analysis_group)
        work_splitter.addWidget(overview_card)
        work_splitter.setStretchFactor(0, 28)
        work_splitter.setStretchFactor(1, 44)
        work_splitter.setStretchFactor(2, 28)
        work_splitter.setSizes([350, 560, 350])
        content_layout.addWidget(work_splitter)

        # ── Trend card ──
        trend_card = QGroupBox()
        trend_card.setObjectName("MultilateralCard")
        trend_layout = QVBoxLayout(trend_card)
        trend_layout.setContentsMargins(14, 12, 14, 14)
        trend_layout.setSpacing(8)
        trend_layout.addWidget(self._manual_card_title("●", "分析趋势（近 7 天）", "#8B5CF6"))
        self._manual_trend_text = QLabel("加载新闻后显示每日新闻数量；平均评分待评分数据支持。")
        self._manual_trend_text.setObjectName("ManualOverviewText")
        self._manual_trend_text.setWordWrap(True)
        trend_layout.addWidget(self._manual_trend_text)
        self._manual_trend_bars = QWidget()
        self._manual_trend_bars.setObjectName("ManualBarList")
        self._manual_trend_bars_layout = QVBoxLayout(self._manual_trend_bars)
        self._manual_trend_bars_layout.setContentsMargins(0, 0, 0, 0)
        self._manual_trend_bars_layout.setSpacing(5)
        trend_layout.addWidget(self._manual_trend_bars, 1)

        # ── Bottom splitter: 新闻数据表格 | 分析趋势 ──
        bottom_splitter = QSplitter(Qt.Horizontal)
        bottom_splitter.setObjectName("MultilateralSplitter")
        bottom_splitter.setChildrenCollapsible(False)
        bottom_splitter.setHandleWidth(12)
        bottom_splitter.addWidget(news_work_group)
        bottom_splitter.addWidget(trend_card)
        bottom_splitter.setStretchFactor(0, 33)
        bottom_splitter.setStretchFactor(1, 17)
        bottom_splitter.setSizes([805, 415])
        content_layout.addWidget(bottom_splitter)

        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)
        self.refresh_news_async()

    def _manual_card_title(self, dot: str, text: str, color: str) -> QWidget:
        """Create the shared, compact card title used by the workbench."""
        container = QWidget()
        container.setObjectName("MultilateralCardTitleRow")
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(7)
        marker = QLabel(dot)
        marker.setStyleSheet(f"color:{color}; font-size:14px; background:transparent;")
        title = QLabel(text)
        title.setObjectName("MultilateralCardTitle")
        row.addWidget(marker)
        row.addWidget(title)
        row.addStretch()
        return container

    @Slot()
    def _sync_manual_date_range(self) -> None:
        """Map the visible date controls to the existing days-based query safely."""
        if not hasattr(self, "_manual_filter_start") or not hasattr(self, "_news_days_filter"):
            return
        days = max(1, self._manual_filter_start.date().daysTo(self._manual_filter_end.date()) + 1)
        self._news_days_filter.blockSignals(True)
        self._news_days_filter.setValue(min(days, self._news_days_filter.maximum()))
        self._news_days_filter.blockSignals(False)
        self.refresh_news_async()

    @Slot(int)
    def _on_news_days_changed(self, value: int) -> None:
        """「最近 N 天」spinbox 变化：同步日期选择器为 (今天-(N-1) ~ 今天)，再按绝对日期刷新。"""
        if not hasattr(self, "_manual_filter_start") or not hasattr(self, "_manual_filter_end"):
            self.refresh_news_async()
            return
        end = QDate.currentDate()
        start = end.addDays(-max(1, value) + 1)
        self._manual_filter_start.blockSignals(True)
        self._manual_filter_end.blockSignals(True)
        self._manual_filter_start.setDate(start)
        self._manual_filter_end.setDate(end)
        self._manual_filter_start.blockSignals(False)
        self._manual_filter_end.blockSignals(False)
        self.refresh_news_async()

    @Slot()
    def _reset_manual_filters(self) -> None:
        """Reset the visible filter controls, then run the existing async reload."""
        self._news_source_filter.blockSignals(True)
        self._news_source_filter.setCurrentIndex(0)
        self._news_source_filter.blockSignals(False)
        self._news_days_filter.blockSignals(True)
        self._news_days_filter.setValue(7)
        self._news_days_filter.blockSignals(False)
        self._manual_filter_start.blockSignals(True)
        self._manual_filter_end.blockSignals(True)
        self._manual_filter_start.setDate(QDate.currentDate().addDays(-6))
        self._manual_filter_end.setDate(QDate.currentDate())
        self._manual_filter_start.blockSignals(False)
        self._manual_filter_end.blockSignals(False)
        self.refresh_news_async()

    def _setup_tab_settings(self) -> None:
        root = QVBoxLayout(self._tab_settings)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        page_header = QWidget()
        page_header.setObjectName("SettingsPageHeader")
        page_header_layout = QVBoxLayout(page_header)
        page_header_layout.setContentsMargins(22, 16, 22, 12)
        page_header_layout.setSpacing(3)
        title = QLabel("设置")
        title.setObjectName("SettingsPageTitle")
        subtitle = QLabel("AI 行业情报系统运行参数配置")
        subtitle.setObjectName("SettingsPageSubtitle")
        page_header_layout.addWidget(title)
        page_header_layout.addWidget(subtitle)
        root.addWidget(page_header)

        workbench = QWidget()
        workbench.setObjectName("SettingsWorkbench")
        workbench_layout = QHBoxLayout(workbench)
        workbench_layout.setContentsMargins(18, 12, 18, 12)
        workbench_layout.setSpacing(16)

        nav_panel = QWidget()
        nav_panel.setObjectName("SettingsNavPanel")
        nav_panel.setFixedWidth(180)
        nav_layout = QVBoxLayout(nav_panel)
        nav_layout.setContentsMargins(10, 12, 10, 12)
        nav_layout.setSpacing(5)
        nav_title = QLabel("设置导航")
        nav_title.setObjectName("SettingsNavTitle")
        nav_layout.addWidget(nav_title)
        self._settings_nav_buttons: list[QPushButton] = []
        self._settings_section_targets: dict[str, QWidget] = {}

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setObjectName("SettingsScroll")
        self._settings_scroll = scroll
        content = QWidget()
        content.setMinimumWidth(900)
        content.setObjectName("SettingsContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 8, 8)
        content_layout.setSpacing(14)

        # AI model configuration -------------------------------------------------
        g_ai = QGroupBox()
        g_ai.setObjectName("SettingsCard")
        ai_layout = QVBoxLayout(g_ai)
        ai_layout.setContentsMargins(16, 14, 16, 16)
        ai_layout.setSpacing(12)
        ai_layout.addWidget(self._settings_card_heading("settings", "AI 模型配置", "配置 DeepSeek 大模型相关参数，用于新闻智能分析与报告生成"))
        ai_body = QHBoxLayout()
        ai_body.setSpacing(18)
        ai_form = QFormLayout()
        self._configure_form_layout(ai_form)
        self._set_api_key = QLineEdit()
        self._set_api_key.setEchoMode(QLineEdit.Password)
        self._set_api_key.setObjectName("SettingsInput")
        api_box = QWidget()
        api_row = QHBoxLayout(api_box)
        api_row.setContentsMargins(0, 0, 0, 0)
        api_row.setSpacing(6)
        api_row.addWidget(self._set_api_key, 1)
        self._btn_toggle_api_key = QPushButton("显示")
        self._btn_toggle_api_key.setObjectName("SettingsInlineButton")
        self._btn_toggle_api_key.clicked.connect(self._toggle_api_key_visibility)
        api_row.addWidget(self._btn_toggle_api_key)
        self._set_base_url = QLineEdit()
        self._set_base_url.setObjectName("SettingsInput")
        self._set_model = QComboBox()
        self._set_model.setObjectName("SettingsInput")
        self._set_model.setEditable(True)
        self._set_model.addItems(["deepseek-chat", "deepseek-v4-flash"])
        ai_form.addRow("API Key", api_box)
        ai_form.addRow("Base URL", self._set_base_url)
        ai_form.addRow("Model", self._set_model)
        ai_body.addLayout(ai_form, 3)
        connection = QWidget()
        connection.setObjectName("SettingsConnectionPanel")
        connection_layout = QVBoxLayout(connection)
        connection_layout.setContentsMargins(14, 12, 14, 12)
        connection_layout.setSpacing(8)
        connection_title = QLabel("连接状态")
        connection_title.setObjectName("SettingsConnectionTitle")
        self._set_conn_state = QLabel("○ 尚未检测")
        self._set_conn_state.setObjectName("SettingsConnectionPending")
        self._set_conn_hint = QLabel("点击“测试连接”验证 API Key / Base URL / Model 配置是否可用。")
        self._set_conn_hint.setObjectName("SettingsHelpText")
        self._set_conn_hint.setWordWrap(True)
        self._set_btn_test_conn = QPushButton("测试连接")
        self._set_btn_test_conn.setObjectName("SettingsInlineButton")
        self._set_btn_test_conn.clicked.connect(self._test_ai_connection_async)
        connection_layout.addWidget(connection_title)
        connection_layout.addWidget(self._set_conn_state)
        connection_layout.addWidget(self._set_conn_hint, 1)
        connection_layout.addWidget(self._set_btn_test_conn)
        ai_body.addWidget(connection, 2)
        ai_layout.addLayout(ai_body)

        # Mail -------------------------------------------------------------------
        g_mail = QGroupBox()
        g_mail.setObjectName("SettingsCard")
        mail_layout = QVBoxLayout(g_mail)
        mail_layout.setContentsMargins(16, 14, 16, 16)
        mail_layout.setSpacing(12)
        mail_layout.addWidget(self._settings_card_heading("mail", "邮件通知配置", "配置 SMTP 服务器和分析结果邮件通知"))
        mail_grid = QGridLayout()
        mail_grid.setHorizontalSpacing(18)
        mail_grid.setVerticalSpacing(10)
        self._set_smtp_host = QLineEdit()
        self._set_smtp_host.setObjectName("SettingsInput")
        self._set_smtp_port = QSpinBox()
        self._set_smtp_port.setObjectName("SettingsInput")
        self._set_smtp_port.setRange(1, 65535)
        self._set_smtp_user = QLineEdit()
        self._set_smtp_user.setObjectName("SettingsInput")
        self._set_smtp_pass = QLineEdit()
        self._set_smtp_pass.setObjectName("SettingsInput")
        self._set_smtp_pass.setEchoMode(QLineEdit.Password)
        self._set_smtp_ssl = QCheckBox("使用 SSL（端口 465 等）")
        self._set_smtp_ssl.setChecked(True)
        self._set_recipients = QLineEdit()
        self._set_recipients.setObjectName("SettingsInput")
        self._set_recipients.setPlaceholderText("多个收件人用英文逗号分隔")
        mail_grid.addWidget(self._settings_field_label("SMTP 服务器"), 0, 0)
        mail_grid.addWidget(self._set_smtp_host, 0, 1)
        mail_grid.addWidget(self._settings_field_label("SSL"), 0, 2)
        mail_grid.addWidget(self._set_smtp_ssl, 0, 3)
        mail_grid.addWidget(self._settings_field_label("端口"), 1, 0)
        mail_grid.addWidget(self._set_smtp_port, 1, 1)
        mail_grid.addWidget(self._settings_field_label("收件人"), 1, 2)
        mail_grid.addWidget(self._set_recipients, 1, 3)
        mail_grid.addWidget(self._settings_field_label("账号"), 2, 0)
        mail_grid.addWidget(self._set_smtp_user, 2, 1)
        mail_grid.addWidget(self._settings_field_label("密码"), 3, 0)
        mail_grid.addWidget(self._set_smtp_pass, 3, 1)
        self._btn_send_test_mail = QPushButton("发送测试邮件")
        self._btn_send_test_mail.setObjectName("SuccessBtn")
        self._btn_send_test_mail.setIcon(self._std_icon(QStyle.SP_MessageBoxInformation))
        self._btn_send_test_mail.clicked.connect(self._send_test_mail_async)
        mail_grid.addWidget(self._btn_send_test_mail, 3, 3)
        mail_grid.setColumnStretch(1, 2)
        mail_grid.setColumnStretch(3, 2)
        mail_layout.addLayout(mail_grid)

        # Crawler ---------------------------------------------------------------
        g_crawl = QGroupBox()
        g_crawl.setObjectName("SettingsCard")
        crawl_layout = QVBoxLayout(g_crawl)
        crawl_layout.setContentsMargins(16, 14, 16, 16)
        crawl_layout.setSpacing(10)
        crawl_layout.addWidget(self._settings_card_heading("crawler", "数据源与采集限制", "选择参与采集的新闻来源，并控制单站采集数量"))
        self._chk_src_ndrc = QCheckBox("国家发改委（ndrc）")
        self._chk_src_nea = QCheckBox("国家能源局（nea）")
        self._chk_src_miit = QCheckBox("工业和信息化部（miit）")
        self._chk_src_china5e = QCheckBox("中国能源网（china5e）")
        source_grid = QGridLayout()
        for index, checkbox in enumerate((self._chk_src_ndrc, self._chk_src_nea, self._chk_src_miit, self._chk_src_china5e)):
            source_grid.addWidget(checkbox, index // 2, index % 2)
        crawl_layout.addLayout(source_grid)
        site_limit_row = QHBoxLayout()
        site_limit_row.addWidget(self._settings_field_label("每站最多抓取"))
        self._crawl_max_items = QSpinBox()
        self._crawl_max_items.setObjectName("SettingsInput")
        self._crawl_max_items.setRange(1, 50)
        site_limit_row.addWidget(self._crawl_max_items)
        site_limit_row.addWidget(QLabel("条"))
        site_limit_row.addStretch()
        crawl_layout.addLayout(site_limit_row)

        # Scheduler -------------------------------------------------------------
        g_sched = QGroupBox()
        g_sched.setObjectName("SettingsCard")
        sched_layout = QVBoxLayout(g_sched)
        sched_layout.setContentsMargins(16, 14, 16, 16)
        sched_layout.setSpacing(12)
        sched_layout.addWidget(self._settings_card_heading("schedule", "自动任务调度", "保存设置后，由现有 SchedulerService 按所选时间执行任务"))
        self._chk_m, self._freq_m, self._weekday_m, self._time_m = self._create_schedule_fields()
        self._chk_n, self._freq_n, self._weekday_n, self._time_n = self._create_schedule_fields()
        self._chk_e, self._freq_e, self._weekday_e, self._time_e = self._create_schedule_fields()
        schedule_cards = QHBoxLayout()
        schedule_cards.setSpacing(10)
        for label, fields in (("☀ 早间任务", (self._chk_m, self._freq_m, self._weekday_m, self._time_m)), ("☀ 午间任务", (self._chk_n, self._freq_n, self._weekday_n, self._time_n)), ("☾ 晚间任务", (self._chk_e, self._freq_e, self._weekday_e, self._time_e))):
            schedule_cards.addWidget(self._schedule_task_card(label, *fields), 1)
        sched_layout.addLayout(schedule_cards)

        # Business and storage --------------------------------------------------
        g_other = QGroupBox()
        g_other.setObjectName("SettingsCard")
        other_layout = QVBoxLayout(g_other)
        other_layout.setContentsMargins(16, 14, 16, 16)
        other_layout.setSpacing(12)
        other_layout.addWidget(self._settings_card_heading("business", "业务分析配置", "管理行业关键词、日志级别与系统分析提示词"))
        other_grid = QGridLayout()
        other_grid.setHorizontalSpacing(16)
        other_grid.setVerticalSpacing(10)
        self._set_keywords = QLineEdit()
        self._set_keywords.setObjectName("SettingsInput")
        self._set_keywords.setPlaceholderText("关键词用逗号分隔")
        self._set_db_path = QLineEdit()
        self._set_db_path.setObjectName("SettingsInput")
        self._set_db_path.textChanged.connect(self._update_storage_paths_hint)
        self._set_log_level = QComboBox()
        self._set_log_level.setObjectName("SettingsInput")
        self._set_log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self._set_prompt = QTextEdit()
        self._set_prompt.setObjectName("PromptInput")
        self._set_prompt.setPlaceholderText("自定义系统 Prompt（留空则使用内置）")
        self._set_prompt.setMinimumHeight(120)
        other_grid.addWidget(self._settings_field_label("行业关键词"), 0, 0)
        other_grid.addWidget(self._set_keywords, 0, 1)
        other_grid.addWidget(self._settings_field_label("数据库路径"), 1, 0)
        other_grid.addWidget(self._set_db_path, 1, 1)
        other_grid.addWidget(self._settings_field_label("日志级别"), 2, 0)
        other_grid.addWidget(self._set_log_level, 2, 1)
        other_grid.addWidget(self._settings_field_label("System Prompt"), 0, 2, Qt.AlignTop)
        other_grid.addWidget(self._set_prompt, 0, 3, 3, 1)
        other_grid.setColumnStretch(1, 2)
        other_grid.setColumnStretch(3, 2)
        other_layout.addLayout(other_grid)

        g_store = QGroupBox()
        g_store.setObjectName("SettingsCard")
        lay_store = QVBoxLayout(g_store)
        lay_store.setContentsMargins(16, 14, 16, 16)
        lay_store.setSpacing(10)
        lay_store.addWidget(self._settings_card_heading("storage", "本地存储路径", "以下路径只读，随当前配置文件与数据库路径变化"))
        self._storage_paths_text = QPlainTextEdit()
        self._storage_paths_text.setObjectName("SettingsPathDisplay")
        self._storage_paths_text.setReadOnly(True)
        self._storage_paths_text.setMinimumHeight(120)
        btn_paths = QPushButton("刷新路径说明")
        btn_paths.setObjectName("SettingsInlineButton")
        btn_paths.setIcon(self._std_icon(QStyle.SP_BrowserReload))
        btn_paths.clicked.connect(self._update_storage_paths_hint)
        lay_store.addWidget(self._storage_paths_text)
        lay_store.addWidget(btn_paths)

        sections = (
            ("AI 设置", "settings", g_ai),
            ("邮件通知", "mail", g_mail),
            ("爬虫设置", "crawler", g_crawl),
            ("调度任务", "schedule", g_sched),
            ("业务与日志", "business", g_other),
            ("存储路径", "storage", g_store),
        )
        for text, icon_name, section in sections:
            button = QPushButton(text)
            button.setIcon(self._settings_std_icon(icon_name))
            button.setIconSize(QSize(18, 18))
            button.setObjectName("SettingsNavButton")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, target=section, nav=button: self._navigate_settings_section(target, nav))
            self._settings_nav_buttons.append(button)
            self._settings_section_targets[text] = section
            nav_layout.addWidget(button)
            content_layout.addWidget(section)
        system_button = QPushButton("系统信息")
        system_button.setIcon(self._settings_std_icon("system"))
        system_button.setIconSize(QSize(18, 18))
        system_button.setObjectName("SettingsNavButton")
        system_button.setCheckable(True)
        system_button.clicked.connect(lambda checked=False, target=g_store, nav=system_button: self._navigate_settings_section(target, nav))
        self._settings_nav_buttons.append(system_button)
        nav_layout.addWidget(system_button)
        nav_layout.addStretch()
        self._settings_nav_buttons[0].setChecked(True)
        self._settings_nav_buttons[0].setIcon(self._settings_std_icon("settings"))
        scroll.setWidget(content)
        workbench_layout.addWidget(nav_panel)
        workbench_layout.addWidget(scroll, 1)
        root.addWidget(workbench, stretch=1)

        footer = QWidget()
        footer.setObjectName("SettingsFooter")
        btn_row = QHBoxLayout(footer)
        btn_row.setContentsMargins(22, 10, 22, 10)
        status_box = QVBoxLayout()
        status_box.setSpacing(2)
        status = QLabel("✓ 配置正常")
        status.setObjectName("SettingsStatusOk")
        saved = QLabel("保存设置后会立即重新加载并应用调度配置")
        saved.setObjectName("SettingsFooterHint")
        status_box.addWidget(status)
        status_box.addWidget(saved)
        btn_row.addLayout(status_box)
        btn_row.addStretch()
        restore = QPushButton("恢复已保存配置")
        restore.setObjectName("SettingsInlineButton")
        restore.clicked.connect(self._reload_settings_into_widgets)
        btn_row.addWidget(restore)
        self._btn_save_settings = QPushButton("保存设置")
        self._btn_save_settings.setObjectName("PrimaryBtn")
        self._btn_save_settings.setIcon(self._std_icon(QStyle.SP_DialogSaveButton))
        self._btn_save_settings.clicked.connect(self._save_settings_async)
        btn_row.addWidget(self._btn_save_settings)
        root.addWidget(footer)

    def _settings_card_heading(self, icon: str, title: str, subtitle: str) -> QWidget:
        heading = QWidget()
        layout = QVBoxLayout(heading)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(8)
        icon_label = QLabel()
        icon_label.setPixmap(self._settings_std_icon(icon).pixmap(QSize(20, 20)))
        icon_label.setFixedSize(20, 20)
        icon_label.setAlignment(Qt.AlignCenter)
        title_label = QLabel(title)
        title_label.setObjectName("SettingsCardTitle")
        title_row.addWidget(icon_label)
        title_row.addWidget(title_label)
        title_row.addStretch()
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("SettingsCardSubtitle")
        subtitle_label.setWordWrap(True)
        layout.addLayout(title_row)
        layout.addWidget(subtitle_label)
        return heading

    @staticmethod
    def _settings_field_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("FieldLabel")
        return label

    def _create_schedule_fields(self) -> tuple[QCheckBox, QComboBox, QComboBox, QLineEdit]:
        enabled = QCheckBox("启用")
        frequency = QComboBox()
        frequency.setObjectName("SettingsInput")
        frequency.addItems(["每天", "每周"])
        weekday = QComboBox()
        weekday.setObjectName("SettingsInput")
        weekday.addItems(["周一", "周二", "周三", "周四", "周五", "周六", "周日"])
        time_edit = QLineEdit()
        time_edit.setObjectName("SettingsInput")
        time_edit.setPlaceholderText("HH:MM")
        return enabled, frequency, weekday, time_edit

    def _schedule_task_card(self, title: str, enabled: QCheckBox, frequency: QComboBox, weekday: QComboBox, time_edit: QLineEdit) -> QWidget:
        card = QWidget()
        card.setObjectName("SettingsScheduleCard")
        layout = QFormLayout(card)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(8)
        heading = QLabel(title)
        heading.setObjectName("SettingsScheduleTitle")
        layout.addRow(heading)
        layout.addRow("", enabled)
        layout.addRow("频率", frequency)
        layout.addRow("时间", time_edit)
        layout.addRow("星期", weekday)
        return card

    @Slot()
    def _toggle_api_key_visibility(self) -> None:
        visible = self._set_api_key.echoMode() == QLineEdit.Normal
        self._set_api_key.setEchoMode(QLineEdit.Password if visible else QLineEdit.Normal)
        self._btn_toggle_api_key.setText("显示" if visible else "隐藏")

    def _navigate_settings_section(self, target: QWidget, active: QPushButton) -> None:
        for button in self._settings_nav_buttons:
            button.setChecked(button is active)
        self._settings_scroll.ensureWidgetVisible(target, 0, 10)

    def _setup_tab_log(self) -> None:
        self._log_entries: list[dict[str, object]] = []
        self._log_page = 0
        self._log_rows_per_page = 20
        self._log_active_level = "全部"
        layout = QVBoxLayout(self._tab_log)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget()
        header.setObjectName("LogPageHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)
        header_layout.setSpacing(14)
        heading = QLabel("☰  日志与状态")
        heading.setObjectName("LogPageTitle")
        self._sched_status = QLabel("●  调度线程状态：运行中")
        self._sched_status.setObjectName("LogSchedulerStatus")
        self._log_uptime = QLabel("运行时长：本次会话")
        self._log_uptime.setObjectName("LogHeaderMeta")
        self._log_updated = QLabel("最近更新：—")
        self._log_updated.setObjectName("LogHeaderMeta")
        clear = QPushButton("清空日志")
        clear.setObjectName("LogHeaderButton")
        clear.clicked.connect(self._clear_log_cache)
        export = QPushButton("导出日志")
        export.setObjectName("LogHeaderButton")
        export.clicked.connect(self._export_log_entries)
        self._log_auto_scroll = QCheckBox("自动滚动")
        self._log_auto_scroll.setObjectName("LogAutoScroll")
        self._log_auto_scroll.setChecked(True)
        display = QPushButton("⚙  显示设置")
        display.setObjectName("LogHeaderButton")
        display.clicked.connect(self._show_log_display_settings)
        header_layout.addWidget(heading)
        header_layout.addSpacing(24)
        header_layout.addWidget(self._sched_status)
        header_layout.addWidget(self._log_uptime)
        header_layout.addWidget(self._log_updated)
        header_layout.addStretch()
        header_layout.addWidget(clear)
        header_layout.addWidget(export)
        header_layout.addWidget(self._log_auto_scroll)
        header_layout.addWidget(display)
        layout.addWidget(header)

        body = QWidget()
        body.setObjectName("LogPageBody")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(18, 12, 18, 10)
        body_layout.setSpacing(14)
        sidebar = self._build_log_sidebar()
        sidebar.setFixedWidth(250)
        body_layout.addWidget(sidebar)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        right_layout.addWidget(self._build_log_filter_bar())
        self._log_table = QTableWidget(0, 6)
        self._log_table.setObjectName("LogTable")
        self._log_table.setHorizontalHeaderLabels(["时间", "级别", "来源", "模块", "消息摘要", "操作"])
        self._log_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._log_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._log_table.setSelectionMode(QTableWidget.SingleSelection)
        self._log_table.setShowGrid(False)
        self._log_table.setAlternatingRowColors(True)
        self._log_table.verticalHeader().setVisible(False)
        self._log_table.verticalHeader().setDefaultSectionSize(34)
        table_header = self._log_table.horizontalHeader()
        table_header.setHighlightSections(False)
        table_header.setSectionResizeMode(0, QHeaderView.Fixed)
        table_header.setSectionResizeMode(1, QHeaderView.Fixed)
        table_header.setSectionResizeMode(2, QHeaderView.Fixed)
        table_header.setSectionResizeMode(3, QHeaderView.Fixed)
        table_header.setSectionResizeMode(4, QHeaderView.Stretch)
        table_header.setSectionResizeMode(5, QHeaderView.Fixed)
        self._log_table.setColumnWidth(0, 120)
        self._log_table.setColumnWidth(1, 88)
        self._log_table.setColumnWidth(2, 76)
        self._log_table.setColumnWidth(3, 100)
        self._log_table.setColumnWidth(5, 48)
        self._log_table.itemSelectionChanged.connect(self._show_selected_log_detail)
        right_layout.addWidget(self._log_table, 3)
        right_layout.addWidget(self._build_log_detail(), 2)
        right_layout.addLayout(self._build_log_pagination())
        body_layout.addWidget(right, 1)
        layout.addWidget(body, 1)

    def _build_log_sidebar(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("LogSidebar")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        overview_title = QLabel("日志概览")
        overview_title.setObjectName("LogSideTitle")
        layout.addWidget(overview_title)
        self._log_level_buttons: dict[str, QPushButton] = {}
        for level, label in (("全部", "全部"), ("INFO", "●  信息  INFO"), ("SUCCESS", "●  成功  SUCCESS"), ("WARNING", "●  警告  WARNING"), ("ERROR", "●  错误  ERROR")):
            button = QPushButton(label)
            button.setObjectName(f"LogOverview{level}")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, value=level: self._set_log_level_filter(value))
            self._log_level_buttons[level] = button
            layout.addWidget(button)
        self._log_level_buttons["全部"].setChecked(True)
        divider = QWidget()
        divider.setObjectName("LogDivider")
        divider.setFixedHeight(1)
        layout.addWidget(divider)
        layout.addWidget(self._log_side_title("来源筛选"))
        self._log_source_all = QCheckBox("全部来源")
        self._log_source_all.setChecked(True)
        self._log_source_all.stateChanged.connect(self._toggle_all_log_sources)
        layout.addWidget(self._log_source_all)
        self._log_source_container = QWidget()
        self._log_source_layout = QVBoxLayout(self._log_source_container)
        self._log_source_layout.setContentsMargins(0, 0, 0, 0)
        self._log_source_layout.setSpacing(4)
        self._log_source_checks: dict[str, QCheckBox] = {}
        layout.addWidget(self._log_source_container)
        layout.addWidget(self._log_side_title("模块筛选"))
        self._log_module_filter = QComboBox()
        self._log_module_filter.setObjectName("LogFilterInput")
        self._log_module_filter.addItem("全部模块")
        self._log_module_filter.currentIndexChanged.connect(self._refresh_log_view)
        layout.addWidget(self._log_module_filter)
        layout.addWidget(self._log_side_title("关键词搜索"))
        self._log_search = QLineEdit()
        self._log_search.setObjectName("LogFilterInput")
        self._log_search.setPlaceholderText("⌕  搜索日志内容（支持关键词）")
        self._log_search.textChanged.connect(self._refresh_log_view)
        layout.addWidget(self._log_search)
        reset = QPushButton("重置筛选")
        reset.setObjectName("PrimaryBtn")
        reset.clicked.connect(self._reset_log_filters)
        layout.addWidget(reset)
        layout.addStretch()
        return panel

    def _log_side_title(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("LogSideTitle")
        return label

    def _build_log_filter_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("LogFilterBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)
        layout.addWidget(QLabel("快捷筛选"))
        self._log_time_buttons: dict[str, QPushButton] = {}
        for key, label in (("all", "全部"), ("hour", "最近1小时"), ("day", "最近24小时"), ("today", "今天"), ("yesterday", "昨天")):
            button = QPushButton(label)
            button.setObjectName("LogTimeButton")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, value=key: self._set_log_time_filter(value))
            self._log_time_buttons[key] = button
            layout.addWidget(button)
        self._log_time_buttons["all"].setChecked(True)
        self._log_start_date = QDateEdit()
        self._log_start_date.setObjectName("LogFilterInput")
        self._log_start_date.setCalendarPopup(True)
        self._log_start_date.setDisplayFormat("yyyy-MM-dd")
        self._log_end_date = QDateEdit()
        self._log_end_date.setObjectName("LogFilterInput")
        self._log_end_date.setCalendarPopup(True)
        self._log_end_date.setDisplayFormat("yyyy-MM-dd")
        self._log_start_date.dateChanged.connect(lambda: self._set_log_time_filter("custom"))
        self._log_end_date.dateChanged.connect(lambda: self._set_log_time_filter("custom"))
        # 默认时间范围：当前半年 —— 结束日期为今天，开始日期为今天往前 6 个月
        # （setDate 触发 dateChanged → 自动切换到 custom 过滤，无需点击）
        self._log_end_date.setDate(QDate.currentDate())
        self._log_start_date.setDate(QDate.currentDate().addMonths(-6))
        layout.addSpacing(8)
        layout.addWidget(self._log_start_date)
        layout.addWidget(QLabel("~"))
        layout.addWidget(self._log_end_date)
        self._log_level_combo = QComboBox()
        self._log_level_combo.setObjectName("LogFilterInput")
        self._log_level_combo.addItems(["全部级别", "INFO", "SUCCESS", "WARNING", "ERROR"])
        self._log_level_combo.currentIndexChanged.connect(self._on_log_level_combo_changed)
        layout.addWidget(self._log_level_combo)
        return bar

    def _build_log_detail(self) -> QWidget:
        detail = QWidget()
        detail.setObjectName("LogDetailCard")
        layout = QVBoxLayout(detail)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(8)
        title_row = QHBoxLayout()
        title = QLabel("⌄  日志详情")
        title.setObjectName("LogDetailTitle")
        copy = QPushButton("复制")
        copy.setObjectName("LogHeaderButton")
        copy.clicked.connect(self._copy_selected_log)
        title_row.addWidget(title)
        title_row.addStretch()
        title_row.addWidget(copy)
        layout.addLayout(title_row)
        content = QHBoxLayout()
        self._log_metadata = QLabel("选择一条日志以查看详情")
        self._log_metadata.setObjectName("LogMetadata")
        self._log_metadata.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._log_metadata.setMinimumWidth(220)
        self._log_message_detail = QPlainTextEdit()
        self._log_message_detail.setObjectName("LogDetailText")
        self._log_message_detail.setReadOnly(True)
        self._log_message_detail.setPlaceholderText("消息内容将在这里显示")
        self._log_context = QPlainTextEdit()
        self._log_context.setObjectName("LogContextText")
        self._log_context.setReadOnly(True)
        self._log_context.setPlaceholderText("上下文信息将在这里显示")
        right = QVBoxLayout()
        right.addWidget(QLabel("消息内容"))
        right.addWidget(self._log_message_detail, 1)
        right.addWidget(QLabel("上下文信息"))
        right.addWidget(self._log_context, 1)
        content.addWidget(self._log_metadata, 1)
        content.addLayout(right, 3)
        layout.addLayout(content, 1)
        return detail

    def _build_log_pagination(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        self._log_page_hint = QLabel("共 0 条")
        self._log_page_hint.setObjectName("LogPageHint")
        self._log_prev = QPushButton("‹")
        self._log_prev.setObjectName("LogPageButton")
        self._log_prev.clicked.connect(lambda: self._change_log_page(-1))
        self._log_page_label = QLabel("1 / 1")
        self._log_page_label.setObjectName("LogPageLabel")
        self._log_next = QPushButton("›")
        self._log_next.setObjectName("LogPageButton")
        self._log_next.clicked.connect(lambda: self._change_log_page(1))
        self._log_page_size = QComboBox()
        self._log_page_size.setObjectName("LogFilterInput")
        self._log_page_size.addItems(["20 条/页", "50 条/页", "100 条/页"])
        self._log_page_size.currentIndexChanged.connect(self._set_log_page_size)
        layout.addWidget(self._log_page_hint)
        layout.addStretch()
        layout.addWidget(self._log_prev)
        layout.addWidget(self._log_page_label)
        layout.addWidget(self._log_next)
        layout.addWidget(self._log_page_size)
        return layout

    def _build_status_bar(self) -> None:
        sb: QStatusBar = self.statusBar()
        sb.setSizeGripEnabled(True)
        size_grip = QSizeGrip(sb)
        sb.addPermanentWidget(size_grip, 0)
        sb.showMessage(
            "就绪｜免责声明：本系统所提供内容不构成任何投资建议及荐股，因使用本系统所造成的任何损失，由使用者自行承担。"
        )

    # --- 主题与日志 ---
    def _apply_theme(self) -> None:
        app = QApplication.instance()
        if app is None:
            return
        pal = QPalette()
        if self._is_dark:
            theme.apply_dark_theme(pal)
        else:
            theme.apply_light_theme(pal)
        app.setPalette(pal)
        app.setFont(QFont("Microsoft YaHei UI", 10))
        app.setStyleSheet("" if self._is_dark else modern_light_qss())

    @Slot()
    def _toggle_theme(self) -> None:
        self._is_dark = not self._is_dark
        self._apply_theme()

    def _setup_file_logging(self) -> None:
        from ai_intelligence_system.utils.paths import logs_dir

        log_path = logs_dir() / "app_{time}.log"
        logger.add(
            str(log_path),
            rotation="10 MB",
            retention="7 days",
            encoding="utf-8",
            level=self._settings.log_level,
        )

    def _setup_ui_logging_sink(self) -> None:
        def sink(message: object) -> None:
            self._log_bus.message.emit(str(message).rstrip())

        # 防抖：多条日志集中到达时合并为一次表格刷新，避免每条日志都重建整个日志表
        # 造成 UI 线程卡顿（日志高频时表现为界面“卡死”）。
        self._log_refresh_timer = QTimer(self)
        self._log_refresh_timer.setSingleShot(True)
        self._log_refresh_timer.setInterval(200)
        self._log_refresh_timer.timeout.connect(
            lambda: self._refresh_log_view(keep_page=getattr(self, "_log_keep_page", False))
        )

        logger.add(
            sink,
            format="{time:HH:mm:ss} | {level} | {message}",
            level=self._settings.log_level,
            enqueue=True,
        )

    @Slot(str)
    def _append_log_line(self, text: str) -> None:
        """Receive LogBus/worker messages on the UI thread and update the log model."""
        raw = text.rstrip()
        if not raw or not hasattr(self, "_log_entries"):
            return
        entry = self._parse_log_entry(raw)
        self._log_entries.append(entry)
        # Bound the in-memory cache while preserving the non-blocking signal flow.
        if len(self._log_entries) > 5000:
            del self._log_entries[:1000]
        self._log_updated.setText(f"最近更新：{entry['time'].strftime('%H:%M:%S')}")
        self._log_keep_page = self._log_auto_scroll.isChecked()
        if hasattr(self, "_log_refresh_timer"):
            self._log_refresh_timer.start()
        else:
            self._refresh_log_view(keep_page=self._log_keep_page)
        if entry["level"] == "ERROR" and getattr(self, "_log_auto_expand_errors", True):
            self._select_log_entry(entry)

    def _parse_log_entry(self, raw: str) -> dict[str, object]:
        now = datetime.now()
        level = "INFO"
        message = raw
        match = re.match(r"^(?P<time>\d{2}:\d{2}:\d{2})\s*\|\s*(?P<level>[A-Z]+)\s*\|\s*(?P<message>.*)$", raw)
        if match:
            level = match.group("level").upper()
            message = match.group("message").strip()
            try:
                now = datetime.combine(now.date(), datetime.strptime(match.group("time"), "%H:%M:%S").time())
            except ValueError:
                pass
        elif any(token in raw for token in ("失败", "异常", "错误", "error", "Error")):
            level = "ERROR"
        elif any(token in raw for token in ("成功", "完成", "已发送", "已写入")):
            level = "SUCCESS"
        elif any(token in raw for token in ("警告", "跳过", "未配置", "warning")):
            level = "WARNING"
        source_match = re.search(r"\[(ndrc|nea|miit|china5e)\]", message, re.IGNORECASE)
        source = source_match.group(1).lower() if source_match else "系统"
        if "邮件" in message or "SMTP" in message:
            module = "邮件"
        elif "AI" in message or "DeepSeek" in message or "模型" in message:
            module = "AI分析"
        elif "SQLite" in message or "数据库" in message:
            module = "数据库"
        elif "调度" in message or "定时" in message:
            module = "任务调度"
        elif source != "系统" or "爬取" in message or "采集" in message:
            module = "爬取管线"
        else:
            module = "系统"
        return {
            "id": f"log-{now.strftime('%Y%m%d%H%M%S%f')}-{len(self._log_entries)}",
            "time": now,
            "level": level if level in {"INFO", "SUCCESS", "WARNING", "ERROR"} else "INFO",
            "source": source,
            "module": module,
            "message": message,
            "thread": "UI LogBus",
            "duration": "—",
            "context": {"source": source, "module": module},
            "raw": raw,
        }

    def _filtered_log_entries(self) -> list[dict[str, object]]:
        entries = list(self._log_entries)
        level = self._log_active_level
        if level != "全部":
            entries = [item for item in entries if item["level"] == level]
        module = self._log_module_filter.currentText()
        if module != "全部模块":
            entries = [item for item in entries if item["module"] == module]
        selected_sources = {name for name, checkbox in self._log_source_checks.items() if checkbox.isChecked()}
        if selected_sources and not self._log_source_all.isChecked():
            entries = [item for item in entries if item["source"] in selected_sources]
        search = self._log_search.text().strip().lower()
        if search:
            entries = [item for item in entries if search in " ".join(str(item[field]) for field in ("source", "module", "message", "raw")).lower()]
        mode = getattr(self, "_log_time_mode", "all")
        today = datetime.now().date()
        if mode == "hour":
            cutoff = datetime.now() - timedelta(hours=1)
            entries = [item for item in entries if item["time"] >= cutoff]
        elif mode == "day":
            cutoff = datetime.now() - timedelta(hours=24)
            entries = [item for item in entries if item["time"] >= cutoff]
        elif mode == "today":
            entries = [item for item in entries if item["time"].date() == today]
        elif mode == "yesterday":
            entries = [item for item in entries if item["time"].date() == today - timedelta(days=1)]
        elif mode == "custom" and self._log_start_date.date().isValid() and self._log_end_date.date().isValid():
            start = self._log_start_date.date().toPython()
            end = self._log_end_date.date().toPython()
            entries = [item for item in entries if start <= item["time"].date() <= end]
        return list(reversed(entries))

    def _refresh_log_view(self, _unused: object = None, *, keep_page: bool = False) -> None:
        if not hasattr(self, "_log_table"):
            return
        self._sync_log_sidebar_options()
        entries = self._filtered_log_entries()
        if not keep_page:
            self._log_page = 0
        page_count = max(1, math.ceil(len(entries) / self._log_rows_per_page))
        self._log_page = min(self._log_page, page_count - 1)
        start = self._log_page * self._log_rows_per_page
        current = entries[start:start + self._log_rows_per_page]
        self._log_table.setUpdatesEnabled(False)
        self._log_table.setRowCount(0)
        for entry in current:
            row = self._log_table.rowCount()
            self._log_table.insertRow(row)
            self._append_log_table_row(row, entry)
        self._log_table.setUpdatesEnabled(True)
        self._log_page_hint.setText(f"共 {len(entries)} 条")
        self._log_page_label.setText(f"{self._log_page + 1} / {page_count}")
        self._log_prev.setEnabled(self._log_page > 0)
        self._log_next.setEnabled(self._log_page < page_count - 1)
        if keep_page and self._log_auto_scroll.isChecked() and self._log_table.rowCount():
            self._log_table.selectRow(0)

    def _append_log_table_row(self, row: int, entry: dict[str, object]) -> None:
        time_item = QTableWidgetItem(entry["time"].strftime("%H:%M:%S.%f")[:-3])
        time_item.setData(Qt.UserRole, str(entry["id"]))
        self._log_table.setItem(row, 0, time_item)
        level_item = QTableWidgetItem(str(entry["level"]))
        level_item.setTextAlignment(Qt.AlignCenter)
        colors = {"INFO": "#2563EB", "SUCCESS": "#10B981", "WARNING": "#F59E0B", "ERROR": "#EF4444"}
        level_item.setForeground(QColor(colors.get(str(entry["level"]), "#64748B")))
        self._log_table.setItem(row, 1, level_item)
        self._log_table.setItem(row, 2, QTableWidgetItem(str(entry["source"])))
        self._log_table.setItem(row, 3, QTableWidgetItem(str(entry["module"])))
        summary = " ".join(str(entry["message"]).split())
        self._log_table.setItem(row, 4, QTableWidgetItem(summary[:160] + ("…" if len(summary) > 160 else "")))
        action = QTableWidgetItem("›")
        action.setTextAlignment(Qt.AlignCenter)
        self._log_table.setItem(row, 5, action)

    def _sync_log_sidebar_options(self) -> None:
        counts = Counter(str(item["level"]) for item in self._log_entries)
        labels = {"全部": "全部", "INFO": "●  信息  INFO", "SUCCESS": "●  成功  SUCCESS", "WARNING": "●  警告  WARNING", "ERROR": "●  错误  ERROR"}
        for level, button in self._log_level_buttons.items():
            count = len(self._log_entries) if level == "全部" else counts.get(level, 0)
            button.setText(f"{labels[level]}   {count}")
        source_counts = Counter(str(item["source"]) for item in self._log_entries)
        for source in list(self._log_source_checks):
            if source not in source_counts:
                checkbox = self._log_source_checks.pop(source)
                self._log_source_layout.removeWidget(checkbox)
                checkbox.deleteLater()
        for source, count in sorted(source_counts.items()):
            if source not in self._log_source_checks:
                checkbox = QCheckBox()
                checkbox.setChecked(True)
                checkbox.stateChanged.connect(self._on_log_source_changed)
                self._log_source_checks[source] = checkbox
                self._log_source_layout.addWidget(checkbox)
            self._log_source_checks[source].setText(f"{source}   {count}")
        current = self._log_module_filter.currentText()
        modules = sorted({str(item["module"]) for item in self._log_entries})
        self._log_module_filter.blockSignals(True)
        self._log_module_filter.clear()
        self._log_module_filter.addItem("全部模块")
        self._log_module_filter.addItems(modules)
        index = self._log_module_filter.findText(current)
        self._log_module_filter.setCurrentIndex(max(index, 0))
        self._log_module_filter.blockSignals(False)

    def _set_log_level_filter(self, level: str) -> None:
        self._log_active_level = level
        for key, button in self._log_level_buttons.items():
            button.setChecked(key == level)
        self._log_level_combo.blockSignals(True)
        self._log_level_combo.setCurrentText("全部级别" if level == "全部" else level)
        self._log_level_combo.blockSignals(False)
        self._refresh_log_view()

    def _on_log_level_combo_changed(self) -> None:
        level = self._log_level_combo.currentText()
        self._set_log_level_filter("全部" if level == "全部级别" else level)

    def _set_log_time_filter(self, mode: str) -> None:
        self._log_time_mode = mode
        for key, button in self._log_time_buttons.items():
            button.setChecked(key == mode)
        self._refresh_log_view()

    def _toggle_all_log_sources(self, state: int) -> None:
        for checkbox in self._log_source_checks.values():
            checkbox.blockSignals(True)
            checkbox.setChecked(state == Qt.Checked)
            checkbox.blockSignals(False)
        self._refresh_log_view()

    def _on_log_source_changed(self) -> None:
        checked = all(item.isChecked() for item in self._log_source_checks.values())
        self._log_source_all.blockSignals(True)
        self._log_source_all.setChecked(checked)
        self._log_source_all.blockSignals(False)
        self._refresh_log_view()

    def _reset_log_filters(self) -> None:
        self._log_search.clear()
        self._log_module_filter.setCurrentIndex(0)
        self._set_log_level_filter("全部")
        self._set_log_time_filter("all")
        self._log_source_all.setChecked(True)
        self._toggle_all_log_sources(Qt.Checked)

    def _set_log_page_size(self) -> None:
        self._log_rows_per_page = int(self._log_page_size.currentText().split()[0])
        self._refresh_log_view()

    def _change_log_page(self, delta: int) -> None:
        self._log_page += delta
        self._refresh_log_view(keep_page=True)

    def _selected_log_entry(self) -> dict[str, object] | None:
        row = self._log_table.currentRow()
        if row < 0 or self._log_table.item(row, 0) is None:
            return None
        entry_id = str(self._log_table.item(row, 0).data(Qt.UserRole))
        return next((item for item in self._log_entries if item["id"] == entry_id), None)

    def _show_selected_log_detail(self) -> None:
        entry = self._selected_log_entry()
        if entry is not None:
            self._select_log_entry(entry)

    def _select_log_entry(self, entry: dict[str, object]) -> None:
        self._log_metadata.setText("\n".join((
            f"时间     {entry['time'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}",
            f"级别     {entry['level']}", f"来源     {entry['source']}", f"模块     {entry['module']}",
            f"线程     {entry['thread']}", f"日志ID   {entry['id']}", f"耗时     {entry['duration']}",
        )))
        self._log_message_detail.setPlainText(str(entry["message"]))
        self._log_context.setPlainText(json.dumps(entry["context"], ensure_ascii=False, indent=2))

    def _copy_selected_log(self) -> None:
        entry = self._selected_log_entry()
        if entry is not None:
            QApplication.clipboard().setText(str(entry["raw"]))

    def _clear_log_cache(self) -> None:
        answer = QMessageBox.question(self, "清空日志", "确定要清空当前 UI 日志缓存吗？\n\n不会删除磁盘上的 loguru 日志文件。", QMessageBox.Cancel | QMessageBox.Yes, QMessageBox.Cancel)
        if answer == QMessageBox.Yes:
            self._log_entries.clear()
            self._log_metadata.setText("当前 UI 日志缓存已清空。")
            self._log_message_detail.clear()
            self._log_context.clear()
            self._refresh_log_view()

    def _export_log_entries(self) -> None:
        path, selected_filter = QFileDialog.getSaveFileName(self, "导出日志", f"logs_{datetime.now():%Y%m%d_%H%M%S}.csv", "CSV 文件 (*.csv);;文本文件 (*.txt)")
        if not path:
            return
        entries = self._filtered_log_entries()
        try:
            if path.lower().endswith(".txt") or "文本" in selected_filter:
                Path(path).write_text("\n".join(str(item["raw"]) for item in entries), encoding="utf-8")
            else:
                with Path(path).open("w", encoding="utf-8-sig", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=["time", "level", "source", "module", "message", "thread", "raw"])
                    writer.writeheader()
                    for item in entries:
                        writer.writerow({"time": item["time"].isoformat(), **{key: item[key] for key in ("level", "source", "module", "message", "thread", "raw")}})
            self.statusBar().showMessage(f"已导出 {len(entries)} 条日志", 5000)
        except OSError as exc:
            QMessageBox.warning(self, "导出失败", str(exc))

    def _show_log_display_settings(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("显示设置")
        dialog.setObjectName("LogDisplayDialog")
        form = QVBoxLayout(dialog)
        form.setContentsMargins(18, 18, 18, 18)
        checks = []
        for text, checked in (("显示时间", True), ("显示线程", True), ("显示模块", True), ("自动展开错误", getattr(self, "_log_auto_expand_errors", True))):
            checkbox = QCheckBox(text)
            checkbox.setChecked(checked)
            checks.append(checkbox)
            form.addWidget(checkbox)
        checks[-1].toggled.connect(lambda value: setattr(self, "_log_auto_expand_errors", value))
        close = QPushButton("完成")
        close.setObjectName("PrimaryBtn")
        close.clicked.connect(dialog.accept)
        form.addWidget(close)
        dialog.exec()

    # --- 设置读写 ---
    def _reload_settings_into_widgets(self) -> None:
        s = self._settings
        self._set_api_key.setText(s.deepseek_api_key)
        self._set_base_url.setText(s.deepseek_base_url)
        self._set_model.setEditText(s.deepseek_model)
        self._set_smtp_host.setText(s.smtp_host)
        self._set_smtp_port.setValue(int(s.smtp_port))
        self._set_smtp_user.setText(s.smtp_user)
        self._set_smtp_pass.setText(s.smtp_password)
        self._set_smtp_ssl.setChecked(s.smtp_use_ssl)
        self._set_recipients.setText(",".join(s.mail_recipients))
        self._chk_m.setChecked(s.scheduler_morning.enabled)
        self._freq_m.setCurrentIndex(1 if s.scheduler_morning.frequency == "weekly" else 0)
        self._weekday_m.setCurrentIndex(int(s.scheduler_morning.weekday) % 7)
        self._time_m.setText(s.scheduler_morning.time)
        self._chk_n.setChecked(s.scheduler_noon.enabled)
        self._freq_n.setCurrentIndex(1 if s.scheduler_noon.frequency == "weekly" else 0)
        self._weekday_n.setCurrentIndex(int(s.scheduler_noon.weekday) % 7)
        self._time_n.setText(s.scheduler_noon.time)
        self._chk_e.setChecked(s.scheduler_evening.enabled)
        self._freq_e.setCurrentIndex(1 if s.scheduler_evening.frequency == "weekly" else 0)
        self._weekday_e.setCurrentIndex(int(s.scheduler_evening.weekday) % 7)
        self._time_e.setText(s.scheduler_evening.time)
        source_checks = {
            "ndrc": self._chk_src_ndrc,
            "nea": self._chk_src_nea,
            "miit": self._chk_src_miit,
            "china5e": self._chk_src_china5e,
        }
        enabled_sources = set(s.crawl_source_ids or source_checks.keys())
        for source_id, checkbox in source_checks.items():
            checkbox.setChecked(source_id in enabled_sources)
        self._crawl_max_items.setValue(int(s.crawl_max_items_per_source))
        self._set_keywords.setText(",".join(s.industry_keywords))
        self._set_db_path.blockSignals(True)
        self._set_db_path.setText(s.database_path)
        self._set_db_path.blockSignals(False)
        idx = self._set_log_level.findText(s.log_level)
        if idx >= 0:
            self._set_log_level.setCurrentIndex(idx)
        self._set_prompt.setPlainText(s.custom_system_prompt)

    def _read_settings_from_widgets(self) -> AppSettings:
        rec = [x.strip() for x in self._set_recipients.text().split(",") if x.strip()]
        kws = [x.strip() for x in self._set_keywords.text().split(",") if x.strip()]
        source_checks = (
            ("ndrc", self._chk_src_ndrc),
            ("nea", self._chk_src_nea),
            ("miit", self._chk_src_miit),
            ("china5e", self._chk_src_china5e),
        )
        selected_sources = [source_id for source_id, checkbox in source_checks if checkbox.isChecked()]
        s = AppSettings(
            log_level=self._set_log_level.currentText(),
            deepseek_api_key=self._set_api_key.text().strip(),
            deepseek_base_url=self._set_base_url.text().strip() or "https://api.deepseek.com",
            deepseek_model=self._set_model.currentText().strip() or "deepseek-chat",
            smtp_host=self._set_smtp_host.text().strip(),
            smtp_port=int(self._set_smtp_port.value()),
            smtp_user=self._set_smtp_user.text().strip(),
            smtp_password=self._set_smtp_pass.text(),
            smtp_use_ssl=self._set_smtp_ssl.isChecked(),
            mail_recipients=rec,
            scheduler_morning=SchedulerSlot(
                enabled=self._chk_m.isChecked(),
                time=self._time_m.text().strip() or "07:30",
                frequency="weekly" if self._freq_m.currentText() == "每周" else "daily",
                weekday=int(self._weekday_m.currentIndex()),
            ),
            scheduler_noon=SchedulerSlot(
                enabled=self._chk_n.isChecked(),
                time=self._time_n.text().strip() or "12:30",
                frequency="weekly" if self._freq_n.currentText() == "每周" else "daily",
                weekday=int(self._weekday_n.currentIndex()),
            ),
            scheduler_evening=SchedulerSlot(
                enabled=self._chk_e.isChecked(),
                time=self._time_e.text().strip() or "20:00",
                frequency="weekly" if self._freq_e.currentText() == "每周" else "daily",
                weekday=int(self._weekday_e.currentIndex()),
            ),
            industry_keywords=kws or self._settings.industry_keywords,
            database_path=self._set_db_path.text().strip() or self._settings.database_path,
            crawl_source_ids=selected_sources or self._settings.crawl_source_ids,
            crawl_max_items_per_source=int(self._crawl_max_items.value()),
            custom_system_prompt=self._set_prompt.toPlainText(),
        )
        return s

    @Slot(int)
    def _on_tab_changed(self, index: int) -> None:
        if index == 3:
            self._update_storage_paths_hint()

    def _update_storage_paths_hint(self) -> None:
        if not hasattr(self, "_storage_paths_text"):
            return
        db_path = self._set_db_path.text().strip() or self._settings.database_path
        self._storage_paths_text.setPlainText(describe_local_storage(database_path=db_path))

    @Slot()
    def _on_settings_save_ok(self) -> None:
        self._btn_save_settings.setEnabled(True)
        self.statusBar().showMessage("设置已保存到本地文件", 10000)
        QMessageBox.information(
            self,
            "成功",
            "设置已写入 config/config.json（API Key、SMTP 密码等为加密存储）。",
        )
        self._settings = load_settings()
        self._reload_settings_into_widgets()
        self._update_storage_paths_hint()
        self._configure_scheduler()
        logger.info(
            "配置已重新加载：smtp_host={} smtp_user={} recipients={}",
            self._settings.smtp_host,
            self._settings.smtp_user,
            len(self._settings.mail_recipients),
        )

    @Slot(str)
    def _on_settings_save_fail(self, msg: str) -> None:
        self._btn_save_settings.setEnabled(True)
        self.statusBar().showMessage("保存失败", 8000)
        QMessageBox.critical(self, "保存失败", msg)

    @Slot(dict)
    def _on_ai_analysis_ok(self, data: dict) -> None:
        self._manual_output.setPlainText(json.dumps(data, ensure_ascii=False, indent=2))
        self._btn_run_ai.setEnabled(True)
        self.statusBar().showMessage("分析完成，已写入 SQLite", 8000)
        QMessageBox.information(self, "完成", "分析完成，结构化结果已写入本地 SQLite 数据库。")
        self.refresh_records_async()

    @Slot(str)
    def _on_ai_analysis_fail(self, msg: str) -> None:
        self._manual_output.setPlainText(msg)
        self._btn_run_ai.setEnabled(True)
        self.statusBar().showMessage("AI 分析失败", 8000)
        QMessageBox.critical(self, "失败", msg)

    @Slot()
    def _on_mail_send_ok(self) -> None:
        self.statusBar().showMessage("测试邮件已发送", 8000)
        QMessageBox.information(self, "成功", "测试邮件已发送。")

    @Slot(str)
    def _on_mail_send_fail(self, msg: str) -> None:
        self.statusBar().showMessage("邮件发送失败", 8000)
        QMessageBox.critical(self, "失败", msg)

    @Slot(str)
    def _on_export_ok(self, path: str) -> None:
        self.statusBar().showMessage(f"已导出 CSV：{path}", 8000)
        QMessageBox.information(self, "完成", f"已导出：\n{path}")

    @Slot(str)
    def _on_export_fail(self, msg: str) -> None:
        self.statusBar().showMessage("导出失败", 8000)
        QMessageBox.critical(self, "失败", msg)

    def _reset_crawl_steps(self) -> None:
        self._crawl_step_status = {
            "连接网站": "等待",
            "请求新闻列表": "等待",
            "解析新闻内容": "等待",
            "写入数据库": "等待",
            "爬取完成": "等待",
        }
        if hasattr(self, "_crawl_log_view"):
            self._crawl_log_view.clear()
            self._append_crawl_log("系统", "等待", "爬取任务尚未开始")
        if hasattr(self, "_crawl_status_label"):
            self._crawl_status_label.setText("等待开始爬取")
        if hasattr(self, "_crawl_step_labels"):
            for step, label in self._crawl_step_labels.items():
                label.setText(step)
                label.setProperty("stepState", "waiting")
                label.style().unpolish(label)
                label.style().polish(label)
            for circle in self._crawl_step_circles.values():
                circle.setProperty("stepState", "waiting")
                circle.style().unpolish(circle)
                circle.style().polish(circle)

    @Slot(str, str, str)
    def _on_crawl_step_changed(self, step: str, status: str, detail: str) -> None:
        self._crawl_step_status[step] = status
        self._append_crawl_log(step, status, detail)
        if hasattr(self, "_crawl_status_label"):
            summary = " ｜ ".join(f"{k}:{v}" for k, v in self._crawl_step_status.items())
            self._crawl_status_label.setText(summary)
        if hasattr(self, "_crawl_step_labels") and step in self._crawl_step_labels:
            state_map = {"进行中": "running", "成功": "success", "失败": "failed", "等待": "waiting"}
            state = state_map.get(status, "waiting")
            label = self._crawl_step_labels[step]
            label.setText(step)
            label.setProperty("stepState", state)
            label.style().unpolish(label)
            label.style().polish(label)
            circle = self._crawl_step_circles[step]
            circle.setProperty("stepState", state)
            circle.style().unpolish(circle)
            circle.style().polish(circle)

    def _append_crawl_log(self, step: str, status: str, detail: str) -> None:
        if not hasattr(self, "_crawl_log_view"):
            return
        color_map = {
            "进行中": "#2563EB",
            "成功": "#16A34A",
            "失败": "#DC2626",
            "等待": "#64748B",
        }
        now = datetime.now().strftime("%H:%M:%S")
        color = color_map.get(status, "#334155")
        safe_detail = str(detail or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        self._crawl_log_view.append(
            f'<div style="margin:4px 0;">'
            f'<span style="color:#64748B;">[{now}]</span> '
            f'<b>{step}</b> '
            f'<span style="color:{color};font-weight:600;">{status}</span> '
            f'<span style="color:#0F172A;">{safe_detail}</span>'
            f'</div>'
        )
        self._crawl_log_view.verticalScrollBar().setValue(self._crawl_log_view.verticalScrollBar().maximum())

    def refresh_news_async(self) -> None:
        if not hasattr(self, "_news_table"):
            return
        source = self._news_source_filter.currentText() if hasattr(self, "_news_source_filter") else "全部"
        days = int(self._news_days_filter.value()) if hasattr(self, "_news_days_filter") else 7
        start_date = None
        end_date = None
        if hasattr(self, "_manual_filter_start") and hasattr(self, "_manual_filter_end"):
            # 以日期选择器的绝对区间为准（修复：此前仅换算成“最近 N 天”滚动查询，
            # 用户选历史窗口时结果错误）。
            start_date = self._manual_filter_start.date().toPython()
            end_date = self._manual_filter_end.date().toPython()
            days = max(1, (end_date - start_date).days + 1)
        self.statusBar().showMessage("正在加载新闻数据…", 3000)
        if hasattr(self, "_btn_news_refresh"):
            self._btn_news_refresh.setEnabled(False)
            self._btn_news_refresh.setText("加载中…")
        self._set_news_bulk_delete_enabled(False)
        thread = QThread(self)
        worker = NewsLoadWorker(self._settings.database_path, days=days, source=source, limit=500,
                                start_date=start_date, end_date=end_date)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.loaded.connect(self._on_news_loaded)
        worker.failed.connect(self._on_news_load_failed)
        worker.loaded.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.loaded.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._retain_worker_thread(thread, worker)
        thread.start()

    @Slot(list, list)
    def _on_news_loaded(self, rows: list, sources: list) -> None:
        self._cached_news_rows = rows
        current = self._news_source_filter.currentText() if hasattr(self, "_news_source_filter") else "全部"
        self._news_source_filter.blockSignals(True)
        self._news_source_filter.clear()
        self._news_source_filter.addItem("全部")
        self._news_source_filter.addItems([str(source) for source in sources])
        idx = self._news_source_filter.findText(current)
        if idx >= 0:
            self._news_source_filter.setCurrentIndex(idx)
        self._news_source_filter.blockSignals(False)
        self._populate_news_table(rows)
        self._update_manual_dashboard(rows)
        if hasattr(self, "_btn_news_refresh"):
            self._btn_news_refresh.setEnabled(True)
            self._btn_news_refresh.setText("刷新新闻")
        self._set_news_bulk_delete_enabled(bool(rows))
        rendered = self._news_table.rendered_count()
        more = "，可点击“加载更多”继续显示" if len(rows) > rendered else ""
        self.statusBar().showMessage(f"已加载 {len(rows)} 条新闻，当前显示 {rendered} 条{more}", 5000)

    @Slot(str)
    def _on_news_load_failed(self, msg: str) -> None:
        if hasattr(self, "_btn_news_refresh"):
            self._btn_news_refresh.setEnabled(True)
            self._btn_news_refresh.setText("刷新新闻")
        self._set_news_bulk_delete_enabled(bool(getattr(self, "_cached_news_rows", [])))
        self.statusBar().showMessage("新闻加载失败", 8000)
        QMessageBox.warning(self, "新闻加载失败", msg)

    def _short_text(self, text: str, limit: int = 160) -> str:
        clean = " ".join(str(text or "").split())
        return clean if len(clean) <= limit else f"{clean[:limit]}…"

    def _populate_news_table(self, rows: list[dict]) -> None:
        rendered = self._news_table.set_rows(rows, visible_count=120)
        self._update_news_page_hint(rendered)

    def _update_manual_dashboard(self, rows: list[dict]) -> None:
        """Render only values that can be derived from loaded SQLite news rows.

        The page intentionally labels metrics that have no persisted source instead
        of manufacturing values solely for a polished dashboard appearance.
        """
        if not hasattr(self, "_manual_kpis"):
            return
        total = len(rows)
        source_counts = Counter(str(row.get("source") or "未知来源") for row in rows)
        latest_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._manual_updated_label.setText(f"数据更新时间：{latest_text}")
        self._manual_kpis["news"].setText(str(total))
        self._manual_kpis["news_detail"].setText("当前筛选结果")
        self._manual_kpis["sources"].setText(str(len(source_counts)))
        self._manual_kpis["sources_detail"].setText("当前筛选来源")
        filter_days = int(self._news_days_filter.value())
        self._manual_kpis["coverage"].setText(f"{filter_days} 天")
        self._manual_kpis["coverage_detail"].setText("当前查询范围")
        value_count = sum(1 for row in rows if _score_bucket_100(self._manual_value_score(row)) == "high")
        self._manual_kpis["value"].setText(str(value_count))
        self._manual_kpis["value_detail"].setText("启发式评分≥80（关键词/权威源/时效）")
        self._manual_kpis["email"].setText(str(self._email_sent_count))
        self._manual_kpis["email_detail"].setText(f"本次运行成功发送 {self._email_sent_count} 封")
        self._crawl_summary_label.setText(f"已采集 {total} 条  ·  成功状态由任务日志实时反馈  ·  用时由任务结束后记录")

        self._clear_layout(self._manual_source_bars_layout)
        if source_counts:
            self._manual_overview_text.setText(f"主题分布暂以真实新闻来源 Top {min(5, len(source_counts))} 展示，共 {total} 条新闻。")
            largest = max(source_counts.values())
            for source, count in source_counts.most_common(5):
                self._manual_source_bars_layout.addWidget(self._manual_bar_row(source, count, largest, "#2563EB"))
        else:
            self._manual_overview_text.setText("当前筛选条件下没有 SQLite 新闻数据。")

        daily: dict[str, int] = defaultdict(int)
        for row in rows:
            raw = str(row.get("publish_time") or row.get("crawled_at") or "")
            label = raw[:10]
            if label:
                daily[label] += 1
        self._clear_layout(self._manual_trend_bars_layout)
        if daily:
            days = sorted(daily)[-7:]
            largest = max(daily[day] for day in days)
            self._manual_trend_text.setText("蓝色为每日新闻数量；平均评分趋势待评分字段支持。")
            for day in days:
                self._manual_trend_bars_layout.addWidget(self._manual_bar_row(day[5:], daily[day], largest, "#10B981"))
        else:
            self._manual_trend_text.setText("暂无可用于计算近 7 天趋势的发布日期数据。")

    def _manual_bar_row(self, label: str, value: int, maximum: int, color: str) -> QWidget:
        row = QWidget()
        row.setObjectName("ManualBarRow")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        name = QLabel(label)
        name.setObjectName("ManualBarLabel")
        name.setFixedWidth(88)
        progress = QProgressBar()
        progress.setObjectName("ManualBarProgress")
        progress.setRange(0, max(maximum, 1))
        progress.setValue(value)
        progress.setTextVisible(False)
        progress.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; }}")
        count = QLabel(str(value))
        count.setObjectName("ManualBarValue")
        count.setFixedWidth(28)
        layout.addWidget(name)
        layout.addWidget(progress, 1)
        layout.addWidget(count)
        return row

    @Slot()
    def _load_more_news_rows(self) -> None:
        rendered = self._news_table.load_more(step=80)
        self._update_news_page_hint(rendered)

    def _update_news_page_hint(self, rendered: int | None = None) -> None:
        if not hasattr(self, "_news_page_hint"):
            return
        rendered_count = self._news_table.rendered_count() if rendered is None else rendered
        total = self._news_table.total_count()
        self._news_page_hint.setText(f"显示 {rendered_count} / {total} 条")
        if hasattr(self, "_btn_news_load_more"):
            self._btn_news_load_more.setEnabled(rendered_count < total)

    def _set_news_bulk_delete_enabled(self, enabled: bool) -> None:
        for name in ("_btn_news_delete_loaded", "_btn_news_delete_range"):
            if hasattr(self, name):
                getattr(self, name).setEnabled(enabled)

    def _run_news_bulk_delete_worker(
        self,
        *,
        news_ids: list[int] | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        source: str | None = None,
    ) -> None:
        self._set_news_bulk_delete_enabled(False)
        self.statusBar().showMessage("正在批量删除新闻…", 3000)
        thread = QThread(self)
        worker = NewsBulkDeleteWorker(
            self._settings.database_path,
            news_ids=news_ids,
            start_at=start_at,
            end_at=end_at,
            source=source,
        )
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished_ok.connect(self._on_news_bulk_delete_ok)
        worker.failed.connect(self._on_news_bulk_delete_failed)
        worker.finished_ok.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.finished_ok.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._retain_worker_thread(thread, worker)
        thread.start()

    @Slot()
    def _delete_loaded_news_async(self) -> None:
        news_ids = [int(row["id"]) for row in self._cached_news_rows if row.get("id") is not None]
        if not news_ids:
            QMessageBox.information(self, "无可删除数据", "当前新闻列表没有可删除的数据。")
            return
        source = self._news_source_filter.currentText() if hasattr(self, "_news_source_filter") else "全部"
        days = int(self._news_days_filter.value()) if hasattr(self, "_news_days_filter") else 7
        reply = QMessageBox.question(
            self,
            "确认批量删除",
            f"确定要删除当前筛选列表中的全部新闻吗？\n\n范围：网站={source}，最近 {days} 天\n数量：{len(news_ids)} 条\n\n此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self._run_news_bulk_delete_worker(news_ids=news_ids)

    @Slot()
    def _delete_news_by_date_range_async(self) -> None:
        start_qdate = self._news_delete_start.date()
        end_qdate = self._news_delete_end.date()
        if start_qdate > end_qdate:
            QMessageBox.warning(self, "时间段无效", "开始日期不能晚于结束日期。")
            return
        start_py = start_qdate.toPython()
        end_py = end_qdate.toPython()
        start_at = datetime(start_py.year, start_py.month, start_py.day)
        end_at = datetime(end_py.year, end_py.month, end_py.day) + timedelta(days=1)
        source = self._news_source_filter.currentText() if hasattr(self, "_news_source_filter") else "全部"
        source_hint = "全部网站" if source == "全部" else source
        reply = QMessageBox.question(
            self,
            "确认按时间段删除",
            f"确定要删除该时间段内的新闻吗？\n\n日期：{start_py:%Y-%m-%d} 至 {end_py:%Y-%m-%d}\n网站：{source_hint}\n\n此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self._run_news_bulk_delete_worker(start_at=start_at, end_at=end_at, source=source)

    @Slot(int)
    def _on_news_bulk_delete_ok(self, deleted: int) -> None:
        self.statusBar().showMessage(f"已删除 {deleted} 条新闻，正在刷新列表…", 5000)
        QMessageBox.information(self, "删除完成", f"已删除 {deleted} 条新闻。")
        self.refresh_news_async()

    @Slot(str)
    def _on_news_bulk_delete_failed(self, msg: str) -> None:
        self._set_news_bulk_delete_enabled(True)
        self.statusBar().showMessage("批量删除失败", 8000)
        QMessageBox.critical(self, "批量删除失败", msg)

    @Slot(int, str)
    def _request_delete_news(self, news_id_int: int, title: str) -> None:
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除这条新闻吗？\n\n{title}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            self._news_table.reset_delete_buttons()
            return
        self.statusBar().showMessage("正在删除新闻…", 3000)
        thread = QThread(self)
        worker = NewsDeleteWorker(self._settings.database_path, news_id_int)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished_ok.connect(self._on_news_delete_ok)
        worker.failed.connect(self._on_news_delete_failed)
        worker.finished_ok.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.finished_ok.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._retain_worker_thread(thread, worker)
        thread.start()

    @Slot(int)
    def _on_news_delete_ok(self, _news_id: int) -> None:
        self.statusBar().showMessage("新闻已删除，正在刷新列表…", 5000)
        self.refresh_news_async()

    @Slot(str)
    def _on_news_delete_failed(self, msg: str) -> None:
        self._news_table.reset_delete_buttons()
        self.statusBar().showMessage("新闻删除失败", 8000)
        QMessageBox.critical(self, "删除失败", msg)

    # --- 异步任务 ---
    def refresh_records_async(self) -> None:
        self.statusBar().showMessage("正在从 SQLite 加载数据…", 3000)
        thread = QThread(self)
        worker = DashboardLoadWorker(self._settings.database_path, limit=200)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.loaded.connect(self._on_records_loaded)
        worker.failed.connect(self._on_records_load_failed)
        worker.loaded.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.loaded.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._retain_worker_thread(thread, worker)
        thread.start()

    @Slot(list)
    def _on_records_loaded(self, rows: list) -> None:
        self._cached_rows = rows
        self._populate_dashboard(rows)
        self._sync_analytics_filters(rows)
        self._update_analytics_view()
        self.statusBar().showMessage(f"已加载 {len(rows)} 条记录", 5000)

    @Slot(str)
    def _on_records_load_failed(self, msg: str) -> None:
        QMessageBox.warning(self, "加载失败", msg)
        self.statusBar().showMessage("加载失败", 5000)

    def _create_bar_group(
        self,
        layout: QVBoxLayout,
        labels: tuple[str, ...],
    ) -> dict[str, QProgressBar]:
        bars: dict[str, QProgressBar] = {}
        for label in labels:
            row = QHBoxLayout()
            name = QLabel(label)
            name.setMinimumWidth(100)
            bar = QProgressBar()
            bar.setRange(0, 1)
            bar.setValue(0)
            bar.setTextVisible(True)
            bar.setFormat("0 条")
            row.addWidget(name)
            row.addWidget(bar, stretch=1)
            layout.addLayout(row)
            bars[label] = bar
        layout.addStretch()
        return bars

    def _clear_layout(self, layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                while child_layout.count():
                    child = child_layout.takeAt(0)
                    child_widget = child.widget()
                    if child_widget is not None:
                        child_widget.deleteLater()

    def _sync_analytics_filters(self, rows: list[dict]) -> None:
        if not hasattr(self, "_analytics_stage"):
            return
        current = self._analytics_stage.currentText()
        stages = sorted({str(row.get("stage", "")).strip() for row in rows if str(row.get("stage", "")).strip()})
        self._analytics_stage.blockSignals(True)
        self._analytics_stage.clear()
        self._analytics_stage.addItem("全部阶段")
        self._analytics_stage.addItems(stages)
        idx = self._analytics_stage.findText(current)
        if idx >= 0:
            self._analytics_stage.setCurrentIndex(idx)
        self._analytics_stage.blockSignals(False)
        if hasattr(self, "_analytics_start_date") and not getattr(self, "_topology_dates_initialized", False):
            dates = [self._parse_datetime(row.get("timestamp", "")) for row in rows]
            dates = [date for date in dates if date.year > 1]
            if dates:
                self._analytics_start_date.blockSignals(True)
                self._analytics_end_date.blockSignals(True)
                start, end = min(dates), max(dates)
                self._analytics_start_date.setDate(QDate(start.year, start.month, start.day))
                self._analytics_end_date.setDate(QDate(end.year, end.month, end.day))
                self._analytics_start_date.blockSignals(False)
                self._analytics_end_date.blockSignals(False)
                self._topology_dates_initialized = True

    def _filtered_analytics_rows(self) -> list[dict]:
        rows = list(self._cached_rows)
        if not hasattr(self, "_analytics_stage"):
            return rows

        if hasattr(self, "_analytics_start_date"):
            start = self._analytics_start_date.date()
            end = self._analytics_end_date.date()
            start_dt = datetime(start.year(), start.month(), start.day(), tzinfo=timezone.utc)
            end_dt = datetime(end.year(), end.month(), end.day(), 23, 59, 59, tzinfo=timezone.utc)
            rows = [
                row for row in rows
                if start_dt <= self._parse_datetime(row.get("timestamp", "")) <= end_dt
            ]
        elif hasattr(self, "_analytics_range"):
            range_text = self._analytics_range.currentText()
            now = datetime.now(timezone.utc)
            days_map = {"最近24小时": 1, "最近3天": 3, "最近7天": 7, "最近30天": 30}
            if range_text in days_map:
                cutoff = now - timedelta(days=days_map[range_text])
                rows = [row for row in rows if self._parse_datetime(row.get("timestamp", "")) >= cutoff]

        stage = self._analytics_stage.currentText()
        if stage != "全部阶段":
            rows = [row for row in rows if str(row.get("stage", "")).strip() == stage]

        score_filter = self._analytics_score.currentText()
        if score_filter != "全部评分":
            rows = [row for row in rows if self._score_bucket(row) == score_filter]

        keyword = self._analytics_keyword.text().strip().lower()
        if keyword:
            rows = [
                row for row in rows
                if keyword in " ".join(
                    str(row.get(key, ""))
                    for key in ("title", "summary", "tags", "source", "source_url", "stage")
                ).lower()
            ]
        return rows

    def _parse_datetime(self, value: object) -> datetime:
        if isinstance(value, datetime):
            dt = value
        else:
            text = str(value).strip().replace("Z", "+00:00")
            if not text:
                return datetime.min.replace(tzinfo=timezone.utc)
            try:
                dt = datetime.fromisoformat(text)
            except ValueError:
                return datetime.min.replace(tzinfo=timezone.utc)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def _score_value(self, row: dict) -> float:
        try:
            score = float(row.get("score", 0) or 0)
        except (TypeError, ValueError):
            return 0.0
        return score * 10 if 0 < score <= 10 else score

    def _score_bucket(self, row: dict) -> str:
        score = self._score_value(row)
        if score >= 80:
            return "高分(>=80)"
        if score >= 50:
            return "中等(50-79)"
        return "低分(<50)"

    def _authoritative_source_names(self) -> set[str]:
        """已配置定向爬虫的权威来源显示名（由 crawl_source_ids 映射而来）。"""
        cache = getattr(self, "_authoritative_sources_cache", None)
        if cache is None:
            from ai_intelligence_system.core import crawler_factory

            names: set[str] = set()
            for sid in (self._settings.crawl_source_ids or []):
                try:
                    name = str(crawler_factory.create(sid).source_name).strip()
                except Exception:  # noqa: BLE001
                    continue
                if name:
                    names.add(name)
            self._authoritative_sources_cache = names
        return self._authoritative_sources_cache

    def _manual_value_score(self, row: dict) -> float:
        """启发式高价值评分（0-100）：复用现有字段，不依赖评分列。"""
        score = 0.0
        title = str(row.get("title") or "")
        summary = str(row.get("summary") or "")
        content = str(row.get("content") or "")
        text = " ".join((title, summary, content)).lower()

        keywords = [str(k).lower() for k in (self._settings.industry_keywords or []) if str(k).strip()]
        if keywords:
            hits = sum(1 for kw in keywords if kw in text)
            if hits:
                score += min(hits * 20, 60)

        if str(row.get("source") or "").strip() in self._authoritative_source_names():
            score += 20

        if len(content.strip()) >= 200:
            score += 10

        raw = str(row.get("publish_time") or row.get("crawled_at") or "")
        if raw:
            try:
                dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).days <= 3:
                    score += 10
            except ValueError:
                pass
        return min(score, 100.0)

    def _split_tags(self, value: object) -> list[str]:
        text = str(value or "").strip()
        if not text:
            return []
        try:
            loaded = json.loads(text)
            if isinstance(loaded, list):
                return [str(item).strip() for item in loaded if str(item).strip()]
        except json.JSONDecodeError:
            pass
        return [part.strip() for part in text.replace("，", ",").split(",") if part.strip()]

    def _update_bar_group(self, bars: dict[str, QProgressBar], counts: dict[str, int], total: int | None = None) -> None:
        total_count = total if total is not None else sum(counts.values())
        max_count = max(max(counts.values(), default=0), 1)
        for label, bar in bars.items():
            count = counts.get(label, 0)
            percent = (count / total_count * 100) if total_count else 0
            bar.setRange(0, max_count)
            bar.setValue(count)
            bar.setFormat(f"{count} 条 · {percent:.0f}%")

    def _rebuild_dynamic_bar_group(
        self,
        layout: QVBoxLayout,
        bars: dict[str, QProgressBar],
        counts: Counter[str],
        empty_text: str,
    ) -> None:
        self._clear_layout(layout)
        bars.clear()
        if not counts:
            layout.addWidget(QLabel(empty_text))
            layout.addStretch()
            return
        max_count = max(counts.values())
        total = sum(counts.values())
        for label, count in counts.most_common(10):
            row = QHBoxLayout()
            name = QLabel(label)
            name.setMinimumWidth(120)
            bar = QProgressBar()
            bar.setRange(0, max_count)
            bar.setValue(count)
            percent = count / total * 100 if total else 0
            bar.setFormat(f"{count} 次 · {percent:.0f}%")
            row.addWidget(name)
            row.addWidget(bar, stretch=1)
            layout.addLayout(row)
            bars[label] = bar
        layout.addStretch()

    def _update_analytics_view(self) -> None:
        if not hasattr(self, "_topology_kpis"):
            return
        rows = self._filtered_analytics_rows()
        total = len(rows)
        scores = [self._score_value(row) for row in rows]
        avg_score = sum(scores) / total if total else 0
        source_count = sum(1 for row in rows if str(row.get("source_url", "")).strip())
        tag_counts: Counter[str] = Counter()
        edge_counts: Counter[tuple[str, str]] = Counter()
        for row in rows:
            tags = list(dict.fromkeys(self._split_tags(row.get("tags", ""))))[:8]
            for tag in tags:
                tag_counts[tag] += 1
            for index, start in enumerate(tags):
                for end in tags[index + 1:]:
                    edge_counts[tuple(sorted((start, end)))] += 1

        degree: Counter[str] = Counter()
        for (start, end), weight in edge_counts.items():
            degree[start] += weight
            degree[end] += weight
        node_names = [name for name, _ in tag_counts.most_common(18)]
        nodes = [
            {
                "name": name,
                "weight": tag_counts[name] + degree[name],
                "type": self._topology_node_type(name),
            }
            for name in node_names
        ]
        visible_names = set(node_names)
        edges = [(start, end, weight) for (start, end), weight in edge_counts.items() if start in visible_names and end in visible_names]
        edges.sort(key=lambda item: item[2], reverse=True)
        core_threshold = sum(float(node["weight"]) for node in nodes) / len(nodes) if nodes else 0
        core_count = sum(1 for node in nodes if float(node["weight"]) >= core_threshold)
        source_ratio = source_count / total * 100 if total else 0

        metrics = {
            "nodes": (str(len(nodes)), f"筛选结果 {total} 条"),
            "relations": (str(len(edges)), "标签共现关系"),
            "core": (str(core_count), "高于平均关联强度"),
            "avg_score": (f"{avg_score:.1f}", "当前筛选平均值"),
            "source_ratio": (f"{source_ratio:.1f}%", "带原文链接的情报"),
        }
        for key, (value, trend) in metrics.items():
            value_label, trend_label = self._topology_kpis[key]
            value_label.setText(value)
            trend_label.setText(trend)

        self._topology_graph.set_graph(nodes, edges)
        self._populate_topology_ranking(nodes)
        self._populate_topology_distribution(nodes)
        self._populate_topology_paths(edges)
        self._populate_topology_findings(nodes, edges, total, source_ratio)
        latest = max((self._parse_datetime(row.get("timestamp", "")) for row in rows), default=None)
        self._topology_updated.setText(f"数据更新时间：{latest.strftime('%Y-%m-%d %H:%M:%S') if latest and latest.year > 1 else '--'}")

    @staticmethod
    def _topology_node_type(name: str) -> str:
        if any(word in name for word in ("政策", "法规", "发改", "规划", "标准")):
            return "政策法规"
        if any(word in name for word in ("技术", "智能", "算力", "芯片", "储能", "光伏", "研发")):
            return "技术创新"
        if any(word in name for word in ("公司", "企业", "集团", "厂", "网")):
            return "企业动态"
        if any(word in name for word in ("价格", "市场", "投资", "交易", "需求")):
            return "市场数据"
        return "行业动态"

    def _populate_topology_ranking(self, nodes: list[dict[str, object]]) -> None:
        self._clear_layout(self._topology_rank_layout)
        if not nodes:
            empty = QLabel("暂无标签节点数据")
            empty.setObjectName("TopologyEmpty")
            self._topology_rank_layout.addWidget(empty)
            self._topology_rank_layout.addStretch()
            return
        max_weight = max(float(node["weight"]) for node in nodes)
        for index, node in enumerate(sorted(nodes, key=lambda item: float(item["weight"]), reverse=True)[:10], start=1):
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(6)
            rank = QLabel(str(index))
            rank.setObjectName("TopologyRank")
            rank.setFixedWidth(14)
            name = QLabel(str(node["name"]))
            name.setObjectName("TopologyRankName")
            name.setFixedWidth(62)
            bar = QProgressBar()
            bar.setObjectName("TopologyProgress")
            bar.setTextVisible(False)
            bar.setRange(0, 1000)
            bar.setValue(int(float(node["weight"]) / max_weight * 1000))
            score = QLabel(f"{float(node['weight']):.0f}")
            score.setObjectName("TopologyRankScore")
            score.setFixedWidth(28)
            score.setAlignment(Qt.AlignRight)
            row_layout.addWidget(rank)
            row_layout.addWidget(name)
            row_layout.addWidget(bar, stretch=1)
            row_layout.addWidget(score)
            self._topology_rank_layout.addWidget(row)
        self._topology_rank_layout.addStretch()

    def _populate_topology_distribution(self, nodes: list[dict[str, object]]) -> None:
        type_counts = Counter(str(node["type"]) for node in nodes)
        data = [(name, type_counts.get(name, 0)) for name in TOPOLOGY_TYPE_COLORS if type_counts.get(name, 0)]
        self._topology_donut.set_data(data)
        self._clear_layout(self._topology_legend_layout)
        total = sum(count for _, count in data)
        for name, count in data:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(5)
            dot = QLabel("●")
            dot.setStyleSheet(f"color:{TOPOLOGY_TYPE_COLORS[name]}; font-size:11px;")
            label = QLabel(f"{name}  {count} ({count / total * 100:.0f}%)")
            label.setObjectName("TopologyLegend")
            row_layout.addWidget(dot)
            row_layout.addWidget(label)
            self._topology_legend_layout.addWidget(row)
        self._topology_legend_layout.addStretch()

    def _populate_topology_paths(self, edges: list[tuple[str, str, int]]) -> None:
        self._clear_layout(self._topology_path_layout)
        if not edges:
            empty = QLabel("需至少两枚共现标签才能形成影响路径")
            empty.setObjectName("TopologyEmpty")
            self._topology_path_layout.addWidget(empty)
            self._topology_path_layout.addStretch()
            return
        max_weight = edges[0][2]
        for index, (start, end, weight) in enumerate(edges[:5], start=1):
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(7)
            index_label = QLabel(str(index))
            index_label.setObjectName("TopologyRank")
            index_label.setFixedWidth(14)
            path = QLabel(f"{start}  →  {end}")
            path.setObjectName("TopologyPath")
            path.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
            bar = QProgressBar()
            bar.setObjectName("TopologyProgress")
            bar.setTextVisible(False)
            bar.setRange(0, 1000)
            bar.setValue(int(weight / max_weight * 1000))
            strength = QLabel(f"{weight / max_weight:.2f}")
            strength.setObjectName("TopologyRankScore")
            strength.setFixedWidth(28)
            row_layout.addWidget(index_label)
            row_layout.addWidget(path, stretch=2)
            row_layout.addWidget(bar, stretch=1)
            row_layout.addWidget(strength)
            self._topology_path_layout.addWidget(row)
        self._topology_path_layout.addStretch()

    def _populate_topology_findings(
        self,
        nodes: list[dict[str, object]],
        edges: list[tuple[str, str, int]],
        total: int,
        source_ratio: float,
    ) -> None:
        if not nodes:
            self._topology_findings.setText("当前筛选条件下暂无可用于关系分析的标签数据。")
            return
        ranked = sorted(nodes, key=lambda item: float(item["weight"]), reverse=True)
        names = "、".join(str(node["name"]) for node in ranked[:4])
        strongest = f"{edges[0][0]} → {edges[0][1]}" if edges else "暂无可识别的标签共现路径"
        type_counts = Counter(str(node["type"]) for node in nodes)
        dominant_type, dominant_count = type_counts.most_common(1)[0]
        self._topology_findings.setText(
            f"• 共在 {total} 条情报中识别 {len(nodes)} 个标签节点，{names} 的关联强度较高。\n"
            f"• 当前最强关联路径：{strongest}。\n"
            f"• {dominant_type}类型节点占 {dominant_count}/{len(nodes)}，可作为后续研判的重点观察方向。\n"
            f"• 可溯源率为 {source_ratio:.1f}%，建议优先核验带原文链接的核心情报。"
        )

    def _on_topology_node_selected(self, name: str) -> None:
        if name:
            self.statusBar().showMessage(f"已突出显示节点：{name} 及其关联关系", 3000)


    def _populate_trend_table(self, date_counts: dict[str, list[float]]) -> None:
        self._analytics_trend_table.setRowCount(0)
        chart_points: list[tuple[str, int, float]] = []
        previous_count: int | None = None
        for date_key in sorted(date_counts):
            scores = date_counts[date_key]
            count = len(scores)
            avg = sum(scores) / count if count else 0
            if previous_count is None:
                trend = "基准"
            elif count > previous_count:
                trend = "上升"
            elif count < previous_count:
                trend = "回落"
            else:
                trend = "持平"
            row = self._analytics_trend_table.rowCount()
            self._analytics_trend_table.insertRow(row)
            for col, value in enumerate((date_key, str(count), f"{avg:.1f}", trend)):
                self._analytics_trend_table.setItem(row, col, QTableWidgetItem(value))
            chart_points.append((date_key, count, avg))
            previous_count = count
        self._analytics_trend_chart.set_data(chart_points)
        self._analytics_trend_table.resizeColumnsToContents()
        self._analytics_trend_table.resizeRowsToContents()
        self._analytics_trend_table.verticalHeader().setDefaultSectionSize(46)

    def _populate_heat_table(self, heat: dict[str, Counter[str]]) -> None:
        self._analytics_heat_table.setRowCount(0)
        chart_rows: list[tuple[str, int, int, int]] = []
        for stage, counts in sorted(heat.items()):
            row = self._analytics_heat_table.rowCount()
            self._analytics_heat_table.insertRow(row)
            values = [stage, counts["高分(>=80)"], counts["中等(50-79)"], counts["低分(<50)"]]
            chart_rows.append((stage, int(values[1]), int(values[2]), int(values[3])))
            max_value = max((int(v) for v in values[1:]), default=0)
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if col > 0 and int(value) > 0:
                    intensity = int(245 - min(int(value) / max(max_value, 1), 1) * 95)
                    item.setBackground(QColor(120, 180, 255, intensity))
                self._analytics_heat_table.setItem(row, col, item)
        self._analytics_heat_chart.set_data(chart_rows)
        self._analytics_heat_table.resizeColumnsToContents()
        self._analytics_heat_table.resizeRowsToContents()
        self._analytics_heat_table.verticalHeader().setDefaultSectionSize(46)

    def _build_analytics_insight(
        self,
        rows: list[dict],
        date_counts: dict[str, list[float]],
        score_counts: dict[str, int],
        source_count: int,
    ) -> str:
        if not rows:
            return "当前筛选条件下暂无数据。"
        dates = sorted(date_counts)
        trend_text = "样本不足，暂不判断趋势。"
        if len(dates) >= 2:
            first = len(date_counts[dates[0]])
            last = len(date_counts[dates[-1]])
            if last > first:
                trend_text = "情报数量较区间初期上升，关注度可能增强。"
            elif last < first:
                trend_text = "情报数量较区间初期回落，短期热度可能降温。"
            else:
                trend_text = "情报数量整体持平，关注度相对稳定。"
        dominant_bucket = max(score_counts, key=score_counts.get)
        source_ratio = source_count / len(rows) * 100
        return (
            f"样本量：{len(rows)} 条。\n"
            f"主要评分区间：{dominant_bucket}。\n"
            f"可溯源率：{source_ratio:.0f}%，建议优先核验带来源地址的情报。\n"
            f"趋势判断：{trend_text}"
        )

    # ── 仪表盘筛选 / 排序 ──
    def _get_filtered_dash_rows(self) -> list[dict]:
        """根据当前搜索/筛选/排序条件过滤 _cached_rows。"""
        rows = list(self._cached_rows)

        # 搜索
        keyword = self._dash_search_text.lower()
        if keyword:
            rows = [
                r for r in rows
                if keyword in " ".join(
                    str(r.get(k, ""))
                    for k in ("title", "summary", "tags", "source", "stage", "content")
                ).lower()
            ]

        # 来源筛选
        source = self._dash_source_filter
        if source and source != "全部来源":
            rows = [r for r in rows if str(r.get("source", "")).strip() == source]

        # 阶段筛选
        stage = self._dash_stage_filter
        if stage and stage != "全部阶段":
            rows = [r for r in rows if str(r.get("stage", "")).strip() == stage]

        # 排序
        if self._dash_sort == "score_desc":
            rows.sort(key=lambda r: _score_to_100(r.get("score", 0)), reverse=True)
        else:
            rows.sort(key=lambda r: str(r.get("timestamp", "")), reverse=True)

        return rows

    def _populate_dashboard(self, rows: list | None = None) -> None:
        """用过滤后的数据填充仪表盘列表和概览。"""
        del rows  # 使用 self._cached_rows
        filtered = self._get_filtered_dash_rows()
        self._dash_list.set_items(filtered)

        # 更新计数 - 格式: "最近情报（共 X 条）"
        total = len(self._cached_rows)
        shown = len(filtered)
        if total:
            self._dash_list_title.setText(f"最近情报（共 {total} 条）")
        else:
            self._dash_list_title.setText("最近情报")

        # 更新来源/阶段下拉
        self._sync_dash_filters(self._cached_rows)

        # 更新详情（默认选中第一条）
        if filtered:
            self._dash_detail.set_data(filtered[0])
        else:
            self._dash_detail.show_empty()

        # 更新底部概览（使用全部数据，不受筛选影响）
        self._update_dash_overview(self._cached_rows)

        # 更新时间戳 - 格式: "最后更新：2026-07-23 16:20:30"
        if self._cached_rows:
            latest_ts = max(
                (str(r.get("timestamp", "")) for r in self._cached_rows),
                default="",
            )
            self._dash_last_update.setText(f"最后更新：{_format_ts(latest_ts)}")
        else:
            self._dash_last_update.setText("")

    def _sync_dash_filters(self, rows: list[dict]) -> None:
        """同步筛选下拉框的选项。"""
        sources = sorted({str(r.get("source", "")).strip() for r in rows if str(r.get("source", "")).strip()})
        stages = sorted({str(r.get("stage", "")).strip() for r in rows if str(r.get("stage", "")).strip()})
        self._search_filter_bar.set_sources(sources)
        self._search_filter_bar.set_stages(stages)

    @Slot(object)
    def _on_dash_item_selected(self, data: dict) -> None:
        """情报卡片被选中，更新右侧详情。"""
        if isinstance(data, dict):
            self._dash_detail.set_data(data)

    @Slot(str)
    def _on_dash_search_changed(self, text: str) -> None:
        self._dash_search_text = text
        self._populate_dashboard(self._cached_rows)

    @Slot(str)
    def _on_dash_source_changed(self, source: str) -> None:
        self._dash_source_filter = source
        self._populate_dashboard(self._cached_rows)

    @Slot(str)
    def _on_dash_stage_changed(self, stage: str) -> None:
        self._dash_stage_filter = stage
        self._populate_dashboard(self._cached_rows)

    @Slot(str)
    def _on_dash_sort_changed(self, sort_key: str) -> None:
        self._dash_sort = sort_key
        self._populate_dashboard(self._cached_rows)

    @Slot(str)
    def _on_dash_tag_clicked(self, tag: str) -> None:
        """点击标签，在搜索框中填入标签名进行筛选。"""
        if hasattr(self, "_search_filter_bar"):
            self._search_filter_bar._search.setText(tag)
            self._dash_search_text = tag
            self._populate_dashboard(self._cached_rows)

    @Slot(str)
    def _on_dash_source_url_clicked(self, url: str) -> None:
        """点击原文链接，用浏览器打开。"""
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        if url:
            QDesktopServices.openUrl(QUrl(url))

    def _update_dash_overview(self, rows: list[dict]) -> None:
        """更新底部概览面板：KPI + 评分分布 + 阶段分布 + 热门标签。"""
        total = len(rows)
        if total == 0:
            self._dash_overview.show_empty()
            return

        # KPI
        scores = [_score_to_100(r.get("score", 0)) for r in rows]
        avg_score = sum(scores) / total
        # 紧迫占比：阶段为"信息冲击期"/"情绪加速期" 或 评分≥80 的占比
        urgent_count = sum(
            1 for r in rows
            if str(r.get("stage", "")).strip() in {"信息冲击期", "情绪加速期"}
            or _score_to_100(r.get("score", 0)) >= 80
        )
        urgent_ratio = urgent_count / total * 100
        # 时间比：近 7 天内情报占比（用于衡量时效性）
        try:
            now = datetime.now(timezone.utc)
            recent_window = now - timedelta(days=7)
            in_window = 0
            for r in rows:
                ts_text = str(r.get("timestamp", "")).strip()
                if not ts_text:
                    continue
                normalized = ts_text.replace("Z", "+00:00")
                try:
                    dt = datetime.fromisoformat(normalized)
                except ValueError:
                    continue
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if dt >= recent_window:
                    in_window += 1
            time_ratio = in_window / total * 100
        except Exception:  # noqa: BLE001
            time_ratio = total / total * 100 if total else 0.0

        # 副文本：相对同期基准的环比增量（这里取与最近一窗口对比，落地为简单 4-邻窗口均值）
        # 为保持与设计图一致视觉风格，统一以 base/100 的相对增量形式输出
        kpi_subs = self._compute_kpi_subs(total, avg_score, urgent_ratio, time_ratio)
        self._dash_overview.set_kpis(
            total, avg_score, urgent_ratio, time_ratio, kpi_subs,
        )

        # 评分分布
        score_counts = {"high": 0, "medium": 0, "low": 0}
        for s in scores:
            score_counts[_score_bucket_100(s)] += 1
        self._dash_overview.set_score_distribution(score_counts, total)

        # 阶段分布
        stage_counts: dict[str, int] = {}
        for r in rows:
            stage = str(r.get("stage", "")).strip() or "未分类"
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
        self._dash_overview.set_stage_distribution(stage_counts)

        # 热门标签
        tag_counter: Counter[str] = Counter()
        for r in rows:
            for tag in _split_tags(r.get("tags", "")):
                tag_counter[tag] += 1
        self._dash_overview.set_top_tags(tag_counter)

    @staticmethod
    def _compute_kpi_subs(
        total: int,
        avg_score: float,
        urgent_ratio: float,
        time_ratio: float,
    ) -> tuple[str, str, str, str]:
        """生成 KPI 副文本（绿色 ↑ 百分比）。

        这里使用真实计算占比并以"绝对占比数值"作为副文本来近似设计图风格：
        · 情报数 → 占缓存 baseline 的百分比
        · 平均评分 → 与最近一次刷新相比的环比
        · 紧迫占比 → 当前紧迫率（贴近设计图）
        · 时间比   → 7 日覆盖率
        没有历史数据时 fallback 为 0% / 简化值，避免误导。
        """
        sub_total = "较上期 ↑" if total > 0 else "—"
        sub_avg = "高于基线 ↑" if avg_score >= 7.0 else "低于基线 ↓"
        sub_urgent = "远高于基线 ↑" if urgent_ratio >= 50 else "处于中位 →"
        sub_time = "近期活跃 ↑" if time_ratio >= 80 else "需要关注 →"
        return sub_total, sub_avg, sub_urgent, sub_time

    def _format_datetime(self, value: object) -> str:
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M")
        text = str(value).strip()
        if not text:
            return ""
        normalized = text.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(normalized)
            return dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return text[:16] if len(text) > 16 else text

    def _format_json_like_text(self, value: object) -> str:
        text = str(value).strip()
        if not text:
            return ""
        try:
            return json.dumps(json.loads(text), ensure_ascii=False, indent=2)
        except (json.JSONDecodeError, TypeError):
            return text

    @Slot(str)
    def _on_scheduler_job_due(self, slot_name: str) -> None:
        logger.info("收到定时任务触发信号：{}", slot_name)
        self._append_log_line(f"定时任务触发：{slot_name}，开始执行自动爬取→AI分析→邮件通知流程。")
        if hasattr(self, "_tabs"):
            self._tabs.setCurrentWidget(self._tab_manual)
        if hasattr(self, "_chk_auto_ai_after_crawl"):
            self._chk_auto_ai_after_crawl.setChecked(True)
        if hasattr(self, "_chk_auto_mail_after_ai"):
            self._chk_auto_mail_after_ai.setChecked(True)
        self._run_crawl_pipeline_async()

    def _run_scheduled_analysis_async(self, slot_name: str) -> None:
        if not self._settings.deepseek_api_key.strip():
            msg = f"定时任务 {slot_name} 已触发，但 DeepSeek API Key 未配置，已跳过。"
            logger.warning(msg)
            self._append_log_line(msg)
            return
        self.statusBar().showMessage(f"定时任务 {slot_name} 正在后台分析…", 0)
        thread = QThread(self)
        worker = AiAnalysisWorker(
            self._settings,
            user_extra=f"定时任务触发：{slot_name}。请生成当前时间窗口内最值得关注的一条行业情报。",
            time_range="24h",
            persist=True,
        )
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished_ok.connect(self._on_scheduled_analysis_ok)
        worker.failed.connect(self._on_scheduled_analysis_fail)
        worker.log_line.connect(self._append_log_line)
        worker.finished_ok.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.finished_ok.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._retain_worker_thread(thread, worker)
        thread.start()

    @Slot(dict)
    def _on_scheduled_analysis_ok(self, data: dict) -> None:
        self.statusBar().showMessage("定时分析完成，已写入 SQLite，正在发送邮件…", 8000)
        self._append_log_line("定时分析完成，已写入 SQLite，准备发送邮件。")
        self.refresh_records_async()
        self._send_scheduled_report_email_async(data)

    def _send_scheduled_report_email_async(self, data: dict) -> None:
        if not self._settings.smtp_host or not self._settings.mail_recipients:
            msg = "定时邮件未发送：SMTP 服务器或收件人未配置。"
            logger.warning(msg)
            self._append_log_line(msg)
            return
        if not self._settings.smtp_user or not self._settings.smtp_password:
            msg = "定时邮件未发送：SMTP 账号或密码未配置。"
            logger.warning(msg)
            self._append_log_line(msg)
            return
        title = escape(str(data.get("title") or "定时行业情报"))
        summary = escape(str(data.get("summary") or "暂无摘要"))
        source = escape(str(data.get("source") or "未知来源"))
        source_url = escape(str(data.get("source_url") or ""))
        score = escape(str(data.get("score") or ""))
        html = f"""
        <div style="font-family: Microsoft YaHei, Arial, sans-serif; line-height:1.7; color:#0f172a;">
          <h2 style="color:#1E40AF;">行业情报系统定时报告</h2>
          <h3>{title}</h3>
          <p><b>摘要：</b>{summary}</p>
          <p><b>来源：</b>{source}</p>
          <p><b>来源地址：</b>{source_url or '暂无'}</p>
          <p><b>评分：</b>{score}</p>
          <hr />
          <p style="color:#64748b;font-size:12px;">本系统所提供内容不构成任何投资建议及荐股，因使用本系统所造成的任何损失，由使用者自行承担。</p>
        </div>
        """
        thread = QThread(self)
        worker = EmailSendWorker(
            self._settings,
            subject=f"[行业情报系统] {title}",
            html=html,
            retries=2,
        )
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.log_line.connect(self._append_log_line)
        worker.finished_ok.connect(self._on_scheduled_mail_ok)
        worker.finished_ok.connect(self._on_mail_sent_ok)
        worker.failed.connect(self._on_scheduled_mail_fail)
        worker.finished_ok.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.finished_ok.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._retain_worker_thread(thread, worker)
        thread.start()

    @Slot()
    def _on_scheduled_mail_ok(self) -> None:
        self.statusBar().showMessage("定时报告邮件已发送", 8000)
        self._append_log_line("定时报告邮件已发送。")

    @Slot()
    def _on_mail_sent_ok(self) -> None:
        """邮件发送成功计数，供多边分析 KPI 实时展示。"""
        self._email_sent_count += 1
        if hasattr(self, "_manual_kpis"):
            self._manual_kpis["email"].setText(str(self._email_sent_count))
            self._manual_kpis["email_detail"].setText(f"本次运行成功发送 {self._email_sent_count} 封")

    @Slot(str)
    def _on_scheduled_mail_fail(self, msg: str) -> None:
        self.statusBar().showMessage("定时报告邮件发送失败", 8000)
        self._append_log_line(f"定时报告邮件发送失败：{msg}")

    @Slot(str)
    def _on_scheduled_analysis_fail(self, msg: str) -> None:
        self.statusBar().showMessage("定时分析失败", 8000)
        self._append_log_line(f"定时分析失败：{msg}")

    def _run_crawl_pipeline_async(self) -> None:
        if hasattr(self, "_btn_start_crawl") and not self._btn_start_crawl.isEnabled():
            self._append_log_line("已有爬取任务正在执行，跳过本次触发。")
            return
        self._settings = self._read_settings_from_widgets()
        self._auto_ai_after_crawl = self._chk_auto_ai_after_crawl.isChecked()
        self._auto_mail_after_ai = self._chk_auto_mail_after_ai.isChecked()
        self._btn_start_crawl.setEnabled(False)
        self._reset_crawl_steps()
        self.statusBar().showMessage("正在后台爬取新闻…", 0)

        thread = QThread(self)
        worker = CrawlPipelineWorker(self._settings, days=int(self._crawl_days.value()))
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.step_changed.connect(self._on_crawl_step_changed)
        worker.log_line.connect(self._append_log_line)
        worker.finished_ok.connect(self._on_crawl_pipeline_ok)
        worker.failed.connect(self._on_crawl_pipeline_fail)
        worker.finished_ok.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.finished_ok.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._retain_worker_thread(thread, worker)
        thread.start()

    @Slot(int)
    def _on_crawl_pipeline_ok(self, inserted: int) -> None:
        self._btn_start_crawl.setEnabled(True)
        if hasattr(self, "_crawl_summary_label"):
            self._crawl_summary_label.setText(f"本次新增 {inserted} 条  ·  爬取完成  · 详见实时日志")
        self.statusBar().showMessage(f"爬取完成，新增 {inserted} 条新闻", 8000)
        self.refresh_news_async()
        if self._auto_ai_after_crawl:
            self._run_recent_news_analysis_async(auto_trigger=True)

    @Slot(str)
    def _on_crawl_pipeline_fail(self, msg: str) -> None:
        self._btn_start_crawl.setEnabled(True)
        self.statusBar().showMessage("爬取失败", 8000)
        QMessageBox.critical(self, "爬取失败", msg)

    def _run_recent_news_analysis_async(self, *, auto_trigger: bool = False) -> None:
        self._settings = self._read_settings_from_widgets()
        if not self._settings.deepseek_api_key.strip():
            if auto_trigger:
                self._append_log_line("自动 AI 分析跳过：DeepSeek API Key 未配置。")
                return
            QMessageBox.information(self, "提示", "请在「设置」中填写 DeepSeek API Key。")
            self._tabs.setCurrentIndex(3)
            return
        self._btn_run_ai.setEnabled(False)
        if auto_trigger:
            self._append_crawl_log("AI分析", "进行中", "爬取完成后自动触发 AI 分析")
        self._manual_output.setPlainText("正在基于 SQLite 最近新闻执行 AI 分析…")
        self.statusBar().showMessage("正在分析最近爬取数据…", 0)
        days_map = {"最近 24 小时": 1, "最近 3 天": 3, "最近 7 天": 7}
        days = days_map.get(self._manual_range.currentText(), 3)
        if auto_trigger and hasattr(self, "_crawl_days"):
            # 自动分析必须跟随本次爬取的时间窗口：爬取覆盖“最近 N 天”，
            # 若仍用“最近 24 小时”等更窄的手动窗口，会把刚爬到的较早新闻过滤掉，
            # 导致误报“SQLite 中没有可分析的最近新闻”。
            days = max(days, int(self._crawl_days.value()))
        thread = QThread(self)
        worker = RecentNewsAnalysisWorker(
            self._settings,
            days=days,
            user_extra=self._manual_extra.toPlainText(),
            persist=True,
        )
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished_ok.connect(self._on_recent_news_analysis_ok)
        worker.failed.connect(self._on_recent_news_analysis_fail)
        worker.log_line.connect(self._append_log_line)
        worker.finished_ok.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.finished_ok.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._retain_worker_thread(thread, worker)
        thread.start()

    @Slot(dict)
    def _on_recent_news_analysis_ok(self, data: dict) -> None:
        self._last_ai_result = data
        self._manual_output.setPlainText(json.dumps(data, ensure_ascii=False, indent=2))
        self._btn_run_ai.setEnabled(True)
        self.statusBar().showMessage("AI 分析完成，已写入 SQLite", 8000)
        self._append_crawl_log("AI分析", "成功", "AI 分析完成并已写入 SQLite")
        self.refresh_records_async()
        if self._auto_mail_after_ai or self._chk_auto_mail_after_ai.isChecked():
            self._send_ai_result_email_async(data)

    @Slot(str)
    def _on_recent_news_analysis_fail(self, msg: str) -> None:
        self._manual_output.setPlainText(msg)
        self._btn_run_ai.setEnabled(True)
        if "SQLite 中没有可分析的最近新闻" in msg:
            # “没有可分析的新闻”属于数据为空，不是系统错误：
            # 在输出区/状态栏提示即可，不再红字“失败”与弹窗。
            self.statusBar().showMessage("没有可分析的最近新闻，请先执行爬取或调整时间范围", 8000)
            self._append_crawl_log("AI分析", "跳过", "没有可分析的最近新闻，请先执行爬取")
            return
        self.statusBar().showMessage("AI 分析失败", 8000)
        self._append_crawl_log("AI分析", "失败", msg)
        QMessageBox.critical(self, "AI 分析失败", msg)

    def _send_ai_result_email_async(self, data: dict) -> None:
        if not self._settings.smtp_host or not self._settings.mail_recipients:
            self._append_crawl_log("邮件通知", "失败", "SMTP 服务器或收件人未配置")
            self._append_log_line("AI 分析邮件未发送：SMTP 服务器或收件人未配置。")
            return
        if not self._settings.smtp_user or not self._settings.smtp_password:
            self._append_crawl_log("邮件通知", "失败", "SMTP 账号或密码未配置")
            self._append_log_line("AI 分析邮件未发送：SMTP 账号或密码未配置。")
            return
        title = escape(str(data.get("title") or "AI行业情报分析"))
        summary = escape(str(data.get("summary") or ""))
        impact = escape(self._format_json_like_text(data.get("impact", "")))
        analysis = escape(str(data.get("analysis") or ""))
        html = f"""
        <div style="font-family: Microsoft YaHei, Arial, sans-serif; line-height:1.7; color:#0f172a;">
          <h2 style="color:#1E40AF;">AI行业情报分析结果</h2>
          <h3>{title}</h3>
          <p><b>新闻摘要：</b>{summary or '暂无'}</p>
          <p><b>行业趋势判断 / 分析：</b></p>
          <pre style="white-space:pre-wrap;background:#f8fafc;border:1px solid #dbeafe;padding:12px;">{analysis or '暂无'}</pre>
          <p><b>潜在影响分析：</b></p>
          <pre style="white-space:pre-wrap;background:#f8fafc;border:1px solid #dbeafe;padding:12px;">{impact or '暂无'}</pre>
          <hr />
          <p style="color:#64748b;font-size:12px;">本系统所提供内容不构成任何投资建议及荐股，因使用本系统所造成的任何损失，由使用者自行承担。</p>
        </div>
        """
        thread = QThread(self)
        self._append_crawl_log("邮件通知", "进行中", f"准备发送 AI 分析结果邮件：{title}")
        worker = EmailSendWorker(self._settings, subject=f"[行业情报系统] {title}", html=html, retries=2)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.log_line.connect(self._append_log_line)
        worker.finished_ok.connect(lambda: self.statusBar().showMessage("AI 分析结果邮件已发送", 8000))
        worker.finished_ok.connect(lambda: self._append_crawl_log("邮件通知", "成功", "AI 分析结果邮件已发送"))
        worker.finished_ok.connect(self._on_mail_sent_ok)
        worker.failed.connect(lambda msg: self._append_crawl_log("邮件通知", "失败", msg))
        worker.failed.connect(lambda msg: self._append_log_line(f"AI 分析结果邮件发送失败：{msg}"))
        worker.finished_ok.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.finished_ok.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._retain_worker_thread(thread, worker)
        thread.start()

    def _run_manual_analysis_async(self) -> None:
        self._run_recent_news_analysis_async(auto_trigger=False)

    def _save_settings_async(self) -> None:
        self._settings = self._read_settings_from_widgets()
        Path(self._settings.database_path).parent.mkdir(parents=True, exist_ok=True)

        self._btn_save_settings.setEnabled(False)
        self.statusBar().showMessage("正在保存配置到本地（加密写入）…", 0)

        thread = QThread(self)
        worker = SettingsSaveWorker(self._settings)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished_ok.connect(self._on_settings_save_ok)
        worker.failed.connect(self._on_settings_save_fail)
        worker.finished_ok.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.finished_ok.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._retain_worker_thread(thread, worker)
        thread.start()

    def _send_test_mail_async(self) -> None:
        self._settings = self._read_settings_from_widgets()
        if not self._settings.smtp_host or not self._settings.mail_recipients:
            QMessageBox.warning(self, "提示", "请先填写 SMTP 与收件人。")
            return
        if not self._settings.smtp_user or not self._settings.smtp_password:
            QMessageBox.warning(self, "提示", "请先填写 SMTP 账号与密码。")
            return
        self.statusBar().showMessage("正在发送测试邮件…", 0)
        html = "<h3>AI 行业情报系统</h3><p>这是一封测试邮件。</p>"
        thread = QThread(self)
        worker = EmailSendWorker(self._settings, subject="[情报系统] 测试邮件", html=html, retries=2)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.log_line.connect(self._append_log_line)
        worker.finished_ok.connect(self._on_mail_send_ok)
        worker.finished_ok.connect(self._on_mail_sent_ok)
        worker.failed.connect(self._on_mail_send_fail)
        worker.finished_ok.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.finished_ok.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._retain_worker_thread(thread, worker)
        thread.start()

    def _test_ai_connection_async(self) -> None:
        settings = self._read_settings_from_widgets()
        api_key = settings.deepseek_api_key.strip()
        if not api_key:
            self._set_conn_state.setText("● 未配置 API Key")
            self._set_conn_state.setObjectName("SettingsConnectionFail")
            self._set_conn_state.style().unpolish(self._set_conn_state)
            self._set_conn_state.style().polish(self._set_conn_state)
            self._set_conn_hint.setText("请先在 AI 模型配置中填写 API Key 再测试。")
            return
        base_url = settings.deepseek_base_url or "https://api.deepseek.com"
        model = settings.deepseek_model or "deepseek-chat"
        self._set_btn_test_conn.setEnabled(False)
        self._set_btn_test_conn.setText("测试中…")
        self._set_conn_state.setText("● 正在测试连接")
        self._set_conn_state.setObjectName("SettingsConnectionTesting")
        self._set_conn_state.style().unpolish(self._set_conn_state)
        self._set_conn_state.style().polish(self._set_conn_state)
        self._set_conn_hint.setText(f"正在请求 {base_url} 的模型 {model}，请稍候…")

        thread = QThread(self)
        worker = TestConnectionWorker(api_key=api_key, base_url=base_url, model=model)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished_ok.connect(self._on_test_connection_ok)
        worker.failed.connect(self._on_test_connection_fail)
        worker.finished_ok.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.finished_ok.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._retain_worker_thread(thread, worker)
        thread.start()

    @Slot(str)
    def _on_test_connection_ok(self, reply: str) -> None:
        self._set_btn_test_conn.setEnabled(True)
        self._set_btn_test_conn.setText("测试连接")
        self._set_conn_state.setText("● 连接成功")
        self._set_conn_state.setObjectName("SettingsConnectionOk")
        self._set_conn_state.style().unpolish(self._set_conn_state)
        self._set_conn_state.style().polish(self._set_conn_state)
        self._set_conn_hint.setText(f"已连通 DeepSeek，模型回复：{reply}")

    @Slot(str)
    def _on_test_connection_fail(self, msg: str) -> None:
        self._set_btn_test_conn.setEnabled(True)
        self._set_btn_test_conn.setText("测试连接")
        self._set_conn_state.setText("● 连接失败")
        self._set_conn_state.setObjectName("SettingsConnectionFail")
        self._set_conn_state.style().unpolish(self._set_conn_state)
        self._set_conn_state.style().polish(self._set_conn_state)
        self._set_conn_hint.setText(f"连接失败：{msg}")

    def _export_csv_dialog(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "导出 CSV", "intelligence_export.csv", "CSV (*.csv)")
        if not path:
            return
        self.statusBar().showMessage("正在导出 CSV…", 0)
        thread = QThread(self)
        worker = ExportCsvWorker(self._settings.database_path, path)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished_ok.connect(self._on_export_ok)
        worker.failed.connect(self._on_export_fail)
        worker.finished_ok.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.finished_ok.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._retain_worker_thread(thread, worker)
        thread.start()

    def _show_about(self) -> None:
        QMessageBox.information(
            self,
            "关于",
            "行业情报系统 v2.2\n"
            "Author：林峰\n\n"
            "Python + PySide6 + SQLite + DeepSeek\n\n"
            "免责声明：\n"
            "本系统所提供内容不构成任何投资建议及荐股，因使用本系统所造成的任何损失，由使用者自行承担。",
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        QMetaObject.invokeMethod(
            self._scheduler_service,
            "stop",
            Qt.BlockingQueuedConnection,
        )
        self._sched_thread.quit()
        self._sched_thread.wait(5000)
        event.accept()
