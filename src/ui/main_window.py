"""PyQt6主窗口 - 参考竞品界面设计"""
import asyncio
import sys
from pathlib import Path
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QThread, QSettings
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QComboBox, QSlider, QCheckBox,
    QGroupBox, QScrollArea, QStatusBar, QToolBar,
    QListWidget, QProgressBar, QFrame, QGridLayout,
    QSizePolicy, QSplitter, QMessageBox, QFileDialog,
    QTabWidget, QLineEdit, QInputDialog
)
from PyQt6.QtGui import QAction, QFont
from loguru import logger


class MainWindow(QMainWindow):
    """主窗口 - 口播数字人系统（参考竞品界面）"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("口播数字人系统 v1.0")
        self.setMinimumSize(1400, 900)

        # 状态
        self._current_avatar = None
        self._current_background = None
        self._current_bgm = None
        self._generated_video = None

        # 初始化UI
        self._init_ui()

        # 初始化业务模块
        self._init_business()

    def _init_business(self):
        """初始化业务模块"""
        try:
            from src.business.rewriter.router import RewriterRouter, RewriteConfig, RewriteMode
            from src.business.tts.router import TTSRouter, TTSConfig, TTSMode
            from src.business.digital_human.router import DigitalHumanRouter, DigitalHumanConfig, DigitalHumanMode
            from src.business.post_production.router import VideoProcessingRouter, VideoProcessingConfig

            # 初始化改写器
            self._rewriter = RewriterRouter(
                config=RewriteConfig(mode=RewriteMode.CLOUD)
            )

            # 初始化TTS
            self._tts_router = TTSRouter(
                config=TTSConfig(mode=TTSMode.CLOUD)
            )

            # 初始化数字人
            self._dh_router = DigitalHumanRouter(
                config=DigitalHumanConfig(mode=DigitalHumanMode.CLOUD)
            )

            # 初始化视频处理
            self._video_router = VideoProcessingRouter(
                config=VideoProcessingConfig()
            )

            logger.info("Business modules initialized")

        except Exception as e:
            logger.error(f"Failed to initialize business modules: {e}")
            self.statusbar.showMessage(f"初始化业务模块失败: {e}")

    def _init_ui(self):
        """初始化UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 左侧边栏（深色主题）
        left_panel = self._create_left_panel()
        main_layout.addWidget(left_panel, 0)

        # 中心区域
        center_panel = self._create_center_panel()
        main_layout.addWidget(center_panel, 1)

        # 右侧面板（标签页）
        right_panel = self._create_right_panel()
        main_layout.addWidget(right_panel, 0)

        # 顶部工具栏
        self._create_toolbar()

        # 底部状态栏
        self._create_statusbar()

    def _create_left_panel(self) -> QFrame:
        """左侧边栏（深色主题）"""
        frame = QFrame()
        frame.setObjectName("left_panel")
        frame.setMaximumWidth(200)
        frame.setMinimumWidth(180)
        frame.setStyleSheet("""
            QFrame#left_panel {
                background-color: #1e1e1e;
                color: white;
            }
        """)

        layout = QVBoxLayout(frame)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Logo区域
        logo_frame = QFrame()
        logo_frame.setStyleSheet("background-color: #1e1e1e; padding: 15px;")
        logo_layout = QVBoxLayout(logo_frame)
        logo_label = QLabel("口播数字人")
        logo_label.setStyleSheet("""
            color: #4CAF50;
            font-size: 18px;
            font-weight: bold;
        """)
        logo_layout.addWidget(logo_label)
        layout.addWidget(logo_frame)

        # 菜单按钮
        menu_items = [
            ("新建任务", self._on_new),
            ("素材库", self._on_material_library),
            ("文案库", self._on_copy_library),
            ("我的声音", self._on_voice_library),
            ("任务中心", self._on_task_center),
            ("设置", self._on_settings),
        ]

        for text, callback in menu_items:
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #cccccc;
                    text-align: left;
                    padding: 14px 20px;
                    border: none;
                    border-radius: 0;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #2d2d2d;
                    color: white;
                }
                QPushButton:pressed {
                    background-color: #3d3d3d;
                    color: #4CAF50;
                }
            """)
            btn.clicked.connect(callback)
            layout.addWidget(btn)

        layout.addStretch()

        # 底部设置
        bottom_frame = QFrame()
        bottom_frame.setStyleSheet("border-top: 1px solid #333; padding: 10px;")
        bottom_layout = QVBoxLayout(bottom_frame)
        bottom_layout.setSpacing(5)

        display_btn = QPushButton("显示设置")
        display_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888;
                text-align: left;
                padding: 8px 20px;
                border: none;
                font-size: 12px;
            }
            QPushButton:hover { color: white; }
        """)

        lang_btn = QPushButton("语言 / 皮肤")
        lang_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888;
                text-align: left;
                padding: 8px 20px;
                border: none;
                font-size: 12px;
            }
            QPushButton:hover { color: white; }
        """)

        bottom_layout.addWidget(display_btn)
        bottom_layout.addWidget(lang_btn)
        layout.addWidget(bottom_frame)

        return frame

    def _create_center_panel(self) -> QFrame:
        """中心区域"""
        frame = QFrame()
        frame.setStyleSheet("background-color: #2d2d2d;")

        layout = QVBoxLayout(frame)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # 视频预览区
        preview_group = QFrame()
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        # 比例切换按钮
        ratio_layout = QHBoxLayout()
        ratio_layout.addStretch()

        self.ratio_9_16 = QPushButton("9:16")
        self.ratio_16_9 = QPushButton("16:9")
        self.ratio_9_16.setCheckable(True)
        self.ratio_16_9.setCheckable(True)
        self.ratio_9_16.setChecked(True)

        for btn in [self.ratio_9_16, self.ratio_16_9]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3d3d3d;
                    color: #cccccc;
                    border: none;
                    padding: 6px 15px;
                    border-radius: 3px;
                    font-size: 12px;
                }
                QPushButton:checked {
                    background-color: #4CAF50;
                    color: white;
                }
                QPushButton:hover:checked {
                    background-color: #45a049;
                }
            """)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        ratio_layout.addWidget(self.ratio_9_16)
        ratio_layout.addWidget(self.ratio_16_9)
        preview_layout.addLayout(ratio_layout)

        # 视频预览标签
        self.preview_label = QLabel("选择数字人形象和背景后，这里将显示预览效果")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(380)
        self.preview_label.setStyleSheet("""
            background-color: #1a1a1a;
            color: #666;
            border: 1px solid #3d3d3d;
            border-radius: 5px;
        """)
        preview_layout.addWidget(self.preview_label)

        layout.addWidget(preview_group, 1)

        # 时间线区域
        timeline_frame = QFrame()
        timeline_frame.setMaximumHeight(70)
        timeline_frame.setStyleSheet("""
            background-color: #252525;
            border-radius: 5px;
            border: 1px solid #3d3d3d;
        """)
        timeline_layout = QHBoxLayout(timeline_frame)
        timeline_layout.setContentsMargins(10, 5, 10, 5)

        # 段落标签
        segment_label = QLabel("段落1: 开头介绍")
        segment_label.setStyleSheet("color: #888; font-size: 11px; padding: 3px 8px; background-color: #333; border-radius: 3px;")
        timeline_layout.addWidget(segment_label)

        segment_label2 = QLabel("段落2: 核心内容")
        segment_label2.setStyleSheet("color: #888; font-size: 11px; padding: 3px 8px; background-color: #333; border-radius: 3px;")
        timeline_layout.addWidget(segment_label2)

        segment_label3 = QLabel("段落3: 结尾引导")
        segment_label3.setStyleSheet("color: #888; font-size: 11px; padding: 3px 8px; background-color: #333; border-radius: 3px;")
        timeline_layout.addWidget(segment_label3)

        timeline_layout.addStretch()

        layout.addWidget(timeline_frame)

        # 文案输入区
        input_group = QFrame()
        input_group.setStyleSheet("""
            background-color: #252525;
            border-radius: 5px;
            border: 1px solid #3d3d3d;
        """)
        input_layout = QVBoxLayout(input_group)
        input_layout.setContentsMargins(10, 8, 10, 8)

        # 行业场景选择
        scene_layout = QHBoxLayout()
        scene_layout.addWidget(QLabel("行业:"))
        self.industry_select = QComboBox()
        self.industry_select.addItems(["通用", "美妆", "知识付费", "电商带货", "美食", "教育"])
        self.industry_select.setStyleSheet("""
            QComboBox {
                background-color: #3d3d3d;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
        """)
        scene_layout.addWidget(self.industry_select)

        scene_layout.addWidget(QLabel("场景:"))
        self.scenario_select = QComboBox()
        self.scenario_select.addItems(["种草安利", "干货分享", "产品介绍", "教程分享", "限时优惠"])
        self.scenario_select.setStyleSheet("""
            QComboBox {
                background-color: #3d3d3d;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
        """)
        scene_layout.addWidget(self.scenario_select)
        scene_layout.addStretch()
        input_layout.addLayout(scene_layout)

        self.copy_input = QTextEdit()
        self.copy_input.setPlaceholderText("在此输入口播文案，或者从链接解析...")
        self.copy_input.setMinimumHeight(80)
        self.copy_input.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 8px;
                font-size: 13px;
            }
        """)
        input_layout.addWidget(self.copy_input)

        # 操作按钮
        btn_layout = QHBoxLayout()

        self.preview_btn = QPushButton("预览效果")
        self.preview_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        self.preview_btn.clicked.connect(self._on_preview)

        self.rewrite_btn = QPushButton("文案改写")
        self.rewrite_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.rewrite_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #7B1FA2; }
        """)
        self.rewrite_btn.clicked.connect(self._on_rewrite)

        self.generate_btn = QPushButton("开始生成")
        self.generate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        self.generate_btn.clicked.connect(self._on_generate)

        self.distribute_btn = QPushButton("一键分发")
        self.distribute_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.distribute_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #F57C00; }
        """)
        self.distribute_btn.clicked.connect(self._on_distribute)

        btn_layout.addWidget(self.preview_btn)
        btn_layout.addWidget(self.rewrite_btn)
        btn_layout.addWidget(self.generate_btn)
        btn_layout.addWidget(self.distribute_btn)
        input_layout.addLayout(btn_layout)

        layout.addWidget(input_group)

        return frame

    def _create_right_panel(self) -> QFrame:
        """右侧面板（标签页）"""
        frame = QFrame()
        frame.setMaximumWidth(300)
        frame.setMinimumWidth(260)
        frame.setStyleSheet("background-color: #252525;")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标签页
        self.right_tabs = QTabWidget()
        self.right_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #252525;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #cccccc;
                padding: 10px 25px;
                border: none;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                background-color: #252525;
                color: #4CAF50;
                border-bottom: 2px solid #4CAF50;
            }
            QTabBar::tab:hover:!selected {
                background-color: #333;
            }
        """)

        # 数字人标签页
        avatar_tab = self._create_avatar_tab()
        self.right_tabs.addTab(avatar_tab, "数字人")

        # 背景标签页
        background_tab = self._create_background_tab()
        self.right_tabs.addTab(background_tab, "背景")

        # 音乐标签页
        music_tab = self._create_music_tab()
        self.right_tabs.addTab(music_tab, "音乐")

        layout.addWidget(self.right_tabs)

        return frame

    def _create_avatar_tab(self) -> QWidget:
        """数字人标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # 提示文字
        hint = QLabel("请先上传数字人形象")
        hint.setStyleSheet("color: #888; font-size: 12px; padding: 10px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        # 数字人列表
        self.avatar_list = QListWidget()
        self.avatar_list.setSpacing(5)
        self.avatar_list.addItems([
            "小美 - 青春活泼",
            "小雅 - 知性优雅",
            "小刚 - 阳光帅气",
            "老王 - 成熟稳重"
        ])
        self.avatar_list.setStyleSheet("""
            QListWidget {
                background-color: #1a1a1a;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 5px;
                color: #cccccc;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 3px;
            }
            QListWidget::item:selected {
                background-color: #4CAF50;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #333;
            }
        """)
        self.avatar_list.currentRowChanged.connect(self._on_avatar_changed)
        layout.addWidget(self.avatar_list)

        # 分类筛选
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("分类:"))
        self.avatar_filter = QComboBox()
        self.avatar_filter.addItems(["综合", "女生", "男生", "健身", "商务"])
        self.avatar_filter.setStyleSheet("""
            QComboBox {
                background-color: #333;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
        """)
        filter_layout.addWidget(self.avatar_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        layout.addStretch()

        return widget

    def _create_background_tab(self) -> QWidget:
        """背景标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # 背景列表
        self.background_list = QListWidget()
        self.background_list.setSpacing(5)
        self.background_list.addItems([
            "演播室默认",
            "光影变化",
            "蓝色科技感",
            "温馨家居",
            "户外风景",
            "抽象背景"
        ])
        self.background_list.setStyleSheet("""
            QListWidget {
                background-color: #1a1a1a;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 5px;
                color: #cccccc;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 3px;
            }
            QListWidget::item:selected {
                background-color: #4CAF50;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #333;
            }
        """)
        self.background_list.currentRowChanged.connect(self._on_background_changed)
        layout.addWidget(self.background_list)

        layout.addStretch()

        return widget

    def _create_music_tab(self) -> QWidget:
        """音乐标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # BGM列表
        self.bgm_list = QListWidget()
        self.bgm_list.setSpacing(5)
        self.bgm_list.addItems([
            "无",
            "流行节奏",
            "氛围音乐",
            "活力充沛",
            "轻柔钢琴",
            "企业宣传"
        ])
        self.bgm_list.setStyleSheet("""
            QListWidget {
                background-color: #1a1a1a;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 5px;
                color: #cccccc;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 3px;
            }
            QListWidget::item:selected {
                background-color: #4CAF50;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #333;
            }
        """)
        self.bgm_list.currentRowChanged.connect(self._on_bgm_changed)
        layout.addWidget(self.bgm_list)

        # 音量控制
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("音量:"))
        self.bgm_volume = QSlider(Qt.Orientation.Horizontal)
        self.bgm_volume.setRange(0, 100)
        self.bgm_volume.setValue(30)
        self.bgm_volume.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #3d3d3d;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background-color: #4CAF50;
                width: 12px;
                border-radius: 6px;
            }
            QSlider::sub-page:horizontal {
                background-color: #4CAF50;
                border-radius: 2px;
            }
        """)
        volume_layout.addWidget(self.bgm_volume)
        self.volume_label = QLabel("30%")
        self.volume_label.setStyleSheet("color: #888;")
        volume_layout.addWidget(self.volume_label)
        self.bgm_volume.valueChanged.connect(lambda v: self.volume_label.setText(f"{v}%"))
        layout.addLayout(volume_layout)

        layout.addStretch()

        return widget

    def _create_toolbar(self):
        """顶部工具栏"""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #252525;
                border: none;
                padding: 5px;
            }
        """)
        self.addToolBar(toolbar)

        # 新建
        new_action = QAction("新建", self)
        new_action.triggered.connect(self._on_new)
        toolbar.addAction(new_action)

        toolbar.addSeparator()

        # 导入文案
        import_action = QAction("导入文案", self)
        import_action.triggered.connect(self._on_import)
        toolbar.addAction(import_action)

        # 从链接解析
        link_action = QAction("从链接解析", self)
        link_action.triggered.connect(self._on_parse_link)
        toolbar.addAction(link_action)

        toolbar.addSeparator()

        # 我的作品
        works_action = QAction("我的作品", self)
        works_action.triggered.connect(self._on_works)
        toolbar.addAction(works_action)

        # 文案库
        copy_action = QAction("文案库", self)
        copy_action.triggered.connect(self._on_copy_library)
        toolbar.addAction(copy_action)

        # 我的声音
        voice_action = QAction("我的声音", self)
        voice_action.triggered.connect(self._on_voice)
        toolbar.addAction(voice_action)

        # 任务中心
        task_action = QAction("任务中心", self)
        task_action.triggered.connect(self._on_task_center)
        toolbar.addAction(task_action)

        toolbar.addSeparator()

        # 系统设置
        settings_action = QAction("系统设置", self)
        settings_action.triggered.connect(self._on_settings)
        toolbar.addAction(settings_action)

    def _create_statusbar(self):
        """底部状态栏"""
        self.statusbar = QStatusBar()
        self.statusbar.setStyleSheet("""
            QStatusBar {
                background-color: #1e1e1e;
                color: #cccccc;
                border-top: 1px solid #333;
            }
        """)
        self.setStatusBar(self.statusbar)

        # 状态标签
        self.status_avatar = QLabel("数字人: 未选择")
        self.status_avatar.setStyleSheet("color: #888; padding: 0 10px;")
        self.statusbar.addPermanentWidget(self.status_avatar)

        separator1 = QLabel("|")
        separator1.setStyleSheet("color: #555;")
        self.statusbar.addPermanentWidget(separator1)

        self.status_background = QLabel("背景: 未选择")
        self.status_background.setStyleSheet("color: #888; padding: 0 10px;")
        self.statusbar.addPermanentWidget(self.status_background)

        separator2 = QLabel("|")
        separator2.setStyleSheet("color: #555;")
        self.statusbar.addPermanentWidget(separator2)

        self.status_music = QLabel("音乐: 无")
        self.status_music.setStyleSheet("color: #888; padding: 0 10px;")
        self.statusbar.addPermanentWidget(self.status_music)

        self.statusbar.addPermanentWidget(QLabel("     "))

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(150)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #333;
                border-radius: 3px;
                text-align: center;
                color: #cccccc;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        self.statusbar.addPermanentWidget(self.progress_bar)

        # 取消按钮
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
                margin-left: 10px;
            }
            QPushButton:hover { background-color: #666; }
        """)
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.statusbar.addPermanentWidget(self.cancel_btn)

    def _on_avatar_changed(self, index):
        """选择数字人形象"""
        if index >= 0:
            self._current_avatar = self.avatar_list.currentItem().text()
            self.status_avatar.setText(f"数字人: {self._current_avatar}")
            self.status_avatar.setStyleSheet("color: #4CAF50; padding: 0 10px;")

    def _on_background_changed(self, index):
        """选择背景"""
        if index >= 0:
            self._current_background = self.background_list.currentItem().text()
            self.status_background.setText(f"背景: {self._current_background}")
            self.status_background.setStyleSheet("color: #4CAF50; padding: 0 10px;")

    def _on_bgm_changed(self, index):
        """选择BGM"""
        if index >= 0:
            self._current_bgm = self.bgm_list.currentItem().text()
            self.status_music.setText(f"音乐: {self._current_bgm}")
            self.status_music.setStyleSheet("color: #4CAF50; padding: 0 10px;")

    def _on_new(self):
        """新建项目"""
        try:
            self.copy_input.clear()
            if self.avatar_list:
                self.avatar_list.setCurrentRow(-1)
            if self.background_list:
                self.background_list.setCurrentRow(-1)
            if self.bgm_list:
                self.bgm_list.setCurrentRow(0)
            self._current_avatar = None
            self._current_background = None
            self._current_bgm = "无"
            self.progress_bar.setValue(0)

            if hasattr(self, 'status_avatar') and self.status_avatar:
                self.status_avatar.setText("数字人: 未选择")
                self.status_avatar.setStyleSheet("color: #888; padding: 0 10px;")
            if hasattr(self, 'status_background') and self.status_background:
                self.status_background.setText("背景: 未选择")
                self.status_background.setStyleSheet("color: #888; padding: 0 10px;")
            if hasattr(self, 'status_music') and self.status_music:
                self.status_music.setText("音乐: 无")
                self.status_music.setStyleSheet("color: #888; padding: 0 10px;")

            self.statusbar.showMessage("已新建项目", 3000)
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, "错误", f"新建项目失败: {str(e)}")

    def _on_preview(self):
        """预览效果"""
        text = self.copy_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请先输入文案")
            return

        parts = []
        parts.append(f"行业: {self.industry_select.currentText()}")
        parts.append(f"场景: {self.scenario_select.currentText()}")
        if self._current_avatar:
            parts.append(f"数字人: {self._current_avatar}")
        if self._current_background:
            parts.append(f"背景: {self._current_background}")
        if self._current_bgm:
            parts.append(f"音乐: {self._current_bgm}")
        parts.append(f"\n文案预览 ({len(text)}字):\n{text[:200]}{'...' if len(text) > 200 else ''}")
        QMessageBox.information(self, "预览", "\n".join(parts))

    def _on_distribute(self):
        """一键分发"""
        text = self.copy_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请先生成视频后再分发")
            return
        QMessageBox.information(self, "分发", "分发功能开发中\n\n支持的平台：抖音、快手、小红书、视频号")

    def _on_material_library(self):
        """素材库"""
        from src.ui.dialogs import MaterialDialog
        dialog = MaterialDialog(self)
        dialog.exec()

    def _on_copy_library(self):
        """文案库"""
        from src.ui.dialogs import CopyLibraryDialog
        dialog = CopyLibraryDialog(self)
        dialog.exec()

    def _on_voice_library(self):
        """我的声音"""
        self._open_voice_dialog()

    def _on_works(self):
        """我的作品"""
        from src.ui.dialogs import WorksDialog
        dialog = WorksDialog(self)
        dialog.exec()

    def _on_voice(self):
        """我的声音（工具栏）"""
        self._open_voice_dialog()

    def _open_voice_dialog(self):
        """打开声音管理窗口"""
        from src.ui.voice_dialog import VoiceDialog
        dialog = VoiceDialog(self)
        dialog.exec()

    def _on_task_center(self):
        """任务中心"""
        from src.ui.dialogs import TaskCenterDialog
        dialog = TaskCenterDialog(self)
        dialog.exec()

    def _on_settings(self):
        """打开设置对话框"""
        from src.ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        dialog.exec()

    def _on_import(self):
        """导入文案"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入文案", "", "文本文件 (*.txt);;所有文件 (*)"
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.copy_input.setPlainText(content)
                self.statusbar.showMessage(f"已导入文案: {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "导入失败", str(e))

    def _on_parse_link(self):
        """从链接解析"""
        link, ok = QInputDialog.getText(self, "链接解析", "请输入要解析的链接:")
        if ok and link:
            self.statusbar.showMessage("正在解析链接...")
            self._parse_link_async(link)

    def _parse_link_async(self, link: str):
        """异步解析链接（使用QThread确保UI线程安全）"""
        from PyQt6.QtCore import QThread, pyqtSignal, QObject

        class ParseWorker(QObject):
            finished = pyqtSignal(object)

            def run(self):
                try:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        from src.browser.link_parser import LinkParser
                        parser = LinkParser()
                        result = loop.run_until_complete(parser.parse(link))
                        loop.run_until_complete(parser.close())
                        self.finished.emit(result)
                    finally:
                        loop.close()
                except Exception as e:
                    self.finished.emit(e)

        self._parse_thread = QThread()
        self._parse_worker = ParseWorker()
        self._parse_worker.moveToThread(self._parse_thread)
        self._parse_thread.started.connect(self._parse_worker.run)
        self._parse_worker.finished.connect(self._on_parse_done)
        self._parse_worker.finished.connect(self._parse_thread.quit)
        self._parse_worker.finished.connect(self._parse_worker.deleteLater)
        self._parse_thread.finished.connect(self._parse_thread.deleteLater)
        self._parse_thread.start()

    def _on_parse_done(self, result):
        """解析完成回调（主线程）"""
        if isinstance(result, Exception):
            QMessageBox.warning(self, "解析失败", str(result))
            self.statusbar.showMessage("解析失败")
            return

        if result and result.success:
            self.copy_input.setPlainText(result.text)
            self.statusbar.showMessage(f"解析成功 ({result.platform})")
        else:
            error_msg = result.error if result else "解析失败，请确认链接是否正确"
            QMessageBox.warning(self, "解析失败", error_msg)
            self.statusbar.showMessage("解析失败")

    def _on_rewrite(self):
        """文案改写"""
        text = self.copy_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请先输入文案")
            return

        self.rewrite_btn.setEnabled(False)
        self.statusbar.showMessage("正在改写文案...")

        industry_map = {"通用": None, "美妆": "beauty", "知识付费": "knowledge",
                        "电商带货": "ecommerce", "美食": "food", "教育": "education"}
        industry = industry_map.get(self.industry_select.currentText())
        scenario = self.scenario_select.currentText()

        from PyQt6.QtCore import QThread, QObject, pyqtSignal

        class RewriteWorker(QObject):
            finished = pyqtSignal(object)

            def __init__(self, text, industry, scenario):
                super().__init__()
                self.text = text
                self.industry = industry
                self.scenario = scenario

            def run(self):
                try:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        from src.business.rewriter.router import (
                            RewriterRouter, RewriteConfig, RewriteMode, RewriteRequest, RewriteResponse
                        )
                        config = RewriteConfig(mode=RewriteMode.AUTO)
                        router = RewriterRouter(config=config)

                        # 从设置读取云端配置
                        settings = QSettings("KBSZR", "config")
                        provider = settings.value("rewriter/provider", "tongyi")

                        default_models = {
                            "tongyi": "qwen-max",
                            "openai": "gpt-4o",
                            "claude": "claude-3-5-sonnet",
                            "deepseek": "deepseek-chat",
                            "doubao": "doubao-pro",
                        }
                        default_model = default_models.get(provider, "gpt-4o")
                        api_key = settings.value(f"api/{provider}_key", "")
                        model = settings.value(f"api/{provider}_model", default_model)

                        cloud_config = {
                            "provider": provider,
                            provider: {
                                "api_key": api_key,
                                "model": model,
                            }
                        }

                        if not api_key:
                            self.finished.emit(RewriteResponse(
                                success=False,
                                error=f"{provider} API Key 未配置，请在系统设置中填写",
                            ))
                            return

                        loop.run_until_complete(router.initialize(cloud_config))

                        request = RewriteRequest(
                            text=self.text,
                            industry=self.industry,
                            scenario=self.scenario,
                        )
                        response = loop.run_until_complete(router.rewrite(request))
                        loop.run_until_complete(router.close())
                        self.finished.emit(response)
                    finally:
                        loop.close()
                except Exception as e:
                    self.finished.emit(e)

        self._rewrite_thread = QThread()
        self._rewrite_worker = RewriteWorker(text, industry, scenario)
        self._rewrite_worker.moveToThread(self._rewrite_thread)
        self._rewrite_thread.started.connect(self._rewrite_worker.run)
        self._rewrite_worker.finished.connect(self._on_rewrite_done)
        self._rewrite_worker.finished.connect(self._rewrite_thread.quit)
        self._rewrite_worker.finished.connect(self._rewrite_worker.deleteLater)
        self._rewrite_thread.finished.connect(self._rewrite_thread.deleteLater)
        self._rewrite_thread.start()

    def _on_rewrite_done(self, result):
        """改写完成回调"""
        self.rewrite_btn.setEnabled(True)

        if isinstance(result, Exception):
            QMessageBox.warning(self, "改写失败", f"发生异常: {result}")
            self.statusbar.showMessage("改写失败")
            return

        if result.success:
            self.copy_input.setPlainText(result.rewritten_text)
            self.statusbar.showMessage(f"改写完成（{result.mode} - {result.provider}）")
        else:
            QMessageBox.warning(self, "改写失败", result.error or "未知错误")
            self.statusbar.showMessage("改写失败")

    def _on_generate(self):
        """开始生成"""
        text = self.copy_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请先输入文案")
            return

        self.generate_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.statusbar.showMessage("正在生成...")

        # 启动后台任务
        async def generate():
            try:
                for i in range(10, 101, 10):
                    await asyncio.sleep(0.3)
                    self.progress_bar.setValue(i)

                return {"success": True, "video_path": "output.mp4"}

            except Exception as e:
                return {"success": False, "error": str(e)}

        def on_finished(result):
            self.generate_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)

            if result["success"]:
                self._generated_video = result.get("video_path")
                self.statusbar.showMessage("生成完成")
                QMessageBox.information(self, "成功", "视频生成完成！")
            else:
                self.statusbar.showMessage("生成失败")
                QMessageBox.warning(self, "失败", result.get("error", "未知错误"))

        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(generate())
            finally:
                loop.close()
            return result

        import threading
        thread = threading.Thread(target=lambda: on_finished(run_async()))
        thread.start()

    def _on_cancel(self):
        """取消生成"""
        self.generate_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.statusbar.showMessage("已取消", 3000)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
