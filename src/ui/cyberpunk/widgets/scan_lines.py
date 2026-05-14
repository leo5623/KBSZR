"""扫描线覆盖层效果"""
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QLinearGradient,QLinearGradient


class ScanLinesOverlay(QWidget):
    """
    扫描线覆盖层效果
    在窗口上添加赛博朋克风格的扫描线效果
    """

    def __init__(self, parent=None, intensity: float = 0.03):
        super().__init__(parent)
        self.intensity = intensity
        self.animation_offset = 0

        # 设置为透明覆盖层 - 但让子控件正常显示
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)

        # 动画定时器 - 扫描线移动效果
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(50)  # 50ms刷新

    def _animate(self):
        """动画更新"""
        self.animation_offset = (self.animation_offset + 1) % 100
        self.update()

    def paintEvent(self, event):
        """绘制扫描线"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 获取窗口尺寸
        width = self.width()
        height = self.height()

        # 扫描线间隔 - 只画细线，不加背景遮罩
        line_spacing = 4
        offset = self.animation_offset

        # 绘制细扫描线（更淡）
        painter.setPen(QColor(0, 255, 255, 5))  # 极淡的青色

        for y in range(offset, height, line_spacing):
            painter.drawLine(0, y, width, y)

        # 每隔一段画一条稍亮的线
        painter.setPen(QColor(0, 255, 255, 12))
        for y in range(offset * 3 % line_spacing, height, line_spacing * 3):
            painter.drawLine(0, y, width, y)

    def setIntensity(self, intensity: float):
        """设置扫描线强度"""
        self.intensity = max(0.01, min(0.1, intensity))

    def stopAnimation(self):
        """停止动画"""
        self._timer.stop()

    def startAnimation(self):
        """开始动画"""
        if not self._timer.isActive():
            self._timer.start(50)

    def close(self):
        """关闭"""
        self._timer.stop()
        super().close()