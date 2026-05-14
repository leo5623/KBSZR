"""赛博朋克卡片组件"""
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QWidget
from PyQt6.QtCore import Qt, pyqtSignal
from ..theme import COLORS, get_neon_glow, get_card_qss


class CyberCard(QFrame):
    """
    赛博朋克风格卡片组件
    hover时显示霓虹边框发光效果
    """

    clicked = pyqtSignal()  # 点击信号

    def __init__(
        self,
        title: str = "",
        content: str = "",
        neon_color: str = "cyan",
        parent=None
    ):
        super().__init__(parent)
        self._neon_color = neon_color

        self.setMinimumHeight(120)
        self.setFrameShape(QFrame.Shape.Box)

        # 初始化UI
        self._init_ui(title, content)

        # 应用样式
        self._apply_style()

        # 开启鼠标追踪以检测hover
        self.setMouseTracking(True)

    def _init_ui(self, title: str, content: str):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # 标题
        if title:
            self._title_label = QLabel(title)
            self._title_label.setStyleSheet(f"""
                color: {COLORS['TEXT_PRIMARY']};
                font-size: 15px;
                font-weight: 600;
            """)
            layout.addWidget(self._title_label)

        # 内容
        if content:
            self._content_label = QLabel(content)
            self._content_label.setStyleSheet(f"""
                color: {COLORS['TEXT_SECONDARY']};
                font-size: 13px;
            """)
            self._content_label.setWordWrap(True)
            layout.addWidget(self._content_label)

        layout.addStretch()

    def _apply_style(self):
        """应用样式"""
        self.setStyleSheet(get_card_qss(False, self._neon_color))

    def setNeonColor(self, color: str):
        """设置霓虹颜色"""
        self._neon_color = color
        self._apply_style()

    def setTitle(self, title: str):
        """设置标题"""
        if hasattr(self, '_title_label'):
            self._title_label.setText(title)

    def setContent(self, content: str):
        """设置内容"""
        if hasattr(self, '_content_label'):
            self._content_label.setText(content)

    def enterEvent(self, event):
        """鼠标进入"""
        super().enterEvent(event)
        self.setStyleSheet(get_card_qss(True, self._neon_color))

    def leaveEvent(self, event):
        """鼠标离开"""
        super().leaveEvent(event)
        self.setStyleSheet(get_card_qss(False, self._neon_color))

    def mousePressEvent(self, event):
        """鼠标按下"""
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


class CyberCardGrid(QWidget):
    """
    赛博朋克卡片网格容器
    自动排列卡片
    """

    def __init__(self, columns: int = 3, spacing: int = 16, parent=None):
        super().__init__(parent)
        self._columns = columns
        self._spacing = spacing

        from PyQt6.QtWidgets import QGridLayout
        self._layout = QGridLayout(self)
        self._layout.setSpacing(spacing)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._cards = []

    def addCard(self, card: CyberCard, row: int = -1, col: int = -1):
        """添加卡片"""
        self._cards.append(card)

        if row == -1 or col == -1:
            # 自动计算位置
            index = len(self._cards) - 1
            row = index // self._columns
            col = index % self._columns

        self._layout.addWidget(card, row, col)

    def clear(self):
        """清空所有卡片"""
        for card in self._cards:
            card.deleteLater()
        self._cards.clear()

    def getCards(self):
        """获取所有卡片"""
        return self._cards