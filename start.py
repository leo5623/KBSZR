"""KBSZR 启动入口"""
import sys
import os

# 确保项目根目录在路径中
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

os.chdir(project_root)

# 默认启动赛博朋克风格UI
# 可选: "cyberpunk" (默认), "classic", 或 "web" (Gradio)
UI_MODE = os.environ.get("KBSZR_UI", "cyberpunk")

if UI_MODE == "cyberpunk":
    from src.ui.cyberpunk.main_window import main
elif UI_MODE == "web":
    from src.web.app import main
else:
    from src.ui.jixiang_main_window import main

if __name__ == "__main__":
    main()
