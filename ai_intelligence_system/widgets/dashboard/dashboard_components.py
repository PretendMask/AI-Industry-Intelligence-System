"""仪表盘专用 UI 组件：情报卡片、搜索筛选、结构化详情、KPI、环形图、标签进度条、概览面板。"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


# ──────────────────────────────────────────────
# 常量
# ──────────────────────────────────────────────
PRIMARY = "#2563EB"
PRIMARY_LIGHT = "#EFF6FF"
PRIMARY_BG = "#DBEAFE"
BG = "#F5F7FA"
CARD_BG = "#FFFFFF"
TEXT_PRIMARY = "#1E293B"
TEXT_SECONDARY = "#64748B"
TEXT_MUTED = "#94A3B8"
BORDER = "#E2E8F0"
SUCCESS = "#10B981"
DANGER = "#EF4444"
WARNING = "#F59E0B"

STAGE_COLORS = {
    "信息冲击期": "#3B82F6",
    "情绪加速期": "#10B981",
    "利多兑现期": "#F59E0B",
    "不确定": "#8B5CF6",
}

# KPI图标（使用Unicode符号替代Emoji）
KPI_ICONS = {
    "情报数": "📊",
    "平均评分": "📈",
    "紧迫占比": "🎯",
    "时间比": "🕐",
}

# 标签"利好/政策利好"型关键词 → 绿色 chip
TAG_GREEN_KEYWORDS = {"利好政策", "利好", "已解决", "利多兑现期"}
# 标签"科技创新/研发"型关键词 → 灰色 chip
TAG_GRAY_KEYWORDS = {"科技创新", "技术", "新能源"}


# ──────────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────────
def _score_to_100(score: object) -> float:
    """将数据库 score (1-10) 转换为 0-100 分制。"""
    try:
        s = float(score or 0)
    except (TypeError, ValueError):
        return 0.0
    return s * 10 if 0 < s <= 10 else s


def _score_bucket_100(score_100: float) -> str:
    if score_100 >= 80:
        return "high"
    if score_100 >= 50:
        return "medium"
    return "low"


def _format_ts(value: object) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    text = str(value or "").strip()
    if not text:
        return ""
    normalized = text.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
        return dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return text[:16]


def _split_tags(value: object) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []
    import json
    try:
        loaded = json.loads(text)
        if isinstance(loaded, list):
            return [str(item).strip() for item in loaded if str(item).strip()]
    except (json.JSONDecodeError, TypeError):
        pass
    return [part.strip() for part in text.replace("，", ",").split(",") if part.strip()]


def _stage_color(stage: str) -> str:
    return STAGE_COLORS.get(stage, TEXT_MUTED)


def _stage_bg(stage: str) -> str:
    color = _stage_color(stage)
    return {
        "信息冲击期": "#DBEAFE",
        "情绪加速期": "#D1FAE5",
        "利多兑现期": "#FEF3C7",
        "不确定": "#EDE9FE",
    }.get(stage, "#F1F5F9")


def _score_color(score_100: float) -> str:
    if score_100 >= 80:
        return SUCCESS
    if score_100 >= 50:
        return PRIMARY
    return WARNING


def _tag_chip_color(tag: str) -> tuple[str, str, str]:
    """根据标签返回 (背景色, 前景色, 边框色) 三个颜色字符串。"""
    t = tag.strip()
    if t in TAG_GREEN_KEYWORDS or any(k in t for k in ("利好", "利多", "已解决")):
        return "#D1FAE5", "#047857", "#10B981"
    if t in TAG_GRAY_KEYWORDS or any(k in t for k in ("科技", "技术", "新能源")):
        return "#F1F5F9", "#475569", "#CBD5E1"
    return "#EFF6FF", "#2563EB", "#BFDBFE"





# ──────────────────────────────────────────────
# IntelligenceCardWidget
# ──────────────────────────────────────────────
class IntelligenceCardWidget(QWidget):
    """单条情报卡片，用于 IntelligenceListWidget。"""

    clicked = Signal(object)  # 发送 dict 数据

    def __init__(self, data: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data = data
        self._selected = False
        self.setObjectName("IntelligenceCard")
        self._build_ui()

    @property
    def data(self) -> dict:
        return self._data

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 左侧蓝色指示条
        indicator = QFrame()
        indicator.setObjectName("CardIndicator")
        indicator.setFixedWidth(4)
        indicator.setStyleSheet("background-color: #2563EB; border-radius: 2px 0 0 2px;")
        layout.addWidget(indicator)

        # 内容区域
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(12, 10, 12, 10)
        content_layout.setSpacing(6)

        # 标题行（带蓝色圆点）
        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        # 蓝色圆点
        dot = QLabel("●")
        dot.setObjectName("CardDot")
        dot.setStyleSheet("color: #2563EB; font-size: 10px;")
        title_row.addWidget(dot)

        # 标题
        title = str(self._data.get("title", "未命名情报"))
        title_label = QLabel(title)
        title_label.setObjectName("CardTitle")
        title_label.setWordWrap(True)
        title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        title_row.addWidget(title_label, stretch=1)

        # 右侧箭头
        arrow = QLabel("›")
        arrow.setObjectName("CardArrow")
        arrow.setStyleSheet("color: #2563EB; font-size: 18px; font-weight: bold;")
        title_row.addWidget(arrow)

        content_layout.addLayout(title_row)

        # 元信息行：时间·来源 + 评分徽章（靠右）+ 阶段徽章（靠右）
        meta_row = QHBoxLayout()
        meta_row.setSpacing(16)

        ts = _format_ts(self._data.get("timestamp", ""))
        if ts:
            time_label = QLabel(f"🕐 {ts}")
            time_label.setObjectName("CardMeta")
            meta_row.addWidget(time_label)

        source = str(self._data.get("source", ""))
        if source:
            source_label = QLabel(f"🏛️ {source}")
            source_label.setObjectName("CardSource")
            meta_row.addWidget(source_label)

        # 评分徽章
        score_100 = _score_to_100(self._data.get("score", 0))
        score_label = QLabel(f"{score_100:.1f}")
        score_label.setObjectName("CardScore")
        score_label.setStyleSheet(
            "background-color: #EFF6FF; color: #2563EB; border: 1px solid #2563EB; "
            "border-radius: 12px; padding: 2px 10px; font-size: 12px; font-weight: bold;"
        )
        meta_row.addWidget(score_label)

        meta_row.addStretch()

        # 阶段徽章
        stage = str(self._data.get("stage", ""))
        if stage:
            stage_label = QLabel(stage)
            stage_label.setObjectName("CardStage")
            stage_color = _stage_color(stage)
            stage_bg = _stage_bg(stage)
            stage_label.setStyleSheet(
                f"background-color: {stage_bg}; color: {stage_color}; "
                f"border: 1px solid {stage_color}; border-radius: 12px; "
                f"padding: 2px 10px; font-size: 12px;"
            )
            meta_row.addWidget(stage_label)

        content_layout.addLayout(meta_row)

        layout.addWidget(content, stretch=1)

        self.setMinimumHeight(88)

    def tag_clicked_inline(self, tag: str) -> None:
        """本地占位：保留接口，子类/外部可监听后将 tag 同步到筛选栏。"""
        # 留作占位实现：实际触发由 IntelligenceListWidget 接管。
        pass

    def mousePressEvent(self, event) -> None:
        super().mousePressEvent(event)
        self.clicked.emit(self._data)


# ──────────────────────────────────────────────
# IntelligenceListWidget
# ──────────────────────────────────────────────
class IntelligenceListWidget(QWidget):
    """情报卡片列表容器，支持选中联动。"""

    item_selected = Signal(object)  # 发送 dict 数据

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._cards: list[IntelligenceCardWidget] = []
        self._selected_index: int = -1
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._container = QWidget()
        self._container.setObjectName("DashListBody")
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setContentsMargins(0, 0, 0, 0)
        self._container_layout.setSpacing(6)
        self._container_layout.addStretch()

        self._scroll.setWidget(self._container)
        layout.addWidget(self._scroll, stretch=1)

        # 分页控件
        self._pagination = self._create_pagination()
        layout.addWidget(self._pagination)

    def _create_pagination(self) -> QWidget:
        """创建底部分页控件。"""
        page_widget = QWidget()
        page_widget.setObjectName("PaginationWidget")
        page_layout = QHBoxLayout(page_widget)
        page_layout.setContentsMargins(0, 8, 0, 8)
        page_layout.setSpacing(4)
        page_layout.addStretch()

        self._prev_btn = QPushButton("‹")
        self._prev_btn.setObjectName("PageButton")
        self._prev_btn.setFixedSize(28, 28)
        self._prev_btn.clicked.connect(self._on_prev_page)
        page_layout.addWidget(self._prev_btn)

        self._page_label = QLabel("1")
        self._page_label.setObjectName("PageLabel")
        self._page_label.setAlignment(Qt.AlignCenter)
        self._page_label.setFixedSize(28, 28)
        page_layout.addWidget(self._page_label)

        self._next_btn = QPushButton("›")
        self._next_btn.setObjectName("PageButton")
        self._next_btn.setFixedSize(28, 28)
        self._next_btn.clicked.connect(self._on_next_page)
        page_layout.addWidget(self._next_btn)

        page_layout.addStretch()
        return page_widget

    def _on_prev_page(self) -> None:
        pass  # 后续实现分页逻辑

    def _on_next_page(self) -> None:
        pass  # 后续实现分页逻辑

    def set_items(self, items: list[dict]) -> None:
        # 清除旧卡片
        for card in self._cards:
            card.deleteLater()
        self._cards.clear()
        self._selected_index = -1

        if not items:
            empty = QLabel("暂无情报")
            empty.setObjectName("EmptyStateTitle")
            empty.setAlignment(Qt.AlignCenter)
            self._container_layout.insertWidget(0, empty)

            empty_sub = QLabel("当前暂无可展示的行业情报")
            empty_sub.setObjectName("EmptyStateSub")
            empty_sub.setAlignment(Qt.AlignCenter)
            self._container_layout.insertWidget(1, empty_sub)
            return

        for idx, item in enumerate(items):
            card = IntelligenceCardWidget(item)
            card.clicked.connect(self._on_card_clicked)
            self._container_layout.insertWidget(idx, card)
            self._cards.append(card)

        if self._cards:
            self._select_card(0)

    def _on_card_clicked(self, data: dict) -> None:
        for idx, card in enumerate(self._cards):
            if card.data is data:
                self._select_card(idx)
                break

    def _select_card(self, index: int) -> None:
        if index < 0 or index >= len(self._cards):
            return
        if self._selected_index >= 0 and self._selected_index < len(self._cards):
            self._cards[self._selected_index].set_selected(False)
        self._selected_index = index
        self._cards[index].set_selected(True)
        self.item_selected.emit(self._cards[index].data)

    def clear_selection(self) -> None:
        if self._selected_index >= 0 and self._selected_index < len(self._cards):
            self._cards[self._selected_index].set_selected(False)
        self._selected_index = -1


# ──────────────────────────────────────────────
# SearchFilterBar
# ──────────────────────────────────────────────
class SearchFilterBar(QWidget):
    """搜索 + 来源筛选 + 阶段筛选 + 排序。"""

    search_changed = Signal(str)       # 搜索关键词
    source_changed = Signal(str)       # 来源
    stage_changed = Signal(str)        # 阶段
    sort_changed = Signal(str)         # 排序方式

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(10)

        # 搜索框
        from PySide6.QtWidgets import QLineEdit
        self._search = QLineEdit()
        self._search.setObjectName("SearchInput")
        self._search.setPlaceholderText("搜索标题、来源、关键词...")
        self._search.textChanged.connect(self.search_changed.emit)
        layout.addWidget(self._search, stretch=2)

        # 来源筛选
        from PySide6.QtWidgets import QComboBox
        self._source_combo = QComboBox()
        self._source_combo.setObjectName("SaasCombo")
        self._source_combo.addItem("全部来源")
        self._source_combo.setFixedWidth(120)
        self._source_combo.currentTextChanged.connect(self.source_changed.emit)
        layout.addWidget(self._source_combo)

        # 阶段筛选
        self._stage_combo = QComboBox()
        self._stage_combo.setObjectName("SaasCombo")
        self._stage_combo.addItem("全部阶段")
        self._stage_combo.setFixedWidth(120)
        self._stage_combo.currentTextChanged.connect(self.stage_changed.emit)
        layout.addWidget(self._stage_combo)

        # 排序
        self._sort_combo = QComboBox()
        self._sort_combo.setObjectName("SaasCombo")
        self._sort_combo.addItems(["最新", "评分最高"])
        self._sort_combo.setFixedWidth(125)
        self._sort_combo.currentTextChanged.connect(self._on_sort_changed)
        layout.addWidget(self._sort_combo)

    def _on_sort_changed(self, text: str) -> None:
        sort_key = "time_desc" if text == "最新" else "score_desc"
        self.sort_changed.emit(sort_key)

    def set_sources(self, sources: list[str]) -> None:
        current = self._source_combo.currentText()
        self._source_combo.blockSignals(True)
        self._source_combo.clear()
        self._source_combo.addItem("全部来源")
        self._source_combo.addItems(sources)
        idx = self._source_combo.findText(current)
        if idx >= 0:
            self._source_combo.setCurrentIndex(idx)
        self._source_combo.blockSignals(False)

    def set_stages(self, stages: list[str]) -> None:
        current = self._stage_combo.currentText()
        self._stage_combo.blockSignals(True)
        self._stage_combo.clear()
        self._stage_combo.addItem("全部阶段")
        self._stage_combo.addItems(stages)
        idx = self._stage_combo.findText(current)
        if idx >= 0:
            self._stage_combo.setCurrentIndex(idx)
        self._stage_combo.blockSignals(False)

    def get_search_text(self) -> str:
        return self._search.text().strip()

    def get_source(self) -> str:
        return self._source_combo.currentText()

    def get_stage(self) -> str:
        return self._stage_combo.currentText()

    def get_sort(self) -> str:
        text = self._sort_combo.currentText()
        return "time_desc" if text == "最新" else "score_desc"


# ──────────────────────────────────────────────
# IntelligenceDetailView
# ──────────────────────────────────────────────
class IntelligenceDetailView(QWidget):
    """结构化情报详情面板。"""

    tag_clicked = Signal(str)   # 点击标签
    source_url_clicked = Signal(str)  # 点击原文链接

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._analysis_expanded = False
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.NoFrame)
        # 内容超宽时显示水平滚动条（与垂直滚动条一致），避免右侧内容无法查看
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self._content = QWidget()
        self._content.setObjectName("DashDetailBody")
        # 保持内容最小宽度：视口窄于该值时出现水平滚动条，可左右滚动查看
        self._content.setMinimumWidth(640)
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(16, 12, 16, 12)
        self._content_layout.setSpacing(12)

        # 标题行（标题 + 收藏按钮）
        title_row = QHBoxLayout()
        self._title_label = QLabel("")
        self._title_label.setObjectName("DetailTitle")
        self._title_label.setWordWrap(True)
        self._title_label.setStyleSheet("color: #1E293B; font-size: 16px; font-weight: bold;")
        title_row.addWidget(self._title_label, stretch=1)

        self._fav_btn = QPushButton("☆ 收藏")
        self._fav_btn.setObjectName("FavButton")
        self._fav_btn.setFixedSize(70, 28)
        title_row.addWidget(self._fav_btn)
        self._content_layout.addLayout(title_row)

        # 元信息行
        self._meta_layout = QHBoxLayout()
        self._meta_layout.setSpacing(12)
        self._content_layout.addLayout(self._meta_layout)

        # 摘要标题 + 内容
        self._summary_title = QLabel("摘要")
        self._summary_title.setObjectName("SectionTitle")
        self._summary_title.setStyleSheet("color: #1E293B; font-size: 13px; font-weight: bold;")
        self._content_layout.addWidget(self._summary_title)
        
        self._summary_label = QLabel("")
        self._summary_label.setObjectName("DetailText")
        self._summary_label.setWordWrap(True)
        self._summary_label.setStyleSheet("color: #475569; font-size: 13px;")
        self._content_layout.addWidget(self._summary_label)

        # 分析要点标题 + 内容
        self._kp_title = QLabel("分析要点")
        self._kp_title.setObjectName("SectionTitle")
        self._kp_title.setStyleSheet("color: #1E293B; font-size: 13px; font-weight: bold;")
        self._content_layout.addWidget(self._kp_title)
        
        self._kp_content = QLabel("")
        self._kp_content.setObjectName("DetailText")
        self._kp_content.setWordWrap(True)
        self._kp_content.setStyleSheet("color: #475569; font-size: 13px;")
        self._content_layout.addWidget(self._kp_content)

        # 标签标题 + 容器
        self._tags_title = QLabel("标签")
        self._tags_title.setObjectName("SectionTitle")
        self._tags_title.setStyleSheet("color: #1E293B; font-size: 13px; font-weight: bold;")
        self._content_layout.addWidget(self._tags_title)
        
        self._tags_container = QWidget()
        self._tags_layout = QHBoxLayout(self._tags_container)
        self._tags_layout.setContentsMargins(0, 0, 0, 0)
        self._tags_layout.setSpacing(6)
        self._content_layout.addWidget(self._tags_container)

        # 风险分析（可折叠）
        analysis_header = QHBoxLayout()
        self._analysis_title = QLabel("风险分析")
        self._analysis_title.setObjectName("SectionTitle")
        self._analysis_title.setStyleSheet("color: #1E293B; font-size: 13px; font-weight: bold;")
        analysis_header.addWidget(self._analysis_title)
        analysis_header.addStretch()
        self._analysis_toggle = QPushButton("展开查看 ∨")
        self._analysis_toggle.setObjectName("GhostButton")
        self._analysis_toggle.setStyleSheet(
            "background-color: transparent; color: #2563EB; border: none; "
            "font-size: 12px; padding: 4px 8px;"
        )
        self._analysis_toggle.clicked.connect(self._toggle_analysis)
        analysis_header.addWidget(self._analysis_toggle)
        self._content_layout.addLayout(analysis_header)

        self._analysis_label = QLabel("")
        self._analysis_label.setObjectName("DetailText")
        self._analysis_label.setWordWrap(True)
        self._analysis_label.setVisible(False)
        self._analysis_label.setStyleSheet("color: #475569; font-size: 13px;")
        self._content_layout.addWidget(self._analysis_label)

        self._content_layout.addStretch()
        self._scroll.setWidget(self._content)
        root.addWidget(self._scroll)

    def _toggle_analysis(self) -> None:
        self._analysis_expanded = not self._analysis_expanded
        self._analysis_label.setVisible(self._analysis_expanded)
        self._analysis_toggle.setText("收起 ∧" if self._analysis_expanded else "展开查看 ∨")

    def set_data(self, data: dict) -> None:
        # 标题
        title = str(data.get("title", "未命名情报"))
        self._title_label.setText(title)

        # 元信息
        self._clear_layout(self._meta_layout)
        ts = _format_ts(data.get("timestamp", ""))
        if ts:
            lbl = QLabel(f"🕐 {ts}")
            lbl.setObjectName("DetailMeta")
            lbl.setStyleSheet("color: #64748B; font-size: 12px;")
            self._meta_layout.addWidget(lbl)

        source = str(data.get("source", ""))
        if source:
            lbl = QLabel(f"🏛️ {source}")
            lbl.setObjectName("DetailMeta")
            lbl.setStyleSheet("color: #64748B; font-size: 12px;")
            self._meta_layout.addWidget(lbl)

        source_url = str(data.get("source_url", "")).strip()
        if source_url:
            link_btn = QPushButton("🔗 原文链接")
            link_btn.setObjectName("LinkButton")
            link_btn.setStyleSheet(
                "background-color: transparent; color: #2563EB; border: none; "
                "font-size: 12px; padding: 0;"
            )
            link_btn.clicked.connect(lambda: self.source_url_clicked.emit(source_url))
            self._meta_layout.addWidget(link_btn)

        score_100 = _score_to_100(data.get("score", 0))
        score_lbl = QLabel(f"评分 {score_100:.1f}")
        score_lbl.setObjectName("DetailScore")
        score_lbl.setStyleSheet(
            "background-color: #EFF6FF; color: #2563EB; border: 1px solid #2563EB; "
            "border-radius: 12px; padding: 2px 10px; font-size: 12px; font-weight: bold;"
        )
        self._meta_layout.addWidget(score_lbl)

        stage = str(data.get("stage", ""))
        if stage:
            stage_lbl = QLabel(stage)
            stage_lbl.setObjectName("DetailStage")
            stage_color = _stage_color(stage)
            stage_bg = _stage_bg(stage)
            stage_lbl.setStyleSheet(
                f"background-color: {stage_bg}; color: {stage_color}; "
                f"border: 1px solid {stage_color}; border-radius: 12px; "
                f"padding: 2px 10px; font-size: 12px;"
            )
            self._meta_layout.addWidget(stage_lbl)

        self._meta_layout.addStretch()

        # 摘要
        summary = str(data.get("summary", "")).strip()
        self._summary_title.setVisible(bool(summary))
        self._summary_label.setVisible(bool(summary))
        self._summary_label.setText(summary)

        # 分析重点
        analysis = str(data.get("content", "")).strip()
        impact = str(data.get("impact", "")).strip()
        key_points = self._extract_key_points(analysis, impact)
        has_key_points = bool(key_points)
        self._kp_title.setVisible(has_key_points)
        self._kp_content.setVisible(has_key_points)
        if has_key_points:
            self._kp_content.setText("\n".join(f"● {p}" for p in key_points))

        # 标签
        tags = _split_tags(data.get("tags", ""))
        self._clear_layout(self._tags_layout)
        self._tags_title.setVisible(bool(tags))
        self._tags_container.setVisible(bool(tags))
        for tag in tags:
            btn = QPushButton(tag)
            btn.setObjectName("TagChip")
            btn.setStyleSheet(
                "background-color: #EFF6FF; color: #2563EB; border: 1px solid #2563EB; "
                "border-radius: 14px; padding: 4px 12px; font-size: 12px;"
            )
            btn.clicked.connect(lambda checked=False, t=tag: self.tag_clicked.emit(t))
            self._tags_layout.addWidget(btn)
        self._tags_layout.addStretch()

        # 完整分析
        has_analysis = bool(analysis)
        self._analysis_title.setVisible(has_analysis)
        self._analysis_toggle.setVisible(has_analysis)
        if has_analysis:
            self._analysis_label.setText(analysis)
            if not self._analysis_expanded:
                self._analysis_label.setVisible(False)
                self._analysis_toggle.setText("展开查看 ∨")

    def _extract_key_points(self, analysis: str, impact: str) -> list[str]:
        """从 analysis / impact 中提取关键要点。"""
        points: list[str] = []

        # 尝试从 analysis 中提取 bullet points
        if analysis:
            for line in analysis.split("\n"):
                line = line.strip()
                if not line:
                    continue
                # 匹配 ●、•、-、* 开头的行
                if line.startswith(("●", "•", "-", "*", "·")):
                    cleaned = line.lstrip("●•-*· ").strip()
                    if cleaned:
                        points.append(cleaned)
                # 匹配 "xxx：" 或 "xxx:" 格式
                elif "：" in line or ":" in line:
                    parts = line.split("：", 1) if "：" in line else line.split(":", 1)
                    if len(parts) == 2 and len(parts[0].strip()) < 20:
                        points.append(line)

        # 如果没有 bullet points，尝试从 impact 提取
        if not points and impact:
            for line in impact.split("\n"):
                line = line.strip()
                if line:
                    points.append(line)

        # 如果还是没有，取 analysis 前3行
        if not points and analysis:
            lines = [l.strip() for l in analysis.split("\n") if l.strip()]
            points = lines[:3]

        return points[:6]  # 最多6条

    def show_empty(self) -> None:
        self._title_label.setText("暂无选中的情报")
        self._clear_layout(self._meta_layout)
        self._summary_title.setVisible(False)
        self._summary_label.setVisible(False)
        self._kp_title.setVisible(False)
        self._kp_content.setVisible(False)
        self._tags_title.setVisible(False)
        self._tags_container.setVisible(False)
        self._analysis_title.setVisible(False)
        self._analysis_toggle.setVisible(False)
        self._analysis_label.setVisible(False)

    @staticmethod
    def _clear_layout(layout: QHBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()


# ──────────────────────────────────────────────
# KpiCardWidget
# ──────────────────────────────────────────────
class KpiCardWidget(QWidget):
    """单个 KPI 卡片（统一高度、圆角、内边距）。"""

    def __init__(self, title: str, icon: str = "📊", icon_color: str = "#2563EB", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("KpiCard")
        # KPI 卡片在数据异步返回后动态创建；显式开启样式背景，
        # 让已有 QWidget#KpiCard QSS 在运行时也绘制白底、边框与圆角。
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(100)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 12)
        layout.setSpacing(6)

        # 图标行（小图标 + 标题）
        header = QHBoxLayout()
        header.setSpacing(6)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet(
            f"color: {icon_color}; font-size: 18px; background-color: transparent;"
        )
        header.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setObjectName("KpiTitle")
        title_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        title_label.setStyleSheet("color: #64748B; font-size: 13px; font-weight: 500; background-color: transparent;")
        header.addWidget(title_label)
        header.addStretch()
        layout.addLayout(header)

        # 数值（视觉主体）
        self._value_label = QLabel("--")
        self._value_label.setObjectName("KpiValue")
        self._value_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self._value_label.setStyleSheet(
            "color: #1E293B; font-size: 30px; font-weight: 700; background-color: transparent;"
        )
        self._value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(self._value_label)

        # 副文本（绿/红/灰）
        self._sub_label = QLabel("")
        self._sub_label.setObjectName("KpiSub")
        self._sub_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self._sub_label.setStyleSheet(
            "color: #10B981; font-size: 12px; background-color: transparent;"
        )
        self._sub_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(self._sub_label)

    def set_value(self, value: str) -> None:
        self._value_label.setText(value)

    def set_sub(self, sub: str) -> None:
        self._sub_label.setText(sub)
        # 根据文本中的箭头微调颜色：↑ → 绿色，↓ → 红色，其它 → 灰色
        if "↑" in sub:
            color = "#10B981"
        elif "↓" in sub:
            color = "#EF4444"
        else:
            color = "#64748B"
        self._sub_label.setStyleSheet(
            f"color: {color}; font-size: 12px; background-color: transparent;"
        )


# ──────────────────────────────────────────────
# StageDonutChart
# ──────────────────────────────────────────────
class StageDonutChart(QWidget):
    """阶段分布环形图（QPainter 自绘，保持1:1正圆）。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data: dict[str, int] = {}
        self.setMinimumSize(180, 180)
        # 使用Fixed宽度，Expanding高度，让父容器控制宽度
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_data(self, data: dict[str, int]) -> None:
        self._data = data
        self.update()

    def sizeHint(self):
        """返回正方形尺寸建议。"""
        return QSize(180, 180)

    def paintEvent(self, event) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        painter.fillRect(rect, QColor(CARD_BG))

        total = sum(self._data.values())
        if total == 0:
            painter.setPen(QColor(TEXT_MUTED))
            painter.drawText(rect, Qt.AlignCenter, "暂无数据")
            return

        # 保持1:1正圆：取宽高最小值作为直径
        diameter = min(rect.width(), rect.height())
        margin = 10
        circle_size = diameter - margin * 2
        
        # 居中绘制
        x_offset = (rect.width() - circle_size) // 2
        y_offset = (rect.height() - circle_size) // 2
        outer_rect = rect.adjusted(x_offset, y_offset, -x_offset, -y_offset)
        
        # 内圆（环形）
        inner_ratio = 0.6
        inner_size = int(circle_size * inner_ratio)
        inner_offset = (circle_size - inner_size) // 2
        inner_rect = outer_rect.adjusted(inner_offset, inner_offset, -inner_offset, -inner_offset)

        start_angle = 90 * 16  # 从12点方向开始
        for stage, count in self._data.items():
            if count <= 0:
                continue
            span = int(count / total * 360 * 16)
            color = QColor(_stage_color(stage))
            painter.setBrush(color)
            painter.setPen(QPen(QColor(CARD_BG), 2))
            painter.drawPie(outer_rect, start_angle, span)
            start_angle += span

        # 中心文字
        painter.setPen(QColor(TEXT_PRIMARY))
        font = QFont("Microsoft YaHei", 10, QFont.Bold)
        painter.setFont(font)
        painter.drawText(inner_rect, Qt.AlignCenter, f"共 {total} 条")

    def get_legend_items(self) -> list[tuple[str, int, float]]:
        """返回 [(阶段名, 数量, 百分比)] 用于图例。"""
        total = sum(self._data.values())
        if total == 0:
            return []
        return [
            (stage, count, count / total * 100)
            for stage, count in self._data.items()
            if count > 0
        ]


# ──────────────────────────────────────────────
# TagBarWidget
# ──────────────────────────────────────────────
class TagBarWidget(QWidget):
    """标签进度条（横向条形图）。"""

    tag_clicked = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)

    def set_data(self, tag_counts: Counter[str], max_items: int = 10) -> None:
        # 清除旧内容
        while self._layout.count():
            item = self._layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not tag_counts:
            empty = QLabel("暂无标签数据")
            empty.setObjectName("EmptyStateSub")
            empty.setAlignment(Qt.AlignCenter)
            self._layout.addWidget(empty)
            return

        max_count = max(tag_counts.values())
        total = sum(tag_counts.values())

        for tag, count in tag_counts.most_common(max_items):
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 2, 0, 2)
            row_layout.setSpacing(8)

            tag_btn = QPushButton(tag)
            tag_btn.setObjectName("TagLabel")
            tag_btn.clicked.connect(lambda checked=False, t=tag: self.tag_clicked.emit(t))
            tag_btn.setFixedWidth(80)
            tag_btn.setStyleSheet(
                "background-color: transparent; color: #1E293B; border: none; "
                "text-align: left; font-size: 12px; padding: 0;"
            )
            row_layout.addWidget(tag_btn)

            bar_bg = QFrame()
            bar_bg.setObjectName("TagBarBg")
            bar_bg.setStyleSheet("background-color: #F1F5F9; border-radius: 4px; min-height: 8px;")
            bar_bg_layout = QHBoxLayout(bar_bg)
            bar_bg_layout.setContentsMargins(0, 0, 0, 0)

            bar_fill = QFrame()
            bar_fill.setObjectName("TagBarFill")
            width_ratio = count / max_count if max_count > 0 else 0
            bar_fill.setStyleSheet(
                f"background-color: #2563EB; border-radius: 4px; min-height: 8px; "
                f"min-width: {int(60 * width_ratio)}px;"
            )
            bar_bg_layout.addWidget(bar_fill)

            row_layout.addWidget(bar_bg, stretch=1)

            count_lbl = QLabel(f"{count}")
            count_lbl.setObjectName("TagCount")
            count_lbl.setFixedWidth(30)
            count_lbl.setAlignment(Qt.AlignRight)
            count_lbl.setStyleSheet("color: #64748B; font-size: 12px;")
            row_layout.addWidget(count_lbl)

            self._layout.addWidget(row)

        # 查看更多链接
        more_link = QPushButton("查看更多 ›")
        more_link.setObjectName("MoreLink")
        more_link.setStyleSheet(
            "background-color: transparent; color: #2563EB; border: none; "
            "font-size: 12px; padding: 4px 0;"
        )
        more_link_layout = QHBoxLayout()
        more_link_layout.addStretch()
        more_link_layout.addWidget(more_link)
        more_link_layout.addStretch()
        more_widget = QWidget()
        more_widget.setLayout(more_link_layout)
        self._layout.addWidget(more_widget)

        self._layout.addStretch()


# ──────────────────────────────────────────────
# OverviewPanel
# ──────────────────────────────────────────────
class OverviewPanel(QWidget):
    """底部情报概览面板：KPI + 评分分布 + 阶段分布 + 热门标签。"""

    tag_clicked = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        # 参考图中底部统计区保持稳定高度；这样顶部双卡与底部三列的
        # 垂直比例不会随内容的 sizeHint 漂移。
        self.setFixedHeight(318)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 目标图的底部采用 2:1:1 三列：左列承载概览标题、四张 KPI
        # 与评分分布；阶段与热门标签各自是一张独立的一级 Card。
        columns = QHBoxLayout()
        columns.setContentsMargins(0, 0, 0, 0)
        columns.setSpacing(12)

        overview_column = QWidget()
        overview_column.setObjectName("OverviewGroup")
        overview_layout = QVBoxLayout(overview_column)
        overview_layout.setContentsMargins(16, 14, 16, 14)
        overview_layout.setSpacing(12)

        # 左列标题行
        header = QHBoxLayout()
        title = QLabel("情报概览")
        title.setObjectName("OverviewTitle")
        title.setStyleSheet("color: #1E293B; font-size: 15px; font-weight: bold;")
        header.addWidget(title)

        subtitle = QLabel("（基于最近 7 天）")
        subtitle.setObjectName("OverviewSubtitle")
        subtitle.setStyleSheet("color: #64748B; font-size: 13px;")
        header.addWidget(subtitle)

        header.addStretch()
        overview_layout.addLayout(header)

        # KPI 行（4张卡片）
        self._kpi_row = QWidget()
        kpi_layout = QHBoxLayout(self._kpi_row)
        kpi_layout.setContentsMargins(0, 0, 0, 0)
        kpi_layout.setSpacing(12)
        overview_layout.addWidget(self._kpi_row)

        # 左列下方：评分分布（外层已是 OverviewGroup 卡，此处仅作卡内分区）
        score_group = QWidget()
        score_layout = QVBoxLayout(score_group)
        score_layout.setContentsMargins(0, 0, 0, 0)
        score_layout.setSpacing(10)
        score_title = QLabel("评分分布")
        score_title.setObjectName("OverviewGroupTitle")
        score_title.setStyleSheet("color: #1E293B; font-size: 14px; font-weight: bold;")
        score_layout.addWidget(score_title)
        self._score_bars_layout = QVBoxLayout()
        self._score_bars_layout.setSpacing(10)
        # 让进度条布局吸收剩余空间，避免"评分分布"标题被垂直拉伸（同 tag_bar 修复）
        score_layout.addLayout(self._score_bars_layout, stretch=1)
        overview_layout.addWidget(score_group, stretch=1)
        columns.addWidget(overview_column, stretch=2)

        # 中列：阶段分布 Card（环图和图例水平排列，避免拉成长椭圆）
        stage_group = QWidget()
        stage_group.setObjectName("OverviewGroup")
        stage_layout = QVBoxLayout(stage_group)
        stage_layout.setContentsMargins(16, 14, 16, 14)
        stage_layout.setSpacing(10)
        stage_title = QLabel("阶段分布")
        stage_title.setObjectName("OverviewGroupTitle")
        stage_title.setStyleSheet("color: #1E293B; font-size: 14px; font-weight: bold;")
        stage_layout.addWidget(stage_title)

        stage_content = QWidget()
        stage_content_layout = QHBoxLayout(stage_content)
        stage_content_layout.setContentsMargins(0, 0, 0, 0)
        stage_content_layout.setSpacing(10)
        self._donut_chart = StageDonutChart()
        self._donut_chart.setFixedSize(166, 166)
        stage_content_layout.addWidget(self._donut_chart, alignment=Qt.AlignVCenter)
        self._legend_container = QWidget()
        self._legend_layout = QVBoxLayout(self._legend_container)
        self._legend_layout.setContentsMargins(0, 0, 0, 0)
        self._legend_layout.setSpacing(6)
        stage_content_layout.addWidget(self._legend_container, stretch=1)
        stage_layout.addWidget(stage_content, stretch=1)
        columns.addWidget(stage_group, stretch=1)

        # 右列：热门标签 Card
        tag_group = QWidget()
        tag_group.setObjectName("OverviewGroup")
        tag_layout = QVBoxLayout(tag_group)
        tag_layout.setContentsMargins(16, 14, 16, 14)
        tag_layout.setSpacing(6)
        tag_title = QLabel("热门标签 Top 10")
        tag_title.setObjectName("OverviewGroupTitle")
        tag_title.setStyleSheet("color: #1E293B; font-size: 14px; font-weight: bold;")
        tag_layout.addWidget(tag_title)
        self._tag_bar = TagBarWidget()
        self._tag_bar.tag_clicked.connect(self.tag_clicked.emit)
        tag_layout.addWidget(self._tag_bar, stretch=1)
        columns.addWidget(tag_group, stretch=1)

        root.addLayout(columns, stretch=1)

    def set_kpis(
        self,
        total: int,
        avg_score: float,
        urgent_ratio: float,
        time_ratio: float,
        subs: tuple[str, str, str, str] | None = None,
    ) -> None:
        """设置 4 个 KPI 数据，对应设计图：情报数/平均评分/紧迫占比/时间比。

        subs: 4 个副文本（绿/红/灰），保持与设计图一致视觉风格
        """
        if subs is None:
            subs = ("", "", "", "")

        # 清除旧 KPI
        while self._kpi_row.layout().count():
            item = self._kpi_row.layout().takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        kpis = [
            ("情报数", "📊", str(total), "#2563EB", subs[0]),
            ("平均评分", "📈", f"{avg_score:.1f}", "#10B981", subs[1]),
            ("紧迫占比", "🎯", f"{urgent_ratio:.1f}%", "#8B5CF6", subs[2]),
            ("时间比", "🕐", f"{time_ratio:.1f}%", "#F59E0B", subs[3]),
        ]
        for title, icon, value, color, sub in kpis:
            card = KpiCardWidget(title, icon, color)
            card.set_value(value)
            if sub:
                card.set_sub(sub)
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self._kpi_row.layout().addWidget(card, stretch=1)

    def set_score_distribution(self, counts: dict[str, int], total: int) -> None:
        # 清除旧 bars
        while self._score_bars_layout.count():
            item = self._score_bars_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
            elif item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    cw = child.widget()
                    if cw:
                        cw.deleteLater()

        labels_map = {
            "high": ("高分 (≥80)", "#10B981"),
            "medium": ("中等 (50-79)", "#2563EB"),
            "low": ("低分 (<50)", "#F59E0B"),
        }
        max_count = max(counts.values()) if counts else 1

        for key, (label, color) in labels_map.items():
            count = counts.get(key, 0)
            percent = (count / total * 100) if total else 0

            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 2, 0, 2)
            row_layout.setSpacing(8)

            name = QLabel(label)
            name.setObjectName("ScoreLabel")
            name.setFixedWidth(100)
            name.setStyleSheet("color: #64748B; font-size: 12px;")
            row_layout.addWidget(name)

            bar_bg = QFrame()
            bar_bg.setObjectName("TagBarBg")
            bar_bg.setStyleSheet("background-color: #F1F5F9; border-radius: 4px; min-height: 8px;")
            bar_bg_layout = QHBoxLayout(bar_bg)
            bar_bg_layout.setContentsMargins(0, 0, 0, 0)
            bar_fill = QFrame()
            bar_fill.setObjectName("TagBarFill")
            width_ratio = count / max_count if max_count > 0 else 0
            bar_fill.setStyleSheet(
                f"background-color: {color}; border-radius: 4px; min-height: 8px; "
                f"min-width: {int(60 * width_ratio)}px;"
            )
            bar_bg_layout.addWidget(bar_fill)
            row_layout.addWidget(bar_bg, stretch=1)

            info = QLabel(f"{count} 条 ({percent:.1f}%)")
            info.setObjectName("TagCount")
            info.setFixedWidth(120)
            info.setAlignment(Qt.AlignRight)
            info.setStyleSheet("color: #64748B; font-size: 12px;")
            row_layout.addWidget(info)

            self._score_bars_layout.addWidget(row)

    def set_stage_distribution(self, data: dict[str, int]) -> None:
        self._donut_chart.set_data(data)

        # 更新图例
        while self._legend_layout.count():
            item = self._legend_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        total = sum(data.values())
        for stage, count in data.items():
            if count <= 0:
                continue
            percent = count / total * 100 if total else 0
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 2, 0, 2)
            row_layout.setSpacing(6)

            dot = QFrame()
            dot.setObjectName("LegendDot")
            dot.setStyleSheet(f"background-color: {_stage_color(stage)}; border-radius: 5px;")
            dot.setFixedSize(10, 10)
            row_layout.addWidget(dot)

            name = QLabel(stage)
            name.setObjectName("LegendLabel")
            name.setStyleSheet("color: #1E293B; font-size: 12px;")
            row_layout.addWidget(name)

            count_lbl = QLabel(f"{count} ({percent:.1f}%)")
            count_lbl.setObjectName("LegendCount")
            count_lbl.setStyleSheet("color: #64748B; font-size: 12px;")
            row_layout.addWidget(count_lbl)
            row_layout.addStretch()

            self._legend_layout.addWidget(row)

    def set_top_tags(self, tag_counts: Counter[str]) -> None:
        self._tag_bar.set_data(tag_counts)

    def show_empty(self) -> None:
        """空数据状态。"""
        self.set_kpis(0, 0.0, 0.0, 0.0)
        self.set_score_distribution({"high": 0, "medium": 0, "low": 0}, 0)
        self.set_stage_distribution({})
        self.set_top_tags(Counter())
