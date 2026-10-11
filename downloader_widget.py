"""主窗口 UI 模块"""
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QTextEdit, QLabel,
    QFileDialog, QMessageBox, QGroupBox
)
from PyQt5.QtCore import Qt
from download_worker import DownloadWorker


class DownloaderWidget(QWidget):
    """Instagram 下载器主窗口"""

    def __init__(self):
        super().__init__()
        self.worker = None
        self._init_ui()

    def _init_ui(self):
        """初始化界面"""
        self.setWindowTitle("坤坤下载器")
        self.setMinimumSize(600, 500)

        layout = QVBoxLayout()

        # 设置组
        settings_group = QGroupBox("下载设置")
        form_layout = QFormLayout()

        # 用户名输入
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("输入 Instagram 用户名")
        form_layout.addRow("用户名:", self.username_input)

        # Cookies 文件路径
        cookies_layout = QHBoxLayout()
        self.cookies_input = QLineEdit()
        self.cookies_input.setPlaceholderText("选择 cookies.txt 文件")
        cookies_btn = QPushButton("浏览...")
        cookies_btn.clicked.connect(self._select_cookies)
        cookies_layout.addWidget(self.cookies_input)
        cookies_layout.addWidget(cookies_btn)
        form_layout.addRow("Cookies 文件:", cookies_layout)

        # 输出文件夹路径
        output_layout = QHBoxLayout()
        self.output_input = QLineEdit()
        self.output_input.setPlaceholderText("选择输出文件夹")
        self.output_input.setText(os.path.expanduser("~/Downloads/Instagram"))
        output_btn = QPushButton("浏览...")
        output_btn.clicked.connect(self._select_output)
        output_layout.addWidget(self.output_input)
        output_layout.addWidget(output_btn)
        form_layout.addRow("输出文件夹:", output_layout)

        settings_group.setLayout(form_layout)
        layout.addWidget(settings_group)

        # 按钮区域
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("开始下载")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        self.start_btn.clicked.connect(self._start_download)

        self.stop_btn = QPushButton("停止下载")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #da190b; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        self.stop_btn.clicked.connect(self._stop_download)

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

        # 日志显示区域
        log_label = QLabel("下载日志:")
        layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: Consolas, monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.log_text)

        self.setLayout(layout)

    def _select_cookies(self):
        """选择 cookies 文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择 Cookies 文件", "",
            "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.cookies_input.setText(file_path)

    def _select_output(self):
        """选择输出文件夹，并预扫描已有媒体数"""
        folder_path = QFileDialog.getExistingDirectory(
            self, "选择输出文件夹"
        )
        if folder_path:
            self.output_input.setText(folder_path)
            existing = self._count_media_files(folder_path)
            self._log(f"[检测] 输出目录已有 {existing} 个媒体文件（将只下载增量）")

    @staticmethod
    def _count_media_files(path: str) -> int:
        """递归统计目录下图片+视频数量"""
        exts = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp',
                '.mp4', '.webm', '.mov', '.mkv', '.avi'}
        count = 0
        for root, _, files in os.walk(path):
            for f in files:
                if os.path.splitext(f)[1].lower() in exts:
                    count += 1
        return count

    def _log(self, message: str):
        """添加日志消息"""
        self.log_text.append(message)
        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _validate_inputs(self) -> bool:
        """验证输入"""
        username = self.username_input.text().strip()
        cookies_path = self.cookies_input.text().strip()
        output_path = self.output_input.text().strip()

        if not username:
            QMessageBox.warning(self, "错误", "请输入 Instagram 用户名")
            return False

        if not cookies_path or not os.path.isfile(cookies_path):
            QMessageBox.warning(self, "错误", "请选择有效的 cookies 文件")
            return False

        if not output_path:
            QMessageBox.warning(self, "错误", "请选择输出文件夹")
            return False

        # 创建输出目录（如果不存在）
        os.makedirs(output_path, exist_ok=True)

        return True

    def _start_download(self):
        """开始下载"""
        if not self._validate_inputs():
            return

        username = self.username_input.text().strip()
        cookies_path = self.cookies_input.text().strip()
        output_path = self.output_input.text().strip()

        # 清空日志
        self.log_text.clear()

        # 更新按钮状态
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        # 记录下载前的媒体数，完成后计算增量
        self._media_before = self._count_media_files(output_path)

        # 创建并启动工作线程
        self.worker = DownloadWorker(username, cookies_path, output_path)
        self.worker.progress.connect(self._log)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _stop_download(self):
        """停止下载"""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self._log("正在停止下载...")

    def _on_finished(self, success: bool, message: str):
        """下载完成回调"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

        if success:
            output_path = self.output_input.text().strip()
            media_after = self._count_media_files(output_path)
            new_count = media_after - getattr(self, '_media_before', 0)
            summary = f"{message} | 已有 {self._media_before} 个，本次新增 {new_count} 个，当前共 {media_after} 个"
            self._log(f"\n✓ {summary}")
            QMessageBox.information(self, "成功", summary)
        else:
            self._log(f"\n✗ {message}")
            if "用户取消" not in message:
                QMessageBox.warning(self, "失败", message)

        self.worker = None
