"""
Dashboard日志页面 - 实时显示爬虫运行日志和任务历史
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QLabel, QFrame, QScrollArea, QTableWidget, QHeaderView,
    QTableWidgetItem, QSplitter, QAbstractItemView
)
from PySide6.QtCore import Qt, QTimer, Signal, QDateTime
from PySide6.QtGui import QColor, QTextCursor, QFont
from datetime import datetime

from ai_intelligence_system.core.log_worker import LogWorker
from ai_intelligence_system.widgets.custom_widgets import (
    LogDetailDialog,
)


class DashboardLog(QWidget):
    """日志和监控页面 - 迁移自monitor_log_widget"""
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.log_worker = LogWorker(db)
        self.init_ui()
        self.init_connections()
    
    def init_ui(self):
        # 日志输出框 (使用QTextEdit以支持富文本)
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setObjectName("logOutput")
        self.log_output.setLineWrapMode(QTextEdit.WidgetWidth)
        self.log_output.setFrameShape(QFrame.NoFrame)
        self.log_output.setMinimumHeight(150)
        self.log_output.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        # 设置等宽字体，更适合日志显示
        log_font = QFont("Consolas", 11)
        log_font.setStyleHint(QFont.Monospace)
        self.log_output.setFont(log_font)
        # 浅色背景 - 匹配全局蓝白主题
        self.log_output.setStyleSheet("""
            QTextEdit#logOutput {
                background-color: #FAFBFC;
                color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        
        # 任务状态映射
        self.task_map = {}
        
        # 保存默认文本格式
        self.default_format = self.log_output.currentCharFormat()
    
    def init_connections(self):
        """初始化信号连接"""
        if self.log_worker:
            self.log_worker.log_signal.connect(self.append_log)
            self.log_worker.task_changed.connect(self.update_task_table)
    
    def append_log(self, status_text, category="info", message=None):
        """追加日志 - 使用HTML富文本以实现颜色区分"""
        if not self.log_output:
            return
        
        # 状态映射为键
        status_map = {
            "已完成": "success",
            "搜索中": "info",
            "解析中": "info",
            "保存中": "info",
            "等待中": "pending",
            "待处理": "pending",
            "空闲": "idle"
        }
        status_key = status_map.get(status_text, "idle")
        
        # 根据状态设置颜色 (浅色背景适配)
        html_color = "#64748B"
        if status_key == "running":
            html_color = "#2563EB"  # 蓝色 - 运行中
        elif status_key == "pending":
            html_color = "#F59E0B"  # 橙色 - 等待中
        elif status_key == "success":
            html_color = "#10B981"  # 绿色 - 成功
        elif status_key == "info":
            html_color = "#2563EB"  # 蓝色 - 搜索/解析/保存中
        elif status_key == "error":
            html_color = "#EF4444"  # 红色 - 错误
        elif status_key == "cancelled":
            html_color = "#94A3B8"  # 灰 - 已取消
        elif status_key == "paused":
            html_color = "#EF4444"  # 红色 - 已暂停
        elif status_key == "idle":
            html_color = "#64748B"  # 次文字色 - 空闲
        
        # 获取底部日志窗口内容
        current_text = self.log_output.toPlainText() if self.log_output else ""
        displayed_rows = len(current_text.strip().split('\n')) if current_text.strip() else 0
        max_rows = 200
        
        # 清理旧日志
        if displayed_rows > max_rows:
            cursor = self.log_output.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor, displayed_rows - max_rows)
            cursor.removeSelectedText()
            cursor.deleteChar()
        
        # 构建 HTML 日志行
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 分类颜色 (浅色背景适配)
        if category in ["success", "完成"]:
            category_color = "#10B981"  # 绿色
            category_text = "完成"
        elif category in ["error", "错误"]:
            category_color = "#EF4444"  # 红色
            category_text = "错误"
        elif category in ["warning", "警告"]:
            category_color = "#F59E0B"  # 橙色
            category_text = "警告"
        else:
            category_color = "#475569"  # 深灰 - 普通信息
            category_text = category if category else "信息"
        
        # 构建 HTML
        log_html = '<div style="margin-bottom: 2px; line-height: 1.6;">'
        log_html += f'<span style="color: #94A3B8; font-size: 11px;">[{timestamp}]</span>&nbsp;'
        
        if message:
            log_html += f'<span style="color: {category_color}; font-weight: 600;">[{category_text}]</span>&nbsp;'
            log_html += f'<span style="color: #F8FAFC;">{message}</span>'
        else:
            log_html += f'<span style="color: {category_color}; font-weight: 600;">[{category_text}]</span>'
        
        log_html += '</div>'
        
        self._append_html_to_log(log_html)

    def _append_html_to_log(self, html: str):
        """添加 HTML 格式日志到输出框"""
        if not self.log_output:
            return
        cursor = self.log_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertHtml(html)
        
        # 自动滚动到底部
        scrollbar = self.log_output.verticalScrollBar()
        if scrollbar and scrollbar.value() >= scrollbar.maximum() - 10:
            scrollbar.setValue(scrollbar.maximum())

    def refresh_data(self):
        """刷新数据"""
        # 刷新任务表格
        if hasattr(self, 'task_table'):
            self.update_task_table(None)
    
    def add_log_line(self, message: str, level: str = "INFO"):
        """添加日志行 - 使用HTML富文本"""
        if not hasattr(self, 'log_output') or not self.log_output:
            return
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 根据级别设置颜色 (浅色背景适配)
        color = "#475569"
        if level == "ERROR":
            color = "#EF4444"  # 红色
        elif level == "WARNING":
            color = "#F59E0B"  # 橙色
        elif level == "SUCCESS":
            color = "#10B981"  # 绿色
        elif level == "INFO":
            color = "#2563EB"  # 蓝色
        
        # 构建HTML日志行
        log_html = (
            f'<div style="margin-bottom: 2px; line-height: 1.6;">'
            f'<span style="color: #94A3B8; font-size: 11px;">[{timestamp}]</span>&nbsp;'
            f'<span style="color: {color}; font-weight: 600;">[{level}]</span>&nbsp;'
            f'<span style="color: #F8FAFC;">{message}</span>'
            f'</div>'
        )
        
        # 追加到日志输出框
        cursor = self.log_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertHtml(log_html)
        
        # 自动滚动到底部
        scrollbar = self.log_output.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())
    
    def update_task_table(self, tasks):
        """更新任务表格"""
        if not hasattr(self, 'task_table') or not self.task_table:
            return
        
        # 保存当前选择
        current_row = self.task_table.currentRow()
        
        # 如果没有任务数据，尝试从log_worker获取
        if tasks is None and self.log_worker:
            tasks = self.log_worker.get_tasks()
        
        if not tasks:
            self.task_table.setRowCount(0)
            return
        
        self.task_table.setRowCount(len(tasks))
        
        for row, task in enumerate(tasks):
            # 名称
            name_item = QTableWidgetItem(task.get("name", ""))
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.task_table.setItem(row, 0, name_item)
            
            # 状态
            status = task.get("status", "空闲")
            status_item = QTableWidgetItem(status)
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
            
            # 根据状态设置颜色
            status_colors = {
                "运行中": QColor("#2563EB"),
                "已完成": QColor("#10B981"),
                "失败": QColor("#EF4444"),
                "已暂停": QColor("#F59E0B"),
                "空闲": QColor("#94A3B8"),
            }
            status_item.setForeground(status_colors.get(status, QColor("#1E293B")))
            self.task_table.setItem(row, 1, status_item)
            
            # 时间
            time_str = task.get("time", datetime.now().strftime("%Y-%m-%d %H:%M"))
            time_item = QTableWidgetItem(time_str)
            time_item.setFlags(time_item.flags() & ~Qt.ItemIsEditable)
            self.task_table.setItem(row, 2, time_item)
    
    def clear_log(self):
        """清空日志"""
        if self.log_output:
            self.log_output.clear()
    
    def get_log_text(self) -> str:
        """获取当前日志内容"""
        if self.log_output:
            return self.log_output.toPlainText()
        return ""

    def _create_log_section(self):
        """创建日志输出区域"""
        log_layout = QVBoxLayout()
        
        # 状态和控制按钮
        control_layout = QHBoxLayout()
        self.log_status_label = QLabel("日志输出")
        self.log_status_label.setObjectName("titleLabel")
        control_layout.addWidget(self.log_status_label)
        
        control_layout.addStretch()
        
        self.btn_clear_log = QPushButton("清空日志")
        self.btn_clear_log.setObjectName("outlineBtn")
        self.btn_clear_log.clicked.connect(self.clear_log)
        control_layout.addWidget(self.btn_clear_log)
        
        self.btn_export_log = QPushButton("导出日志")
        self.btn_export_log.setObjectName("outlineBtn")
        self.btn_export_log.clicked.connect(self.export_log)
        control_layout.addWidget(self.btn_export_log)
        
        log_layout.addLayout(control_layout)
        log_layout.addWidget(self.log_output)
        
        return log_layout

    def export_log(self):
        from PySide6.QtWidgets import QFileDialog
        from datetime import datetime
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出日志", f"crawler_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "文本文件 (*.txt);;日志文件 (*.log);;所有文件 (*.*)"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_output.toPlainText())
                self.add_log_line(f"日志已导出至: {file_path}", "SUCCESS")
            except Exception as e:
                self.add_log_line(f"导出日志时出错: {str(e)}", "ERROR")

    def _on_task_double_clicked(self, index):
        """任务表格双击事件 - 查看详情"""
        row = index.row()
        if not hasattr(self, 'task_table') or not self.task_table:
            return
        
        task_name = self.task_table.item(row, 0).text() if self.task_table.item(row, 0) else ""
        task_status = self.task_table.item(row, 1).text() if self.task_table.item(row, 1) else ""
        task_time = self.task_table.item(row, 2).text() if self.task_table.item(row, 2) else ""
        
        # 从log_worker获取详细任务数据
        tasks = self.log_worker.get_tasks() if self.log_worker else []
        task_data = None
        for t in tasks:
            if t.get("name") == task_name:
                task_data = t
                break
        
        # 如果没有找到详细数据，构建基本数据
        if not task_data:
            task_data = {
                "name": task_name,
                "status": task_status,
                "time": task_time,
                "url": "",
                "keyword": "",
                "total_found": 0,
                "success_count": 0,
                "error_count": 0,
                "crawled_urls": [],
                "errors": []
            }
        
        dialog = LogDetailDialog(task_data, self)
        dialog.exec()

    def _on_url_clicked(self, url):
        """处理URL点击 - 在浏览器中打开"""
        import webbrowser
        if url:
            webbrowser.open(url)
    
    def _on_stop_crawl(self):
        """停止爬虫按钮点击"""
        self.add_log_line("用户手动停止爬虫", "WARNING")
        # TODO: 实际停止爬虫的逻辑
    
    def _on_clear_tasks(self):
        """清空已完成任务"""
        if self.log_worker:
            self.log_worker.clear_completed_tasks()
        self.add_log_line("已清空已完成的任务", "INFO")
    
    def _on_export_tasks(self):
        """导出任务列表"""
        tasks = self.log_worker.get_tasks() if self.log_worker else []
        
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出任务列表",
            f"tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV文件 (*.csv);;所有文件 (*.*)"
        )
        if file_path:
            try:
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(["任务名称", "状态", "时间", "URL数量", "成功", "失败"])
                    for task in tasks:
                        writer.writerow([
                            task.get("name", ""),
                            task.get("status", ""),
                            task.get("time", ""),
                            task.get("total_found", 0),
                            task.get("success_count", 0),
                            task.get("error_count", 0)
                        ])
                self.add_log_line(f"任务列表已导出至: {file_path}", "SUCCESS")
            except Exception as e:
                self.add_log_line(f"导出任务列表时出错: {str(e)}", "ERROR")
    
    def _on_retry_tasks(self):
        """重试失败任务信号"""
        self.add_log_line("重试失败的任务", "INFO")
        # TODO: 实际重试逻辑
    
    def _on_crawl_selected(self):
        """对选中关键词执行爬取"""
        self.add_log_line("执行选中爬取", "INFO")
    
    def _on_crawl_all(self):
        """对所有关键词执行爬取"""
        self.add_log_line("执行全部爬取", "INFO")
    
    def _on_pause_all(self):
        """暂停所有爬取"""
        self.add_log_line("暂停所有爬取任务", "WARNING")
    
    def refresh_log_signal(self, log_text: str):
        """刷新日志信号处理"""
        if hasattr(self, 'log_output') and self.log_output:
            self.log_output.clear()
            self.log_output.setPlainText(log_text)
            # 滚动到底部
            scrollbar = self.log_output.verticalScrollBar()
            if scrollbar:
                scrollbar.setValue(scrollbar.maximum())

    # 爬虫监控面板（可选功能）
    def setup_crawler_monitor_panel(self, parent_layout):
        """设置爬虫监控面板 - 可选功能"""
        # 这是一个可选面板，仅在需要时使用
        monitor_frame = QFrame()
        monitor_frame.setFrameShape(QFrame.StyledPanel)
        monitor_frame.setObjectName("card")
        
        monitor_layout = QVBoxLayout(monitor_frame)
        
        # 标题
        title_label = QLabel("爬虫监控面板")
        title_label.setObjectName("titleLabel")
        monitor_layout.addWidget(title_label)
        
        # 控制按钮
        btn_layout = QHBoxLayout()
        self.monitor_start_btn = QPushButton("启动监控")
        self.monitor_start_btn.clicked.connect(lambda: self.add_log_line("启动监控", "INFO"))
        btn_layout.addWidget(self.monitor_start_btn)
        
        self.monitor_stop_btn = QPushButton("停止监控")
        self.monitor_stop_btn.clicked.connect(lambda: self.add_log_line("停止监控", "WARNING"))
        btn_layout.addWidget(self.monitor_stop_btn)
        
        monitor_layout.addLayout(btn_layout)
        
        parent_layout.addWidget(monitor_frame)
        return monitor_frame


class MonitorLogPanel(QWidget):
    """向后兼容的日志面板"""
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.dashboard_log = DashboardLog(db, parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.dashboard_log)
    
    def add_log_line(self, message: str, level: str = "INFO"):
        """添加日志行"""
        if hasattr(self, 'dashboard_log'):
            self.dashboard_log.add_log_line(message, level)
    
    def clear_log(self):
        """清空日志"""
        if hasattr(self, 'dashboard_log'):
            self.dashboard_log.clear_log()