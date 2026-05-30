"""主窗口：菜单、工具栏、多 Tab、线程任务编排。"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from loguru import logger
from PySide6.QtCore import QMetaObject, QObject, Qt, QThread, Signal, Slot
from PySide6.QtGui import QAction, QCloseEvent, QColor, QIcon, QPainter, QPalette, QPen
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
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
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from ai_intelligence_system.config.settings import AppSettings, SchedulerSlot, load_settings
from ai_intelligence_system.core.scheduler import SchedulerService
from ai_intelligence_system.ui import theme
from ai_intelligence_system.utils.paths import app_icon_path, describe_local_storage
from ai_intelligence_system.workers.ai_analysis_worker import (
    AiAnalysisWorker,
    DashboardLoadWorker,
    EmailSendWorker,
    ExportCsvWorker,
    SettingsSaveWorker,
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


class LogBus(QObject):
    """将 loguru 日志投递到 UI 线程。"""

    message = Signal(str)


class MainWindow(QMainWindow):
    configure_scheduler_requested = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("行业情报系统 v1.0")
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
        self._act_quit = QAction("退出", self)
        self._act_quit.triggered.connect(self.close)
        self._act_settings = QAction("设置…", self)
        self._act_settings.triggered.connect(lambda: self._tabs.setCurrentIndex(3))
        self._act_export = QAction("导出 CSV…", self)
        self._act_export.triggered.connect(self._export_csv_dialog)
        self._act_refresh = QAction("立即刷新数据", self)
        self._act_refresh.triggered.connect(self.refresh_records_async)
        self._act_mail = QAction("发送测试邮件", self)
        self._act_mail.triggered.connect(self._send_test_mail_async)
        self._act_history = QAction("统计分析", self)
        self._act_history.triggered.connect(lambda: self._tabs.setCurrentIndex(1))
        self._act_log_tab = QAction("日志", self)
        self._act_log_tab.triggered.connect(lambda: self._tabs.setCurrentIndex(4))
        self._act_about = QAction("关于", self)
        self._act_about.triggered.connect(self._show_about)
        self._act_theme = QAction("切换深/浅色", self)
        self._act_theme.triggered.connect(self._toggle_theme)

    def _build_menu_toolbar(self) -> None:
        menu_file = self.menuBar().addMenu("文件")
        menu_file.addAction(self._act_settings)
        menu_file.addAction(self._act_export)
        menu_file.addSeparator()
        menu_file.addAction(self._act_quit)

        menu_ops = self.menuBar().addMenu("操作")
        menu_ops.addAction(self._act_refresh)
        menu_ops.addAction(self._act_mail)

        menu_view = self.menuBar().addMenu("查看")
        menu_view.addAction(self._act_history)
        menu_view.addAction(self._act_log_tab)
        menu_view.addSeparator()
        menu_view.addAction(self._act_theme)

        menu_help = self.menuBar().addMenu("帮助")
        menu_help.addAction(self._act_about)

        tb = QToolBar("主工具栏")
        tb.setMovable(False)
        self.addToolBar(tb)
        tb.addAction(self._act_refresh)
        tb.addAction(self._act_mail)
        tb.addAction(self._act_export)

    def _build_tabs(self) -> None:
        self._tabs = QTabWidget()
        self.setCentralWidget(self._tabs)

        self._tab_dashboard = QWidget()
        self._tab_browse = QWidget()
        self._tab_manual = QWidget()
        self._tab_settings = QWidget()
        self._tab_log = QWidget()

        self._tabs.addTab(self._tab_dashboard, "仪表盘")
        self._tabs.addTab(self._tab_browse, "统计分析")
        self._tabs.addTab(self._tab_manual, "手动分析")
        self._tabs.addTab(self._tab_settings, "设置")
        self._tabs.addTab(self._tab_log, "日志与状态")

        self._setup_tab_dashboard()
        self._setup_tab_browse()
        self._setup_tab_manual()
        self._setup_tab_settings()
        self._setup_tab_log()

    def _setup_tab_dashboard(self) -> None:
        layout = QVBoxLayout(self._tab_dashboard)

        header_row = QHBoxLayout()
        self._dash_hint = QLabel("最近情报（自动从数据库加载）")
        self._btn_dash_refresh = QPushButton("刷新")
        self._btn_dash_refresh.clicked.connect(self.refresh_records_async)
        header_row.addWidget(self._dash_hint)
        header_row.addStretch()
        header_row.addWidget(self._btn_dash_refresh)
        layout.addLayout(header_row)

        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 8, 0)
        left_layout.addWidget(QLabel("最近情报"))
        self._dash_list = QListWidget()
        self._dash_list.currentItemChanged.connect(self._on_dashboard_item_changed)
        left_layout.addWidget(self._dash_list)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(8, 0, 0, 0)

        detail_group = QGroupBox("情报详情")
        detail_layout = QVBoxLayout(detail_group)
        self._dash_detail = QPlainTextEdit()
        self._dash_detail.setReadOnly(True)
        self._dash_detail.setPlaceholderText("选择左侧情报后查看格式化详情。")
        detail_layout.addWidget(self._dash_detail)

        chart_group = QGroupBox("统计分析")
        chart_layout = QVBoxLayout(chart_group)
        self._dash_stats_summary = QLabel("暂无统计数据")
        self._dash_stats_summary.setAlignment(Qt.AlignCenter)
        chart_layout.addWidget(self._dash_stats_summary)

        self._dash_score_bars: dict[str, QProgressBar] = {}
        for label in ("高分(>=80)", "中等(50-79)", "低分(<50)"):
            row = QHBoxLayout()
            name = QLabel(label)
            name.setMinimumWidth(90)
            bar = QProgressBar()
            bar.setRange(0, 1)
            bar.setValue(0)
            bar.setFormat("0 条")
            bar.setTextVisible(True)
            row.addWidget(name)
            row.addWidget(bar, stretch=1)
            chart_layout.addLayout(row)
            self._dash_score_bars[label] = bar
        chart_layout.addStretch()

        right_layout.addWidget(detail_group, stretch=3)
        right_layout.addWidget(chart_group, stretch=2)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setChildrenCollapsible(False)
        layout.addWidget(splitter, stretch=1)

    def _setup_tab_browse(self) -> None:
        root = QVBoxLayout(self._tab_browse)

        filter_group = QGroupBox("分析筛选")
        filter_layout = QHBoxLayout(filter_group)
        self._analytics_range = QComboBox()
        self._analytics_range.addItems(["全部", "最近24小时", "最近3天", "最近7天", "最近30天"])
        self._analytics_stage = QComboBox()
        self._analytics_stage.addItem("全部阶段")
        self._analytics_score = QComboBox()
        self._analytics_score.addItems(["全部评分", "高分(>=80)", "中等(50-79)", "低分(<50)"])
        self._analytics_keyword = QLineEdit()
        self._analytics_keyword.setPlaceholderText("按标题、摘要、标签、来源筛选")
        self._btn_analytics_refresh = QPushButton("刷新分析")
        self._btn_analytics_refresh.clicked.connect(self._update_analytics_view)
        for widget in (
            self._analytics_range,
            self._analytics_stage,
            self._analytics_score,
            self._analytics_keyword,
        ):
            if isinstance(widget, QComboBox):
                widget.currentIndexChanged.connect(self._update_analytics_view)
            else:
                widget.textChanged.connect(self._update_analytics_view)
        filter_layout.addWidget(QLabel("时间区间"))
        filter_layout.addWidget(self._analytics_range)
        filter_layout.addWidget(QLabel("阶段"))
        filter_layout.addWidget(self._analytics_stage)
        filter_layout.addWidget(QLabel("评分"))
        filter_layout.addWidget(self._analytics_score)
        filter_layout.addWidget(self._analytics_keyword, stretch=1)
        filter_layout.addWidget(self._btn_analytics_refresh)
        root.addWidget(filter_group)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        content = QWidget()
        content.setMinimumWidth(1120)
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(14)

        kpi_row = QHBoxLayout()
        self._analytics_kpis: dict[str, QLabel] = {}
        for key, title in (
            ("total", "情报总量"),
            ("avg_score", "平均评分"),
            ("high_ratio", "高分占比"),
            ("source_ratio", "可溯源率"),
        ):
            card = QGroupBox(title)
            card_layout = QVBoxLayout(card)
            value = QLabel("--")
            value.setObjectName("KpiValue")
            value.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(value)
            self._analytics_kpis[key] = value
            kpi_row.addWidget(card)
        content_layout.addLayout(kpi_row)

        charts_row = QHBoxLayout()
        self._score_group = QGroupBox("柱状图｜评分分布")
        self._score_bars_layout = QVBoxLayout(self._score_group)
        self._analytics_score_bars = self._create_bar_group(
            self._score_bars_layout,
            ("高分(>=80)", "中等(50-79)", "低分(<50)"),
        )
        charts_row.addWidget(self._score_group)

        self._stage_group = QGroupBox("饼图｜阶段占比")
        self._stage_bars_layout = QVBoxLayout(self._stage_group)
        self._analytics_stage_bars: dict[str, QProgressBar] = {}
        charts_row.addWidget(self._stage_group)
        content_layout.addLayout(charts_row)

        trend_row = QHBoxLayout()
        trend_group = QGroupBox("折线/趋势图｜按日期情报数量与平均评分")
        trend_layout = QVBoxLayout(trend_group)
        self._analytics_trend_chart = TrendChartWidget()
        trend_layout.addWidget(self._analytics_trend_chart)
        self._analytics_trend_table = QTableWidget(0, 4)
        self._analytics_trend_table.setMinimumHeight(300)
        self._analytics_trend_table.verticalHeader().setDefaultSectionSize(46)
        self._analytics_trend_table.horizontalHeader().setStretchLastSection(True)
        self._analytics_trend_table.setAlternatingRowColors(True)
        self._analytics_trend_table.setWordWrap(True)
        self._analytics_trend_table.setStyleSheet(
            "QTableWidget { font-size: 15px; gridline-color: #D6E4F0; } "
            "QHeaderView::section { font-size: 15px; font-weight: 600; padding: 8px; } "
            "QTableWidget::item { padding: 8px; }"
        )
        self._analytics_trend_table.setHorizontalHeaderLabels(["日期", "情报数量", "平均评分", "趋势强度"])
        trend_layout.addWidget(self._analytics_trend_table)
        trend_row.addWidget(trend_group, stretch=3)
        trend_group.setMinimumHeight(740)

        heat_group = QGroupBox("热力图｜阶段 × 评分分布")
        heat_layout = QVBoxLayout(heat_group)
        self._analytics_heat_chart = HeatMapWidget()
        heat_layout.addWidget(self._analytics_heat_chart)
        self._analytics_heat_table = QTableWidget(0, 4)
        self._analytics_heat_table.setMinimumHeight(300)
        self._analytics_heat_table.verticalHeader().setDefaultSectionSize(46)
        self._analytics_heat_table.horizontalHeader().setStretchLastSection(True)
        self._analytics_heat_table.setAlternatingRowColors(True)
        self._analytics_heat_table.setWordWrap(True)
        self._analytics_heat_table.setStyleSheet(
            "QTableWidget { font-size: 15px; gridline-color: #D6E4F0; } "
            "QHeaderView::section { font-size: 15px; font-weight: 600; padding: 8px; } "
            "QTableWidget::item { padding: 8px; }"
        )
        self._analytics_heat_table.setHorizontalHeaderLabels(["阶段", "高分", "中等", "低分"])
        heat_layout.addWidget(self._analytics_heat_table)
        trend_row.addWidget(heat_group, stretch=2)
        heat_group.setMinimumHeight(740)
        content_layout.addLayout(trend_row, stretch=2)

        bottom_row = QHBoxLayout()
        tag_group = QGroupBox("分类统计｜热门标签 Top 10")
        tag_layout = QVBoxLayout(tag_group)
        self._analytics_tag_bars: dict[str, QProgressBar] = {}
        self._analytics_tag_layout = tag_layout
        bottom_row.addWidget(tag_group)

        source_group = QGroupBox("来源统计｜来源机构 Top 10")
        source_layout = QVBoxLayout(source_group)
        self._analytics_source_bars: dict[str, QProgressBar] = {}
        self._analytics_source_layout = source_layout
        bottom_row.addWidget(source_group)
        content_layout.addLayout(bottom_row)

        insight_group = QGroupBox("趋势分析结论")
        insight_layout = QVBoxLayout(insight_group)
        self._analytics_insight = QPlainTextEdit()
        self._analytics_insight.setReadOnly(True)
        self._analytics_insight.setMinimumHeight(150)
        self._analytics_insight.setStyleSheet("QPlainTextEdit { font-size: 14px; line-height: 1.6; }")
        insight_layout.addWidget(self._analytics_insight)
        content_layout.addWidget(insight_group)
        content_layout.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll, stretch=1)

    def _setup_tab_manual(self) -> None:
        layout = QVBoxLayout(self._tab_manual)
        form = QFormLayout()
        self._manual_range = QComboBox()
        self._manual_range.addItems(["24h", "3d", "7d"])
        self._manual_extra = QTextEdit()
        self._manual_extra.setPlaceholderText("可选：对本次分析的补充说明或约束…")
        self._manual_extra.setMaximumHeight(120)
        form.addRow("时间范围", self._manual_range)
        form.addRow("补充说明", self._manual_extra)
        layout.addLayout(form)

        row = QHBoxLayout()
        self._btn_run_ai = QPushButton("开始 AI 搜索分析")
        self._btn_run_ai.clicked.connect(self._run_manual_analysis_async)
        row.addWidget(self._btn_run_ai)
        row.addStretch()
        layout.addLayout(row)

        self._manual_output = QPlainTextEdit()
        self._manual_output.setReadOnly(True)
        layout.addWidget(QLabel("输出（结构化 JSON）"))
        layout.addWidget(self._manual_output)

    def _setup_tab_settings(self) -> None:
        root = QVBoxLayout(self._tab_settings)

        g_store = QGroupBox("本地存储（持久化）")
        lay_store = QVBoxLayout(g_store)
        self._storage_paths_text = QPlainTextEdit()
        self._storage_paths_text.setReadOnly(True)
        self._storage_paths_text.setMinimumHeight(120)
        self._storage_paths_text.setMaximumHeight(200)
        btn_paths = QPushButton("刷新路径说明")
        btn_paths.clicked.connect(self._update_storage_paths_hint)
        lay_store.addWidget(self._storage_paths_text)
        lay_store.addWidget(btn_paths)
        root.addWidget(g_store)

        g_ai = QGroupBox("DeepSeek")
        f_ai = QFormLayout(g_ai)
        self._set_api_key = QLineEdit()
        self._set_api_key.setEchoMode(QLineEdit.Password)
        self._set_base_url = QLineEdit()
        self._set_model = QLineEdit()
        f_ai.addRow("API Key", self._set_api_key)
        f_ai.addRow("Base URL", self._set_base_url)
        f_ai.addRow("Model", self._set_model)

        g_mail = QGroupBox("邮件 SMTP")
        f_mail = QFormLayout(g_mail)
        self._set_smtp_host = QLineEdit()
        self._set_smtp_port = QSpinBox()
        self._set_smtp_port.setRange(1, 65535)
        self._set_smtp_user = QLineEdit()
        self._set_smtp_pass = QLineEdit()
        self._set_smtp_pass.setEchoMode(QLineEdit.Password)
        self._set_smtp_ssl = QCheckBox("使用 SSL（端口 465 等）")
        self._set_smtp_ssl.setChecked(True)
        self._set_recipients = QLineEdit()
        self._set_recipients.setPlaceholderText("多个收件人用英文逗号分隔")
        f_mail.addRow("服务器", self._set_smtp_host)
        f_mail.addRow("端口", self._set_smtp_port)
        f_mail.addRow("账号", self._set_smtp_user)
        f_mail.addRow("密码", self._set_smtp_pass)
        f_mail.addRow("", self._set_smtp_ssl)
        f_mail.addRow("收件人", self._set_recipients)

        g_sched = QGroupBox("定时任务（占位，后续接入完整管线）")
        fs = QFormLayout(g_sched)
        self._chk_m = QCheckBox("启用")
        self._time_m = QLineEdit()
        self._chk_n = QCheckBox("启用")
        self._time_n = QLineEdit()
        self._chk_e = QCheckBox("启用")
        self._time_e = QLineEdit()
        fs.addRow("早间", self._chk_m)
        fs.addRow("早间时间", self._time_m)
        fs.addRow("午间", self._chk_n)
        fs.addRow("午间时间", self._time_n)
        fs.addRow("晚间", self._chk_e)
        fs.addRow("晚间时间", self._time_e)

        g_other = QGroupBox("其他")
        fo = QFormLayout(g_other)
        self._set_keywords = QLineEdit()
        self._set_keywords.setPlaceholderText("关键词用逗号分隔")
        self._set_db_path = QLineEdit()
        self._set_db_path.textChanged.connect(self._update_storage_paths_hint)
        self._set_log_level = QComboBox()
        self._set_log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self._set_prompt = QTextEdit()
        self._set_prompt.setPlaceholderText("自定义系统 Prompt（留空则使用内置）")
        self._set_prompt.setMaximumHeight(160)
        fo.addRow("行业关键词", self._set_keywords)
        fo.addRow("数据库路径", self._set_db_path)
        fo.addRow("日志级别", self._set_log_level)
        fo.addRow("系统 Prompt", self._set_prompt)

        btn_row = QHBoxLayout()
        self._btn_save_settings = QPushButton("保存设置")
        self._btn_save_settings.clicked.connect(self._save_settings_async)
        btn_row.addWidget(self._btn_save_settings)
        btn_row.addStretch()

        # 左右分栏，避免最大化时所有表单项挤在一条竖线里
        splitter = QSplitter(Qt.Horizontal)
        left_col = QWidget()
        ll = QVBoxLayout(left_col)
        ll.setContentsMargins(0, 0, 8, 0)
        ll.addWidget(g_ai)
        ll.addWidget(g_mail)
        ll.addStretch()

        right_col = QWidget()
        rl = QVBoxLayout(right_col)
        rl.setContentsMargins(8, 0, 0, 0)
        rl.addWidget(g_sched)
        rl.addWidget(g_other)
        rl.addStretch()

        splitter.addWidget(left_col)
        splitter.addWidget(right_col)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setChildrenCollapsible(False)

        root.addWidget(g_store)
        root.addWidget(splitter, stretch=1)
        root.addLayout(btn_row)

    def _setup_tab_log(self) -> None:
        layout = QVBoxLayout(self._tab_log)
        self._log_edit = QPlainTextEdit()
        self._log_edit.setReadOnly(True)
        self._sched_status = QLabel("定时任务线程：运行中")
        layout.addWidget(self._sched_status)
        layout.addWidget(self._log_edit)

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
        if not self._is_dark:
            app.setStyleSheet(
                "QMainWindow, QWidget { background: #eef3f8; color: #1f2d3d; }"
                "QGroupBox { background: #ffffff; border: 1px solid #c8d7e6; border-radius: 8px; margin-top: 12px; padding: 12px; }"
                "QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #0b63ce; font-weight: 600; }"
                "QTabWidget::pane { border: 1px solid #c8d7e6; background: #f7fbff; }"
                "QTabBar::tab { padding: 8px 18px; background: #dce8f5; border: 1px solid #c8d7e6; border-bottom: none; }"
                "QTabBar::tab:selected { background: #ffffff; color: #0b63ce; font-weight: 600; }"
                "QPushButton { background: #0b63ce; color: white; border: none; border-radius: 5px; padding: 6px 12px; }"
                "QPushButton:hover { background: #084f9f; }"
                "QLineEdit, QComboBox, QTextEdit, QPlainTextEdit, QTableWidget, QListWidget { background: #ffffff; border: 1px solid #c8d7e6; border-radius: 4px; padding: 4px; }"
                "QProgressBar { border: 1px solid #c8d7e6; border-radius: 5px; background: #edf4fb; text-align: center; min-height: 18px; }"
                "QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #12b5cb, stop:1 #0b63ce); border-radius: 4px; }"
                "QLabel#KpiValue { color: #0b63ce; font-size: 26px; font-weight: 700; }"
            )
        else:
            app.setStyleSheet("")

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

        logger.add(
            sink,
            format="{time:HH:mm:ss} | {level} | {message}",
            level=self._settings.log_level,
            enqueue=True,
        )

    @Slot(str)
    def _append_log_line(self, text: str) -> None:
        self._log_edit.appendPlainText(text.rstrip())

    # --- 设置读写 ---
    def _reload_settings_into_widgets(self) -> None:
        s = self._settings
        self._set_api_key.setText(s.deepseek_api_key)
        self._set_base_url.setText(s.deepseek_base_url)
        self._set_model.setText(s.deepseek_model)
        self._set_smtp_host.setText(s.smtp_host)
        self._set_smtp_port.setValue(int(s.smtp_port))
        self._set_smtp_user.setText(s.smtp_user)
        self._set_smtp_pass.setText(s.smtp_password)
        self._set_smtp_ssl.setChecked(s.smtp_use_ssl)
        self._set_recipients.setText(",".join(s.mail_recipients))
        self._chk_m.setChecked(s.scheduler_morning.enabled)
        self._time_m.setText(s.scheduler_morning.time)
        self._chk_n.setChecked(s.scheduler_noon.enabled)
        self._time_n.setText(s.scheduler_noon.time)
        self._chk_e.setChecked(s.scheduler_evening.enabled)
        self._time_e.setText(s.scheduler_evening.time)
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
        s = AppSettings(
            log_level=self._set_log_level.currentText(),
            deepseek_api_key=self._set_api_key.text().strip(),
            deepseek_base_url=self._set_base_url.text().strip() or "https://api.deepseek.com",
            deepseek_model=self._set_model.text().strip() or "deepseek-chat",
            smtp_host=self._set_smtp_host.text().strip(),
            smtp_port=int(self._set_smtp_port.value()),
            smtp_user=self._set_smtp_user.text().strip(),
            smtp_password=self._set_smtp_pass.text(),
            smtp_use_ssl=self._set_smtp_ssl.isChecked(),
            mail_recipients=rec,
            scheduler_morning=SchedulerSlot(
                enabled=self._chk_m.isChecked(),
                time=self._time_m.text().strip() or "07:30",
            ),
            scheduler_noon=SchedulerSlot(
                enabled=self._chk_n.isChecked(),
                time=self._time_n.text().strip() or "12:30",
            ),
            scheduler_evening=SchedulerSlot(
                enabled=self._chk_e.isChecked(),
                time=self._time_e.text().strip() or "20:00",
            ),
            industry_keywords=kws or self._settings.industry_keywords,
            database_path=self._set_db_path.text().strip() or self._settings.database_path,
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
        self._populate_dashboard(rows[:8])
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

    def _filtered_analytics_rows(self) -> list[dict]:
        rows = list(self._cached_rows)
        if not hasattr(self, "_analytics_range"):
            return rows

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
        if not hasattr(self, "_analytics_kpis"):
            return
        rows = self._filtered_analytics_rows()
        total = len(rows)
        scores = [self._score_value(row) for row in rows]
        avg_score = sum(scores) / total if total else 0
        high_count = sum(1 for row in rows if self._score_bucket(row) == "高分(>=80)")
        source_count = sum(1 for row in rows if str(row.get("source_url", "")).strip())
        self._analytics_kpis["total"].setText(str(total))
        self._analytics_kpis["avg_score"].setText(f"{avg_score:.1f}")
        self._analytics_kpis["high_ratio"].setText(f"{(high_count / total * 100) if total else 0:.0f}%")
        self._analytics_kpis["source_ratio"].setText(f"{(source_count / total * 100) if total else 0:.0f}%")

        score_counts = {"高分(>=80)": 0, "中等(50-79)": 0, "低分(<50)": 0}
        for row in rows:
            score_counts[self._score_bucket(row)] += 1
        self._update_bar_group(self._analytics_score_bars, score_counts, total)

        stage_counts = Counter(str(row.get("stage", "未分类") or "未分类") for row in rows)
        self._clear_layout(self._stage_bars_layout)
        self._analytics_stage_bars = self._create_bar_group(self._stage_bars_layout, tuple(stage_counts.keys()) or ("暂无数据",))
        self._update_bar_group(self._analytics_stage_bars, dict(stage_counts), total)

        tag_counts: Counter[str] = Counter()
        source_counts: Counter[str] = Counter()
        date_counts: dict[str, list[float]] = defaultdict(list)
        heat: dict[str, Counter[str]] = defaultdict(Counter)
        for row in rows:
            for tag in self._split_tags(row.get("tags", "")):
                tag_counts[tag] += 1
            source_counts[str(row.get("source", "未知来源") or "未知来源")] += 1
            date_key = self._parse_datetime(row.get("timestamp", "")).strftime("%Y-%m-%d")
            date_counts[date_key].append(self._score_value(row))
            stage_name = str(row.get("stage", "未分类") or "未分类").strip() or "未分类"
            heat[stage_name][self._score_bucket(row)] += 1

        self._rebuild_dynamic_bar_group(self._analytics_tag_layout, self._analytics_tag_bars, tag_counts, "暂无标签数据")
        self._rebuild_dynamic_bar_group(self._analytics_source_layout, self._analytics_source_bars, source_counts, "暂无来源数据")
        self._populate_trend_table(date_counts)
        self._populate_heat_table(heat)
        self._analytics_insight.setPlainText(self._build_analytics_insight(rows, date_counts, score_counts, source_count))

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

    def _populate_dashboard(self, rows: list) -> None:
        self._dash_list.clear()
        for item in rows:
            title = str(item.get("title", "未命名情报"))
            ts = self._format_datetime(item.get("timestamp", ""))
            score = item.get("score", "")
            source = str(item.get("source", "未知来源"))
            source_url = str(item.get("source_url", "")).strip()
            source_line = f"来源：{source}"
            if source_url:
                source_line += f"｜地址：{source_url}"
            lw_item = QListWidgetItem(f"{ts}｜{title}\n{source_line}  评分：{score}")
            lw_item.setData(Qt.UserRole, item)
            self._dash_list.addItem(lw_item)
        self._update_dashboard_chart(self._cached_rows)
        if rows:
            self._dash_list.setCurrentRow(0)
        else:
            self._dash_detail.setPlainText("暂无情报记录。")

    @Slot(QListWidgetItem, QListWidgetItem)
    def _on_dashboard_item_changed(
        self,
        current: QListWidgetItem | None,
        previous: QListWidgetItem | None,
    ) -> None:
        del previous
        if current is None:
            self._dash_detail.setPlainText("暂无选中的情报。")
            return
        item = current.data(Qt.UserRole)
        if isinstance(item, dict):
            self._dash_detail.setPlainText(self._format_record_detail(item))

    def _format_record_detail(self, item: dict) -> str:
        fields = [
            ("标题", item.get("title", "")),
            ("时间", self._format_datetime(item.get("timestamp", ""))),
            ("来源", item.get("source", "")),
            ("来源地址", item.get("source_url", "")),
            ("评分", item.get("score", "")),
            ("阶段", item.get("stage", "")),
            ("标签", item.get("tags", "")),
            ("摘要", item.get("summary", "")),
            ("影响", self._format_json_like_text(item.get("impact", ""))),
            ("内容", item.get("content", "")),
        ]
        lines: list[str] = []
        for label, value in fields:
            text = str(value).strip()
            if not text:
                continue
            lines.append(f"【{label}】")
            lines.append(text)
            lines.append("")
        return "\n".join(lines).strip() or "暂无详情。"

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

    def _update_dashboard_chart(self, rows: list[dict]) -> None:
        buckets = {"高分(>=80)": 0, "中等(50-79)": 0, "低分(<50)": 0}
        for item in rows:
            score = self._score_value(item)
            if score >= 80:
                buckets["高分(>=80)"] += 1
            elif score >= 50:
                buckets["中等(50-79)"] += 1
            else:
                buckets["低分(<50)"] += 1

        total = sum(buckets.values())
        max_count = max(max(buckets.values()), 1)
        self._dash_stats_summary.setText(f"共 {total} 条情报｜按评分分布统计")

        for label, count in buckets.items():
            bar = self._dash_score_bars[label]
            bar.setRange(0, max_count)
            bar.setValue(count)
            percent = (count / total * 100) if total else 0
            bar.setFormat(f"{count} 条 · {percent:.0f}%")

    @Slot(str)
    def _on_scheduler_job_due(self, slot_name: str) -> None:
        logger.info("收到定时任务触发信号：{}", slot_name)
        self._run_scheduled_analysis_async(slot_name)

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
        title = str(data.get("title") or "定时行业情报")
        summary = str(data.get("summary") or "暂无摘要")
        source = str(data.get("source") or "未知来源")
        source_url = str(data.get("source_url") or "")
        score = str(data.get("score") or "")
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

    @Slot(str)
    def _on_scheduled_mail_fail(self, msg: str) -> None:
        self.statusBar().showMessage("定时报告邮件发送失败", 8000)
        self._append_log_line(f"定时报告邮件发送失败：{msg}")

    @Slot(str)
    def _on_scheduled_analysis_fail(self, msg: str) -> None:
        self.statusBar().showMessage("定时分析失败", 8000)
        self._append_log_line(f"定时分析失败：{msg}")

    def _run_manual_analysis_async(self) -> None:
        self._settings = self._read_settings_from_widgets()
        if not self._settings.deepseek_api_key.strip():
            QMessageBox.information(
                self,
                "提示",
                "请在「设置」中填写 DeepSeek API Key。\n"
                "填写后可直接点「开始 AI 搜索分析」；点「保存设置」可将配置写入本地文件以便下次启动使用。",
            )
            self._tabs.setCurrentIndex(3)
            return

        self._btn_run_ai.setEnabled(False)
        self._manual_output.setPlainText("")
        self.statusBar().showMessage("正在调用 DeepSeek API（后台线程）…", 0)

        tr = self._manual_range.currentText()
        extra = self._manual_extra.toPlainText()
        thread = QThread(self)
        worker = AiAnalysisWorker(self._settings, user_extra=extra, time_range=tr, persist=True)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished_ok.connect(self._on_ai_analysis_ok)
        worker.failed.connect(self._on_ai_analysis_fail)
        worker.log_line.connect(self._append_log_line)
        worker.finished_ok.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.finished_ok.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._retain_worker_thread(thread, worker)
        thread.start()

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
        worker.failed.connect(self._on_mail_send_fail)
        worker.finished_ok.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.finished_ok.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._retain_worker_thread(thread, worker)
        thread.start()

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
            "行业情报系统 v1.0\n"
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
