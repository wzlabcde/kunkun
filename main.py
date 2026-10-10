"""Instagram 收藏下载器 - 主程序入口"""
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from downloader_widget import DownloaderWidget


def main():
    app = QApplication(sys.argv)

    # 设置全局字体（macOS 无微软雅黑，用苹方）
    if sys.platform == "darwin":
        font = QFont("PingFang SC", 10)
    else:
        font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    # 设置样式
    app.setStyle("Fusion")

    window = DownloaderWidget()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
