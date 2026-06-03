"""紧凑现代新闻表格组件。"""

from __future__ import annotations

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


class NewsTableWidget(QTableWidget):
    """新闻数据展示表格：紧凑行高、短摘要、详情弹窗。"""

    delete_requested = Signal(int, str)

    def __init__(self, parent: object | None = None) -> None:
        super().__init__(0, 6, parent)  # type: ignore[arg-type]
        self._rows: list[dict] = []
        self._visible_count = 120
        self.setHorizontalHeaderLabels(["标题", "发布时间", "来源", "摘要", "详情", "操作"])
        self.setAlternatingRowColors(True)
        self.setWordWrap(True)
        self.setShowGrid(False)
        self.setMouseTracking(True)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(72)
        self.verticalHeader().setMinimumSectionSize(64)
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.setColumnWidth(1, 112)
        self.setColumnWidth(2, 110)
        self.setColumnWidth(4, 98)
        self.setColumnWidth(5, 86)
        self.cellClicked.connect(self._open_link_if_title_clicked)

    @property
    def visible_count(self) -> int:
        return self._visible_count

    def set_rows(self, rows: list[dict], visible_count: int | None = None) -> int:
        self._rows = rows
        if visible_count is not None:
            self._visible_count = max(40, visible_count)
        return self._render_rows()

    def load_more(self, step: int = 80) -> int:
        self._visible_count += step
        return self._render_rows()

    def total_count(self) -> int:
        return len(self._rows)

    def rendered_count(self) -> int:
        return min(len(self._rows), self._visible_count)

    def reset_delete_buttons(self) -> None:
        for row in range(self.rowCount()):
            widget = self.cellWidget(row, 5)
            if isinstance(widget, QPushButton):
                widget.setEnabled(True)
                widget.setText("删除")

    def _render_rows(self) -> int:
        self.setUpdatesEnabled(False)
        self.setRowCount(0)
        rendered = self.rendered_count()
        for item in self._rows[:rendered]:
            self._append_row(item)
        self.setUpdatesEnabled(True)
        return rendered

    def _append_row(self, item: dict) -> None:
        row = self.rowCount()
        self.insertRow(row)
        self.setRowHeight(row, 72)

        title = str(item.get("title", ""))
        url = str(item.get("url", "")).strip()
        source = str(item.get("source", ""))
        summary = str(item.get("summary", ""))
        publish_time = self._format_datetime(item.get("publish_time", ""))

        title_cell = QTableWidgetItem(title)
        title_font = QFont()
        title_font.setWeight(QFont.DemiBold)
        title_cell.setFont(title_font)
        title_cell.setForeground(QColor("#1d4ed8"))
        title_cell.setData(Qt.UserRole, url)
        title_cell.setToolTip(f"{title}\n\n点击打开：{url}" if url else title)
        self.setItem(row, 0, title_cell)

        time_cell = QTableWidgetItem(publish_time)
        time_cell.setForeground(QColor("#64748b"))
        self.setItem(row, 1, time_cell)

        source_cell = QTableWidgetItem(self._ellipsize(source, 20))
        source_cell.setToolTip(source)
        source_cell.setForeground(QColor("#475569"))
        self.setItem(row, 2, source_cell)

        summary_cell = QTableWidgetItem(self._ellipsize(summary, 96))
        summary_cell.setForeground(QColor("#334155"))
        summary_cell.setToolTip(summary or "暂无摘要")
        self.setItem(row, 3, summary_cell)

        detail_btn = QPushButton("查看详情")
        detail_btn.setObjectName("GhostButton")
        detail_btn.setProperty("news_title", title)
        detail_btn.setProperty("news_summary", summary)
        detail_btn.clicked.connect(self._show_summary_dialog)
        self.setCellWidget(row, 4, detail_btn)

        delete_btn = QPushButton("删除")
        delete_btn.setObjectName("DangerButton")
        delete_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogDiscardButton))
        delete_btn.setProperty("news_id", item.get("id"))
        delete_btn.setProperty("news_title", title)
        delete_btn.clicked.connect(self._emit_delete_request)
        self.setCellWidget(row, 5, delete_btn)

    def _open_link_if_title_clicked(self, row: int, column: int) -> None:
        if column != 0:
            return
        item = self.item(row, column)
        if item is None:
            return
        url = str(item.data(Qt.UserRole) or "").strip()
        if url:
            QDesktopServices.openUrl(QUrl(url))

    def _show_summary_dialog(self) -> None:
        button = self.sender()
        if not isinstance(button, QPushButton):
            return
        title = str(button.property("news_title") or "新闻详情")
        summary = str(button.property("news_summary") or "暂无摘要")
        dialog = QDialog(self)
        dialog.setWindowTitle("新闻摘要详情")
        dialog.resize(720, 520)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        title_label = QLabel(title)
        title_label.setWordWrap(True)
        title_label.setObjectName("DialogTitle")
        detail = QPlainTextEdit()
        detail.setReadOnly(True)
        detail.setPlainText(summary)
        detail.setMinimumHeight(360)
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        actions = QHBoxLayout()
        actions.addStretch()
        actions.addWidget(close_btn)
        layout.addWidget(title_label)
        layout.addWidget(detail, stretch=1)
        layout.addLayout(actions)
        dialog.exec()

    def _emit_delete_request(self) -> None:
        button = self.sender()
        if not isinstance(button, QPushButton):
            return
        try:
            news_id = int(button.property("news_id"))
        except (TypeError, ValueError):
            return
        title = str(button.property("news_title") or "未命名新闻")
        button.setEnabled(False)
        button.setText("删除中…")
        self.delete_requested.emit(news_id, title)

    @staticmethod
    def _ellipsize(text: str, limit: int) -> str:
        clean = " ".join(str(text or "").split())
        return clean if len(clean) <= limit else f"{clean[:limit]}..."

    @staticmethod
    def _format_datetime(value: object) -> str:
        if value is None:
            return ""
        if hasattr(value, "strftime"):
            return value.strftime("%Y-%m-%d")  # type: ignore[no-any-return]
        text = str(value).strip()
        return text[:10].replace("T", " ")
