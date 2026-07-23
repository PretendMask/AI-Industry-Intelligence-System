"""
AI行业情报监控系统 - 全局样式表 (QSS)
蓝白现代主题 · 统一视觉风格
"""

STYLE_SHEET = """
/* ================================================================
   全局基础样式
   ================================================================ */
QWidget, QFrame, QPushButton, QLineEdit, QTextEdit, QPlainTextEdit,
QTextBrowser, QTableWidget, QListWidget, QTreeWidget, QComboBox,
QSpinBox, QDoubleSpinBox, QDateEdit, QDateTimeEdit {
    font-family: 'Microsoft YaHei', 'PingFang SC', 'Helvetica Neue', sans-serif;
    font-size: 13px;
    color: #1E293B;
}

QWidget {
    background-color: #F5F7FA;
}

/* ================================================================
   导航标签页 - QTabWidget / QTabBar
   ================================================================ */
QTabWidget::pane {
    border: none;
    background-color: transparent;
    top: -1px;
}

QTabBar {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E2E8F0;
    padding: 0 8px;
}

QTabBar::tab {
    background: transparent;
    color: #64748B;
    padding: 10px 20px 8px 20px;
    margin: 6px 2px 0 2px;
    border: none;
    border-bottom: 2.5px solid transparent;
    border-radius: 8px 8px 0 0;
    font-weight: 500;
    font-size: 13px;
}

QTabBar::tab:selected {
    color: #2563EB;
    border-bottom: 2.5px solid #2563EB;
    font-weight: 600;
}

QTabBar::tab:hover:!selected {
    color: #1E293B;
    background-color: #F1F5F9;
    border-radius: 8px 8px 0 0;
}

QTabBar::tab:disabled {
    color: #CBD5E1;
}

QTabBar::tab QLabel {
    margin-left: 6px;
}

/* ================================================================
   按钮 - QPushButton
   ================================================================ */
QPushButton {
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #1D4ED8;
}

QPushButton:pressed {
    background-color: #1E40AF;
}

QPushButton:disabled {
    background-color: #CBD5E1;
    color: #94A3B8;
}

/* PrimaryBtn: 主操作按钮 */
QPushButton#PrimaryBtn {
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 500;
    font-size: 13px;
}

QPushButton#PrimaryBtn:hover {
    background-color: #1D4ED8;
}

QPushButton#PrimaryBtn:pressed {
    background-color: #1E40AF;
}

QPushButton#PrimaryBtn:disabled {
    background-color: #CBD5E1;
    color: #94A3B8;
}

/* SuccessBtn: 成功按钮 */
QPushButton#SuccessBtn {
    background-color: #10B981;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 500;
    font-size: 13px;
}

QPushButton#SuccessBtn:hover {
    background-color: #059669;
}

QPushButton#SuccessBtn:pressed {
    background-color: #047857;
}

QPushButton#SuccessBtn:disabled {
    background-color: #A7F3D0;
    color: #ECFDF5;
}

/* DangerButton: 危险操作按钮 */
QPushButton#DangerButton {
    background-color: #EF4444;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 500;
    font-size: 13px;
}

QPushButton#DangerButton:hover {
    background-color: #DC2626;
}

QPushButton#DangerButton:pressed {
    background-color: #B91C1C;
}

QPushButton#DangerButton:disabled {
    background-color: #FCA5A5;
    color: #FEE2E2;
}

/* GhostButton: 幽灵/文字按钮 */
QPushButton#GhostButton {
    background-color: transparent;
    color: #64748B;
    border: none;
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: 400;
}

QPushButton#GhostButton:hover {
    background-color: #F1F5F9;
    color: #1E293B;
}

QPushButton#GhostButton:pressed {
    background-color: #E2E8F0;
}

/* SecondaryBtn: 次要按钮 */
QPushButton#SecondaryBtn {
    background-color: #F1F5F9;
    color: #475569;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 500;
}

QPushButton#SecondaryBtn:hover {
    background-color: #E2E8F0;
    color: #1E293B;
}

QPushButton#SecondaryBtn:pressed {
    background-color: #CBD5E1;
}

QPushButton#SecondaryBtn:disabled {
    background-color: #F8FAFC;
    color: #CBD5E1;
}

/* OutlineButton: 轮廓按钮 */
QPushButton#OutlineButton {
    background-color: transparent;
    color: #2563EB;
    border: 1.5px solid #2563EB;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 500;
}

QPushButton#OutlineButton:hover {
    background-color: #EFF6FF;
}

QPushButton#OutlineButton:pressed {
    background-color: #DBEAFE;
}

/* FlatSearch: 扁平搜索按钮 */
QPushButton#FlatSearch {
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
    border-radius: 0 6px 6px 0;
    padding: 7px 14px;
    font-weight: 500;
}

QPushButton#FlatSearch:hover {
    background-color: #1D4ED8;
}

/* InlineAction: 行内操作按钮 */
QPushButton#InlineAction {
    background-color: transparent;
    color: #2563EB;
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}

QPushButton#InlineAction:hover {
    background-color: #EFF6FF;
}

QPushButton#InlineAction:pressed {
    background-color: #DBEAFE;
}

/* DarkDanger: 深色背景下的危险按钮 */
QPushButton#DarkDanger {
    background-color: #EF4444;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 500;
}

QPushButton#DarkDanger:hover {
    background-color: #DC2626;
}

QPushButton#DarkDanger:pressed {
    background-color: #B91C1C;
}

QPushButton#DarkDanger:disabled {
    background-color: #FCA5A5;
}

/* ================================================================
   输入控件 - QLineEdit / QTextEdit / QPlainTextEdit / QTextBrowser
   ================================================================ */
QLineEdit, QTextEdit, QPlainTextEdit, QTextBrowser {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 8px 12px;
    color: #1E293B;
    selection-background-color: #DBEAFE;
    selection-color: #1E293B;
}

QLineEdit:focus, QTextEdit:focus,
QPlainTextEdit:focus, QTextBrowser:focus {
    border: 1.5px solid #2563EB;
}

QLineEdit:disabled, QTextEdit:disabled,
QPlainTextEdit:disabled, QTextBrowser:disabled {
    background-color: #F8FAFC;
    color: #94A3B8;
}

QLineEdit[readOnly="true"], QTextEdit[readOnly="true"],
QPlainTextEdit[readOnly="true"] {
    background-color: #F8FAFC;
    color: #1E293B;
}

/* 日志输出专用 - 保持明亮可读 */
QPlainTextEdit#logOutput {
    background-color: #FAFBFC;
    color: #1E293B;
    font-family: 'Consolas', 'Microsoft YaHei', 'PingFang SC', monospace;
    font-size: 12px;
}

/* PromptInput: AI 补充说明输入框 */
QTextEdit#PromptInput {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 10px 12px;
    min-height: 60px;
}

QTextEdit#PromptInput:focus {
    border: 1.5px solid #2563EB;
}

/* LogConsole: 爬取日志控制台 */
QTextBrowser#LogConsole {
    background-color: #F8FAFC;
    color: #1E293B;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 10px 12px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    selection-background-color: #DBEAFE;
    selection-color: #1E293B;
}

/* OutputConsole: AI 分析输出控制台 */
QPlainTextEdit#OutputConsole {
    background-color: #F8FAFC;
    color: #1E293B;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 10px 12px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
}

/* ================================================================
   表格 - QTableWidget
   ================================================================ */
QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    gridline-color: #F1F5F9;
    selection-background-color: #DBEAFE;
    selection-color: #1E293B;
    outline: none;
}

QTableWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid #F8FAFC;
}

QTableWidget::item:selected {
    background-color: #DBEAFE;
    color: #1E293B;
}

QTableWidget::item:hover {
    background-color: #F1F5F9;
}

QHeaderView::section {
    background-color: #F8FAFC;
    border: none;
    border-bottom: 2px solid #E2E8F0;
    padding: 10px 12px;
    font-weight: 600;
    font-size: 12px;
    color: #475569;
}

QHeaderView::section:hover {
    background-color: #F1F5F9;
}

QHeaderView::section:horizontal {
    border-right: 1px solid #F1F5F9;
}

QTableCornerButton::section {
    background-color: #F8FAFC;
    border: none;
    border-bottom: 2px solid #E2E8F0;
}

/* ================================================================
   卡片/面板样式
   ================================================================ */

/* TerminalCard: 卡片面板 */
QGroupBox#TerminalCard {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    margin-top: 0;
    padding: 0;
    font-weight: 600;
    color: #1E293B;
}

QGroupBox#TerminalCard::title {
    subcontrol-origin: margin;
    padding: 0;
    color: transparent;
}

/* CardHeader: 卡片头部 */
QWidget#CardHeader {
    background-color: #F8FAFC;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    padding: 10px 16px;
}

/* CardTitle: 卡片标题 */
QLabel#CardTitle {
    font-size: 15px;
    font-weight: 700;
    color: #1E293B;
    background-color: transparent;
}

/* CardDivider: 卡片头部分割线 */
QWidget#CardDivider {
    background-color: #E2E8F0;
}

/* FilterBar: 筛选工具栏 */
QWidget#FilterBar {
    background-color: #F8FAFC;
    padding: 8px 16px;
}

/* DeleteBar: 删除管理工具栏 */
QWidget#DeleteBar {
    background-color: #FEF2F2;
    border-radius: 8px;
    padding: 8px 16px;
}

/* ================================================================
   表单项专用样式
   ================================================================ */

/* FieldLabel: 字段标签 */
QLabel#FieldLabel {
    color: #64748B;
    font-size: 12px;
    font-weight: 500;
    background-color: transparent;
}

/* CompactSpin: 紧凑微调框 */
QSpinBox#CompactSpin {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 5px 8px;
    min-width: 70px;
    max-width: 120px;
}

QSpinBox#CompactSpin:focus {
    border-color: #2563EB;
}

/* CompactDate: 紧凑日期编辑 */
QDateEdit#CompactDate {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 5px 8px;
    min-width: 120px;
    max-width: 150px;
}

QDateEdit#CompactDate:focus {
    border-color: #2563EB;
}

/* FilterCombo: 筛选下拉框 */
QComboBox#FilterCombo {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 5px 28px 5px 10px;
    min-width: 100px;
    max-width: 160px;
}

QComboBox#FilterCombo:hover {
    border-color: #CBD5E1;
}

QComboBox#FilterCombo:focus {
    border-color: #2563EB;
}

/* InlineCheck: 行内复选框 */
QCheckBox#InlineCheck {
    spacing: 6px;
    color: #475569;
    font-size: 12px;
}

/* StatusChip: 状态指示标签 */
QLabel#StatusChip {
    color: #64748B;
    font-size: 12px;
    font-weight: 500;
    padding: 2px 8px;
    background-color: transparent;
}

/* StatusPill: 状态说明标签 */
QLabel#StatusPill {
    color: #64748B;
    font-size: 12px;
    padding: 6px 12px;
    background-color: #F1F5F9;
    border-radius: 6px;
}

/* FooterHint: 表格底部提示 */
QLabel#FooterHint {
    color: #94A3B8;
    font-size: 12px;
}

/* KpiValue: 仪表盘 KPI 数值 */
QLabel#KpiValue {
    font-size: 28px;
    font-weight: 700;
    color: #1E293B;
    background-color: transparent;
}

/* DialogTitle: 对话框标题 */
QLabel#DialogTitle {
    font-size: 16px;
    font-weight: 700;
    color: #1E293B;
}

/* HeaderDotGreen: 绿色状态点 */
QLabel#HeaderDotGreen {
    color: #10B981;
    font-size: 14px;
    font-weight: bold;
    background-color: transparent;
}

/* HeaderDotBlue: 蓝色状态点 */
QLabel#HeaderDotBlue {
    color: #2563EB;
    font-size: 14px;
    font-weight: bold;
    background-color: transparent;
}

/* HeaderDotPurple: 紫色状态点 */
QLabel#HeaderDotPurple {
    color: #7C3AED;
    font-size: 14px;
    font-weight: bold;
    background-color: transparent;
}

/* VSep: 垂直分割线 */
QWidget#VSep {
    background-color: #E2E8F0;
}

/* ================================================================
   滚动条
   ================================================================ */
QScrollBar:vertical {
    background: #F1F5F9;
    width: 8px;
    border-radius: 4px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #CBD5E1;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #94A3B8;
}

QScrollBar::handle:vertical:pressed {
    background: #64748B;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
    background: none;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

QScrollBar:horizontal {
    background: #F1F5F9;
    height: 8px;
    border-radius: 4px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: #CBD5E1;
    border-radius: 4px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background: #94A3B8;
}

QScrollBar::handle:horizontal:pressed {
    background: #64748B;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
    background: none;
}

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}

/* ================================================================
   分组框 - QGroupBox
   ================================================================ */
QGroupBox {
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    margin-top: 16px;
    padding: 18px 16px 16px 16px;
    font-weight: 600;
    font-size: 13px;
    color: #1E293B;
    background-color: #FFFFFF;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
    color: #1E293B;
}

/* ================================================================
   下拉框 - QComboBox
   ================================================================ */
QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 8px 32px 8px 12px;
    color: #1E293B;
}

QComboBox:hover {
    border-color: #CBD5E1;
}

QComboBox:focus {
    border-color: #2563EB;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border-left: 1px solid #F1F5F9;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    selection-background-color: #DBEAFE;
    selection-color: #1E293B;
    padding: 4px;
    outline: none;
}

QComboBox:disabled {
    background-color: #F8FAFC;
    color: #94A3B8;
}

/* ================================================================
   进度条 - QProgressBar
   ================================================================ */
QProgressBar {
    background-color: #E2E8F0;
    border: none;
    border-radius: 6px;
    height: 8px;
    text-align: center;
    font-size: 11px;
    color: transparent;
}

QProgressBar::chunk {
    background-color: #2563EB;
    border-radius: 6px;
}

/* ================================================================
   复选框 / 单选框 - QCheckBox / QRadioButton
   ================================================================ */
QCheckBox, QRadioButton {
    spacing: 8px;
    color: #1E293B;
    background-color: transparent;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1.5px solid #CBD5E1;
    border-radius: 4px;
    background-color: #FFFFFF;
}

QCheckBox::indicator:hover {
    border-color: #2563EB;
    background-color: #EFF6FF;
}

QCheckBox::indicator:checked {
    background-color: #2563EB;
    border-color: #2563EB;
    image: url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><path fill='none' stroke='white' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round' d='M3 8l3.5 3.5L13 5'/></svg>");
}

QCheckBox::indicator:disabled {
    background-color: #F1F5F9;
    border-color: #E2E8F0;
}

QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border: 1.5px solid #CBD5E1;
    border-radius: 9px;
    background-color: #FFFFFF;
}

QRadioButton::indicator:hover {
    border-color: #2563EB;
}

QRadioButton::indicator:checked {
    background-color: #2563EB;
    border-color: #2563EB;
}

QRadioButton::indicator:disabled {
    background-color: #F1F5F9;
    border-color: #E2E8F0;
}

/* ================================================================
   标签 - QLabel
   ================================================================ */
QLabel {
    color: #1E293B;
    background-color: transparent;
}

/* ================================================================
   菜单 - QMenuBar / QMenu
   ================================================================ */
QMenuBar {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E2E8F0;
    padding: 2px 0;
}

QMenuBar::item {
    padding: 6px 14px;
    background-color: transparent;
    color: #1E293B;
    border-radius: 4px;
    margin: 2px 2px;
}

QMenuBar::item:selected {
    background-color: #EFF6FF;
    color: #2563EB;
}

QMenu {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 4px;
}

QMenu::item {
    padding: 8px 28px 8px 16px;
    border-radius: 4px;
    color: #1E293B;
}

QMenu::item:selected {
    background-color: #EFF6FF;
    color: #2563EB;
}

QMenu::item:disabled {
    color: #CBD5E1;
}

QMenu::separator {
    height: 1px;
    background-color: #E2E8F0;
    margin: 4px 8px;
}

/* ================================================================
   工具提示 - QToolTip
   ================================================================ */
QToolTip {
    background-color: #1E293B;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12px;
}

/* ================================================================
   状态栏 - QStatusBar
   ================================================================ */
QStatusBar {
    background-color: #FFFFFF;
    border-top: 1px solid #E2E8F0;
    color: #64748B;
    font-size: 12px;
    padding: 2px 8px;
}

QStatusBar::item {
    border: none;
}

/* ================================================================
   列表 - QListWidget
   ================================================================ */
QListWidget {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 4px;
    outline: none;
}

QListWidget::item {
    padding: 8px 12px;
    border-radius: 4px;
    color: #1E293B;
    border-bottom: 1px solid #F8FAFC;
}

QListWidget::item:selected {
    background-color: #DBEAFE;
    color: #2563EB;
}

QListWidget::item:hover:!selected {
    background-color: #F1F5F9;
}

/* ================================================================
   树形控件 - QTreeWidget / QTreeView
   ================================================================ */
QTreeWidget, QTreeView {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 4px;
    outline: none;
}

QTreeWidget::item, QTreeView::item {
    padding: 6px 8px;
    border-radius: 3px;
    color: #1E293B;
}

QTreeWidget::item:selected, QTreeView::item:selected {
    background-color: #DBEAFE;
    color: #2563EB;
}

QTreeWidget::item:hover:!selected, QTreeView::item:hover:!selected {
    background-color: #F1F5F9;
}

QTreeWidget::branch:has-children:!has-siblings:closed,
QTreeWidget::branch:closed:has-children:has-siblings {
    border-image: none;
}

QTreeWidget::branch:open:has-children:!has-siblings,
QTreeWidget::branch:open:has-children:has-siblings {
    border-image: none;
}

/* ================================================================
   微调框 - QSpinBox / QDoubleSpinBox
   ================================================================ */
QSpinBox, QDoubleSpinBox {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 7px 10px;
    color: #1E293B;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #2563EB;
}

QSpinBox:disabled, QDoubleSpinBox:disabled {
    background-color: #F8FAFC;
    color: #94A3B8;
}

QSpinBox::up-button, QDoubleSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid #F1F5F9;
    border-bottom: 1px solid #F1F5F9;
    border-top-right-radius: 6px;
}

QSpinBox::down-button, QDoubleSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 24px;
    border-left: 1px solid #F1F5F9;
    border-bottom-right-radius: 6px;
}

/* ================================================================
   日期时间控件 - QDateEdit / QDateTimeEdit
   ================================================================ */
QDateEdit, QDateTimeEdit {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 7px 10px;
    color: #1E293B;
}

QDateEdit:focus, QDateTimeEdit:focus {
    border-color: #2563EB;
}

QDateEdit:disabled, QDateTimeEdit:disabled {
    background-color: #F8FAFC;
    color: #94A3B8;
}

QDateEdit::drop-down, QDateTimeEdit::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border-left: 1px solid #F1F5F9;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}

QCalendarWidget {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
}

QCalendarWidget QToolButton {
    color: #1E293B;
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
    font-weight: 600;
}

QCalendarWidget QToolButton:hover {
    background-color: #EFF6FF;
    color: #2563EB;
}

QCalendarWidget QMenu {
    background-color: #FFFFFF;
}

QCalendarWidget QSpinBox {
    border: 1px solid #E2E8F0;
    border-radius: 4px;
}

QCalendarWidget QTableView {
    alternate-background-color: #F8FAFC;
    selection-background-color: #DBEAFE;
    selection-color: #1E293B;
}

/* ================================================================
   滑动条 - QSlider
   ================================================================ */
QSlider::groove:horizontal {
    border: none;
    height: 6px;
    background: #E2E8F0;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #2563EB;
    border: 2px solid #FFFFFF;
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background: #1D4ED8;
    width: 18px;
    height: 18px;
    margin: -7px 0;
    border-radius: 9px;
}

QSlider::sub-page:horizontal {
    background: #2563EB;
    border-radius: 3px;
}

QSlider::groove:vertical {
    border: none;
    width: 6px;
    background: #E2E8F0;
    border-radius: 3px;
}

QSlider::handle:vertical {
    background: #2563EB;
    border: 2px solid #FFFFFF;
    width: 16px;
    height: 16px;
    margin: 0 -6px;
    border-radius: 8px;
}

QSlider::handle:vertical:hover {
    background: #1D4ED8;
}

QSlider::sub-page:vertical {
    background: #2563EB;
    border-radius: 3px;
}

/* ================================================================
   拆分器 - QSplitter
   ================================================================ */
QSplitter::handle {
    background-color: #E2E8F0;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}

QSplitter::handle:hover {
    background-color: #2563EB;
}

/* ================================================================
   工具栏 - QToolBar / QToolButton
   ================================================================ */
QToolBar {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E2E8F0;
    padding: 4px;
    spacing: 4px;
}

QToolButton {
    background-color: transparent;
    border: none;
    border-radius: 6px;
    padding: 6px 10px;
    color: #64748B;
}

QToolButton:hover {
    background-color: #F1F5F9;
    color: #1E293B;
}

QToolButton:pressed {
    background-color: #E2E8F0;
}

QToolButton:checked {
    background-color: #EFF6FF;
    color: #2563EB;
}

/* ================================================================
   对话框 - QDialog
   ================================================================ */
QDialog {
    background-color: #F5F7FA;
}

/* ================================================================
   停靠窗口 - QDockWidget
   ================================================================ */
QDockWidget {
    color: #1E293B;
    titlebar-close-icon: none;
}

QDockWidget::title {
    background-color: #F8FAFC;
    border-bottom: 1px solid #E2E8F0;
    padding: 8px 12px;
    text-align: left;
}
"""

# 兼容 main_window.py 的函数调用方式
def modern_light_qss() -> str:
    """返回亮色主题 QSS 字符串"""
    return STYLE_SHEET
