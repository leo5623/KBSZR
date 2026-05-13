"""KBSZR 启动入口"""
import sys
import os

# 确保项目根目录在路径中
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

os.chdir(project_root)

from src.ui.jixiang_main_window import main

if __name__ == "__main__":
    main()
