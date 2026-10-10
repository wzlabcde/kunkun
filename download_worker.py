"""后台下载线程模块"""
import subprocess
import sys
import os
from PyQt5.QtCore import QThread, pyqtSignal


class DownloadWorker(QThread):
    """Instagram 下载后台线程"""

    # 信号定义
    progress = pyqtSignal(str)      # 进度消息
    finished = pyqtSignal(bool, str)  # (成功, 消息)

    def __init__(self, username: str, cookies_path: str, output_path: str):
        super().__init__()
        self.username = username
        self.cookies_path = cookies_path
        self.output_path = output_path
        self._is_cancelled = False
        self.process = None

    def _resolve_gallery_dl(self) -> str:
        """冻结(打包)状态下优先使用随程序一起打包的 gallery-dl"""
        if getattr(sys, "frozen", False):
            base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
            bundled = os.path.join(base, "gallery-dl")
            if os.path.isfile(bundled):
                return bundled
        return "gallery-dl"

    def run(self):
        """执行下载任务"""
        try:
            url = f"https://www.instagram.com/{self.username}/saved/"

            cmd = [
                self._resolve_gallery_dl(),
                '--cookies', self.cookies_path,
                '-d', self.output_path,
                url
            ]

            self.progress.emit(f"开始下载: {url}")
            self.progress.emit(f"输出目录: {self.output_path}")
            self.progress.emit("-" * 50)

            # 使用 subprocess 执行 gallery-dl
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # 实时读取输出
            while True:
                if self._is_cancelled:
                    self.process.terminate()
                    self.progress.emit("下载已取消")
                    self.finished.emit(False, "用户取消")
                    return

                line = self.process.stdout.readline()
                if line:
                    self.progress.emit(line.strip())

                if self.process.poll() is not None:
                    break

            returncode = self.process.returncode

            if returncode == 0:
                self.progress.emit("-" * 50)
                self.progress.emit("下载完成!")
                self.finished.emit(True, "下载成功完成")
            else:
                self.progress.emit(f"错误代码: {returncode}")
                self.finished.emit(False, f"下载失败，错误代码: {returncode}")

        except FileNotFoundError:
            self.finished.emit(False, "找不到 gallery-dl，请确保已安装")
        except Exception as e:
            self.finished.emit(False, f"发生错误: {str(e)}")

    def cancel(self):
        """取消下载"""
        self._is_cancelled = True
        if self.process:
            self.process.terminate()
