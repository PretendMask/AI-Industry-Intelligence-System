"""应用路径解析（数据目录、配置、日志）。"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def project_root() -> Path:
    """仓库根目录（含 main.py 的目录）。"""
    # ai_intelligence_system/utils/paths.py -> parents[2] = 项目根
    return Path(__file__).resolve().parents[2]


def _user_data_root() -> Path:
    """用户可写数据根目录。打包后使用 APPDATA，开发时使用项目根。"""
    if getattr(sys, "frozen", False):
        base = Path(os.environ.get("APPDATA", "~")).expanduser()
        return base / "AIIntelligenceSystem"
    return project_root()


def data_dir() -> Path:
    p = _user_data_root() / "data"
    p.mkdir(parents=True, exist_ok=True)
    return p


def logs_dir() -> Path:
    p = _user_data_root() / "logs"
    p.mkdir(parents=True, exist_ok=True)
    return p


def default_database_path() -> Path:
    return data_dir() / "intelligence.db"


def config_dir() -> Path:
    p = _user_data_root() / "config"
    p.mkdir(parents=True, exist_ok=True)
    return p


def user_config_path() -> Path:
    """用户可编辑的 JSON 配置文件路径。"""
    return config_dir() / "config.json"


def fernet_key_path() -> Path:
    """本地对称密钥文件（用于加密 API Key 等，勿提交到版本库）。"""
    return data_dir() / ".fernet_key"


def frozen_resource_root() -> Path:
    """PyInstaller 单文件模式下资源根路径。"""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return project_root()


def app_icon_path() -> Path:
    """应用图标路径，兼容源码运行与 PyInstaller 打包。"""
    return frozen_resource_root() / "ico.ico"


def describe_local_storage(*, database_path: str) -> str:
    """供界面展示的本地持久化路径（绝对路径）。"""
    cfg = user_config_path().resolve()
    key = fernet_key_path().resolve()
    logd = logs_dir().resolve()
    db = Path(database_path).expanduser()
    try:
        db_abs = str(db.resolve())
    except OSError:
        db_abs = str(db)
    return (
        "本地数据落盘说明\n"
        "————————————————————————————————\n"
        "【配置】JSON 文件（API Key / SMTP 等为加密字段）：\n"
        f"  {cfg}\n\n"
        "【情报与分析】SQLite 数据库（表 intelligence_records）：\n"
        f"  {db_abs}\n\n"
        "【加密密钥】用于解密上述配置中的敏感字段：\n"
        f"  {key}\n\n"
        "【日志】loguru 滚动日志：\n"
        f"  {logd}\n"
    )
