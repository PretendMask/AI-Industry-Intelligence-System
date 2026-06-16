"""现代 UI QSS 样式表。"""

from __future__ import annotations


def modern_light_qss() -> str:
    return """
QMainWindow, QWidget {
    background: #f6f8fb;
    color: #172033;
    font-family: "Microsoft YaHei UI", "Segoe UI", system-ui, sans-serif;
    font-size: 14px;
}

QMenuBar {
    background: #ffffff;
    border-bottom: 1px solid #e5eaf2;
    padding: 4px 8px;
}

QMenuBar::item {
    padding: 7px 12px;
    border-radius: 8px;
}

QMenuBar::item:selected {
    background: #f1f5ff;
    color: #2558d8;
}

QToolBar {
    background: #ffffff;
    border: none;
    border-bottom: 1px solid #e5eaf2;
    spacing: 8px;
    padding: 8px 12px;
}

QTabWidget::pane {
    border: none;
    background: #f6f8fb;
    top: -1px;
}

QTabBar::tab {
    background: transparent;
    color: #64748b;
    padding: 12px 18px 10px 18px;
    border: none;
    border-bottom: 2px solid transparent;
    margin: 0 4px;
    font-weight: 600;
}

QTabBar::tab:selected {
    color: #1d4ed8;
    border-bottom: 2px solid #2563eb;
}

QTabBar::tab:hover {
    color: #1d4ed8;
    background: #eef4ff;
    border-radius: 10px;
}

QGroupBox {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    margin-top: 18px;
    padding: 18px;
    font-weight: 700;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
    color: #0f172a;
    background: transparent;
}

QGroupBox#PanelCard {
    background: #ffffff;
    border: 1px solid #e5eaf2;
    border-radius: 18px;
}

QLabel#KpiValue {
    color: #2563eb;
    font-size: 28px;
    font-weight: 800;
}

QLabel#DialogTitle {
    color: #0f172a;
    font-size: 18px;
    font-weight: 800;
    padding: 8px 0;
}

QLabel#StatusPill {
    background: #eff6ff;
    color: #1d4ed8;
    border: 1px solid #bfdbfe;
    border-radius: 10px;
    padding: 8px 12px;
    font-weight: 600;
}

QPushButton {
    background: #2563eb;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    min-height: 28px;
    font-weight: 600;
}

QPushButton:hover {
    background: #1d4ed8;
}

QPushButton:pressed {
    background: #1e40af;
}

QPushButton:disabled {
    background: #94a3b8;
    color: #f8fafc;
}

QPushButton#DangerButton {
    background: #fff1f2;
    color: #be123c;
    border: 1px solid #fecdd3;
    padding: 6px 10px;
    min-height: 24px;
}

QPushButton#DangerButton:hover {
    background: #ffe4e6;
    border: 1px solid #fda4af;
}

QPushButton#GhostButton {
    background: #eef2ff;
    color: #3730a3;
    border: 1px solid #c7d2fe;
    padding: 6px 10px;
    min-height: 24px;
}

QPushButton#GhostButton:hover {
    background: #e0e7ff;
    border: 1px solid #a5b4fc;
}

QLineEdit {
    min-height: 30px;
}

QLineEdit, QTextEdit, QPlainTextEdit, QTextBrowser, QListWidget {
    background: #ffffff;
    border: 1px solid #d8e0ec;
    border-radius: 10px;
    padding: 8px;
    selection-background-color: #bfdbfe;
}

QComboBox, QSpinBox, QDateEdit {
    background: #ffffff;
    border: 1px solid #b9c6d8;
    border-radius: 7px;
    color: #172033;
    font-size: 13px;
    min-height: 26px;
    max-height: 30px;
    padding: 3px 28px 3px 9px;
    selection-background-color: #bfdbfe;
}

QComboBox:hover, QSpinBox:hover, QDateEdit:hover {
    border: 1px solid #7da2e8;
    background: #fbfdff;
}

QComboBox:focus, QSpinBox:focus, QDateEdit:focus {
    border: 1px solid #2563eb;
    background: #ffffff;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid #d8e0ec;
    border-top-right-radius: 7px;
    border-bottom-right-radius: 7px;
    background: #f1f5ff;
}

QComboBox::drop-down:hover {
    background: #dbeafe;
}

QComboBox QAbstractItemView {
    background: #ffffff;
    border: 1px solid #93b4ea;
    border-radius: 8px;
    padding: 4px;
    outline: none;
    selection-background-color: #eff6ff;
    selection-color: #1d4ed8;
}

QSpinBox::up-button, QSpinBox::down-button,
QDateEdit::up-button, QDateEdit::down-button {
    subcontrol-origin: border;
    width: 22px;
    border-left: 1px solid #d8e0ec;
    background: #f1f5ff;
}

QSpinBox::up-button {
    subcontrol-position: top right;
    border-top-right-radius: 7px;
}

QSpinBox::down-button {
    subcontrol-position: bottom right;
    border-bottom-right-radius: 7px;
}

QSpinBox::up-button:hover, QSpinBox::down-button:hover,
QDateEdit::up-button:hover, QDateEdit::down-button:hover {
    background: #dbeafe;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QTextBrowser:focus {
    border: 1px solid #2563eb;
}

QTableWidget {
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    background-color: white;
    gridline-color: #f1f5f9;
    selection-background-color: #eff6ff;
    selection-color: #0f172a;
    alternate-background-color: #fbfdff;
    outline: none;
}

QTableWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid #f1f5f9;
}

QTableWidget::item:hover {
    background-color: #f8fafc;
}

QTableWidget::item:selected {
    background: #eff6ff;
    color: #0f172a;
}

QHeaderView::section {
    background-color: #f8fafc;
    color: #475569;
    padding: 12px 8px;
    border: none;
    border-bottom: 1px solid #e2e8f0;
    font-weight: 600;
}

QProgressBar {
    border: 1px solid #d8e0ec;
    border-radius: 10px;
    background: #eff6ff;
    text-align: center;
    min-height: 22px;
}

QProgressBar::chunk {
    background: #2563eb;
    border-radius: 9px;
}

QSplitter::handle {
    background: #e2e8f0;
    border-radius: 6px;
}

QSplitter::handle:hover {
    background: #bfdbfe;
}

QSplitter::handle:horizontal {
    width: 8px;
    margin: 2px 6px;
}

QSplitter::handle:vertical {
    height: 8px;
    margin: 6px 2px;
}

QScrollBar:vertical {
    background: transparent;
    width: 14px;
    margin: 6px 3px;
    border-radius: 7px;
}

QScrollBar::handle:vertical {
    background: #cbd5e1;
    border-radius: 7px;
    min-height: 42px;
}

QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
    background: transparent;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}

QScrollBar:horizontal {
    background: transparent;
    height: 14px;
    margin: 3px 6px;
    border-radius: 7px;
}

QScrollBar::handle:horizontal {
    background: #cbd5e1;
    border-radius: 7px;
    min-width: 42px;
}

QScrollBar::handle:horizontal:hover {
    background: #94a3b8;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
    background: transparent;
}

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: transparent;
}

/* ── Terminal Panel (Financial Terminal Style) ── */
/* PLACEHOLDER_TERMINAL_STYLES */
"""
