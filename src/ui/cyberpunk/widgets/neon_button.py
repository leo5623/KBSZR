"""霓虹按钮组件"""
from PyQt6.QtWidgets import QPushButton, QWidget, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from ..theme import get_button_qss, COLORS, get_neon_glow


class NeonButton(QPushButton):
    """
    霓虹按钮组件
    支持 primary (渐变填充) / secondary (边框) / ghost (透明) 三种样式
    """

    clickedWithPos = pyqtSignal(int, int)  # 带位置的点击信号

    def __init__(
        self,
        text: str = "",
        variant: str = "primary",
        icon: str = None,
        parent=None
    ):
        super().__init__(text, parent)
        self._variant = variant
        self._icon = icon

        self.setMinimumHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # 设置样式
        self._apply_style()

        # 设置文本和图标
        if icon:
            self.setText(f"{icon}  {text}")
        else:
            self.setText(text)

    def _apply_style(self):
        """应用样式"""
        self.setStyleSheet(get_button_qss(self._variant))

    def setVariant(self, variant: str):
        """设置按钮变体"""
        self._variant = variant
        self._apply_style()

    def enterEvent(self, event):
        """鼠标进入事件"""
        super().enterEvent(event)
        self.update()

    def leaveEvent(self, event):
        """鼠标离开事件"""
        super().leaveEvent(event)
        self.update()


class IconNeonButton(NeonButton):
    """
    图标霓虹按钮 - 方形图标按钮
    """

    def __init__(
        self,
        icon: str,
        tooltip: str = "",
        variant: str = "primary",
        size: int = 40,
        parent=None
    ):
        super().__init__(text="", variant=variant, icon=None, parent=parent)
        self._icon = icon
        self._size = size

        self.setFixedSize(size, size)
        self.setToolTip(tooltip)
        self.setText(icon)
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['PRIMARY_NEON']}, stop:1 {COLORS['ACCENT']});
                color: {COLORS['BACKGROUND']};
                border: none;
                border-radius: {size//2}px;
                font-size: {size//2}px;
            }}
            QPushButton:hover {{
                box-shadow: {get_neon_glow('cyan', 0.6)};
            }}
        """)

    def sizeHint(self) -> QSize:
        return QSize(self._size, self._size)