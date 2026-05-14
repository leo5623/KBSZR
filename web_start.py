"""极享AI口播智能体 - Gradio Web应用"""
import os
import sys

# 确保项目根目录在路径中
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

os.chdir(project_root)

# 默认启动Gradio Web应用
from src.web.app import main

if __name__ == "__main__":
    main()