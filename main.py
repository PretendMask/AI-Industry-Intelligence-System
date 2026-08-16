"""应用入口。"""

from __future__ import annotations

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

# 注意：这里刻意不调用 SetCurrentProcessExplicitAppUserModelID。
# 当进程设置了 AppUserModelID、但系统中没有带相同 ID 的快捷方式(.lnk)时，
# Windows 任务栏按钮图标会回退到 exe 图标（即 python.exe 的 Python 徽标），
# 而不是 setWindowIcon 设置的窗口图标——表现为"任务栏没有程序图标"。
# 去掉该调用后，任务栏按钮直接使用窗口图标（ico.ico）。


def _load_app_icon() -> QIcon:
    icon_path = app_icon_path()
    if icon_path.exists():
        return QIcon(str(icon_path))
    return QIcon()


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("行业情报系统")
    app.setStyle("Fusion")

    icon = _load_app_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)

    window = MainWindow()
    if not icon.isNull():
        window.setWindowIcon(icon)
    window.show()
    if not icon.isNull():
        # show 之后再设置一次窗口图标，覆盖任务栏按钮创建的时序差异
        window.setWindowIcon(icon)
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
