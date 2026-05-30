# AI 行业情报系统（桌面版）

基于 **Python 3.10+**、**PySide6**、**SQLite** 与 **DeepSeek API** 的个人行业情报桌面应用：手动/定时分析、本地存储、邮件推送（SMTP）。

## 环境要求

- Python 3.10 或更高版本
- Windows / macOS / Linux

## 安装

在项目根目录（含 `main.py` 与 `requirements.txt`）执行：

```bash
python -m venv .venv
```

**Windows（PowerShell）：**

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux：**

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## 配置

1. 首次运行会在 `config/config.json` 写入配置（若不存在则从默认加载）。（仓库已忽略 `config/config.json`）。
2. API Key 与 SMTP 密码在磁盘上以 **Fernet** 对称加密存储，密钥文件位于 `data/.fernet_key`（已加入 `.gitignore`）。
3. 可选：复制 `.env.example` 为 `.env`，设置 `AI_INTELLIGENCE_LOG_LEVEL` 等（见 `config/settings.py` 中的 `env_prefix`）。

在应用内 **「设置」** 标签页填写 **DeepSeek API Key**、SMTP 与收件人后点击 **保存设置**。

## 运行

在项目根目录：

```bash
python main.py
```

## 项目结构（摘要）

- `main.py`：入口
- `ai_intelligence_system/`：主包（主窗口、UI 主题、Worker、Core、模型、工具）
- `data/`：SQLite 与本地密钥
- `logs/`：滚动日志文件
- `config/`：用户 `config.json`（运行时生成）

## 开发说明

- 网络请求、AI 调用、数据库批量读写、导出、邮件发送等均在 **QThread + QObject Worker** 中执行，避免阻塞 UI。
- 定时任务使用 **APScheduler** 的 `BackgroundScheduler`，在 **独立 QThread** 中启停（见 `core/scheduler.py`）。





