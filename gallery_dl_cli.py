"""gallery-dl 命令行入口，供 CI 打包成独立可执行文件并内置进 .app"""
import sys

from gallery_dl import main

if __name__ == "__main__":
    sys.exit(main())
