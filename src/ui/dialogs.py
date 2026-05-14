"""素材/文案/作品/任务中心 通用浏览窗口"""
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QMessageBox, QTextEdit, QGroupBox, QTabWidget, QWidget,
)
from PyQt6.QtCore import Qt
from loguru import logger


def _get_data_dir() -> Path:
    """获取数据目录（项目根目录下的data文件夹）"""
    # 获取项目根目录（src/ui/dialogs.py -> 项目根目录）
    project_root = Path(__file__).parent.parent.parent
    return project_root / "data"


class MaterialDialog(QDialog):
    """素材库窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("素材库")
        self.setMinimumSize(600, 450)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        # 形象素材
        avatar_tab = QWidget()
        avatar_layout = QVBoxLayout(avatar_tab)
        avatar_list = QListWidget()
        avatar_list.setStyleSheet("QListWidget{background:#1a1a1a;color:#ccc;border:1px solid #333;border-radius:4px;padding:5px;}")
        avatars_dir = _get_data_dir() / "avatars"
        for f in sorted(avatars_dir.iterdir()) if avatars_dir.exists() else []:
            avatar_list.addItem(f.name)
        if avatar_list.count() == 0:
            avatar_list.addItem("（暂无素材，请导入）")
        avatar_layout.addWidget(avatar_list)
        tabs.addTab(avatar_tab, "形象")

        # 背景素材
        bg_tab = QWidget()
        bg_layout = QVBoxLayout(bg_tab)
        bg_list = QListWidget()
        bg_list.setStyleSheet("QListWidget{background:#1a1a1a;color:#ccc;border:1px solid #333;border-radius:4px;padding:5px;}")
        backgrounds_dir = _get_data_dir() / "backgrounds"
        for f in sorted(backgrounds_dir.iterdir()) if backgrounds_dir.exists() else []:
            bg_list.addItem(f.name)
        if bg_list.count() == 0:
            bg_list.addItem("（暂无素材，请导入）")
        bg_layout.addWidget(bg_list)
        tabs.addTab(bg_tab, "背景")

        # BGM
        bgm_tab = QWidget()
        bgm_layout = QVBoxLayout(bgm_tab)
        bgm_list = QListWidget()
        bgm_list.setStyleSheet("QListWidget{background:#1a1a1a;color:#ccc;border:1px solid #333;border-radius:4px;padding:5px;}")
        bgm_dir = _get_data_dir() / "bgm"
        for f in sorted(bgm_dir.iterdir()) if bgm_dir.exists() else []:
            bgm_list.addItem(f.name)
        if bgm_list.count() == 0:
            bgm_list.addItem("（暂无素材，请导入）")
        bgm_layout.addWidget(bgm_list)
        tabs.addTab(bgm_tab, "音乐")

        layout.addWidget(tabs)
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("background:#555;color:white;border:none;padding:8px 24px;border-radius:4px;")
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)


class CopyLibraryDialog(QDialog):
    """文案库窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("文案库")
        self.setMinimumSize(650, 500)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        # 场景模板
        template_tab = QWidget()
        tm_layout = QVBoxLayout(template_tab)

        from src.business.rewriter.scenario_manager import get_scenario_manager
        mgr = get_scenario_manager()
        industries = mgr.list_industries()

        import_list = QListWidget()
        import_list.setStyleSheet("QListWidget{background:#1a1a1a;color:#ccc;border:1px solid #333;border-radius:4px;padding:5px;}")
        for ind in industries:
            scenarios = mgr.list_scenarios(ind["id"])
            for sc in scenarios:
                import_list.addItem(f"[{ind['name']}] {sc['name']} — {sc['description']}")
        if import_list.count() == 0:
            import_list.addItem("（暂无模板）")
        tm_layout.addWidget(import_list)
        tabs.addTab(template_tab, "场景模板")

        # 已保存文案
        saved_tab = QWidget()
        sv_layout = QVBoxLayout(saved_tab)
        saved_list = QListWidget()
        saved_list.setStyleSheet("QListWidget{background:#1a1a1a;color:#ccc;border:1px solid #333;border-radius:4px;padding:5px;}")
        saved_list.addItem("（文案保存功能开发中）")
        sv_layout.addWidget(saved_list)
        tabs.addTab(saved_tab, "已保存")

        layout.addWidget(tabs)
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("background:#555;color:white;border:none;padding:8px 24px;border-radius:4px;")
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)


class WorksDialog(QDialog):
    """我的作品窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("我的作品")
        self.setMinimumSize(600, 450)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        output_list = QListWidget()
        output_list.setStyleSheet("QListWidget{background:#1a1a1a;color:#ccc;border:1px solid #333;border-radius:4px;padding:5px;}")
        output_dir = _get_data_dir() / "output"
        if output_dir.exists():
            for f in sorted(output_dir.iterdir()):
                size = f.stat().st_size
                output_list.addItem(f"{f.name}  ({size / 1024:.1f} KB)")
        if output_list.count() == 0:
            output_list.addItem("（暂无作品）")
        layout.addWidget(output_list)

        btn_layout = QHBoxLayout()
        open_btn = QPushButton("打开所在文件夹")
        open_btn.clicked.connect(lambda: self._on_open_folder(output_dir))
        open_btn.setStyleSheet("background:#4CAF50;color:white;border:none;padding:8px 16px;border-radius:4px;")

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("background:#555;color:white;border:none;padding:8px 24px;border-radius:4px;")

        btn_layout.addWidget(open_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _on_open_folder(self, path: Path):
        import subprocess, platform, os
        try:
            if platform.system() == "Windows":
                os.startfile(str(path))
            else:
                subprocess.run(["xdg-open", str(path)])
        except Exception as e:
            QMessageBox.warning(self, "打开失败", str(e))


class TaskCenterDialog(QDialog):
    """任务中心窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("任务中心")
        self.setMinimumSize(600, 400)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 状态
        status_group = QGroupBox("队列状态")
        status_layout = QVBoxLayout(status_group)
        status_label = QLabel("任务队列运行正常（空闲中）")
        status_label.setStyleSheet("color: #4CAF50; font-size: 14px; padding: 10px;")
        status_layout.addWidget(status_label)
        layout.addWidget(status_group)

        # 任务列表
        task_group = QGroupBox("最近任务")
        task_layout = QVBoxLayout(task_group)
        task_list = QListWidget()
        task_list.setStyleSheet("QListWidget{background:#1a1a1a;color:#ccc;border:1px solid #333;border-radius:4px;padding:5px;}")
        task_list.addItem("（暂无任务记录）")
        task_layout.addWidget(task_list)
        layout.addWidget(task_group)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("background:#555;color:white;border:none;padding:8px 24px;border-radius:4px;")
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
