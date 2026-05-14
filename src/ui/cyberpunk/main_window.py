"""极享AI口播智能体 - 赛博朋克风格主窗口"""
import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel, QStatusBar, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from .theme import COLORS, get_window_qss, get_neon_glow, reload_theme_if_changed
from .widgets import NavSidebar, ScanLinesOverlay
from .views import (
    HomeView,
    CreationView,
    DigitalHumanView,
    TimelineView,
    PublishView,
    SettingsView
)


class CyberpunkMainWindow(QMainWindow):
    """
    极享AI口播智能体 - 赛博朋克风格主窗口

    布局：
    - 顶部：标题栏（50px）
    - 左侧：导航栏（80px）
    - 中心：内容区（根据导航切换）
    - 底部：状态栏（30px）
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("极享AI口播智能体 - Cyberpunk Edition")
        self.setMinimumSize(1280, 800)

        # 视图实例缓存
        self._views = {}

        # 初始化UI
        self._init_ui()
        self._apply_theme()

        # 连接信号
        self._connect_signals()

        # 显示首页
        self._show_view("home")

        # 状态栏更新定时器
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._update_status)
        self._status_timer.start(1000)

    def _init_ui(self):
        """初始化UI"""
        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)

        # 主布局
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 标题栏
        header = self._create_header()
        main_layout.addWidget(header)

        # 内容区域
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # 左侧导航
        self._nav_sidebar = NavSidebar()
        content_layout.addWidget(self._nav_sidebar)

        # 主内容区
        content_container = QWidget()
        content_container.setObjectName("contentContainer")
        content_container.setStyleSheet(f"""
            #contentContainer {{
                background-color: {COLORS['BACKGROUND']};
            }}
        """)
        self._content_stack = QStackedWidget()
        content_layout.addWidget(content_container, 1)

        main_layout.addLayout(content_layout)

        # 状态栏
        self._status_bar = self._create_status_bar()
        self.setStatusBar(self._status_bar)

        # 主题热重载定时器
        self._theme_timer = QTimer(self)
        self._theme_timer.timeout.connect(self._check_theme_reload)
        self._theme_timer.start(2000)  # 每2秒检查一次

    def _create_header(self) -> QWidget:
        """创建标题栏"""
        header = QWidget()
        header.setFixedHeight(50)
        header.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['SURFACE']};
                border-bottom: 1px solid {COLORS['BORDER']};
            }}
        """)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)

        # Logo和标题
        logo_area = QWidget()
        logo_layout = QHBoxLayout(logo_area)
        logo_layout.setSpacing(12)

        logo_label = QLabel("AI")
        logo_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        logo_label.setStyleSheet(f"""
            color: {COLORS['PRIMARY_NEON']};
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {COLORS['PRIMARY_NEON']}, stop:1 {COLORS['ACCENT']});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            padding: 4px 8px;
        """)

        title_label = QLabel("极享AI口播智能体")
        title_label.setStyleSheet(f"""
            color: {COLORS['TEXT_PRIMARY']};
            font-size: 16px;
            font-weight: 600;
        """)

        version_label = QLabel("v2.0")
        version_label.setStyleSheet(f"""
            color: {COLORS['TEXT_MUTED']};
            font-size: 11px;
            background-color: {COLORS['CARD']};
            padding: 2px 6px;
            border-radius: 4px;
        """)

        logo_layout.addWidget(logo_label)
        logo_layout.addWidget(title_label)
        logo_layout.addWidget(version_label)

        layout.addWidget(logo_area)

        # 右侧快捷操作
        quick_actions = QWidget()
        quick_layout = QHBoxLayout(quick_actions)
        quick_layout.setSpacing(8)

        # 快捷操作按钮
        from .widgets import NeonButton, IconNeonButton
        refresh_btn = IconNeonButton("🔄", tooltip="刷新状态", variant="ghost", size=32)
        settings_btn = IconNeonButton("⚙️", tooltip="设置", variant="ghost", size=32)
        settings_btn.clicked.connect(lambda: self._show_view("settings"))
        help_btn = IconNeonButton("❓", tooltip="帮助", variant="ghost", size=32)

        quick_layout.addWidget(refresh_btn)
        quick_layout.addWidget(settings_btn)
        quick_layout.addWidget(help_btn)

        layout.addWidget(quick_actions)

        return header

    def _create_status_bar(self) -> QStatusBar:
        """创建状态栏"""
        status_bar = QStatusBar()
        status_bar.setFixedHeight(28)
        status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {COLORS['SURFACE']};
                color: {COLORS['TEXT_SECONDARY']};
                border-top: 1px solid {COLORS['BORDER']};
                font-size: 12px;
            }}
        """)

        # 状态标签
        self._status_label = QLabel("系统就绪")
        self._status_label.setStyleSheet(f"color: {COLORS['TEXT_SECONDARY']};")

        # 版本标签
        version_label = QLabel("Cyberpunk Edition")
        version_label.setStyleSheet(f"color: {COLORS['TEXT_MUTED']};")

        status_bar.addPermanentWidget(version_label)
        status_bar.addWidget(self._status_label)

        return status_bar

    def _apply_theme(self):
        """应用主题"""
        self.setStyleSheet(get_window_qss())

    def _connect_signals(self):
        """连接信号"""
        self._nav_sidebar.view_changed.connect(self._on_view_changed)

    def _on_view_changed(self, view_id: str):
        """视图切换"""
        self._show_view(view_id)

    def _show_view(self, view_id: str):
        """显示指定视图"""
        # 检查是否已存在
        if view_id in self._views:
            widget = self._views[view_id]
        else:
            widget = self._create_view(view_id)
            self._views[view_id] = widget
            self._content_stack.addWidget(widget)

        # 切换显示
        self._content_stack.setCurrentWidget(widget)
        self._nav_sidebar.setCurrentView(view_id)

    def _create_view(self, view_id: str) -> QWidget:
        """创建视图"""
        view_classes = {
            "home": HomeView,
            "creation": CreationView,
            "digital_human": DigitalHumanView,
            "timeline": TimelineView,
            "publish": PublishView,
            "settings": SettingsView,
        }

        view_class = view_classes.get(view_id, HomeView)
        return view_class()

    def _check_theme_reload(self):
        """检查并重载主题配置"""
        if reload_theme_if_changed():
            self._apply_theme()
            # 更新所有视图
            for view in self._views.values():
                view.update()

    def _update_status(self):
        """更新状态"""
        import datetime
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self._status_label.setText(f"系统就绪 | {now}")

    def closeEvent(self, event):
        """关闭事件"""
        # 清理资源
        if hasattr(self, '_scan_lines'):
            self._scan_lines.close()

        # 关闭所有视图
        for view in self._views.values():
            if hasattr(view, 'close'):
                view.close()

        event.accept()


def main():
    """主函数"""
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # 应用全局样式
    app.setStyleSheet(get_window_qss())

    # 创建并显示窗口
    window = CyberpunkMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()