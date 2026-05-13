"""极享 AI 风格 UI - 主窗口"""
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
    QTabWidget, QLineEdit, QInputDialog, QStackedWidget,
    QListWidgetItem
)
from PyQt6.QtGui import QAction, QFont, QPainter, QLinearGradient, QColor
from loguru import logger

# 极享 AI 风格颜色常量
COLORS = {
    "PRIMARY": "#8B5CF6",           # 紫色主色
    "PRIMARY_LIGHT": "#A78BFA",     # 浅紫色
    "PRIMARY_GRADIENT_START": "#8B5CF6",
    "PRIMARY_GRADIENT_END": "#A78BFA",
    "BACKGROUND": "#F9FAFB",         # 浅灰背景
    "WHITE": "#FFFFFF",
    "TEXT_PRIMARY": "#1F2937",      # 深灰文字
    "TEXT_SECONDARY": "#6B7280",    # 次级文字
    "BORDER": "#E5E7EB",           # 边框色
    "CARD_SHADOW": "rgba(0,0,0,0.08)",
    "NAV_HOVER": "#F3F4F6",        # 导航悬停
    "SUCCESS": "#10B981",           # 成功绿
    "WARNING": "#F59E0B",           # 警告黄
    "ERROR": "#EF4444",            # 错误红
}


class JixiangMainWindow(QMainWindow):
    """
    极享 AI 口播智能体 - 主窗口

    布局：
    - 左侧：导航栏（200px固定）
    - 顶部：标题栏（紫色渐变，60px）
    - 中心：内容区（白色背景）
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("极享 AI 口播智能体")
        self.setMinimumSize(1400, 900)
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['BACKGROUND']};
            }}
            QPushButton {{
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['NAV_HOVER']};
            }}
            QLabel {{
                color: {COLORS['TEXT_PRIMARY']};
            }}
            QInputDialog {{
                background-color: {COLORS['WHITE']};
            }}
            QInputDialog QLineEdit {{
                background-color: {COLORS['WHITE']};
                color: {COLORS['TEXT_PRIMARY']};
                border: 1px solid {COLORS['BORDER']};
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
            }}
            QInputDialog QPushButton {{
                background-color: {COLORS['PRIMARY']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }}
            QInputDialog QPushButton:hover {{
                background-color: #7C3AED;
            }}
            QMessageBox {{
                background-color: {COLORS['WHITE']};
            }}
            QMessageBox QLabel {{
                color: {COLORS['TEXT_PRIMARY']};
                font-size: 14px;
            }}
            QMessageBox QPushButton {{
                background-color: {COLORS['PRIMARY']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                min-width: 80px;
            }}
            QMessageBox QPushButton:hover {{
                background-color: #7C3AED;
            }}
            QFileDialog {{
                background-color: {COLORS['WHITE']};
            }}
            QFileDialog QLabel {{
                color: {COLORS['TEXT_PRIMARY']};
            }}
        """)

        self._current_view = "video_creation"
        self._init_ui()

    def _init_ui(self):
        """初始化 UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 左侧导航栏
        nav_panel = self._create_nav_panel()
        main_layout.addWidget(nav_panel)

        # 右侧内容区
        content_panel = self._create_content_panel()
        main_layout.addWidget(content_panel, 1)

        # 顶部标题栏（通过 setMenuBar 方式）
        self._create_title_bar()

        # 底部状态栏
        self.statusbar = QStatusBar()
        self.statusbar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {COLORS['WHITE']};
                color: {COLORS['TEXT_SECONDARY']};
                border-top: 1px solid {COLORS['BORDER']};
            }}
        """)
        self.setStatusBar(self.statusbar)

    def _create_nav_panel(self) -> QFrame:
        """创建左侧导航栏"""
        frame = QFrame()
        frame.setObjectName("nav_panel")
        frame.setFixedWidth(220)
        frame.setStyleSheet(f"""
            QFrame#nav_panel {{
                background-color: {COLORS['WHITE']};
                border-right: 1px solid {COLORS['BORDER']};
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Logo 区域
        logo_frame = QFrame()
        logo_frame.setFixedHeight(70)
        logo_frame.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS['PRIMARY_GRADIENT_START']},
                stop:1 {COLORS['PRIMARY_GRADIENT_END']});
            border-bottom: 1px solid {COLORS['BORDER']};
        """)
        logo_layout = QHBoxLayout(logo_frame)
        logo_layout.setContentsMargins(20, 0, 0, 0)

        logo_label = QLabel("极享 AI")
        logo_label.setStyleSheet("""
            color: white;
            font-size: 20px;
            font-weight: bold;
        """)
        logo_layout.addWidget(logo_label)
        logo_layout.addStretch()
        layout.addWidget(logo_frame)

        # 导航菜单（7个核心功能入口）
        nav_items = [
            ("首页", "home", "🏠"),
            ("视频创作", "video_creation", "🎬"),
            ("数字人库", "digital_human", "👤"),
            ("音色库", "voice_library", "🎙️"),
            ("字幕模板", "subtitle_template", "📝"),
            ("分镜素材", "storyboard", "🎞️"),
            ("发布账号", "accounts", "📱"),
            ("会员中心", "membership", "💎"),
            ("API设置", "api_settings", "⚙️"),
        ]

        nav_container = QWidget()
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setSpacing(4)
        nav_layout.setContentsMargins(12, 20, 12, 0)

        self._nav_buttons = {}
        for text, view_id, icon in nav_items:
            btn = self._create_nav_button(text, icon, view_id)
            self._nav_buttons[view_id] = btn
            nav_layout.addWidget(btn)

        nav_layout.addStretch()
        layout.addWidget(nav_container)

        # 默认选中首页
        self._nav_buttons["home"].setProperty("selected", True)
        self._nav_buttons["home"].setStyleSheet(self._get_nav_button_style(selected=True))

        return frame

    def _create_nav_button(self, text: str, icon: str, view_id: str) -> QPushButton:
        """创建导航按钮"""
        btn = QPushButton(f"  {icon}  {text}")
        btn.setObjectName(f"nav_btn_{view_id}")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(self._get_nav_button_style())
        btn.clicked.connect(lambda: self._switch_view(view_id))
        return btn

    def _get_nav_button_style(self, selected: bool = False) -> str:
        """获取导航按钮样式"""
        if selected:
            return f"""
                QPushButton {{
                    background-color: {COLORS['PRIMARY']};
                    color: white;
                    text-align: left;
                    padding: 12px 16px;
                    border-radius: 8px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['PRIMARY']};
                }}
            """
        else:
            return f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLORS['TEXT_SECONDARY']};
                    text-align: left;
                    padding: 12px 16px;
                    border-radius: 8px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['NAV_HOVER']};
                    color: {COLORS['PRIMARY']};
                }}
            """

    def _create_content_panel(self) -> QWidget:
        """创建内容面板"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部标题栏
        title_bar = self._create_title_bar_widget()
        layout.addWidget(title_bar)

        # 内容区域（堆叠窗口）
        self._view_stack = QStackedWidget()
        layout.addWidget(self._view_stack, 1)

        # 创建各视图
        self._views = {
            "home": self._create_home_view(),
            "video_creation": self._create_video_creation_view(),
            "digital_human": self._create_digital_human_view(),
            "voice_library": self._create_voice_library_view(),
            "subtitle_template": self._create_subtitle_template_view(),
            "storyboard": self._create_storyboard_view(),
            "accounts": self._create_accounts_view(),
            "membership": self._create_membership_view(),
            "api_settings": self._create_api_settings_view(),
        }

        for view_id, view in self._views.items():
            self._view_stack.addWidget(view)

        return container

    def _create_title_bar_widget(self) -> QFrame:
        """创建标题栏"""
        frame = QFrame()
        frame.setFixedHeight(60)
        frame.setStyleSheet(f"""
            background-color: {COLORS['WHITE']};
            border-bottom: 1px solid {COLORS['BORDER']};
        """)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(24, 0, 24, 0)

        # 页面标题
        self._page_title = QLabel("视频创作")
        self._page_title.setStyleSheet(f"""
            color: {COLORS['TEXT_PRIMARY']};
            font-size: 18px;
            font-weight: 600;
        """)
        layout.addWidget(self._page_title)

        layout.addStretch()

        # 顶部按钮
        btn_style = f"""
            QPushButton {{
                background-color: {COLORS['BACKGROUND']};
                color: {COLORS['TEXT_PRIMARY']};
                border: 1px solid {COLORS['BORDER']};
                border-radius: 8px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                border-color: {COLORS['PRIMARY']};
                color: {COLORS['PRIMARY']};
            }}
        """

        download_btn = QPushButton("下载客户端")
        download_btn.setStyleSheet(btn_style)
        layout.addWidget(download_btn)

        create_btn = QPushButton("立即创作")
        create_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['PRIMARY_GRADIENT_START']},
                    stop:1 {COLORS['PRIMARY_GRADIENT_END']});
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """)
        layout.addWidget(create_btn)

        return frame

    def _create_video_creation_view(self) -> QWidget:
        """创建视频创作视图 - 左右对比布局"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # 左侧：原文案输入区
        left_panel = self._create_text_input_panel("原文案输入")
        layout.addWidget(left_panel, 1)

        # 中间：操作按钮
        center_panel = self._create_operation_panel()
        layout.addWidget(center_panel, 0)

        # 右侧：仿写文案输出区
        right_panel = self._create_text_output_panel("仿写文案")
        layout.addWidget(right_panel, 1)

        return widget

    def _create_text_input_panel(self, title: str) -> QFrame:
        """创建文案输入面板"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['WHITE']};
                border-radius: 12px;
                border: 1px solid {COLORS['BORDER']};
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 标题栏
        header = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {COLORS['TEXT_PRIMARY']};")
        header.addWidget(title_label)

        # 链接输入按钮
        self._link_parse_btn = QPushButton("📎 从链接提取")
        self._link_parse_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['BACKGROUND']};
                border: 1px solid {COLORS['BORDER']};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                border-color: {COLORS['PRIMARY']};
                color: {COLORS['PRIMARY']};
            }}
        """)
        self._link_parse_btn.clicked.connect(self._on_link_parse)
        header.addWidget(self._link_parse_btn)
        layout.addLayout(header)

        # 文本输入框
        self._input_text = QTextEdit()
        self._input_text.setPlaceholderText("输入文案内容，或粘贴链接提取...")
        self._input_text.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {COLORS['BORDER']};
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                background-color: {COLORS['BACKGROUND']};
            }}
            QTextEdit:focus {{
                border-color: {COLORS['PRIMARY']};
            }}
        """)
        layout.addWidget(self._input_text, 1)

        return frame

    def _create_text_output_panel(self, title: str) -> QFrame:
        """创建文案输出面板"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['WHITE']};
                border-radius: 12px;
                border: 1px solid {COLORS['BORDER']};
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 标题栏
        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {COLORS['TEXT_PRIMARY']};")
        layout.addWidget(title_label)

        # 文本输出框
        self._output_text = QTextEdit()
        self._output_text.setReadOnly(True)
        self._output_text.setPlaceholderText("仿写后的文案将显示在这里...")
        self._output_text.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {COLORS['BORDER']};
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                background-color: {COLORS['WHITE']};
            }}
        """)
        layout.addWidget(self._output_text, 1)

        return frame

    def _create_operation_panel(self) -> QWidget:
        """创建操作按钮面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(12)

        # 一键仿写按钮
        rewrite_btn = QPushButton("▶ 一键仿写")
        rewrite_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['PRIMARY_GRADIENT_START']},
                    stop:1 {COLORS['PRIMARY_GRADIENT_END']});
                color: white;
                border: none;
                border-radius: 20px;
                padding: 12px 24px;
                font-weight: 600;
            }}
        """)
        rewrite_btn.clicked.connect(self._on_rewrite)
        layout.addWidget(rewrite_btn)

        # 其他操作按钮
        actions = ["🎬 生成视频", "🎙️ 生成配音", "💾 保存文案"]
        for action in actions:
            btn = QPushButton(action)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['WHITE']};
                    border: 1px solid {COLORS['BORDER']};
                    border-radius: 8px;
                    padding: 10px 16px;
                    color: {COLORS['TEXT_PRIMARY']};
                }}
                QPushButton:hover {{
                    border-color: {COLORS['PRIMARY']};
                    color: {COLORS['PRIMARY']};
                }}
            """)
            layout.addWidget(btn)

        layout.addStretch()
        return widget

    def _create_home_view(self) -> QWidget:
        """创建首页视图 - Banner + 4个功能卡片"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(24)

        # Banner 区域
        banner = self._create_banner()
        layout.addWidget(banner, 1)

        # 4个功能卡片网格
        cards_container = QWidget()
        cards_container.setLayout(self._create_feature_cards())
        layout.addWidget(cards_container, 1)

        return widget

    def _create_banner(self) -> QFrame:
        """创建Banner区域"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['PRIMARY_GRADIENT_START']},
                    stop:1 {COLORS['PRIMARY_GRADIENT_END']});
                border-radius: 16px;
            }}
        """)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(40, 30, 40, 30)

        # 左侧文字
        left_area = QWidget()
        left_layout = QVBoxLayout(left_area)
        left_layout.setSpacing(12)

        title = QLabel("极享 AI 口播智能体")
        title.setStyleSheet("""
            color: white;
            font-size: 32px;
            font-weight: bold;
        """)
        left_layout.addWidget(title)

        slogan = QLabel("AI 赋能，一键生成高质量口播视频")
        slogan.setStyleSheet("""
            color: rgba(255,255,255,0.9);
            font-size: 16px;
        """)
        left_layout.addWidget(slogan)

        left_layout.addStretch()

        # 立即创作按钮
        create_btn = QPushButton("立即开启创作")
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #1F2937;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 28px;
                font-size: 15px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #374151;
            }
        """)
        create_btn.clicked.connect(lambda: self._switch_view("video_creation"))
        left_layout.addWidget(create_btn)

        layout.addWidget(left_area, 1)

        # 右侧图标
        icon_label = QLabel("🎬")
        icon_label.setStyleSheet("""
            font-size: 80px;
            color: rgba(255,255,255,0.3);
        """)
        layout.addWidget(icon_label, 0)

        return frame

    def _create_feature_cards(self) -> QGridLayout:
        """创建4个功能卡片"""
        cards = [
            ("智能文案改写", "AI赋能，一键生成高质量口播文案", "✍️", "video_creation"),
            ("数字人形象库", "海量虚拟主播，一键合成数字人视频", "👤", "digital_human"),
            ("音色克隆", "复刻专属人声，满足多元配音需求", "🎙️", "voice_library"),
            ("一键分发", "多平台账号管理，批量发布作品", "📱", "accounts"),
        ]

        grid = QGridLayout()
        grid.setSpacing(20)

        for i, (title, desc, icon, view_id) in enumerate(cards):
            row = i // 2
            col = i % 2
            card = self._create_feature_card(title, desc, icon, view_id)
            grid.addWidget(card, row, col)

        return grid

    def _create_feature_card(self, title: str, desc: str, icon: str, view_id: str) -> QFrame:
        """创建单个功能卡片"""
        frame = QFrame()
        frame.setCursor(Qt.CursorShape.PointingHandCursor)
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['WHITE']};
                border-radius: 16px;
                border: 1px solid {COLORS['BORDER']};
            }}
            QFrame:hover {{
                border-color: {COLORS['PRIMARY_LIGHT']};
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # 图标
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 36px;")
        layout.addWidget(icon_label)

        # 标题
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {COLORS['TEXT_PRIMARY']};
            font-size: 18px;
            font-weight: 600;
        """)
        layout.addWidget(title_label)

        # 描述
        desc_label = QLabel(desc)
        desc_label.setStyleSheet(f"""
            color: {COLORS['TEXT_SECONDARY']};
            font-size: 14px;
        """)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label, 1)

        layout.addStretch()

        # 点击事件
        frame.mousePressEvent = lambda e: self._switch_view(view_id)

        return frame

    def _create_digital_human_view(self) -> QWidget:
        """创建数字人库视图"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("数字人库")
        title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLORS['TEXT_PRIMARY']};")
        layout.addWidget(title)

        info_label = QLabel("选择公版数字人或创建自定义数字人")
        info_label.setStyleSheet(f"color: {COLORS['TEXT_SECONDARY']}; margin: 8px 0 20px 0;")
        layout.addWidget(info_label)

        # 占位 - 实际应为数字人卡片网格
        placeholder = QLabel("数字人卡片网格展示区")
        placeholder.setStyleSheet(f"""
            background-color: {COLORS['WHITE']};
            border-radius: 12px;
            padding: 100px;
            color: {COLORS['TEXT_SECONDARY']};
        """)
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(placeholder, 1)

        return widget

    def _create_voice_library_view(self) -> QWidget:
        """创建音色库视图"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("音色库")
        title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLORS['TEXT_PRIMARY']};")
        layout.addWidget(title)

        info_label = QLabel("选择公版音色或克隆您的声音")
        info_label.setStyleSheet(f"color: {COLORS['TEXT_SECONDARY']}; margin: 8px 0 20px 0;")
        layout.addWidget(info_label)

        placeholder = QLabel("音色选择面板")
        placeholder.setStyleSheet(f"""
            background-color: {COLORS['WHITE']};
            border-radius: 12px;
            padding: 100px;
            color: {COLORS['TEXT_SECONDARY']};
        """)
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(placeholder, 1)

        return widget

    def _create_subtitle_template_view(self) -> QWidget:
        """创建字幕模板视图"""
        from src.business.post_production.subtitle_style import SubtitleStyle, SubtitleStyleConfig, PRESET_STYLES

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("字幕模板")
        title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLORS['TEXT_PRIMARY']};")
        layout.addWidget(title)

        info = QLabel("选择精品动态字幕样式，一键套用")
        info.setStyleSheet(f"color: {COLORS['TEXT_SECONDARY']}; margin: 8px 0 20px 0;")
        layout.addWidget(info)

        # 字幕样式网格
        grid = QGridLayout()
        grid.setSpacing(12)

        self._subtitle_style_buttons = {}
        for i, (style_enum, style_config) in enumerate(PRESET_STYLES.items()):
            card = QFrame()
            card.setObjectName(f"style_card_{style_enum.value}")
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['WHITE']};
                    border-radius: 8px;
                    border: 2px solid {COLORS['BORDER']};
                    padding: 16px;
                }}
                QFrame:hover {{
                    border-color: {COLORS['PRIMARY_LIGHT']};
                }}
            """)

            card_layout = QVBoxLayout(card)

            # 预览区域
            preview = QFrame()
            preview.setFixedHeight(60)
            preview.setStyleSheet(f"""
                QFrame {{
                    background-color: {style_config.background_color or '#333'};
                    border-radius: 4px;
                }}
            """)
            preview_label = QLabel("字幕预览")
            preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            preview_label.setStyleSheet(f"""
                color: {style_config.font_color};
                font-size: {min(style_config.font_size, 18)}px;
                font-weight: bold;
            """)
            preview_layout = QVBoxLayout(preview)
            preview_layout.addWidget(preview_label)
            card_layout.addWidget(preview)

            # 样式名称
            name_label = QLabel(style_config.name)
            name_label.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {COLORS['TEXT_PRIMARY']};")
            card_layout.addWidget(name_label)

            # 样式参数
            params = QLabel(
                f"字体:{style_config.font_family} | 大小:{style_config.font_size}px\n"
                f"颜色:{style_config.font_color} | 位置:{style_config.position}"
            )
            params.setStyleSheet(f"font-size: 11px; color: {COLORS['TEXT_SECONDARY']};")
            params.setWordWrap(True)
            card_layout.addWidget(params)

            # 选中按钮
            select_btn = QPushButton("应用此样式")
            select_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['PRIMARY']};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 12px;
                    margin-top: 8px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['PRIMARY_LIGHT']};
                }}
            """)
            select_btn.clicked.connect(lambda checked, s=style_enum: self._on_select_subtitle_style(s))
            card_layout.addWidget(select_btn)

            row = i // 2
            col = i % 2
            grid.addWidget(card, row, col)

        layout.addLayout(grid)
        layout.addStretch()

        # 当前选中样式提示
        self._current_subtitle_style_label = QLabel("当前选中：默认样式")
        self._current_subtitle_style_label.setStyleSheet(f"color: {COLORS['PRIMARY']}; font-weight: 600; margin-top: 16px;")
        layout.addWidget(self._current_subtitle_style_label)

        return widget

    def _on_select_subtitle_style(self, style_enum):
        """选择字幕样式"""
        from src.business.post_production.subtitle_style import SubtitleStyle, PRESET_STYLES
        style_config = PRESET_STYLES.get(style_enum)
        if style_config:
            self._current_subtitle_style = style_enum
            self._current_subtitle_style_label.setText(f"当前选中：{style_config.name}")
            logger.info(f"Subtitle style selected: {style_config.name}")

    def _create_storyboard_view(self) -> QWidget:
        """创建分镜素材视图"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("分镜素材")
        title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLORS['TEXT_PRIMARY']};")
        layout.addWidget(title)

        info = QLabel("行业分镜片段、场景素材、背景视频，支持预览插入")
        info.setStyleSheet(f"color: {COLORS['TEXT_SECONDARY']}; margin: 8px 0 20px 0;")
        layout.addWidget(info)

        placeholder = QLabel("分镜素材展示区\n\n行业分类：美妆 / 知识 / 电商 / 美食 / 教育")
        placeholder.setStyleSheet(f"""
            background-color: {COLORS['WHITE']};
            border-radius: 12px;
            padding: 100px;
            color: {COLORS['TEXT_SECONDARY']};
        """)
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(placeholder, 1)

        return widget

    def _create_accounts_view(self) -> QWidget:
        """创建发布账号视图"""
        from src.browser.platform_bots.distributor import DistributorBot, DistributionResult
        from src.browser.platform_bots.distributor import DouyinDistributor, KuaishouDistributor, XiaohongshuDistributor

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("发布账号")
        title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLORS['TEXT_PRIMARY']};")
        layout.addWidget(title)

        info = QLabel("绑定多平台账号，作品完成后一键分发")
        info.setStyleSheet(f"color: {COLORS['TEXT_SECONDARY']}; margin: 8px 0 20px 0;")
        layout.addWidget(info)

        # 平台列表
        platforms = [
            ("🐮 抖音", "douyin", "已绑定 0 个账号"),
            ("🎯 快手", "kuaishou", "未绑定"),
            ("📕 小红书", "xiaohongshu", "未绑定"),
            ("📺 视频号", "wechat", "未绑定"),
            ("🎬 B站", "bilibili", "未绑定"),
        ]

        for name, platform_id, status in platforms:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['WHITE']};
                    border-radius: 8px;
                    border: 1px solid {COLORS['BORDER']};
                    padding: 16px;
                    margin-bottom: 12px;
                }}
            """)
            card_layout = QHBoxLayout(card)

            # 平台图标和名称
            platform_layout = QVBoxLayout()
            name_label = QLabel(name)
            name_label.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {COLORS['TEXT_PRIMARY']};")
            platform_layout.addWidget(name_label)

            status_label = QLabel(status)
            status_label.setObjectName(f"status_{platform_id}")
            status_label.setStyleSheet(f"font-size: 12px; color: {COLORS['TEXT_SECONDARY']};")
            platform_layout.addWidget(status_label)
            card_layout.addLayout(platform_layout)

            card_layout.addStretch()

            # 绑定Cookie按钮
            bind_btn = QPushButton("绑定账号")
            bind_btn.setObjectName(f"bind_{platform_id}")
            bind_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['PRIMARY']};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['PRIMARY_LIGHT']};
                }}
            """)
            bind_btn.clicked.connect(lambda checked, p=platform_id, n=name: self._on_bind_account(p, n))
            card_layout.addWidget(bind_btn)

            # 一键发布按钮
            publish_btn = QPushButton("测试发布")
            publish_btn.setObjectName(f"publish_{platform_id}")
            publish_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['BACKGROUND']};
                    color: {COLORS['TEXT_PRIMARY']};
                    border: 1px solid {COLORS['BORDER']};
                    border-radius: 6px;
                    padding: 10px 20px;
                }}
                QPushButton:hover {{
                    border-color: {COLORS['PRIMARY']};
                }}
            """)
            card_layout.addWidget(publish_btn)

            layout.addWidget(card)

        # 提示信息
        hint = QLabel("💡 提示：绑定账号需要提供平台的登录Cookie，获取方法请参考帮助文档")
        hint.setStyleSheet(f"font-size: 12px; color: {COLORS['TEXT_SECONDARY']}; padding: 16px; background-color: {COLORS['BACKGROUND']}; border-radius: 8px;")
        layout.addWidget(hint)

        layout.addStretch()
        return widget

    def _on_bind_account(self, platform: str, platform_name: str):
        """绑定账号 - 需要Cookie"""
        from PyQt6.QtWidgets import QInputDialog, QMessageBox

        cookie_hint = {
            "douyin": "请输入抖音的登录Cookie（格式：sessionid=xxx; odin_tt=xxx）",
            "kuaishou": "请输入快手的登录Cookie",
            "xiaohongshu": "请输入小红书的登录Cookie",
            "wechat": "请输入视频号的登录Cookie",
            "bilibili": "请输入B站的登录Cookie",
        }

        cookie, ok = QInputDialog.getMultiLineText(
            self,
            f"绑定 {platform_name}",
            cookie_hint.get(platform, "请输入登录Cookie") + "\n\n获取方法：\n1. 在浏览器登录对应平台\n2. 按F12打开开发者工具\n3. 复制Cookie值粘贴到这里"
        )

        if ok and cookie:
            # 保存Cookie到配置
            settings = QSettings("KBSZR", "config")
            settings.setValue(f"account/{platform}_cookie", cookie)

            # 更新状态显示
            status_label = self.findChild(QLabel, f"status_{platform}")
            if status_label:
                status_label.setText("已绑定 ✓")
                status_label.setStyleSheet(f"font-size: 12px; color: {COLORS['SUCCESS']};")

            QMessageBox.information(self, "绑定成功", f"{platform_name} 账号已绑定")
            self.statusbar.showMessage(f"{platform_name} 账号绑定成功")

    def _create_membership_view(self) -> QWidget:
        """创建会员中心视图"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("会员中心")
        title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLORS['TEXT_PRIMARY']};")
        layout.addWidget(title)

        info = QLabel("管理会员权益、算力额度、套餐服务")
        info.setStyleSheet(f"color: {COLORS['TEXT_SECONDARY']}; margin: 8px 0 20px 0;")
        layout.addWidget(info)

        # 会员卡片
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['PRIMARY_GRADIENT_START']},
                    stop:1 {COLORS['PRIMARY_GRADIENT_END']});
                border-radius: 12px;
                padding: 24px;
            }}
        """)
        card_layout = QVBoxLayout(card)

        level_label = QLabel("💎 普通会员")
        level_label.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        card_layout.addWidget(level_label)

        quota_label = QLabel("剩余算力：1000 点")
        quota_label.setStyleSheet("color: rgba(255,255,255,0.9); font-size: 14px; margin-top: 8px;")
        card_layout.addWidget(quota_label)

        upgrade_btn = QPushButton("升级套餐")
        upgrade_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #8B5CF6;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: 600;
                margin-top: 16px;
            }
        """)
        card_layout.addWidget(upgrade_btn)
        layout.addWidget(card)

        # 使用记录
        records_label = QLabel("使用记录")
        records_label.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {COLORS['TEXT_PRIMARY']}; margin-top: 24px;")
        layout.addWidget(records_label)

        records = QLabel("暂无使用记录")
        records.setStyleSheet(f"color: {COLORS['TEXT_SECONDARY']}; padding: 20px;")
        layout.addWidget(records)

        layout.addStretch()
        return widget

    def _create_title_bar(self):
        """创建标题栏（通过 MenuBar 实现）"""
        pass  # 已在_create_content_panel中处理

    def _switch_view(self, view_id: str):
        """切换视图"""
        # 更新导航按钮状态
        for vid, btn in self._nav_buttons.items():
            btn.setProperty("selected", vid == view_id)
            btn.setStyleSheet(self._get_nav_button_style(selected=vid == view_id))

        # 切换视图
        if view_id in self._views:
            self._view_stack.setCurrentWidget(self._views[view_id])

        # 更新页面标题
        titles = {
            "home": "首页",
            "video_creation": "视频创作",
            "digital_human": "数字人库",
            "voice_library": "音色库",
            "subtitle_template": "字幕模板",
            "storyboard": "分镜素材",
            "accounts": "发布账号",
            "membership": "会员中心",
            "api_settings": "API 设置",
        }
        self._page_title.setText(titles.get(view_id, ""))
        self._current_view = view_id

    def _on_rewrite(self):
        """一键仿写"""
        input_text = self._input_text.toPlainText()
        if not input_text:
            QMessageBox.warning(self, "提示", "请输入文案内容")
            return

        self._output_text.setPlainText("正在仿写...")
        self.statusbar.showMessage("正在仿写文案...")

        # 获取API配置
        settings = QSettings("KBSZR", "config")
        provider = settings.value("rewriter/provider", "tongyi")
        api_key = settings.value(f"api/{provider}_key", "")
        model = settings.value(f"api/{provider}_model", "")

        if not api_key:
            self._output_text.setPlainText("请先在 API设置 中配置服务商密钥")
            self.statusbar.showMessage("请先配置API密钥")
            return

        # 使用线程避免阻塞UI
        from PyQt6.QtCore import QThread

        class RewriteWorker(QThread):
            def __init__(self, text, provider, api_key, model):
                super().__init__()
                self.text = text
                self.provider = provider
                self.api_key = api_key
                self.model = model
                self.result = None
                self.error = None

            def run(self):
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    from src.business.rewriter.router import RewriterRouter, RewriteConfig
                    from src.business.rewriter.api_rewriter import create_rewriter

                    config = RewriteConfig(provider=self.provider)
                    router = RewriterRouter(config=config)

                    cloud_config = {
                        "provider": self.provider,
                        self.provider: {
                            "api_key": self.api_key,
                            "model": self.model or "qwen-max"
                        }
                    }
                    loop.run_until_complete(router.initialize(cloud_config))

                    from src.business.rewriter.router import RewriteRequest
                    request = RewriteRequest(text=self.text)
                    response = loop.run_until_complete(router.rewrite(request))
                    loop.run_until_complete(router.close())

                    if response.success:
                        self.result = response.rewritten_text
                    else:
                        self.error = response.error
                except Exception as e:
                    self.error = str(e)
                finally:
                    loop.close()

        self._rewrite_worker = RewriteWorker(input_text, provider, api_key, model)
        self._rewrite_worker.finished.connect(self._on_rewrite_done)
        self._rewrite_worker.start()

    def _on_rewrite_done(self):
        """仿写完成回调"""
        worker = self._rewrite_worker
        if worker.error:
            self._output_text.setPlainText(f"仿写失败: {worker.error}")
            self.statusbar.showMessage("仿写失败")
        elif worker.result:
            self._output_text.setPlainText(worker.result)
            self.statusbar.showMessage("仿写完成")
        else:
            self._output_text.setPlainText("仿写失败：未知错误")
            self.statusbar.showMessage("仿写失败")
        worker.deleteLater()

    def _create_api_settings_view(self) -> QWidget:
        """创建API设置视图"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {COLORS['BACKGROUND']};
            }}
            QScrollBar:vertical {{
                background-color: {COLORS['BACKGROUND']};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {COLORS['BORDER']};
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {COLORS['PRIMARY_LIGHT']};
            }}
        """)

        # 内容容器
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(32, 24, 32, 24)
        content_layout.setSpacing(24)

        # 标题
        title = QLabel("API 设置")
        title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLORS['TEXT_PRIMARY']};")
        content_layout.addWidget(title)

        info = QLabel("配置您的AI服务商API密钥，按功能模块分区显示")
        info.setStyleSheet(f"color: {COLORS['TEXT_SECONDARY']}; margin-bottom: 20px;")
        content_layout.addWidget(info)

        # ========== 文案改写模块 ==========
        content_layout.addWidget(self._create_api_section(
            "📝 文案改写", "AI文案改写、仿写、优化",
            [
                ("通义千问", "tongyi", "qwen-max", ["qwen-max", "qwen-plus", "qwen-turbo"]),
                ("DeepSeek", "deepseek", "deepseek-chat", ["deepseek-chat", "deepseek-coder"]),
                ("豆包", "doubao", "doubao-pro", ["doubao-pro", "doubao-lite"]),
                ("文心一言", "wenxin", "ernie-4.0-8k-latest", ["ernie-4.0-8k-latest", "ernie-3.5-8k"]),
                ("腾讯混元", "hunyuan", "hunyuan", ["hunyuan", "hunyuan-pro"]),
                ("讯飞星火", "spark", "generalv3", ["generalv3", "generalv2"]),
                ("火山引擎", "volcengine", "doubao-pro", ["doubao-pro", "doubao-lite"]),
            ]
        ))

        # ========== 语音合成模块 ==========
        content_layout.addWidget(self._create_api_section(
            "🎙️ 语音合成 (TTS)", "文字转语音、配音生成",
            [
                ("阿里云TTS", "aliyun_tts", "xiaomo", ["xiaomo", "zhijia", "xiaoyun", "xiaogang"]),
                ("火山引擎TTS", "volcengine_tts", "BV002_streaming", ["BV001_streaming", "BV002_streaming", "BV003_streaming"]),
                ("讯飞TTS", "xfyun_tts", "xiaoyan", ["xiaoyan", "aisjiuxu", "aisbabyxu"]),
            ]
        ))

        # ========== 数字人模块 ==========
        content_layout.addWidget(self._create_api_section(
            "👤 数字人", "数字人视频生成",
            [
                ("阿里云数字人", "aliyun_dh", "avatar_001", ["avatar_001", "avatar_002", "avatar_003"]),
                ("火山引擎数字人", "volcengine_dh", "volc_avatar_001", ["volc_avatar_001", "volc_avatar_002"]),
                ("腾讯云数字人", "tencent_dh", "tencent_avatar_001", ["tencent_avatar_001"]),
            ]
        ))

        # ========== 视频处理模块 ==========
        content_layout.addWidget(self._create_api_section(
            "🎬 视频处理", "字幕生成、画质增强、视频合成",
            [
                ("阿里云视频API", "aliyun_video", "video_enhance", ["video_enhance", "video_edit"]),
                ("火山引擎视频API", "volcengine_video", "ve_video_edit", ["ve_video_edit"]),
            ]
        ))

        # ========== 内容安全模块 ==========
        content_layout.addWidget(self._create_api_section(
            "🛡️ 内容安全", "敏感词过滤、内容审核",
            [
                ("阿里云内容安全", "aliyun_content", "scan_text", ["scan_text", "scan_image"]),
            ]
        ))

        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

        return widget

    def _create_api_section(self, title: str, desc: str, providers: list) -> QFrame:
        """创建API分区"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['WHITE']};
                border-radius: 12px;
                border: 1px solid {COLORS['BORDER']};
                padding: 16px;
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        # 分区标题
        header = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {COLORS['TEXT_PRIMARY']};")
        header.addWidget(title_label)

        desc_label = QLabel(desc)
        desc_label.setStyleSheet(f"font-size: 12px; color: {COLORS['TEXT_SECONDARY']};")
        header.addWidget(desc_label)
        header.addStretch()
        layout.addLayout(header)

        # 卡片网格
        cards_layout = QGridLayout()
        cards_layout.setSpacing(12)

        for i, (name, provider, default_model, models) in enumerate(providers):
            row = i // 2
            col = i % 2
            card = self._create_api_card(name, provider, default_model, models)
            cards_layout.addWidget(card, row, col)

        layout.addLayout(cards_layout)
        return frame

    def _create_api_card(self, name: str, provider: str, default_model: str, models: list) -> QFrame:
        """创建单个API配置卡片"""
        frame = QFrame()
        frame.setObjectName(f"api_card_{provider}")
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['BACKGROUND']};
                border-radius: 8px;
                border: 1px solid {COLORS['BORDER']};
                padding: 12px;
            }}
            QFrame:hover {{
                border-color: {COLORS['PRIMARY_LIGHT']};
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # 顶部：状态和名称
        top = QHBoxLayout()
        status_label = QLabel("⚪")
        status_label.setObjectName(f"status_{provider}")
        status_label.setStyleSheet("font-size: 12px;")
        status_label.setToolTip("未配置")
        top.addWidget(status_label)

        name_label = QLabel(name)
        name_label.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {COLORS['TEXT_PRIMARY']};")
        top.addWidget(name_label)
        top.addStretch()
        layout.addLayout(top)

        # 模型输入框（可自由填写）
        model_layout = QHBoxLayout()
        model_label = QLabel("模型:")
        model_label.setStyleSheet(f"font-size: 12px; color: {COLORS['TEXT_SECONDARY']}; width: 40px;")
        model_layout.addWidget(model_label)

        model_input = QLineEdit()
        model_input.setObjectName(f"model_{provider}")
        model_input.setText(default_model)
        model_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {COLORS['BORDER']};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
                background-color: {COLORS['WHITE']};
                color: {COLORS['TEXT_PRIMARY']};
            }}
            QLineEdit:focus {{
                border-color: {COLORS['PRIMARY']};
            }}
        """)
        model_layout.addWidget(model_input)

        # 提示可选模型
        if models:
            hint_label = QLabel(f"如: {', '.join(models[:3])}")
            hint_label.setStyleSheet(f"font-size: 10px; color: {COLORS['TEXT_SECONDARY']};")
            model_layout.addWidget(hint_label)
        model_layout.addStretch()
        layout.addLayout(model_layout)

        # API Key输入框
        api_key_input = QLineEdit()
        api_key_input.setObjectName(f"input_{provider}")
        api_key_input.setPlaceholderText("输入 API Key")
        api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        api_key_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {COLORS['BORDER']};
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 12px;
                background-color: {COLORS['WHITE']};
                color: {COLORS['TEXT_PRIMARY']};
            }}
            QLineEdit:focus {{
                border-color: {COLORS['PRIMARY']};
            }}
            QLineEdit::placeholder {{
                color: {COLORS['TEXT_SECONDARY']};
            }}
        """)
        layout.addWidget(api_key_input)

        # 底部：保存按钮
        bottom = QHBoxLayout()
        bottom.addStretch()

        save_btn = QPushButton("保存")
        save_btn.setObjectName(f"save_{provider}")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['PRIMARY']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['PRIMARY_LIGHT']};
            }}
        """)
        bottom.addWidget(save_btn)

        layout.addLayout(bottom)

        # 加载已保存的配置
        settings = QSettings("KBSZR", "config")
        saved_key = settings.value(f"api/{provider}_key", "")
        saved_model = settings.value(f"api/{provider}_model", default_model)

        if saved_key:
            api_key_input.setText(saved_key)
            status_label.setText("🟢")
            status_label.setToolTip("已配置")

        model_input.setText(saved_model)

        save_btn.clicked.connect(lambda checked, p=provider, i=api_key_input, s=status_label, m=model_input: self._on_save_api(p, i.text(), m.text(), s))

        return frame

    def _on_save_api(self, provider: str, api_key: str, model: str, status_label: QLabel):
        """保存API密钥"""
        if not api_key:
            QMessageBox.warning(self, "提示", "请输入API密钥")
            return

        settings = QSettings("KBSZR", "config")
        settings.setValue(f"api/{provider}_key", api_key)
        settings.setValue(f"api/{provider}_model", model)

        # 更新状态
        status_label.setText("🟢")
        status_label.setToolTip("已配置")

        QMessageBox.information(self, "成功", f"API密钥已保存\n\n服务商: {provider}\n模型: {model}")
        self.statusbar.showMessage(f"{provider} API密钥已保存 (模型: {model})")

    def _on_link_parse(self):
        """从链接提取文案"""
        from PyQt6.QtWidgets import QInputDialog, QMessageBox
        link, ok = QInputDialog.getText(self, "链接解析", "请输入要解析的链接:\n(支持抖音/快手/小红书/视频号/B站分享文本)")
        if ok and link:
            self._parse_link_async(link)

    def _parse_link_async(self, link: str):
        """异步解析链接"""
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
        self.statusbar.showMessage("正在解析链接...")

    def _on_parse_done(self, result):
        """解析完成回调"""
        if isinstance(result, Exception):
            QMessageBox.warning(self, "解析失败", str(result))
            self.statusbar.showMessage("解析失败")
            return

        if result and result.success:
            self._input_text.setPlainText(result.text)
            self.statusbar.showMessage(f"解析成功 ({result.platform})")
        else:
            error_msg = result.error if result else "解析失败，请确认链接是否正确"
            QMessageBox.warning(self, "解析失败", error_msg)
            self.statusbar.showMessage("解析失败")


def main():
    app = QApplication(sys.argv)
    window = JixiangMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()