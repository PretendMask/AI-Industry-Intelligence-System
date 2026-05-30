"""应用入口。"""

from __future__ import annotations

import ctypes
import sys
from pathlib import Path

# 确保以 `python main.py` 从项目根运行时能导入包
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from ai_intelligence_system.main_window import MainWindow
from ai_intelligence_system.utils.paths import app_icon_path


def _set_windows_app_user_model_id() -> None:
    if sys.platform != "win32":
        return
    app_id = "AIIndustryIntelligence.System.Desktop.1"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)


def _load_app_icon() -> QIcon:
    icon_path = app_icon_path()
    if icon_path.exists():
        return QIcon(str(icon_path))
    return QIcon()


def main() -> None:
    _set_windows_app_user_model_id()

    app = QApplication(sys.argv)
    app.setApplicationName("AI行业情报系统")
    app.setStyle("Fusion")

    icon = _load_app_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)

    window = MainWindow()
    if not icon.isNull():
        window.setWindowIcon(icon)
    window.show()
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
