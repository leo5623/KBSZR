"""导航侧边栏组件"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QSpacerItem
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPainter, QColor, QLinearGradient
from ..theme import COLORS, get_neon_glow, get_nav_item_qss


class NavSidebar(QWidget):
    """
    80px宽图标导航侧边栏
    支持6个导航项，带霓虹发光效果
    """

    view_changed = pyqtSignal(str)  # 导航项变化信号

    # 导航项配置
    NAV_ITEMS = [
        {"id": "home", "icon": "🏠", "text": "首页"},
        {"id": "creation", "icon": "✍️", "text": "创作"},
        {"id": "digital_human", "icon": "👤", "text": "数字人"},
        {"id": "timeline", "icon": "🎬", "text": "时间线"},
        {"id": "publish", "icon": "🚀", "text": "发布"},
        {"id": "settings", "icon": "⚙️", "text": "设置"},
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_id = "home"

        # 设置固定宽度
        self.setFixedWidth(80)

        self._init_ui()
        self._apply_style()

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Logo区域
        logo_frame = QWidget()
        logo_frame.setFixedHeight(70)
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(0, 15, 0, 15)

        logo_label = QLabel("AI")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet(f"""
            font-size: 20px;
            font-weight: bold;
            color: {COLORS['PRIMARY_NEON']};
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {COLORS['PRIMARY_NEON']}, stop:1 {COLORS['ACCENT']});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        """)
        logo_layout.addWidget(logo_label)
        main_layout.addWidget(logo_frame)

        # 分割线
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background: {COLORS['BORDER']};")
        main_layout.addWidget(separator)

        # 导航按钮容器
        nav_container = QWidget()
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 10, 0, 10)
        nav_layout.setSpacing(4)

        self._nav_buttons = {}

        for item in self.NAV_ITEMS:
            btn = NavItemButton(
                icon=item["icon"],
                text=item["text"],
                selected=(item["id"] == self._selected_id)
            )
            btn.clicked.connect(lambda checked, id=item["id"]: self._on_nav_clicked(id))
            nav_layout.addWidget(btn)
            self._nav_buttons[item["id"]] = btn

        main_layout.addWidget(nav_container)
        main_layout.addStretch()

    def _apply_style(self):
        """应用样式"""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['SURFACE']};
            }}
        """)

    def _on_nav_clicked(self, item_id: str):
        """导航项点击"""
        if item_id == self._selected_id:
            return

        # 更新选中状态
        self._nav_buttons[self._selected_id].setSelected(False)
        self._nav_buttons[item_id].setSelected(True)
        self._selected_id = item_id

        # 发送信号
        self.view_changed.emit(item_id)

    def setCurrentView(self, view_id: str):
        """设置当前视图"""
        if view_id in self._nav_buttons and view_id != self._selected_id:
            self._nav_buttons[self._selected_id].setSelected(False)
            self._nav_buttons[view_id].setSelected(True)
            self._selected_id = view_id


class NavItemButton(QPushButton):
    """
    导航项按钮
    显示图标+文字，hover和选中状态有不同样式
    """

    def __init__(self, icon: str, text: str, selected: bool = False):
        super().__init__()
        self._icon = icon
        self._text = text
        self._selected = selected

        self.setFixedHeight(50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumWidth(80)

        # 使用固定文本格式
        self.setText(f"{icon}  {text}")
        self.setStyleSheet(get_nav_item_qss(selected))

    def setSelected(self, selected: bool):
        """设置选中状态"""
        self._selected = selected
        self.setStyleSheet(get_nav_item_qss(selected))

    def enterEvent(self, event):
        """鼠标进入"""
        super().enterEvent(event)
        if not self._selected:
            self.setStyleSheet(get_nav_item_qss(False).replace(
                f"color: {COLORS['TEXT_SECONDARY']}",
                f"color: {COLORS['PRIMARY_NEON']}"
            ))

    def leaveEvent(self, event):
        """鼠标离开"""
        super().leaveEvent(event)
        if not self._selected:
            self.setStyleSheet(get_nav_item_qss(False))