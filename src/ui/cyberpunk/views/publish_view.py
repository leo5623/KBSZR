"""发布视图 - 多平台发布管理"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QGridLayout, QScrollArea, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from ..theme import COLORS, get_card_qss, get_neon_glow
from ..widgets import CyberCard, NeonButton


class PlatformCard(QFrame):
    """平台卡片"""

    def __init__(self, platform_id: str, name: str, icon: str, parent=None):
        super().__init__(parent)
        self._platform_id = platform_id
        self._name = name
        self._bound = False

        self.setFixedSize(200, 160)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_style()

        self._init_ui(icon)

    def _init_ui(self, icon: str):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 平台图标
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(f"""
            font-size: 36px;
            background-color: {COLORS['CARD']};
            border-radius: 20px;
            padding: 10px;
        """)
        layout.addWidget(icon_label)

        # 平台名称
        name_label = QLabel(self._name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet(f"""
            color: {COLORS['TEXT_PRIMARY']};
            font-size: 14px;
            font-weight: 600;
        """)
        layout.addWidget(name_label)

        # 状态标签
        self._status_label = QLabel("未绑定")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet(f"""
            background-color: {COLORS['SURFACE']};
            color: {COLORS['TEXT_SECONDARY']};
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
        """)
        layout.addWidget(self._status_label)

    def _update_style(self):
        """更新样式"""
        glow = get_neon_glow("cyan", 0.3) if self._bound else ""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['CARD']};
                border-radius: 12px;
                border: 1px solid {COLORS['BORDER']};
            }}
            QFrame:hover {{
                border: 1px solid {COLORS['PRIMARY_NEON']};
                box-shadow: {glow};
            }}
        """)

    def setBound(self, bound: bool, account: str = ""):
        """设置绑定状态"""
        self._bound = bound
        if bound:
            self._status_label.setText(f"✅ {account}")
            self._status_label.setStyleSheet(f"""
                background-color: rgba(0, 255, 136, 0.1);
                color: {COLORS['SUCCESS']};
                padding: 4px 12px;
                border-radius: 4px;
                font-size: 12px;
            """)
        else:
            self._status_label.setText("未绑定")
            self._status_label.setStyleSheet(f"""
                background-color: {COLORS['SURFACE']};
                color: {COLORS['TEXT_SECONDARY']};
                padding: 4px 12px;
                border-radius: 4px;
                font-size: 12px;
            """)
        self._update_style()


class PublishView(QWidget):
    """
    发布视图
    平台卡片网格（抖音/快手/小红书/视频号/B站）+ 发布历史
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._load_platforms()

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        # 标题
        title = QLabel("🚀 多平台发布")
        title.setStyleSheet(f"""
            color: {COLORS['TEXT_PRIMARY']};
            font-size: 20px;
            font-weight: 600;
        """)
        main_layout.addWidget(title)

        # 平台选择区域
        platform_label = QLabel("选择发布平台")
        platform_label.setStyleSheet(f"color: {COLORS['TEXT_SECONDARY']}; font-size: 13px;")
        main_layout.addWidget(platform_label)

        # 平台卡片网格
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.Box)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
        """)

        self._platform_grid = QWidget()
        self._platform_grid_layout = QGridLayout(self._platform_grid)
        self._platform_grid_layout.setSpacing(16)
        self._platform_grid_layout.setContentsMargins(0, 0, 0, 0)

        scroll.setWidget(self._platform_grid)
        main_layout.addWidget(scroll, 1)

        # 发布历史
        history_label = QLabel("📋 发布历史")
        history_label.setStyleSheet(f"color: {COLORS['TEXT_PRIMARY']}; font-size: 14px; font-weight: 600;")
        main_layout.addWidget(history_label)

        # 历史表格
        self._history_table = QTableWidget()
        self._history_table.setColumnCount(5)
        self._history_table.setHorizontalHeaderLabels(["平台", "标题", "状态", "发布时间", "操作"])
        self._history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._history_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['SURFACE']};
                color: {COLORS['TEXT_PRIMARY']};
                border: 1px solid {COLORS['BORDER']};
                border-radius: 8px;
                gridline-color: {COLORS['BORDER']};
            }}
            QTableWidget::item {{
                padding: 10px;
            }}
            QTableWidget::item:selected {{
                background-color: rgba(0, 255, 255, 0.1);
            }}
            QHeaderView::section {{
                background-color: {COLORS['CARD']};
                color: {COLORS['TEXT_PRIMARY']};
                padding: 10px;
                border: none;
                border-bottom: 1px solid {COLORS['BORDER']};
            }}
        """)
        self._history_table.setAlternatingRowColors(True)
        main_layout.addWidget(self._history_table)

        # 批量操作栏
        action_bar = self._create_action_bar()
        main_layout.addWidget(action_bar)

    def _create_action_bar(self) -> QFrame:
        """创建操作栏"""
        frame = QFrame()
        frame.setFixedHeight(50)
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['SURFACE']};
                border-radius: 8px;
            }}
        """)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 0, 16, 0)

        # 批量选择
        select_all_btn = NeonButton("全选", variant="ghost")
        deselect_all_btn = NeonButton("取消全选", variant="ghost")

        layout.addWidget(select_all_btn)
        layout.addWidget(deselect_all_btn)
        layout.addStretch()

        # 一键发布
        publish_all_btn = NeonButton("🚀 一键发布", variant="primary")
        layout.addWidget(publish_all_btn)

        return frame

    def _load_platforms(self):
        """加载平台数据"""
        platforms = [
            {"id": "douyin", "name": "抖音", "icon": "📱"},
            {"id": "kuaishou", "name": "快手", "icon": "🎬"},
            {"id": "xiaohongshu", "name": "小红书", "icon": "📕"},
            {"id": "weixin", "name": "视频号", "icon": "💬"},
            {"id": "bilibili", "name": "B站", "icon": "📺"},
        ]

        for i, platform in enumerate(platforms):
            row = i // 3
            col = i % 3

            card = PlatformCard(
                platform["id"],
                platform["name"],
                platform["icon"]
            )

            self._platform_grid_layout.addWidget(card, row, col)