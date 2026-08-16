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
    padding: 6px 20px 5px 20px;
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

/* DangerIconButton: 表格行内删除图标按钮 */
QPushButton#DangerIconButton {
    background-color: transparent;
    border: none;
    border-radius: 6px;
}

QPushButton#DangerIconButton:hover {
    background-color: #FEF2F2;
}

QPushButton#DangerIconButton:pressed {
    background-color: #FEE2E2;
}

QPushButton#DangerIconButton:disabled {
    background-color: transparent;
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
    alternate-background-color: #FFFFFF;
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

QWidget#CellCenterContainer {
    background-color: transparent;
}

QTableWidget#LogTable QHeaderView::section {
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
    image: url(__CHECK_WHITE_URL__);
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
    min-height: 30px;
    padding: 0 12px;
}

QMenuBar::item {
    padding: 5px 15px;
    background-color: transparent;
    color: #1E293B;
    border-radius: 4px;
    margin: 0 1px;
}

QMenuBar::item:selected {
    background-color: #EFF6FF;
    color: #2563EB;
}

QWidget#HeaderActions {
    background: transparent;
}

QPushButton#HeaderIconButton {
    background: transparent;
    color: #334155;
    border: none;
    border-radius: 5px;
    padding: 4px;
}

QPushButton#HeaderIconButton:hover {
    background-color: #EFF6FF;
}

QLabel#HeaderActionSeparator {
    background-color: #E2E8F0;
    border: none;
}

QPushButton#HeaderUserButton {
    min-height: 28px;
    background: transparent;
    color: #64748B;
    border: none;
    padding: 2px 4px 2px 8px;
    font-size: 12px;
}

QPushButton#HeaderUserButton:hover {
    color: #2563EB;
    background-color: #EFF6FF;
    border-radius: 5px;
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

# 仪表盘专用样式与全局样式分开定义；二者均由 modern_light_qss() 返回。
# 此处不能使用函数 docstring 承载 QSS，否则 Qt 永远不会接收到这部分样式。
DASHBOARD_STYLE_SHEET = """
/* ================================================================
   仪表盘组件 - Dashboard Components
   ================================================================ */

/* -- 情报卡片 -- */
QWidget#IntelligenceCard {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
}

QWidget#IntelligenceCard[selected="true"] {
    background-color: #EFF6FF;
    border: 1px solid #BFDBFE;
}

QWidget#IntelligenceCard:hover {
    background-color: #F8FAFC;
}

QWidget#IntelligenceCard[selected="true"]:hover {
    background-color: #EFF6FF;
}

QFrame#CardIndicator {
    background-color: #2563EB;
    border-radius: 2px;
}

QLabel#CardTitle {
    font-size: 13px;
    font-weight: 600;
    color: #1E293B;
    background-color: transparent;
}

QLabel#CardMeta {
    font-size: 11px;
    color: #64748B;
    background-color: transparent;
}

QLabel#CardSource {
    font-size: 11px;
    color: #475569;
    background-color: transparent;
    font-weight: 500;
}

QLabel#CardScore {
    font-size: 11px;
    color: #2563EB;
    background-color: transparent;
    font-weight: 600;
}

QLabel#CardStage {
    font-size: 11px;
    font-weight: 500;
    padding: 2px 8px;
    border-radius: 4px;
    background-color: #F1F5F9;
    color: #475569;
}

QLabel#CardStage[stage="信息冲击期"] {
    background-color: #DBEAFE;
    color: #1D4ED8;
}

QLabel#CardStage[stage="情绪加速期"] {
    background-color: #D1FAE5;
    color: #047857;
}

QLabel#CardStage[stage="利多兑现期"] {
    background-color: #FEF3C7;
    color: #B45309;
}

QLabel#CardStage[stage="不确定"] {
    background-color: #EDE9FE;
    color: #6D28D9;
}

QLabel#CardArrow {
    color: #CBD5E1;
    background-color: transparent;
}

/* -- 搜索框 -- */
QLineEdit#SearchInput {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 13px;
    color: #1E293B;
}

QLineEdit#SearchInput:focus {
    border: 1.5px solid #2563EB;
}

QLineEdit#SearchInput:disabled {
    background-color: #F8FAFC;
    color: #94A3B8;
}

/* -- 情报详情 -- */
QLabel#DetailTitle {
    font-size: 18px;
    font-weight: 700;
    color: #1E293B;
    background-color: transparent;
    line-height: 1.4;
}

QLabel#DetailMeta {
    font-size: 12px;
    color: #64748B;
    background-color: transparent;
}

QLabel#DetailScore {
    font-size: 13px;
    font-weight: 700;
    color: #2563EB;
    background-color: transparent;
}

QLabel#DetailStage {
    font-size: 12px;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 4px;
    background-color: #FEF3C7;
    color: #B45309;
}

QLabel#DetailStage[stage="信息冲击期"] {
    background-color: #DBEAFE;
    color: #1D4ED8;
}

QLabel#DetailStage[stage="情绪加速期"] {
    background-color: #D1FAE5;
    color: #047857;
}

QLabel#DetailStage[stage="利多兑现期"] {
    background-color: #FEF3C7;
    color: #B45309;
}

QLabel#DetailStage[stage="不确定"] {
    background-color: #EDE9FE;
    color: #6D28D9;
}

QFrame#DetailDivider {
    background-color: #E2E8F0;
}

QLabel#SectionTitle {
    font-size: 14px;
    font-weight: 700;
    color: #1E293B;
    background-color: transparent;
}

QLabel#DetailText {
    font-size: 13px;
    color: #334155;
    background-color: transparent;
    line-height: 1.6;
}

/* -- 原文链接按钮 -- */
QPushButton#LinkButton {
    background-color: transparent;
    color: #2563EB;
    border: 1px solid #BFDBFE;
    border-radius: 4px;
    padding: 3px 10px;
    font-size: 12px;
    font-weight: 500;
}

QPushButton#LinkButton:hover {
    background-color: #EFF6FF;
}

/* -- 标签 Chip -- */
QPushButton#TagChip {
    background-color: #EFF6FF;
    color: #2563EB;
    border: 1px solid #BFDBFE;
    border-radius: 12px;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 500;
}

QPushButton#TagChip:hover {
    background-color: #DBEAFE;
}

QPushButton#TagChip:pressed {
    background-color: #BFDBFE;
}

QPushButton#TagLabel {
    background-color: transparent;
    color: #1E293B;
    border: none;
    font-size: 12px;
    font-weight: 500;
    text-align: left;
    padding: 2px 0;
}

QPushButton#TagLabel:hover {
    color: #2563EB;
}

/* -- 标签进度条 -- */
QFrame#TagBarBg {
    background-color: #F1F5F9;
    border-radius: 4px;
    min-height: 8px;
}

QFrame#TagBarFill {
    background-color: #2563EB;
    border-radius: 4px;
    min-height: 8px;
}

QLabel#TagCount {
    font-size: 12px;
    color: #64748B;
    background-color: transparent;
}

/* -- KPI 卡片 -- */
QWidget#KpiCard {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
}

QWidget#KpiCard:hover {
    border-color: #CBD5E1;
}

QLabel#KpiIcon {
    font-size: 18px;
    background-color: transparent;
}

QLabel#KpiTitle {
    font-size: 12px;
    color: #64748B;
    font-weight: 500;
    background-color: transparent;
}

QLabel#KpiValue {
    font-size: 28px;
    font-weight: 700;
    color: #1E293B;
    background-color: transparent;
}

QLabel#KpiSub {
    font-size: 12px;
    color: #10B981;
    background-color: transparent;
    font-weight: 500;
}

/* -- 仪表盘页脚免责声明 -- */
QLabel#FooterHint {
    color: #94A3B8;
    font-size: 11px;
    background-color: transparent;
    padding: 4px 4px 0 0;
}

/* -- 概览面板 -- */
QLabel#OverviewTitle {
    font-size: 16px;
    font-weight: 700;
    color: #1E293B;
    background-color: transparent;
}

QWidget#OverviewGroup {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
}

QLabel#OverviewGroupTitle {
    font-size: 13px;
    font-weight: 700;
    color: #1E293B;
    background-color: transparent;
}

QLabel#ScoreLabel {
    font-size: 12px;
    color: #475569;
    background-color: transparent;
    font-weight: 500;
}

/* -- 图例 -- */
QFrame#LegendDot {
    border-radius: 5px;
}

QLabel#LegendLabel {
    font-size: 12px;
    color: #475569;
    background-color: transparent;
}

QLabel#LegendCount {
    font-size: 12px;
    color: #64748B;
    background-color: transparent;
}

/* -- 空状态 -- */
QLabel#EmptyStateTitle {
    font-size: 18px;
    font-weight: 700;
    color: #94A3B8;
    background-color: transparent;
    padding: 24px 0 8px 0;
}

QLabel#EmptyStateSub {
    font-size: 13px;
    color: #94A3B8;
    background-color: transparent;
    padding: 0 0 24px 0;
}

/* -- 仪表盘标题 -- */
QLabel#DashSectionTitle {
    font-size: 14px;
    font-weight: 700;
    color: #1E293B;
    background-color: transparent;
}

/* -- 仪表盘一级Card容器 -- */
QWidget#DashCard {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
}

QSplitter#DashboardSplitter::handle {
    background-color: transparent;
}

QSplitter#DashboardSplitter::handle:horizontal {
    width: 12px;
}

QSplitter#MultilateralSplitter::handle {
    background-color: transparent;
}

QSplitter#MultilateralSplitter::handle:horizontal {
    width: 12px;
}

QWidget#DashListBody,
QWidget#DashDetailBody {
    background-color: #FFFFFF;
}

QWidget#PaginationWidget {
    background-color: #FFFFFF;
    border-top: 1px solid #E2E8F0;
}

QLabel#DashHint {
    font-size: 12px;
    color: #64748B;
    background-color: transparent;
}

/* -- 卡片标题行图标刷新按钮（只显示图标） -- */
QPushButton#RefreshIconBtn {
    background-color: transparent;
    color: #64748B;
    border: none;
    border-radius: 6px;
    padding: 0;
}

QPushButton#RefreshIconBtn:hover {
    background-color: #EFF6FF;
}

QPushButton#RefreshIconBtn:pressed {
    background-color: #DBEAFE;
}

QPushButton#RefreshIconBtn:disabled {
    background-color: transparent;
}

/* -- 分页控件 -- */
QWidget#PaginationWidget {
    background-color: #FFFFFF;
    border-top: 1px solid #E2E8F0;
}

QPushButton#PageButton {
    background-color: #FFFFFF;
    color: #2563EB;
    border: 1px solid #E2E8F0;
    border-radius: 4px;
    padding: 0;
    font-size: 14px;
    font-weight: bold;
}

QPushButton#PageButton:hover {
    background-color: #EFF6FF;
    border-color: #2563EB;
}

QPushButton#PageButton:pressed {
    background-color: #DBEAFE;
}

QLabel#PageLabel {
    background-color: #2563EB;
    color: #FFFFFF;
    border-radius: 4px;
    font-size: 12px;
    font-weight: bold;
}

/* -- 收藏按钮 -- */
QPushButton#FavButton {
    background-color: transparent;
    color: #64748B;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 4px 12px;
    font-size: 12px;
}

QPushButton#FavButton:hover {
    color: #2563EB;
    border-color: #2563EB;
    background-color: #EFF6FF;
}

/* -- 卡片圆点 -- */
QLabel#CardDot {
    color: #2563EB;
    font-size: 10px;
    background-color: transparent;
}

/* -- 卡片箭头 -- */
QLabel#CardArrow {
    color: #2563EB;
    font-size: 18px;
    font-weight: bold;
    background-color: transparent;
}

/* -- 概览副标题 -- */
QLabel#OverviewSubtitle {
    color: #64748B;
    font-size: 13px;
    background-color: transparent;
}

/* -- 查看更多链接 -- */
QPushButton#MoreLink {
    background-color: transparent;
    color: #2563EB;
    border: none;
    font-size: 12px;
    text-align: right;
    padding: 4px 0;
}

QPushButton#MoreLink:hover {
    text-decoration: underline;
}

/* ================================================================
   多边分析工作台：与仪表盘/拓扑页共用的轻量数据工作区语言
   ================================================================ */
QWidget#MultilateralPage {
    background-color: #F5F7FA;
}

QLabel#MultilateralPageTitle {
    color: #1E293B;
    font-size: 20px;
    font-weight: 700;
    background: transparent;
}

QLabel#MultilateralPageSubtitle, QLabel#MultilateralUpdated {
    color: #64748B;
    font-size: 12px;
    background: transparent;
}

QLabel#MultilateralSectionLabel {
    color: #1E293B;
    font-size: 13px;
    font-weight: 700;
    background: transparent;
}

QGroupBox#MultilateralCard, QWidget#MultilateralKpiCard {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
}

QGroupBox#MultilateralCard::title {
    subcontrol-origin: margin;
    left: -9999px;
}

QWidget#MultilateralCardHeader {
    background: transparent;
    border: none;
}

QLabel#MultilateralCardTitle {
    color: #1E293B;
    font-size: 14px;
    font-weight: 700;
    background: transparent;
}

QWidget#MultilateralCardTitleRow {
    background-color: #FFFFFF;
}

QWidget#ManualBarList {
    background-color: #FFFFFF;
}

QWidget#ManualBarRow {
    background-color: #FFFFFF;
}

QWidget#MultilateralControlBar {
    background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 7px;
}

QWidget#MultilateralDangerBar {
    background-color: #FFFDFD;
    border: 1px solid #FECACA;
    border-radius: 7px;
}

QPushButton#MultilateralPrimaryButton {
    min-height: 32px;
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 5px 14px;
    font-weight: 600;
}

QPushButton#MultilateralPrimaryButton:hover { background-color: #1D4ED8; }
QPushButton#MultilateralPrimaryButton:disabled { background-color: #93C5FD; color: #EFF6FF; }

QPushButton#MultilateralSecondaryButton {
    min-height: 32px;
    background-color: #FFFFFF;
    color: #2563EB;
    border: 1px solid #BFDBFE;
    border-radius: 6px;
    padding: 5px 12px;
    font-weight: 600;
}

QPushButton#MultilateralSecondaryButton:hover { background-color: #EFF6FF; border-color: #2563EB; }

QPushButton#MultilateralSuccessButton {
    min-height: 32px;
    background-color: #10B981;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 5px 14px;
    font-weight: 600;
}

QPushButton#MultilateralSuccessButton:hover { background-color: #059669; }
QPushButton#MultilateralSuccessButton:disabled { background-color: #86EFAC; color: #F0FDF4; }

QLabel#MultilateralKpiTitle, QLabel#MultilateralKpiDetail, QLabel#ManualFooterHint,
QLabel#ManualOverviewText, QLabel#ManualBarLabel, QLabel#ManualBarValue {
    background: transparent;
    color: #64748B;
    font-size: 11px;
}

QLabel#MultilateralKpiValue {
    background: transparent;
    color: #1E293B;
    font-size: 24px;
    font-weight: 700;
}

QLabel#MultilateralKpiIcon {
    border-radius: 18px;
    min-width: 36px;
    max-width: 36px;
    min-height: 36px;
    max-height: 36px;
    qproperty-alignment: AlignCenter;
    font-size: 18px;
    font-weight: 700;
}

QWidget#CrawlStepRail {
    background-color: #FFFFFF;
}

QWidget#CrawlStepNode {
    background-color: transparent;
    min-width: 48px;
}

QLabel#CrawlStepCircle {
    color: #94A3B8;
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 14px;
    font-size: 13px;
    font-weight: 700;
}

QLabel#CrawlStepCircle[stepState="running"] {
    color: #2563EB;
    border: 1px solid #2563EB;
    background-color: #EFF6FF;
}

QLabel#CrawlStepCircle[stepState="success"] {
    color: #FFFFFF;
    border: 1px solid #2563EB;
    background-color: #2563EB;
}

QLabel#CrawlStepCircle[stepState="failed"] {
    color: #FFFFFF;
    border: 1px solid #EF4444;
    background-color: #EF4444;
}

QLabel#CrawlStep {
    color: #64748B;
    background-color: transparent;
    font-size: 10px;
    padding: 0;
}

QLabel#CrawlStep[stepState="running"], QLabel#CrawlStep[stepState="success"] {
    color: #2563EB;
    font-weight: 700;
}

QLabel#CrawlStep[stepState="failed"] {
    color: #DC2626;
    font-weight: 700;
}

QWidget#CrawlStepConnector {
    background-color: #D9E2F0;
    margin-top: 13px;
}

QLabel#StatusChip {
    color: #64748B;
    background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 5px;
    padding: 4px 8px;
    font-size: 10px;
}

QProgressBar#ManualBarProgress {
    background-color: #EFF6FF;
    border: none;
    border-radius: 3px;
    min-height: 6px;
    max-height: 6px;
}

QProgressBar#ManualBarProgress::chunk {
    border-radius: 3px;
}

/* ================================================================
   设置中心：分类导航、配置卡片及固定操作栏
   ================================================================ */
QWidget#SettingsWorkbench, QWidget#SettingsContent {
    background-color: #F5F7FA;
}

QWidget#SettingsPageHeader {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E2E8F0;
}

QLabel#SettingsPageTitle {
    color: #1E293B;
    background: transparent;
    font-size: 20px;
    font-weight: 700;
}

QLabel#SettingsPageSubtitle, QLabel#SettingsCardSubtitle, QLabel#SettingsHelpText,
QLabel#SettingsFooterHint {
    color: #64748B;
    background: transparent;
    font-size: 12px;
}

QWidget#SettingsNavPanel {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
}

QLabel#SettingsNavTitle {
    color: #1E293B;
    background: transparent;
    font-size: 13px;
    font-weight: 700;
    padding: 0 8px 8px 8px;
}

QPushButton#SettingsNavButton {
    min-height: 34px;
    color: #475569;
    background: transparent;
    border: none;
    border-radius: 6px;
    padding: 0 10px;
    text-align: left;
    font-size: 13px;
}

QPushButton#SettingsNavButton:hover { background-color: #F1F5F9; color: #2563EB; }
QPushButton#SettingsNavButton:checked { background-color: #EFF6FF; color: #2563EB; font-weight: 700; border-left: 3px solid #2563EB; }

QGroupBox#SettingsCard {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
}

QGroupBox#SettingsCard::title { subcontrol-origin: margin; left: -9999px; }

QLabel#SettingsCardTitle {
    color: #1E293B;
    background: transparent;
    font-size: 16px;
    font-weight: 700;
}

QLineEdit#SettingsInput, QComboBox#SettingsInput, QSpinBox#SettingsInput {
    min-height: 34px;
    background-color: #FFFFFF;
    color: #1E293B;
    border: 1px solid #D9E2F0;
    border-radius: 6px;
    padding: 0 10px;
    font-size: 13px;
}

QLineEdit#SettingsInput:focus, QComboBox#SettingsInput:focus, QSpinBox#SettingsInput:focus {
    border-color: #2563EB;
}

QPushButton#SettingsInlineButton {
    min-height: 32px;
    background-color: #FFFFFF;
    color: #2563EB;
    border: 1px solid #BFDBFE;
    border-radius: 6px;
    padding: 4px 12px;
    font-weight: 600;
}

QPushButton#SettingsInlineButton:hover { background-color: #EFF6FF; border-color: #2563EB; }
QPushButton#SettingsInlineButton:disabled { color: #94A3B8; background-color: #F8FAFC; border-color: #E2E8F0; }

QWidget#SettingsConnectionPanel, QWidget#SettingsScheduleCard {
    background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
}

QLabel#SettingsConnectionTitle, QLabel#SettingsScheduleTitle {
    color: #1E293B;
    background: transparent;
    font-size: 13px;
    font-weight: 700;
}

QLabel#SettingsConnectionPending {
    color: #64748B;
    background-color: #F1F5F9;
    border-radius: 8px;
    padding: 3px 8px;
    font-size: 11px;
}

QLabel#SettingsConnectionTesting {
    color: #2563EB;
    background-color: #EFF6FF;
    border-radius: 8px;
    padding: 3px 8px;
    font-size: 11px;
}

QLabel#SettingsConnectionOk {
    color: #059669;
    background-color: #ECFDF5;
    border-radius: 8px;
    padding: 3px 8px;
    font-size: 11px;
}

QLabel#SettingsConnectionFail {
    color: #DC2626;
    background-color: #FEF2F2;
    border-radius: 8px;
    padding: 3px 8px;
    font-size: 11px;
}

QPlainTextEdit#SettingsPathDisplay {
    background-color: #F8FAFC;
    color: #475569;
    border: 1px solid #E2E8F0;
    border-radius: 7px;
    padding: 8px;
    font-family: Consolas, "Microsoft YaHei";
    font-size: 12px;
}

QWidget#SettingsFooter {
    background-color: #FFFFFF;
    border-top: 1px solid #E2E8F0;
}

QLabel#SettingsStatusOk {
    color: #059669;
    background: transparent;
    font-size: 13px;
    font-weight: 700;
}

/* ================================================================
   日志与状态：结构化日志控制台（浅色、紧凑、业务系统风格）
   ================================================================ */
QWidget#LogPageBody { background-color: #F5F7FA; }

QWidget#LogPageHeader {
    background-color: #FFFFFF;
    border-bottom: 1px solid #DCE7F5;
}

QLabel#LogPageTitle {
    color: #1565E8;
    background: transparent;
    font-size: 18px;
    font-weight: 700;
}

QLabel#LogSchedulerStatus, QLabel#LogHeaderMeta {
    color: #475569;
    background: transparent;
    font-size: 12px;
}

QLabel#LogSchedulerStatus { color: #16A34A; font-weight: 600; }

QPushButton#LogHeaderButton {
    min-height: 30px;
    background-color: #FFFFFF;
    color: #334155;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 4px 11px;
    font-size: 12px;
}

QPushButton#LogHeaderButton:hover { color: #2563EB; background-color: #F8FAFC; border-color: #BFDBFE; }

QCheckBox#LogAutoScroll {
    color: #334155;
    background: transparent;
    font-size: 12px;
    spacing: 6px;
}

QCheckBox#LogAutoScroll::indicator {
    width: 32px;
    height: 18px;
    image: url(__SWITCH_OFF_URL__);
}

QCheckBox#LogAutoScroll::indicator:checked { image: url(__SWITCH_ON_URL__); }

/* 日志来源为真实多选控件；选中态使用清晰的蓝底白勾，而非仅边框变色。 */
QWidget#LogSidebar QCheckBox::indicator {
    width: 17px;
    height: 17px;
    border: 1.5px solid #94A3B8;
    border-radius: 4px;
    background-color: #FFFFFF;
}

QWidget#LogSidebar QCheckBox::indicator:hover { border-color: #2563EB; background-color: #EFF6FF; }
QWidget#LogSidebar QCheckBox::indicator:checked {
    background-color: #2563EB;
    border-color: #2563EB;
    image: url(__CHECK_WHITE_URL__);
}

QWidget#LogSidebar, QWidget#LogFilterBar, QWidget#LogDetailCard {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
}

QLabel#LogSideTitle, QLabel#LogDetailTitle {
    color: #1E293B;
    background: transparent;
    font-size: 14px;
    font-weight: 700;
}

QWidget#LogDivider { background-color: #E2E8F0; }

QPushButton#LogOverview全部, QPushButton#LogOverviewINFO, QPushButton#LogOverviewSUCCESS,
QPushButton#LogOverviewWARNING, QPushButton#LogOverviewERROR {
    min-height: 27px;
    background: transparent;
    border: none;
    border-radius: 6px;
    padding: 3px 7px;
    text-align: left;
    font-size: 12px;
}

QPushButton#LogOverview全部 { color: #475569; }
QPushButton#LogOverviewINFO { color: #2563EB; }
QPushButton#LogOverviewSUCCESS { color: #16A34A; }
QPushButton#LogOverviewWARNING { color: #EA580C; }
QPushButton#LogOverviewERROR { color: #DC2626; }
QPushButton#LogOverview全部:hover, QPushButton#LogOverviewINFO:hover, QPushButton#LogOverviewSUCCESS:hover,
QPushButton#LogOverviewWARNING:hover, QPushButton#LogOverviewERROR:hover { background-color: #F8FAFC; }
QPushButton#LogOverview全部:checked, QPushButton#LogOverviewINFO:checked, QPushButton#LogOverviewSUCCESS:checked,
QPushButton#LogOverviewWARNING:checked, QPushButton#LogOverviewERROR:checked { background-color: #EFF6FF; font-weight: 700; }

QLineEdit#LogFilterInput, QComboBox#LogFilterInput, QDateEdit#LogFilterInput {
    min-height: 30px;
    color: #334155;
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 0 9px;
    font-size: 12px;
}

QLineEdit#LogFilterInput:focus, QComboBox#LogFilterInput:focus, QDateEdit#LogFilterInput:focus { border-color: #2563EB; }

QWidget#LogFilterBar > QLabel {
    color: #334155;
    background: transparent;
    font-size: 13px;
    font-weight: 700;
}

QPushButton#LogTimeButton {
    min-height: 28px;
    color: #64748B;
    background: transparent;
    border: none;
    border-radius: 5px;
    padding: 3px 10px;
    font-size: 12px;
}

QPushButton#LogTimeButton:hover { color: #2563EB; background-color: #F8FAFC; }
QPushButton#LogTimeButton:checked { color: #2563EB; background-color: #EFF6FF; font-weight: 700; }

QTableWidget#LogTable {
    color: #334155;
    background-color: #FFFFFF;
    alternate-background-color: #FCFDFE;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    gridline-color: #EEF2F7;
    selection-background-color: #EFF6FF;
    selection-color: #1E293B;
    font-size: 12px;
}

QTableWidget#LogTable::item { padding: 4px 7px; border-bottom: 1px solid #EEF2F7; }
QTableWidget#LogTable::item:selected { background-color: #EFF6FF; color: #1E293B; }
QHeaderView::section {
    background-color: #F8FAFC;
    color: #334155;
    border: none;
    border-bottom: 1px solid #E2E8F0;
    padding: 8px;
    font-size: 12px;
    font-weight: 700;
}

QLabel#LogMetadata {
    color: #334155;
    background: transparent;
    font-size: 12px;
    line-height: 1.65;
}

QPlainTextEdit#LogDetailText, QPlainTextEdit#LogContextText {
    color: #334155;
    background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 6px;
    font-family: Consolas, "Microsoft YaHei";
    font-size: 12px;
}

QLabel#LogPageHint { color: #64748B; background: transparent; font-size: 12px; }
QLabel#LogPageLabel { color: #2563EB; background: #EFF6FF; border-radius: 5px; padding: 6px 10px; font-weight: 700; }
QPushButton#LogPageButton { min-width: 30px; min-height: 30px; color: #64748B; background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 5px; }
QPushButton#LogPageButton:hover { color: #2563EB; border-color: #BFDBFE; }

/* ================================================================
   拓扑分析工作台
   ================================================================ */
QWidget#TopologyPage {
    background-color: #F5F7FA;
}

QDialog#TopologyFullscreenDialog {
    background-color: #F5F7FA;
}

QLabel#TopologyPageTitle {
    color: #1E293B;
    font-size: 20px;
    font-weight: 700;
    background: transparent;
}

QLabel#TopologyPageSubtitle, QLabel#TopologyUpdated, QLabel#TopologyHint {
    color: #64748B;
    font-size: 12px;
    background: transparent;
}

QWidget#TopologyCard, QWidget#TopologyKpiCard {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
}

/* 筛选区保持干净的卡片层级，不为字段提供额外的悬浮效果。 */
QWidget#TopologyFilterCard {
    background-color: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
}

/* 全局 QWidget 的浅灰底不能渗入字段容器，否则会像标签下方有阴影。 */
QWidget#TopologyFilterField, QWidget#TopologyFilterActions {
    background-color: #FFFFFF;
    border: none;
}

QWidget#TopologyCard:hover, QWidget#TopologyKpiCard:hover {
    border-color: #CBD5E1;
}

QLabel#TopologyFieldLabel {
    color: #64748B;
    font-size: 14px;
    font-weight: 400;
    border: none;
}

QWidget#TopologyDateRange {
    background-color: #FFFFFF;
    border: 1px solid #D9E2F0;
    border-radius: 6px;
}

QDateEdit#TopologyDateRangeInput {
    min-height: 38px;
    background: transparent;
    border: none;
    padding: 0 5px;
    color: #1E293B;
}

QLabel#TopologyDateSeparator {
    color: #64748B;
    background: transparent;
    min-width: 14px;
}

QLineEdit#TopologyKeyword, QComboBox#TopologySelect {
    min-height: 38px;
    background-color: #FFFFFF;
    border: 1px solid #D9E2F0;
    border-radius: 6px;
    padding: 0 10px;
    color: #1E293B;
    font-size: 13px;
}

QComboBox#TopologySelect {
    padding: 0 28px 0 10px;
    selection-background-color: #EFF6FF;
    selection-color: #1E293B;
}

QWidget#TopologyDateRange:hover, QComboBox#TopologySelect:hover {
    border-color: #2563EB;
}

QDateEdit#TopologyDateRangeInput:focus, QLineEdit#TopologyKeyword:focus, QComboBox#TopologySelect:focus {
    border-color: #2563EB;
    outline: none;
}

QLineEdit#TopologyKeyword::placeholder {
    color: #94A3B8;
}

QPushButton#TopologyPrimaryButton {
    height: 34px;
    min-height: 0px;
    max-height: 34px;
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 0 16px;
    font-weight: 600;
}

QPushButton#TopologyPrimaryButton:hover {
    background-color: #1D4ED8;
}

QPushButton#TopologyFilterSecondaryButton {
    height: 32px;
    min-height: 0px;
    max-height: 32px;
    background-color: #FFFFFF;
    color: #2563EB;
    border-width: 1px;
    border-style: solid;
    border-color: #BFDBFE;
    border-radius: 6px;
    padding: 0 14px;
    font-weight: 600;
}

QPushButton#TopologyFilterSecondaryButton:hover {
    background-color: #EFF6FF;
    border-color: #2563EB;
}

/* 全屏弹窗等原有次级按钮保持原尺寸，避免筛选区规则外溢。 */
QPushButton#TopologySecondaryButton {
    min-height: 34px;
    background-color: #FFFFFF;
    color: #2563EB;
    border: 1px solid #BFDBFE;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 600;
}

QPushButton#TopologySecondaryButton:hover {
    background-color: #EFF6FF;
    border-color: #2563EB;
}

QPushButton#TopologyExportButton {
    min-height: 34px;
    background-color: #FFFFFF;
    color: #2563EB;
    border: 1px solid #BFDBFE;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 600;
}

QPushButton#TopologyExportButton:hover {
    background-color: #EFF6FF;
    border-color: #2563EB;
}

QPushButton#TopologyTextButton {
    color: #2563EB;
    background: transparent;
    border: none;
    padding: 4px 8px;
    font-size: 12px;
}

QLabel#TopologyKpiTitle {
    color: #64748B;
    font-size: 12px;
    background: transparent;
}

QLabel#TopologyKpiValue {
    color: #1E293B;
    font-size: 27px;
    font-weight: 700;
    background: transparent;
}

QLabel#TopologyKpiTrend {
    color: #10B981;
    font-size: 11px;
    background: transparent;
}

QLabel#TopologyCardTitle {
    color: #1E293B;
    font-size: 14px;
    font-weight: 700;
    background: transparent;
}

QWidget#TopologyCanvas, QWidget#TopologyDonut {
    background-color: #FFFFFF;
}

QProgressBar#TopologyProgress {
    background-color: #EEF2F7;
    border: none;
    border-radius: 3px;
    min-height: 5px;
    max-height: 5px;
}

QProgressBar#TopologyProgress::chunk {
    background-color: #2563EB;
    border-radius: 3px;
}

QLabel#TopologyRank {
    color: #2563EB;
    font-size: 11px;
    background: transparent;
}

QLabel#TopologyRankName, QLabel#TopologyPath {
    color: #475569;
    font-size: 11px;
    background: transparent;
}

QLabel#TopologyRankScore, QLabel#TopologyLegend {
    color: #64748B;
    font-size: 11px;
    background: transparent;
}

QLabel#TopologyGraphLegend {
    color: #64748B;
    font-size: 11px;
    background: transparent;
}

QLabel#TopologyGraphLegendDot {
    font-size: 10px;
    background: transparent;
}

QLabel#TopologyInfoIcon {
    color: #2563EB;
    background-color: #EFF6FF;
    border-radius: 10px;
    font-size: 19px;
}

QLabel#TopologyBodyText {
    color: #475569;
    font-size: 12px;
    background: transparent;
    line-height: 1.6;
}

QLabel#TopologyEmpty {
    color: #94A3B8;
    font-size: 12px;
    background: transparent;
}

/* -- 企业 SaaS 下拉框（仪表盘「最近情报」筛选：来源/阶段/排序）-- */
QComboBox#SaasCombo {
    background-color: #FFFFFF;
    border: 1px solid #D0D7DE;
    border-radius: 6px;
    padding: 5px 30px 5px 12px;
    color: #1F2328;
    font-size: 13px;
    selection-background-color: #EFF6FF;
    selection-color: #1F2328;
}

QComboBox#SaasCombo:hover {
    border-color: #2563EB;
    background-color: #FAFBFC;
}

QComboBox#SaasCombo:focus {
    border-color: #2563EB;
    background-color: #FFFFFF;
}

QComboBox#SaasCombo:disabled {
    background-color: #F6F8FA;
    border-color: #E2E8F0;
    color: #94A3B8;
}

QComboBox#SaasCombo::drop-down {
    /* 覆盖全局 QComboBox 的右侧分隔线，保持单层外框。 */
    border: 0px;
    border-left: 0px;
    width: 28px;
    subcontrol-origin: padding;
    subcontrol-position: center right;
}

/* 指定单一箭头资源；覆盖 native 绘制，避免与系统箭头叠加。 */
QComboBox#SaasCombo::down-arrow {
    image: url(__ARROW_DOWN_URL__);
    width: 12px;
    height: 12px;
}

/* 下拉弹出列表 */
QComboBox#SaasCombo QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 4px;
    outline: 0;
    selection-background-color: #EFF6FF;
    selection-color: #2563EB;
}

QComboBox#SaasCombo QAbstractItemView::item {
    height: 30px;
    padding: 0 12px;
    border-radius: 6px;
    color: #1F2328;
}

QComboBox#SaasCombo QAbstractItemView::item:hover {
    background-color: #F1F5F9;
    color: #1F2328;
}

QComboBox#SaasCombo QAbstractItemView::item:selected {
    background-color: #EFF6FF;
    color: #2563EB;
    font-weight: 600;
}

"""


def _qss_arrow_url(filename: str) -> str:
    """返回箭头 SVG 的本地绝对路径（正斜杠），兼容源码运行与 PyInstaller 打包。

    注意：Qt 的 QIcon/QSS url() 不接受 file:/// URL 字符串，必须给本地路径；
    本地路径已实测支持中文目录。
    """
    from pathlib import Path

    from ai_intelligence_system.utils.paths import frozen_resource_root

    icon = Path(frozen_resource_root()) / "ai_intelligence_system" / "ui" / filename
    return icon.resolve().as_posix()


def modern_light_qss() -> str:
    """返回完整的亮色主题 QSS。"""
    qss = STYLE_SHEET + DASHBOARD_STYLE_SHEET
    return (
        qss.replace("__ARROW_DOWN_URL__", _qss_arrow_url("arrow-down.svg"))
        .replace("__ARROW_DOWN_ACTIVE_URL__", _qss_arrow_url("arrow-down-active.svg"))
        .replace("__CHECK_WHITE_URL__", _qss_arrow_url("check-white.svg"))
        .replace("__SWITCH_ON_URL__", _qss_arrow_url("switch-on.svg"))
        .replace("__SWITCH_OFF_URL__", _qss_arrow_url("switch-off.svg"))
    )
