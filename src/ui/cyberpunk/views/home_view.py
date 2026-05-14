"""首页视图 - 仪表盘"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGridLayout, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QLinearGradient, QColor
from ..theme import COLORS, get_card_qss, get_neon_glow
from ..widgets import CyberCard, NeonButton


class HomeView(QWidget):
    """
    首页仪表盘视图
    包含欢迎横幅、统计数据、最近项目
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        # 欢迎横幅
        welcome_banner = self._create_welcome_banner()
        main_layout.addWidget(welcome_banner)

        # 统计卡片区域
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        # 创建统计卡片
        stats_data = [
            {"icon": "🎬", "value": "128", "label": "创作数", "color": "cyan"},
            {"icon": "👤", "value": "16", "label": "数字人", "color": "magenta"},
            {"icon": "🚀", "value": "89", "label": "发布次数", "color": "blue"},
            {"icon": "⏱️", "value": "2.5h", "label": "总时长", "color": "cyan"},
        ]

        for stat in stats_data:
            stat_card = self._create_stat_card(stat)
            stats_layout.addWidget(stat_card)

        stats_layout.addStretch()
        main_layout.addLayout(stats_layout)

        # 最近项目区域
        recent_label = QLabel("最近项目")
        recent_label.setStyleSheet(f"""
            color: {COLORS['TEXT_PRIMARY']};
            font-size: 16px;
            font-weight: 600;
        """)
        main_layout.addWidget(recent_label)

        # 最近项目列表（可滚动）
        recent_scroll = QScrollArea()
        recent_scroll.setWidgetResizable(True)
        recent_scroll.setFrameShape(QFrame.Shape.Box)
        recent_scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
        """)

        recent_container = QWidget()
        recent_layout = QVBoxLayout(recent_container)
        recent_layout.setSpacing(12)

        # 模拟最近项目
        recent_projects = [
            {"title": "美妆种草视频", "platform": "抖音", "time": "2小时前"},
            {"title": "知识干货分享", "platform": "B站", "time": "5小时前"},
            {"title": "产品测评", "platform": "小红书", "time": "昨天"},
        ]

        for project in recent_projects:
            project_card = self._create_project_card(project)
            recent_layout.addWidget(project_card)

        recent_layout.addStretch()
        recent_scroll.setWidget(recent_container)
        main_layout.addWidget(recent_scroll)

    def _create_welcome_banner(self) -> QFrame:
        """创建欢迎横幅"""
        banner = QFrame()
        banner.setFixedHeight(100)
        banner.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0a0a1a, stop:0.5 #1a0a2a, stop:1 #0a1a2a);
                border-radius: 12px;
                border: 1px solid {COLORS['PRIMARY_NEON']};
            }}
        """)

        layout = QVBoxLayout(banner)
        layout.setContentsMargins(24, 20, 24, 20)

        title = QLabel("欢迎使用 极享AI口播智能体")
        title.setStyleSheet(f"""
            color: {COLORS['PRIMARY_NEON']};
            font-size: 22px;
            font-weight: bold;
        """)

        subtitle = QLabel("数字人口播视频创作平台 | 一站式视频生产流水线")
        subtitle.setStyleSheet(f"""
            color: {COLORS['TEXT_SECONDARY']};
            font-size: 13px;
        """)

        layout.addWidget(title)
        layout.addWidget(subtitle)

        return banner

    def _create_stat_card(self, data: dict) -> CyberCard:
        """创建统计卡片"""
        card = CyberCard(
            title=f"{data['icon']} {data['label']}",
            content=data["value"],
            neon_color=data["color"]
        )
        card.setFixedSize(140, 100)
        return card

    def _create_project_card(self, project: dict) -> QFrame:
        """创建项目卡片"""
        card = QFrame()
        card.setStyleSheet(get_card_qss(False, "cyan"))

        layout = QHBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)

        # 平台标签
        platform_label = QLabel(project["platform"])
        platform_label.setStyleSheet(f"""
            background: {COLORS['SURFACE']};
            color: {COLORS['PRIMARY_NEON']};
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
        """)

        # 标题
        title_label = QLabel(project["title"])
        title_label.setStyleSheet(f"""
            color: {COLORS['TEXT_PRIMARY']};
            font-size: 14px;
        """)

        # 时间
        time_label = QLabel(project["time"])
        time_label.setStyleSheet(f"""
            color: {COLORS['TEXT_MUTED']};
            font-size: 12px;
        """)

        layout.addWidget(platform_label)
        layout.addWidget(title_label, 1)
        layout.addWidget(time_label)

        return card