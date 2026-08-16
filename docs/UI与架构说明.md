# AI 行业情报系统 v2.2 — UI 与架构说明

> 生成日期：2026-08-15 ｜ 基于源码 `ai_intelligence_system/` 静态梳理

---

## 一、项目定位

个人行业情报桌面应用：**定时/手动抓取权威网站新闻 → DeepSeek 大模型结构化分析 → SQLite 本地存储 → SMTP 邮件推送**。

- 技术栈：Python 3.12 + PySide6 (Qt Widgets) + SQLAlchemy 2.0 / SQLite + httpx/asyncio + BeautifulSoup + DeepSeek API + loguru + Fernet 加密
- 入口：`main.py`（GUI）、`crawl_main.py`（命令行爬虫）、`scripts/run_crawl_pipeline.py`（命令行采集+分析）
- 打包：PyInstaller（`行业情报系统.spec`），Windows 一键安装

---

## 二、UI 说明

主窗口 `MainWindow`（`main_window.py`，2373 行）：窗口 1280×820，最小 960×640，Fusion 风格，默认浅色主题（可切换深色）。

### 2.1 顶层结构

```
┌─────────────────────────────────────────────────────────────┐
│ 菜单栏: 文件 | 操作 | 查看 | 帮助                             │
├─────────────────────────────────────────────────────────────┤
│ QTabWidget（5 个标签页，底部蓝色下划线指示选中）               │
│  [仪表盘] [统计分析] [手动分析] [设置] [日志与状态]            │
├─────────────────────────────────────────────────────────────┤
│ 状态栏: 就绪 + 免责声明（投资风险提示）                      │
└─────────────────────────────────────────────────────────────┘
```

菜单动作：退出、设置、导出 CSV、立即刷新数据、发送测试邮件、统计分析、日志、关于、切换深/浅色。

### 2.2 标签页 1 —— 仪表盘

左右 `QSplitter` 布局：

| 区域 | 内容 |
|---|---|
| 左侧「最近情报」 | `QListWidget` 情报列表，选中后右侧联动显示详情 |
| 右上「情报详情」 | 只读 `QPlainTextEdit`，格式化展示标题/来源/摘要/影响/评分/阶段/标签/分析全文 |
| 右下「统计分析」 | 评分分布三条进度条：高分(≥80) / 中等(50-79) / 低分(<50)，显示条数与占比 |

顶部有「刷新」按钮，数据来自 `intelligence_records` 表最近记录。

### 2.3 标签页 2 —— 统计分析

`QScrollArea` 长页，含筛选栏 + 六组可视化：

- **分析筛选**：时间区间（全部/24h/3d/7d/30d）、阶段、评分、关键词文本搜索
- **KPI 卡片** ×4：情报总量、平均评分、高分占比、可溯源率
- **评分分布**：柱状图（高分/中等/低分 三档进度条）
- **阶段占比**：饼图样式进度条（信息冲击期/情绪加速期/利多兑现期/不确定）
- **趋势图**：自绘 `TrendChartWidget`（按日期情报数量+平均评分折线）+ 明细表格（日期/数量/均分/趋势强度）
- **热力图**：自绘 `HeatMapWidget`（阶段 × 评分分布）+ 明细表格
- **分类统计**：热门标签 Top 10、来源机构 Top 10（进度条）
- **趋势分析结论**：只读文本区，规则化生成洞察

所有图表均为 QPainter 自绘控件（无第三方绘图库）。

### 2.4 标签页 3 —— 手动分析（核心操作页）

上下 `QSplitter`，三张「终端卡片」（TerminalCard，带阴影与彩色圆点标题）：

**① 爬取流程**（蓝点）
- 工具栏：采集天数 SpinBox(1-30) + 「爬取后自动分析」「分析后发邮件」两个复选 + 主按钮「采集」
- 状态徽章（○ 等待开始）+ 实时日志 `QTextBrowser`（链接可点开）
- 后台走 `CrawlPipelineWorker`：连接网站 → 请求新闻列表 → 解析内容 → 写 SQLite，逐步推送状态

**② 新闻数据**（绿点）
- 筛选：来源下拉（全部/ndrc/nea/miit/china5e）+ 天数(1-365) + 「刷新」
- 删除管理栏：清空列表、按日期区间删除（QDateEdit 起止 + 删除区间），红色危险按钮
- `NewsTableWidget` 六列：标题（蓝色可点击打开原文）/ 发布时间 / 来源 / 摘要（截断+tooltip）/ 查看详情弹窗 / 删除按钮
- 分页：显示条数提示 + 「加载更多」（每次 +80 行，初始 120 行）

**③ AI 智能分析**（紫点）
- 工具栏：分析范围（最近 24 小时/3 天/7 天）+ 绿色主按钮「执行分析」
- 补充说明输入框（可选，追加进 Prompt）
- 只读输出控制台展示模型返回的结构化 JSON 分析

### 2.5 标签页 4 —— 设置

上下分区，中部左右 `QSplitter`：

- **本地存储与路径**：只读文本展示配置 JSON / SQLite / 加密密钥 / 日志目录的绝对路径
- **AI 设置**：API Key（密码掩码）、Base URL、Model（默认 deepseek-chat）
- **通知设置（邮件）**：SMTP 服务器/端口/账号/密码（掩码）/SSL 开关/收件人（逗号分隔）
- **爬虫设置**：4 个来源复选（ndrc/nea/miit/china5e）+ 每站最多条数(1-50)；早/午/晚三个调度时段，每个含启用复选、每天/每周频率、周几、HH:MM 时间
- **业务与日志**：行业关键词（逗号分隔）、数据库路径、日志级别、自定义系统 Prompt
- 底部「保存设置」按钮，后台线程写盘，保存后调度立即重载

### 2.6 标签页 5 —— 日志与状态

- 调度线程状态标签（运行中）+ 只读日志区 `QPlainTextEdit`
- 通过 loguru sink 转发到 UI（`LogBus` 信号桥接）

### 2.7 视觉设计系统（`ui/styles.py`，1178 行 QSS）

蓝白现代主题，Tailwind 风格色板：

| 用途 | 色值 |
|---|---|
| 页面背景 | `#F5F7FA` |
| 卡片/导航背景 | `#FFFFFF` |
| 主色（选中/主按钮） | `#2563EB`（hover `#1D4ED8`，pressed `#1E40AF`） |
| 成功绿 | `#10B981` |
| 危险红 | `#EF4444` |
| 正文 / 次要文字 | `#1E293B` / `#64748B` |
| 分割线 / 禁用 | `#E2E8F0` / `#CBD5E1` |

组件命名规范（objectName）：`PrimaryBtn` `SuccessBtn` `DangerButton` `GhostButton` `TerminalCard` `CardHeader` `CardTitle` `CardDivider` `HeaderDotBlue/Green/Purple` `FilterBar` `DeleteBar` `FieldLabel` `CompactSpin` `FilterCombo` `InlineCheck` `StatusChip` `StatusPill` `FooterHint` `KpiValue` `LogConsole` `OutputConsole` `PromptInput` `VSep`。

字体：Microsoft YaHei / PingFang SC，13px 基础字号。深色主题由 `ui/theme.py` 提供 QPalette（深灰 #353535 系 + 蓝色高亮）。

---

## 三、架构说明

### 3.1 分层架构

```
┌──────────────────────────────────────────────────────────────┐
│ 表现层（UI）                                                  │
│  main_window.py（MainWindow + 自绘图表 + 菜单/状态栏）         │
│  ui/（styles QSS、theme 深浅色、news_table_widget）           │
├──────────────────────────────────────────────────────────────┤
│ 异步层（Workers，QThread + QObject 信号槽）                    │
│  workers/ai_analysis_worker.py                               │
│   ├ CrawlPipelineWorker     爬取管线（分步状态推送）            │
│   ├ NewsLoadWorker          新闻表加载                        │
│   ├ RecentNewsAnalysisWorker 基于SQLite新闻的AI分析           │
│   ├ AiAnalysisWorker        手动/定时分析（先实时爬取）        │
│   ├ DashboardLoadWorker     仪表盘加载                        │
│   ├ SettingsSaveWorker      配置写盘                          │
│   ├ EmailSendWorker         邮件发送（带重试）                 │
│   └ ExportCsvWorker         CSV 导出（UTF-8 BOM）             │
├──────────────────────────────────────────────────────────────┤
│ 业务层（Core）                                                │
│  data_collector.py    多源并行采集调度                         │
│  crawler_factory.py   爬虫注册表（装饰器模式）                 │
│  base_crawler.py      BaseCrawler 抽象基类 + NewsItem          │
│  crawlers/            4 个具体爬虫（ndrc/nea/miit/china5e）    │
│  crawl_history.py     按日增量进度（JSON）                     │
│  ai_analyzer.py       DeepSeek 聚合分析（结构化JSON）          │
│  analyzer.py          Prompt 构建 + JSON 容错解析              │
│  ai_client.py         DeepSeek 客户端（OpenAI兼容）            │
│  scheduler.py         定时服务（QTimer 轮询）                  │
│  email_sender.py      HTML 邮件（SSL/STARTTLS）               │
│  database.py          SQLAlchemy 引擎/会话/CRUD               │
├──────────────────────────────────────────────────────────────┤
│ 模型层                                                        │
│  models/intelligence_record.py                                │
│   ├ IntelligenceRecord  情报分析结果表                        │
│   └ NewsRecord          原始新闻表                            │
├──────────────────────────────────────────────────────────────┤
│ 基础设施                                                      │
│  config/settings.py   Pydantic 配置 + JSON 持久化              │
│  utils/crypto.py      Fernet 对称加密（API Key/SMTP 密码）     │
│  utils/paths.py       路径解析（源码/打包双模式）               │
│  SQLite + loguru 滚动日志 + 环境变量(.env)                     │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 核心数据流

```
[采集]  DataCollector ──▶ 4×BaseCrawler（asyncio 并行）
        │                   列表页解析 → 详情页并发抓取（Semaphore=5）
        ▼
    NewsItem[]（URL 去重）
        ▼
[入库]  SQLite news_records（url 唯一约束，增量 upsert）
        ▼
[分析]  NewsItem[] ──▶ AiAnalyzer ──▶ DeepSeek Chat Completions
        │                  system prompt：仅基于本地数据研判
        │                  user prompt：关键词 + 时间窗 + news_items JSON
        ▼
    结构化 JSON：title/source/source_url/time/summary/impact/score(1-10)/
                 stage(四档)/tags/related/analysis
        ▼
[入库]  SQLite intelligence_records
        ▼
[推送]  手动邮件 或 定时任务（SchedulerService）→ EmailSendWorker
        → HTML 简报（含免责声明）→ SMTP
```

### 3.3 线程模型（关键设计）

- **UI 主线程**：仅负责界面与信号分发，任何网络/AI/DB 批量操作一律不阻塞 UI
- **通用 Worker 模式**：`QThread` + `QObject` Worker，`thread.started → worker.run`，`finished_ok/failed → thread.quit`，`deleteLater` 清理；主窗口用 `_active_background_jobs` 强引用防止 Worker 被 GC（代码注释明确提到此坑）
- **调度线程**：`SchedulerService` 常驻独立 `QThread`，内部 `QTimer` 每 30 秒比对 HH:MM 触发 `job_due` 信号，主线程收到后执行「爬取→自动分析→自动邮件」流水线
- **爬虫并发**：`asyncio` 单事件循环内 `asyncio.gather` 并行多源；详情页 `Semaphore` 限流（默认 5）

### 3.4 配置与安全

- `config/config.json`：全部运行时配置，敏感字段（`deepseek_api_key_enc`、`smtp_password_enc`）以 **Fernet** 加密存储
- 密钥文件 `data/.fernet_key`（已 .gitignore，权限 600）；解密仅发生在内存
- `.env` 可选（`AI_INTELLIGENCE_` 前缀）覆盖默认值

### 3.5 数据库 Schema

**intelligence_records**（分析结果）
`id / timestamp(索引) / title / source / source_url / content(分析全文) / summary / impact / score(Float) / stage / tags / raw_json(完整模型输出)`

**news_records**（原始新闻）
`id / title / url(唯一约束) / publish_time(索引) / source(索引) / content / summary / raw_html / metadata_json / crawled_at(索引)`

### 3.6 爬虫扩展机制

```python
@register("ndrc")          # 装饰器注册到 _REGISTRY
class NdrcCrawler(BaseCrawler):
    source_id = "ndrc"
    source_name = "国家发改委"
    async def fetch_by_date(client, start_date, end_date) -> list[NewsItem]: ...
```

- 新源三步启用：新建模块 + `@register` 装饰 → 在 `crawlers/__init__.py` 的 `_AUTO_IMPORTS` 加入模块名 → 在设置页勾选（写入 `crawl_source_ids`）
- 内置 `_parse_utils.py` 提供统一解析工具：政府正文提取 `extract_gov_article`、日期归一化、URL 日期解析、同域判断
- `stcn.py`（证券时报）是预留模板，未启用

### 3.7 定时任务机制（与 README 的差异）

- README 声称 APScheduler，**实际实现是 `QTimer` 30 秒轮询**（`core/scheduler.py`），独立 QThread 常驻
- 每日三个时段（早/午/晚），支持 daily/weekly + 周几；按日期键防重复触发
- 触发后走完整流水线：`_run_crawl_pipeline_async`（自动勾选"爬取后自动分析"+"分析后发邮件"）

### 3.8 打包（PyInstaller）

- `行业情报系统.spec`：单目录模式（COLLECT），隐藏导入 `bs4` + 爬虫子模块 + PySide6 Qt 全部模块
- 资源打包：`ico.ico`、`ai_intelligence_system/`、`config/`、`data/`、`logs/`
- 排除 Qt Qml/Quick/WebEngine 以减小体积
- 运行时路径双模式：源码→项目根；frozen→`%APPDATA%/AIIntelligenceSystem`（解决 C 盘权限问题）

### 3.9 遗留/注意点

1. `widgets/dashboard/dashboard_log.py`（旧版日志组件）未被当前主窗口引用，属遗留代码
2. `RecentNewsAnalysisWorker._save_to_db` 通过实例化 `AiAnalysisWorker` 复用入库逻辑，较绕
3. 手动分析（`AiAnalysisWorker`）每次**实时重新爬取**；仅"最近新闻分析"复用 SQLite 数据
4. `source` 字段在分析输出中为"来源机构"，`NewsRecord.source` 为站点名，两者语义不同
5. `screenshots/` 中已有 7 张历史界面截图（dashboard/statistics/settings/email/log/analyze），但本项目未配置 vision model，无法自动读图
